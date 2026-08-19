#!/usr/bin/env python3
"""Fill English section of SHT Humantech abstract template with zkDietFormer content."""

from docx import Document
from docx.shared import Pt, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

INPUT = "/Users/minhae/Projects/overleaf/zkDietformer/SHT/2_33rd_abstract_sample.docx"
OUTPUT = INPUT  # overwrite

doc = Document(INPUT)
ENG_START = 48  # First English-section paragraph

# ── helpers ──────────────────────────────────────────────────────────
def clear_para(p):
    el = p._element
    for ch in list(el):
        if ch.tag != qn('w:pPr'):
            el.remove(ch)

def add_run(p, text, bold=None, italic=None, size=None):
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    if bold is not None:  r.font.bold = bold
    if italic is not None: r.font.italic = italic
    if size is not None:  r.font.size = size
    return r

def set_title(p, text):
    clear_para(p)
    add_run(p, text, bold=True, size=Pt(20))
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

def set_abstract(p, text):
    clear_para(p)
    add_run(p, text, bold=True, size=Pt(10))
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

def set_heading(p, text):
    clear_para(p)
    add_run(p, text, bold=True, size=Pt(11))
    p.paragraph_format.space_before = Emu(38100)

def set_body(p, text):
    clear_para(p)
    add_run(p, text, size=Pt(10))
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Emu(38100)

def set_body_with_header(p, header, text):
    clear_para(p)
    add_run(p, header, bold=True, italic=True, size=Pt(10))
    add_run(p, text, size=Pt(10))
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Emu(38100)

def set_ref(p, text):
    clear_para(p)
    add_run(p, text, size=Pt(9))
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Emu(38100)

def set_empty(p):
    clear_para(p)

def hide_para(p):
    """Make paragraph invisible (empty, 1pt font)."""
    clear_para(p)
    add_run(p, "", size=Pt(1))
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)

# ── content ──────────────────────────────────────────────────────────
P = [doc.paragraphs[ENG_START + i] for i in range(len(doc.paragraphs) - ENG_START)]
idx = 0

# Title
set_title(P[idx], "zkDietFormer: Verifiable Transformer Inference "
    "with Linear-Cost Attention Proofs via Low-Rank Approximation"); idx += 1

# 2 empty (author placeholder area)
set_empty(P[idx]); idx += 1
set_empty(P[idx]); idx += 1

# Abstract
set_abstract(P[idx],
    "(Abstract) The deployment of Transformer models via Model-as-a-Service "
    "(MaaS) platforms raises a trust problem: users cannot verify that the "
    "provider faithfully executed the claimed model. Zero-knowledge SNARKs "
    "can prove correct inference without revealing model weights, yet existing "
    "approaches face an O(n\u00b2) proving-cost bottleneck from the n \u00d7 n "
    "self-attention matrix. We propose zkDietFormer, the first zero-knowledge "
    "verification framework for low-rank self-attention. By instantiating the "
    "Nystr\u00f6m approximation inside the proving circuit, we replace the full "
    "attention computation with three smaller matrix products involving "
    "m \u226a n landmark tokens, reducing the dominant cost to O(n). "
    "Freivalds\u2019 randomized checks verify all matrix products, and a "
    "commit-carrying SNARK binds every proof to a single committed model. "
    "Experiments on five BERT-scale configurations show up to 4\u00d7 extension "
    "in maximum provable sequence length under 128 GB memory, with per-layer "
    "prove time growing near-linearly in n."
); idx += 1

# 2 empty before intro
set_empty(P[idx]); idx += 1
set_empty(P[idx]); idx += 1

# ── 1. INTRODUCTION ─────────────────────────────────────────────────
set_heading(P[idx], "1. INTRODUCTION"); idx += 1
set_empty(P[idx]); idx += 1

set_body(P[idx],
    "Modern large language models are deployed via remote inference APIs "
    "where users cannot inspect the computation. Zero-knowledge proofs "
    "(ZKPs) offer a principled solution: the provider proves correct "
    "inference without revealing model weights. However, self-attention"
    "\u2014the core Transformer operation\u2014forms an n \u00d7 n attention "
    "matrix with row-wise softmax, creating an O(n\u00b2) bottleneck in "
    "both computation and proof generation. As context windows grow from "
    "512 tokens to millions in frontier models, quadratic verification "
    "cost becomes prohibitive."
); idx += 1

set_body(P[idx],
    "Probabilistic techniques such as Freivalds\u2019 algorithm [1] and "
    "sumcheck protocols [7] reduce matrix-multiplication verification "
    "cost but leave the O(n\u00b2) term intact. Meanwhile, attention "
    "matrices often exhibit approximate low-rank structure, and "
    "Nystr\u00f6mformer [2] exploits this to achieve O(n) inference cost "
    "with accuracy comparable to standard self-attention."
); idx += 1

set_body(P[idx],
    "We present zkDietFormer, which combines: (1) Nystr\u00f6m low-rank "
    "decomposition, reducing the attention circuit from O(n\u00b2) to O(n); "
    "(2) Freivalds\u2019 randomized checks, verifying matrix products via "
    "vector inner products; and (3) a commit-carrying SNARK (CC-SNARK) [3], "
    "binding each proof to committed model weights outside the circuit."
); idx += 1

# ── 2. METHOD ────────────────────────────────────────────────────────
set_empty(P[idx]); idx += 1
set_heading(P[idx], "2. METHOD"); idx += 1
set_empty(P[idx]); idx += 1

