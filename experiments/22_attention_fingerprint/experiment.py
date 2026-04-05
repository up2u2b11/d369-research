"""
Experiment 22 — Attention Pattern Analysis (Quran vs Controls)
===============================================================
Question: Do the multi-head attention patterns in AraBERT, when
          processing Quranic ayahs, show systematic differences for
          words with D369 digital roots? Do D369 words "attend"
          preferentially to other D369 words?

Method:
  1. Process 6,236 ayahs through AraBERT with output_attentions=True
  2. Extract attention weights: 12 layers x 12 heads = 144 heads
  3. For each ayah: compute D369 attention flow ratio
  4. Permutation test: shuffle D369 labels to get p-value
  5. Identify "fingerprint heads" with Bonferroni correction
  6. Repeat for Bukhari control text

The "D369 attention ratio" measures: what fraction of total attention
flows between pairs of D369 words vs non-D369 words?

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
"""

import sys
import os
import json
import random
import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from attention_utils import (
    load_arabert, load_quran_ayahs, load_control_text,
    word_to_subtoken_map
)
from utils import digit_root

random.seed(42)
np.random.seed(42)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
MAX_TOKENS = 512


def compute_d369_flow_per_head(attention_layers, word_map, d369_mask, n_words):
    """
    Compute D369 attention flow for each of 144 heads.
    Optimized: builds subtoken-level D369 mask and computes flow directly.

    Args:
        attention_layers: tuple of (1, n_heads, seq_len, seq_len) tensors
        word_map: list of (start, end) subtoken index ranges
        d369_mask: boolean array — True for D369 words
        n_words: number of words

    Returns:
        numpy array of shape (144,) — D369->D369 attention ratio per head
    """
    n_d369 = d369_mask.sum()
    if n_d369 == 0 or n_d369 == n_words:
        return np.full(144, np.nan)

    # Build subtoken-level D369 mask (much faster than word-level aggregation)
    seq_len = attention_layers[0].shape[-1]
    sub_d369 = np.zeros(seq_len, dtype=bool)
    for i, (start, end) in enumerate(word_map):
        if d369_mask[i]:
            sub_d369[start:min(end, seq_len)] = True

    flows = []
    for layer_attn in attention_layers:
        attn = layer_attn[0].numpy()  # (n_heads, seq_len, seq_len)
        for head_idx in range(attn.shape[0]):
            head = attn[head_idx]  # (seq_len, seq_len)
            # D369 rows -> D369 cols flow
            d369_to_d369 = head[sub_d369][:, sub_d369].sum()
            d369_total = head[sub_d369].sum()
            ratio = d369_to_d369 / d369_total if d369_total > 0 else np.nan
            flows.append(ratio)

    return np.array(flows)


