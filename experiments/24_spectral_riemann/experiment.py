"""
Experiment 24 — Spectral Analysis of D369 Distribution (Riemann-Inspired)
==========================================================================
Question: Does the distribution of D369 surahs across the 114-surah
          sequence contain periodic structure (hidden harmonics)?

Methodology (inspired by Riemann's approach to primes):
  Riemann discovered that primes are not random — they contain hidden
  harmonics revealed by the zeta function / Fourier transform.

  We ask the same question about {3, 6, 9} digital root surahs:
  1. Build binary indicator: f(n) = 1 if surah n is D369, else 0
  2. Apply Discrete Fourier Transform (DFT) to find dominant frequencies
  3. Permutation test: is the spectral structure stronger than chance?
  4. Autocorrelation: do D369 surahs repeat at regular intervals?
  5. Cumulative density: compare to uniform distribution (pi(x) analogy)

Controls:
  - Bukhari hadith (split into 114 equal segments) — from Opus Web
  - 10,000 random sequences with same D369 proportion

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
"""

import sys
import os
import json
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from attention_utils import load_surah_sequences, load_control_text
from utils import JUMMAL_5, KHASS_6, digit_root, word_value

np.random.seed(369)  # Fixed seed per Opus Web directive

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# Opus Web baseline results (Bukhari split into 114 equal segments)
BUKHARI_BASELINE = {
    'd369_count': 41,
    'spectral_entropy': 0.8847,
    'max_power': 0.9725,
    'global_pvalue': 0.6320,
    'ks_pvalue': 0.901,
}

RANDOM_BASELINE = {
    'entropy_mean': 0.896,
    'max_power_mean_35': 1.014,
    'max_power_95pct_35': 1.4825,
    'max_power_99pct_35': 1.9181,
}


# ──────────────────────────────────────────────────────────────
# Step 1: Data Extraction
# ──────────────────────────────────────────────────────────────

def extract_surah_sequences():
    """
    Extract D369 binary sequences for both encoding systems.
    Uses load_surah_sequences() from shared utilities.
    """
    sequences = load_surah_sequences()

    roots_abjad = [s['surah_total_dr'] for s in sequences]
    roots_k6 = [s['surah_total_k6_dr'] for s in sequences]
    binary_abjad = [1 if s['is_d369_abjad'] else 0 for s in sequences]
    binary_k6 = [1 if s['is_d369_k6'] else 0 for s in sequences]

    return roots_abjad, roots_k6, binary_abjad, binary_k6, sequences


def extract_bukhari_sequence():
    """
    Split Bukhari into 114 equal segments and compute D369 for each.
    Matches Opus Web methodology for comparable baselines.
    """
    buk_words = load_control_text('bukhari_sample.txt')
    if not buk_words:
        return None

    n_words = len(buk_words)
    segment_size = n_words // 114
    binary = []

    for i in range(114):
        start = i * segment_size
        end = start + segment_size if i < 113 else n_words
        segment = buk_words[start:end]
        total = sum(word_value(w['text'], JUMMAL_5) for w in segment)
        dr = digit_root(total)
        binary.append(1 if dr in {3, 6, 9} else 0)

    return binary


# ──────────────────────────────────────────────────────────────
# Step 2: Spectral Analysis (FFT)
# ──────────────────────────────────────────────────────────────

def compute_psd(binary_sequence):
    """Compute Power Spectral Density via FFT."""
    signal = np.array(binary_sequence, dtype=float)
    signal = signal - np.mean(signal)  # Center (remove DC)
    fft_vals = np.fft.rfft(signal)
    n = len(binary_sequence)
    psd = np.abs(fft_vals) ** 2 / n
    freqs = np.fft.rfftfreq(n)
    return freqs, psd


def spectral_entropy(psd):
    """
    Spectral entropy — measures energy concentration.
    Low entropy = concentrated energy (periodic structure)
    High entropy = uniform distribution (random)
    """
    psd_nondc = psd[1:]  # exclude DC component
    total = np.sum(psd_nondc)
    if total == 0:
        return 0.0, 0.0, 0.0
    psd_norm = psd_nondc / total
    psd_norm = psd_norm[psd_norm > 0]
    entropy = -np.sum(psd_norm * np.log2(psd_norm))
    max_entropy = np.log2(len(psd) - 1)
    return float(entropy), float(max_entropy), float(entropy / max_entropy)


