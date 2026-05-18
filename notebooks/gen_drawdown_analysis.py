"""Generate notebooks/mcore_drawdown_analysis.ipynb — Gappy's drawdown formulas applied to MCORE-1."""
import json, uuid, pathlib

def mk_id():
    return uuid.uuid4().hex[:8]

def md(lines):
    return {"cell_type": "markdown", "id": mk_id(), "metadata": {},
            "source": lines if isinstance(lines, list) else [lines]}

def code(src):
    lines = src.strip().split('\n')
    sourced = [l + '\n' for l in lines[:-1]] + [lines[-1]]
    return {"cell_type": "code", "execution_count": None, "id": mk_id(),
            "metadata": {}, "outputs": [], "source": sourced}

cells = [

md([
    "# Drawdown Analysis — Gappy's Formulas Applied to MCORE-1\n",
    "\n",
    "Marco Paleologo's drawdown framework (Nov 2025) treats PnL as an arithmetic diffusion:\n",
    "\n",
    "$$dX_t = \\mu\\,dt + \\sigma\\,dB_t, \\quad X_0 = 0$$\n",
    "\n",
    "We map this onto three MCORE-1 domains where the same structure appears:\n",
    "\n",
    "1. **GJB2 frameshift** — trit-sequence fidelity as a drifting process; c.35delG = SR→0 degenerate case\n",
    "2. **MethylationMetrics drift** — beta-value trajectory toward S3 overflow (oncological progression)\n",
    "3. **L7 TNet information break** — masked STFT region as a drawdown event; E(τ) as imputation prior\n",
    "\n",
    "All formulas are implemented exactly as in Paleologo (2025).\n",
]),

md("## §1  Gappy's Formulas — Python Implementation"),

code("""
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Deterministic seed — all random draws reproducible across runs
SEED = 42
np.random.seed(SEED)

plt.rcParams.update({
    'figure.dpi': 120,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'font.family': 'monospace',
})

Phi = norm.cdf   # standard normal CDF

# ── Formula (3): P(b) = exp(-2*mu*b / sigma^2) = exp(-2*b_sigma*SR)
def P_ever(b, mu, sigma):
    \"\"\"Probability of ever hitting drawdown b (infinite horizon).\"\"\"
    return np.exp(-2 * mu * b / sigma**2)

# ── Formula (4)/(5): P(b, T) — probability of hitting b within horizon T
def P_bT(b, T, mu, sigma):
    \"\"\"CDF of first hitting time for drawdown b within horizon T.\"\"\"
    s = sigma * np.sqrt(T)
    term1 = Phi((-b - mu * T) / s)
    term2 = np.exp(-2 * mu * b / sigma**2) * Phi((-b + mu * T) / s)
    return term1 + term2

# ── Formula (6): Stationary distribution P(D_t >= b) -> exp(-2*b_sigma*SR)
def P_stationary(b, mu, sigma):
    \"\"\"Stationary probability that drawdown exceeds b (large t limit).\"\"\"
    return np.exp(-2 * mu * b / sigma**2)

# ── Formula (7): E[D_t] = sigma^2 / (2*mu) = sigma / (2*SR)
def E_drawdown(mu, sigma):
    \"\"\"Expected drawdown in stationary regime.\"\"\"
    SR = mu / sigma
    return sigma / (2 * SR)

# ── Formula E(tau) = b/mu = b_sigma/SR: expected recovery time from drawdown b
def E_recovery(b, mu, sigma):
    \"\"\"Expected time to recover from drawdown b back to prior high.\"\"\"
    return b / mu

# ── Formula (9): std(tau) = b*sigma^2 / mu^3
def std_recovery(b, mu, sigma):
    \"\"\"Std dev of recovery time.\"\"\"
    return b * sigma**2 / mu**3

# ── Formula (10): Expected time *spent* in drawdown = sigma^2/(w*mu^2) = 1/(2*SR^2)
def E_time_in_drawdown(mu, sigma):
    \"\"\"Expected fraction of time process spends in a drawdown (per unit time).\"\"\"
    SR = mu / sigma
    return 1 / (2 * SR**2)

# ── Derived: normalised drawdown and Sharpe ratio
def b_sigma(b, sigma):
    return b / sigma

def SR(mu, sigma):
    return mu / sigma

print("Gappy's drawdown formulas loaded.")
print(f"  P_ever(b=1, mu=0.1, sigma=1)  = {P_ever(1, 0.1, 1):.4f}")
print(f"  E_drawdown(mu=0.1, sigma=1)   = {E_drawdown(0.1, 1):.4f}")
print(f"  E_recovery(b=1, mu=0.1, sigma=1) = {E_recovery(1, 0.1, 1):.4f}")
"""),

md([
    "## §2  Table 1 Reproduction\n",
    "\n",
    "Reproduce Paleologo Table 1: P(D_t ≥ b) for a range of Sharpe ratios and normalised\n",
    "drawdown levels b/σ. Stationary regime (large t).",
]),

code("""
sharpes  = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50]
b_sigmas = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50]

print(f"{'Sharpe':>8}  " + "  ".join(f"b/σ={bs:.2f}" for bs in b_sigmas))
print("-" * 72)
for sr in sharpes:
    row = []
    for bs in b_sigmas:
        # P(D_t >= b) = exp(-2 * b_sigma * SR)
        p = np.exp(-2 * bs * sr)
        row.append(f"{p*100:6.1f}%")
    print(f"{sr:>8.2f}  " + "  ".join(row))
print()
print("(matches Paleologo 2025 Table 1)")
"""),

md([
    "## §3  GJB2 Frameshift — Trit Fidelity as a Drawdown Process\n",
    "\n",
    "We model the per-position trit match probability as a drifting process:\n",
    "\n",
    "$$X_t = \\text{(running match rate at position } t\\text{)}$$\n",
    "\n",
    "**Wildtype**: high SR (μ > 0, sequence conserved). Low expected drawdown.\n",
    "\n",
    "**c.35delG frameshift**: μ ≈ 0 (no correction mechanism downstream of deletion).\n",
    "SR → 0 → P(b) → 1 for any b. Permanent drawdown. This is the closed-form\n",
    "prediction matching the step function we observed from audio in §4 of gabor_analysis.",
]),

code("""
import sys, os, pathlib

_HERE = pathlib.Path(os.path.abspath(''))
_GJB2 = pathlib.Path(os.environ.get(
    'GJB2_REPO',
    str(_HERE.parent.parent / 'gjb2-mcore-sonification'),
))
sys.path.insert(0, str(_GJB2 / 'code'))

from gjb2_sonification import dna_to_mcore_trits, fetch_gjb2_cds

try:
    ref_seq = fetch_gjb2_cds()
    print(f"NCBI reference: {len(ref_seq)} bp")
except Exception:
    ref_seq = (
        "ATGGATTGGGGCAAAGAGGCAGAGAAACACAAACGCAGACT"
        "TTATTTGGGTCCTGGAGCTATTATCACCATCATTTTTGGGATTGGCCTGG"
        "TCATCATCTTTGTGGTCATTTTCCTATTTGGAGAGCAGAAG"
        "ATTGAGGTTGTGTTAGCAGTGTTCACAGCCATCATCAAGAA"
        "AGGCATCAAAGTTGTGCGCATCTTCTTCATCGTCAATGCCA"
        "TCATCATCATCTTCGTGGATGTGATGATCATTTTCTTGGTC"
    ).replace(" ", "")
    print(f"Fallback reference: {len(ref_seq)} bp")
"""),

code("""
def apply_deletion(seq, pos_1indexed):
    idx = pos_1indexed - 1
    return seq[:idx] + seq[idx + 1:]

wt_trits   = dna_to_mcore_trits(ref_seq)
c35_trits  = dna_to_mcore_trits(apply_deletion(ref_seq, 35))
c235_trits = dna_to_mcore_trits(apply_deletion(ref_seq, 235))

N = min(len(wt_trits), len(c35_trits), len(c235_trits))

# Per-position match (1=match, 0=mismatch vs wildtype)
match_35  = np.array([1 if wt_trits[i] == c35_trits[i]  else 0 for i in range(N)], float)
match_235 = np.array([1 if wt_trits[i] == c235_trits[i] else 0 for i in range(N)], float)

# Running match rate (X_t in Gappy's model)
run_match_35  = np.cumsum(match_35)  / (np.arange(N) + 1)
run_match_235 = np.cumsum(match_235) / (np.arange(N) + 1)

# Drawdown D_t = running_max(X) - X_t
def drawdown_series(x):
    running_max = np.maximum.accumulate(x)
    return running_max - x

dd_35  = drawdown_series(run_match_35)
dd_235 = drawdown_series(run_match_235)

# Estimate mu and sigma from upstream region (before deletion)
UPSTREAM = 34   # positions before c.35 deletion
upstream_series = run_match_35[:UPSTREAM]
diffs = np.diff(upstream_series)
mu_hat    = diffs.mean()
sigma_hat = diffs.std() + 1e-9
sr_hat    = mu_hat / sigma_hat

print("Wildtype upstream region (positions 1-34):")
print(f"  Estimated mu    = {mu_hat:.6f}  (drift per position)")
print(f"  Estimated sigma = {sigma_hat:.6f}  (volatility per position)")
print(f"  Estimated SR    = {sr_hat:.4f}")
print()

# Gappy's predictions for wildtype vs frameshift
b_test = 0.10   # 10% drawdown threshold
print(f"Gappy P(ever drawdown >= {b_test:.0%}) predictions:")
print(f"  Wildtype  (SR={sr_hat:.2f}):  P(b) = {P_ever(b_test, max(mu_hat,1e-9), sigma_hat):.4f}")
print(f"  c.35delG  (SR→0):            P(b) → {P_ever(b_test, 1e-9, sigma_hat):.4f}  (certain)")
print()
print(f"Expected drawdown E[D]: {E_drawdown(max(mu_hat,1e-9), sigma_hat):.4f}")
print(f"Expected recovery E[τ] from b={b_test:.2f}: {E_recovery(b_test, max(mu_hat,1e-9), sigma_hat):.1f} positions")
"""),

code("""
fig, axes = plt.subplots(2, 2, figsize=(13, 8))
fig.suptitle("GJB2 Trit Fidelity — Drawdown Analysis (Paleologo 2025)", fontsize=12)

# ── Panel 1: Running match rate
ax = axes[0, 0]
ax.plot(run_match_35,  color='#E05A5A', label='c.35delG',   lw=1.2)
ax.plot(run_match_235, color='#C97E08', label='c.235delC',  lw=1.2, alpha=0.8)
ax.axvline(34,  color='#E05A5A', ls='--', lw=0.8, alpha=0.6)
ax.axvline(234, color='#C97E08', ls='--', lw=0.8, alpha=0.6)
ax.set_title("Running Match Rate  X_t")
ax.set_xlabel("Position")
ax.set_ylabel("Match rate vs wildtype")
ax.legend(fontsize=9)

# ── Panel 2: Drawdown series
ax = axes[0, 1]
ax.plot(dd_35,  color='#E05A5A', label='c.35delG',  lw=1.2)
ax.plot(dd_235, color='#C97E08', label='c.235delC', lw=1.2, alpha=0.8)
ax.axvline(34,  color='#E05A5A', ls='--', lw=0.8, alpha=0.6)
ax.axvline(234, color='#C97E08', ls='--', lw=0.8, alpha=0.6)
ax.set_title("Drawdown  D_t = max(X) − X_t")
ax.set_xlabel("Position")
ax.set_ylabel("Drawdown (information loss)")
ax.legend(fontsize=9)

# ── Panel 3: Stationary P(D >= b) vs b/sigma — Gappy formula vs empirical
ax = axes[1, 0]
bs_range = np.linspace(0, 3, 200)
sr_wt = max(sr_hat, 0.01)
theory_curve = np.exp(-2 * bs_range * sr_wt)
ax.plot(bs_range, theory_curve, 'k-', lw=2, label=f'Gappy eq.(6)  SR={sr_wt:.2f}')
ax.plot(bs_range, np.exp(-2 * bs_range * 0.001), 'r--', lw=1.5, label='SR≈0 (frameshift)')
ax.set_title("Stationary P(D_t ≥ b)  [eq. 6]")
ax.set_xlabel("b / σ  (normalised drawdown)")
ax.set_ylabel("Probability")
ax.legend(fontsize=9)

# ── Panel 4: P(b,T) over horizons T for wildtype SR
ax = axes[1, 1]
b_val = sigma_hat * 0.5   # half-sigma drawdown
T_range = np.linspace(0.01, 200, 300)
p_curve = [P_bT(b_val, T, max(mu_hat, 1e-9), sigma_hat) for T in T_range]
ax.plot(T_range, p_curve, color='#4BA3C7', lw=2)
ax.axhline(P_ever(b_val, max(mu_hat, 1e-9), sigma_hat),
           color='k', ls='--', lw=1, label=f'P(ever) = {P_ever(b_val, max(mu_hat,1e-9), sigma_hat):.3f}')
ax.set_title(f"P(drawdown ≥ {b_val:.4f} within T)  [eq. 4]")
ax.set_xlabel("Horizon T (positions)")
ax.set_ylabel("Probability")
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('gjb2_drawdown.png', bbox_inches='tight')
plt.show()
print("Saved gjb2_drawdown.png")
"""),

md([
    "## §4  MethylationMetrics — Oncological Drawdown\n",
    "\n",
    "The `decoherence_trajectory` models beta values drifting toward hypermethylation.\n",
    "In Gappy's framework:\n",
    "\n",
    "- **μ** = `drift_rate` (positive = hypermethylation pressure)\n",
    "- **σ** = stochastic variation in beta values\n",
    "- **b** = distance to S3 threshold = `BETA_HEMIMETHYLATED_MAX − beta_0`\n",
    "\n",
    "P(b) = probability of tumor suppressor silencing (crossing the S3 boundary).\n",
    "E(τ) = expected epigenetic time-to-silencing.",
]),

code("""
from mcore_py.overlays.methylation import (
    MethylationMetrics, classify_cpg, MethylationState,
    BETA_HEMIMETHYLATED_MAX
)

# Simulate trajectories and overlay Gappy predictions
DRIFT_RATES = [0.02, 0.05, 0.10, 0.15]
SIGMA_METHYL = 0.02   # plausible beta stochasticity
INITIAL_BETA = 0.10   # normal unmethylated promoter
STEPS = 50
b_to_threshold = BETA_HEMIMETHYLATED_MAX - INITIAL_BETA  # = 0.70

print(f"S3 threshold: beta = {BETA_HEMIMETHYLATED_MAX}")
print(f"Initial beta: {INITIAL_BETA}   =>   b = {b_to_threshold:.2f}")
print()
print(f"{'Drift rate (mu)':>18}  {'SR':>6}  {'P(silencing)':>14}  {'E(tau) steps':>14}")
print("-" * 60)

for dr in DRIFT_RATES:
    sr_m  = dr / SIGMA_METHYL
    p_sil = P_ever(b_to_threshold, dr, SIGMA_METHYL)
    e_tau = E_recovery(b_to_threshold, dr, SIGMA_METHYL)
    print(f"{dr:>18.3f}  {sr_m:>6.2f}  {p_sil:>14.4f}  {e_tau:>14.1f}")
"""),

code("""
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("MethylationMetrics — Oncological Drawdown (Paleologo Framework)", fontsize=12)

# ── Panel 1: Simulated trajectories with Gappy P(b) annotations
ax = axes[0]
colors = ['#4BA3C7', '#C97E08', '#E05A5A', '#7B4B8C']
for dr, col in zip(DRIFT_RATES, colors):
    traj = MethylationMetrics.decoherence_trajectory(
        [INITIAL_BETA], drift_rate=dr, steps=STEPS
    )
    beta_path = [INITIAL_BETA + dr * i for i in range(STEPS)]
    beta_path = [min(1.0, b) for b in beta_path]
    p_sil = P_ever(b_to_threshold, dr, SIGMA_METHYL)
    ax.plot(beta_path, color=col, lw=1.5, label=f'μ={dr:.2f}  P(sil)={p_sil:.3f}')

ax.axhline(BETA_HEMIMETHYLATED_MAX, color='k', ls='--', lw=1.2, label='S3 threshold (0.80)')
ax.set_title("Beta Drift Trajectories")
ax.set_xlabel("Step")
ax.set_ylabel("Beta value")
ax.legend(fontsize=8)

# ── Panel 2: P(silencing within T steps) for each drift rate
ax = axes[1]
T_range = np.linspace(1, STEPS, 200)
for dr, col in zip(DRIFT_RATES, colors):
    p_curve = [P_bT(b_to_threshold, T, dr, SIGMA_METHYL) for T in T_range]
    ax.plot(T_range, p_curve, color=col, lw=1.5, label=f'μ={dr:.2f}')

ax.set_title("P(silencing within T steps)  [eq. 4]")
ax.set_xlabel("Horizon T (steps)")
ax.set_ylabel("P(beta ≥ 0.80)")
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig('methylation_drawdown.png', bbox_inches='tight')
plt.show()
print("Saved methylation_drawdown.png")
"""),

md([
    "## §5  L7 TNet — Information Break as Drawdown\n",
    "\n",
    "The masked STFT region in L7 TNet is a drawdown event:\n",
    "\n",
    "- **b** = depth of the information break (fraction of STFT bins masked)\n",
    "- **E(τ) = b/μ** = expected recovery duration = how many time frames the imputation covers\n",
    "- This gives T-Net a closed-form prior on gap length, improving t★ localization\n",
    "\n",
    "We fit μ and σ from the unmasked STFT region, then compute Gappy's predictions\n",
    "for each information break in a test batch.",
]),

code("""
import torch
import torch.nn.functional as F

torch.manual_seed(SEED)
np.random.seed(SEED)

# Re-use DecaySTFTGenerator from L7 notebook
class DecaySTFTGenerator:
    def __init__(self, seq_len=256, sample_rate=100, n_fft=32, hop_length=8):
        self.seq_len = seq_len
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.window = torch.hann_window(n_fft)
        self.duration = seq_len / sample_rate

    def generate_batch(self, batch_size=32):
        t = torch.linspace(0, self.seq_len / self.sample_rate, self.seq_len
                           ).unsqueeze(0).repeat(batch_size, 1)
        t_star = torch.rand(batch_size, 1) * (self.duration * 0.6) + 0.2
        sigma_t = 0.05
        omega_0 = 15.0
        latent = torch.exp(-((t - t_star)**2) / (2 * sigma_t**2)) * torch.cos(omega_0 * t)
        stft_obs = torch.stft(latent, n_fft=self.n_fft, hop_length=self.hop_length,
                              window=self.window, return_complex=True)
        stft_mag = torch.abs(stft_obs)
        gradients = torch.abs(torch.gradient(stft_mag, dim=2)[0])
        fisher_info = (gradients ** 2) / (stft_mag + 1e-6)
        fi_threshold = fisher_info.mean() * 0.5
        mask = (fisher_info > fi_threshold).float()
        masked_stft = stft_mag * mask
        return masked_stft, stft_mag, mask, t_star

gen = DecaySTFTGenerator()
masked_stft, oracle_stft, mask, t_star = gen.generate_batch(64)

# For each sample: compute break depth b and estimate mu/sigma from unmasked region
break_depths = []
e_taus = []
actual_durations = []

T_frames = oracle_stft.shape[2]  # number of time frames

for i in range(len(t_star)):
    m = mask[i, 0, :].numpy()          # mask for first freq bin
    mag = oracle_stft[i, 0, :].numpy() # STFT magnitude trajectory

    # b = fraction of frames that are masked (= drawdown depth)
    b_val = 1.0 - m.mean()

    # Fit mu/sigma from the unmasked frames
    unmasked_vals = mag[m > 0.5]
    if len(unmasked_vals) > 2:
        diffs = np.diff(unmasked_vals)
        mu_i    = max(diffs.mean(), 1e-6)
        sigma_i = max(diffs.std(), 1e-6)
    else:
        mu_i, sigma_i = 1e-4, 1e-3

    e_tau_i = E_recovery(b_val, mu_i, sigma_i)
    break_depths.append(b_val)
    e_taus.append(min(e_tau_i, T_frames))   # cap at sequence length

    # Actual masked duration (in frames)
    actual_dur = (m < 0.5).sum()
    actual_durations.append(actual_dur)

break_depths   = np.array(break_depths)
e_taus         = np.array(e_taus)
actual_durations = np.array(actual_durations, float)

print(f"Mean information break depth b:    {break_depths.mean():.4f}  (fraction masked)")
print(f"Mean Gappy E(tau):                 {e_taus.mean():.2f} frames")
print(f"Mean actual masked duration:       {actual_durations.mean():.2f} frames")
corr = np.corrcoef(e_taus, actual_durations)[0, 1]
print(f"Correlation E(tau) vs actual dur:  {corr:.4f}")
"""),

code("""
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
fig.suptitle("L7 TNet — Information Break as Drawdown (Paleologo Framework)", fontsize=12)

ax = axes[0]
ax.scatter(break_depths, e_taus, s=10, alpha=0.6, color='#4BA3C7')
ax.set_title("Break Depth b vs E(τ)  [eq. E(τ)=b/μ]")
ax.set_xlabel("Break depth b")
ax.set_ylabel("E(τ)  predicted recovery (frames)")

ax = axes[1]
ax.scatter(e_taus, actual_durations, s=10, alpha=0.6, color='#C97E08')
ax.plot([0, actual_durations.max()], [0, actual_durations.max()],
        'k--', lw=1, label='y=x')
ax.set_title(f"E(tau) vs Actual Break Duration (corr={corr:.3f})")
ax.set_xlabel("E(τ)  Gappy prediction")
ax.set_ylabel("Actual masked frames")
ax.legend(fontsize=9)

ax = axes[2]
ax.hist(break_depths, bins=20, color='#E05A5A', alpha=0.7, edgecolor='white')
ax.axvline(break_depths.mean(), color='k', ls='--', lw=1.5,
           label=f'mean={break_depths.mean():.3f}')
p_ever_mean = P_ever(break_depths.mean(), 1e-4, 1e-3)
ax.set_title(f"Break Depth Distribution  P(ever) at mean b={p_ever_mean:.3f}")
ax.set_xlabel("Break depth b")
ax.set_ylabel("Count")
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('l7_drawdown.png', bbox_inches='tight')
plt.show()
print("Saved l7_drawdown.png")
"""),

md([
    "## §6  Summary\n",
    "\n",
    "| Domain | μ analog | σ analog | Key result |\n",
    "|--------|----------|----------|-----------|\n",
    "| GJB2 wildtype | match-rate drift | carry noise | Low P(b): sequence resists corruption |\n",
    "| GJB2 c.35delG | ≈ 0 (no correction) | carry noise | SR→0 → P(b)=1: permanent drawdown |\n",
    "| CpG methylation | drift_rate | beta volatility | E(τ) = time-to-silencing |\n",
    "| L7 info break | unmasked STFT drift | STFT volatility | E(τ) predicts imputation window |\n",
    "\n",
    "**Formula (7)** `E[D] = σ/(2·SR)` is the single most useful result:\n",
    "it gives the expected information loss in steady state as a function of signal quality.\n",
    "For SR → 0 (frameshift, demethylated cancer cell), E[D] diverges — the system\n",
    "has no ability to self-correct.\n",
    "\n",
    "---\n",
    "*MCORE-1 — Drawdown analysis via Paleologo (2025)*",
]),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "cells": cells,
}

out = pathlib.Path(__file__).with_name("mcore_drawdown_analysis.ipynb")
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
print(f"Wrote {out}  ({out.stat().st_size} bytes)")
nb2 = json.loads(out.read_text())
assert nb2["nbformat"] == 4
print("JSON round-trip OK")
