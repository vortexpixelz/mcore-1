"""gjb2_c35delg_digest_scan.py

In-silico restriction digest scan for GJB2 c.35delG allele discrimination.

Goal: identify restriction enzymes that cut WT but not mutant (or vice versa)
around cDNA position 35 of NM_004004.6, enabling RFLP-based genotyping.

If no clean natural allele-specific site is found, output recommends
dCAPS (derived Cleaved Amplified Polymorphic Sequence) primer design.

Requires: biopython
    pip install biopython

Outputs:
    gjb2_digest_allele_diff.tsv   enzyme x cut-position table
    gjb2_digest_summary.txt       human-readable summary

Reference sequences (NM_004004.6):
    WT  (c.1-c.54, 54 nt):  ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGGTGTGAACAAACACTCCACC
    MUT (c.35del,  53 nt):  ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGTGTGAACAAACACTCCACC

WT translation (18 aa):  MDWGTLQTILGGVNKHST
MUT translation (to *):  MDWGTLQTILGV*
"""

from Bio.Seq import Seq
from Bio.Restriction import Analysis, RestrictionBatch, CommOnly
import csv

# ── Sequences ──────────────────────────────────────────────────────────────
WT  = "ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGGTGTGAACAAACACTCCACC"
MUT = WT[:34] + WT[35:]   # delete c.35 (0-based index 34)

# ── Hard assertions: fail immediately if sequences are wrong ─────────────
assert len(WT)  == 54, f"WT length wrong: {len(WT)} (expected 54)"
assert len(MUT) == 53, f"MUT length wrong: {len(MUT)} (expected 53)"

wt_prot  = str(Seq(WT).translate())
mut_prot = str(Seq(MUT).translate(to_stop=False))
mut_stub = mut_prot.split("*")[0]

assert wt_prot  == "MDWGTLQTILGGVNKHST", (
    f"WT translation wrong: {wt_prot!r}\nExpected: 'MDWGTLQTILGGVNKHST'"
)
assert mut_stub == "MDWGTLQTILGV", (
    f"MUT stub wrong: {mut_stub!r}\nExpected: 'MDWGTLQTILGV'"
)

print("✅ All sequence assertions passed")
print(f"   WT  ({len(WT)} nt): {WT}")
print(f"   MUT ({len(MUT)} nt): {MUT}")
print(f"   WT  translation: {wt_prot}")
print(f"   MUT translation: {mut_prot}")
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

all_enzymes  = sorted(set(wt_hits) | set(mut_hits))
diff_enzymes = [e for e in all_enzymes if wt_hits.get(e) != mut_hits.get(e)]

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
        site  = (wt_hits.get(e) or mut_hits.get(e, {})).get("site", "?")
        print(f"{e:<20} {site:<20} {str(wt_c):<25} {str(mut_c)}")
else:
    print("⚠️  No CommOnly enzyme discriminates WT from c.35delG in this window.")
    print("    This is expected: the variant is a 1-bp deletion in a poly-G run.")
    print("    → Next step: dCAPS / forced restriction site primer design.")
    print("    Tools: http://helix.wustl.edu/dcaps/dcaps.html")

# ── Write TSV ──────────────────────────────────────────────────────────────
with open("gjb2_digest_allele_diff.tsv", "w", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["enzyme", "recognition_site", "wt_cuts", "mut_cuts", "discriminating"])
    for e in all_enzymes:
        wt_c  = wt_hits.get(e,  {}).get("cuts", [])
        mut_c = mut_hits.get(e, {}).get("cuts", [])
        site  = (wt_hits.get(e) or mut_hits.get(e, {})).get("site", "?")
        disc  = "YES" if e in diff_enzymes else "no"
        writer.writerow([e, site, wt_c, mut_c, disc])
print("Wrote gjb2_digest_allele_diff.tsv")

# ── Summary report ────────────────────────────────────────────────────────────
with open("gjb2_digest_summary.txt", "w") as f:
    f.write("GJB2 c.35delG In-Silico Restriction Digest Summary\n")
    f.write("=" * 52 + "\n\n")
    f.write(f"WT  sequence ({len(WT)} nt): {WT}\n")
    f.write(f"MUT sequence ({len(MUT)} nt): {MUT}\n\n")
    f.write(f"WT  translation: {wt_prot}\n")
    f.write(f"MUT translation: {mut_prot}\n\n")
    f.write(f"Allele-discriminating enzymes found: {len(diff_enzymes)}\n\n")
    if diff_enzymes:
        f.write("Discriminating enzymes:\n")
        for e in diff_enzymes:
            wt_c  = wt_hits.get(e,  {}).get("cuts", [])
            mut_c = mut_hits.get(e, {}).get("cuts", [])
            site  = (wt_hits.get(e) or mut_hits.get(e, {})).get("site", "?")
            f.write(f"  {e}: site={site} WT={wt_c} MUT={mut_c}\n")
    else:
        f.write("No natural CommOnly enzyme discriminates WT vs c.35delG.\n")
        f.write("Expected: 1-bp deletion in poly-G run rarely creates/destroys sites.\n")
        f.write("Recommended next step: dCAPS primer design.\n")
        f.write("See README.md dCAPS section for details.\n")
print("Wrote gjb2_digest_summary.txt")