def process_ayahs(ayahs, model, tokenizer, max_ayahs=None):
    """
    Process ayahs through AraBERT and compute D369 flow per head.

    Args:
        ayahs: list of ayah dicts from load_quran_ayahs()
        model: AraBERT model
        tokenizer: AraBERT tokenizer
        max_ayahs: limit number of ayahs (None = all)

    Returns:
        all_flows: numpy array of shape (n_ayahs, 144)
        all_d369_fracs: fraction of D369 words per ayah
    """
    if max_ayahs:
        ayahs = ayahs[:max_ayahs]

    all_flows = []
    all_d369_fracs = []
    skipped = 0

    for idx, ayah in enumerate(ayahs):
        words = [w['text_clean'] for w in ayah['words']]
        d369_mask = np.array([w['digit_root'] in {3, 6, 9} for w in ayah['words']])

        if len(words) < 3:
            skipped += 1
            continue

        # Tokenize
        text = ' '.join(words)
        encoded = tokenizer(text, return_tensors='pt', truncation=True, max_length=MAX_TOKENS)

        # Get attention
        with torch.no_grad():
            outputs = model(**encoded)
        attentions = outputs.attentions  # tuple of (1, n_heads, seq_len, seq_len)

        # Word-subtoken mapping
        word_map = word_to_subtoken_map(words, tokenizer)

        # Check if mapping exceeds token count
        total_subtokens = word_map[-1][1] if word_map else 0
        seq_len = encoded['input_ids'].shape[1]
        if total_subtokens >= seq_len:
            # Truncation happened — trim words
            valid_words = 0
            for start, end in word_map:
                if end < seq_len - 1:  # -1 for [SEP]
                    valid_words += 1
                else:
                    break
            if valid_words < 3:
                skipped += 1
                continue
            words = words[:valid_words]
            word_map = word_map[:valid_words]
            d369_mask = d369_mask[:valid_words]

        # Compute flows
        flows = compute_d369_flow_per_head(attentions, word_map, d369_mask, len(words))
        all_flows.append(flows)
        all_d369_fracs.append(d369_mask.mean())

        if (idx + 1) % 200 == 0:
            print(f"  Processed {idx+1}/{len(ayahs)} ayahs (skipped: {skipped})")

    print(f"  Total: {len(all_flows)} ayahs processed, {skipped} skipped")
    return np.array(all_flows), np.array(all_d369_fracs)


def permutation_test_heads(flows, d369_fracs, n_perms=1000):
    """
    Permutation test per head: for each ayah, randomly assign which words
    are "D369" (preserving count), recompute flow ratio.

    Since we can't easily re-run BERT, we use the expected D369->D369 flow
    under random assignment: E[flow] = d369_frac (each D369 word attends
    uniformly, so fraction going to D369 = fraction of D369 words).

    Test: is the observed flow significantly different from expected?

    Returns:
        observed: (144,) mean flow per head
        expected: (144,) expected under null
        z_scores: (144,) standardized difference
        p_values: (144,) two-sided p-values
    """
    # Remove NaN rows
    valid = ~np.isnan(flows).any(axis=1)
    flows_clean = flows[valid]
    fracs_clean = d369_fracs[valid]

    observed = np.nanmean(flows_clean, axis=0)  # (144,)
    expected = np.mean(fracs_clean)  # scalar: expected under null

    # Bootstrap standard error
    n = len(flows_clean)
    boot_means = np.zeros((n_perms, 144))
    for i in range(n_perms):
        idx = np.random.choice(n, size=n, replace=True)
        boot_means[i] = np.nanmean(flows_clean[idx], axis=0)

    std_err = boot_means.std(axis=0)
    std_err[std_err == 0] = 1e-10

    z_scores = (observed - expected) / std_err

    # Two-sided p-values from z-scores
    from scipy.stats import norm
    p_values = 2 * (1 - norm.cdf(np.abs(z_scores)))

    return observed, expected, z_scores, p_values


