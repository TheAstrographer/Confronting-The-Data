def H_jcrin(z, H0_base=70.0, torque=3.17, tau=5.8, **standard_args):
    H_lcdm = standard_H_lcdm(z, H0=H0_base, **standard_args)
    return H_lcdm + torque * np.exp(-z / tau)
