# ==============================================================================
# Master Joint Likelihood Matrix
# Planck 2018 + DESI DR2 BAO + Pantheon+ + DES Y6 3×2pt + KiDS-Legacy
# Proper marginalization of Intrinsic Alignments (NLA) + Baryonic Feedback (HMcode)
# ==============================================================================

likelihood:
  # --------------------------------------------------------------------------
  # 1. Early-Universe Anchor: Planck 2018
  # --------------------------------------------------------------------------
  planck_2018_highl_plik.TTTEEE:
  planck_2018_lowl.TT:
  planck_2018_lowl.EE:
  planck_2018_lensing.baseline:

  # --------------------------------------------------------------------------
  # 2. Expansion History: DESI DR2 BAO (full stack)
  # --------------------------------------------------------------------------
  bao.desi_dr2:          # official Cobaya module (or bao.desi_dr2.desi_bao_all)

  # --------------------------------------------------------------------------
  # 3. Low-redshift distances: Pantheon+
  # --------------------------------------------------------------------------
  sn.pantheonplus:

  # --------------------------------------------------------------------------
  # 4. Late-Universe structure growth
  # --------------------------------------------------------------------------
  # DES Y6 3×2pt (cosmic shear + galaxy clustering + galaxy-galaxy lensing)
  des_y6.3x2pt:          # replace with actual public module name when released
    # data_file: des_y6_3x2pt_fiducial.dataset   # if custom
    # baryonic_feedback_model: hmcode

  # KiDS-Legacy cosmic shear
  kids_legacy.cosmic_shear:   # replace with actual public module name when released
    # data_file: kids_legacy_direct_shear.dataset
    # baryonic_feedback_model: hmcode

theory:
  camb:
    extra_args:
      lens_potential_accuracy: 2
      AccuracyBoost: 1.2
      halofit_version: mead2020   # required for consistent HMcode baryonic feedback

params:
  # ==========================================================================
  # Baseline cosmological parameters
  # ==========================================================================
  ombh2:
    prior: {min: 0.005, max: 0.1}
    ref: 0.02237
    proposal: 0.0001
    latex: \Omega_b h^2

  omch2:
    prior: {min: 0.001, max: 0.99}
    ref: 0.1200
    proposal: 0.001
    latex: \Omega_c h^2

  H0:
    prior: {min: 55.0, max: 85.0}
    ref: 67.36
    proposal: 0.4
    latex: H_0

  logA:
    prior: {min: 1.61, max: 3.91}
    ref: 3.044
    proposal: 0.001
    drop: true
    latex: \ln(10^{10} A_s)

  As:
    value: 'lambda logA: 1e-10 * np.exp(logA)'
    latex: A_s

  ns:
    prior: {min: 0.8, max: 1.2}
    ref: 0.9649
    proposal: 0.004
    latex: n_s

  tau:
    prior: {min: 0.01, max: 0.8}
    ref: 0.0544
    proposal: 0.006
    latex: \tau

  # ==========================================================================
  # Derived parameters
  # ==========================================================================
  Omega_m:
    latex: \Omega_m
  sigma8:
    latex: \sigma_8
  S8:
    derived: 'lambda sigma8, Omega_m: sigma8 * (Omega_m / 0.3)**0.5'
    latex: S_8

  # ==========================================================================
  # Intrinsic Alignments (NLA model) – CRITICAL
  # ==========================================================================
  A_IA:
    prior: {min: -5.0, max: 5.0}
    ref: 0.5
    proposal: 0.1
    latex: A_{\rm IA}

  eta_IA:                 # often called alpha_IA or eta_IA
    prior: {min: -5.0, max: 5.0}
    ref: 0.0
    proposal: 0.2
    latex: \eta_{\rm IA}

  # ==========================================================================
  # Baryonic Feedback (HMcode-2020)
  # ==========================================================================
  logT_AGN:
    prior: {min: 7.0, max: 9.0}
    ref: 7.8
    proposal: 0.05
    latex: \log_{10}(T_{\rm AGN}/{\rm K})

sampler:
  mcmc:
    burn_in: 0
    max_tries: 10000
    covmat: auto
    Rminus1_stop: 0.01          # tighter for production
    Rminus1_cl_stop: 0.15
    output_every: 30s

output: chains/full_joint_universe_mcmc
