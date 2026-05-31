"""gjb2_c35delg_digest_scan.py

In-silico restriction digest scan for GJB2 c.35delG allele discrimination.

Goal: identify restriction enzymes that cut WT but not mutant (or vice versa)
around cDNA position 35, enabling RFLP-based genotyping.

If no clean natural allele-specific site is found, the output will recommend
dCAPS (derived Cleaved Amplified Polymorphic Sequence) primer design.

Requires: biopython
    pip install biopython

Outputs:
    - Console report of allele-discriminating enzymes
    - gjb2_digest_allele_diff.tsv  (enzyme, site, WT_cuts, MUT_cuts)
    - gjb2_digest_summary.txt

Reference:
    WT extended window  (c.1-c.54 of NM_004004.6 CDS):
        ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGGTGTGAACAAACAGCTCCACC
    c.35delG mutant equivalent (delete index 34, 0-based):
        ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGTGTGAACAAACAGCTCCACC
"""

from Bio.Seq import Seq
from Bio.Restriction import Analysis, RestrictionBatch, CommOnly
import csv

# ── Sequences ─────────────────────────────────────────────────────────────────
WT  = "ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGGTGTGAACAAACAGCTCCACC"
MUT = WT[:34] + WT[35:]   # delete c.35 (0-based index 34)

print("WT  sequence:", WT)
print("MUT sequence:", MUT)
print(f"WT  length: {len(WT)} nt")
print(f"MUT length: {len(MUT)} nt")
print()

# ── Translation check ─────────────────────────────────────────────────────────
wt_prot  = Seq(WT).translate()
mut_prot = Seq(MUT).translate(to_stop=False)

print("WT  translation:", wt_prot)
print("MUT translation:", mut_prot)
print()

# Sanity check: mutant peptide before stop = MDWGTLQTILGV
mut_before_stop = str(mut_prot).split("*")[0]
assert mut_before_stop == "MDWGTLQTILGV", (
    f"Unexpected mutant peptide: {mut_before_stop!r} (expected MDWGTLQTILGV)"
)
print("✅ Mutant stub confirmed: MDWGTLQTILGV (p.Gly12Valfs*2)")
print()

# ── Restriction scan ──────────────────────────────────────────────────────────
batch = RestrictionBatch(CommOnly)

def scan(seq_str):
    analysis = Analysis(batch, Seq(seq_str), linear=True)
    return {
        str(enzyme): {"site": str(enzyme.site), "cuts": cuts}
        for enzyme, cuts in analysis.full().items()
        if cuts
    }

wt_hits  = scan(WT)
mut_hits = scan(MUT)

all_enzymes = sorted(set(wt_hits) | set(mut_hits))
diff_enzymes = [
    e for e in all_enzymes
    if wt_hits.get(e) != mut_hits.get(e)
]

print(f"Enzymes cutting WT:  {len(wt_hits)}")
print(f"Enzymes cutting MUT: {len(mut_hits)}")
print(f"Allele-discriminating enzymes: {len(diff_enzymes)}")
print()

if diff_enzymes:
    print("ALLELE-DISCRIMINATING ENZYMES (WT cuts ≠ MUT cuts):")
    print(f"{'Enzyme':<20} {'Recognition site':<20} {'WT cuts':<25} {'MUT cuts'}")
    print("-" * 85)
    for e in diff_enzymes:
        wt_c  = wt_hits.get(e,  {}).get("cuts", [])
        mut_c = mut_hits.get(e, {}).get("cuts", [])
        site  = wt_hits.get(e, mut_hits.get(e, {})).get("site", "?")
        print(f"{e:<20} {site:<20} {str(wt_c):<25} {str(mut_c)}")
else:
    print("⚠️  No common restriction enzyme discriminates WT from c.35delG")
    print("    in this sequence window using CommOnly enzymes.")
    print("    → Next step: dCAPS / forced restriction site primer design.")

# ── Write TSV ─────────────────────────────────────────────────────────────────
with open("gjb2_digest_allele_diff.tsv", "w", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["enzyme", "recognition_site", "wt_cuts", "mut_cuts", "discriminating"])
    for e in all_enzymes:
        wt_c  = wt_hits.get(e,  {}).get("cuts", [])
        mut_c = mut_hits.get(e, {}).get("cuts", [])
        site  = wt_hits.get(e, mut_hits.get(e, {})).get("site", "?")
        disc  = "YES" if e in diff_enzymes else "no"
        writer.writerow([e, site, wt_c, mut_c, disc])
print("\nWrote gjb2_digest_allele_diff.tsv")

# ── Summary report ────────────────────────────────────────────────────────────
with open("gjb2_digest_summary.txt", "w") as f:
    f.write("GJB2 c.35delG In-Silico Restriction Digest Summary\n")
    f.write("=" * 52 + "\n\n")
    f.write(f"WT  sequence: {WT}\n")
    f.write(f"MUT sequence: {MUT}\n\n")
    f.write(f"WT  translation: {wt_prot}\n")
    f.write(f"MUT translation: {mut_prot}\n\n")
    f.write(f"Allele-discriminating enzymes found: {len(diff_enzymes)}\n\n")
    if diff_enzymes:
        f.write("Discriminating enzymes:\n")
        for e in diff_enzymes:
            wt_c  = wt_hits.get(e,  {}).get("cuts", [])
            mut_c = mut_hits.get(e, {}).get("cuts", [])
            site  = wt_hits.get(e, mut_hits.get(e, {})).get("site", "?")
            f.write(f"  {e}: site={site} WT={wt_c} MUT={mut_c}\n")
    else:
        f.write("No natural CommOnly enzyme discriminates WT vs c.35delG in this window.\n")
        f.write("Recommended next step: dCAPS primer design.\n")
        f.write("See README.md dCAPS section for details.\n")
print("Wrote gjb2_digest_summary.txt")
