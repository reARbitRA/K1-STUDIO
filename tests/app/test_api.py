import io
import os
import platform
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from k1_studio.app.main import create_app


def wav(seconds=1):
    t = np.arange(int(48000 * seconds)) / 48000
    x = 0.1 * np.sin(2 * np.pi * 440 * t)
    output = io.BytesIO()
    sf.write(output, np.column_stack([x, x]), 48000, format="WAV", subtype="FLOAT")
    return output.getvalue()


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path))


def upload(client, seconds=1, project_id=None):
    res = client.post(
        "/api/v1/ingest/upload",
        files={"file": ("stem.wav", wav(seconds), "audio/wav")},
        data={"project_id": project_id} if project_id else {},
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_ac_1_project_schema(client):
    graph = upload(client)["project"]
    assert graph["sample_rate"] == 48000 and graph["master_bus"]["target_lufs"] == -9.5
    graph["tracks"][0]["pan"] = 2
    assert client.post("/api/v1/project/render", json=graph).status_code == 422
    graph["tracks"][0]["pan"] = 0
    graph["tracks"][0]["mute"] = "false"
    assert client.post("/api/v1/project/render", json=graph).status_code == 422
    assert "/api/v1/project/render" in client.get("/openapi.json").json()["paths"]


def test_ac_2_upload_and_peaks(client):
    data = upload(client)
    assert data["sample_rate"] == 48000 and data["channels"] == 2
    assert len(data["waveform_peaks"]["channels"]) == 2
    assert len(data["waveform_peaks"]["channels"][0]) == 512
    response = client.get("/api/v1/assets/" + data["asset_id"])
    audio, rate = sf.read(io.BytesIO(response.content))
    assert rate == 48000 and audio.shape == (48000, 2)


def test_ac_3_demucs_modes(tmp_path):
    calls = []

    def fake(x, mode):
        calls.append(mode)
        return {
            name: x * (i + 1) / 10 for i, name in enumerate(["Vocals", "Drums", "Bass", "Other"])
        }

    c = TestClient(create_app(tmp_path, separator=fake))
    for mode, count in [("2stem", 2), ("4stem", 4)]:
        graph = upload(c)["project"]
        response = c.post(
            "/api/v1/ingest/split-stems",
            json={
                "project_id": graph["project_id"],
                "track_id": graph["tracks"][0]["track_id"],
                "mode": mode,
            },
        )
        assert response.status_code == 202, response.text
        with c.websocket_connect(response.json()["websocket_url"]) as ws:
            events = []
            while not events or events[-1]["status"] not in ("succeeded", "failed"):
                events.append(ws.receive_json())
        assert events[-1]["status"] == "succeeded", events
        tracks = events[-1]["project"]["tracks"]
        assert len(tracks) == count
        if mode == "2stem":
            data = c.get("/api/v1/assets/" + tracks[1]["file_path"]).content
            y, _ = sf.read(io.BytesIO(data))
            original, _ = sf.read(io.BytesIO(wav()))
            np.testing.assert_allclose(y, original * 0.9, atol=1e-6)
    assert calls == ["2stem", "4stem"]


def test_ac_4_job_websocket(client, tmp_path):
    from k1_studio.dsp.engine import DSPError

    def fail(x, mode):
        raise DSPError("model_unavailable")

    missing = upload(client)["project"]
    assert (
        client.post(
            "/api/v1/ingest/split-stems",
            json={
                "project_id": missing["project_id"],
                "track_id": missing["tracks"][0]["track_id"],
                "mode": "2stem",
            },
        ).status_code
        == 503
    )
    client = TestClient(create_app(tmp_path / "failure", separator=fail))
    graph = upload(client)["project"]
    r = client.post(
        "/api/v1/ingest/split-stems",
        json={
            "project_id": graph["project_id"],
            "track_id": graph["tracks"][0]["track_id"],
            "mode": "2stem",
        },
    )
    with client.websocket_connect(r.json()["websocket_url"]) as ws:
        terminal = ws.receive_json()
        while terminal["status"] not in ("succeeded", "failed"):
            terminal = ws.receive_json()
    assert (
        terminal["status"] == "failed" and terminal["error"]["error"]["code"] == "model_unavailable"
    )
    with client.websocket_connect(r.json()["websocket_url"]) as ws:
        assert ws.receive_json()["status"] == "failed"


def test_ac_5_preview_slice(client):
    graph = upload(client, 4)["project"]
    graph["tracks"][0]["regions"] = [
        dict(region_id="r", start_sec=0, end_sec=0.5, effect_type="HARD_MUTE")
    ]
    response = client.post(
        "/api/v1/preview/region",
        json=dict(
            project=graph,
            target_type="track",
            track_id=graph["tracks"][0]["track_id"],
            region_id="r",
        ),
    )
    assert response.status_code == 200, response.text
    data, rate = sf.read(io.BytesIO(response.content))
    assert rate == 48000 and len(data) == 120000 and response.headers["x-start-sec"] == "0.0"
    full = client.post("/api/v1/project/render", json=graph)
    assert full.status_code == 200, full.text
    exported = client.get(full.json()["downloads"][0]["url"])
    y, _ = sf.read(io.BytesIO(exported.content))
    np.testing.assert_allclose(data, y[: len(data)], atol=1e-5)


def test_ac_6_render_downloads(client):
    graph = upload(client)["project"]
    response = client.post("/api/v1/project/render", json=graph)
    assert response.status_code == 200, response.text
    url = response.json()["downloads"][0]["url"]
    assert url.startswith("/api/")
    data = client.get(url)
    assert sf.info(io.BytesIO(data.content)).subtype == "PCM_24"
    assert response.json()["telemetry"]["after"]["true_peak_dbtp"] <= -0.3
    assert client.get(url, headers={"Range": "bytes=0-99"}).status_code == 206


def test_ac_7_security_limits(client):
    graph = upload(client)["project"]
    graph["tracks"][0]["file_path"] = "../../etc/passwd"
    response = client.post("/api/v1/project/render", json=graph)
    assert response.status_code == 404 and "passwd" not in response.text
    assert (
        client.post("/api/v1/ingest/upload", files={"file": ("a.wav", b"bad")}).status_code == 415
    )
    assert (
        client.get("/openapi.json", headers={"Origin": "https://evil.example"}).status_code == 403
    )


def test_ac_12_preview_latency(client, record_property):
    graph = upload(client, 10)["project"]
    for _ in range(3):
        graph = upload(client, 10, graph["project_id"])["project"]
    graph["tracks"][0]["regions"] = [
        dict(
            region_id="bench",
            start_sec=4,
            end_sec=5,
            effect_type="NASA_WALKIE_TALKIE",
            wet_mix=1,
            fade_ms=8,
        )
    ]
    body = dict(
        project=graph,
        target_type="track",
        track_id=graph["tracks"][0]["track_id"],
        region_id="bench",
    )
    times = []
    for i in range(120):
        start = time.perf_counter()
        r = client.post("/api/v1/preview/region", json=body)
        assert r.status_code == 200, r.text
        if i >= 20:
            times.append((time.perf_counter() - start) * 1000)
    report = dict(
        median_ms=float(np.median(times)),
        p95_ms=float(np.percentile(times, 95)),
        max_ms=max(times),
        platform=platform.platform(),
        logical_cores=os.cpu_count(),
        memory_kib=int(
            next(
                line.split()[1]
                for line in Path("/proc/meminfo").read_text().splitlines()
                if line.startswith("MemTotal:")
            )
        )
        if Path("/proc/meminfo").exists()
        else None,
        python=platform.python_version(),
    )
    print(report)
    record_property("preview_benchmark", str(report))
    assert report["p95_ms"] < 300


def test_upload_admission_before_multipart(client):
    r = client.post(
        "/api/v1/ingest/upload",
        content=b"x",
        headers={
            "Content-Length": str(300 * 1024 * 1024),
            "Content-Type": "application/octet-stream",
        },
    )
    assert r.status_code == 413
