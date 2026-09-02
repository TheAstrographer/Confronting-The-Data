import math
import numpy as np

# ==============================================================================
# 1. FUNDAMENTAL COSMOLOGICAL PARAMETERS & TENSIONS
# ==============================================================================

def equation_s8(sigma_8: float, omega_m: float) -> float:
    """
    The structure growth amplitude parameter.
    Balances the clumpiness degeneracy between sigma_8 and Omega_m.
    """
    return sigma_8 * math.sqrt(omega_m / 0.3)


def equation_omega_m(ombh2: float, omch2: float, H0: float) -> float:
    """
    Total non-relativistic matter density parameter fraction.
    Derived from physical baryon and cold dark matter densities.
    """
    h = H0 / 100.0
    return (ombh2 + omch2) / (h ** 2)


def equation_primordial_amplitude(logA: float) -> float:
    """
    Primordial scalar perturbation power spectrum amplitude (As).
    Transforms the log-sampled MCMC parameter into physical initial conditions.
    """
    return 1e-10 * math.exp(logA)


# ==============================================================================
# 2. BACKGROUND EXPANSION HISTORY & DISTANCES
# ==============================================================================

def equation_hubble_expansion(z: np.ndarray, H0: float, omega_m: float, 
                              alpha_fluid: float, z_decay: float) -> np.ndarray:
    """
    Modified Hubble expansion profile H(z).
    Integrates standard matter/lambda components with a custom fluid injection profile.
    """
    # Logarithmic custom dark energy fluid step track
    omega_fluid = alpha_fluid * np.exp(-((z - z_decay) ** 2) / 0.5)
    
    # Core Friedmann background equation
    return H0 * np.sqrt(omega_m * (1.0 + z)**3 + (1.0 - omega_m) + omega_fluid)


def equation_comoving_distance(z_grid: np.ndarray, H_z: np.ndarray, c: float = 299792.458) -> np.ndarray:
    """
    Line-of-sight comoving distance integration grid chi(z).
    Solved via numerical trapezoidal integrations inside the solver lifecycle loop.
    """
    chi_grid = np.zeros_like(z_grid, dtype=float)
    for i in range(1, len(z_grid)):
        dz = z_grid[i] - z_grid[i-1]
        integrand_avg = 0.5 * (c / H_z[i-1] + c / H_z[i])
        chi_grid[i] = chi_grid[i-1] + (integrand_avg * dz)
    return chi_grid


def equation_transverse_distance(chi: np.ndarray) -> np.ndarray:
    """
    Transverse comoving distance D_M(z).
    Identical to line-of-sight comoving distance assuming zero spatial curvature (Omega_k = 0).
    """
    return chi


def equation_radial_hubble_distance(H_z: np.ndarray, c: float = 299792.458) -> np.ndarray:
    """
    Radial Hubble distance metric D_H(z).
    Maps expansion parameters directly to line-of-sight spectroscopic BAO frames.
    """
    return c / H_z


def equation_luminosity_distance(chi: np.ndarray, z_grid: np.ndarray) -> np.ndarray:
    """
    Luminosity distance scale d_L(z).
    The geometric tracker required to optimize Pantheon+ Type Ia supernova likelihood matrices.
    """
    return chi * (1.0 + z_grid)


# ==============================================================================
# 3. WEAK LENSING KERNELS & PROJECTIONS
# ==============================================================================

def equation_cosmic_shear_kernel(chi: np.ndarray, z: np.ndarray, n_z: np.ndarray, 
                                 H0: float, omega_m: float, c: float = 299792.458) -> np.ndarray:
    """
    Lensing efficiency weight kernel W_gamma(chi) for a tomographic bin.
    Integrates mass distributions between the observer and background source galaxies.
    """
    W_g = np.zeros_like(chi)
    # Pre-factor from the Poisson equation mapping mass to potentials
    prefactor = (3.0 * omega_m * (H0 ** 2)) / (2.0 * (c ** 2))
    
    # Scale factor array a(chi)
    a_chi = 1.0 / (1.0 + z)
    
    for i in range(len(chi)):
        # Inner efficiency integral: bounds from current chi to edge of the universe
        integrand = n_z[i:] * (chi[i:] - chi[i]) / np.clip(chi[i:], 1e-5, None)
        inner_integral = np.trapz(integrand, chi[i:])
        W_g[i] = prefactor * (chi[i] / a_chi[i]) * inner_integral
    return W_g


