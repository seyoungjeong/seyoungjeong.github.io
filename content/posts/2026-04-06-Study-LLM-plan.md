---
title: Study LLM 3-day implementation plan
date: 2026-04-06T12:00:00+09:00
lastmod: 2026-04-06T02:50:00+09:00
description: GPT-2 스타일 decoder-only transformer를 3일 계획으로 구현하는 단계별 일정
categories:
  - Coding
tags:
  - StudyLLM
draft: true
---
# Study LLM — 3-Day Implementation Plan

> Spec: [Study LLM specification](../2026-04-04-Study-LLM-spec)

Start with **Tiny config** (4L, d=128, vocab=65 char-level) to validate the full pipeline end-to-end before scaling up to **Small config** (~30M params).

---

## Day 1 — Project setup + Data pipeline + Model architecture

**Goal:** Token batches loading cleanly; forward pass runs; loss ≈ `ln(65) ≈ 4.17` at random init.

### Tasks

1. Create project skeleton at `~/ws/study-llm/`

   ```
   study-llm/
   ├── data/prepare.py
   ├── model.py
   ├── train.py
   ├── inference.py
   ├── config.py
   └── checkpoints/
   ```

2. Set up Python virtual environment and install dependencies

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install torch numpy tiktoken
   ```

3. Write `config.py` — `TinyConfig` and `SmallConfig` dataclasses

   | Field | Tiny | Small |
   |---|---|---|
   | `n_layers` | 4 | 6 |
   | `d_model` | 128 | 384 |
   | `n_heads` | 4 | 6 |
   | `d_ff` | 512 | 1536 |
   | `block_size` | 256 | 512 |
   | `vocab_size` | 65 | 50257 |
   | `batch_size` | 32 | 32 |
   | `dropout` | 0.1 | 0.1 |

4. Write `data/prepare.py`
   - Download Shakespeare corpus
   - Build char-level vocab (65 tokens), encode full text to `uint16`
   - Split 90% → `train.bin`, 10% → `val.bin`
   - `DataLoader` class: `get_batch(split)` returns `(x, y)` tensors of shape `[batch_size, block_size]`

5. **Verify data:** `x.shape == (32, 256)`, `y == x` shifted by 1, values in `[0, 64]`

6. Write `model.py` with four classes:

   **`CausalSelfAttention`**
   - Fused Q/K/V linear, output projection
   - Causal mask via `torch.tril` (register as buffer)
   - Dropout on attention weights

   **`FeedForward`**
   - `Linear(d_model → d_ff) → GELU → Linear(d_ff → d_model)`
   - Dropout on output

   **`TransformerBlock`**
   - Pre-norm: `LayerNorm → CausalSelfAttention → residual`
   - Pre-norm: `LayerNorm → FeedForward → residual`

   **`GPT`**
   - Token embedding + learned positional embedding
   - Stack of N `TransformerBlock`s
   - Final `LayerNorm`
   - `lm_head`: `Linear(d_model, vocab_size, bias=False)` — **weight-tied** to token embedding
   - `forward(idx)` returns logits `[B, T, vocab_size]`

7. **Verify model:**
   ```python
   cfg = TinyConfig()
   model = GPT(cfg)
   x = torch.randint(0, 65, (4, 256))
   logits = model(x)           # → [4, 256, 65]
   loss = F.cross_entropy(logits.view(-1, 65), x.view(-1))
   print(loss.item())          # ≈ 4.17
   # sum(p.numel() for p in model.parameters()) ≈ 834K
   ```

---

## Day 2 — Training loop + Checkpointing

**Goal:** Loss decreasing on MPS with bfloat16; best checkpoint saves on val improvement.

### Tasks

1. Write basic training loop in `train.py`
   - `device = torch.device("mps")`
   - Cast model to `bfloat16`
   - `optimizer = AdamW(param_groups, lr, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.1)`
   - Param groups: weight decay **only** on 2D weight tensors (not embeddings, not LayerNorm)

2. Add LR scheduler (computed manually inside the loop)

   ```
   warmup_steps = 100
   max_steps    = 5000   # Tiny
   min_lr       = 6e-5   # 10% of peak

   if step < warmup_steps:
       lr = peak_lr * step / warmup_steps
   else:
       ratio = (step - warmup_steps) / (max_steps - warmup_steps)
       lr = min_lr + 0.5 * (peak_lr - min_lr) * (1 + cos(π * ratio))
   ```

3. Add gradient clipping

   ```python
   norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
   ```

   Log `norm` every 10 steps to confirm clipping fires early, then stabilises.

4. **Verify training:** Run 100 steps; loss drops from ~4.17 toward ~3.x; no NaN/inf.

5. Add validation loop to `train.py`
   - Run every 200 steps on `val.bin`
   - Save `checkpoints/best.pt` when val loss improves
   - Checkpoint contains: `model.state_dict()`, `optimizer.state_dict()`, `step`, `val_loss`, `config`

6. **Verify checkpoint round-trip:**
   ```python
   loss_before = eval(model)
   torch.save(ckpt, "best.pt")
   model.load_state_dict(torch.load("best.pt")["model"])
   loss_after = eval(model)
   assert abs(loss_before - loss_after) < 1e-5
   ```

---

## Day 3 — Inference + Small config + Evaluation

**Goal:** Prompt → generated text from Tiny checkpoint; ~30M model training with perplexity tracked.

### Tasks

1. Write `inference.py`
   - Load `best.pt`, reconstruct model from saved config
   - `generate(prompt, max_new_tokens, temperature, top_k, top_p)`
     - Tokenize prompt → `[1, T]`
     - Loop: forward → logits at `[:, -1, :]` → apply temperature → top-k mask → top-p mask → softmax → sample → append
   - Default params: `temperature=0.8`, `top_k=40`, `top_p=0.9`, `max_new_tokens=200`

2. **Verify:** `python inference.py --prompt "To be or not"` → 200 chars of plausible Shakespeare-style text.

3. Add BPE path to `data/prepare.py`
   - Download TinyStories or WikiText-2
   - Tokenize with `tiktoken.get_encoding("gpt2")`
   - Write `train.bin` / `val.bin` as `uint16` (same format as Tiny)

4. Switch to `SmallConfig` in `train.py`; adjust `max_steps = 10000`, `peak_lr = 6e-4`

5. Add perplexity logging: `ppl = exp(val_loss)` printed at each validation step

6. Run training; inspect generated samples at steps 1000, 3000, 5000

7. **Expected metrics:**

   | Step | Perplexity |
   |---|---|
   | 0 (random) | ~50,257 |
   | 500 | ~100–200 |
   | 3000 | ~30–60 |
   | Converged | ~20–40 |

8. **(Stretch)** Experiments in separate branches:
   - Swap `GELU → SwiGLU` in `FeedForward`
   - Replace learned positional embedding with `RoPE`
   - Compare val perplexity after 3000 steps

---

## Reference configs

| | Tiny | Small |
|---|---|---|
| **Purpose** | Pipeline validation | Main training target |
| **Params** | ~834K | ~30M |
| **Vocab** | 65 (char) | 50,257 (BPE) |
| **Corpus** | Shakespeare | TinyStories / WikiText-2 |
| **Est. train time** | ~5 min | ~1 hr |
| **Device** | MPS bfloat16 | MPS bfloat16 |