# ──────────────────────────────────────────────────────────────
# Step 3: Permutation Spectral Test
# ──────────────────────────────────────────────────────────────

def permutation_spectral_test(binary_seq, n_perms=10000):
    """
    Test: is the spectral structure stronger than chance?
    Preserve D369 count, shuffle positions.
    """
    n = len(binary_seq)
    n_ones = sum(binary_seq)
    freqs, observed_psd = compute_psd(binary_seq)
    observed_max = np.max(observed_psd[1:])
    obs_ent = spectral_entropy(observed_psd)[2]

    n_freqs = len(freqs)
    perm_max_powers = []
    perm_powers = np.zeros((n_perms, n_freqs))
    perm_entropies = []

    for i in range(n_perms):
        perm = np.zeros(n, dtype=int)
        perm[np.random.choice(n, n_ones, replace=False)] = 1
        _, perm_psd = compute_psd(perm)
        perm_powers[i] = perm_psd
        perm_max_powers.append(np.max(perm_psd[1:]))
        perm_entropies.append(spectral_entropy(perm_psd)[2])

        if (i + 1) % 2000 == 0:
            print(f"    Permutation {i+1}/{n_perms}")

    # Global p-value (max power)
    global_pvalue = float(np.mean(np.array(perm_max_powers) >= observed_max))

    # Per-frequency p-values
    freq_pvalues = np.zeros(n_freqs)
    for j in range(n_freqs):
        freq_pvalues[j] = np.mean(perm_powers[:, j] >= observed_psd[j])

    # Entropy p-value (one-sided: is observed entropy LOWER than random?)
    entropy_pvalue = float(np.mean(np.array(perm_entropies) <= obs_ent))

    # Percentiles
    perm_95 = np.percentile(perm_powers, 95, axis=0)
    perm_99 = np.percentile(perm_powers, 99, axis=0)

    return {
        'global_pvalue': global_pvalue,
        'freq_pvalues': freq_pvalues.tolist(),
        'observed_psd': observed_psd.tolist(),
        'observed_max_power': float(observed_max),
        'perm_95': perm_95.tolist(),
        'perm_99': perm_99.tolist(),
        'entropy_pvalue': entropy_pvalue,
        'observed_entropy': obs_ent,
        'freqs': freqs.tolist(),
        'perm_max_mean': float(np.mean(perm_max_powers)),
        'perm_max_std': float(np.std(perm_max_powers)),
    }


# ──────────────────────────────────────────────────────────────
# Step 4: Autocorrelation
# ──────────────────────────────────────────────────────────────

def compute_autocorrelation(binary_seq, max_lag=57):
    """
    Do D369 surahs repeat at regular intervals?
    E.g., every 3 surahs? every 7? every 19?
    """
    signal = np.array(binary_seq, dtype=float) - np.mean(binary_seq)
    n = len(signal)
    results = []
    for lag in range(1, min(max_lag + 1, n)):
        c = float(np.corrcoef(signal[:n - lag], signal[lag:])[0, 1])
        results.append({'lag': lag, 'correlation': c})
    return results


# ──────────────────────────────────────────────────────────────
# Step 5: Cumulative Density — pi(x) analogy
# ──────────────────────────────────────────────────────────────

def cumulative_analysis(binary_seq, n_d369):
    """Compare cumulative D369 count vs expected uniform distribution."""
    n = len(binary_seq)
    deviations = []
    cumulative = []
    for i in range(1, n + 1):
        observed = sum(binary_seq[:i])
        expected = i * (n_d369 / n)
        deviations.append(float(observed - expected))
        cumulative.append(observed)

    # KS test for uniformity of D369 positions
    d369_positions = np.array([i / n for i, b in enumerate(binary_seq) if b == 1])
    ks_stat, ks_pval = stats.kstest(d369_positions, 'uniform')

    max_dev = max(deviations, key=abs)
    max_dev_idx = deviations.index(max_dev) + 1

    return {
        'deviations': deviations,
        'cumulative': cumulative,
        'ks_statistic': float(ks_stat),
        'ks_pvalue': float(ks_pval),
        'max_deviation': float(max_dev),
        'max_deviation_surah': max_dev_idx,
    }


# ──────────────────────────────────────────────────────────────
# Step 6: Visualization
# ──────────────────────────────────────────────────────────────

