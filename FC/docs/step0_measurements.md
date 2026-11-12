# Step 0: FC Manuscript Page Allocation Measurements

All measurements taken from FC/main.pdf (25 pages, compiled from identical content as ICISC).
Fractional page positions determined by pdftotext line-level analysis.

---

## 1. Section-level page occupancy

| Section | Start | End | Pages |
|---------|-------|-----|-------|
| Title + Abstract + Keywords | 1.00 | 1.80 | 0.8 |
| **Sec 1 Introduction** | **1.80** | **3.39** | **1.6** |
| -- 1.1 Our Contribution | 2.80 | 3.39 | 0.6 |
| **Sec 2 Related Work** | **3.39** | **3.93** | **0.5** |
| **Sec 3 Preliminaries** | **3.93** | **6.44** | **2.5** |
| -- 3.1 Self-Attention | 4.13 | 4.40 | 0.3 |
| -- 3.2 Nystrom Linear Attention | 4.40 | 5.53 | 1.1 |
| -- 3.3 zk-SNARKs | 5.53 | 6.04 | 0.5 |
| -- 3.4 Freivalds' Algorithm | 6.04 | 6.44 | 0.4 |
| **Sec 4 Technical Overview** | **6.44** | **7.83** | **1.4** |
| **Sec 5 zkDietFormer (Protocol)** | **7.83** | **11.55** | **3.7** |
| -- Figures 1-3 (floats in Sec 4-5) | 7.00 | 8.81 | 1.8 |
| -- 5.1 Protocol Overview | 9.04 | 9.75 | 0.7 |
| -- 5.2 Nystrom-Based Attention | 9.75 | 10.51 | 0.8 |
| -- 5.3 Freivalds Verification | 10.51 | 11.55 | 1.0 |
| **Sec 6 Security** | **11.55** | **15.88** | **4.3** |
| -- 6.1 System & Threat Model | 11.67 | 13.96 | 2.3 |
| -- 6.2 Security Definition | 13.96 | 14.31 | 0.3 |
| -- 6.3 Security Analysis | 14.31 | 15.88 | 1.6 |
| **Sec 7 Experiments** | **15.88** | **20.91** | **5.0** |
| -- 7.1 Implementation | 16.15 | 17.26 | 1.1 |
| -- 7.2 Experimental Configuration | 17.26 | 17.47 | 0.2 |
| -- 7.3 Results | 17.47 | 20.68 | 3.2 |
| -- 7.4 Conclusion & Future Work | 20.68 | 20.91 | 0.2 |
| **BODY TOTAL** | **1.00** | **20.91** | **~20** |

---

## 2. Figure occupancy

| Figure | Page(s) | Occupancy | Content |
|--------|---------|-----------|---------|
| Fig 1(a)+(b) | 7 | 0.3 p | Two subfigures: Nystrom block decomposition + Freivalds check (external JPG) |
| Fig 2 | 8 top | 0.1 p | Overview diagram (external PNG, 0.9\textwidth) |
| Fig 3 | 8 | 0.7 p | Protocol (cryptocode \procedure, resizebox, 384pt overfull) |
| Fig 4 | 11.55-12.89 | 1.3 p | Relation (cryptocode \procedure, 26 lines + caption) |
| Fig 5 | 20.00-20.43 | 0.4 p | Multi-spec TikZ pgfplots (per-layer prove time) |
| **Total figures** | | **2.8 p** | |

---

## 3. Table occupancy

| Table | Page | Occupancy | Content |
|-------|------|-----------|---------|
| Table 1 | 17 | 0.2 p | Model configurations (5 rows) |
| Table 2 | 18 | 0.7 p | Full 2x2 factorial design, Tiny config (16 rows, resized) |
| Table 3 | 20 | 0.2 p | Quantization fidelity (1 data row) |
| **Total body tables** | | **1.1 p** | |
| Table 4 (Appendix B) | 24 | 0.4 p | MLP+LN costs (4 rows) |

---

## 4. Figure 4 (Relation) detail

Source lines: FC/main.tex 338-374 (37 lines of TeX, producing 26 numbered relation lines).

26 relation lines breakdown:

| Lines | Content | Count |
|-------|---------|-------|
| 1 | R(ins, wit) header | 1 |
| 2-5 | Parse ins, comwit, uncomwit, Q/K row decomposition | 4 |
| 6-8 | Q/K/V projection Freivalds: r_n^T Q = r_n^T X W^Q etc. | 3 |
| 9-12 | Segment averaging for loop: Q_tilde, K_tilde landmarks | 4 |
| 13-15 | Low-rank product Freivalds: Q K_tilde^T, Q_tilde K_tilde^T, Q_tilde K^T | 3 |
| 16-18 | Softmax 3 factors: F_tilde, A_tilde, B_tilde | 3 |
| 19-22 | Moore-Penrose 4 conditions (element-wise range check) | 4 |
| 23 | B_tilde V Freivalds | 1 |
| 24 | F_tilde A^+ Freivalds | 1 |
| 25 | Y = (F_tilde A^+)(B_tilde V) Freivalds | 1 |
| 26 | Y' = Y W^O Freivalds (output projection) | 1 |
| **Total** | | **26** |

Page occupancy: 1.3 pages (including caption).

---

## 5. Algorithm occupancy

| Algorithm | Page | Occupancy |
|-----------|------|-----------|
| Algorithm 1 (NystromAttention) | 10 | 0.5 p |
| Algorithm 2 (ComputeMPInverse, Appendix A) | 23 | 0.4 p |

---

## 6. Appendix occupancy

| Appendix | Page(s) | Occupancy | Content |
|----------|---------|-----------|---------|
| A: Newton-Schulz Iteration | 23.24-23.76 | 0.5 p | Algorithm 2 + 3 lines of text |
| B: MLP + LayerNorm Costs | 23.76-24.83 | 1.1 p | Discussion + Table 4 |
| C: Formal Security Definitions | 24.83-25.00 | 1.2 p | Completeness/Soundness/ZK formal statements + Real/Ideal experiment |
| **Total appendix** | | **2.8 p** | |

---

## 7. Budget summary

| Component | Pages |
|-----------|-------|
| Body text | 20.0 |
| References | 2.0 |
| Appendix | 2.8 |
| **Grand total** | **~25** |
| FC body limit | 15 |
| **Overage** | **5.0 pages** |
