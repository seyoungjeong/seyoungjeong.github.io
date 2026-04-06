---
title: Study LLM specification
date: 2026-04-04T01:00:00+09:00
lastmod: 2026-04-06T02:40:00+09:00
description: LLM을 이해하기 위해서 24GB 메모리를 가진 M5 Mac Pro에서 ~30M 파라메터 크기의 LLM을 Claude Code의 도움을 받아 바닥에서 부터 만들어 보기로 함.
categories:
  - Coding
tags:
  - StudyLLM
draft: true
---
# Study LLM — High-Level Specification

## 1. Project goal

Build a decoder-only transformer language model from scratch for the purpose of understanding every component end-to-end. Target scale is the "Small" config (~30M parameters). The model should be trainable to coherent output on a single M5 Pro Mac (24GB unified memory) in under a few hours.



---

## 2. Architecture configuration

| Parameter           | Tiny (~830K) | Small (~30M)     | Medium (~124M) | LLaMA 3 8B (ref) |
| ------------------- | ------------ | ---------------- | -------------- | ---------------- |
| Layers              | 4            | **6**            | 12             | 32               |
| Model dimension     | 128          | **384**          | 768            | 4,096            |
| FFN dimension       | 512          | **1,536**        | 3,072          | 14,336           |
| Attention heads     | 4            | **6**            | 12             | 32               |
| Key/value heads     | 4            | **6**            | 12             | 8 (GQA)          |
| Context length      | 256          | **512**          | 1,024          | 8,192            |
| Peak learning rate  | 1×10⁻³       | **6×10⁻⁴**       | 3×10⁻⁴         | 3×10⁻⁴           |
| Activation function | GELU         | **GELU**         | SwiGLU         | SwiGLU           |
| Vocabulary size     | 65 (char)    | **50,257**       | 50,257         | 128,000          |
| Positional encoding | Learned abs. | **Learned abs.** | RoPE           | RoPE             |
| Train time (M5 Pro) | ~5 min       | **~1 hr**        | ~8 hrs         | —                |

> Bold = recommended starting configuration (Small). Tiny is best for first pipeline validation.  
> FFN dim = 4× model dim for GELU; ~3.5× for SwiGLU. Vocabulary of 65 = all unique characters in Shakespeare corpus.

