# ICISC to FC Migration Report

## 1. ICISC vs FC Format Differences

| Item | ICISC | FC | Difference |
|------|-------|----|------------|
| Document class | `llncs.cls` v2.24 (2024-01-29) | `llncs.cls` v2.24 (2024-01-29) | None (byte-identical) |
| Class options | `[runningheads]` | `[runningheads]` | None |
| BibTeX style | `splncs04.bst` | `splncs04.bst` | None (byte-identical) |
| Body page limit | 20 pages (ICISC) | 15 pages (FC CFP) | FC is 5 pages shorter |
| Anonymity | Already anonymous | Blind review required | No change needed |

Both directories use the identical `llncs.cls` and `splncs04.bst`.
No class file changes, no style file changes, no margin/font/spacing adjustments.

## 2. Renamed Macros

None. No macro name collisions with the FC class. All macros from `macro.tex`
were copied without modification.

## 3. Reference Number Changes

Reference numbering is identical between ICISC and FC builds.
The `.bbl` files differ only in whitespace/line wrapping (BibTeX regeneration artifacts).
No hardcoded reference numbers were found in the body text; all citations use `\cite{}`.

## 4. Page Count and Limit

| Metric | Count |
|--------|-------|
| Body pages (incl. title, abstract, conclusion, competing interests) | 20 |
| Reference pages | ~2 (pages 21-22) |
| Appendix pages | 3 (pages 23-25) |
| Total pages | 25 |
| FC body limit | 15 |
| **Overage** | **5 pages** |

## 5. Recovery Candidates

Body overage is 5 pages. The following candidates are listed with estimated space,
without recommendation on which to cut. All decisions are deferred.

### A. Move to appendix

| Candidate | Current location | Estimated size | Effect on body argument |
|-----------|-----------------|----------------|------------------------|
| Sec 6.3 Security Analysis full proof sketch (Soundness + Pseudoinverse tolerance + ZK paragraphs) | pages 14-15 | ~1.5 pages | Would leave Theorem 1 statement in body; proof sketch moves to appendix. Body would reference appendix for proof. |
| Table 2 (full 4x4 factorial design, Tiny config) | page 17-18 | ~1 page (table + surrounding analysis subsubsections 7.3.1-7.3.4) | Core experimental results table. Body argument would need to summarize findings in text and reference appendix table. |
| MLP+LayerNorm discussion at end of Sec 7 (lines 676-677 referencing Appendix B) | page 20 | Already deferred; only 2 lines in body | Negligible recovery. |
| Figure 4 (Relation definition, cryptocode box) | pages 12-13 | ~1 page | Central formal artifact; moving weakens Sec 5 significantly. |
| Table 1 (model configurations) | page 17 | ~0.3 pages | Small table; easily moved but commonly expected in body. |

### B. Compress in place (content not deleted, only reformatted)

| Candidate | Current location | Estimated savings | Notes |
|-----------|-----------------|-------------------|-------|
| Sec 3 Preliminaries (3 pages) | pages 3-6 | ~1 page if zk-SNARK/CP-SNARK/CC-SNARK/Freivalds defs are shortened to 1-sentence pointers | Standard crypto community knowledge; FC reviewers may not need full definitions. |
| Sec 4 Technical Overview (1.5 pages) | pages 6-7 | ~0.5 pages if merged with Sec 5 intro | Some overlap with Sec 5.1 Protocol Overview. |
| Sec 2 Related Work (<1 page) | page 3 | ~0.25 pages | Already compact. |
| Subsubsections 7.3.1-7.3.4 (individual analysis paragraphs) | pages 18-19 | ~0.5 pages if merged into a single combined-analysis paragraph | Four short subsubsections could be consolidated. |

### C. Figures

| Figure | Pages | Estimated size | Notes |
|--------|-------|----------------|-------|
| Fig 1(a)+(b) (Nystrom approx + Freivalds check) | page 7 | ~0.5 pages | Two subfigures; could be shrunk. |
| Fig 2 (Overview) | page 8 | ~0.4 pages | Already at 0.9\textwidth. |
| Fig 3 (Protocol, cryptocode) | page 9 | ~0.7 pages (resizebox to columnwidth) | Hard to shrink without losing readability. |
| Fig 5 (TikZ multi-spec plot) | page 20 | ~0.4 pages | Could be moved to appendix but is main experimental result. |

### D. Out-of-scope attacks paragraph

| Candidate | Location | Size |
|-----------|----------|------|
| "Out-of-Scope Attacks" paragraph (Sec 6.2) | page 15 | ~0.3 pages |

## 6. Open Items Requiring Decision

1. **5-page overage**: Which combination of recovery candidates to apply.
   The body needs to shrink from 20 to 15 pages.

2. **Overfull hbox warnings**: 22 overfull hbox warnings exist (inherited from ICISC).
   Most are in the cryptocode protocol/relation figures (lines 243, 303, 371).
   The largest is 384pt at line 243 (Figure 3 protocol box).
   These are cosmetic and were present in the ICISC build as well.

3. **`\krev` and `\brev` macros**: Defined in `macro.tex` but never used in body text.
   They can be removed from macro.tex, but per instructions, magenta markup is not
   removed without authorization.

4. **Competing interests statement**: The `\begin{credits}` block contains only
   `\discintname` (no acknowledgements). FC requires anonymous submission. The
   generic "The authors have no competing interests..." statement is standard and
   should be acceptable, but verify against FC guidelines.

5. **Figure 3 (Protocol box)**: 384pt overfull hbox. The `\resizebox{\columnwidth}`
   is already applied but the box content is wider than columnwidth. This was
   present in ICISC too. May need `\resizebox{\textwidth}` or manual reformatting
   if FC reviewers flag it.

## Compilation Summary

- **Errors**: 0
- **Warnings**: 22 overfull hbox (all inherited from ICISC, none new)
- **Unresolved references**: 0
- **Unresolved citations**: 0
- **PDF metadata**: No author info (Creator: TeX, no Author field)

## Integrity Cross-Check

| Element | ICISC | FC | Match |
|---------|-------|----|-------|
| `\section` | 10 | 10 | Yes |
| `\subsection` | 15 | 15 | Yes |
| `\subsubsection` | 6 | 6 | Yes |
| `\paragraph` | 3 | 3 | Yes |
| `\begin{figure}` | 5 | 5 | Yes |
| `\begin{table}` | 4 | 4 | Yes |
| `\begin{algorithm}` | 2 | 2 | Yes |
| `\begin{theorem}` | 1 | 1 | Yes |
| `\begin{definition}` | 1 | 1 | Yes |
| `\label` | 42 | 42 | Yes |
| `\cite` | 44 | 44 | Yes |
| Total pages | 25 | 25 | Yes |

Body text is identical (diff shows only line 1 comment changed: "ICISC" to "FC").
Caption text is identical (no changes). No content modifications were made.

## Files in FC/

| File | Source | Notes |
|------|--------|-------|
| `main.tex` | Copied from ICISC, line 1 comment changed | Body text unchanged |
| `macro.tex` | Copied from ICISC verbatim | No changes |
| `references.bib` | Copied from ICISC verbatim | No changes |
| `llncs.cls` | Already in FC (identical to ICISC) | No changes |
| `splncs04.bst` | Already in FC (identical to ICISC) | No changes |
| `docs/migration_report.md` | New | This file |
| `samplepaper.tex` | Pre-existing FC template | Untouched |
| `fig1.eps` | Pre-existing FC template | Untouched |
| Images | Referenced via `../images/` | Shared with ICISC |