def equation_galaxy_clustering_kernel(n_z: np.ndarray, H_z: np.ndarray, bias_g: np.ndarray) -> np.ndarray:
    """
    Galaxy positioning weight kernel W_delta_g(chi) for a foreground lens.
    Maps galaxy spatial shells modulated by their local linear galaxy tracer bias b(z).
    """
    return bias_g * n_z * H_z


def equation_cmb_lensing_kernel(chi: np.ndarray, z: np.ndarray, chi_cmb: float, 
                                H0: float, omega_m: float, c: float = 299792.458) -> np.ndarray:
    """
    CMB lensing convergence efficiency kernel W_kappa(chi).
    Extends backward as a single, un-binned envelope to the surface of last scattering.
    """
    prefactor = (3.0 * omega_m * (H0 ** 2)) / (2.0 * (c ** 2))
    a_chi = 1.0 / (1.0 + z)
    return prefactor * (chi / a_chi) * ((chi_cmb - chi) / chi_cmb)


def equation_limber_angular_spectrum(l: float, chi: np.ndarray, W_x: np.ndarray, W_y: np.ndarray, 
                                     z: np.ndarray, S8: float) -> float:
    """
    Limber angular cross-spectrum projection C_ell.
    Projects 3D power spectra into 2D observables at high multipoles by setting k_parallel = 0.
    """
    # Map wavevector scale: k = (ell + 0.5) / chi
    k_mapped = (l + 0.5) / np.clip(chi, 1e-5, None)
    
    # Conceptual isotropic matter power spectrum profile P(k, z) proportional to S8^2
    P_k_z = ((S8 / 0.8)**2) * (1.0 / (1.0 + (k_mapped / 0.05)**2)) / (1.0 + z)
    
    # Line-of-sight angular profile projection
    integrand = (W_x * W_y / (chi**2 + 1e-8)) * P_k_z
    return float(np.trapz(integrand, chi))


def equation_beyond_limber_exact(l: int, chi: np.ndarray, W_x: np.ndarray, 
                                  k_spectrum: np.ndarray, P_k_z0: np.ndarray) -> float:
    """
    Exact Non-Limber projection equation using spherical Bessel transformations.
    Preserves non-radial wavevector geometry for large angular scales (ell < 30).
    """
    # Cylindrical Bessel helper function to approximate SciPy's jv
    def bessel_j(order, x):
        if x < 1e-4: return 0.0
        theta = np.linspace(0, math.pi, 60)
        return np.trapz(np.cos(order * theta - x * np.sin(theta)), theta) / math.pi

    bessel_inner = np.zeros_like(k_spectrum)
    for k_idx, k in enumerate(k_spectrum):
        # Convert cylindrical J_v to spherical bessel j_l via factor adjustment
        sph_bessel_factor = np.sqrt(math.pi / (2.0 * k * chi + 1e-8))
        bessel_args = k * chi
        j_l = np.array([bessel_j(l + 0.5, arg) for arg in bessel_args])
        
        bessel_inner[k_idx] = np.trapz(W_x * sph_bessel_factor * j_l, chi)
        
    outer_integrand = (k_spectrum ** 2) * P_k_z0 * (bessel_inner ** 2)
    return float((2.0 / math.pi) * np.trapz(outer_integrand, k_spectrum))


# ==============================================================================
# 4. SYSTEMATICS & NUISANCE FIELDS
# ==============================================================================

