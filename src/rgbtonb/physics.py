"""Small spectral-profile helpers for the narrowband visualizer."""

import numpy as np


def wavelength_to_rgb(wavelength_nm: float) -> str:
    """Approximate a visible spectral wavelength as an sRGB color."""
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

    rgb = [round(255 * (channel * attenuation) ** 0.8) for channel in (red, green, blue)]
    return "#{:02x}{:02x}{:02x}".format(*rgb)


CHANNELS = {
    "H-alpha": {"wavelength_nm": 656.3, "color": wavelength_to_rgb(656.3)},
    "O III": {"wavelength_nm": 500.7, "color": "#00d98a"},
    "S II": {"wavelength_nm": 672.4, "color": wavelength_to_rgb(672.4)},
    "He II": {"wavelength_nm": 468.6, "color": wavelength_to_rgb(468.6)},
}


def ideal_sensor_color(intensities: dict[str, float]) -> str:
    """Mix line colors with unchanged intensities for an ideal 100% sensor."""
    rgb = np.zeros(3)
    for name, intensity in intensities.items():
        color = CHANNELS[name]["color"]
        rgb += np.array([int(color[index:index + 2], 16) for index in (1, 3, 5)]) * intensity
    if rgb.max() > 0:
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


