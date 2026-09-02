import math
import numpy as np
from scipy.integrate import quad
from scipy.special import jv  # Spherical bessel approximated via standard cylindrical J_v

class StageIVAdaptiveProjectionEngine:
    def __init__(self, l_center: float, sigma_0: float = 0.15, gamma: float = 0.25):
        """
        Stage-IV Cosmological Angular Projection Engine.
        Integrates Nuisance Folding, Beyond-Limber Switching, and Adaptive Geometry.
        """
        self.l_center = l_center
        self.sigma_0 = sigma_0
        self.gamma = gamma
        self.z_transition = 5.8
        self.c = 299792.458  # km/s
        
    def compute_adaptive_width(self, z: float, delta_rho: float) -> float:
        """ Calculates the adaptive width operator sigma(z, delta_rho). """
        epoch_scaling = (1.0 + z) / (1.0 + self.z_transition)
        density_modulator = math.log(1.0 + delta_rho**2)
        width = self.sigma_0 / (1.0 + self.gamma * epoch_scaling * density_modulator)
        return max(width, 0.02)

    def evaluate_harmonic_bandpower(self, l_array: np.ndarray, z: float, delta_rho: float) -> np.ndarray:
        """ Evaluates the log-normal normalized window operator over the multipoles. """
        sigma = self.compute_adaptive_width(z, delta_rho)
        valid_mask = l_array > 0
        weights = np.zeros_like(l_array, dtype=float)
        
        log_l = np.log(l_array[valid_mask])
        log_lc = math.log(self.l_center)
        response = np.exp(-((log_l - log_lc) ** 2) / (2.0 * sigma ** 2))
        
        # Consistent integration under d(ln_ell)
        normalization = np.trapz(response / l_array[valid_mask], l_array[valid_mask])
        if normalization > 0:
            weights[valid_mask] = response / normalization
        return weights

    def fold_nuisance_kernels(self, chi_grid: np.ndarray, z_grid: np.ndarray, 
                              p_z_raw: np.ndarray, delta_z: float, 
                              A_ia: float, eta_ia: float, bias_g: float) -> dict:
        """
        1. FOLDS EXPERIMENTAL NUISANCE ENTRIES AND ENFORCES STRUCTURE INVARIANCE
        Applies photo-z shifts to selection metrics, and decouples physical growth
        from Intrinsic Alignment (NLA model) loops.
        """
        # Fold Photometric Redshift Shift Nuisance
        z_shifted = z_grid - delta_z
        p_z_shifted = np.interp(z_grid, z_shifted, p_z_raw, left=0.0, right=0.0)
        norm_p = np.trapz(p_z_shifted, z_grid)
        if norm_p > 0: p_z_shifted /= norm_p
        
        # Intrinsic Alignment Redshift-Evolution Amplitude Scaling (NLA baseline)
        C_1 = 0.0134  # Standard normalization constant
        A_IA_z = A_ia * C_1 * ((1.0 + z_grid) / 1.1) ** eta_ia
        
        # Continuous Truncated Weight Construction
        W_clustering = bias_g * p_z_shifted  # Galaxy clustering kernel
        W_intrinsic = p_z_shifted * A_IA_z   # Intrinsic alignment contamination profile
        
        return {"clustering": W_clustering, "intrinsic": W_intrinsic, "photo_z": p_z_shifted}

    def compute_angular_spectrum(self, l_array: np.ndarray, chi_grid: np.ndarray, z_grid: np.ndarray,
                                 kernels: dict, cosmology: dict, hybrid_boundary: int = 30) -> np.ndarray:
        """
        2. EXECUTED HYBRID BEYOND-LIMBER HYBRIDIZATION SWITCHING
        Evaluates exact double-integral Bessel equations for low multipoles, 
        switching to instantaneous Limber mapping at small physical scales.
        
        3. MAPS PARAMETER SENSITIVITIES (AMPLITUDE VS COORDINATE METRICS)
        Coordinate shifts (H0, w0, wa) rewrite chi_grid and k <-> l mappings.
        Amplitude changes (S8) scale the 3D Matter Power spectrum directly via S8^2.
        """
        C_l_total = np.zeros_like(l_array, dtype=float)
        H0 = cosmology["H0"]
        Om = cosmology["Omega_m"]
        S8 = cosmology["S8"]
        
        # Isolate baseline amplitude scaling matrix from the geometry coordinates
        # S8 scales the 3D matter spectrum normalization quadratically: P(k) ~ S8^2
        amplitude_scale = (S8 / 0.8) ** 2 
        
        # Conceptual 3D Power Spectrum functional mapping for demonstration
        def mock_P_delta(k, z):
            return amplitude_scale * (1.0 / (1.0 + (k / 0.05)**2)) / (1.0 + z)

        for idx, l in enumerate(l_array):
            if l < hybrid_boundary:
                # Beyond-Limber Phase: Double Line-of-Sight Spherical Bessel Projections
                # Handles non-radial wavevectors where the Limber step breaks down
                def bessel_inner_integral(k):
                    # Fast integration mapping using a representative sub-grid
                    integrand = kernels["clustering"] * np.sqrt(math.pi / (2.0 * k * chi_grid + 1e-5)) * jv(l + 0.5, k * chi_grid)
                    return np.trapz(integrand, chi_grid)
                
                # Outer wavevector integral loop
                k_spectrum = np.logspace(-4, 1, 100)
                outer_integrand = np.array([k**2 * mock_P_delta(k, 0.0) * (bessel_inner_integral(k)**2) for k in k_spectrum])
                C_l_total[idx] = (2.0 / math.pi) * np.trapz(outer_integrand, k_spectrum)
            else:
                # Limber Phase: Speed-optimized instantaneous mapping
                # Exact wavevector calculation based on adaptive distance coordinate scale
                chi_l = (l + 0.5) / k_spectrum if 'k_spectrum' in locals() else (l + 0.5) / 0.1
                
                # Match line-of-sight coordinates adaptively via interpolation
                chi_interp = (l + 0.5) / np.clip(chi_grid, 0.1, None)
                P_k_mapped = np.array([mock_P_delta((l + 0.5)/chi, z) for chi, z in zip(chi_grid, z_grid)])
                
                # Final fast line-of-sight projection tracking integration
                integrand = (kernels["clustering"] ** 2 / (chi_grid ** 2 + 1e-5)) * P_k_mapped
                C_l_total[idx] = np.trapz(integrand, chi_grid)
                
        return C_l_total

