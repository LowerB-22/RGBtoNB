import numpy as np

from src.rgbtonb.physics import CHANNELS, ideal_sensor_color, super_gaussian_profile, wavelength_to_rgb


def test_spectral_colors_follow_wavelength_order():
    assert wavelength_to_rgb(500.7) != wavelength_to_rgb(656.3)
    assert CHANNELS["S II"]["color"] == CHANNELS["H-alpha"]["color"] == "#ff0000"
    assert wavelength_to_rgb(468.6).startswith("#")


def test_ideal_sensor_uses_intensities_without_response_correction():
    assert ideal_sensor_color({"H-alpha": 0, "O III": 0, "S II": 0, "He II": 0}) == "rgb(0, 0, 0)"
    assert ideal_sensor_color({"H-alpha": 100, "O III": 0, "S II": 0, "He II": 0}) == "rgb(255, 0, 0)"


def test_super_gaussian_has_requested_fwhm():
    profile = super_gaussian_profile(np.array([500.0, 503.0, 506.0]), 503.0, 6.0)
    assert profile[1] == 1.0
    assert np.isclose(profile[0], 0.5)
    assert np.isclose(profile[2], 0.5)
