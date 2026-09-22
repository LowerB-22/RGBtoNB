"""Compact, explainable models for a Sony IMX571 narrowband exposure."""

from dataclasses import dataclass

import numpy as np

CHANNELS = {
    "H-alpha": {"wavelength_nm": 656.3, "bandwidth_nm": 6.0, "color": "#ef665b"},
    "O III": {"wavelength_nm": 500.7, "bandwidth_nm": 6.0, "color": "#56c6c8"},
    "S II": {"wavelength_nm": 672.4, "bandwidth_nm": 6.0, "color": "#f3bd52"},
}


@dataclass(frozen=True)
class SensorConfig:
    """Relevant nominal characteristics of the back-illuminated IMX571."""

    width_px: int = 6248
    height_px: int = 4176
    pixel_um: float = 3.76
    full_well_e: float = 80_000
    read_noise_e: float = 1.5
    dark_current_e_s: float = 0.002


def sensor_qe(wavelength_nm: np.ndarray | float) -> np.ndarray:
    """Approximate quantum efficiency curve for a colour IMX571 matrix."""
    wavelength = np.asarray(wavelength_nm, dtype=float)
    qe = 0.28 + 0.37 * np.exp(-0.5 * ((wavelength - 610.0) / 150.0) ** 2)
    return np.clip(qe, 0.12, 0.66)


def atmospheric_transmission(wavelength_nm: np.ndarray | float, airmass: float) -> np.ndarray:
    """A smooth approximation of extinction for an illustrative comparison."""
    wavelength = np.asarray(wavelength_nm, dtype=float)
    extinction_mag = airmass * (0.18 * (550.0 / wavelength) ** 1.3)
    return 10 ** (-0.4 * extinction_mag)


def channel_signal(
    flux_photons_s: float,
    wavelength_nm: float,
    bandwidth_nm: float,
    exposure_s: float,
    aperture_mm: float,
    airmass: float,
    sensor: SensorConfig,
    dark_temperature_c: float,
) -> dict[str, float]:
    """Estimate electrons, shot noise, and SNR for one narrowband channel."""
    collecting_area_m2 = np.pi * (aperture_mm / 2000.0) ** 2
    passband_factor = bandwidth_nm / 6.0
    incoming = flux_photons_s * collecting_area_m2 * passband_factor * exposure_s
    electrons = incoming * float(sensor_qe(wavelength_nm)) * float(
        atmospheric_transmission(wavelength_nm, airmass)
    )
    thermal_factor = 2 ** ((dark_temperature_c - 20.0) / 6.0)
    dark_electrons = sensor.dark_current_e_s * thermal_factor * exposure_s
    noise = np.sqrt(max(electrons + dark_electrons + sensor.read_noise_e**2, 1e-12))
    return {
        "electrons": float(electrons),
        "dark_electrons": float(dark_electrons),
        "noise": float(noise),
        "snr": float(electrons / noise),
        "qe": float(sensor_qe(wavelength_nm)),
        "transmission": float(atmospheric_transmission(wavelength_nm, airmass)),
    }


def simulate_channels(
    exposure_s: float = 300.0,
    aperture_mm: float = 80.0,
    airmass: float = 1.3,
    fluxes: dict[str, float] | None = None,
    dark_temperature_c: float = 0.0,
    sensor: SensorConfig | None = None,
) -> dict[str, dict[str, float]]:
    """Return modelled channel measurements for the current observing setup."""
    sensor = sensor or SensorConfig()
    fluxes = fluxes or {"H-alpha": 180.0, "O III": 125.0, "S II": 90.0}
    return {
        channel: channel_signal(
            fluxes[channel],
            values["wavelength_nm"],
            values["bandwidth_nm"],
            exposure_s,
            aperture_mm,
            airmass,
            sensor,
            dark_temperature_c,
        )
        for channel, values in CHANNELS.items()
    }
