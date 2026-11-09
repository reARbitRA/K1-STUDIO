import numpy as np
import pyloudnorm as pyln
import pytest
import soundfile as sf
from scipy import signal

from k1_studio.dsp import mastering as m
from k1_studio.dsp.engine import DSPError


def audio(seconds=10):
    t = np.arange(int(48000 * seconds)) / 48000
    x = 0.08 * (np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 2000 * t))
    return np.column_stack([x, x]).astype("float32")


def test_ac_1_ms_filter_and_width():
    x = audio(1)
    x[:, 1] *= -0.3
    y = m.ms_stage(x, 0)
    np.testing.assert_allclose(y[:, 0], y[:, 1], atol=1e-7)
    z = m.ms_stage(x, 1.15)
    np.testing.assert_allclose(z.mean(axis=1), x.mean(axis=1), atol=1e-6)
    for n in [0, 1, 4, 20]:
        assert m.ms_stage(x[:n], 1).shape == (n, 2)


def test_ac_2_low_band_correlation():
    t = np.arange(480000) / 48000
    low = 0.1 * np.sin(2 * np.pi * 40 * t)
    side = 0.1 * np.sin(2 * np.pi * 2000 * t)
    x = np.column_stack([low + side, low - side]).astype("float32")
    y = m.ms_stage(x, 1.15)
    sos = signal.butter(4, 80, fs=48000, output="sos")
    filtered = signal.sosfiltfilt(sos, y, axis=0)[48000:-48000]
    assert np.corrcoef(filtered.T)[0, 1] > 0.9999
    sideonly = np.column_stack([low, -low]).astype("float32")
    counter = m.ms_stage(sideonly, 1)
    assert np.corrcoef(counter[48000:-48000].T)[0, 1] < -0.99


def test_ac_3_master_eq():
    x = audio(1)
    y = m.eq_stage(x, {})
    assert np.isfinite(y).all() and y.shape == x.shape
    assert not np.allclose(x, y)
    with pytest.raises(DSPError):
        m.master(x, {"air_boost_db": 13})


def test_ac_4_parallel_compression():
    x = audio(1)
    a = m.parallel_stage(x, 0)
    b = m.parallel_stage(x, 1)
    np.testing.assert_allclose(m.parallel_stage(x, 0.18), 0.82 * a + 0.18 * b, atol=1e-6)


def test_ac_5_asymmetric_tape():
    x = np.column_stack([np.linspace(-2, 2, 1000)] * 2).astype("float32")
    for d in [1, 1.22, 2]:
        expected = (np.tanh(d * x + 0.035) - np.tanh(0.035)) / np.tanh(d)
        np.testing.assert_allclose(m.tape(x, d), expected, atol=1e-6)
    assert abs(m.tape(np.zeros((1, 2), dtype="float32"), 1.22)).max() < 1e-7


@pytest.mark.parametrize("target", [-14, -9.5, -8])
def test_ac_6_lufs_true_peak_export(tmp_path, target):
    result = m.master(audio(), {"target_lufs": target})
    path = tmp_path / "master.wav"
    m.export_wav(result, path)
    x, rate = sf.read(path)
    assert abs(pyln.Meter(rate).integrated_loudness(x) - target) <= 0.2
    # Independent 8x detector (production uses 4x).
    peak = np.max(abs(signal.resample_poly(x, 8, 1, axis=0)))
    assert 20 * np.log10(peak) <= -0.3 + 1e-5


def test_ac_7_silence_short_and_failure():
    for n in [0, 1, 100, 19200]:
        result = m.master(np.zeros((n, 2), dtype="float32"), {})
        assert not result.audio.any() and result.telemetry["after"]["integrated_lufs"] is None
    result = m.master(audio(0.1), {})
    assert len(result.audio) == 4800 and result.telemetry["analysis_padded"]
    with pytest.raises(DSPError):
        m.master(np.full((10, 2), np.nan, dtype="float32"), {})


def test_ac_8_pcm_formats_and_dither(tmp_path):
    result = m.master(audio(1), {})
    for depth in [16, 24]:
        path = tmp_path / f"{depth}.wav"
        m.export_wav(result, path, depth)
        info = sf.info(path)
        assert info.subtype == f"PCM_{depth}" and info.samplerate == 48000 and info.frames == 48000
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    m.export_wav(result, a, 16)
    m.export_wav(result, b, 16)
    assert a.read_bytes() == b.read_bytes()


def test_ac_9_order_bypass_and_telemetry(monkeypatch):
    order = []
    x = audio(1)
    for name in ["ms_stage", "eq_stage", "parallel_stage", "tape"]:
        monkeypatch.setattr(m, name, lambda a, *args, _name=name: (order.append(_name) or a))
    result = m.master(x, {})
    assert order == ["ms_stage", "eq_stage", "parallel_stage", "tape"]
    assert set(result.telemetry) >= {"before", "after", "analysis_padded"}
    np.testing.assert_array_equal(m.bypass(x), x)


def test_intersample_peak_and_atomic_failure(tmp_path):
    x = np.sin(np.arange(48000) * np.pi / 2 + np.pi / 4) * 1.1
    stereo = np.column_stack([x, x]).astype("float32")
    assert np.max(abs(stereo)) < 1 and m.true_peak(stereo) > 1
    limited = m.limit(stereo)
    assert 20 * np.log10(np.max(abs(signal.resample_poly(limited, 8, 1, axis=0)))) <= -0.3
    result = m.MasterResult(np.ones((48000, 2), dtype="float32") * 2, {}, -9.5)
    path = tmp_path / "failed.wav"
    with pytest.raises(DSPError):
        m.export_wav(result, path)
    assert not path.exists() and not list(tmp_path.glob("*.wav"))
    pulse = np.zeros((480000, 2), dtype="float32")
    pulse[240000] = 1
    with pytest.raises(DSPError, match="loudness_target_unreachable"):
        m.master(pulse, {"target_lufs": -8})
