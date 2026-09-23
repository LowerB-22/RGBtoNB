"""Small spectral-profile helpers for the narrowband visualizer."""

import json
from pathlib import Path

import numpy as np


def wavelength_to_rgb_channels(wavelength_nm: float) -> np.ndarray:
    """Return normalized sRGB channel values for one visible wavelength."""
    wavelength = float(wavelength_nm)
    if not 380.0 <= wavelength <= 780.0:
        raise ValueError("wavelength_nm must be between 380 and 780 nm")

    if wavelength < 440:
        red, green, blue = -(wavelength - 440) / 60, 0, 1
    elif wavelength < 490:
        red, green, blue = 0, (wavelength - 440) / 50, 1
    elif wavelength < 510:
        red, green, blue = 0, 1, -(wavelength - 510) / 20
    elif wavelength < 580:
        red, green, blue = (wavelength - 510) / 70, 1, 0
    elif wavelength < 645:
        red, green, blue = 1, -(wavelength - 645) / 65, 0
    else:
        red, green, blue = 1, 0, 0

    if wavelength < 420:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / 40
    elif wavelength > 700:
        attenuation = 0.3 + 0.7 * (780 - wavelength) / 80
    else:
        attenuation = 1.0

    return np.array([(channel * attenuation) ** 0.8 for channel in (red, green, blue)])


def wavelength_to_rgb(wavelength_nm: float) -> str:
    """Approximate a visible spectral wavelength as an sRGB color."""
    rgb = np.rint(wavelength_to_rgb_channels(wavelength_nm) * 255).astype(int)
    return "#{:02x}{:02x}{:02x}".format(*rgb)


CHANNELS = {
    "H-alpha": {"wavelength_nm": 656.3, "color": wavelength_to_rgb(656.3)},
    "O III": {"wavelength_nm": 500.7, "color": wavelength_to_rgb(500.7)},
    "S II": {"wavelength_nm": 672.4, "color": wavelength_to_rgb(672.4)},
    "He II": {"wavelength_nm": 468.6, "color": wavelength_to_rgb(468.6)},
}


def _load_sensor_curves() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    data_path = Path(__file__).resolve().parents[2] / "sensor_data" / "Sony_IMX571.json"
    with data_path.open(encoding="utf-8") as data_file:
        records = json.load(data_file)
    return {
        record["channel"]: (
            np.asarray(record["wavelength"]["value"], dtype=float),
            np.asarray(record["values"]["value"], dtype=float),
        )
        for record in records
    }


SENSOR_CURVES = _load_sensor_curves()
DISPLAY_REFERENCE_INTENSITY = 100.0


