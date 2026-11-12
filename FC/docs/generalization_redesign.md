# FC Generalization Redesign

## 1. Relation Redesign

### 1-1. Classification of current 26 relation lines

Source: FC/main.tex lines 344-370 (Figure 4).

| Line | Content | Category | Rationale |
|------|---------|----------|-----------|
| 1 | R(ins, wit) | Framework skeleton | Identical in all instances |
| 2 | parse ins = (X, r_n, r_m, Y'), wit = (comwit, uncomwit) | Framework skeleton | r_m dimension may differ but structure is the same |
| 3 | parse comwit | **Instance-specific** | Committed values differ: Nystrom commits A^+, F_tilde A^+, B_tilde V; Linformer commits EK, FV; SOFT commits A^+ (Gaussian) |
| 4 | parse uncomwit | **Instance-specific** | Nystrom: Q_tilde, K_tilde, 3 pre-softmax products. Linformer: none (no free witnesses). SOFT: similar to Nystrom |
| 5 | parse Q, K row decomposition | Common | All instances decompose Q, K into row vectors for segment operations. However, Linformer does not use this decomposition. **Reclassified: Nystrom+SOFT only** |
| 6 | r_n^T Q = r_n^T X W^Q | **Common** | Q/K/V projection is shared by all three instances |
| 7 | r_n^T K = r_n^T X W^K | **Common** | Same |
| 8 | r_n^T V = r_n^T X W^V | **Common** | Same |
| 9 | for j in {1,...,m}: | **Nystrom-specific** | Segment averaging. SOFT uses landmark sampling, not averaging. Linformer has no landmarks |
| 10 | q_tilde_j = mean(q_i), k_tilde_j = mean(k_i) | **Nystrom-specific** | Same |
| 11 | endfor | **Nystrom-specific** | Same |
| 12 | Q_tilde = [q_tilde_1,...,q_tilde_m]^T, K_tilde = ... | **Nystrom-specific** | SOFT constructs landmarks differently |
| 13 | r_n^T (Q K_tilde^T) = (r_n^T Q) K_tilde^T | **Instance-specific** | Nystrom: 3 low-rank kernel products. Linformer: 2 projection products E_i K, F_i V + 1 logit product. SOFT: 3 Gaussian kernel products |
| 14 | r_m^T (Q_tilde K_tilde^T) = (r_m^T Q_tilde) K_tilde^T | **Instance-specific** | Same |
| 15 | r_m^T (Q_tilde K^T) = (r_m^T Q_tilde) K^T | **Instance-specific** | Same |
| 16 | F_tilde = softmax(Q K_tilde^T / sqrt(d_k)) | **Instance-specific** | Nystrom: 3 softmax. Linformer: 1 softmax. SOFT: 3 Gaussian kernel (no softmax) |
| 17 | A_tilde = softmax(Q_tilde K_tilde^T / sqrt(d_k)) | **Instance-specific** | Same |
| 18 | B_tilde = softmax(Q_tilde K^T / sqrt(d_k)) | **Instance-specific** | Same |
| 19 | ||A A^+ A - A||_max <= epsilon | **Nystrom+SOFT shared** | MP condition 1. Linformer: absent |
| 20 | ||A^+ A A^+ - A^+||_max <= epsilon | **Nystrom+SOFT shared** | MP condition 2 |
| 21 | ||(A A^+)^T - A A^+||_max <= epsilon | **Nystrom+SOFT shared** | MP condition 3 |
| 22 | ||(A^+ A)^T - A^+ A||_max <= epsilon | **Nystrom+SOFT shared** | MP condition 4 |
| 23 | r_m^T (B_tilde V) = (r_m^T B_tilde) V | **Instance-specific** | Nystrom: 3-stage chain. Linformer: 1-stage P*FV. SOFT: 3-stage chain |
| 24 | r_n^T (F_tilde A^+) = (r_n^T F_tilde) A^+ | **Instance-specific** | Same |
| 25 | r_n^T Y = r_n^T (F_tilde A^+)(B_tilde V) | **Instance-specific** | Same |
| 26 | r_n^T Y' = (r_n^T Y) W^O | **Common** | Output projection shared by all instances |

**Summary count:**

| Category | Lines | Count |
|----------|-------|-------|
| Framework skeleton | 1-2 | 2 |
| Common (all 3) | 6-8, 26 | 4 |
| Nystrom-specific | 5, 9-12 | 4 |
| Instance-specific (varies per kernel) | 3-4, 13-18, 23-25 | 10 |
| Nystrom+SOFT shared (MP) | 19-22 | 4 |
| Nystrom-only total | 5, 9-12 = 4; plus 13-18 + 23-25 variants | 18 |
| **Common core** | | **6 lines** |

### 1-2. Generalized relation

#### General form

The framework verifies Y = G_1 G_2 ... G_j V projected through W^O, where each G_i
is a low-rank factor. The general relation has three layers:

**Layer A: Common prefix (6 lines)**
```
1   R(ins, wit):
2     parse ins = (X, r, Y'), wit = (comwit, uncomwit)
3     r_n^T Q = r_n^T X W^Q                    [Freivalds]
4     r_n^T K = r_n^T X W^K                    [Freivalds]
5     r_n^T V = r_n^T X W^V                    [Freivalds]
6     r_n^T Y' = (r_n^T Y) W^O                 [Freivalds]
```

**Layer B: Instance-parametrized middle (variable)**
```
    // Factor generation (instance-specific)
    // Low-rank product Freivalds checks (instance-specific count)
    // Non-linearity enforcement (softmax / Gaussian kernel / none)
    // Witness verification (MP conditions / none)
    // Chain assembly: Y = G_1 G_2 ... G_j V (Freivalds)
```

**Layer C: Commit structure specification (per instance)**
```
    comwit = {weights, lookup operands, aux intermediates}
    uncomwit = {values uniquely determined from comwit by in-circuit constraints}
```

#### Commit classification principle

This principle, confirmed empirically in the Linformer implementation, can be stated
at the framework level:

**Principle (Commit Necessity).** Let M be a matrix appearing in a Freivalds
projected identity. M requires pre-challenge commitment (inclusion in comwit) if and
only if no element-wise in-circuit constraint uniquely determines each entry of M from
already-committed data.

Concretely:
- **Aux-commit required**: Outputs of enforce_freivalds (projection-only constraint,
  not element-wise). Examples: Q, K, V (projection outputs), EK, FV (Linformer),
  F_tilde A^+, B_tilde V, Y (Nystrom chain intermediates).
- **No commit needed (omega)**: Values recoverable element-wise from d1-committed data.
  Examples: pre-softmax logits (recovered from lookup index + remainder via
  enforce_softmax element-wise equality), scaled Q/K (recovered from projection
  output + scaling remainder via enforce_scaling element-wise equality),
  segment-averaged landmarks (recovered from Q/K rows + division remainder).

**Evidence**: In the Linformer implementation, pre-softmax logit Q_sim_logit was
confirmed to not need commitment. The recovery is injective: given the triple
(table_idx, r_sm, R_matmul_logit) committed in d1, the enforce_softmax equality
```
(Q_sim[i][j] * 2^k + R[i][j]) * M_sm = table_idx[i][j] * 2^(2k) + r_sm[i][j]
```
uniquely determines Q_sim[i][j]. Injectivity was verified empirically over all
16,384 elements (S*k = 128*32 for one batch/head) with zero collisions.

Conversely, EK and FV (outputs of enforce_freivalds only, no element-wise
successor constraint) were confirmed to require aux commitment. Without commitment,
an adversary observing the Freivalds challenge r can adaptively choose a different
EK' satisfying the projection constraint (k equations for k*D unknowns, an
underdetermined system).

**Can this be elevated to a section-level principle?** Yes. The three-category
classification in current Section 6.3 (public values, committed-before-challenge
values, uniquely-determined values) already implicitly contains this principle.
Promoting it to Section 3 or Section 4 would provide a framework-level vocabulary
that each instance section can reference. Recommendation: state the principle in
Section 4 (Technical Overview) as a design guideline, then reference it in each
instance's relation specification.

### 1-3. Instance delta relations

#### Nystrom delta (current, baseline)

Lines added to common prefix: 18 lines

```
3n   parse comwit := {(W^i, o_i)_{Q,K,V,O}, (lk, o_lk),
       (Q, K, V, A^+, F_tilde A^+, B_tilde V, Y, o_aux)}
4n   parse uncomwit := (Q_tilde, K_tilde, Q K_tilde^T,
       Q_tilde K_tilde^T, Q_tilde K^T)
5n   parse Q = [q_1,...,q_n]^T, K = [k_1,...,k_n]^T
     -- Landmark generation (4 lines) --
9n   for j in {1,...,m}:
10n    q_tilde_j = mean(q_i), k_tilde_j = mean(k_i)
11n  endfor
12n  Q_tilde = [...], K_tilde = [...]
     -- Low-rank Freivalds (3 lines) --
13n  r_n^T (Q K_tilde^T) = (r_n^T Q) K_tilde^T
14n  r_m^T (Q_tilde K_tilde^T) = (r_m^T Q_tilde) K_tilde^T
15n  r_m^T (Q_tilde K^T) = (r_m^T Q_tilde) K^T
     -- Softmax (3 lines) --
16n  F_tilde = softmax(Q K_tilde^T / sqrt(d_k))
17n  A_tilde = softmax(Q_tilde K_tilde^T / sqrt(d_k))
18n  B_tilde = softmax(Q_tilde K^T / sqrt(d_k))
     -- MP conditions (4 lines) --
19n  ||A A^+ A - A||_max <= epsilon
20n  ||A^+ A A^+ - A^+||_max <= epsilon
21n  ||(A A^+)^T - A A^+||_max <= epsilon
22n  ||(A^+ A)^T - A^+ A||_max <= epsilon
     -- Chain (3 lines) --
23n  r_m^T (B_tilde V) = (r_m^T B_tilde) V
24n  r_n^T (F_tilde A^+) = (r_n^T F_tilde) A^+
25n  r_n^T Y = r_n^T (F_tilde A^+)(B_tilde V)
```

Total delta: **18 lines** (5n+4 landmark + 3 kernel + 3 softmax + 4 MP + 3 chain)

Freivalds identity count: 10 (lines 6-8, 13-15, 23-25, 26 from common)

#### Linformer delta

Lines added to common prefix: **9 lines**

```
3l   parse comwit := {(W^i, o_i)_{Q,K,V,O}, (E_i, F_i, o_proj),
       (lk, o_lk), (Q, K, V, EK, FV, Y, o_aux)}
4l   parse uncomwit := (Q(EK)^T)    [pre-softmax logit, omega]
     -- Projection Freivalds (2 lines) --
p1   r_k^T (E_i K) = (r_k^T E_i) K
p2   r_k^T (F_i V) = (r_k^T F_i) V
     -- Logit Freivalds (1 line) --
p3   r_n^T (Q (EK)^T) = (r_n^T Q) (EK)^T
     -- Softmax (1 line) --
p4   P = softmax(Q (EK)^T / sqrt(d_k))
     -- Chain (1 line) --
p5   r_n^T Y = (r_n^T P) (FV)
```

