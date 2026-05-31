# GJB2 c.35delG: Restriction Digest / RFLP Evidence Lane

## What This Is

This folder contains an **in-silico restriction digest scan** for allele-specific discrimination of the GJB2 c.35delG variant at the **DNA level**.

This is DNA-level evidence — not protein structure, not AlphaFold. Restriction enzymes cut DNA. The target here is the sequence window around **cDNA position 35** of NM_004004.6.

---

## The Evidence Stack (Full Lane)

```
DNA lane            c.35delG sequence window (this folder)
       ↓
Restriction digest  RFLP / dCAPS allele discrimination
       ↓
Protein lane        p.Gly12Valfs*2 — 12-aa stub (AlphaFold folder)
       ↓
Structure lane      AlphaFold: no full Cx26 fold in mutant
       ↓
Clinical lane       Verified ClinVar/ClinGen/literature accession
```

---

## Codon-Level Precision

### What the deletion actually does at the DNA level

The GJB2 CDS contains a homopolymer run of **six consecutive G nucleotides** at positions c.30–c.35. The c.35del removes one G from this run.

```
WT  genomic/cDNA context (c.28–c.45):
  ... CTG | GGG | GGT | GTG | AAC ...
       Leu   Gly   Gly   Val   Asn
       aa10  aa11  aa12  aa13  aa14

c.35delG mutant context (frame-shifted from aa12):
  ... CTG | GGG | GTG | TGA
       Leu   Gly   Val   STOP
       aa10  aa11  aa12
```

**Key points:**
- Positions 1–11 of the protein are **unchanged**
- Residue 12 becomes **Val** (GTG) instead of Gly (GGT)
- The very next codon is **TGA = stop**
- Protein consequence: **p.Gly12Valfs*2** — final peptide `MDWGTLQTILGV` (12 aa)
- This is NOT a subtle missense. It is complete loss of full-length Connexin-26.

---

## The RFLP Principle

Restriction Fragment Length Polymorphism (RFLP) genotyping works as follows:

1. PCR-amplify the genomic region spanning c.35
2. Digest the PCR product with a restriction enzyme
3. Run on gel or capillary electrophoresis
4. Alleles are distinguished by **different fragment sizes**

This only works cleanly if the variant **creates or destroys a restriction site**.

### Natural Site Scan

Run `gjb2_c35delg_digest_scan.py` to check all commercially available (CommOnly) restriction enzymes against both allele windows.

**The scan compares:**
- WT: `ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGGTGTGAACAAACAGCTCCACC`
- MUT: `ATGGATTGGGGCACGCTGCAGACGATCCTGGGGGTGTGAACAAACAGCTCCACC` *(c.35 deleted)*

### If No Natural Site Exists → dCAPS

The c.35del is a 1-bp deletion in a homopolymer run. Natural enzyme sites in this region are unlikely to discriminate perfectly because:
- Many enzymes don't recognize poly-G sequences
- A 1-nt size difference in PCR fragments is technically challenging to resolve

If the scan returns no discriminating enzymes, the correct next step is **dCAPS** (derived Cleaved Amplified Polymorphic Sequence):

1. **Design a mismatched primer** near c.35 that introduces 1–2 intentional mismatches
2. The mismatch, combined with either the WT or mutant sequence, **creates a clean restriction site** in one allele but not the other
3. Tools: [dCAPS Finder 2.0](http://helix.wustl.edu/dcaps/dcaps.html) or [Primer3Plus with NEBcutter]

> ⚠️ Do not claim a validated diagnostic restriction assay from this in-silico scan alone.  
> Validated RFLP/dCAPS assays require wet-lab confirmation (restriction digest + gel + sequencing of digestion products).

---

## Running the Script

```bash
# Install dependency
pip install biopython

# Run scan
cd alpha_fold_gjb2_c35delg_check/restriction_digest/
python gjb2_c35delg_digest_scan.py
```

**Outputs:**
- Console: allele-discriminating enzyme table (or dCAPS recommendation)
- `gjb2_digest_allele_diff.tsv`: full enzyme × cut-position table
- `gjb2_digest_summary.txt`: human-readable summary

---

## RFLP vs Direct Sequencing

| Method | What it shows | Throughput | Cost |
|---|---|---|---|
| RFLP / CAPS | Fragment size difference on gel | High | Low |
| dCAPS | Engineered restriction site | High | Low |
| Sanger sequencing | Exact nucleotide change | Low–medium | Medium |
| NGS panel | Full GJB2 coding region | High | Medium–high |

For population-scale carrier screening of c.35delG specifically, RFLP or dCAPS historically provided fast, cheap genotyping before NGS became routine. The scan here reconstructs that logic in silico.

---

## Clinical Disclaimer

- This folder contains **research / educational in-silico analysis only**
- Clinical diagnosis of GJB2-related hearing loss requires validated laboratory testing
- ClinVar accession for c.35del: **verify independently** at https://www.ncbi.nlm.nih.gov/clinvar/?term=NM_004004.6(GJB2):c.35del
- Do not use this script output as clinical evidence

---

## Files

```
restriction_digest/
├── README.md                              ← this file
├── gjb2_c35delg_digest_scan.py            ← BioPython in-silico digest
└── gjb2_c35delg_reference_windows.fasta  ← WT and mutant DNA windows
```

## References

- Neff MW et al. Use of dCAPS markers. *BioTechniques* 1998.
- Kelsell DP et al. Connexin 26 mutations in hereditary non-syndromic sensorineural deafness. *Nature* 1997;387:80–83.
- NEBcutter v3.0: https://nc3.neb.com/NEBcutter/
- dCAPS Finder 2.0: http://helix.wustl.edu/dcaps/dcaps.html
- BioPython Restriction module: https://biopython.org/docs/latest/api/Bio.Restriction.html
