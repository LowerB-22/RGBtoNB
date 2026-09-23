# RGBtoNB: A Physically Interpretable Narrowband-to-RGB Spectral Visualization Model

## Abstract

RGBtoNB is an interactive spectral visualization model for four astronomical emission lines: H-alpha at 656.3 nm, O III at 500.7 nm, S II at 672.4 nm, and He II at 468.6 nm. The application represents each line by a normalized super-Gaussian transmission profile and combines line emission with an optional flat continuum. The resulting signal is projected into three RGB channels either with an ideal wavelength-independent detector or with interpolated red, green, and blue response curves for a Sony IMX571 one-shot-colour sensor.

The central quantity is the channel signal obtained by integrating spectral intensity multiplied by channel sensitivity over wavelength. This formulation makes emission-line width, continuum emission, detector response, and additive line-of-sight components explicit. The model is intended for qualitative instrument and visualization studies. It is not a calibrated photometric reduction pipeline, a radiative-transfer solver, or a substitute for measured filter and detector response data.

## 1. Introduction

Narrowband astronomical imaging isolates emission features whose relative strengths encode information about ionization, temperature, density, composition, shocks, extinction, and geometry. A colour image, however, compresses a wavelength-dependent spectrum into a small number of display channels. This compression is useful for visualization but is intrinsically non-injective: distinct spectra can produce identical or nearly identical RGB responses.

RGBtoNB provides an explicit, inspectable model for this compression. Its purpose is not to infer a unique physical state from an RGB colour, but to show how selected emission lines, a continuum, a filter passband, and an optional sensor response combine before display rendering.

The current implementation exposes the following controls:

- independent intensity controls for H-alpha, O III, S II, and He II;
- a common emission-line FWHM from 1 to 10 nm;
- an optional white-continuum intensity;
- an optional IMX571 spectral response;
- optional maximum normalization for display output;
- display code depths of 8, 10, 12, or 16 bit.

## 2. Scope and Assumptions

The model uses the following assumptions:

1. Each emission line is represented by a symmetric super-Gaussian profile.
2. The reported line intensity is an integrated line intensity. The profile is normalized to unit area before multiplication by this intensity.
3. The continuum is spectrally flat across 430-710 nm and its slider value represents its integrated intensity over that interval.
4. Line and continuum signals add linearly at the detector.
5. The ideal detector has unit sensitivity over the modeled wavelength interval.
6. The optional sensor model uses the red, green, and blue response curves supplied in `sensor_data/Sony_IMX571.json`.
7. The supplied sensor curves are interpolated smoothly between tabulated samples, clipped to the physical interval $[0,1]$, and set to zero outside their tabulated wavelength range.
8. The RGB display rectangle is a visualization of the computed channel signals, not a calibrated representation of emitted radiance or detector counts.

No atmospheric transmission, optical throughput, quantum efficiency uncertainty, photon noise, read noise, dark current, saturation model, Bayer demosaicing, extinction correction, or radiative-transfer calculation is currently included.

## 3. Spectral Model

### 3.1 Emission-line centers

The modeled line centers are:

| Line | Center wavelength |
|---|---:|
| He II | 468.6 nm |
| O III | 500.7 nm |
| H-alpha | 656.3 nm |
| S II | 672.4 nm |

These are representative narrowband features. In particular, the implementation treats O III as a single line at 500.7 nm and S II as a single representative feature at 672.4 nm. Real filters and nebular spectra may contain additional nearby components.

### 3.2 Super-Gaussian profile

For a line centered at $\lambda_0$ with full width at half maximum $B$, the unnormalized profile is

$$
P(\lambda;\lambda_0,B,n)
=\exp\left[-\ln(2)\left|\frac{2(\lambda-\lambda_0)}{B}\right|^n\right],
$$

where the current implementation uses order $n=4$. By construction,

$$
P(\lambda_0 \pm B/2)=\frac{1}{2}.
$$

The normalized profile is

$$
\widetilde{P}(\lambda)
=\frac{P(\lambda)}{\int P(\lambda)\,d\lambda}.
$$

For a line intensity $L_i$, the spectral line contribution is therefore

$$
I_i(\lambda)=L_i\widetilde{P}_i(\lambda).
$$

