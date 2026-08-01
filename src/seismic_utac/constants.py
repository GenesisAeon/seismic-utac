import math

SIGMA: float = 2.2
GAMMA_SEISMIC: float = 0.200
GAMMA_SEISMIC_TOL: float = 0.03
B_CRITICAL: float = 1.0
B_MAX: float = 2.5
B_SOC_TYPICAL: float = 1.7  # crustal SOC b-value -> Gamma ~= 0.200
K_ENERGY: float = 1e17  # Joules normalization
R_LOADING: float = 0.05  # tectonic loading rate per year
OMORI_P: float = 1.1
OMORI_C: float = 0.1
M_MIN_COMPLETENESS: float = 2.5
LOG10_E: float = math.log10(math.e)  # = 1/ln(10) ~= 0.4343
PACKAGE_ID: int = 23
PACKAGE_NAME: str = "seismic-utac"
ZENODO_DOI: str = "10.5281/zenodo.20842889"
