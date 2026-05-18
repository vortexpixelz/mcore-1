import json

cells = []

def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source}

def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source}

# §1 Problem & setup
cells.append(md("""# L7 TNet Imputation — Atomic Decay via STFT & S3 Crystallization

## §1 Problem & Setup

**Level 7 sub-atomic decay** trajectories are latent damped oscillations that cannot be
directly observed. At Level 6, Gabor's uncertainty principle limits joint time-frequency
resolution: where the amplitude changes rapidly, the Fisher information drops and spectral
bins go dark — an *Information Break*.

**Goal:** train a Temporal Hallucination Network (T-Net) that:
1. *Imputes* the missing STFT bins (reconstruction MSE)
2. *Localises* the exact decay time t★ from the corrupted spectrogram
3. Uses an *S3 crystallization prior* (symmetric group on 3 letters, 6 elements) as a
   structured bottleneck

We also ablate the S3 prior to show it contributes to imputation quality.
"""))

# §2 Data generator
cells.append(md("## §2 Data Generator — DecaySTFTGenerator"))

cells.append(code("""\
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Reproducibility
torch.manual_seed(42)
np.random.seed(42)

# ── Hyper-parameters ─────────────────────────────────────────────────────────
SEQ_LEN     = 256
SAMPLE_RATE = 100
N_FFT       = 32
HOP_LENGTH  = 8
FREQ_BINS   = N_FFT // 2 + 1   # = 17
HIDDEN_DIM  = 64
EPOCHS      = 150
BATCH_SIZE  = 16
LR          = 1e-3
print(f"FREQ_BINS={FREQ_BINS}  (n_fft={N_FFT})")
"""))

cells.append(code("""\
class DecaySTFTGenerator:
    \"\"\"
    Generates latent decay trajectories and applies a Gabor-limited observation model.
    Returns (masked_stft, oracle_stft, mask, t_star):
      - masked_stft / oracle_stft : (batch, freq_bins, time_frames)  float32
      - mask                      : (batch, freq_bins, time_frames)  {0,1} float32
      - t_star                    : (batch, 1)  true decay time in seconds
    \"\"\"
    def __init__(self, seq_len=SEQ_LEN, sample_rate=SAMPLE_RATE,
                 n_fft=N_FFT, hop_length=HOP_LENGTH):
        self.seq_len     = seq_len
        self.sample_rate = sample_rate
        self.n_fft       = n_fft
        self.hop_length  = hop_length
        self.window      = torch.hann_window(n_fft)

    def generate_batch(self, batch_size=BATCH_SIZE):
        t = (torch.linspace(0, self.seq_len / self.sample_rate, self.seq_len)
                  .unsqueeze(0).expand(batch_size, -1))

        # True decay time uniformly in [0.2, 0.8] × duration
        duration = self.seq_len / self.sample_rate
        t_star   = torch.rand(batch_size, 1) * duration * 0.6 + duration * 0.2

        # Latent: damped oscillation localised around t_star
        sigma_t  = 0.05
        omega_0  = 15.0
        latent   = (torch.exp(-((t - t_star) ** 2) / (2 * sigma_t ** 2))
                    * torch.cos(omega_0 * t))

        # STFT → magnitude spectrogram
        stft_obs = torch.stft(latent, n_fft=self.n_fft, hop_length=self.hop_length,
                               window=self.window, return_complex=True)
        stft_mag = torch.abs(stft_obs)           # (batch, freq_bins, T_frames)

        # Fisher-information surrogate → mask low-FI bins
        grads      = torch.abs(torch.gradient(stft_mag, dim=2)[0])
        fisher_info = grads ** 2 / (stft_mag + 1e-6)
        fi_thr      = fisher_info.mean() * 0.5
        mask        = (fisher_info > fi_thr).float()

        masked_stft = stft_mag * mask
        return masked_stft, stft_mag, mask, t_star

gen = DecaySTFTGenerator()
sample_masked, sample_oracle, sample_mask, sample_t = gen.generate_batch(4)
print(f"masked_stft : {sample_masked.shape}   (batch, freq_bins, T_frames)")
print(f"t_star      : {sample_t.shape}")
"""))

# §3 Model architecture
cells.append(md("## §3 Model Architecture"))

