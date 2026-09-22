import numpy as np

from src.rgbtonb.physics import (
    CHANNELS,
    continuum_channel_signals,
    SENSOR_CURVES,
    integrated_sensor_signal,
    ideal_sensor_color,
    interpolate_sensor_response,
    line_channel_signals,
    sensor_display_values,
    sensor_channel_signals,
    super_gaussian_profile,
    wavelength_to_rgb,
    wavelength_to_rgb_channels,
)


def test_spectral_colors_follow_wavelength_order():
    assert wavelength_to_rgb(500.7) != wavelength_to_rgb(656.3)
    assert CHANNELS["S II"]["color"] == CHANNELS["H-alpha"]["color"] == "#ff0000"
    assert wavelength_to_rgb(468.6).startswith("#")


def test_spectral_rgb_reference_has_three_bounded_channels():
    channels = wavelength_to_rgb_channels(500.7)
    assert channels.shape == (3,)
    assert np.all((channels >= 0) & (channels <= 1))
    assert wavelength_to_rgb(500.7) == "#00ff8a"


def test_ideal_sensor_uses_intensities_without_response_correction():
    assert ideal_sensor_color({"H-alpha": 0, "O III": 0, "S II": 0, "He II": 0}) == "rgb(0, 0, 0)"
    assert ideal_sensor_color({"H-alpha": 100, "O III": 0, "S II": 0, "He II": 0}) == "rgb(255, 0, 0)"


def test_sensor_response_mixes_all_sensor_channels():
    intensities = {"H-alpha": 100, "O III": 0, "S II": 0, "He II": 0}
    color = ideal_sensor_color(intensities, use_sensor_response=True)
    assert color != "rgb(255, 0, 0)"
    assert not color.startswith("rgb(255, ")


def test_sensor_signal_can_be_normalized_to_maximum():
    intensities = {"H-alpha": 80, "O III": 65, "S II": 55, "He II": 40}
    color = ideal_sensor_color(intensities, True, 6.0, normalize_to_max=True)
    channels = [int(value) for value in color[4:-1].split(", ")]
    assert max(channels) == 255


def test_bandwidth_changes_effective_sensor_response():
    narrow = integrated_sensor_signal("GREEN", 500.7, 1.0, 100)
    wide = integrated_sensor_signal("GREEN", 500.7, 10.0, 100)
    assert not np.isclose(narrow, wide)


def test_zero_intensity_has_no_sensor_signal():
    assert integrated_sensor_signal("RED", 656.3, 6.0, 0) == 0


def test_white_continuum_contributes_to_all_ideal_channels():
    assert np.array_equal(continuum_channel_signals(12), np.array([4.0, 4.0, 4.0]))


def test_white_continuum_is_sensor_weighted():
    response = continuum_channel_signals(12, True)
    assert response.shape == (3,)
    assert np.all(response > 0)
    assert not np.allclose(response, response[0])


def test_continuum_shifts_ideal_combined_color():
    line_only = sensor_channel_signals({"O III": 65}, False, 6.0)
    with_continuum = sensor_channel_signals({"O III": 65}, False, 6.0, 100)
    assert with_continuum[0] > line_only[0]
    assert not np.isclose(line_only[1] / line_only.sum(), with_continuum[1] / with_continuum.sum())


def test_line_and_continuum_sliders_share_integrated_scale():
    line = sensor_channel_signals({"O III": 12}, False, 6.0)
    continuum = continuum_channel_signals(12, False)
    assert np.isclose(line.sum(), continuum.sum())


def test_white_continuum_has_scatter_coordinates():
    response = continuum_channel_signals(20, True)
    total = response.sum()
    assert 0 <= response[0] / total <= 1
    assert 0 <= response[1] / total <= 1


def test_sensor_channel_ratios_sum_to_one():
    intensities = {"H-alpha": 80, "O III": 65, "S II": 55, "He II": 40}
    signals = sensor_channel_signals(intensities, True, 6.0)
    assert np.isclose(signals.sum() / signals.sum(), 1.0)


def test_line_channel_signals_produce_normalized_scatter_coordinates():
    signals = line_channel_signals("H-alpha", 80, True, 6.0)
    assert signals.shape == (3,)
    assert np.isclose(signals[:2].sum() / signals.sum(), signals[0] / signals.sum() + signals[1] / signals.sum())


def test_display_values_respect_selected_bit_depth():
    intensities = {"H-alpha": 80, "O III": 65, "S II": 55, "He II": 40}
    values = sensor_display_values(intensities, 6.0, 10, normalize_to_max=True)
    assert values.max() == 1023
    assert np.all(values >= 0)


def test_display_values_support_sensor_16_bit_output():
    intensities = {"H-alpha": 80, "O III": 65, "S II": 55, "He II": 40}
    values = sensor_display_values(intensities, 6.0, 16, normalize_to_max=True)
    assert values.max() == 65535
    assert np.all(values >= 0)


def test_bit_depth_quantizes_display_values():
    intensities = {"H-alpha": 80, "O III": 65, "S II": 55, "He II": 40}
    values = sensor_display_values(intensities, 6.0, 8, normalize_to_max=False)
    assert np.all(values == np.floor(values))


def test_sensor_curves_are_smooth_and_bounded():
    assert set(SENSOR_CURVES) == {"RED", "GREEN", "BLUE"}
    wavelengths = np.linspace(450, 680, 1000)
    response = interpolate_sensor_response("GREEN", wavelengths)
    assert response.shape == wavelengths.shape
    assert np.all((response >= 0) & (response <= 1))


def test_super_gaussian_has_requested_fwhm():
    profile = super_gaussian_profile(np.array([500.0, 503.0, 506.0]), 503.0, 6.0)
    assert profile[1] == 1.0
    assert np.isclose(profile[0], 0.5)
    assert np.isclose(profile[2], 0.5)