def plot_all(freqs_a, psd_a, test_a, ac_a, cum_a, n_d369_a,
             freqs_k, psd_k, test_k, ac_k, cum_k, n_d369_k,
             filepath_prefix):
    """Generate 4 publication-quality figures."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # Style: academic, clean
    plt.rcParams.update({
        'font.size': 11, 'axes.titlesize': 13, 'axes.labelsize': 11,
        'figure.facecolor': 'white', 'axes.grid': True,
        'grid.alpha': 0.3, 'grid.linestyle': '--',
    })

    # ── Figure 1: Power Spectral Density ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, freqs, psd, test, name, n_d in [
        (axes[0], freqs_a, psd_a, test_a, 'Abjad', n_d369_a),
        (axes[1], freqs_k, psd_k, test_k, 'Special-6', n_d369_k),
    ]:
        ax.bar(freqs[1:], psd[1:], width=0.005, color='#2c3e50', alpha=0.8, label='Observed')
        ax.plot(freqs[1:], test['perm_95'][1:], 'r--', linewidth=1, label='95th percentile (null)')
        ax.plot(freqs[1:], test['perm_99'][1:], 'r-', linewidth=1, label='99th percentile (null)')
        ax.set_xlabel('Frequency (cycles per surah)')
        ax.set_ylabel('Power')
        ax.set_title(f'Power Spectral Density — {name} ({n_d}/114 D369)\n'
                     f'Global p={test["global_pvalue"]:.4f}')
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{filepath_prefix}_psd.png', dpi=150, bbox_inches='tight')
    plt.close()

    # ── Figure 2: Autocorrelation ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    threshold = 2.0 / np.sqrt(114)

    for ax, ac, name in [(axes[0], ac_a, 'Abjad'), (axes[1], ac_k, 'Special-6')]:
        lags = [a['lag'] for a in ac]
        corrs = [a['correlation'] for a in ac]
        colors = ['#e74c3c' if abs(c) > threshold else '#95a5a6' for c in corrs]
        ax.bar(lags, corrs, color=colors, alpha=0.7)
        ax.axhline(y=threshold, color='#e74c3c', linestyle='--', linewidth=0.8,
                   label=f'Significance: |r| > {threshold:.3f}')
        ax.axhline(y=-threshold, color='#e74c3c', linestyle='--', linewidth=0.8)
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.set_xlabel('Lag (surahs)')
        ax.set_ylabel('Autocorrelation')
        ax.set_title(f'Autocorrelation — {name}')
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{filepath_prefix}_autocorrelation.png', dpi=150, bbox_inches='tight')
    plt.close()

    # ── Figure 3: Cumulative Density (pi(x) analogy) ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, cum, name, n_d in [
        (axes[0], cum_a, 'Abjad', n_d369_a),
        (axes[1], cum_k, 'Special-6', n_d369_k),
    ]:
        x = range(1, 115)
        expected = [i * (n_d / 114) for i in x]
        ax.plot(x, cum['cumulative'], 'b-', linewidth=2, label='Observed D369 count')
        ax.plot(x, expected, 'r--', linewidth=1.5, label='Expected (uniform)')
        ax.fill_between(x, cum['cumulative'], expected, alpha=0.15, color='blue')
        ax.set_xlabel('Surah number')
        ax.set_ylabel('Cumulative D369 count')
        ax.set_title(f'Cumulative Distribution — {name}\n'
                     f'KS p={cum["ks_pvalue"]:.4f}, max dev={cum["max_deviation"]:+.2f} '
                     f'at surah {cum["max_deviation_surah"]}')
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{filepath_prefix}_cumulative.png', dpi=150, bbox_inches='tight')
    plt.close()

    # ── Figure 4: Comparison summary ──
    fig, ax = plt.subplots(figsize=(10, 6))

    categories = ['Spectral\nEntropy', 'Max\nPower', 'Global\np-value']
    quran_a = [test_a['observed_entropy'], test_a['observed_max_power'], test_a['global_pvalue']]
    quran_k = [test_k['observed_entropy'], test_k['observed_max_power'], test_k['global_pvalue']]
    bukhari = [BUKHARI_BASELINE['spectral_entropy'], BUKHARI_BASELINE['max_power'],
               BUKHARI_BASELINE['global_pvalue']]
    random_vals = [RANDOM_BASELINE['entropy_mean'], RANDOM_BASELINE['max_power_mean_35'], 0.5]

    x_pos = np.arange(len(categories))
    width = 0.2

    ax.bar(x_pos - 1.5 * width, quran_a, width, label='Quran (Abjad)', color='#2c3e50', alpha=0.85)
    ax.bar(x_pos - 0.5 * width, quran_k, width, label='Quran (K6)', color='#2980b9', alpha=0.85)
    ax.bar(x_pos + 0.5 * width, bukhari, width, label='Bukhari', color='#95a5a6', alpha=0.85)
    ax.bar(x_pos + 1.5 * width, random_vals, width, label='Random', color='#bdc3c7', alpha=0.85)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories)
    ax.set_ylabel('Value')
    ax.set_title('Spectral Fingerprint Comparison')
    ax.legend()
    ax.axhline(y=0.05, color='red', linestyle=':', linewidth=0.8, alpha=0.5)
    ax.annotate('p=0.05', xy=(2.4, 0.06), fontsize=8, color='red')

    plt.tight_layout()
    plt.savefig(f'{filepath_prefix}_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  Saved 4 figures: {filepath_prefix}_*.png")


# ──────────────────────────────────────────────────────────────
# Main Runner
# ──────────────────────────────────────────────────────────────

def run():
    """Main experiment runner."""

    print("=" * 70)
    print("EXPERIMENT 24: Spectral Analysis — Riemann-Inspired")
    print("=" * 70)

    # ── Step 1: Extract data ──
    print("\n[1/6] Extracting surah digital root sequences...")
    roots_a, roots_k, bin_a, bin_k, sequences = extract_surah_sequences()

    n_d369_a = sum(bin_a)
    n_d369_k = sum(bin_k)

    # Compute total Abjad from database
    import sqlite3
    db_path = os.environ.get("D369_DB", "/home/emad/d369-quran-fingerprint/data/d369_research.db")
    conn = sqlite3.connect(db_path)
    total_abjad = conn.execute("SELECT SUM(jummal_value) FROM words").fetchone()[0]
    conn.close()

    # Assertions
    assert n_d369_a == 35, f"ERROR: D369 Abjad = {n_d369_a}, expected 35"
    assert n_d369_k == 51, f"ERROR: D369 K6 = {n_d369_k}, expected 51"
    assert total_abjad == 23476120, f"ERROR: Total Abjad = {total_abjad}, expected 23476120"

    print(f"  D369 Abjad: {n_d369_a}/114")
    print(f"  D369 K6:    {n_d369_k}/114")
    print(f"  Total Abjad: {total_abjad:,}")
    print(f"  All assertions passed")

    print(f"\n  Abjad roots: {roots_a}")
    print(f"  K6 roots:    {roots_k}")

    # ── Step 2: Spectral Analysis ──
    print("\n[2/6] Computing Power Spectral Density...")
    freqs_a, psd_a = compute_psd(bin_a)
    freqs_k, psd_k = compute_psd(bin_k)

    ent_a, max_ent_a, norm_ent_a = spectral_entropy(psd_a)
    ent_k, max_ent_k, norm_ent_k = spectral_entropy(psd_k)

    print(f"  Quran Abjad  — spectral entropy: {norm_ent_a:.4f}")
    print(f"  Quran K6     — spectral entropy: {norm_ent_k:.4f}")
    print(f"  Bukhari      — spectral entropy: {BUKHARI_BASELINE['spectral_entropy']}")
    print(f"  Random       — spectral entropy: ~{RANDOM_BASELINE['entropy_mean']}")

    # Top-5 frequencies
    print("\n  Top-5 Dominant Frequencies (Abjad):")
    indices_a = np.argsort(psd_a[1:])[::-1][:5] + 1
    for rank, idx in enumerate(indices_a):
        period = 1.0 / freqs_a[idx] if freqs_a[idx] > 0 else float('inf')
        print(f"    #{rank+1}: freq={freqs_a[idx]:.4f}, "
              f"period={period:.1f} surahs, power={psd_a[idx]:.4f}")

    print("\n  Top-5 Dominant Frequencies (K6):")
    indices_k = np.argsort(psd_k[1:])[::-1][:5] + 1
    for rank, idx in enumerate(indices_k):
        period = 1.0 / freqs_k[idx] if freqs_k[idx] > 0 else float('inf')
        print(f"    #{rank+1}: freq={freqs_k[idx]:.4f}, "
              f"period={period:.1f} surahs, power={psd_k[idx]:.4f}")

    # ── Step 3: Permutation test ──
    print("\n[3/6] Permutation spectral test (10,000 permutations)...")
    print("  Testing Abjad...")
    test_a = permutation_spectral_test(bin_a)
    n_tests = len(test_a['freq_pvalues']) - 1
    sig_005_a = int(np.sum(np.array(test_a['freq_pvalues'][1:]) < 0.05))
    sig_bonf_a = int(np.sum(np.array(test_a['freq_pvalues'][1:]) < 0.05 / n_tests))

    print(f"  Abjad — Global p-value: {test_a['global_pvalue']:.4f}")
    print(f"           Max power: {test_a['observed_max_power']:.4f}")
    print(f"           Entropy p-value: {test_a['entropy_pvalue']:.4f}")
    print(f"           Sig freqs (p<0.05): {sig_005_a}")
    print(f"           Sig freqs (Bonferroni): {sig_bonf_a}")

    print("\n  Testing Special-6...")
    test_k = permutation_spectral_test(bin_k)
    sig_005_k = int(np.sum(np.array(test_k['freq_pvalues'][1:]) < 0.05))
    sig_bonf_k = int(np.sum(np.array(test_k['freq_pvalues'][1:]) < 0.05 / n_tests))

    print(f"  K6 — Global p-value: {test_k['global_pvalue']:.4f}")
    print(f"        Max power: {test_k['observed_max_power']:.4f}")
    print(f"        Entropy p-value: {test_k['entropy_pvalue']:.4f}")
    print(f"        Sig freqs (p<0.05): {sig_005_k}")
    print(f"        Sig freqs (Bonferroni): {sig_bonf_k}")

    # ── Step 4: Autocorrelation ──
    print("\n[4/6] Autocorrelation analysis...")
    threshold = 2.0 / np.sqrt(114)

    ac_a = compute_autocorrelation(bin_a)
    sig_lags_a = [a for a in ac_a if abs(a['correlation']) > threshold]
    print(f"  Abjad — Significant lags (|r| > {threshold:.3f}): {len(sig_lags_a)}")
    for a in sig_lags_a:
        mark = ' <-- notable!' if abs(a['correlation']) > 0.25 else ''
        print(f"    lag={a['lag']:>3}, r={a['correlation']:+.4f}{mark}")

    ac_k = compute_autocorrelation(bin_k)
    sig_lags_k = [a for a in ac_k if abs(a['correlation']) > threshold]
    print(f"\n  K6 — Significant lags: {len(sig_lags_k)}")
    for a in sig_lags_k:
        mark = ' <-- notable!' if abs(a['correlation']) > 0.25 else ''
        print(f"    lag={a['lag']:>3}, r={a['correlation']:+.4f}{mark}")

    # ── Step 5: Cumulative density ──
    print("\n[5/6] Cumulative density analysis (pi(x) analogy)...")

    cum_a = cumulative_analysis(bin_a, n_d369_a)
    print(f"  Abjad — KS: D={cum_a['ks_statistic']:.4f}, p={cum_a['ks_pvalue']:.4f}")
    print(f"           Max deviation: {cum_a['max_deviation']:+.2f} at surah {cum_a['max_deviation_surah']}")
    if cum_a['ks_pvalue'] > 0.05:
        print(f"           -> Uniform distribution (no periodicity)")
    else:
        print(f"           -> NON-UNIFORM distribution (structure detected!)")

    cum_k = cumulative_analysis(bin_k, n_d369_k)
    print(f"  K6 — KS: D={cum_k['ks_statistic']:.4f}, p={cum_k['ks_pvalue']:.4f}")
    print(f"        Max deviation: {cum_k['max_deviation']:+.2f} at surah {cum_k['max_deviation_surah']}")
    if cum_k['ks_pvalue'] > 0.05:
        print(f"        -> Uniform distribution (no periodicity)")
    else:
        print(f"        -> NON-UNIFORM distribution (structure detected!)")

    # ── Step 6: Visualization + Save ──
    print("\n[6/6] Generating figures and saving results...")
    plot_all(
        np.array(freqs_a), np.array(psd_a), test_a, ac_a, cum_a, n_d369_a,
        np.array(freqs_k), np.array(psd_k), test_k, ac_k, cum_k, n_d369_k,
        os.path.join(RESULTS_DIR, 'exp24')
    )

    # ── Summary ──
    print("\n" + "=" * 70)
    print("EXPERIMENT 24 — COMPLETE SUMMARY")
    print("=" * 70)
    print(f"""
  Metric              Quran(Abjad)  Quran(K6)  Bukhari  Random
  ─────────────────   ───────────   ────────   ───────  ──────
  D369 proportion     {n_d369_a}/114        {n_d369_k}/114       41/114   varies
  Spectral entropy    {norm_ent_a:.4f}        {norm_ent_k:.4f}       0.8847   ~0.896
  Max power           {test_a['observed_max_power']:.4f}        {test_k['observed_max_power']:.4f}       0.9725   ~1.014
  Global p-value      {test_a['global_pvalue']:.4f}        {test_k['global_pvalue']:.4f}       0.6320   —
  Sig freqs (p<.05)   {sig_005_a}            {sig_005_k}           2        —
  Sig freqs (Bonf)    {sig_bonf_a}            {sig_bonf_k}           0        —
  Sig autocorr lags   {len(sig_lags_a)}            {len(sig_lags_k)}           7        —
  KS p-value          {cum_a['ks_pvalue']:.4f}        {cum_k['ks_pvalue']:.4f}       0.9010   —