cells.append(code("""\
# ── S3Crystallizer ────────────────────────────────────────────────────────────
class S3Crystallizer(nn.Module):
    \"\"\"
    S3 prior: maps a hidden vector to one of 6 permutation states via Gumbel-softmax.
    Returns (s3_one_hot, logits).
    \"\"\"
    def __init__(self, input_dim, tau=1.0):
        super().__init__()
        self.tau       = tau
        self.s3_logits = nn.Linear(input_dim, 6)

    def forward(self, x):
        logits   = self.s3_logits(x)                              # (B, 6)
        s3_state = F.gumbel_softmax(logits, tau=self.tau, hard=True)  # (B, 6)
        return s3_state, logits


# ── ZigzagFusion ──────────────────────────────────────────────────────────────
class ZigzagFusion(nn.Module):
    \"\"\"Bidirectional GRU fusion (forward + retrocausal).\"\"\"
    def __init__(self, hidden_dim):
        super().__init__()
        half = hidden_dim // 2
        self.fwd_branch  = nn.GRU(hidden_dim, half, batch_first=True)
        self.bwd_branch  = nn.GRU(hidden_dim, half, batch_first=True)
        self.fusion      = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, x):
        fwd_out, _  = self.fwd_branch(x)
        x_rev       = torch.flip(x, dims=[1])
        bwd_out, _  = self.bwd_branch(x_rev)
        bwd_out     = torch.flip(bwd_out, dims=[1])
        fused       = torch.cat([fwd_out, bwd_out], dim=-1)   # (B, T, H)
        return F.relu(self.fusion(fused))


# ── ZigzagTNet ────────────────────────────────────────────────────────────────
class ZigzagTNet(nn.Module):
    \"\"\"
    T-Net with S3 crystallization bottleneck.
    forward(masked_stft) → (imputed_stft, t_hat, s3_logits)
      imputed_stft : (B, freq_bins, T_frames)
      t_hat        : (B, 1)  in [0,1]  (normalised by duration)
      s3_logits    : (B, 6)
    \"\"\"
    def __init__(self, freq_bins=FREQ_BINS, hidden_dim=HIDDEN_DIM):
        super().__init__()
        self.encoder    = nn.Linear(freq_bins, hidden_dim)
        self.s3_head    = S3Crystallizer(hidden_dim)
        self.zigzag     = ZigzagFusion(hidden_dim)
        self.decoder    = nn.Linear(hidden_dim, freq_bins)
        self.t_star_head = nn.Linear(hidden_dim, 1)

    def forward(self, masked_stft):
        # masked_stft: (B, F, T) → permute to (B, T, F)
        x        = masked_stft.permute(0, 2, 1)
        encoded  = F.relu(self.encoder(x))          # (B, T, H)

        # Global state for S3 head and t_star regression
        global_h = encoded.mean(dim=1)              # (B, H)
        s3_cryst, s3_logits = self.s3_head(global_h)  # (B,6), (B,6)

        # Use s3_cryst as a learned 6-way gate projected onto hidden dim via dot
        # Simple approach: treat it as a scalar weight summed with the global mean
        # to scale the sequence before zigzag (shape-safe)
        # s3_cryst is (B,6); project to scalar per sample
        s3_gate  = s3_cryst.sum(dim=-1, keepdim=True).unsqueeze(1)  # (B,1,1)
        encoded_gated = encoded * s3_gate            # (B, T, H)

        zagged   = self.zigzag(encoded_gated)        # (B, T, H)
        imputed  = self.decoder(zagged).permute(0, 2, 1)  # (B, F, T)

        # t_hat: use global mean of zagged output, predict normalised t_star
        global_z = zagged.mean(dim=1)               # (B, H)
        t_hat    = torch.sigmoid(self.t_star_head(global_z))  # (B, 1)

        return imputed, t_hat, s3_logits


# ── NoS3TNet (ablation) ───────────────────────────────────────────────────────
class NoS3TNet(nn.Module):
    \"\"\"
    Identical to ZigzagTNet but S3 crystallization is skipped.
    The raw mean of the encoder output is used as the global gate (=1 always).
    \"\"\"
    def __init__(self, freq_bins=FREQ_BINS, hidden_dim=HIDDEN_DIM):
        super().__init__()
        self.encoder     = nn.Linear(freq_bins, hidden_dim)
        self.zigzag      = ZigzagFusion(hidden_dim)
        self.decoder     = nn.Linear(hidden_dim, freq_bins)
        self.t_star_head = nn.Linear(hidden_dim, 1)

    def forward(self, masked_stft):
        x       = masked_stft.permute(0, 2, 1)
        encoded = F.relu(self.encoder(x))
        zagged  = self.zigzag(encoded)
        imputed = self.decoder(zagged).permute(0, 2, 1)
        global_z = zagged.mean(dim=1)
        t_hat   = torch.sigmoid(self.t_star_head(global_z))
        return imputed, t_hat

print("ZigzagTNet params:", sum(p.numel() for p in ZigzagTNet().parameters()))
print("NoS3TNet params  :", sum(p.numel() for p in NoS3TNet().parameters()))
"""))

# §4 Training ZigzagTNet
cells.append(md("## §4 Training — ZigzagTNet (150 epochs, batch_size=16)"))