def _prepare_curve(
    wavelengths_nm: np.ndarray,
    values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    order = np.argsort(wavelengths_nm)
    wavelengths = wavelengths_nm[order]
    sorted_values = values[order]
    unique_wavelengths, unique_indices = np.unique(wavelengths, return_index=True)
    return unique_wavelengths, sorted_values[unique_indices], np.gradient(sorted_values, wavelengths)[unique_indices]


def interpolate_sensor_response(channel: str, wavelength_nm: np.ndarray | float) -> np.ndarray:
    """Smoothly interpolate one sensor channel; return zero outside its data range."""
    wavelengths, values = SENSOR_CURVES[channel]
    source_wavelengths, source_values, slopes = _prepare_curve(wavelengths, values)
    query = np.asarray(wavelength_nm, dtype=float)
    positions = np.searchsorted(source_wavelengths, query, side="right") - 1
    positions = np.clip(positions, 0, len(source_wavelengths) - 2)
    left_wavelength = source_wavelengths[positions]
    right_wavelength = source_wavelengths[positions + 1]
    span = right_wavelength - left_wavelength
    fraction = np.clip((query - left_wavelength) / span, 0, 1)
    left_value = source_values[positions]
    right_value = source_values[positions + 1]
    left_slope = slopes[positions]
    right_slope = slopes[positions + 1]
    smooth_value = (
        (2 * fraction**3 - 3 * fraction**2 + 1) * left_value
        + (fraction**3 - 2 * fraction**2 + fraction) * span * left_slope
        + (-2 * fraction**3 + 3 * fraction**2) * right_value
        + (fraction**3 - fraction**2) * span * right_slope
    )
    in_range = (query >= source_wavelengths[0]) & (query <= source_wavelengths[-1])
    return np.where(in_range, np.clip(smooth_value, 0, 1), 0.0)


def sensor_response_curve(channel: str, wavelength_nm: np.ndarray) -> np.ndarray:
    """Return a smooth sensor curve over the requested wavelength grid."""
    return interpolate_sensor_response(channel, wavelength_nm)


def continuum_channel_signals(
    intensity: float,
    use_sensor_response: bool = False,
    wavelength_range: tuple[float, float] = (430.0, 710.0),
) -> np.ndarray:
    """Return the RGB contribution of a flat white continuum."""
    if intensity <= 0:
        return np.zeros(3)
    if not use_sensor_response:
        return np.full(3, intensity / 3.0, dtype=float)
    wavelengths = np.linspace(*wavelength_range, 1001)
    return intensity * np.array([
        np.trapezoid(interpolate_sensor_response(channel, wavelengths), wavelengths)
        / (wavelength_range[1] - wavelength_range[0])
        for channel in ("RED", "GREEN", "BLUE")
    ])


def integrated_sensor_signal(
    channel: str,
    center_nm: float,
    bandwidth_nm: float,
    intensity: float,
) -> float:
    """Integrate line intensity times sensor response across its passband."""
    if intensity <= 0:
        return 0.0
    wavelengths = np.linspace(center_nm - 4 * bandwidth_nm, center_nm + 4 * bandwidth_nm, 401)
    profile = super_gaussian_profile(wavelengths, center_nm, bandwidth_nm)
    line_profile = intensity * profile / np.trapezoid(profile, wavelengths)
    response = interpolate_sensor_response(channel, wavelengths)
    return float(np.trapezoid(line_profile * response, wavelengths))


def sensor_channel_signals(
    intensities: dict[str, float],
    use_sensor_response: bool = False,
    bandwidth_nm: float = 6.0,
    white_continuum: float = 0.0,
) -> np.ndarray:
    """Return the summed R, G and B signals before display formatting."""
    rgb = np.zeros(3)
    for name, intensity in intensities.items():
        rgb += line_channel_signals(name, intensity, use_sensor_response, bandwidth_nm)
    rgb += continuum_channel_signals(white_continuum, use_sensor_response)
    return rgb


def line_channel_signals(
    name: str,
    intensity: float,
    use_sensor_response: bool = False,
    bandwidth_nm: float = 6.0,
) -> np.ndarray:
    """Return one line's R, G and B contributions before normalization."""
    if intensity <= 0:
        return np.zeros(3)
    if use_sensor_response:
        return np.array([
            integrated_sensor_signal(
                channel,
                CHANNELS[name]["wavelength_nm"],
                bandwidth_nm,
                intensity,
            )
            for channel in ("RED", "GREEN", "BLUE")
        ])
    center_nm = CHANNELS[name]["wavelength_nm"]
    wavelengths = np.linspace(center_nm - 4 * bandwidth_nm, center_nm + 4 * bandwidth_nm, 401)
    profile_shape = super_gaussian_profile(wavelengths, center_nm, bandwidth_nm)
    profile = intensity * profile_shape / np.trapezoid(profile_shape, wavelengths)
    spectral_rgb = np.array([wavelength_to_rgb_channels(wavelength) for wavelength in wavelengths])
    spectral_rgb /= np.maximum(spectral_rgb.sum(axis=1, keepdims=True), 1e-12)
    return np.trapezoid(profile[:, None] * spectral_rgb, wavelengths, axis=0)


def sensor_display_values(
    intensities: dict[str, float],
    bandwidth_nm: float,
    bit_depth: int,
    normalize_to_max: bool = False,
    white_continuum: float = 0.0,
) -> np.ndarray:
    """Convert integrated sensor signals to relative display-code values.

    Without maximum normalization, 100 intensity units correspond to full scale
    before clipping; this is an explicit visualization reference, not ADC calibration.
    """
    signals = sensor_channel_signals(intensities, True, bandwidth_nm, white_continuum)
    full_scale = (1 << bit_depth) - 1
    if signals.max() <= 0:
        return np.zeros(3)
    if normalize_to_max:
        display_values = signals / signals.max() * full_scale
    else:
        display_values = signals / DISPLAY_REFERENCE_INTENSITY * full_scale
    return np.rint(np.clip(display_values, 0, full_scale))


def ideal_sensor_color(
    intensities: dict[str, float],
    use_sensor_response: bool = False,
    bandwidth_nm: float = 6.0,
    normalize_to_max: bool = False,
    bit_depth: int = 8,
    white_continuum: float = 0.0,
) -> str:
    """Mix ideal spectral colors or integrated sensor-channel signals."""
    rgb = sensor_channel_signals(intensities, use_sensor_response, bandwidth_nm, white_continuum)
    if use_sensor_response:
        full_scale = (1 << bit_depth) - 1
        display_values = sensor_display_values(
            intensities, bandwidth_nm, bit_depth, normalize_to_max, white_continuum
        )
        rgb = display_values / full_scale * 255
    elif rgb.max() > 0:
        rgb = rgb / rgb.max() * 255
    return "rgb({:.0f}, {:.0f}, {:.0f})".format(*rgb)


def super_gaussian_profile(
    wavelength_nm: np.ndarray | float,
    center_nm: float,
    bandwidth_nm: float,
    order: int = 4,
) -> np.ndarray:
    """Return a normalized super-Gaussian with the requested FWHM."""
    wavelength = np.asarray(wavelength_nm, dtype=float)
    if bandwidth_nm <= 0:
        raise ValueError("bandwidth_nm must be positive")
    if order <= 0:
        raise ValueError("order must be positive")
    scaled_distance = 2 * (wavelength - center_nm) / bandwidth_nm
    return np.exp(-np.log(2) * np.abs(scaled_distance) ** order)