Notes:
- No segment averaging, no landmarks, no MP conditions, no epsilon tolerance.
- EK and FV are aux-committed (Freivalds-only, no element-wise successor).
- Pre-softmax logit is omega (element-wise determined via enforce_softmax).
- E_i, F_i dimensions are k x n, so they are n-dependent. This means c_W changes
  when n changes (unlike Nystrom where c_W is n-independent).

Total delta: **9 lines** (2 parse + 2 projection + 1 logit + 1 softmax + 1 chain + 2 implied from parse)

Freivalds identity count: 8 (lines 6-8 common + p1-p3 + p5 + 26 common)

#### SOFT delta (partially confirmed)

Based on the SOFT paper (Lu et al., NeurIPS 2021, arXiv:2110.11945):

SOFT replaces softmax with a Gaussian kernel:
```
S_{i,j} = exp(-||Q_i - K_j||^2 / (2 sqrt(d_e)))
```
and uses Nystrom decomposition with Moore-Penrose pseudoinverse (Newton-Raphson).

Lines added to common prefix: **~17 lines** (estimated)

```
3s   parse comwit := {(W^i, o_i)_{Q,K,V,O}, (lk, o_lk),
       (Q, K, V, A^+, F A^+, B V, Y, o_aux)}
4s   parse uncomwit := (Q_tilde, K_tilde, pairwise distances)
     -- Landmark generation (method unconfirmed) --
9s   [landmark selection/sampling: unconfirmed whether segment
      averaging, random sampling, or learned]
     -- Low-rank Freivalds (3 lines, same structure as Nystrom) --
13s  r_n^T (G_F) = ...   where G_F = exp(-||Q - K_tilde||^2 / ...)
14s  r_m^T (G_A) = ...   where G_A = exp(-||Q_tilde - K_tilde||^2 / ...)
15s  r_m^T (G_B) = ...   where G_B = exp(-||Q_tilde - K||^2 / ...)
     -- Gaussian kernel (3 lines, replacing softmax) --
16s  F = GaussianKernel(Q, K_tilde)
17s  A = GaussianKernel(Q_tilde, K_tilde)
18s  B = GaussianKernel(Q_tilde, K)
     -- MP conditions (4 lines, same as Nystrom) --
19s-22s  [identical to Nystrom]
     -- Chain (3 lines, same structure as Nystrom) --
23s-25s  [identical to Nystrom]
```

**Unconfirmed items:**
- Landmark generation method (segment averaging vs. random sampling vs. learned)
- Exact Gaussian kernel circuit enforcement (element-wise exp of squared distance
  is expensive in-circuit; may require lookup tables different from softmax tables)
- Whether the Gaussian kernel can be enforced via the same Lasso lookup mechanism
  as softmax (the input domain differs: softmax takes dot products, Gaussian takes
  squared L2 distances)
- DConv residual connection (SOFT paper mentions it; whether it would be included
  in the relation is unconfirmed)

Total delta: **~17 lines** (similar to Nystrom)

Freivalds identity count: 10 (same structure as Nystrom)

### 1-4. Page estimate

**Current Figure 4**: 26 lines = 1.3 pages (measured).

**Option X: Single generalized figure + instance table**
- Generalized relation: 6 common + 5 parametrized placeholders = ~11 lines
- Instance comparison table (showing delta per instance): ~12 rows, ~0.3 pages
- Total: ~0.7 pages (figure) + 0.3 pages (table) = 1.0 pages
- **Net change: -0.3 pages** vs. current

**Option Y: Generalized figure + 3 full delta figures**
- Generalized relation: ~11 lines = 0.5 pages
- Nystrom delta figure: 18 lines = ~0.8 pages
- Linformer delta figure: 9 lines = ~0.5 pages
- SOFT delta figure: 17 lines = ~0.8 pages
- Total: ~2.6 pages
- **Net change: +1.3 pages** (prohibitive for 15-page target)

**Option Z: Generalized figure in body + deltas in appendix**
- Body: generalized relation (~0.5p) + instance table (~0.3p) = 0.8 pages
- Appendix: Nystrom full (0.8p) + Linformer full (0.5p) + SOFT full (0.8p) = 2.1 pages
- **Net body change: -0.5 pages** vs. current

Recommendation: Option Z (generalized relation + table in body, full instances in
appendix) gives the best body-page savings while preserving formal completeness.
Option X is also viable if appendix space is constrained.

---

## 2. Figure Redesign

### 2-1. Figure 1 (Nystrom block decomposition + Freivalds check)

Current: (a) Nystrom matrix approximation (JPG), (b) Freivalds check (JPG).
Occupancy: 0.3 pages.

**Option A: Replace (a) with general projection chain, delete (b)**
- Shows abstract G_1 G_2 ... G_j V chain with Freivalds checks on each factor
- Pro: Framework-level figure, not tied to any instance
- Con: Loses the concrete visual intuition of Nystrom block decomposition;
  Freivalds check diagram in (b) is pedagogically valuable
- Estimated size: 0.2 pages (single diagram)

**Option B: Replace (a) with general chain, keep (b)**
- (a) shows abstract chain, (b) shows Freivalds verification of one factor
- Pro: General framing + keeps the concrete verification illustration
- Con: (a) becomes somewhat abstract without a concrete example
- Estimated size: 0.3 pages (no change)

**Option C: Keep as is, add caption qualifier**
- Caption: "Illustrated for the Nystrom instance; see Table X for other instances"
- Pro: No figure redrawing, minimal effort
- Con: First impression remains Nystrom-specific; reviewers may still perceive
  the work as Nystrom-only
- Estimated size: 0.3 pages (no change)

Recommendation: Option B. The Freivalds check is instance-independent and worth
keeping. Replacing (a) with a general chain makes the framework claim visible
from the first figure.

### 2-2. Figure 2 (Framework overview)

Current: Left side shows Nystrom single attention layer, right side shows circuit.
Occupancy: 0.1 pages (PNG, compact).

**Redesign proposal**: Replace the left side with an abstract pipeline:
```
X -> [Q/K/V Projection] -> [Low-Rank Factor Generation (instance-specific)]
  -> [Non-linearity] -> [Chain Assembly] -> Y -> [O Projection] -> Y'
```
The right side (circuit structure) remains the same since the proving pipeline is
instance-independent.

A small callout box or color-coded labels can indicate where instance-specific
operations occur.

Estimated size: 0.1-0.2 pages (similar to current).

### 2-3. Figure 3 (Protocol)

Current: 0.7 pages, 384pt overfull hbox.
Source: FC/main.tex lines 228-246 (cryptocode \procedure environment).

**Overfull cause**: The \procedure box content (particularly the u and omega
definitions) exceeds \columnwidth even after \resizebox. The resizebox scales
to columnwidth but the content's natural width is columnwidth + 384pt.

**Fix options**:
1. Break the u and omega definitions into multiple lines (most effective)
2. Use \resizebox{\textwidth} instead of \resizebox{\columnwidth} (LNCS is
   single-column, so these should be equal; the overfull is from content
   inside the box that exceeds the box width before resizing)
3. Reduce font size inside the procedure box
4. Move to appendix

**Protocol generalization**: The current protocol defines:
- u := {(W^i, o_i), (ins, o), (W^i, o_i), (Q, K, V, A^+, FA^+, BV, Y, o_aux)}
- omega := {Q_tilde, K_tilde, pre-softmax products}

For Linformer:
- u := {(W^i, o_i), (E_i, F_i, o_proj), (lk, o), (Q, K, V, EK, FV, Y, o_aux)}
- omega := {logit, P}  (no free witnesses)

These can be generalized:
- u := {weights, instance-specific aux intermediates, lookup operands}
- omega := {values determined element-wise from committed data}

The protocol structure (commit -> challenge -> prove -> verify) is identical
across instances. Only the u/omega contents change.

**Recommendation**: If the protocol figure stays in body, generalize u and omega
to use abstract notation and add a footnote or table mapping to each instance.
If moved to appendix, show instance-specific versions there.

### 2-4. Instance comparison table (new)

Proposed column structure:

| Column | Nystrom | Linformer | SOFT |
|--------|---------|-----------|------|
| Attention formula | F_tilde A^+ B_tilde V | softmax(Q(EK)^T/sqrt(d)) FV | F A^+ B V (Gaussian) |
| Low-rank factors | 3 (F_tilde, A_tilde^+, B_tilde) | 2 (EK, FV) + 1 logit | 3 (F, A^+, B) |
| Factor dimensions | n x m, m x m, m x n | k x d, k x d, n x k | n x m, m x m, m x n |
| Factor source | Input-derived (segment avg) | Learned weights (E_i, F_i) | Input-derived (unconfirmed) |
| Non-linearity | softmax x 3 | softmax x 1 | Gaussian kernel x 3 |
| Witness supply | A^+ (Newton-Schulz) | None | A^+ (Newton-Raphson) |
| Commit targets (aux) | Q,K,V, A^+, FA^+, BV, Y | Q,K,V, EK, FV, Y | Q,K,V, A^+, FA^+, BV, Y |
| Omega set | Q_tilde, K_tilde, pre-sm | logit, P | (unconfirmed) |
| MP conditions | 4 | 0 | 4 |
| Freivalds identities | 10 | 8 | 10 |
| Param n-dependence | None (m independent of n) | E_i, F_i are k x n | (unconfirmed) |
| epsilon tolerance | Yes (MP residual) | No | Yes (MP residual) |

Estimated occupancy: **0.3-0.4 pages** (11 rows, 4 columns, footnotesize).

---

## Corrected Addition Tally and Recovery Targets

### 2-INST (Nystrom + Linformer)

| Item | Est. addition | Basis |
|------|--------------|-------|
| Instance comparison table (new, Sec 5) | +0.3 p | 11-row table, ~Table 1 width |
| Sec 3.2 restructuring: general + 2 instance summaries | +0.4 p | Current 1.1p → ~1.5p |
| Linformer rows in Table 2 | +0.3 p | 2 extra configs (Lin-Naive, Lin-Freivalds) × 4 n-blocks |
| Linformer curves in Figure 5 | +0.1 p | Additional data series on same plot |
| Linformer result discussion in Sec 7.3 | +0.2 p | 1-2 paragraphs |
| Sec 6 modifications (functionality, soundness, assumptions) | +0.4 p | In-place rewording + assumption table |
| Related Work update | +0.1 p | 2-3 sentences |
| Generalized relation (Option Z body) | −0.5 p | Current 1.3p → 0.8p |
| **Total 2-INST additions** | **+1.3 p** | |

| Component | Pages |
|-----------|-------|
| Current body | 20.0 |
| 2-INST additions | +1.3 |
| FC body limit | 15.0 |
| **Recovery needed (2-INST)** | **6.3 p** |