This normalization gives the line-width slider a physically interpretable role: changing the line width changes the distribution and the sensor-weighted result, while preserving the integrated line intensity before detector weighting. It is not a model of filter transmission.

### 3.3 Continuum

The continuum is modeled as a flat spectrum over

$$
[\lambda_{\min},\lambda_{\max}]=[430,710]\,\mathrm{nm}.
$$

For continuum intensity $C$, the spectral density is

$$
I_C(\lambda)=\frac{C}{\lambda_{\max}-\lambda_{\min}}.
$$

Consequently,

$$
\int_{430\,\mathrm{nm}}^{710\,\mathrm{nm}} I_C(\lambda)\,d\lambda=C.
$$

Line and continuum sliders thus share an integrated-intensity scale. For example, a line slider value of 12 and a continuum slider value of 12 represent equal total modeled photon contributions before channel sensitivity is applied.

## 4. Detector and Channel Model

Let $S_c(\lambda)$ denote the sensitivity of detector channel $c\in\{R,G,B\}$. The channel signal for a spectrum $I(\lambda)$ is

$$
Q_c=\int I(\lambda)S_c(\lambda)\,d\lambda.
$$

For a set of emission lines and continuum,

$$
I(\lambda)=\sum_i L_i\widetilde{P}_i(\lambda)+I_C(\lambda),
$$

and therefore

$$
Q_c=\sum_i\int L_i\widetilde{P}_i(\lambda)S_c(\lambda)\,d\lambda
+\int I_C(\lambda)S_c(\lambda)\,d\lambda.
$$

This is the primary signal equation used by the sensor-enabled model.

### 4.1 Ideal detector

In the idealized mode, the detector sensitivity is wavelength-independent. For the continuum, the total continuum contribution is distributed equally among the three RGB channels. For emission lines, the wavelength-dependent visible-spectrum RGB representation is normalized channel-wise so that the RGB contribution at each wavelength preserves the line's integrated intensity.

This ideal RGB representation is a display-space approximation. It should not be interpreted as a physical Bayer response.

### 4.2 Sony IMX571 response

When sensor response is enabled, the application loads the tabulated RED, GREEN, and BLUE curves from `sensor_data/Sony_IMX571.json`. Each response curve is sorted by wavelength, duplicate wavelength samples are removed, and values are interpolated with a cubic Hermite construction. The resulting response is clipped to $[0,1]$ and set to zero outside the tabulated range; no unmeasured edge response is extrapolated.

For each line and sensor channel, the code evaluates

$$
Q_{c,i}=\int L_i\widetilde{P}_i(\lambda)S_c(\lambda)\,d\lambda.
$$

For the flat continuum,

$$
Q_{c,C}=\int_{430}^{710} I_C(\lambda)S_c(\lambda)\,d\lambda.
$$

The total channel signal is

$$
Q_c=\sum_i Q_{c,i}+Q_{c,C}.
$$

The response curves in the JSON file are treated as relative channel sensitivities. They are not converted into absolute electrons, quantum efficiency, or calibrated system throughput. No additional factor of $1/3$ is applied in sensor mode; each channel signal is the direct integral for that channel. The factor of $1/3$ in ideal mode only defines the equal three-channel display decomposition.

## 5. Display Representation

The application reports the normalized channel fractions

$$
I=Q_R+Q_G+Q_B,
\qquad
R/I=Q_R/I,
\qquad
G/I=Q_G/I,
\qquad
B/I=Q_B/I.
$$

These ratios are invariant under a common multiplicative scaling and describe chromatic composition rather than absolute brightness.

The optional maximum-normalization mode maps the largest display channel to the selected full-scale value. This is a visualization operation and deliberately discards absolute brightness. Without this mode, the display codes are proportional to the modeled integrated signal relative to an explicit reference intensity of 100 and are clipped at the selected full-scale value. This reference is a visualization convention, not a calibrated ADC or electron scale.

The application offers 8-, 10-, 12-, and 16-bit display-code scales. A browser RGB rectangle is nevertheless rendered through an 8-bit sRGB CSS colour. The reported higher-bit values are therefore diagnostic values, not proof that the browser or physical display is presenting 16-bit radiometric output.