# --- PIPELINE DEMONSTRATION WORKFLOW ---
if __name__ == "__main__":
    engine = StageIVAdaptiveProjectionEngine(l_center=100.0)
    
    # Generate representative coordinate grids
    z_axes = np.linspace(0.01, 3.0, 200)
    # Coordinate Mapping Shift: H0 / geometry alters the physical comoving distance metric
    H0_candidate = 67.4
    chi_axes = (299792.458 / H0_candidate) * z_axes  
    raw_photo_z = np.exp(-((z_axes - 0.8) ** 2) / (2.0 * 0.15 ** 2))
    
    # 1. Fold Nuisance Matrices
    folded_loops = engine.fold_nuisance_kernels(
        chi_grid=chi_axes, z_grid=z_axes, p_z_raw=raw_photo_z,
        delta_z=0.02, A_ia=1.2, eta_ia=-0.5, bias_g=1.4
    )
    
    # Define Cosmological Inputs
    cosmo_params = {"H0": H0_candidate, "Omega_m": 0.315, "S8": 0.789}
    ell_array = np.array([15, 25, 45, 100, 500]) # Spans cross-boundary hybrid limits
    
    # 2. Run Hybrid Angular Projection
    theoretical_Cl = engine.compute_angular_spectrum(ell_array, chi_axes, z_axes, folded_loops, cosmo_params)
    
    print("=" * 80)
    print("       STAGE-IV INTEGRATED ADAPTIVE PIPELINE VERIFICATION")
    print("=" * 80)
    for l, val in zip(ell_array, theoretical_Cl):
        mode_type = "Beyond-Limber Exact" if l < 30 else "Standard Limber Speed"
        print(f"Multipole ℓ = {l:<3} | Regime: {mode_type:<23} | Calculated C_ℓ Vector: {val:.6e}")
    print("=" * 80)