set_body_with_header(P[idx],
    "Nystr\u00f6m Low-Rank Attention. ",
    "Standard self-attention requires forming an n \u00d7 n attention matrix "
    "via softmax of the query-key product, then multiplying by values V. "
    "Nystr\u00f6mformer [2] avoids this by partitioning the sequence into m "
    "segments, computing m landmark queries and keys by segment averaging. "
    "This yields three low-rank factors of sizes n\u00d7m, m\u00d7m, and "
    "m\u00d7n, with the m\u00d7m factor\u2019s pseudoinverse replacing the "
    "full n \u00d7 n inversion. Since all products involve at most "
    "n \u00d7 m entries, the total cost is O(n) for fixed m."
); idx += 1

set_body_with_header(P[idx],
    "Freivalds\u2019 Verification. ",
    "To verify a claimed matrix product AB = C without recomputing it in "
    "O(n\u00b3), Freivalds\u2019 algorithm [1] checks ABr = Cr for a random "
    "vector r, reducing verification from O(n\u00b3) to O(n\u00b2) for "
    "n \u00d7 n matrices\u2014or O(nm) for n \u00d7 m products. We apply "
    "this to every large product in the Nystr\u00f6m pipeline, making total "
    "in-circuit cost linear in n."
); idx += 1

set_body_with_header(P[idx],
    "Pseudoinverse Verification. ",
    "Computing the pseudoinverse inside the circuit is prohibitively "
    "expensive. The prover computes it off-circuit via Newton\u2013Schulz "
    "iteration and supplies it as a witness. The circuit verifies the four "
    "Moore\u2013Penrose conditions element-wise on m \u00d7 m matrices at "
    "negligible O(m\u00b3) cost for m = 32."
); idx += 1

set_body_with_header(P[idx],
    "Commit-Carrying SNARK. ",
    "Model weights are committed once under a circuit-independent key. Each "
    "proof carries a circuit-dependent commitment linked via CP-linkage [3], "
    "enabling constant-time verification. This moves expensive group "
    "exponentiations outside the circuit, critical for scaling to large "
    "weight matrices."
); idx += 1

# ── 3. EXPERIMENTAL RESULTS ─────────────────────────────────────────
set_empty(P[idx]); idx += 1
set_heading(P[idx], "3. EXPERIMENTAL RESULTS"); idx += 1
set_empty(P[idx]); idx += 1

set_body(P[idx],
    "We implement zkDietFormer using Groth16 [6] and benchmark on five "
    "BERT-family configurations\u2014Tiny (L=2, d=128), Mini (4, 256), "
    "Small (4, 512), Medium (8, 512), and Base (12, 768)\u2014on an Apple "
    "M1 Ultra with 128 GB unified memory (CPU only). All metrics are per "
    "single layer averaged over L layers."
); idx += 1

set_body(P[idx],
    "On the Tiny model, the full combination of Nystr\u00f6m + Freivalds "
    "achieves 4.1\u00d7 constraint reduction (39.22M \u2192 9.55M at "
    "n=256), 4.8\u00d7 prove-time reduction (345.44 s \u2192 72.02 s), and "
    "2.0\u00d7 memory reduction (112.13 GB \u2192 56.25 GB) over standard "
    "BERT attention with naive verification. BERT exhausts 128 GB at "
    "n \u2265 512, while Nystr\u00f6m-Freivalds extends to n = 1024."
); idx += 1

set_body(P[idx],
    "Across the full model family, BERT prove time scales as O(n\u00b2) "
    "while Nystr\u00f6m grows near-linearly. At Base (d=768), BERT caps at "
    "n=512 while Nystr\u00f6m reaches n=2048\u2014a 4\u00d7 extension. "
    "Quantization to 26-bit fixed-point preserves 98.8% top-1 agreement "
    "with the floating-point model."
); idx += 1

# ── 4. CONCLUSION ───────────────────────────────────────────────────
set_empty(P[idx]); idx += 1
set_heading(P[idx], "4. CONCLUSION"); idx += 1
set_empty(P[idx]); idx += 1

set_body(P[idx],
    "zkDietFormer demonstrates that low-rank attention structure can be "
    "systematically exploited for linear-cost zero-knowledge proofs. The "
    "combination of Nystr\u00f6m approximation with Freivalds verification "
    "yields multiplicative constraint savings and extends the scalability "
    "boundary of verifiable Transformer inference."
); idx += 1

# ── References ───────────────────────────────────────────────────────
set_empty(P[idx]); idx += 1
set_heading(P[idx], "References"); idx += 1
set_empty(P[idx]); idx += 1

refs = [
    "[1] Freivalds, R. Probabilistic machines can use less running time. "
        "In IFIP Congress (1977)",
    "[2] Xiong, Y. et al. Nystr\u00f6mformer: A Nystr\u00f6m-based algorithm "
        "for approximating self-attention. In AAAI (2021)",
    "[3] Campanelli, M. et al. LegoSNARK: Modular design and composition of "
        "succinct zero-knowledge proofs. In CCS (2019)",
    "[4] Liu, T. et al. zkCNN: Zero knowledge proofs for CNN predictions and "
        "accuracy. In CCS (2021)",
    "[5] Sun, H. et al. zkLLM: Zero knowledge proofs for large language "
        "models. arXiv:2404.16109 (2024)",
    "[6] Groth, J. On the size of pairing-based non-interactive arguments. "
        "In EUROCRYPT, pp. 305\u2013326 (2016)",
    "[7] Thaler, J. Time-optimal interactive proofs for circuit evaluation. "
        "In CRYPTO, pp. 71\u201389 (2013)",
]
for ref in refs:
    set_ref(P[idx], ref); idx += 1

# ── hide leftover template paragraphs ────────────────────────────────
total_eng = len(doc.paragraphs) - ENG_START
for j in range(idx, total_eng):
    hide_para(P[j])

doc.save(OUTPUT)
print(f"Saved: {OUTPUT}")
print(f"Used {idx} paragraphs, hid {total_eng - idx} leftover paragraphs")