### 3-INST (Nystrom + Linformer + SOFT)

| Item | Est. addition | Basis |
|------|--------------|-------|
| Instance comparison table (new, Sec 5) | +0.3 p | Same table, one extra column |
| Sec 3.2 restructuring: general + 3 instance summaries | +0.5 p | Current 1.1p → ~1.6p |
| Lin + SOFT rows in Table 2 | +0.7 p | 4 extra configs × 4 n-blocks; 16 → 32 rows (0.7p → ~1.4p) |
| Figure 5 expansion (3 instances) | +0.1 p | Single plot overlay; +0.4p if 2×2 subplot |
| Lin + SOFT result discussion in Sec 7.3 | +0.4 p | 2-3 paragraphs (SOFT speculative without implementation) |
| Sec 6 modifications | +0.5 p | Extra Gaussian kernel assumption, SOFT-specific epsilon |
| Related Work update | +0.1 p | 3-4 sentences (+ SOFT citation) |
| Generalized relation (Option Z body) | −0.5 p | Same as 2-INST |
| **Total 3-INST additions** | **+2.1 p** | |

| Component | Pages |
|-----------|-------|
| Current body | 20.0 |
| 3-INST additions | +2.1 |
| FC body limit | 15.0 |
| **Recovery needed (3-INST)** | **7.1 p** |

### Transition cost (3-INST → 2-INST fallback)

If SOFT is dropped after initial 3-INST drafting:

| Rollback item | Savings |
|---------------|---------|
| Remove SOFT Table 2 rows | −0.4 p |
| Remove SOFT discussion | −0.2 p |
| Remove SOFT Sec 6 assumptions | −0.1 p |
| Remove SOFT Sec 3 summary | −0.1 p |
| **Total rollback** | **~0.8 p** |

The framework structure (generalized relation, Option Z, parametrized security) does not change between 2-INST and 3-INST. Only content volume differs.

---

## 3. Security Section Redesign

### 3-1. Functionality parametrization by instance

**Current** (line 386): "the quantized Nyström attention pipeline of Figure 4" — hardcoded to Nystrom.

**Generalized**: Parametrize by instance identifier $\mathcal{I}$:

```
F^{ε_I}_{zkdiet, I}(W, X)
```

where $\mathcal{I} \in \{\text{Nystrom}, \text{Linformer}, \text{SOFT}\}$.

**Required text changes**:
- Definition 1 (line 427): Replace $\mathcal{F}^{\varepsilon}_{\mathsf{zkdiet}}$ with $\mathcal{F}^{\varepsilon_{\mathcal{I}}}_{\mathsf{zkdiet}, \mathcal{I}}$ throughout.
- Sec 6.1 (line 386): Replace "quantized Nyström attention pipeline" with "quantized low-rank attention pipeline for instance $\mathcal{I}$".
- Theorem 1 (line 440): Add "for any supported instance $\mathcal{I}$" to the statement.

**Page impact**: Negligible (in-place symbol changes).

### 3-2. Epsilon decomposition

**Current**: ε is a single scalar tolerance that absorbs both the Moore-Penrose pseudoinverse residual and quantization rounding artifacts. The soundness paragraph (line 445) treats quantization as "absorbed by the ε-tolerant functionality $\mathcal{F}^{\varepsilon}_{\mathsf{zkdiet}}$." The Pseudoinverse tolerance paragraph (lines 447-454) treats ε as the MP acceptance bound.

**Generalized decomposition**:

| Source | Nystrom | Linformer | SOFT |
|--------|---------|-----------|------|
| MP pseudoinverse residual (ε_MP) | Present (Newton-Schulz, 4 conditions) | **Absent** | Present (Newton-Raphson, 4 conditions) |
| Quantization residual | Absorbed by defining functionality over quantized field; exact in-circuit via Euclidean division uniqueness | Same | Same |

For Linformer, ε = 0 (no pseudoinverse tolerance), so the functionality becomes $\mathcal{F}_{\mathsf{zkdiet}, \text{Lin}}$ without the ε superscript. The quantization "residual" is not a tolerance at all — Euclidean division is unique in-circuit, so the quotient-remainder pair is exact once the relation holds. The functionality simply *is* the quantized computation.

**Required text changes**:
- Soundness paragraph (line 445): Remove "Any residual discrepancy introduced by clamping or rounding during lookup-index derivation is a quantization artifact absorbed by the ε-tolerant functionality." Restate at framework level: quantization is exact in-circuit (Euclidean division uniqueness), defining the functionality rather than introducing tolerance.
- Pseudoinverse tolerance paragraph (lines 447-454): Qualify as "applicable to instances employing a pseudoinverse witness (Nystrom, SOFT). For instances without a pseudoinverse (Linformer), this paragraph and assumption (v) are vacuous."

**Page impact**: ~0 (removal and restatement roughly cancel).

### 3-3. Soundness error bound generalization

**Current** (line 445): "Each equality in lines 6–8, 13–15, and 23–26 of Figure 4 is a rank-one projection of a matrix identity" and "A union bound over the ten projected identities gives a total soundness error of $10/|\mathbb{F}| + \mathsf{negl}(\lambda)$."

Two problems: (a) hardcoded line numbers tied to the Nystrom-specific Figure 4, and (b) hardcoded identity count "ten."

**Generalized**: Replace with parametric form:

```
N_I / |F| + negl(λ)
```

| Instance | Common identities | Instance-specific identities | Total N_I |
|----------|-------------------|------------------------------|-----------|
| Nystrom | 4 (Q/K/V proj + O proj) | 6 (3 kernel product + 3 chain) | 10 |
| Linformer | 4 | 4 (2 proj + 1 logit + 1 chain) | 8 |
| SOFT | 4 | 6 (3 kernel product + 3 chain) | 10 |

The hardcoded "lines 6-8, 13-15, and 23-26" must be replaced. Under Option Z (generalized relation in body), the soundness argument references:
- "The $N_{\text{common}} = 4$ common projected identities (Q/K/V projection and output projection)"
- "The $N_{\mathcal{I}} - 4$ instance-specific projected identities (see Table X for per-instance counts)"

This is self-contained via the comparison table rather than via Figure 4 line numbers.

**Required text changes**:
- Replace specific line references with the parametric form.
- Replace "ten" with $N_{\mathcal{I}}$.
- The comparison table (Step 2-4) already includes "Freivalds identities" row with counts 10/8/10.

**Page impact**: ~0 (in-place replacement).

### 3-4. Assumption (v) instance-conditional separation

**Current** (line 440): "(v) well-conditionedness of the landmark softmax matrix, i.e., $\sigma_{\min}(\tilde{A}) \geq \sigma_0 > 0$ for a fixed public constant $\sigma_0$."

| Instance | Assumption (v) needed? | Matrix conditioned |
|----------|------------------------|-------------------|
| Nystrom | Yes | Landmark softmax matrix $\tilde{A}$ |
| Linformer | **No** (no pseudoinverse, no landmark matrix) | — |
| SOFT | Yes | Landmark Gaussian kernel matrix $A_{\text{Gauss}}$ |

**Generalized**: Restate assumption (v) as instance-conditional:

> "(v) [If $\mathcal{I}$ employs a pseudoinverse:] well-conditionedness of the instance's kernel matrix, i.e., $\sigma_{\min}(A_{\mathcal{I}}) \geq \sigma_0 > 0$."

For Linformer, assumption (v) is vacuously satisfied (no pseudoinverse). For SOFT, the conditioned matrix is a Gaussian kernel matrix, not a softmax matrix — the nature of the non-linearity changes.

**Implication for the Pseudoinverse tolerance paragraph**: The perturbation bound $\|Z^* - \tilde{A}^+\| \leq O(\varepsilon \|\tilde{A}^+\|)$ applies only when assumption (v) is active. Add: "For instances without a pseudoinverse (e.g., Linformer), lines 19-22 and assumption (v) are absent, and the soundness argument reduces to the Freivalds union bound over $N_{\mathcal{I}}$ identities alone."

**Page impact**: +0.1p (one added sentence).

### 3-5. Cross-configuration binding (c_W n-dependence)

**Current** (line 384): "the provider publishes a single commitment $c_W$ to its weights under a circuit-independent key, so that every subsequent response, including responses produced under a circuit instantiated for a different sequence length, is bound to one and the same model."

**Problem for Linformer**: The Linformer projection matrices $E_i, F_i \in \mathbb{R}^{k \times n}$ change dimension with $n$. Therefore:

| Instance | Weights in c_W | n-dependent? | Cross-n binding? |
|----------|---------------|--------------|-------------------|
| Nystrom | $\{W^Q, W^K, W^V, W^O\}$ per layer | No | **Yes** |
| Linformer | $\{W^Q, W^K, W^V, W^O, E_1..E_H, F_1..F_H\}$ per layer | Yes ($E_i, F_i$ are $k \times n$) | **No** |
| SOFT | $\{W^Q, W^K, W^V, W^O\}$ per layer | No (landmarks input-derived) | **Yes** |

Source: linformer_dev_plan.md §전역 가중치 커밋의 n 의존성: "E_i, F_i의 차원이 k×n이므로 n이 바뀌면 사영 행렬이 달라진다. 따라서 전역 커밋 c_W는 n마다 별도로 계산해야 하며."

**Options**:

(a) **Acknowledge as instance property**: Cross-n binding is a property of instances with n-independent weights. Linformer's projection matrices are n-dependent, so $c_W$ binds only within a fixed $n$. Add "Cross-n binding: Yes/No/Yes" to the comparison table.

(b) **Split commitment**: Commit n-independent weights in $c_{W,\text{core}}$ (cross-n) and n-dependent weights in $c_{W,n}$ (per-n). Verifier checks both.

(c) **Exclude Linformer from cross-n claims**: State that Linformer requires per-configuration commitment.

**Recommendation**: Option (a). Cross-n binding is a genuine advantage of input-derived low-rank methods (Nystrom, SOFT) over learned-projection methods (Linformer). Acknowledging it enriches the comparative analysis.

**Required text changes**:
- Sec 6.1 (line 384): Qualify: "For instances with n-independent weights (Nystrom, SOFT), the provider publishes a single $c_W$... For instances with n-dependent projection weights (Linformer), $c_W$ must be re-issued for each sequence length."
- Comparison table: Add row "Cross-n binding."
- "Inference integrity" (line 416): Qualify to "the very weights fixed by the published commitment(s)."

**Page impact**: +0.1p.

### 3-6. Commit classification principle elevation

**Current state**: The three-category classification (public / committed-before-challenge / uniquely-determined) appears only in the soundness proof paragraph (line 445). It is the most important structural insight for generalization, yet it is buried in prose.

**Proposal**: Elevate to a named principle in Section 4 (Technical Overview):

> **Principle (Commit Necessity).** A matrix $M$ appearing in a Freivalds projected identity requires pre-challenge commitment if and only if no element-wise in-circuit constraint uniquely determines each entry of $M$ from already-committed data.

