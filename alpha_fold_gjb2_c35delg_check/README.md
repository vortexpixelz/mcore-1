# AlphaFold Evidence Packet: GJB2 / Connexin-26 / c.35delG

## Variant Identity

| Field | Value |
|---|---|
| Gene | GJB2 |
| Protein | Connexin-26 (Cx26) |
| WT UniProt | P29033 (226 aa) |
| Transcript | NM_004004.6 |
| Variant (HGVS nucleotide) | **c.35del** (commonly written c.35delG) |
| Protein consequence | **p.Gly12Valfs\*2** |
| ClinVar classification | Reported pathogenic; verify exact c.35del accession before citation |
| Phenotype | Autosomal recessive non-syndromic sensorineural hearing loss (DFNB1) |

> **⚠️ ClinVar / ClinGen source:** The exact c.35delG accession must be independently verified before citation.  
> Do **not** use VCV000017023 — that record is `NM_004004.6(GJB2):c.109G>A` / `p.Val37Ile`, a different variant entirely.  
> To find the correct accession: search ClinVar for `NM_004004.6(GJB2):c.35del` directly at https://www.ncbi.nlm.nih.gov/clinvar/

---

## Critical Precision: cDNA Position 35, NOT Codon 35

This is the most common point of confusion:

- **c.35** refers to **nucleotide position 35** in the coding sequence (cDNA).
- Codon 12 spans cDNA positions 34–36.
- Deleting nucleotide 35 (a G) shifts the reading frame at amino acid 12.
- **Positions 1–11 are unchanged; residue 12 becomes Val; translation terminates at the next codon. The final peptide is 12 aa: `MDWGTLQTILGV`.**
- This is annotated as `p.Gly12Valfs*2`.

Do **not** interpret this as a "codon-35" variant or a subtle structural change to full-length Connexin-26.

---

## FASTA Files

### `GJB2_WT_P29033.fasta`
Full-length wild-type Connexin-26, UniProt P29033, 226 amino acids.  
Source: [UniProt P29033](https://www.uniprot.org/uniprot/P29033)

### `GJB2_c35delG_pGly12ValfsTer2.fasta`
Frameshifted truncation product, 12 amino acids.  
This is the **entire translated product** from the c.35del allele before the premature stop codon.  
AlphaFold will predict a short peptide with no membrane topology, no N-terminal helix bundle, and no connexin-fold.

---

## AlphaFold Submission Instructions

### Option A: ColabFold (Recommended for Custom Mutants)

URL: https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/AlphaFold2.ipynb

**Job 1 — Wild-type:**
```
Query sequence:
MDWGTLQTILGGVNKHSTSIGKIWLTVLFIFRIMILVVAAKEVWGDEQADFVCNTLQPGCKNVCYDHYFPSHIRLWALQLIFVSTPALLVAMHVAYRRHEKKRKFIKGEIKSEFKDIEEIKTQKVRIEGSLWWTYTSSIFFRVIFEAAFMYVFYVMYDGFSMQRLVKCNAWPCPNTVDCFVSRPTEKTVFTVFMIAVSGICILLNVTELCYLLIRYCSGKSKKPV
Job name: GJB2_WT_P29033
num_recycle: 3
use_amber: true
use_templates: true
```

**Job 2 — Mutant:**
```
Query sequence:
MDWGTLQTILGV
Job name: GJB2_c35delG_pGly12ValfsTer2
num_recycle: 3
use_amber: true
use_templates: false
```

### Option B: AlphaFold Server (alphafoldserver.com)

Go to https://alphafoldserver.com, create a new job, paste each sequence above.

### Option C: Pre-computed WT Structure

https://alphafold.ebi.ac.uk/entry/P29033

---

## Experimental Reference

**PDB 2ZW3** — Human Connexin-26 gap-junction channel, resolved at **3.5 Å** by X-ray diffraction.  
Download: https://www.rcsb.org/structure/2ZW3

**Expected AlphaFold WT result:** Four TM helices, plDDT high in TM regions, consistent with 2ZW3 topology.

**Expected AlphaFold mutant result:** Disordered 12-aa peptide, low plDDT throughout. No TM topology. The variant does not produce a remodeled Connexin-26; it produces no functional Connexin-26.

---

## Pathogenicity Interpretation

AlphaFold structure prediction **does not prove pathogenicity** and should not be cited as primary evidence.  
The pathogenicity of c.35delG / p.Gly12Valfs*2 is established by:

1. **ClinVar** — search `NM_004004.6(GJB2):c.35del` and verify accession before citing
2. **ClinGen Hearing Loss VCEP** — expert curated classification
3. **Kelsell et al., Nature 1997** — original GJB2 linkage to DFNB1
4. **Population frequency**: ~3% carrier frequency in European populations

AlphaFold here serves as **visual/structural illustration only**.

---

## Internal Note: MCORE-1 Hypothesis (Not Clinical Evidence)

> ⚠️ **This section is speculative / internal research context. It is not AlphaFold evidence and not clinical evidence. Do not cite it in clinical or regulatory submissions.**

The MCORE-1 project uses GJB2 c.35delG as a test case for an encoding hypothesis. In the MCORE-1 trit-tree representation of the 681-nucleotide GJB2 CDS, a deletion at position k=35 is predicted to produce a step-function CONSERVATION error profile (Theorem 1, Algebraic Carry Cascade). Empirical measurements on the encoded sequence are consistent with this prediction.

This is a property of the MCORE-1 encoding — not a property of the cochlea, the protein, or the clinical variant.

For MCORE-1 theoretical details see the paper at [github.com/vortexpixelz/mcore-1](https://github.com/vortexpixelz/mcore-1).

---

## File Manifest

```
alpha_fold_gjb2_c35delg_check/
├── README.md                              ← this file
├── GJB2_WT_P29033.fasta                   ← 226-aa WT sequence ✅
├── GJB2_c35delG_pGly12ValfsTer2.fasta     ← 12-aa mutant stub ✅
├── visualize_truncation.py                ← length/domain comparison figure
└── restriction_digest/                    ← DNA-level RFLP/dCAPS lane
```

## References

- Kelsell DP et al. *Nature* 1997;387:80–83.
- Maeda S et al. *Nature* 2009;458:597–602. (PDB: 2ZW3)
- AlphaFold DB entry P29033: https://alphafold.ebi.ac.uk/entry/P29033
- ClinVar search (verify accession): https://www.ncbi.nlm.nih.gov/clinvar/?term=NM_004004.6(GJB2):c.35del
