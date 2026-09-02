import numpy as np
from cobaya.theory import Theory

class CustomBackgroundFluid(Theory):
    # Define the parameters that your custom framework introduces to the MCMC
    params = {
        "alpha_fluid": None,  # Example coupling parameter
        "z_decay": None       # Example transition redshift scale
    }

    def initialize(self):
        """ Initializes internal look-up tables and constants. """
        self.c = 299792.458  # km/s
        
    def initialize_with_provider(self, provider):
        """ Links this module to other active theory components. """
        self.provider = provider

    def get_can_provide_params(self):
        """ Informs the sampler which derived parameters this module calculates. """
        return ["Omega_fluid_effective"]

    def calculate(self, state, want_derived=True, **params_values):
        """
        Executes the explicit expansion math at each parameter coordinate step.
        """
        # 1. Extract the live parameter coordinates from the sampler step
        alpha = params_values["alpha_fluid"]
        z_c = params_values["z_decay"]
        
        # Pull standard background metrics from the primary Boltzmann engine
        H0 = self.provider.get_param("H0")
        Om0 = self.provider.get_param("Omega_m")
        
        # 2. Formulate your custom background integration grid
        z_grid = np.linspace(0.0, 5.0, 500)
        
        # CONCEPTUAL MATHEMATICAL FUNCTION: Replace with your exact function
        # e.g., an early or late-time dark fluid energy injection step:
        fluid_injection = alpha * np.exp(-((z_grid - z_c) ** 2) / 0.5)
        
        # Compute the modified Hubble expansion parameter H(z) directly
        H_z_custom = H0 * np.sqrt(Om0 * (1.0 + z_grid)**3 + (1.0 - Om0) + fluid_injection)
        
        # 3. Derive the updated comoving distance ladder grid chi(z)
        # This breaks the standard distance mapping to confront the DESI AP splits
        chi_grid = np.zeros_like(z_grid)
        for i in range(1, len(z_grid)):
            # Perform instantaneous trapezoidal line-of-sight integration
            chi_grid[i] = chi_grid[i-1] + np.trapz(self.c / H_z_custom[i-1:i+1], z_grid[i-1:i+1])

        # 4. Pack the evaluated arrays into the state dictionary for the provider
        state["z_grid"] = z_grid
        state["H_z"] = H_z_custom
        state["chi_grid"] = chi_grid
        
        if want_derived:
            state["derived"] = {"Omega_fluid_effective": np.max(fluid_injection)}

    def get_custom_background(self):
        """ Public getter function for the Stage-IV likelihood projection loops. """
        return self._current_state["z_grid"], self._current_state["H_z"], self._current_state["chi_grid"]