def equation_photo_z_shift(z_grid: np.ndarray, n_z_raw: np.ndarray, delta_z: float) -> np.ndarray:
    """
    Photometric redshift shift systemic distortion.
    Folds camera offsets directly into the shape profiles via coordinate translation.
    """
    z_shifted = z_grid - delta_z
    n_z_shifted = np.interp(z_grid, z_shifted, n_z_raw, left=0.0, right=0.0)
    norm = np.trapz(n_z_shifted, z_grid)
    return n_z_shifted / norm if norm > 0 else n_z_shifted


def equation_nla_intrinsic_alignment(z: np.ndarray, A_ia: float, eta_ia: float) -> np.ndarray:
    """
    Non-Linear Linear Alignment (NLA) intrinsic galaxy scaling.
    Models fake shear alignment under local gravitational tidal fields.
    """
    C_1 = 0.0134  # Normalized baseline reference constant
    z_0 = 1.1     # Pivot redshift boundary
    return A_ia * C_1 * ((1.0 + z) / z_0) ** eta_ia


def equation_adaptive_kernel_width(z: float, delta_rho: float, sigma_0: float = 0.15, gamma: float = 0.25) -> float:
    """
    Environment-dependent sharpening operator standard deviation (sigma).
    Nrows harmonic filter widths under highly non-linear or feedback-heavy structures.
    """
    epoch_scaling = (1.0 + z) / (1.0 + 5.8)
    density_modulator = math.log(1.0 + delta_rho**2)
    width = sigma_0 / (1.0 + gamma * epoch_scaling * density_modulator)
    return max(width, 0.02)


def equation_harmonic_bandpower_window(l_array: np.ndarray, l_center: float, z: float, delta_rho: float) -> np.ndarray:
    """
    Log-space bandpower filtering window W_band(ell).
    Enforces invariant integration constraints across the parameter grid under d(ln_ell).
    """
    sigma = equation_adaptive_kernel_width(z, delta_rho)
    valid_mask = l_array > 0
    weights = np.zeros_like(l_array, dtype=float)
    
    log_l = np.log(l_array[valid_mask])
    log_lc = math.log(l_center)
    response = np.exp(-((log_l - log_lc) ** 2) / (2.0 * (sigma ** 2)))
    
    # Standard log-space normalization metric step
    norm = np.trapz(response / l_array[valid_mask], l_array[valid_mask])
    if norm > 0:
        weights[valid_mask] = response / norm
    return weights


# ==============================================================================
# 5. MULTI-PROBE LIKELIHOOD MATRIX ARRAYS
# ==============================================================================

def equation_joint_log_likelihood(ln_L_planck: float, ln_L_desi: float, 
                                  ln_L_pantheon: float, ln_L_desy6: float, ln_L_kids: float) -> float:
    """
    The multivariate 5-probe joint log-likelihood vector summation.
    Calculates the combined score across independent data channels inside the MCMC chain.
    """
    return ln_L_planck + ln_L_desi + ln_L_pantheon + ln_L_desy6 + ln_L_kids


def equation_anisotropic_ap_chi2(obs_DM: float, obs_DH: float, theo_DM: float, theo_DH: float) -> float:

    """
    Multivariate Alcock-Paczynski anisotropic chi2 residual mapping.
    Evaluates transverse vs radial coordinate offsets against an inverse covariance matrix.
    """
    # Example localized inverse covariance matrix coupling radial and transverse variances
    inv_covariance = np.array([[120.0, -15.0], [-15.0, 95.0]])

    residuals = np.array([obs_DM - theo_DM, obs_DH - theo_DH])
    return float(residuals.T @ inv_covariance @ residuals)


def equation_profile_delta_chi2(chi2_custom_model: float, chi2_lcdm_baseline: float) -> float:
   
    """
    Profile likelihood Delta Chi-Square calculation.
    Reports the absolute improvement or penalty of a new theory relative to standard LCDM.
    """
    return chi2_custom_model - chi2_lcdm_baseline
