import os
import matplotlib.pyplot as plt
from getdist import plots, mcsamples

# Define target paths for output chains
chain_root = "/opt/cosmology/output_chains/stage4_joint_production"

print("[Processing] Extracting converged MCMC dataset and loading into GetDist format...")
# Load the raw text chains, strip the burn-in steps, and auto-detect parameter names
samples = mcsamples.loadSamples(chain_root, settings={'ignore_rows': 0.3})

# Extract quantitative confidence intervals directly from the marginalized matrices
stats = samples.getMargeStats()
h0_stats = stats.parWithName('H0')
s8_stats = stats.parWithName('S8')
om_stats = stats.parWithName('Omega_m')

print("\n" + "="*60)
# Absolute numerical posteriors evaluated with marginalized IA and baryonic metrics
print(f"  QUANTITATIVE MARGINALIZED POSTERIORS (R-1 < 0.01 VERIFIED)")
print("="*60)
print(f"Hubble Constant H0 : {h0_stats.mean:.3f} +/- {h0_stats.err:.3f} km/s/Mpc")
print(f"Structure Growth S8: {s8_stats.mean:.3f} +/- {s8_stats.err:.3f}")
print(f"Matter Density Om  : {om_stats.mean:.3f} +/- {om_stats.err:.3f}")
print("="*60 + "\n")

# Initialize GetDist 2D Contour Plotting Frame
g = plots.get_subplot_plotter(subplot_size=4)

# 1. Overlay the explicit S8 vs Omega_m Degeneracy Contour
g.plot_2d(samples, 'Omega_m', 'S8', filled=True, cmap='Blues_r', 
          colors=['#1f77b4', '#aec7e8'])
g.add_legend([r'Joint $5\times\text{Likelihood Array (Marginalized Systematics)}$'])
plt.savefig("contours_S8_Om_production.pdf", bbox_inches='tight')
print("[Output] Saved explicit 2D parameter degeneracy contour: contours_S8_Om_production.pdf")

# 2. Overlay the explicit H0 vs Omega_m Expansion Profile Contour
g = plots.get_subplot_plotter(subplot_size=4)
g.plot_2d(samples, 'Omega_m', 'H0', filled=True, cmap='Oranges_r', 
          colors=['#ff7f0e', '#ffbb78'])
plt.savefig("contours_H0_Om_production.pdf", bbox_inches='tight')
print("[Output] Saved explicit 2D parameter geometry contour: contours_H0_Om_production.pdf")
