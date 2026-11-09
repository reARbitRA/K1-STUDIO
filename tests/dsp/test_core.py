import numpy as np
import pytest

from k1_studio.dsp import engine as e
from k1_studio.dsp import filters as f


def tone(hz=440, seconds=2, amplitude=0.1):
    x = amplitude * np.sin(np.arange(int(seconds * 48000)) * 2 * np.pi * hz / 48000)
    return np.column_stack([x, x]).astype("float32")


@pytest.mark.parametrize("rate", [44100, 48000, 96000])
@pytest.mark.parametrize("channels", [1, 2])
def test_ac_1_canonical_audio(rate, channels):
    x = np.ones((rate, channels), dtype="float64") * 0.25
    original = x.copy()
    y = e.canonicalize(x, rate)
    assert y.shape == (48000, 2) and y.dtype == np.float32 and np.isfinite(y).all()
    np.testing.assert_array_equal(x, original)


def test_ac_2_gain_phase_validation():
    x = tone()
    np.testing.assert_allclose(e.gain_phase(x, 6, True), -x * 10 ** (0.3), atol=1e-6)
    for value in [np.nan, 13, -25]:
        with pytest.raises(e.DSPError):
            e.gain_phase(x, value, False)
    for rate in [0, -1, 1.2, True]:
        with pytest.raises(e.DSPError):
            e.canonicalize(x, rate)
    for audio in [np.ones((3, 3)), np.array([[np.nan, 0]]), np.ones(3)]:
        with pytest.raises(e.DSPError):
            e.canonicalize(audio, 48000)


def test_ac_3_equal_power_pan():
    x = np.ones((10, 2), dtype="float32")
    for p in [-1, 0, 1]:
        y = e.pan(x, p)
        theta = (p + 1) * np.pi / 4
        np.testing.assert_allclose(y[0], [np.cos(theta), np.sin(theta)], atol=1e-6)
        assert abs(np.sum(y[0] ** 2) - 1) < 1e-6


def test_ac_4_mute_solo_padding():
    a = np.ones((4, 2), dtype="float32") * 0.1
    b = np.ones((8, 2), dtype="float32") * 0.2
    r = e.mix_tracks([a, b], [{"solo": True}, {"mute": True}])
    assert r.audio.shape == (8, 2)
    np.testing.assert_allclose(r.audio[:4], a * 10 ** (-6 / 20), atol=1e-6)
    assert not r.audio[4:].any()
    assert not e.mix_tracks([a, b], [{"mute": True, "solo": True}, {}]).audio.any()
    assert e.mix_tracks([], []).audio.shape == (0, 2)


def test_ac_5_headroom():
    for amplitude in [0, 0.1, 4]:
        x = np.full((20, 2), amplitude, dtype="float32")
        r = e.mix_tracks([x], [{}])
        gain = 10 ** (-6 / 20) / max(1, amplitude)
        np.testing.assert_allclose(r.audio, x * gain, atol=1e-6)
        assert np.max(abs(r.audio)) <= 10 ** (-6 / 20) + 1e-6
        assert abs(r.pre_master_gain_db - 20 * np.log10(gain)) < 1e-6


def test_ac_6_channel_eq():
    impulse = np.zeros((48000, 2), dtype="float32")
    impulse[0] = 1
    for hz, q, db in [(290, 1.6, -2), (2650, 1.2, 3), (4850, 2.5, -4)]:
        y = f.bell(impulse, hz, q, db)
        response = np.sum(y[:, 0] * np.exp(-2j * np.pi * hz * np.arange(len(y)) / 48000))
        assert abs(20 * np.log10(abs(response)) - db) < 0.25
        np.testing.assert_array_equal(f.bell(impulse, hz, q, 0), impulse)
    low = f.butter(tone(50), 100, "highpass", 2)
    high = f.butter(tone(4000), 100, "highpass", 2)
    assert 20 * np.log10(np.std(low[24000:]) / np.std(high[24000:])) < -10


def test_ac_7_channel_compression():
    x = tone(amplitude=0.3)
    np.testing.assert_allclose(f.compress(x, -20, 1, 1, 20), x, atol=1e-6)
    outputs = []
    for a in [0.2, 0.4]:
        y = f.compress(tone(amplitude=a), -30, 4, 1, 20)
        outputs.append(20 * np.log10(np.std(y[-24000:])))
    assert abs((outputs[1] - outputs[0]) / (20 * np.log10(2)) - 0.25) < 0.05
    with pytest.raises(e.DSPError):
        e.render_track(x, {"channel_strip": {"comp_attack_ms": 0}})


def test_ac_8_order_and_immutability(monkeypatch):
    order = []
    x = tone()
    original = x.copy()
    monkeypatch.setattr(e, "gain_phase", lambda a, *args: (order.append("gain") or a.copy()))
    monkeypatch.setattr(e, "channel_strip", lambda a, *args: (order.append("strip") or a.copy()))
    monkeypatch.setattr(e, "pan", lambda a, *args: (order.append("pan") or a.copy()))

    def callback(a, regions):
        order.append("regions")
        return a.copy()

    e.render_track(x, {}, callback)
    assert order == ["gain", "strip", "regions", "pan"]
    np.testing.assert_array_equal(x, original)
    monkeypatch.undo()
    np.testing.assert_allclose(e.render_track(x, {}), e.render_track(x, {}), atol=1e-6)


def test_invalid_mixer_flags():
    x = tone()
    with pytest.raises(e.DSPError):
        e.mix_tracks([x], [{"mute": "false"}])