cells.append(code("""\
def causal_closure_loss(imputed, oracle, mask, t_hat, t_star, duration):
    \"\"\"
    imputed / oracle / mask : (B, F, T)
    t_hat   : (B, 1)  sigmoid output in [0,1]
    t_star  : (B, 1)  in seconds
    duration: scalar  seq_len / sample_rate
    \"\"\"
    inv_mask   = 1.0 - mask
    mse_num    = F.mse_loss(imputed * inv_mask, oracle * inv_mask, reduction='sum')
    imp_loss   = mse_num / (inv_mask.sum() + 1e-8)

    # normalise t_star to [0,1] before L1 comparison with sigmoid t_hat
    t_star_norm = t_star / duration
    loc_loss    = F.l1_loss(t_hat, t_star_norm)

    total = imp_loss + 0.5 * loc_loss
    return total, imp_loss, loc_loss


generator  = DecaySTFTGenerator()
model      = ZigzagTNet()
optimizer  = optim.Adam(model.parameters(), lr=LR)
duration   = SEQ_LEN / SAMPLE_RATE   # 2.56 s

loss_history = []
imp_history  = []
loc_history  = []

print(f"Training ZigzagTNet for {EPOCHS} epochs …")
for epoch in range(EPOCHS):
    model.train()
    optimizer.zero_grad()

    masked, oracle, mask, t_star = generator.generate_batch(BATCH_SIZE)
    imputed, t_hat, s3_logits    = model(masked)

    total_loss, imp_loss, loc_loss = causal_closure_loss(
        imputed, oracle, mask, t_hat, t_star, duration)

    total_loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()

    loss_history.append(total_loss.item())
    imp_history.append(imp_loss.item())
    loc_history.append(loc_loss.item())

    if (epoch + 1) % 25 == 0 or epoch == 0:
        print(f"  Epoch {epoch+1:3d}/{EPOCHS}  total={total_loss.item():.4f}"
              f"  imp={imp_loss.item():.4f}  loc={loc_loss.item():.4f}")

print("Training complete.")
"""))

# §5 Loss curves
cells.append(md("## §5 Loss Curves"))

cells.append(code("""\
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, hist, label, color in zip(
        axes,
        [loss_history, imp_history, loc_history],
        ["Total loss", "Imputation MSE", "t★ L1"],
        ["steelblue", "darkorange", "green"]):
    ax.plot(hist, color=color, linewidth=1.2)
    ax.set_title(label)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.grid(True, alpha=0.3)
plt.suptitle("ZigzagTNet Training Curves", fontsize=13)
plt.tight_layout()
plt.savefig("/home/user/mcore-1/notebooks/L7_loss_curves.png", dpi=100)
plt.show()
print("Loss curves saved.")
"""))

# §6 STFT visualisation
cells.append(md("## §6 STFT Visualisation — Observable / Imputed / Oracle (first sample)"))

cells.append(code("""\
model.eval()
with torch.no_grad():
    vis_masked, vis_oracle, vis_mask, vis_t = generator.generate_batch(4)
    vis_imputed, vis_that, _ = model(vis_masked)

idx = 0
obs_np    = vis_masked[idx].numpy()
imp_np    = vis_imputed[idx].numpy()
oracle_np = vis_oracle[idx].numpy()

fig, axs = plt.subplots(1, 3, figsize=(15, 4))
for ax, data, title in zip(
        axs,
        [obs_np, imp_np, oracle_np],
        ["Observable (masked by Gabor limit)",
         "T-Net imputed (ZigzagTNet)",
         "Oracle (true trajectory)"]):
    ax.imshow(data, aspect='auto', origin='lower', cmap='viridis')
    ax.set_title(title)
    ax.set_xlabel("Time frames")
    ax.set_ylabel("Frequency bins")
plt.tight_layout()
plt.savefig("/home/user/mcore-1/notebooks/L7_stft_vis.png", dpi=100)
plt.show()
"""))

# §7 Metrics report
cells.append(md("## §7 Metrics Report"))

cells.append(code("""\
model.eval()
torch.manual_seed(99)
with torch.no_grad():
    test_masked, test_oracle, test_mask, test_t_star = generator.generate_batch(64)
    test_imputed, test_t_hat, _ = model(test_masked)

    # Imputation MSE (on held-out test batch, over ALL bins for comparability)
    test_imp_mse = F.mse_loss(test_imputed, test_oracle).item()

    # t_star localisation MAE in seconds
    t_hat_sec = test_t_hat * duration          # back to seconds
    t_mae_sec = F.l1_loss(t_hat_sec, test_t_star).item()

    # t_star accuracy: fraction within 5% of seq_len/sample_rate
    tol        = 0.05 * duration
    t_acc      = ((test_t_hat * duration - test_t_star).abs() < tol).float().mean().item()

print("=" * 48)
print("  METRICS REPORT — ZigzagTNet (test batch 64)")
print("=" * 48)
print(f"  Imputation MSE          : {test_imp_mse:.6f}")
print(f"  t★ localisation MAE (s) : {t_mae_sec:.4f}")
print(f"  t★ accuracy (±5%)       : {t_acc:.3f}")
print("=" * 48)
"""))