> 파라메터 크기 계산은 [Appendix A](#appendix-a-parameter-count) 참고.

---

## 3. System components

The project has four major subsystems. They are largely independent and can be built and tested in isolation.

| Subsystem | Responsibility |
|---|---|
| Data pipeline | Convert raw text → binary token arrays for training |
| Model architecture | Decoder-only transformer: forward pass only |
| Training loop | Autoregressive LM objective, optimizer, checkpointing |
| Inference engine | Autoregressive sampling from a trained checkpoint |

{{< drawio "/diagrams/study_llm_diagrams.drawio" >}}

---

## 4. Data pipeline

Converts raw text into a binary token array that the training loop can stream efficiently.

**Stages:**

1. **Acquire corpus** — Shakespeare (~1MB) for initial run; WikiText-2 or TinyStories for Small config
2. **Tokenize** — character-level (vocab 65) for Tiny; GPT-2 BPE via `tiktoken` (vocab 50,257) for Small+
3. **Encode + split** — 90% `train.bin` / 10% `val.bin`, stored as `uint16` arrays
4. **DataLoader** — samples random windows of `block_size` tokens at training time

**Key parameters:**

- `block_size` = 512 (context window / sequence length)
- `batch_size` = 32

---

## 5. Model architecture

Standard GPT-2 style decoder-only transformer.

### 5.1 Component stack (top to bottom)

```
Input token IDs  [B, T]
      ↓
Token embedding + positional embedding  →  [B, T, d_model]
      ↓
[ Transformer Block ] × N layers
  ├─ Pre-norm LayerNorm
  ├─ Multi-head self-attention  (causal mask)
  ├─ Residual add
  ├─ Pre-norm LayerNorm
  ├─ Feed-forward network  (Linear → GELU → Linear)
  └─ Residual add
      ↓
Final LayerNorm
      ↓
Linear projection  (weight-tied with token embedding)  →  [B, T, vocab_size]
      ↓
Logits
```

### 5.2 Multi-head self-attention

```
Q = x · W_q      # "what am I looking for?"
K = x · W_k      # "what do I contain?"
V = x · W_v      # "what do I return if matched?"

scores = Q · Kᵀ / sqrt(d_head)
scores = masked_fill(scores, causal_mask)   # no future token access
weights = softmax(scores)
output  = weights · V
```

- `d_head` = `d_model` / `n_heads` = 384 / 6 = **64**
- Causal mask ensures position `t` can only attend to positions `≤ t`

### 5.3 Feed-forward network

```
x → Linear(d_model → 4·d_model) → GELU → Linear(4·d_model → d_model)
```

- FFN dimension = 4 × 384 = **1,536**
- Dropout (0.1) applied after attention weights and after FFN output

### 5.4 Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Norm position | Pre-norm (before attn/FFN) | More stable gradients than post-norm |
| Weight tying | Output projection = token embedding | Saves ~20M params; empirically better |
| Positional encoding | Learned absolute | Simplest to implement; sufficient for study |
| Dropout | 0.1 | Regularization; disable at inference |

---

## 6. Training loop

### 6.1 Objective

Autoregressive next-token prediction. Given input sequence `x = [t₀, t₁, ..., t_{T-1}]`, predict `y = [t₁, t₂, ..., t_T]` at every position. Loss is cross-entropy averaged over all positions and all batch examples.

### 6.2 Optimizer

- **AdamW** with `β₁=0.9`, `β₂=0.95`, `ε=1e-8`, `weight_decay=0.1`
- Do not apply weight decay to embeddings or LayerNorm parameters

### 6.3 Learning rate schedule

1. **Linear warmup** — steps 0 → 100, LR increases from 0 to peak (6×10⁻⁴)
2. **Cosine decay** — steps 100 → max_steps, LR decays to 10% of peak
3. **Minimum LR** = 6×10⁻⁵

### 6.4 Gradient clipping

Clip gradient vector norm to **1.0** before each optimizer step. Preserves gradient direction; prevents weight explosions from abnormally large gradient norms. Applied as:

```
‖g‖ > 1.0  →  g = g × (1.0 / ‖g‖)
```

### 6.5 Hardware

- Device: `torch.device("mps")` on M5 Pro
- Dtype: `bfloat16` for activations (halves memory, improves throughput)
- Evaluation on `val.bin` every **200 steps**
- Checkpoint saved on validation loss improvement

### 6.6 Expected metrics

| Phase | Perplexity (Shakespeare) |
|---|---|
| Random init | ~65 (= vocab size) |
| After 500 steps | ~10–15 |
| Converged | ~3–5 |

---

## 7. Inference engine

### 7.1 Generation loop

```
1. Tokenize prompt  →  token ID sequence
2. Forward pass     →  logits at final position  [vocab_size]
3. Apply temperature:  logits /= T
4. Apply top-k:        zero out all but top-k logits
5. Softmax            →  probability distribution
6. Sample             →  next token ID
7. Append to sequence, repeat from step 2
```

### 7.2 Sampling parameters

| Parameter | Description | Typical value |
|---|---|---|
| Temperature | Scales logit magnitude. Higher = more random | 0.8 – 1.0 |
| Top-k | Restrict to k highest-probability tokens | 40 – 200 |
| Top-p | Nucleus: smallest set summing to probability p | 0.9 |
| Max new tokens | Generation length limit | 200 – 500 |

### 7.3 KV-cache (optional optimization)

Instead of recomputing all past key/value tensors at each step, cache and reuse them. Reduces per-step cost from O(T²) to O(T). Implement after the baseline works.

---

## 8. Evaluation

- **Primary metric**: validation perplexity = `exp(cross_entropy_loss)` on `val.bin`
- **Qualitative**: inspect generated samples at checkpoints — look for grammatical structure, consistent style, plausible word sequences
- **Overfitting check**: training loss should track validation loss; large gap = overfitting → increase dropout or reduce model size

---

## 9. Suggested build order

| Step | Task | Verify |
|---|---|---|
| 1 | Data pipeline | Load a batch, check shape `[32, 512]` |
| 2 | Model forward pass | Input `[B, T]` → output `[B, T, 50257]`, no errors |
| 3 | Loss computation | Cross-entropy ≈ `ln(50257)` ≈ 10.8 at random init |
| 4 | Training loop (basic) | Loss decreases over 100 steps |
| 5 | LR schedule + grad clip | Monitor norm before/after clip |
| 6 | Checkpointing | Save + reload weights, loss identical |
| 7 | Inference / generation | Prompt → coherent text output |
| 8 | Experiments | Swap GELU→SwiGLU, add RoPE, try GQA |

---

## 10. File structure

```
study-llm/
├── data/
│   ├── prepare.py          # download + tokenize + write .bin files
│   ├── train.bin
│   └── val.bin
├── model.py                # transformer architecture (forward pass only)
├── train.py                # training loop, optimizer, checkpointing
├── inference.py            # load checkpoint, generate text
├── config.py               # hyperparameter dataclass
└── checkpoints/
    └── best.pt
```

---

## Appendix A: Parameter count

Total parameters = embeddings + N × block + final LN. Output head is weight-tied to the token embedding, so it adds zero extra parameters.

### Formula

| Component | Formula | Notes |
|---|---|---|
| Token embedding | `vocab × d` | |
| Positional embedding | `ctx × d` | |
| **Per block (× N layers):** | | |
| LayerNorm ×2 | `2 × (2d)` | weight + bias each |
| Attn Q, K, V projections | `3 × (d² + d)` | weight + bias each |
| Attn output projection | `d² + d` | weight + bias |
| FFN fc1 | `d × d_ff + d_ff` | weight + bias |
| FFN fc2 | `d_ff × d + d` | weight + bias |
| Final LayerNorm | `2d` | weight + bias |
| Output head | `0` | weight-tied with token embedding |

Where `d` = `d_model`, `d_ff` = 4 × `d_model`.

### Worked examples

**Tiny** (4L, d=128, d_ff=512, ctx=256, vocab=65):

```
Token embedding:      65 × 128              =       8,320
Positional embedding: 256 × 128             =      32,768
Per block:
  LN ×2:             2 × (2 × 128)          =         512
  Attn Q,K,V:        3 × (128² + 128)       =      49,536
  Attn out:          128² + 128             =      16,512
  FFN fc1:           128 × 512 + 512        =      66,048
  FFN fc2:           512 × 128 + 128        =      65,664
  Block subtotal                            =     198,272
4 blocks:             4 × 198,272           =     793,088
Final LN:             2 × 128               =         256
─────────────────────────────────────────────────────────
Total                                       =     834,432  ≈ 830K ✓
```

**Small** (6L, d=384, d_ff=1536, ctx=512, vocab=50,257):

```
Token embedding:      50,257 × 384          =  19,298,688
Positional embedding: 512 × 384             =     196,608
Per block:
  LN ×2:             2 × (2 × 384)          =       1,536
  Attn Q,K,V:        3 × (384² + 384)       =     443,520
  Attn out:          384² + 384             =     147,840
  FFN fc1:           384 × 1,536 + 1,536    =     591,360
  FFN fc2:           1,536 × 384 + 384      =     590,208
  Block subtotal                            =   1,774,464
6 blocks:             6 × 1,774,464         =  10,646,784
Final LN:             2 × 384               =         768
─────────────────────────────────────────────────────────
Total                                       =  30,142,848  ≈ 30M ✓
```

> Without weight tying, the output head (`vocab × d`) would add another ~19M parameters to the Small config — nearly doubling the count. Weight tying is a significant saving.