Then in each instance's specification (comparison table or appendix), reference this principle to justify the commit structure.

**Benefits**:
- Provides framework-level vocabulary that the soundness argument references once
- Makes the three-category classification explicit and named rather than re-derived per instance
- Allows per-instance commit structures to be justified by citation rather than re-argument

**Required text changes**:
- Add ~3 sentences to Section 4 stating the principle
- Refactor the three-category sentence in the soundness paragraph to reference the principle by name
- Instance comparison table already includes "Commit targets (aux)" and "Omega set" rows

**Page impact**: +0.15p (new Sec 4 text) − 0.05p (shortened soundness paragraph) = +0.1p net.

### 3-7. Option Z soundness self-containedness

**Question**: If full instance-specific relations are in the appendix (Option Z), can the body soundness argument remain self-contained?

**Current soundness references** (line 445):
1. Specific Figure 4 line numbers: "lines 6-8, 13-15, and 23-26"
2. Three-category matrix classification
3. Count: "ten projected identities"
4. Specific committed intermediates: "$Q, K, V, \tilde{A}^+, \tilde{F}\tilde{A}^+, \tilde{B}V, Y$"

**Under Option Z, each reference is resolved as follows**:

| Reference | Resolution | Self-contained? |
|-----------|-----------|-----------------|
| Line numbers → | Generalized relation body figure (abstract identity placeholders) + comparison table counts | Yes, via table |
| Three-category classification → | Commit Necessity principle in Sec 4 (Step 3-6) | Yes, via principle |
| "ten" → | $N_{\mathcal{I}}$ from comparison table | Yes, via table |
| Specific intermediates → | "the aux intermediates listed in Table X for each instance $\mathcal{I}$" | Yes, via table |

**Conclusion**: Option Z soundness is self-contained provided:

1. The comparison table includes: Freivalds identity count, committed intermediates (abbreviated), and epsilon status per instance. **(Already in Step 2-4 proposal.)**
2. The Commit Necessity principle is stated in body Sec 4. **(Proposed in Step 3-6.)**
3. The generalized relation figure shows abstract identity placeholders with notation matching the soundness argument. **(Proposed in Step 1-2.)**

All three conditions are met. **No additional body content is needed for soundness self-containedness under Option Z.**

**Page impact**: 0 (no content beyond Steps 3-1 through 3-6).

### 3-S. Security redesign summary

| Item | Sec 6 text change | Page impact |
|------|-------------------|-------------|
| 3-1 Functionality parametrization | Symbol replacements in Def 1, Thm 1, Sec 6.1 | ~0 |
| 3-2 Epsilon decomposition | Remove redundant sentence, add framework-level statement | ~0 |
| 3-3 Soundness error bound | Replace line refs with parametric $N_{\mathcal{I}}/|\mathbb{F}|$ | ~0 |
| 3-4 Assumption (v) conditional | Add 1 sentence excluding Linformer | +0.1 |
| 3-5 Cross-n binding | Add 1-2 sentences qualifying cross-n for Linformer | +0.1 |
| 3-6 Commit principle elevation | 3 sentences in Sec 4; shorten soundness paragraph | +0.1 |
| 3-7 Option Z compatibility | No additional content | 0 |
| **Total Sec 6 page impact** | | **+0.3 p** |

Note: The +0.4p estimate in the addition tally (Step 0 correction) included +0.1p margin; the itemized total here is +0.3p.

---

## 4. 15-Page Composition Plans

### Recovery source catalog

| ID | Source | Recovery | Type | Notes |
|----|--------|----------|------|-------|
| R1 | Sec 3 compress (defs → 1-sentence pointers) | 1.0 p | Compress | zk-SNARK/CP-SNARK/Freivalds defs to citations |
| R2 | Sec 4/5.1 merge (remove overlap) | 0.5 p | Compress | Technical overview + protocol overview combined |
| R3 | Sec 6.3 proof sketch → appendix | 1.5 p | Move | Keep Thm 1 statement + 1-paragraph summary in body |
| R4 | Table 2 → appendix | 0.8 p (2-INST) / 1.2 p (3-INST) | Move | Keep 1-paragraph summary with key findings |
| R5 | Fig 3 (Protocol) → appendix | 0.7 p | Move | Body references appendix figure |
| R6 | Sec 7.3 subsubsections → single analysis | 0.5 p | Compress | Four subsubsections → one combined paragraph |
| R7 | Out-of-scope attacks → appendix | 0.3 p | Move | |
| R8 | Sec 2 compress | 0.25 p | Compress | Already tight |
| R9 | Fig 5 → appendix | 0.4 p | Move | Main experimental plot; moving costly to narrative |
| R10 | Table 1 → appendix | 0.3 p | Move | Model configs commonly expected in body |
| R11 | Fig 1 shrink | 0.1 p | Compress | Reduce to single diagram |
| R12 | Abstract/intro tighten | 0.2 p | Compress | Remove Nystrom-specific language, condense |

### 4-1. 2-INST compositions (target: 6.3 p)

#### Plan 2A: "Appendix-heavy, body lean"

| Applied | Source | Save |
|---------|--------|------|
| ✓ | R1 Sec 3 compress | 1.0 |
| ✓ | R2 Sec 4/5.1 merge | 0.5 |
| ✓ | R3 Sec 6.3 → appendix | 1.5 |
| ✓ | R4 Table 2 → appendix | 0.8 |
| ✓ | R5 Fig 3 → appendix | 0.7 |
| ✓ | R6 Sec 7.3 merge | 0.5 |
| ✓ | R7 Out-of-scope → appendix | 0.3 |
| ✓ | R8 Sec 2 compress | 0.25 |
| ✓ | R10 Table 1 → appendix | 0.3 |
| ✓ | R11 Fig 1 shrink | 0.1 |
| ✓ | R12 Abstract/intro tighten | 0.2 |
| — | R9 Fig 5 stays in body | — |
| **Total** | | **6.15** |
| **Margin** | | **−0.15** |

Within typesetting margin (float placement, paragraph breaks). If tight, apply R9 as reserve (+0.4p → total 6.55p, comfortable margin).

**Characteristics**: Protocol and proof sketch move to appendix. Fig 5 stays in body as the main experimental result. All formal definitions compressed to citation pointers.

#### Plan 2B: "Protocol in body, experiments compressed"

| Applied | Source | Save |
|---------|--------|------|
| ✓ | R1 Sec 3 compress | 1.0 |
| ✓ | R2 Sec 4/5.1 merge | 0.5 |
| ✓ | R3 Sec 6.3 → appendix | 1.5 |
| ✓ | R4 Table 2 → appendix | 0.8 |
| — | R5 Fig 3 stays in body | — |
| ✓ | R6 Sec 7.3 merge | 0.5 |
| ✓ | R7 Out-of-scope → appendix | 0.3 |
| ✓ | R8 Sec 2 compress | 0.25 |
| ✓ | R9 Fig 5 → appendix | 0.4 |
| ✓ | R10 Table 1 → appendix | 0.3 |
| ✓ | R11 Fig 1 shrink | 0.1 |
| ✓ | R12 Abstract/intro tighten | 0.2 |
| **Total** | | **5.85** |
| **Margin** | | **−0.45** |

Achievable if Sec 3 compression yields ~1.2p (likely given current 2.5p with substantial formal definitions). Alternatively, push R6 harder (~0.7p from aggressive subsubsection merge).

**Characteristics**: Protocol (Fig 3) stays in body (valuable for FC cryptography reviewers). Fig 5 moves to appendix. Trade-off: protocol visibility vs. experimental figure visibility.

### 4-2. 3-INST compositions (target: 7.1 p)

#### Plan 3A: "Maximum appendix offload"

| Applied | Source | Save |
|---------|--------|------|
| ✓ | R1 Sec 3 compress | 1.0 |
| ✓ | R2 Sec 4/5.1 merge | 0.5 |
| ✓ | R3 Sec 6.3 → appendix | 1.5 |
| ✓ | R4 Table 2 → appendix (3-INST) | 1.2 |
| ✓ | R5 Fig 3 → appendix | 0.7 |
| ✓ | R6 Sec 7.3 merge | 0.5 |
| ✓ | R7 Out-of-scope → appendix | 0.3 |
| ✓ | R8 Sec 2 compress | 0.25 |
| ✓ | R9 Fig 5 → appendix | 0.4 |
| ✓ | R10 Table 1 → appendix | 0.3 |
| ✓ | R11 Fig 1 shrink | 0.1 |
| ✓ | R12 Abstract/intro tighten | 0.2 |
| **Total** | | **6.95** |
| **Margin** | | **−0.15** |

Within typesetting margin. Every recovery source applied.

**Characteristics**: Extremely lean body. All tables, protocol figure, proof sketch, and experimental figure move to appendix. Body retains only the generalized relation figure, comparison table, and textual summaries. Risk: FC reviewers may find the body insufficiently detailed.

#### Plan 3B: "Aggressive compression, selective appendix"

| Applied | Source | Save |
|---------|--------|------|
| ✓ | R1 Sec 3 compress (aggressive: 1.3p) | 1.3 |
| ✓ | R2 Sec 4/5.1 merge | 0.5 |
| ✓ | R3 Sec 6.3 → appendix | 1.5 |
| ✓ | R4 Table 2 → appendix (3-INST) | 1.2 |
| ✓ | R5 Fig 3 → appendix | 0.7 |
| ✓ | R6 Sec 7.3 merge | 0.5 |
| ✓ | R7 Out-of-scope → appendix | 0.3 |
| ✓ | R8 Sec 2 compress | 0.25 |
| — | R9 Fig 5 stays in body | — |
| — | R10 Table 1 stays in body | — |
| ✓ | R12 Abstract/intro tighten | 0.2 |
| **Total** | | **6.45** |
| **Margin** | | **−0.65** |

Shortfall 0.65p. Close by: R11 (+0.1p) + pushing R1 to 1.5p (all formal defs to appendix) → total ~7.05p, margin −0.05p.

**Characteristics**: More aggressive Sec 3 compression (all formal definitions moved to appendix). Fig 5 and Table 1 stay in body. Tighter margin.

### 4-3. Body page budget sketch (Plan 2A, 2-INST)

| Section | Current | Additions | Recoveries | Target |
|---------|---------|-----------|------------|--------|
| Title + Abstract | 0.8 | — | −0.2 (R12) | 0.6 |
| Sec 1 Introduction | 1.6 | — | — | 1.6 |
| Sec 2 Related Work | 0.5 | +0.1 | −0.25 (R8) | 0.35 |
| Sec 3 Preliminaries | 2.5 | +0.4 | −1.0 (R1) | 1.9 |
| Sec 4+5 Protocol | 5.1 | +0.3 (table) −0.5 (Z) | −0.5 (R2) −0.7 (R5) | 3.7 |
| Sec 6 Security | 4.3 | +0.3 | −1.5 (R3) −0.3 (R7) | 2.8 |
| Sec 7 Experiments | 5.0 | +0.6 | −0.8 (R4) −0.5 (R6) −0.3 (R10) | 4.0 |
| **Total** | **19.8** | | | **14.95** |

