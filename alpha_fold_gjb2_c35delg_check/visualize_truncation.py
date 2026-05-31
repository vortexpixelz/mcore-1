"""visualize_truncation.py
Produces a side-by-side domain cartoon comparing WT GJB2/Connexin-26 (226 aa)
vs the c.35delG truncation product (12 aa), and a bar chart of sequence lengths.
Outputs:
  gjb2_wt_vs_mutant_length.png  — bar chart
  gjb2_domain_cartoon.png       — domain architecture cartoon
Requires: matplotlib, numpy
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Sequence data ──────────────────────────────────────────────────────────────
WT_SEQ  = "MDWGTLQTILGGVNKHSTSIGKIWLTVLFIFRIMILVVAAKEVWGDEQADFVCNTLQPGCKNVCYDHYFPSHIRLWALQLIFVSTPALLVAMHVAYRRHEKKRKFIKGEIKSEFKDIEEIKTQKVRIEGSLWWTYTSSIFFRVIFEAAFMYVFYVMYDGFSMQRLVKCNAWPCPNTVDCFVSRPTEKTVFTVFMIAVSGICILLNVTELCYLLIRYCSGKSKKPV"
MUT_SEQ = "MDWGTLQTILGV"

# ── 1. Bar chart: sequence lengths ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
labels = ["WT GJB2/Cx26\n(P29033)", "c.35delG\np.Gly12Valfs*2"]
lengths = [len(WT_SEQ), len(MUT_SEQ)]
colors  = ["#2e86ab", "#e84855"]
bars = ax.bar(labels, lengths, color=colors, width=0.45, edgecolor="black", linewidth=0.8)
for bar, val in zip(bars, lengths):
    ax.text(bar.get_x() + bar.get_width()/2, val + 3, str(val) + " aa",
            ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylabel("Protein length (amino acids)", fontsize=11)
ax.set_title("GJB2 / Connexin-26: WT vs c.35delG Truncation", fontsize=12, fontweight="bold")
ax.set_ylim(0, 260)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("gjb2_wt_vs_mutant_length.png", dpi=150)
plt.close()
print("Saved gjb2_wt_vs_mutant_length.png")

# ── 2. Domain architecture cartoon ───────────────────────────────────────────
# Connexin-26 domains (approximate residue ranges, based on Maeda 2009 / UniProt)
domains = [
    {"label": "NT",   "start": 1,   "end": 22,  "color": "#6db1d0", "region": "cytoplasmic"},
    {"label": "TM1",  "start": 23,  "end": 43,  "color": "#f4a261", "region": "transmembrane"},
    {"label": "EL1",  "start": 44,  "end": 75,  "color": "#2a9d8f", "region": "extracellular"},
    {"label": "TM2",  "start": 76,  "end": 96,  "color": "#f4a261", "region": "transmembrane"},
    {"label": "CL",   "start": 97,  "end": 122, "color": "#e9c46a", "region": "cytoplasmic"},
    {"label": "TM3",  "start": 123, "end": 143, "color": "#f4a261", "region": "transmembrane"},
    {"label": "EL2",  "start": 144, "end": 175, "color": "#2a9d8f", "region": "extracellular"},
    {"label": "TM4",  "start": 176, "end": 196, "color": "#f4a261", "region": "transmembrane"},
    {"label": "CT",   "start": 197, "end": 226, "color": "#6db1d0", "region": "cytoplasmic"},
]

fig, axes = plt.subplots(2, 1, figsize=(12, 4), gridspec_kw={"height_ratios": [1, 1]})
fig.suptitle("GJB2/Connexin-26 Domain Architecture: WT vs c.35delG",
             fontsize=12, fontweight="bold", y=1.02)

def draw_sequence_bar(ax, length, domains_to_draw, title, subtitle):
    ax.set_xlim(0, 226)
    ax.set_ylim(-0.5, 1.5)
    ax.axis("off")
    ax.set_title(f"{title}\n{subtitle}", fontsize=10, loc="left", pad=3)
    # backbone
    ax.add_patch(mpatches.FancyBboxPatch((0, 0.3), length, 0.4,
                                          boxstyle="round,pad=0.01",
                                          facecolor="#d0d0d0", edgecolor="#888", linewidth=0.6))
    for d in domains_to_draw:
        s, e = d["start"] - 1, d["end"]
        if s >= length:
            continue
        e = min(e, length)
        ax.add_patch(mpatches.FancyBboxPatch((s, 0.25), e - s, 0.5,
                                              boxstyle="round,pad=0.01",
                                              facecolor=d["color"], edgecolor="#444",
                                              linewidth=0.7, alpha=0.92))
        mid = (s + e) / 2
        ax.text(mid, 0.50, d["label"], ha="center", va="center",
                fontsize=7.5, fontweight="bold", color="white")
    # truncation marker
    if length < 226:
        ax.axvline(length, color="#e84855", linewidth=2.5, linestyle="--")
        ax.text(length + 2, 1.05, f"STOP\n(aa {length})", fontsize=8,
                color="#e84855", fontweight="bold")
    # scale ticks
    for tick in [1, 50, 100, 150, 200, length]:
        ax.text(tick, -0.1, str(tick), ha="center", va="top", fontsize=7, color="#555")

draw_sequence_bar(axes[0], 226, domains,
                  "Wild-type Cx26 (226 aa)",
                  "Full connexin fold: 4 TM helices, 2 extracellular loops, cytoplasmic NT/CT")

draw_sequence_bar(axes[1], 12, domains,
                  "c.35delG mutant — p.Gly12Valfs*2 (12 aa)",
                  "Premature stop at aa 13. No TM helix. No gap-junction function. Loss of protein.")

# Legend
legend_items = [
    mpatches.Patch(color="#f4a261", label="Transmembrane (TM)"),
    mpatches.Patch(color="#2a9d8f", label="Extracellular loop (EL)"),
    mpatches.Patch(color="#6db1d0", label="Cytoplasmic (NT/CT/CL)"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=3,
           fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.08))
plt.tight_layout()
plt.savefig("gjb2_domain_cartoon.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved gjb2_domain_cartoon.png")