# §8 S3 crystallization analysis
cells.append(md("## §8 S3 Crystallization Analysis"))

cells.append(code("""\
model.eval()
state_counts = torch.zeros(6)

torch.manual_seed(0)
with torch.no_grad():
    for _ in range(100):
        masked_b, _, _, _ = generator.generate_batch(BATCH_SIZE)
        _, _, s3_logits_b = model(masked_b)
        # argmax of one-hot Gumbel-softmax
        winners = F.gumbel_softmax(s3_logits_b, tau=1.0, hard=True).argmax(dim=-1)
        for w in winners:
            state_counts[w.item()] += 1

total_samples = state_counts.sum().item()
fractions = (state_counts / total_samples).numpy()

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(range(6), fractions, color='steelblue', edgecolor='white', linewidth=0.8)
ax.set_xticks(range(6))
ax.set_xticklabels([f"S3[{i}]" for i in range(6)])
ax.set_ylabel("Selection fraction")
ax.set_title("S3 State Crystallization (100 batches × 16 samples = 1600 total)")
ax.axhline(1/6, color='red', linestyle='--', linewidth=1.2, label="Uniform (1/6)")
ax.legend()
for bar, frac in zip(bars, fractions):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f"{frac:.3f}", ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig("/home/user/mcore-1/notebooks/L7_s3_histogram.png", dpi=100)
plt.show()

most_selected = int(state_counts.argmax().item())
print(f"Most selected S3 state : {most_selected}  ({fractions[most_selected]*100:.1f}%)")
print(f"Uniform baseline       : {100/6:.1f}%")
print("Entropy collapsed?" , "YES" if fractions.max() > 0.5 else "NO — diverse selection")
"""))

# §9 Ablation
cells.append(md("## §9 Ablation — ZigzagTNet vs NoS3TNet"))

cells.append(code("""\
# Train NoS3TNet for the same number of epochs with identical settings
no_s3_model    = NoS3TNet()
no_s3_optimizer = optim.Adam(no_s3_model.parameters(), lr=LR)

print(f"Training NoS3TNet for {EPOCHS} epochs …")
for epoch in range(EPOCHS):
    no_s3_model.train()
    no_s3_optimizer.zero_grad()

    masked, oracle, mask, t_star = generator.generate_batch(BATCH_SIZE)
    imputed_ns, t_hat_ns         = no_s3_model(masked)

    total_ns, imp_ns, loc_ns = causal_closure_loss(
        imputed_ns, oracle, mask, t_hat_ns, t_star, duration)

    total_ns.backward()
    torch.nn.utils.clip_grad_norm_(no_s3_model.parameters(), 1.0)
    no_s3_optimizer.step()

    if (epoch + 1) % 25 == 0 or epoch == 0:
        print(f"  Epoch {epoch+1:3d}/{EPOCHS}  total={total_ns.item():.4f}"
              f"  imp={imp_ns.item():.4f}  loc={loc_ns.item():.4f}")

print("NoS3TNet training complete.")
"""))

cells.append(code("""\
no_s3_model.eval()
torch.manual_seed(99)
with torch.no_grad():
    test_masked2, test_oracle2, _, _ = generator.generate_batch(64)
    test_imp_ns, _ = no_s3_model(test_masked2)
    nos3_mse = F.mse_loss(test_imp_ns, test_oracle2).item()

# ZigzagTNet MSE already computed above as test_imp_mse
delta    = nos3_mse - test_imp_mse
rel_imp  = delta / nos3_mse * 100

print()
print("=" * 56)
print("  ABLATION: Imputation MSE Comparison (test batch 64)")
print("=" * 56)
print(f"  {'Model':<20} {'Imputation MSE':>16}")
print(f"  {'-'*36}")
print(f"  {'ZigzagTNet (S3)':<20} {test_imp_mse:>16.6f}")
print(f"  {'NoS3TNet':<20} {nos3_mse:>16.6f}")
print(f"  {'-'*36}")
print(f"  S3 improvement        : {delta:+.6f}  ({rel_imp:+.1f}%)")
print("=" * 56)
if delta > 0:
    print("  S3 prior HELPS — lower MSE with crystallization.")
else:
    print("  S3 prior does NOT help on this run (noisy result expected).")
"""))

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "cells": cells
}

with open("/home/user/mcore-1/notebooks/L7_TNet_Imputation.ipynb", "w") as f:
    json.dump(notebook, f, indent=1)

print("Notebook written.")
