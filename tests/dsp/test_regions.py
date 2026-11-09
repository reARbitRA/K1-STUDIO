import numpy as np
import pytest

from k1_studio.dsp import presets as p
from k1_studio.dsp import regions as r
from k1_studio.dsp.engine import DSPError


def tone(hz=110):
    x = 0.7 * np.sin(np.arange(96000) * 2 * np.pi * hz / 48000)
    return np.column_stack([x, x]).astype("float32")


def region(effect="HARD_MUTE", **kwargs):
    return dict(
        region_id="r",
        start_sec=0.5,
        end_sec=1.5,
        effect_type=effect,
        wet_mix=1,
        fade_ms=8,
        **kwargs,
    )


def test_ac_1_zero_crossing_boundaries():
    x = np.ones((1000, 2), dtype="float32")
    assert r.snap(x, 500) == 500
    x[499:] = -1
    assert r.snap(x, 500) == 498
    assert r.snap(np.zeros_like(x), 0) == 0
    anti = np.column_stack([np.ones(1000), -np.ones(1000)]).astype("float32")
    assert r.snap(anti, 500) == 500
    assert 0 <= r.snap(x, 1000) <= 1000


def test_ac_2_complementary_fades():
    for n in [2, 4, 200, 1000]:
        weights = r.envelope(n, 144)
        assert len(weights) == n and weights[0] == weights[-1] == 0
        np.testing.assert_allclose(weights, weights[::-1], atol=1e-7)
    x = tone()
    reg = region()
    reg["wet_mix"] = 0
    np.testing.assert_array_equal(r.apply_regions(x, [reg]).audio, x)
    for field, value in [("start_sec", -1), ("end_sec", 3), ("fade_ms", 1), ("wet_mix", 2)]:
        bad = region()
        bad[field] = value
        with pytest.raises(DSPError):
            r.apply_regions(x, [bad])


def test_ac_3_hard_mute():
    result = r.apply_regions(tone(), [region()])
    b = result.boundaries[0]
    assert b["fade_samples"] == 144
    assert not result.audio[b["start"] + 144 : b["end"] - 144].any()
    np.testing.assert_array_equal(result.audio[: b["start"]], tone()[: b["start"]])


def test_ac_4_nasa_radio():
    levels = []
    for hz in [100, 1350, 10000]:
        y = p.process(tone(hz) * 0.01, "NASA_WALKIE_TALKIE")
        levels.append(np.std(y[24000:]))
    assert levels[1] > levels[0] and levels[1] > levels[2]
    assert p.process(tone(), "NASA_WALKIE_TALKIE").shape == tone().shape


def test_ac_5_underwater():
    lo = p.process(tone(100), "UNDERWATER_WOMB")
    hi = p.process(tone(4000), "UNDERWATER_WOMB")
    assert 20 * np.log10(np.std(hi[24000:]) / np.std(lo[24000:])) < -40


def test_ac_6_tape_stop():
    positions, speed = p.tape_positions(96000)
    assert positions[0] == 0 and np.all(np.diff(positions) >= 0)
    assert speed[0] == 1 and speed[-1] == 0.02
    y = p.process(tone(), "ANALOG_TAPE_STOP")
    assert len(y) == 96000 and abs(y[-1]).max() == 0


def test_ac_7_stutter_degrade():
    x = tone()
    for bpm in [None, 120]:
        a = p.process(x, "TAPE_STUTTER_DEGRADE", bpm)
        np.testing.assert_array_equal(a, p.process(x, "TAPE_STUTTER_DEGRADE", bpm))
        assert np.isfinite(a).all() and a.shape == x.shape
    with pytest.raises(DSPError):
        r.apply_regions(x, [], bpm=0)


def test_ac_8_sub_drop():
    n = 96000
    u = np.linspace(0, 1, n)
    freq = 90 * (36 / 90) ** u
    phase = 2 * np.pi * np.concatenate([[0], np.cumsum(freq[:-1])]) / 48000
    expected = 10 ** (-6 / 20) * np.exp(-6 * u) * np.sin(phase)
    y = p.process(np.zeros((n, 2), dtype="float32"), "SUB_40HZ_DROP")
    np.testing.assert_allclose(y[:, 0], expected, atol=1e-5)
    np.testing.assert_array_equal(y[:, 0], y[:, 1])
    assert y[0, 0] == 0


def test_ac_9_overlap_and_targets():
    x = tone()
    old = x.copy()
    a = region("UNDERWATER_WOMB")
    b = region("SUB_40HZ_DROP")
    b["region_id"] = "b"
    y = r.apply_regions(x, [a, b]).audio
    manual = r.apply_regions(r.apply_regions(x, [a]).audio, [b]).audio
    np.testing.assert_allclose(y, manual, atol=1e-6)
    np.testing.assert_array_equal(x, old)
    assert not np.allclose(y, r.apply_regions(x, [b, a]).audio)
    with pytest.raises(DSPError):
        p.process(x, "NOT_A_PRESET")


def test_ac_10_click_boundary_fixtures(tmp_path):
    import soundfile as sf
    from scipy import signal

    for hz in [55, 110, 220]:
        for fx in ["HARD_MUTE", "NASA_WALKIE_TALKIE"]:
            x = tone(hz)
            result = r.apply_regions(x, [region(fx)])
            b = result.boundaries[0]
            np.testing.assert_allclose(
                result.audio[[b["start"], b["end"] - 1]], x[[b["start"], b["end"] - 1]], atol=1e-6
            )
            sf.write(tmp_path / f"{hz}-{fx}.wav", result.audio, 48000, subtype="FLOAT")
            _, _, s = signal.spectrogram(result.audio[:, 0], 48000)
            assert np.isfinite(s).all()