## 6. Spectral Visualizations

The upper graph shows the emission-line profiles, the optional white continuum, the optional IMX571 response curves, and the optional wavelength-to-sRGB reference curves.

The lower spectral image is intended to resemble a slit-spectrograph strip. Emission lines appear at their wavelength positions with widths determined by the super-Gaussian profile. The continuum is rendered as a separate white component rather than being multiplied by the wavelength colour map. This distinction is important: a flat white continuum must not be converted into a rainbow background merely because wavelength-to-colour rendering is used for the lines.

The R/I versus G/I scatter plot shows the chromatic contribution of the individual lines, the continuum, the line-only aggregate, and the line-plus-continuum aggregate. The displacement between aggregate points visualizes how added continuum changes the resulting channel ratios.

## 7. Metamerism

The mapping from a spectrum to three channel signals is generally non-injective. With four independently variable line intensities and three RGB channels, the line-to-RGB response matrix is a $3\times4$ matrix. Even when its rank is three, its null space has dimension at least one.

Thus, distinct line-intensity vectors can produce identical RGB signals:

$$
A\mathbf{x}_1=A\mathbf{x}_2,
\qquad
\mathbf{x}_1\neq\mathbf{x}_2.
$$

The existence of a mathematical null space does not imply that arbitrary examples are astrophysically plausible. Real nebular line ratios are constrained by temperature, density, ionization parameter, elemental abundances, extinction, shocks, and geometry. However, line-of-sight superposition, continuum emission, unresolved spatial structure, and point-spread-function mixing increase the probability of near-metameric observations.

Accordingly, RGB equality should not be interpreted as spectral equality. The application is designed to make this loss of information visible, not to invert it uniquely.

## 8. Limitations

The following limitations are material for publication-quality interpretation:

- The line intensities are user-controlled and are not generated from a photoionization or shock model.
- Only one representative wavelength is used for each named feature.
- The emission-line profile is represented by an idealized super-Gaussian; the line-width control is not a measured filter-transmission curve.
- The IMX571 data are relative spectral response data and may not represent a complete camera system response.
- Optical throughput, atmospheric extinction, detector noise, exposure time, gain, saturation, and quantization noise are not modeled as physical measurements.
- The visible-spectrum `wavelength_to_rgb` function is an approximate display mapping and cannot reproduce monochromatic spectral perception exactly.
- The CSS colour rectangle is an 8-bit sRGB visualization even when 16-bit diagnostic codes are shown.
- The continuum is flat by assumption and does not represent a stellar, thermal, synchrotron, or scattered-light spectral energy distribution.

The model should therefore be described as an explanatory forward visualization model, not as a calibrated instrument simulator.

## 9. Reproducibility

Create the environment and install the pinned dependency ranges with:

```bash
uv venv
uv pip install -r requirements.txt
```

Run the tests with:

```bash
uv run pytest
```

Start the application with:

```bash
uv run streamlit run app.py --server.headless true --server.port 8513
```

The current test suite covers wavelength colour conversion, bounded and smooth sensor interpolation, integrated line signals, continuum contributions, bandwidth dependence, bit-depth conversion, and RGB ratio calculations.

## 10. Conclusions

RGBtoNB provides a transparent forward model for examining how narrowband emission lines and a flat continuum are transformed into RGB channel signals. Its central methodological choice is to integrate spectral intensity multiplied by channel sensitivity over wavelength. This makes line bandwidth, continuum contribution, detector response, and additive line-of-sight components explicit.

The model demonstrates both the usefulness and the ambiguity of RGB visualization. Sensor response and continuum emission can substantially change channel ratios, while different underlying spectra can remain indistinguishable after projection into three channels. These properties motivate retaining the spectral profiles and integrated channel signals alongside any rendered colour image.

## Data and Software Availability

The implementation, test suite, requirements, and Sony IMX571 response data are contained in this repository. The provenance URL embedded in the sensor JSON file should be cited separately when the sensor-response data are used in a publication.

## Suggested Citation

> RGBtoNB: A Physically Interpretable Narrowband-to-RGB Spectral Visualization Model, software and technical paper draft, 2026.