Note: Rough allocation; final fit requires compilation. The 0.1p difference from measured 20.0p body is rounding.

### 4-4. Appendix growth estimate (Plan 2A, 2-INST)

| Appendix section | Current | Added |
|------------------|---------|-------|
| A: Newton-Schulz | 0.5 p | — |
| B: MLP+LN costs | 1.1 p | — |
| C: Formal security defs | 1.2 p | — |
| D: Sec 6.3 proof sketch (new) | — | +1.5 p |
| E: Table 2 full factorial (new) | — | +1.0 p |
| F: Fig 3 protocol (new) | — | +0.7 p |
| G: Out-of-scope attacks (new) | — | +0.3 p |
| H: Instance-specific relations, Option Z (new) | — | +1.3 p (Nystrom 0.8 + Linformer 0.5) |
| I: Table 1 model configs (new) | — | +0.3 p |
| **Total appendix** | **2.8 p** | **8.1 p** |

FC allows unlimited appendix (not counted toward 15p body limit), but reviewers are not obligated to read it. The body must be self-contained for the main claims.

---

## 5. Open Items and Dependencies

### 5-1. Decision items (blocking manuscript modification)

| ID | Item | Depends on | Blocks | Owner |
|----|------|-----------|--------|-------|
| D1 | Instance count: 2-INST or 3-INST | SOFT feasibility (O1) | All composition plans | User |
| D2 | Option X/Y/Z for relation placement | D1 | Sec 5 rewrite, Sec 6 soundness | User |
| D3 | Recovery combination (Plan A or B) | D1, D2 | All section edits | User |
| D4 | Fig 1 redesign (Option A/B/C) | D2 | Figure creation | User |
| D5 | Fig 3 disposition (body or appendix) | D3 | Protocol section rewrite | User |
| D6 | Cross-n binding treatment (3-5a/b/c) | D1 | Sec 6.1 rewrite | User |
| D7 | Figure 5 layout (same plot or subplot) | D1 | Figure creation, page tally | User |

### 5-2. Implementation items

| ID | Item | Status | Effort est. | Blocks | Deadline risk |
|----|------|--------|------------|--------|---------------|
| O1 | SOFT kernel implementation | Not started | 7-10 days | D1 (if 3-INST) | **HIGH** |
| O2 | Linformer benchmarks for Table 2 | Unknown | 2-3 days | Table 2 data | Medium |
| O3 | Linformer benchmarks for Figure 5 | Unknown | 1-2 days (same runs as O2) | Figure 5 data | Medium |
| O4 | SOFT benchmarks | Not started | 3-5 days | Table 2/Fig 5 (3-INST only) | HIGH (needs O1) |

### 5-3. Manuscript modification items

| ID | Item | Depends on | Effort est. |
|----|------|-----------|------------|
| M1 | Abstract + title rewrite (generalize) | D1 | 0.5 day |
| M2 | Sec 1 intro rewrite | D1 | 0.5 day |
| M3 | Sec 2 related work update | D1 | 0.5 day |
| M4 | Sec 3 compress + restructure | D1, D3 | 1 day |
| M5 | Sec 4/5 merge + protocol generalize | D2, D5 | 1-2 days |
| M6 | Generalized relation figure + comparison table | D2 | 1 day |
| M7 | Instance-specific relations (appendix) | D2 | 0.5 day |
| M8 | Sec 6 security rewrite | D1, D2, D6 | 1-2 days |
| M9 | Sec 7: add Linformer data | O2, O3 | 1 day |
| M10 | Sec 7: add SOFT data (if 3-INST) | O4 | 1 day |
| M11 | Fig 1 redraw | D4 | 0.5 day |
| M12 | Fig 2 redraw | D2 | 0.5 day |
| M13 | Fig 5 update | D7, O2 (O4 if 3-INST) | 0.5 day |
| M14 | Appendix expansion (moved content) | D3, M5-M8 | 1 day |
| M15 | Final compilation + page fit | All M* | 1 day |
| M16 | Proofreading + overfull fixes | M15 | 0.5 day |

### 5-4. Critical path analysis (Sept 17 deadline, 16 days from Sept 1)

#### 2-INST critical path

```
Day 0-1:   O2+O3 Linformer benchmarks (no decision dependency)
Day 1-2:   D1-D7 decisions (user)
Day 2-5:   M1-M4 (front matter, intro, preliminaries)
Day 5-8:   M5-M8 (protocol, relation, security)
Day 8-10:  M9 (experiments), M6-M7 (relation figures), M11-M13 (figures)
Day 10-12: M14 (appendix assembly)
Day 12-14: M15 compilation + page fitting
Day 14-16: M16 proofreading + buffer
```

**Feasibility**: Tight but feasible if decisions are made by Day 2 and Linformer benchmarks complete by Day 3. Buffer: 2 days.

#### 3-INST critical path

```
Day 0:     D1 = 3-INST decision
Day 0-10:  O1 SOFT implementation (parallel, bottleneck)
Day 0-3:   O2+O3 Linformer benchmarks (parallel)
Day 1-3:   D2-D7 decisions
Day 3-6:   M1-M4 (front matter, intro, preliminaries)
Day 6-9:   M5-M8 (protocol, relation, security)
Day 9-11:  M9 (Linformer experiments), M6-M7, M11-M13
Day 10-14: O4 SOFT benchmarks (needs O1 complete by Day 10)
Day 14-15: M10 SOFT experiments write-up
Day 15-16: M15-M16 compile + proofread
```

**Feasibility**: Very tight. SOFT implementation (O1, 7-10 days) is the bottleneck. If O1 finishes on Day 10, only 6 days remain for benchmarks + writing + compiling. **Zero buffer.**

### 5-5. Risk matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SOFT implementation not done by Day 10 | 3-INST impossible; fall back to 2-INST | HIGH | Set Day 8 go/no-go checkpoint |
| Linformer benchmarks show unexpected results | Re-analysis needed | LOW | Run benchmarks Day 0-1 |
| Page target missed after all recoveries | Submission blocked | MEDIUM | Reserve R9 (Fig 5 → appendix, +0.4p) |
| Security argument gaps during rewrite | Blocks Sec 6 | LOW | Validate Option Z self-containedness first (Step 3-7: confirmed) |
| Overfull hbox in new figures/tables | Cosmetic | MEDIUM | Fix existing Fig 3 overfull in M5; use resizebox |

### 5-6. Recommended action sequence

1. **Immediate (Day 0-1)**: Start Linformer benchmarks (O2+O3). No decision dependency.
2. **Day 1-2**: Decide D1-D7. Key: 2-INST vs 3-INST. **Recommendation**: commit to 2-INST as primary; start SOFT implementation in parallel if 3-INST desired, with Day 8 go/no-go.
3. **Day 2-5**: Begin manuscript M1-M4 (intro, related work, Sec 3 compression).
4. **Day 5-8**: Core technical M5-M8 (protocol, relation, security).
5. **Day 8**: SOFT go/no-go. If no-go, finalize 2-INST.
6. **Day 8-12**: Experiments, figures, appendix (M9-M14).
7. **Day 12-14**: Compilation + page fitting (M15).
8. **Day 14-16**: Proofreading + submission prep (M16 + buffer).

---

## Stopping point

Steps 1-5 are complete.

**Corrected recovery targets**:
- **2-INST: 6.3 pages** (20.0 current + 1.3 additions − 15.0 limit)
- **3-INST: 7.1 pages** (20.0 current + 2.1 additions − 15.0 limit)

All composition plans have tight margins (0.15-0.65p shortfall before typesetting adjustments). The 3-INST path carries high schedule risk due to unstarted SOFT implementation (7-10 day effort with 16 days to deadline). A Day 8 go/no-go checkpoint is recommended.

Seven decision items (D1-D7) block manuscript modification. The first and most consequential is D1 (2-INST vs 3-INST).

Awaiting decisions before beginning manuscript modifications.

---

## Part 0 Addendum: Re-tally with Missing Items

이전 집계에서 빠진 두 항목을 실측 기반으로 재산출한다.

### 0-1. Table 2 SOFT/Linformer rows

**현황**: Table 2 (FC/main.tex lines 519-558)는 kernel 2종 (BERT, Nystrom) x
verification 2종 (Naive, Freivalds) = 4 configurations x 4 sequence lengths = 16 data rows,
resizebox{\columnwidth}{!}로 축소, 0.7p (step0 실측).

**변경 결정**: 새 커널(Linformer, SOFT)의 Naive 행은 측정하지 않는다.
추가되는 행은 다음과 같다.

| 시나리오 | 추가 configuration | 추가 행 (config x 4 n-blocks) |
|---------|-------------------|------------------------------|
| 2-INST | Lin-Freivalds | 1 x 4 = 4 |
| 3-INST | Lin-Freivalds, SOFT-Freivalds | 2 x 4 = 8 |

**실측 방법**: LNCS llncs.cls 동일 tabular 구조(10 columns, \small, \tabcolsep=3pt,
\resizebox{\columnwidth}{!})로 16/20/24행 table을 별도 TeX 파일에서 컴파일하고
pdftotext -bbox로 marker 간격을 측정.

실측 환경:
- \textheight = 549.14pt (llncs.cls)
- \columnwidth = 347.12pt (llncs.cls, single column)

**실측 결과**:

| Table variant | Marker span (pt) | Occupancy (p) |
|--------------|------------------|---------------|
| 16 rows (baseline) | 313.6 | 0.571 |
| 20 rows (2-INST) | 358.0 | 0.652 |
| 24 rows (3-INST) | 401.3 | 0.731 |

| Metric | Value |
|--------|-------|
| Per-row height | 10.96pt = 0.020p |
| Delta +4 rows (2-INST) | 44.3pt = +0.08p |
| Delta +8 rows (3-INST) | 87.7pt = +0.16p |

테스트 table의 caption은 1행("16-row test.")이고 실제 Table 2의 caption은 5행이다.
Caption 길이는 행 추가와 무관하므로 delta만 적용한다.

**적용**: Table 2 baseline 0.70p에 delta를 합산한다.
- 2-INST: 0.70 + 0.08 = 0.78p (이전 추정 1.00p에서 0.22p 하향)
- 3-INST: 0.70 + 0.16 = 0.86p (이전 추정 1.40p에서 0.54p 하향)

이전 추정이 컸던 이유:
1. Naive 행을 포함했다 (행 수가 2배)
2. 행당 비용을 0.038p로 잡았다 (실측 0.020p의 1.9배)

### 0-2. Figure 5

**현황**: Figure 5 (FC/main.tex lines 585-648)는 attention-only (onlyeq) prove time을
BERT (red, 4 curves) vs Nystrom (blue, 4 curves)으로 표시. 0.4p (step0 실측).

