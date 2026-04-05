"""
Experiment 23 — Custom Self-Attention on Digital Root Sequences
================================================================
Question: When a lightweight self-attention mechanism is trained on the
          sequence of digital root values within each surah, which
          positions attend to which? Does the attention pattern differ
          between D369 surahs (51 with root in {3,6,9}) and non-D369 surahs?

Method:
  1. Represent each surah as a sequence of digit roots (integers 1-9)
  2. Build a minimal PyTorch self-attention classifier:
     - Embedding: 9 values -> d_model=16
     - Sinusoidal positional encoding
     - Single self-attention layer (2 heads)
     - Binary classifier: is surah's total DR in {3,6,9}?
  3. Train with Leave-One-Out cross-validation (114 folds)
  4. Extract and analyze learned attention weights
  5. Compare D369 vs non-D369 attention templates

Key insight: The attention maps directly reveal which word POSITIONS
within a surah "cooperate" to produce the {3,6,9} total.

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
"""

import sys
import os
import json
import random
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from attention_utils import load_surah_sequences

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
MAX_LEN = 128  # Truncate long surahs for feasible CPU training


# ──────────────────────────────────────────────────────────────
# Model Architecture
# ──────────────────────────────────────────────────────────────

class SinusoidalPE(nn.Module):
    """Sinusoidal positional encoding."""
    def __init__(self, d_model, max_len=8000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model > 1:
            pe[:, 1::2] = torch.cos(position * div_term[:d_model // 2])
        self.register_buffer('pe', pe.unsqueeze(0))  # (1, max_len, d_model)

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]


class D369AttentionClassifier(nn.Module):
    """
    Minimal self-attention classifier for digit root sequences.

    Architecture:
      digit root (1-9) -> embedding (d_model) -> positional encoding
      -> multi-head self-attention (n_heads) -> global average pooling
      -> linear classifier -> sigmoid
    """
    def __init__(self, d_model=16, n_heads=2, n_values=10):
        super().__init__()
        self.embedding = nn.Embedding(n_values, d_model)  # 0-9
        self.pos_enc = SinusoidalPE(d_model)
        self.attention = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.classifier = nn.Linear(d_model, 1)

    def forward(self, x, return_attention=False):
        """
        Args:
            x: (batch, seq_len) integer tensor of digit roots
            return_attention: if True, also return attention weights

        Returns:
            logits: (batch, 1)
            attn_weights: (batch, seq_len, seq_len) if return_attention=True
        """
        emb = self.embedding(x)
        emb = self.pos_enc(emb)
        attn_out, attn_weights = self.attention(emb, emb, emb)
        pooled = attn_out.mean(dim=1)  # global average pooling
        logits = self.classifier(pooled)

        if return_attention:
            return logits, attn_weights
        return logits


def pad_sequence(seq, max_len):
    """Pad or truncate a sequence to max_len."""
    if len(seq) <= max_len:
        padded = np.zeros(max_len, dtype=np.int32)
        padded[:len(seq)] = seq
        return padded, len(seq)
    else:
        return seq[:max_len].copy(), max_len


def train_and_evaluate(sequences, use_k6=True, d_model=16, n_heads=2, epochs=30, lr=0.01):
    """
    Train a single model on all data and extract attention patterns.
    Then evaluate with 10-fold cross-validation for accuracy.

    Args:
        sequences: list of surah dicts from load_surah_sequences()
        use_k6: use K6 encoding (True) or Abjad (False) for labels

    Returns:
        predictions: list of (surah_id, predicted_prob, true_label)
        attention_maps: dict {surah_id: attention_weight_matrix}
    """
    label_key = 'is_d369_k6' if use_k6 else 'is_d369_abjad'
    dr_key = 'k6_digit_roots' if use_k6 else 'digit_roots'

    # Prepare all data
    all_X = []
    all_y = []
    all_lens = []
    for s in sequences:
        dr_seq = s[dr_key]
        padded, length = pad_sequence(dr_seq, MAX_LEN)
        all_X.append(padded)
        all_y.append(1.0 if s[label_key] else 0.0)
        all_lens.append(length)

    all_X_t = torch.tensor(np.array(all_X), dtype=torch.long)
    all_y_t = torch.tensor(all_y, dtype=torch.float32).unsqueeze(1)

    # --- Phase 1: Train full model for attention extraction ---
    print("  Training full model for attention analysis...")
    model = D369AttentionClassifier(d_model=d_model, n_heads=n_heads)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        logits = model(all_X_t)
        loss = criterion(logits, all_y_t)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            acc = ((torch.sigmoid(logits) >= 0.5).float() == all_y_t).float().mean()
            print(f"    Epoch {epoch+1}/{epochs}: loss={loss.item():.4f}, train_acc={acc.item():.3f}")

    # Extract attention maps
    model.eval()
    attention_maps = {}
    with torch.no_grad():
        for i, seq in enumerate(sequences):
            x = all_X_t[i:i+1]
            _, attn = model(x, return_attention=True)
            attn_np = attn[0, :all_lens[i], :all_lens[i]].numpy()
            attention_maps[seq['surah_id']] = attn_np

    # --- Phase 2: 10-fold CV for accuracy ---
    print("  Running 10-fold cross-validation...")
    n = len(sequences)
    indices = list(range(n))
    random.shuffle(indices)
    fold_size = n // 10
    predictions = [None] * n

    for fold in range(10):
        test_idx = indices[fold * fold_size: (fold + 1) * fold_size if fold < 9 else n]
        train_idx = [i for i in indices if i not in test_idx]

        train_X = all_X_t[train_idx]
        train_y = all_y_t[train_idx]

        cv_model = D369AttentionClassifier(d_model=d_model, n_heads=n_heads)
        cv_opt = torch.optim.Adam(cv_model.parameters(), lr=lr)

        cv_model.train()
        for epoch in range(epochs):
            cv_opt.zero_grad()
            logits = cv_model(train_X)
            loss = criterion(logits, train_y)
            loss.backward()
            cv_opt.step()

        cv_model.eval()
        with torch.no_grad():
            test_X = all_X_t[test_idx]
            test_logits = cv_model(test_X)
            test_probs = torch.sigmoid(test_logits).squeeze().numpy()

        if test_probs.ndim == 0:
            test_probs = np.array([test_probs.item()])

        for j, idx in enumerate(test_idx):
            true_label = 1 if sequences[idx][label_key] else 0
            prob = float(test_probs[j]) if j < len(test_probs) else 0.5
            predictions[idx] = (sequences[idx]['surah_id'], prob, true_label)

    # Filter None (shouldn't happen, but safety)
    predictions = [p for p in predictions if p is not None]

    return predictions, attention_maps


def analyze_attention_templates(attention_maps, sequences, use_k6=True):
    """
    Compute average attention templates for D369 vs non-D369 surahs.

    For each group: normalize surah attention to relative positions (0-1),
    then bin into a grid and average.
    """
    label_key = 'is_d369_k6' if use_k6 else 'is_d369_abjad'
    n_bins = 20  # 20x20 grid for normalized position

    d369_grids = []
    other_grids = []

    for seq in sequences:
        sid = seq['surah_id']
        if sid not in attention_maps:
            continue

        attn = attention_maps[sid]
        n = attn.shape[0]
        if n < 5:
            continue

        # Normalize to relative position grid
        grid = np.zeros((n_bins, n_bins), dtype=np.float32)
        counts = np.zeros((n_bins, n_bins), dtype=np.float32)

        for i in range(n):
            for j in range(n):
                bi = min(int(i / n * n_bins), n_bins - 1)
                bj = min(int(j / n * n_bins), n_bins - 1)
                grid[bi, bj] += attn[i, j]
                counts[bi, bj] += 1

        counts[counts == 0] = 1
        grid = grid / counts

        if seq[label_key]:
            d369_grids.append(grid)
        else:
            other_grids.append(grid)

    d369_template = np.mean(d369_grids, axis=0) if d369_grids else np.zeros((n_bins, n_bins))
    other_template = np.mean(other_grids, axis=0) if other_grids else np.zeros((n_bins, n_bins))
    diff_template = d369_template - other_template

    return d369_template, other_template, diff_template


def visualize_templates(d369_tmpl, other_tmpl, diff_tmpl, filepath):
    """Save attention template heatmaps."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    im0 = axes[0].imshow(d369_tmpl, cmap='Reds', aspect='equal')
    axes[0].set_title('D369 Surahs — Average Attention')
    axes[0].set_xlabel('Key Position (normalized)')
    axes[0].set_ylabel('Query Position (normalized)')
    plt.colorbar(im0, ax=axes[0])

    im1 = axes[1].imshow(other_tmpl, cmap='Blues', aspect='equal')
    axes[1].set_title('Non-D369 Surahs — Average Attention')
    axes[1].set_xlabel('Key Position (normalized)')
    axes[1].set_ylabel('Query Position (normalized)')
    plt.colorbar(im1, ax=axes[1])

    vmax = max(abs(diff_tmpl.min()), abs(diff_tmpl.max()))
    im2 = axes[2].imshow(diff_tmpl, cmap='RdBu_r', aspect='equal',
                          vmin=-vmax, vmax=vmax)
    axes[2].set_title('Difference (D369 - Other)')
    axes[2].set_xlabel('Key Position (normalized)')
    axes[2].set_ylabel('Query Position (normalized)')
    plt.colorbar(im2, ax=axes[2])

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def visualize_sample_attention(attention_maps, sequences, filepath, n_samples=6):
    """Visualize attention maps for sample surahs (3 D369 + 3 non-D369)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    d369_sids = [s['surah_id'] for s in sequences if s['is_d369_k6']]
    other_sids = [s['surah_id'] for s in sequences if not s['is_d369_k6']]

    # Pick short surahs for visibility
    short_d369 = sorted(d369_sids, key=lambda s: attention_maps.get(s, np.zeros((1,1))).shape[0])
    short_other = sorted(other_sids, key=lambda s: attention_maps.get(s, np.zeros((1,1))).shape[0])

    # Pick surahs with 20-80 words for best visualization
    samples_d369 = [s for s in short_d369 if 20 <= attention_maps.get(s, np.zeros((1,1))).shape[0] <= 80][:3]
    samples_other = [s for s in short_other if 20 <= attention_maps.get(s, np.zeros((1,1))).shape[0] <= 80][:3]

    if not samples_d369 or not samples_other:
        samples_d369 = short_d369[10:13]
        samples_other = short_other[10:13]

    samples = samples_d369 + samples_other
    labels = ['D369'] * len(samples_d369) + ['Other'] * len(samples_other)

    n = len(samples)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    if n == 1:
        axes = [axes]

    for idx, (sid, label) in enumerate(zip(samples, labels)):
        attn = attention_maps.get(sid)
        if attn is None:
            continue
        axes[idx].imshow(attn, cmap='viridis', aspect='equal')
        axes[idx].set_title(f'Surah {sid} ({label})\n{attn.shape[0]} words')
        axes[idx].set_xlabel('Key')
        axes[idx].set_ylabel('Query')

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def run():
    """Main experiment runner."""

    print("=" * 70)
    print("EXPERIMENT 23: Custom Self-Attention on Digital Root Sequences")
    print("=" * 70)

    # ── Step 1: Load data ──
    print("\n[1/5] Loading surah sequences...")
    sequences = load_surah_sequences()
    n_d369_k6 = sum(1 for s in sequences if s['is_d369_k6'])
    print(f"  114 surahs loaded")
    print(f"  D369 (K6): {n_d369_k6}/114 ({n_d369_k6/114*100:.1f}%)")
    print(f"  Surah lengths: min={min(len(s['digit_roots']) for s in sequences)}, "
          f"max={max(len(s['digit_roots']) for s in sequences)}, "
          f"median={int(np.median([len(s['digit_roots']) for s in sequences]))}")

    # ── Step 2: CV Training (K6) ──
    print("\n[2/5] Training + 10-fold CV (K6 labels)...")
    predictions_k6, attn_maps_k6 = train_and_evaluate(sequences, use_k6=True)

    # Compute accuracy
    correct = sum(1 for _, prob, true in predictions_k6 if (prob >= 0.5) == (true == 1))
    accuracy = correct / len(predictions_k6)
    print(f"  CV Accuracy (K6): {correct}/114 = {accuracy*100:.1f}%")

    # Baseline: always predict majority class
    baseline = max(n_d369_k6, 114 - n_d369_k6) / 114
    print(f"  Baseline (majority): {baseline*100:.1f}%")

    # Confidence analysis
    probs = [p for _, p, _ in predictions_k6]
    true_labels = [t for _, _, t in predictions_k6]
    mean_prob_d369 = np.mean([p for p, t in zip(probs, true_labels) if t == 1])
    mean_prob_other = np.mean([p for p, t in zip(probs, true_labels) if t == 0])
    print(f"  Mean predicted prob (true D369): {mean_prob_d369:.3f}")
    print(f"  Mean predicted prob (true Other): {mean_prob_other:.3f}")

    # ── Step 3: CV Training (Abjad) ──
    print("\n[3/5] Training + 10-fold CV (Abjad labels)...")
    predictions_abjad, attn_maps_abjad = train_and_evaluate(sequences, use_k6=False)
    correct_abjad = sum(1 for _, prob, true in predictions_abjad if (prob >= 0.5) == (true == 1))
    accuracy_abjad = correct_abjad / len(predictions_abjad)
    n_d369_abjad = sum(1 for s in sequences if s['is_d369_abjad'])
    print(f"  CV Accuracy (Abjad): {correct_abjad}/114 = {accuracy_abjad*100:.1f}%")

    # ── Step 4: Attention template analysis ──
    print("\n[4/5] Analyzing attention templates...")
    d369_tmpl, other_tmpl, diff_tmpl = analyze_attention_templates(
        attn_maps_k6, sequences, use_k6=True
    )

    # Key finding: where does D369 attention concentrate?
    max_diff_pos = np.unravel_index(np.argmax(np.abs(diff_tmpl)), diff_tmpl.shape)
    print(f"  Largest difference at normalized position: "
          f"query={max_diff_pos[0]/20:.2f}, key={max_diff_pos[1]/20:.2f}")
    print(f"  Difference value: {diff_tmpl[max_diff_pos]:.4f}")

    # Diagonal analysis (self-attention to nearby positions)
    diag_d369 = np.mean([d369_tmpl[i, i] for i in range(d369_tmpl.shape[0])])
    diag_other = np.mean([other_tmpl[i, i] for i in range(other_tmpl.shape[0])])
    print(f"  Self-attention (diagonal) D369:  {diag_d369:.4f}")
    print(f"  Self-attention (diagonal) Other: {diag_other:.4f}")

    # ── Step 5: Visualizations ──
    print("\n[5/5] Generating visualizations...")
    visualize_templates(
        d369_tmpl, other_tmpl, diff_tmpl,
        os.path.join(RESULTS_DIR, 'attention_templates_k6.png')
    )

    visualize_sample_attention(
        attn_maps_k6, sequences,
        os.path.join(RESULTS_DIR, 'sample_attention_maps.png')
    )

    # ── Summary ──
    print("\n" + "=" * 70)
    print("SUMMARY — Experiment 23: Custom Self-Attention on Digit Root Sequences")
    print("=" * 70)
    print(f"\nClassification Performance:")
    print(f"  K6:    {accuracy*100:.1f}% (baseline: {baseline*100:.1f}%)")
    print(f"  Abjad: {accuracy_abjad*100:.1f}% (baseline: {max(n_d369_abjad, 114-n_d369_abjad)/114*100:.1f}%)")

    if accuracy > baseline + 0.05:
        print("\n  RESULT: Self-attention CAN learn D369 structure from digit root sequences")
        print("  --> The sequence of digit roots carries learnable structural information")
    else:
        print("\n  RESULT: Self-attention CANNOT distinguish D369 from sequence alone")
        print("  --> The D369 signal is distributed and not positionally learnable")

    print(f"\nAttention Pattern Analysis:")
    if abs(diag_d369 - diag_other) > 0.01:
        print(f"  D369 surahs show {'more' if diag_d369 > diag_other else 'less'} "
              f"self-attention (local focus) than non-D369 surahs")
    else:
        print(f"  No significant difference in self-attention patterns between groups")

    # Save results
    results = {
        'k6': {
            'accuracy': accuracy,
            'baseline': baseline,
            'n_d369': n_d369_k6,
            'predictions': [(sid, float(p), t) for sid, p, t in predictions_k6],
        },
        'abjad': {
            'accuracy': accuracy_abjad,
            'n_d369': n_d369_abjad,
        },
        'attention': {
            'diagonal_d369': float(diag_d369),
            'diagonal_other': float(diag_other),
            'max_diff_position': [int(max_diff_pos[0]), int(max_diff_pos[1])],
        }
    }
    with open(os.path.join(RESULTS_DIR, 'results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == '__main__':
    run()
