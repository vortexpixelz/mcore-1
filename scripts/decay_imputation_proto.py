# Missing Frame Decay Imputation: Level 6 → Level 7
# Minimal reconstruction prototype — 1D damped oscillation with phase break.
# Reference implementation shared as context for the L7 TNet ablation study.

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Constants ────────────────────────────────────────────────────────────────

GABOR_LIMIT = 1 / (4 * np.pi)

T_TOTAL = 10.0
DT = 0.01

OMEGA_PRE = 12.0
OMEGA_POST = 28.0

GAMMA_PRE = 0.05
GAMMA_POST = 0.30

SIGMA_T_BREAK = 0.15
NOISE_LEVEL = 0.03

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ── Synthetic decay trajectory ────────────────────────────────────────────────

def generate_decay_signal():
    t = np.arange(0, T_TOTAL, DT)
    break_time = np.random.uniform(3.0, 7.0)
    signal = np.zeros_like(t)
    pre_mask = t < break_time
    post_mask = t >= break_time
    signal[pre_mask] = (
        np.exp(-GAMMA_PRE * t[pre_mask]) * np.sin(OMEGA_PRE * t[pre_mask])
    )
    shifted_t = t[post_mask] - break_time
    signal[post_mask] = (
        np.exp(-GAMMA_POST * shifted_t) * np.sin(OMEGA_POST * shifted_t)
    )
    signal += np.random.normal(0, NOISE_LEVEL, size=signal.shape)
    return t, signal, break_time


def apply_missing_frame(signal, t, break_time):
    mask = np.ones_like(signal)
    break_region = np.abs(t - break_time) < SIGMA_T_BREAK
    masked_signal = signal.copy()
    masked_signal[break_region] = 0.0
    mask[break_region] = 0.0
    return masked_signal, mask


def fisher_information(signal):
    grad = np.gradient(signal)
    return grad ** 2 / (np.abs(signal) + 1e-6)

# ── Reconstruction network ────────────────────────────────────────────────────

class ReconstructionNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(2, 64), nn.ReLU(),
            nn.Linear(64, 128), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

# ── Dataset ───────────────────────────────────────────────────────────────────

def build_dataset(n_samples=256):
    X, Y = [], []
    for _ in range(n_samples):
        t, signal, break_time = generate_decay_signal()
        masked_signal, mask = apply_missing_frame(signal, t, break_time)
        X.append(np.stack([masked_signal, mask], axis=-1))
        Y.append(signal[:, None])
    return (
        torch.tensor(np.array(X), dtype=torch.float32),
        torch.tensor(np.array(Y), dtype=torch.float32),
    )

# ── Training ──────────────────────────────────────────────────────────────────

model = ReconstructionNet().to(DEVICE)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
X_train, Y_train = build_dataset()
X_train, Y_train = X_train.to(DEVICE), Y_train.to(DEVICE)

for epoch in range(50):
    optimizer.zero_grad()
    loss = F.mse_loss(model(X_train), Y_train)
    loss.backward()
    optimizer.step()
    if epoch % 10 == 0:
        print(f"Epoch {epoch:03d} | Loss: {loss.item():.6f}")

# ── Test example ──────────────────────────────────────────────────────────────

t, signal, break_time = generate_decay_signal()
masked_signal, mask = apply_missing_frame(signal, t, break_time)
inp = np.stack([masked_signal, mask], axis=-1)
inp_tensor = torch.tensor(inp, dtype=torch.float32).unsqueeze(0).to(DEVICE)

with torch.no_grad():
    reconstructed = model(inp_tensor).squeeze().cpu().numpy()

fi_original = fisher_information(signal)
fi_masked = fisher_information(masked_signal)
mse = np.mean((signal - reconstructed) ** 2)

# ── Visualisation ─────────────────────────────────────────────────────────────

fig, axes = plt.subplots(3, 1, figsize=(12, 10))

axes[0].plot(t, signal, label="Ground Truth")
axes[0].plot(t, masked_signal, label="Observed (Masked)", alpha=0.7)
axes[0].plot(t, reconstructed, label="Reconstructed", linestyle="--")
axes[0].axvline(break_time, color="red", linestyle=":")
axes[0].set_title("Missing Frame Reconstruction")
axes[0].legend()

axes[1].plot(t, fi_original, label="Original FI")
axes[1].plot(t, fi_masked, label="Masked FI")
axes[1].set_title("Fisher Information Collapse")
axes[1].legend()

axes[2].plot(t, mask)
axes[2].set_title("Observability Mask")

plt.tight_layout()
plt.savefig("decay_imputation_result.png", dpi=100)
print(f"\nGabor Limit:       {GABOR_LIMIT:.6f}")
print(f"Break Time:        {break_time:.3f}")
print(f"Reconstruction MSE: {mse:.6f}")
print("Plot saved: decay_imputation_result.png")