**판정**: Linformer와 SOFT에는 onlyeq 회로가 없다. 이 측정은 BERT-Nystrom 전용이므로
새 커널을 추가할 근거가 없다. Figure 5는 기존 2종(BERT, Nystrom) 유지.

**추가분**: 0.

이전 집계에서 2-INST +0.1p, 3-INST +0.1p로 잡았던 항목을 0으로 정정한다.

### 0-3. 재집계

이전 항목을 유지하되 Table 2와 Figure 5 두 항목만 정정한다.

**2-INST (Nystrom + Linformer) 정정 집계:**

| Item | 이전 | 정정 | 변경 사유 |
|------|------|------|----------|
| Instance comparison table (Sec 5) | +0.3 | +0.3 | 변동 없음 |
| Sec 3.2 restructuring | +0.4 | +0.4 | 변동 없음 |
| Linformer rows in Table 2 | +0.3 | **+0.08** | Naive 제외, 실측 per-row 0.020p |
| Linformer curves in Figure 5 | +0.1 | **0** | onlyeq 회로 없음 |
| Linformer result discussion | +0.2 | +0.2 | 변동 없음 |
| Sec 6 modifications | +0.4 | +0.4 | 변동 없음 |
| Related Work | +0.1 | +0.1 | 변동 없음 |
| Generalized relation (Option Z) | -0.5 | -0.5 | 변동 없음 |
| **Total** | **+1.3** | **+0.98** | **-0.32** |

| Component | Pages |
|-----------|-------|
| Current body | 20.0 |
| 2-INST additions (corrected) | +0.98 |
| FC body limit | 15.0 |
| **Recovery needed (2-INST)** | **5.98p** |

**3-INST (Nystrom + Linformer + SOFT) 정정 집계:**

| Item | 이전 | 정정 | 변경 사유 |
|------|------|------|----------|
| Instance comparison table (Sec 5) | +0.3 | +0.3 | 변동 없음 |
| Sec 3.2 restructuring | +0.5 | +0.5 | 변동 없음 |
| Lin+SOFT rows in Table 2 | +0.7 | **+0.16** | Naive 제외, 실측 per-row 0.020p |
| Figure 5 expansion | +0.1 | **0** | onlyeq 회로 없음 |
| Lin+SOFT result discussion | +0.4 | +0.4 | 변동 없음 |
| Sec 6 modifications | +0.5 | +0.5 | 변동 없음 |
| Related Work | +0.1 | +0.1 | 변동 없음 |
| Generalized relation (Option Z) | -0.5 | -0.5 | 변동 없음 |
| **Total** | **+2.1** | **+1.46** | **-0.64** |

| Component | Pages |
|-----------|-------|
| Current body | 20.0 |
| 3-INST additions (corrected) | +1.46 |
| FC body limit | 15.0 |
| **Recovery needed (3-INST)** | **6.46p** |

**Transition cost (3-INST to 2-INST) 정정:**

| Item | 이전 | 정정 |
|------|------|------|
| SOFT Table 2 rows (4 rows) | -0.4 | -0.08 |
| SOFT discussion | -0.2 | -0.2 |
| SOFT Sec 6 | -0.1 | -0.1 |
| SOFT Sec 3 | -0.1 | -0.1 |
| **Total** | **-0.8** | **-0.48** |

검증: 3-INST addition - transition = 2-INST addition: 1.46 - 0.48 = 0.98. 일치.

**요약**: 이전 대비 recovery 목표가 2-INST는 6.3p에서 6.0p로, 3-INST는 7.1p에서 6.5p로
각각 0.3p, 0.6p 완화되었다. 주된 원인은 Naive 행 제외(행 수 절반)와 Figure 5 추가분
제거이다.

---

## Part 1: Implementation Findings

개발 과정에서 확정된 사실을 정리하고, 원고의 어느 절을 어떻게 바꾸어야 하는지 방향을 제시한다.

### 1-1. Commit classification principle

#### 확정 원칙 (실측 근거)

다음 세 규칙이 Linformer 구현과 SOFT 구현에서 실증되었다.

**규칙 1 (Freivalds-only output은 commit 필요).**
Freivalds projected identity에만 등장하고 element-wise in-circuit constraint가 없는
행렬의 출력은 challenge 도출 이전에 반드시 commit되어야 한다. Commit 없이 challenge를
관측한 adversary는 Freivalds 등식을 만족하는 다른 행렬을 적응적으로 선택할 수 있다
(k개 등식에 k*D개 미지수, underdetermined system).

근거: Linformer의 EK, FV (projection Freivalds만 통과, 후속 element-wise 제약 없음)는
aux commit이 필요했다. SOFT의 동종 행렬도 동일.

**규칙 2 (In-circuit equality로 유일 결정되면 commit 불요).**
Committed data에서 exact in-circuit equality (Euclidean division 유일성 또는 element-wise
R1CS)로 모든 원소가 결정되는 값은 commit이 불필요하다.

근거: Linformer의 pre-softmax logit Q_sim_logit은 committed triple
(table_idx, r_sm, R_matmul_logit)으로부터 enforce_softmax equality를 통해 복원된다.
16,384개 전 원소(S*k = 128*32)에서 복원치와 원본의 일치를 확인했다. Collision 0건.

**규칙 3 (Lookup index + remainder limb으로 원소별 복원되면 commit 불요).**
Lookup table의 index와 나머지 limb에서 element-wise로 복원 가능한 값은 규칙 2의
특수 사례이며 commit이 불필요하다.

근거: Softmax exponential 출력, segment averaging의 division quotient 등이 이에 해당.

**반례 (SOFT cross-term).**
SOFT의 cross-term은 정수 도메인에서 676/8192 원소가 불일치했다
(omega 판정 기준 위반). Element-wise 복원의 injectivity가 실패하는 경우이며,
이 값은 aux commit으로 이동해야 했다. 이 반례는 규칙 2의 injectivity 조건이
형식적으로 필요함을 보여 준다.

#### 현재 원고와의 관계

Section 6.3 (FC/main.tex line 445)의 soundness paragraph는 이미 세 범주 분류를 포함한다:

