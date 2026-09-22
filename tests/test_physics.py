import numpy as np

from src.rgbtonb.physics import SensorConfig, atmospheric_transmission, sensor_qe, simulate_channels


def test_sensor_qe_is_bounded_and_vectorized():
    values = sensor_qe(np.array([400.0, 550.0, 700.0]))
    assert values.shape == (3,)
    assert np.all((values >= 0.12) & (values <= 0.66))


def test_transmission_decreases_with_airmass():
    assert atmospheric_transmission(656.3, 2.0) < atmospheric_transmission(656.3, 1.0)


def test_signal_scales_with_exposure():
    short = simulate_channels(exposure_s=60, sensor=SensorConfig())
    long = simulate_channels(exposure_s=120, sensor=SensorConfig())
    assert long["H-alpha"]["electrons"] == 2 * short["H-alpha"]["electrons"]
    assert long["H-alpha"]["snr"] > short["H-alpha"]["snr"]