""")

    # Interpretation
    for name, test, n_d in [("Abjad", test_a, n_d369_a), ("K6", test_k, n_d369_k)]:
        p = test['global_pvalue']
        if p < 0.01:
            print(f"  {name}: STRONG periodic structure detected (p={p:.4f})")
            print(f"         -> New dimension of the fingerprint!")
        elif p < 0.05:
            print(f"  {name}: Suggestive periodic structure (p={p:.4f})")
            print(f"         -> Needs confirmation with additional tests")
        else:
            print(f"  {name}: No significant periodicity (p={p:.4f})")
            print(f"         -> D369 distribution is consistent with random placement")
            print(f"         -> The fingerprint is in the PROPORTION, not the ARRANGEMENT")

    # Save JSON
    results = {
        'experiment': 24,
        'title': 'Spectral Analysis — Riemann-Inspired',
        'date': '2026-04-06',
        'seed': 369,
        'quran_abjad': {
            'digital_roots': roots_a,
            'binary_sequence': bin_a,
            'd369_count': n_d369_a,
            'total_abjad': total_abjad,
            'spectral_entropy': norm_ent_a,
            'max_power': test_a['observed_max_power'],
            'global_pvalue': test_a['global_pvalue'],
            'entropy_pvalue': test_a['entropy_pvalue'],
            'sig_freqs_005': sig_005_a,
            'sig_freqs_bonf': sig_bonf_a,
            'sig_autocorr_lags': len(sig_lags_a),
            'autocorr_details': sig_lags_a,
            'ks_statistic': cum_a['ks_statistic'],
            'ks_pvalue': cum_a['ks_pvalue'],
            'max_deviation': cum_a['max_deviation'],
            'max_deviation_surah': cum_a['max_deviation_surah'],
        },
        'quran_k6': {
            'digital_roots': roots_k,
            'binary_sequence': bin_k,
            'd369_count': n_d369_k,
            'spectral_entropy': norm_ent_k,
            'max_power': test_k['observed_max_power'],
            'global_pvalue': test_k['global_pvalue'],
            'entropy_pvalue': test_k['entropy_pvalue'],
            'sig_freqs_005': sig_005_k,
            'sig_freqs_bonf': sig_bonf_k,
            'sig_autocorr_lags': len(sig_lags_k),
            'autocorr_details': sig_lags_k,
            'ks_statistic': cum_k['ks_statistic'],
            'ks_pvalue': cum_k['ks_pvalue'],
            'max_deviation': cum_k['max_deviation'],
            'max_deviation_surah': cum_k['max_deviation_surah'],
        },
        'bukhari_baseline': BUKHARI_BASELINE,
        'random_baseline': RANDOM_BASELINE,
    }
    with open(os.path.join(RESULTS_DIR, 'results.json'), 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {RESULTS_DIR}/")
    print("Send results.json to Opus Web for final analysis.")


if __name__ == '__main__':
    run()