| Section 6.3 범주 | 대응 규칙 |
|-----------------|----------|
| (i) public values (X, Y') | 해당 없음 (commit 논의 대상 아님) |
| (ii) committed before challenge | 규칙 1의 결과물 |
| (iii) uniquely determined from committed data | 규칙 2, 3의 결과물 |

세 범주 분류는 이미 원고에 있으나 soundness proof 산문에 매몰되어 있다.
Framework-level principle로 승격하면 각 인스턴스의 commit 구조를 정당화할 때
soundness paragraph를 재인용하지 않아도 된다.

#### 수정 방향

**권고: Section 4 (Technical Overview)로 승격.**

Section 4에 3문장 분량의 named principle을 추가한다:

> **Principle (Commit Necessity).** A matrix M appearing in a Freivalds projected
> identity requires pre-challenge commitment if and only if no element-wise
> in-circuit constraint uniquely determines each entry of M from
> already-committed data. [+injectivity 조건 명시]

Section 6.3의 세 범주 문장은 이 principle을 이름으로 참조하도록 축약한다.
Instance comparison table (2단계 2-4)의 "Commit targets (aux)"와 "Omega set" 행이
이 principle의 인스턴스별 적용이 된다.

SOFT cross-term 반례를 Section 4 principle 아래 footnote로 추가하면 injectivity
조건의 필요성을 실증적으로 뒷받침할 수 있다.

**분량 영향**: +0.15p (principle 3문장 + footnote) - 0.05p (Sec 6.3 축약) = +0.1p net.
기존 Sec 6 modifications 항목(+0.4p)에 이미 포함되어 있다.

---

### 1-2. MP condition 2 omission

#### 사실

현재 원고의 서술과 구현의 차이:

| 항목 | 원고 | 구현 |
|------|------|------|
| Figure 4 lines 19-22 | 4 conditions 모두 강제 | Condition 1, 3, 4만 강제 |
| Section 5.3 line 330 | "four Moore-Penrose conditions" | 3 conditions |
| Section 6.3 lines 447-448 | "Lines 19-22 enforce the four" | 3 conditions |
| Condition 2 residual | 미언급 | 64-93% of range, 생략 |

SOFT도 동일하다. Condition 2 (X A X - X) 잔차가 범위의 64-93%에 달하는 것은
Newton-Schulz / Newton-Raphson 반복의 수렴 특성이며, full rank 입력에서도 발생한다.

#### 수학적 근거

{1,3,4}-generalized inverse의 해집합:
```
X = A^+ + N,  where N = (I - A^+A) Z (I - AA^+),  Z arbitrary
```

이 X는 conditions 1, 3, 4를 만족한다 (standard result, Ben-Israel & Greville).

- A가 full rank (A_tilde가 m x m 가역행렬)이면:
  A^+A = I, AA^+ = I이므로 N = 0. {1,3,4}-inverse는 A^+ 유일.
- A가 rank deficient이면:
  N != 0인 해가 존재. Adversary가 Z를 자유롭게 선택하여
  원하는 pseudoinverse를 공급할 수 있다.

#### Theorem 1 가정 (v)와의 관계

Theorem 1의 가정 (v)는 sigma_min(A_tilde) >= sigma_0 > 0을 요구한다.
이는 A_tilde가 가역임을 뜻하며, {1,3,4}-inverse의 유일성을 보장한다.

따라서 가정 (v) 하에서 condition 2 생략은 soundness에 영향을 주지 않는다.
가정 (v)가 유일성의 전제 역할을 하는 구조로 Theorem 1을 재서술할 수 있다:

> (v) well-conditionedness: sigma_min(A_tilde) >= sigma_0 > 0, which ensures
> that the {1,3,4}-generalized inverse enforced by the circuit is the unique
> Moore-Penrose pseudoinverse.

#### 수정 방향

**Figure 4**: Line 20 (condition 2)을 삭제하거나, 삭제 후 행 번호를 재배정한다.
현재 4 lines(19-22)이 3 lines(19-21)로 줄면 relation이 25 lines가 되고
Figure 4 occupancy가 ~0.05p 감소한다.

**Section 5.3** (FC/main.tex line 330): "four Moore-Penrose conditions
(lines 19-22)" -> "three Moore-Penrose conditions (conditions 1, 3, 4;
lines 19-21)". 부연 1문장: "Condition 2 (X A X = X) is omitted because its
empirical residual exceeds 60% of the quantization range under both
Newton-Schulz and Newton-Raphson iterations. Under assumption (v), the
{1,3,4}-inverse is unique and equals A^+."

**Section 6.3** (FC/main.tex lines 447-448): "Lines 19-22 enforce the four
Moore-Penrose conditions" -> "Lines 19-21 enforce conditions 1, 3, 4".
이하 perturbation bound 서술은 변경 없음 (epsilon 정의와 sigma_min 가정이
그대로 적용됨).

**Theorem 1 가정 (v)**: 현재 "well-conditionedness of the landmark softmax matrix,
i.e., sigma_min >= sigma_0 > 0"에 다음을 추가:
"which guarantees uniqueness of the {1,3,4}-generalized inverse enforced
by the circuit (cf. Ben-Israel & Greville, Theorem 2.1)."

**분량 영향**: Figure 4에서 -0.05p (1 line 삭제), Section 5.3에서 +0.05p (부연 1문장).
Net 0.

---

### 1-3. Epsilon values mismatch

#### 사실

| Condition | 원고 (Sec 7.1) | 코드 (Nystrom) | 코드 (SOFT) |
|-----------|---------------|---------------|-------------|
| 1: AXA = A | 4 | 4096 | 8037 |
| 3: (AX)^T = AX | 64 | 512 | 99 |
| 4: (XA)^T = XA | 512 | 32 | 144 |

원고 Section 7.1 (FC/main.tex line 480):
"the circuit enforces bounds of epsilon in {4, 64, 512}, providing a 3x to 5x
safety margin above the empirical maximum errors"

세 가지 불일치:
1. **값 불일치**: 원고와 코드의 epsilon 값이 전혀 다르다.
2. **Condition 1 vacuous**: Nystrom의 epsilon_1 = 4096은 12-bit 양자화 범위
   [0, 4095] 전체를 허용하므로 제약으로 기능하지 않는다.
   SOFT의 epsilon_1 = 8037 > 4095도 마찬가지다.
3. **인스턴스별 차이**: Nystrom과 SOFT의 epsilon 값이 다르다.
   Linformer에는 MP condition 자체가 없어 epsilon이 존재하지 않는다.

Condition 1이 vacuous이므로, 실질적으로 enforced되는 조건은 3과 4 두 개뿐이다.
이는 1-2절의 condition 2 생략과 합치면, 유효하게 작동하는 MP condition은
{3, 4}이고 epsilon 값은 각각 512, 32 (Nystrom) 또는 99, 144 (SOFT)이다.

#### 수정 방향

**Section 7.1** (FC/main.tex lines 477-480): 코드의 실제 값으로 정정한다.
Condition별 epsilon을 표로 제시하는 것이 명확하다:

```
| Condition | Nystrom epsilon | Nystrom empirical max | Margin |
|-----------|----------------|----------------------|--------|
| 1 (AXA=A) | 4096 (vacuous) | [measured] | -- |
| 3 ((AX)^T=AX) | 512 | [measured] | [x]x |
| 4 ((XA)^T=XA) | 32 | [measured] | [x]x |
```

Condition 1 vacuous 사실은 Section 5.3의 부연 또는 Section 7.1의 footnote로
설명한다: "The bound for condition 1 is set to the full quantization range and
does not actively constrain the witness; the soundness guarantee rests on
conditions 3 and 4 together with assumption (v)."

커널마다 epsilon 산출 규칙이 다르다는 사실은 인스턴스 comparison table에
"epsilon profile" 행을 추가하여 정리할 수 있다.
Linformer의 해당 행은 "N/A (no pseudoinverse)"로 표기한다.

**분량 영향**: 산문 1줄 삭제 + 표 1개 (~3 rows) 추가. 표를 Section 7.1 인라인으로
넣으면 +0.1p 내외. 기존 Sec 6 modifications 항목의 잔여 마진에 포함 가능.

---

### 1-4. Theorem 1 assumption (v) -- padding에 의한 rank deficiency

#### 사실

Segment averaging에서 연속 padding 토큰이 구간 길이 n/m을 초과하면
해당 landmark가 0벡터가 된다. 0벡터 landmark가 여러 개 생기면
A_tilde에 중복 행(모두 0)이 만들어져 rank가 떨어진다.

실측 (SAMPLE_TEXTS[0], 9 토큰 입력):

| n | Rank of A_tilde (m=32) | sigma_min |
|---|----------------------|-----------|
| 128 | 4 | 0 |
| 512 | 2 | 0 |
| 1024 | 2 | 0 |

모든 n에서 sigma_min = 0이므로 가정 (v)가 위반된다.

이 현상은 Nystrom과 SOFT에 공통이다 (둘 다 segment averaging 기반 landmark 생성).
Linformer에는 landmark가 없으므로 해당 없다.

#### 현재 원고의 취급

Section 6.2 (FC/main.tex lines 459-463):
"A model or input for which the landmark matrix violates the well-conditionedness
assumption falls into the same category [as backdoored models]: the commitment
still binds the provider to that model, and attesting to its conditioning requires
the same kind of auxiliary attestation."

이 서술은 가정 (v) 위반을 backdoor나 저품질 모델과 같은 예외적 상황으로 분류한다.
그러나 padding은 일상적이다. 대부분의 입력이 최대 시퀀스 길이보다 짧으므로
padding이 들어가고, 구간 길이를 초과하는 연속 padding은 흔하다.

#### 가정 (v) 위반 시 보안 영향

1-2절에서 확인한 것처럼, 구현은 conditions {1(vacuous), 3, 4}만 enforced한다.
Condition 1이 vacuous이므로 실질적으로 {3,4}-inverse이다.

A_tilde가 rank deficient이면:
- {1,3,4}-inverse 해: X = A^+ + (I - A^+A)Z(I - AA^+), Z 임의
- {3,4}-inverse 해: 이보다 더 넓은 family (condition 1 제약도 무효이므로)
- Adversary가 Z를 선택하여 Y' = F_tilde (A^+ + N) B_tilde V를 조작할 수 있다
- 출력 편차: ||F_tilde N B_tilde V|| 만큼 자유도가 존재

이 자유도의 실제 크기는 A_tilde의 null space 차원에 의존한다.
Rank 2 (m=32) 상황에서 null space 차원은 30이므로 상당한 자유도가 있다.

#### 수정 방향

**Section 6.2**: "falls into the same category" 서술을 개정한다.
Padding에 의한 rank deficiency는 예외가 아니라 일상적 사례임을 인정하고,
이 경우의 보안 보장 범위를 명시한다.

두 가지 서술 방향이 가능하다:

**(A) 한정 조건 명시**: 가정 (v)가 성립하는 조건(충분히 긴 입력, 또는 padding
비율이 1 - m/n 미만)을 구체적으로 서술하고, 이 범위 밖에서는 soundness
보장이 약해진다고 적는다.

**(B) Padding-aware mitigation 제안**: Padding 구간을 제외하고 landmark를
구성하는 변형을 future work으로 제시한다. 또는 zero-landmark row를 제거한 후
A_tilde를 구성하는 방식을 서술한다. 구현 변경이 필요하므로 본 논문의 범위
밖이다.

**Theorem 1**: 가정 (v) 앞에 "For inputs where" 한정어를 추가하거나,
"When assumption (v) is violated, the soundness guarantee of the pseudoinverse
factor degrades: the adversary gains dim(null(A_tilde))^2 degrees of freedom
in the pseudoinverse witness" 부연을 추가한다.

**Nystrom과 SOFT 공통 사안**: 이 문제는 segment averaging을 사용하는 모든
인스턴스에 해당한다. Linformer는 해당 없음. Instance comparison table의
"Assumption (v) required" 행에 "Yes (padding-sensitive)" / "No"를 표기한다.

**분량 영향**: Section 6.2에 1-2문장 추가 (~+0.05p). Theorem 1에 한정어 추가 (~0).

---

### 1-5. Lookup value binding gap

#### 사실

현재 구현에서 Lasso는 comm_derefs에 조회된 함수값(softmax output 등)을 커밋한다.
CP-Link proof는 인덱스 커밋만 묶고, 함수값 커밋은 묶지 않는다.
따라서 Lasso가 커밋한 함수값과 R1CS의 비선형 출력 변수 사이에 바인딩이 없다.

이 gap은 BERT, Nystrom, Linformer, SOFT 전부에 해당한다.

#### 현재 원고의 주장

**Section 6.3** (FC/main.tex line 444):
"the lookup argument guarantees that the non-linear operands
(F_tilde, A_tilde, B_tilde) are correct evaluations of the quantized softmax"

**Section 5.1** (FC/main.tex lines 260, 264):
link proof가 cm_lk와 lookup operand commitment이 "the same lk
(= (F_tilde, A_tilde, B_tilde))"를 열도록 보장한다고 주장한다.

**구현**: CP-Link는 index commitment만 바인딩. function value commitment는
Lasso 내부에서 comm_derefs로 커밋되지만, 이 커밋이 R1CS의 cm_aux에 연결되지 않는다.
Adversary가 correct lookup index를 사용하면서 다른 function value를 R1CS에
공급할 수 있는 여지가 있다.

#### 수정 비용

Link 추가 시:
- Proof size: +1.1KB (CP-Link proof 1개 추가)
- Verifier: +3 pairings (link verification)
- R1CS constraints: +0 (link는 R1CS 외부)

#### 서술 방향: Section 7.1의 ZK 서술 패턴 차용

Section 7.1 (FC/main.tex lines 473-474)은 Lasso zero-knowledge에 대해 다음과 같이 쓴다:

> "Theorem 1 requires the lookup argument to be zero-knowledge; Lasso admits
> standard zero-knowledge instantiations by blinding the committed operands,
> and our security analysis assumes such an instantiation. Our benchmarks use
> the non-hiding variant, whose costs are identical up to the blinding overhead."

이 패턴을 lookup value binding에도 적용할 수 있다:

> "The security analysis assumes that the lookup function-value commitment is
> linked to the circuit's auxiliary commitment via an additional CP-Link proof,
> ensuring that the non-linear operands in the R1CS witness are consistent
> with the Lasso-verified lookup evaluations. Our implementation does not yet
> include this link; adding it requires one additional CP-Link proof
> (+1.1 KB proof size, +3 verifier pairings) with no change to the R1CS
> constraint count."

이 서술이 적합한지에 대한 판단:

**공통점**: 두 경우 모두 security analysis는 완전한 instantiation을 가정하고,
벤치마크는 비용이 동일하거나 소폭 증가하는 변형을 사용한다.

**차이점**: ZK의 경우 non-hiding variant의 비용이 hiding variant와 "identical up to
blinding overhead"이므로 벤치마크 수치가 그대로 유효하다. Lookup binding의 경우
+1.1KB와 +3 pairings는 정량적으로 명시할 수 있고, 현재 벤치마크 수치에 더해야 한다.
Proof size 증가분 1.1KB는 현재 proof size 603-1,625KB 대비 0.07-0.18%이므로
벤치마크 결론에 실질적 영향이 없다.

#### 수정 위치

**Section 5.1** (FC/main.tex line 260 부근): link proof 서술에 function-value link를
포함하도록 확장한다. "and that cm_lk and the lookup argument's operand and
function-value commitments open to the same lk" 또는 유사 표현.

**Section 6.3** (FC/main.tex line 444): "the lookup argument guarantees" 문장 뒤에
footnote를 추가하여 구현 상태와 추가 비용을 명시한다.

또는 **Section 7.1**에 ZK 서술 바로 다음에 동일 패턴으로 배치한다.

**분량 영향**: footnote 2-3행 또는 paragraph 2-3행. +0.05p 이내.

---

### Part 1 Summary: Affected Sections

| Finding | 영향 Section | 수정 유형 |
|---------|------------|----------|
| 1-1 Commit principle | Sec 4 (신규 principle), Sec 6.3 (축약) | 추가 + 개정 |
| 1-2 MP cond 2 omit | Fig 4 (1 line 삭제), Sec 5.3 (개정), Sec 6.3 (개정), Thm 1 (보강) | 삭제 + 개정 |
| 1-3 Epsilon mismatch | Sec 7.1 (값 정정 + 표 추가) | 정정 |
| 1-4 Assumption (v) | Sec 6.2 (개정), Thm 1 (한정어 추가) | 개정 |
| 1-5 Lookup binding | Sec 5.1 or 7.1 (footnote/paragraph 추가), Sec 6.3 (footnote) | 추가 |

**총 분량 영향**: Items 1-1 through 1-5의 net은 ~+0.15p.
기존 Sec 6 modifications 항목(+0.4p)은 1-1, 1-2, 1-4를 포괄한다.
1-3 (+0.1p)과 1-5 (+0.05p)는 Sec 7 항목에 흡수 가능하므로
전체 addition tally에 대한 영향은 미미하다 (기존 +0.98p / +1.46p 유지).

**항목 간 연결**:
- 1-2와 1-3은 연결된다: condition 1의 epsilon이 vacuous이므로
  실질적으로 enforced되는 MP condition은 {3, 4}뿐이다.
- 1-2와 1-4는 연결된다: assumption (v) 위반 시 {1,3,4}-inverse(또는 {3,4}-inverse)가
  유일하지 않아 adversary에게 자유도가 생긴다.
- 1-1과 1-5는 연결된다: 규칙 1의 commit 필요성이 lookup function value에도 적용되며,
  현재 이 link가 빠져 있다.

---

# Part A: Moore-Penrose Condition Effectiveness (Empirical)

## A-1. Zero Witness Test

### Test design

Set Q_inv_k2 (A+) to all z_inv (zero-point), representing A+ = 0 in real domain.
Recompute all downstream values using the ZEN quantized matmul formula:

```
numerator = M * (G1 + n*z_w*z_x + M' - z_x*rowsum(W) - z_w*colsum(X))
Q_y = numerator >> k_bits
R   = numerator % (1 << k_bits)
```

Verify all Freivalds constraints and range checks pass.

Test script: `Dietformer/models/Nystromformer/code/dietformer/zero_witness_test.py`

### Results

**Layer 0** (transformer_0.mha.attn):

| Step | Label | Q_y range | R range | Freivalds | Range |
|------|-------|-----------|---------|-----------|-------|
| MP 1-1 | A * A+_fake = Y1 | [0, 0] | [0, 0] | PASS | PASS |
| MP 1-2 | Y1 * A = Y2 | [0, 0] | [0, 0] | PASS | PASS |
| MP 2-1 | A+_fake * A = Y3 | [126, 126] | [0, 0] | PASS | PASS |
| MP 2-2 | Y3 * A+_fake = Y4 | [125, 125] | [4156372, 4156372] | PASS | PASS |
| temp | P_k3 * V | (unchanged) | (unchanged) | PASS | PASS |
| mid | P_k1 * A+_fake | [76, 76] | [4192996, 4192996] | PASS | PASS |
| X | mid_fake * temp | [133, 139] | [46440, 4089960] | PASS | PASS |

- Y2 == A? **No** (Y2 = 0, A = 1024)
- Y4 == A+? **No** (Y4 = 125, A+ range [0, 254])
- Attention output X changed? **Yes** (honest: [60, 199], fake: [133, 139])
- All constraints satisfied? **Yes**

**Layer 1** (transformer_1.mha.attn):

| Step | Label | Q_y range | R range | Freivalds | Range |
|------|-------|-----------|---------|-----------|-------|
| MP 1-1 | A * A+_fake = Y1 | [0, 0] | [0, 0] | PASS | PASS |
| MP 1-2 | Y1 * A = Y2 | [0, 0] | [0, 0] | PASS | PASS |
| MP 2-1 | A+_fake * A = Y3 | [119, 119] | [0, 0] | PASS | PASS |
| MP 2-2 | Y3 * A+_fake = Y4 | [118, 118] | [4147628, 4147628] | PASS | PASS |
| temp | P_k3 * V | (unchanged) | (unchanged) | PASS | PASS |
| mid | P_k1 * A+_fake | [78, 78] | [4193532, 4193532] | PASS | PASS |
| X | mid_fake * temp | [125, 132] | [262272, 4188416] | PASS | PASS |

- Attention output changed? **Yes** (honest: [51, 200], fake: [125, 132])
- All constraints satisfied? **Yes**

### Conclusion

**The fake witness satisfies ALL circuit constraints on both layers.**
A malicious prover can substitute A+ = 0 (null pseudoinverse) and produce a valid
SNARK proof with an incorrect attention output.

The attack works because:
1. Q_inv (A+) is an uncommitted witness with no range check
2. Y1, Y2, Y3, Y4 are uncommitted witnesses with no range check
3. Freivalds checks verify multiplication correctness but NOT the equality conditions
4. The circuit has no constraint binding Y2 to A or Y4 to A+
5. M_inv and M_prime_inv are witness-controlled constants (FpVar::Constant from NPZ)

---

## A-2. Per-Condition Effective Range

### Variable classification in the circuit

| Variable | Witness mode | Range check | Commitment | Freivalds role |
|----------|-------------|-------------|------------|----------------|
| r_var (challenge) | **Public input** | N/A | N/A | Derives r_pows |
| Q_q, Q_k, Q_v | Witness | None | d2 (Pedersen, no CP-link) | RHS input |
| Q_inv (A+) | Witness | **None** | **None** | RHS input |
| Y1, Y2, Y3, Y4 | Witness | **None** | **None** | LHS (compressed) |
| R_inv low/high | Witness | **Lasso (11-bit)** | d1 (CP-linked) | LHS via decomposition |
| M_inv, M'_inv | Constant from witness | N/A | N/A | Scaling factor |

### Degrees of freedom per head (L = 64)

| Category | Count |
|----------|-------|
| A+ elements | 4096 |
| Y1, Y2, Y3, Y4 elements | 4 x 4096 = 16384 |
| R_inv elements | 4 x 4096 = 16384 |
| M, M' constants | 8 |
| **Total free parameters** | **36872** |
| Freivalds row constraints | 4 x 64 = 256 |
| R decomposition constraints | 4 x 4096 = 16384 |
| **Total constraints** | **16640** |
| **Net degrees of freedom** | **20232** |

The adversary has 20,232 degrees of freedom per head for MP-related variables.
The effective range of A+ is: any value in [0, p-1] (entire BN254 scalar field).

### Per-condition analysis

**Condition 1 (A * A+ * A = A)**:
- Step 1-1: Freivalds verifies A * A+ = Y1 (multiplication correctness only)
- Step 1-2: Freivalds verifies Y1 * A = Y2 (multiplication correctness only)
- **Missing constraint**: Y2 == A is never checked
- Adversary can choose any A+; Y1 and Y2 follow deterministically, and the circuit accepts

**Condition 2 (A+ * A * A+ = A+)**:
- Step 2-1: Freivalds verifies A+ * A = Y3 (multiplication correctness only)
- Step 2-2: Freivalds verifies Y3 * A+ = Y4 (multiplication correctness only)
- **Missing constraint**: Y4 == A+ is never checked
- Same freedom as condition 1

**Conditions 3 and 4 (symmetry)**: Not implemented in the circuit.

### Honest deviation measurement

Even in the honest case, quantization rounding causes significant deviation:

| Condition | Layer | max |Y - target| | mean |Y - target| |
|-----------|-------|-------------------|---------------------|
| Cond 1 (Y2 vs A) | 0 | 442 | 439.5 |
| Cond 1 (Y2 vs A) | 1 | 402 | 401.5 |
| Cond 2 (Y4 vs A+) | 0 | 129 | 23.9 |
| Cond 2 (Y4 vs A+) | 1 | 137 | 31.8 |

Condition 1 produces deviations of 40-43% of A's magnitude (A = 1024).
Even the honest prover violates MP condition 1 by a large margin.

---

## A-3. Epsilon Adjustment Scenarios

### Scenario 1: Exact equality check (epsilon = 0)

Add constraints: Y2_ij == A_ij and Y4_ij == A+_ij for all i, j.

- **Honest prover**: FAILS (max deviation 442 for cond 1, 137 for cond 2)
- **Verdict**: Not viable without fundamental architectural change to the quantization

### Scenario 2: Epsilon = honest max + 20% margin

- epsilon_1 = 530 (for condition 1, covering honest max 442)
- epsilon_2 = 164 (for condition 2, covering honest max 137)
- **Honest prover**: Passes with 20% safety margin
- **Adversary freedom**: each Y2_ij can deviate from A_ij by up to 530
  - Per-element freedom: 1061 possible values (vs A = 1024 fixed)
  - 51.8% of A's range is exploitable
- **Verdict**: Provides marginal constraint; adversary retains significant freedom

### Scenario 3: Drop MP conditions entirely

- **Circuit cost saved**:
  - R1CS constraints: 16,640 (4 Freivalds x 64 rows + 4 x 4096 decompositions)
  - Lasso entries: 32,768 (4 x 4096 x 2 low/high halves)
- **Security lost**: None (MP conditions provide zero effective constraint as shown by A-1)
- **Paper impact**: Section 5.3 simplifies; Figure 4 relation loses lines 6-22; Section 6.3 theorem
  drops conditions 1-2; 0.4-0.6p recovery from Fig 4 reduction
- **Verdict**: Net positive (save cost, lose no security, simplify paper)

### Cost comparison

| Option | Additional R1CS | Additional Lasso | Security gain |
|--------|----------------|------------------|---------------|
| A: Add epsilon-bounded check | +32,768 | +16,384 | Marginal (epsilon >> 0) |
| B: Drop MP entirely | -16,640 | -32,768 | None lost |
| C: Commit output only | 0 | 0 | Binds output, not A+ |

### Recommendation (not a decision)

Three options in order of recommendation:

1. **Drop MP conditions**: Save circuit cost, simplify paper, lose no security.
   Rewrite Section 5.3 and Figure 4 to remove MP steps. Theorem 1 assumptions
   simplify. Recovery: 0.4-0.6p from Figure 4 alone.

2. **Drop MP conditions + commit attention output**: Same as (1) but additionally
   commit Q_sim_x to d2. This doesn't verify A+ correctness but binds the
   prover's claimed output, preventing the adversary from changing the
   attention output without detection.

3. **Keep MP with epsilon (not recommended)**: If MP conditions must remain for
   narrative reasons, use epsilon_1 >= 530, epsilon_2 >= 164. Document the
   large epsilon as a known limitation. Costs 32,768 additional R1CS constraints
   and 16,384 Lasso entries for marginal security.