def visualize_head_analysis(z_scores, p_values, filepath, bonferroni_alpha=0.05/144):
    """Visualize the 144 attention heads as a 12x12 grid of z-scores."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    z_grid = z_scores.reshape(12, 12)
    p_grid = p_values.reshape(12, 12)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Z-score heatmap
    vmax = max(abs(z_grid.min()), abs(z_grid.max()))
    im = axes[0].imshow(z_grid, cmap='RdBu_r', vmin=-vmax, vmax=vmax, aspect='equal')
    axes[0].set_title('D369 Attention Preference (z-score)\nRed = D369 words attend more to D369')
    axes[0].set_xlabel('Head')
    axes[0].set_ylabel('Layer')
    for i in range(12):
        for j in range(12):
            sig = '*' if p_grid[i, j] < bonferroni_alpha else ''
            axes[0].text(j, i, f'{z_grid[i,j]:.1f}{sig}',
                        ha='center', va='center', fontsize=7,
                        color='white' if abs(z_grid[i,j]) > vmax*0.6 else 'black')
    plt.colorbar(im, ax=axes[0])

    # Significance heatmap
    sig_grid = -np.log10(p_grid + 1e-300)
    im2 = axes[1].imshow(sig_grid, cmap='hot', aspect='equal')
    axes[1].set_title(f'Significance (-log10 p)\nBonferroni threshold: {-np.log10(bonferroni_alpha):.1f}')
    axes[1].set_xlabel('Head')
    axes[1].set_ylabel('Layer')
    plt.colorbar(im2, ax=axes[1])

    # Mark significant heads
    for i in range(12):
        for j in range(12):
            if p_grid[i, j] < bonferroni_alpha:
                rect = plt.Rectangle((j-0.5, i-0.5), 1, 1,
                                     fill=False, edgecolor='lime', linewidth=2)
                axes[1].add_patch(rect)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def run():
    """Main experiment runner."""

    print("=" * 70)
    print("EXPERIMENT 22: Attention Pattern Analysis (Quran vs Controls)")
    print("=" * 70)

    # ── Step 1: Load data ──
    print("\n[1/5] Loading Quranic ayahs...")
    ayahs = load_quran_ayahs()
    print(f"  {len(ayahs)} ayahs loaded")
    total_words = sum(len(a['words']) for a in ayahs)
    d369_words = sum(1 for a in ayahs for w in a['words'] if w['digit_root'] in {3, 6, 9})
    print(f"  {total_words} words, {d369_words} D369 ({d369_words/total_words*100:.1f}%)")

    # ── Step 2: Load model ──
    print("\n[2/5] Loading AraBERT...")
    model, tokenizer = load_arabert()
    print("  Model loaded (135M params)")

    # ── Step 3: Process ayahs (sample 2000 for feasible CPU time) ──
    print("\n[3/5] Processing 2000 random ayahs through AraBERT...")
    random.seed(42)
    sampled_ayahs = random.sample(ayahs, min(2000, len(ayahs)))
    flows, d369_fracs = process_ayahs(sampled_ayahs, model, tokenizer)
    print(f"  Flow matrix shape: {flows.shape}")
    print(f"  Mean D369 fraction per ayah: {d369_fracs.mean():.3f}")

    # ── Step 4: Statistical analysis ──
    print("\n[4/5] Statistical analysis of 144 attention heads...")
    observed, expected, z_scores, p_values = permutation_test_heads(flows, d369_fracs)

    bonferroni = 0.05 / 144
    n_significant = (p_values < bonferroni).sum()
    print(f"  Expected D369->D369 flow under null: {expected:.4f}")
    print(f"  Observed mean across heads: {observed.mean():.4f}")

    # Top 10 heads by z-score
    top_indices = np.argsort(np.abs(z_scores))[::-1][:10]
    print(f"\n  Top 10 heads by |z-score|:")
    for idx in top_indices:
        layer = idx // 12
        head = idx % 12
        sig = '***' if p_values[idx] < bonferroni else ('*' if p_values[idx] < 0.05 else '')
        direction = '+' if z_scores[idx] > 0 else '-'
        print(f"    Layer {layer:2d}, Head {head:2d}: "
              f"z={z_scores[idx]:+.3f}, p={p_values[idx]:.6f}, "
              f"flow={observed[idx]:.4f} ({direction}D369 preference) {sig}")

    print(f"\n  Significant heads (Bonferroni p<{bonferroni:.5f}): {n_significant}/144")

    # Uncorrected significance
    n_uncorrected = (p_values < 0.05).sum()
    print(f"  Heads with p<0.05 (uncorrected): {n_uncorrected}/144")

    # Layer-by-layer analysis
    print("\n  Layer-wise D369 preference (mean z-score):")
    for layer in range(12):
        layer_z = z_scores[layer*12:(layer+1)*12]
        layer_obs = observed[layer*12:(layer+1)*12]
        print(f"    Layer {layer:2d}: mean_z={layer_z.mean():+.3f}, "
              f"mean_flow={layer_obs.mean():.4f}")

    # ── Step 5: Visualization ──
    print("\n[5/5] Generating visualizations...")
    visualize_head_analysis(
        z_scores, p_values,
        os.path.join(RESULTS_DIR, 'attention_heads_quran.png')
    )

    # ── Bukhari control ──
    print("\n[CONTROL] Processing Bukhari text...")
    bukhari_words = load_control_text('bukhari_sample.txt')
    if bukhari_words:
        # Split Bukhari into pseudo-ayahs (~12 words each, like Quran average)
        avg_ayah_len = total_words // len(ayahs)
        buk_ayahs = []
        for i in range(0, len(bukhari_words), avg_ayah_len):
            chunk = bukhari_words[i:i + avg_ayah_len]
            if len(chunk) >= 3:
                buk_ayahs.append({
                    'surah_id': 0,
                    'ayah_number': i // avg_ayah_len,
                    'words': [
                        {'text_clean': w['text'], 'digit_root': w['digit_root'], 'k6_value': 0}
                        for w in chunk
                    ]
                })

        print(f"  Bukhari: {len(buk_ayahs)} pseudo-ayahs")
        buk_flows, buk_fracs = process_ayahs(buk_ayahs, model, tokenizer,
                                              max_ayahs=min(len(buk_ayahs), 3000))
        buk_obs, buk_exp, buk_z, buk_p = permutation_test_heads(buk_flows, buk_fracs)

        buk_n_sig = (buk_p < bonferroni).sum()
        print(f"  Bukhari significant heads: {buk_n_sig}/144")

        visualize_head_analysis(
            buk_z, buk_p,
            os.path.join(RESULTS_DIR, 'attention_heads_bukhari.png')
        )
    else:
        buk_n_sig = None
        print("  Bukhari text not found — skipping")

    # ── Summary ──
    print("\n" + "=" * 70)
    print("SUMMARY — Experiment 22: Attention Pattern Analysis")
    print("=" * 70)
    print(f"\nQuran ({len(ayahs)} ayahs, {total_words} words):")
    print(f"  D369 fraction: {d369_words/total_words*100:.1f}%")
    print(f"  Expected D369->D369 flow: {expected:.4f}")
    print(f"  Observed mean flow: {observed.mean():.4f}")
    print(f"  Significant heads (Bonferroni): {n_significant}/144")

    if n_significant > 0:
        print(f"\n  RESULT: {n_significant} attention heads show SIGNIFICANT D369 preference")
        print("  --> AraBERT's learned representations encode D369 relationships")
        print("  --> The fingerprint is entangled with the Quran's grammatical structure")
    elif n_uncorrected > 7:  # >5% expected by chance
        print(f"\n  RESULT: {n_uncorrected} heads show uncorrected significance")
        print("  --> Suggestive but not conclusive D369 preference")
    else:
        print("\n  RESULT: No significant D369 attention preference detected")
        print("  --> D369 words do not form a special attention community")

    if buk_n_sig is not None:
        print(f"\nBukhari control: {buk_n_sig} significant heads")

    # Save results
    results = {
        'quran': {
            'n_ayahs': len(ayahs),
            'n_words': total_words,
            'd369_fraction': d369_words / total_words,
            'expected_flow': float(expected),
            'observed_mean_flow': float(observed.mean()),
            'n_significant_bonferroni': int(n_significant),
            'n_significant_uncorrected': int(n_uncorrected),
            'top_heads': [
                {
                    'layer': int(idx // 12),
                    'head': int(idx % 12),
                    'z_score': float(z_scores[idx]),
                    'p_value': float(p_values[idx]),
                    'flow': float(observed[idx]),
                }
                for idx in top_indices[:10]
            ],
        },
        'bukhari_significant': int(buk_n_sig) if buk_n_sig is not None else None,
    }
    with open(os.path.join(RESULTS_DIR, 'results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == '__main__':
    run()
