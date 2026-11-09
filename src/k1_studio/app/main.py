# SPEC-004
from __future__ import annotations

import asyncio
import io
import os
import re
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, cast
from urllib.parse import urlsplit

import numpy as np
import soundfile as sf
from fastapi import FastAPI, File, Form, Request, UploadFile, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response

from ..dsp.engine import DSPError
from ..dsp.filters import Audio
from ..dsp.mastering import export_wav
from ..dsp.separator import separate
from .admission import UploadAdmission
from .schemas import Preview, Project, RenderRequest, Split, Track
from .service import Workspace, uid

STATUS = {
    "project_not_found": 404,
    "asset_not_found": 404,
    "region_not_found": 404,
    "busy": 409,
    "loudness_target_unreachable": 409,
    "project_limit": 413,
    "duration_limit": 413,
    "upload_too_large": 413,
    "unsupported_audio": 415,
    "model_unavailable": 503,
    "processing_failed": 500,
    "export_failed": 500,
}


def envelope(code: str, field: str | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": code.replace("_", " "), "field": field}}


def origin_allowed(host: str, origin: str | None) -> bool:
    hostname = host.split(":")[0]
    extra = os.environ.get("K1_ALLOWED_HOSTS", "").split(",")
    valid = hostname in ["localhost", "127.0.0.1", "testserver", *extra] or bool(
        re.fullmatch(r"\d+-[a-zA-Z0-9-]+\.e2b\.app", hostname)
    )
    return valid and (not origin or urlsplit(origin).netloc == host)


def create_app(
    root: Path | None = None, separator: Callable[[Audio, str], dict[str, Audio]] | None = None
) -> FastAPI:
    app = FastAPI(title="K1-STUDIO", version="0.1.0")
    app.add_middleware(UploadAdmission)
    workspace = Workspace(root or Path(os.environ.get("K1_WORKSPACE", ".workspace")))
    jobs: dict[str, dict[str, Any]] = {}
    app.state.workspace = workspace
    splitter = separator or separate

    @app.middleware("http")
    async def security(request: Request, call_next: Any) -> Response:
        if not origin_allowed(request.headers.get("host", ""), request.headers.get("origin")):
            return JSONResponse(envelope("origin_forbidden"), 403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return cast(Response, response)

    @app.exception_handler(DSPError)
    async def domain_error(request: Request, exc: DSPError) -> JSONResponse:
        return JSONResponse(envelope(exc.code, exc.field), STATUS.get(exc.code, 422))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(envelope("invalid_request"), 422)

    @app.exception_handler(Exception)
    async def processing_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(envelope("processing_failed"), 500)

    @app.post("/api/v1/ingest/upload", status_code=201)
    async def upload(
        file: Annotated[UploadFile, File()], project_id: Annotated[str | None, Form()] = None
    ) -> dict[str, Any]:
        raw = bytearray()
        try:
            while block := await file.read(1024 * 1024):
                raw.extend(block)
                if len(raw) > 256 * 1024 * 1024:
                    raise DSPError("upload_too_large")
            return await asyncio.to_thread(workspace.ingest, bytes(raw), project_id)
        finally:
            await file.close()

    def split_worker(job: dict[str, Any], graph: Project, track: Track, mode: str) -> None:
        published = []
        try:
            job.update(status="running", progress=0.1, stage="separating")
            audio = workspace.asset(track.file_path, graph.project_id).audio
            stems = splitter(audio.copy(), mode)

            def aligned(x: Audio) -> Audio:
                return np.pad(x[: len(audio)], ((0, max(0, len(audio) - len(x))), (0, 0)))

            buffers = {name: aligned(stems[name]) for name in ["Vocals", "Drums", "Bass", "Other"]}
            if mode == "2stem":
                buffers = {
                    "Vocals": buffers["Vocals"],
                    "Instrumental": buffers["Drums"] + buffers["Bass"] + buffers["Other"],
                }
            if len(graph.tracks) - 1 + len(buffers) > 8:
                raise DSPError("project_limit")
            tracks = []
            for name, audio in buffers.items():
                asset = workspace.add(audio, graph.project_id)
                published.append(asset)
                tracks.append(Track(track_id=uid(), name=name, file_path=asset.id))
            index = next(i for i, t in enumerate(graph.tracks) if t.track_id == track.track_id)
            graph.tracks[index : index + 1] = tracks
            workspace.projects[graph.project_id] = graph
            job.update(
                status="succeeded", progress=1.0, stage="complete", project=graph.model_dump()
            )
        except Exception as exc:
            for asset in published:
                workspace.assets.pop(asset.id, None)
                asset.path.unlink(missing_ok=True)
            code = exc.code if isinstance(exc, DSPError) else "processing_failed"
            job.update(status="failed", stage="failed", error=envelope(code))
        finally:
            workspace.heavy.release()

    @app.post("/api/v1/ingest/split-stems", status_code=202)
    def split(body: Split) -> dict[str, Any]:
        graph = workspace.projects.get(body.project_id)
        if not graph:
            raise DSPError("project_not_found")
        track = next((t for t in graph.tracks if t.track_id == body.track_id), None)
        if not track:
            raise DSPError("asset_not_found")
        if separator is None and not os.environ.get("K1_DEMUCS_MODELS"):
            raise DSPError("model_unavailable")
        if not workspace.heavy.acquire(blocking=False):
            raise DSPError("busy")
        id = uid()
        jobs[id] = dict(
            job_id=id, status="queued", progress=0.0, stage="queued", error=None, project=None
        )
        threading.Thread(
            target=split_worker,
            args=(jobs[id], graph.model_copy(deep=True), track.model_copy(deep=True), body.mode),
            daemon=True,
        ).start()
        return dict(job_id=id, status="queued", websocket_url=f"/ws/jobs/{id}")

    @app.websocket("/ws/jobs/{job_id}")
    async def progress(ws: WebSocket, job_id: str) -> None:
        if job_id not in jobs or not origin_allowed(
            ws.headers.get("host", ""), ws.headers.get("origin")
        ):
            await ws.close(code=1008)
            return
        await ws.accept()
        last = None
        while True:
            event = jobs[job_id].copy()
            if event != last:
                await ws.send_json(event)
                last = event
            if event["status"] in ("succeeded", "failed"):
                break
            await asyncio.sleep(0.02)
        await ws.close()

    @app.post("/api/v1/preview/region")
    def preview(body: Preview) -> Response:
        workspace.validate(body.project)
        if body.target_type == "master":
            regions = body.project.master_bus.regions
        else:
            track = next((t for t in body.project.tracks if t.track_id == body.track_id), None)
            if not track:
                raise DSPError("region_not_found")
            regions = track.regions
        region = next((r for r in regions if r.region_id == body.region_id), None)
        if not region:
            raise DSPError("region_not_found")
        if not workspace.heavy.acquire(blocking=False):
            raise DSPError("busy")
        try:
            result = workspace.render(body.project, body.bypass_master)
            start = max(0.0, region.start_sec - 2)
            end = min(len(result.audio) / 48000, region.end_sec + 2)
            stream = io.BytesIO()
            sf.write(
                stream,
                result.audio[round(start * 48000) : round(end * 48000)],
                48000,
                format="WAV",
                subtype="FLOAT",
            )
            return Response(
                stream.getvalue(),
                media_type="audio/wav",
                headers={"X-Start-Sec": str(start), "X-End-Sec": str(end)},
            )
        finally:
            workspace.heavy.release()

    @app.post("/api/v1/project/render")
    def render(body: RenderRequest) -> dict[str, Any]:
        if not workspace.heavy.acquire(blocking=False):
            raise DSPError("busy")
        try:
            graph = Project.model_validate(body.model_dump(exclude={"export_bit_depth"}))
            result = workspace.render(graph)
            id = uid()
            path = workspace.root / f"{id}.wav"
            export_wav(result, path, body.export_bit_depth)
            from .service import Asset

            workspace.assets[id] = Asset(id, graph.project_id, path, result.audio)
            return dict(
                project_id=graph.project_id,
                downloads=[
                    dict(asset_id=id, url=f"/api/v1/assets/{id}", bit_depth=body.export_bit_depth)
                ],
                telemetry=result.telemetry,
            )
        finally:
            workspace.heavy.release()

    @app.get("/api/v1/assets/{asset_id}")
    def asset(asset_id: str) -> FileResponse:
        a = workspace.asset(asset_id)
        return FileResponse(a.path, media_type="audio/wav", filename=f"k1-{asset_id}.wav")

    return app


app = create_app()
