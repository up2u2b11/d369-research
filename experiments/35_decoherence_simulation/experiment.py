"""
Experiment 35 — Decoherence Simulation on the Quran
====================================================
Date: May 15, 2026
Author: Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
Phase: Internal Research — NO PUBLICATION

THE QUESTION:
  Does shuffling Quranic word order (increasing decoherence) reduce
  the projection onto {3,6,9}? Does it follow an exponential decay?

DECOHERENCE LEVELS:
  L0: original order (coherent)
  L1: 25% of words shuffled within each surah
  L2: 50% shuffled
  L3: 75% shuffled
  L4: 100% shuffled (fully decohered)

SUCCESS: Monotonic decrease L0->L4 with approximately exponential behavior.
"""

import sqlite3
import json
import os
import sys
import math
import random
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'd369_research.db')

random.seed(369)
N_TRIALS = 50  # trials per level per surah for averaging


def load_surah_words():
    """Load word-level DR data grouped by surah and ayah."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT surah_id, ayah_number, word_position, digit_root
        FROM words
        ORDER BY surah_id, ayah_number, word_position
    """)
    rows = cur.fetchall()
    conn.close()

    surahs = {}
    for surah_id, ayah_num, word_pos, dr in rows:
        if dr is None or dr == 0:
            continue
        if surah_id not in surahs:
            surahs[surah_id] = {'words': [], 'ayahs': {}}
        surahs[surah_id]['words'].append(dr)
        if ayah_num not in surahs[surah_id]['ayahs']:
            surahs[surah_id]['ayahs'][ayah_num] = []
        surahs[surah_id]['ayahs'][ayah_num].append(dr)

    return surahs


def compute_projection(roots):
    """Compute projection onto {3,6,9}: p3+p6+p9."""
    if not roots:
        return 0.0
    total = len(roots)
    counts = Counter(roots)
    return (counts.get(3, 0) + counts.get(6, 0) + counts.get(9, 0)) / total


def apply_decoherence(roots, level):
    """
    Apply decoherence by shuffling a fraction of words.
    level: 0.0=none, 0.25, 0.50, 0.75, 1.0=full shuffle
    Returns shuffled version of roots list.
    """
    if level == 0.0:
        return roots[:]
    if level >= 1.0:
        shuffled = roots[:]
        random.shuffle(shuffled)
        return shuffled

    result = roots[:]
    n = len(result)
    n_shuffle = int(n * level)
    if n_shuffle == 0:
        return result

    # Pick n_shuffle positions to shuffle
    positions = random.sample(range(n), n_shuffle)
    values = [result[i] for i in positions]
    random.shuffle(values)
    for i, pos in enumerate(positions):
        result[pos] = values[i]
    return result


def compute_decoherence_curve_for_surah(surah_words, n_trials=N_TRIALS):
    """
    For a single surah, compute mean projection at each decoherence level.
    """
    roots = surah_words['words']
    if len(roots) < 10:
        return None

    levels = [0.0, 0.25, 0.50, 0.75, 1.0]
    level_results = {}

    for level in levels:
        if level == 0.0:
            # Original — deterministic
            proj = compute_projection(roots)
            level_results[level] = {'mean': proj, 'std': 0.0, 'trials': [proj]}
        else:
            # Monte Carlo
            trial_projections = []
            for _ in range(n_trials):
                shuffled = apply_decoherence(roots, level)
                trial_projections.append(compute_projection(shuffled))
            mean = sum(trial_projections) / len(trial_projections)
            variance = sum((p - mean)**2 for p in trial_projections) / len(trial_projections)
            std = math.sqrt(variance)
            level_results[level] = {
                'mean': round(mean, 6),
                'std': round(std, 6),
                'trials': [round(p, 6) for p in trial_projections]
            }

    return level_results


def fit_exponential(x_vals, y_vals):
    """
    Fit y = A * exp(-x/tau) + C to decoherence curve.
    Simple approach: use log-linear fit on (y - y_inf).
    Returns A, tau, C, R^2.
    """
    if len(x_vals) < 3:
        return None

    y0 = y_vals[0]  # L0 value
    y_inf = y_vals[-1]  # L4 value (fully decohered)

    if abs(y0 - y_inf) < 1e-8:
        return {'A': 0, 'tau': float('inf'), 'C': y0, 'R2': 0.0, 'note': 'no decay'}

    # Normalize: z = (y - y_inf) / (y0 - y_inf)
    # Fit log(z) = -x/tau  =>  use linear regression on log(z) vs x
    z_vals = [(y - y_inf) / (y0 - y_inf) for y in y_vals]

    # Only use points where z > 0
    log_points = [(x, math.log(z)) for x, z in zip(x_vals, z_vals) if z > 1e-10]
    if len(log_points) < 2:
        return {'note': 'insufficient points for fit'}

    # Linear regression: log(z) = -x/tau
    n = len(log_points)
    sum_x  = sum(p[0] for p in log_points)
    sum_y  = sum(p[1] for p in log_points)
    sum_xy = sum(p[0]*p[1] for p in log_points)
    sum_x2 = sum(p[0]**2 for p in log_points)

    denom = n * sum_x2 - sum_x**2
    if abs(denom) < 1e-10:
        return {'note': 'degenerate fit'}

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    tau = -1.0 / slope if abs(slope) > 1e-10 else float('inf')
    A = (y0 - y_inf) * math.exp(intercept)

    # Compute R^2
    y_pred = [A * math.exp(-x / tau) + y_inf for x in x_vals]
    ss_res = sum((y - yp)**2 for y, yp in zip(y_vals, y_pred))
    y_mean = sum(y_vals) / len(y_vals)
    ss_tot = sum((y - y_mean)**2 for y in y_vals)
    r2 = 1 - ss_res / ss_tot if ss_tot > 1e-10 else 0.0

    return {
        'A': round(float(A), 6),
        'tau': round(float(tau), 4),
        'C': round(float(y_inf), 6),
        'R2': round(float(r2), 6),
        'slope': round(float(slope), 6)
    }


def main():
    print("=" * 65)
    print("Exp 35 — Decoherence Simulation on the Quran")
    print("=" * 65)

    print("\n[1] Loading surah word data...")
    surahs = load_surah_words()
    print(f"  Surahs loaded: {len(surahs)}")

    levels = [0.0, 0.25, 0.50, 0.75, 1.0]
    level_labels = ['L0', 'L1', 'L2', 'L3', 'L4']

    print(f"\n[2] Computing decoherence curves ({N_TRIALS} trials/level)...")
    surah_curves = {}
    all_level_projs = {l: [] for l in levels}

    for sid, data in sorted(surahs.items()):
        curve = compute_decoherence_curve_for_surah(data, N_TRIALS)
        if curve is None:
            continue
        surah_curves[sid] = curve
        for l in levels:
            if l in curve:
                all_level_projs[l].append(curve[l]['mean'])

    # Aggregate across all surahs
    mean_curve = {}
    for l in levels:
        vals = all_level_projs[l]
        if vals:
            mean = sum(vals) / len(vals)
            variance = sum((v - mean)**2 for v in vals) / len(vals)
            std = math.sqrt(variance)
            mean_curve[l] = {'mean': round(mean, 6), 'std': round(std, 6), 'n': len(vals)}

    print("\n[3] Decoherence curve (mean across all surahs):")
    print(f"  {'Level':6s} {'Decoherence':12s} {'Mean Proj':10s} {'Std':8s}")
    for l, label in zip(levels, level_labels):
        if l in mean_curve:
            mc = mean_curve[l]
            print(f"  {label:6s} {int(l*100):11d}%  {mc['mean']:.6f}  {mc['std']:.6f}")

    # Check monotonic decrease
    mean_values = [mean_curve[l]['mean'] for l in levels if l in mean_curve]
    is_monotone = all(mean_values[i] >= mean_values[i+1] for i in range(len(mean_values)-1))
    total_decay = mean_values[0] - mean_values[-1] if len(mean_values) >= 2 else 0
    pct_decay = 100 * total_decay / mean_values[0] if mean_values[0] > 0 else 0

    print(f"\n[4] Monotonic decrease L0->L4: {'YES' if is_monotone else 'NO'}")
    print(f"  Total decay: {total_decay:.6f}  ({pct_decay:.2f}%)")

    # Fit exponential to the mean curve
    print("\n[5] Exponential fit y = A*exp(-x/tau) + C:")
    x_vals = [l for l in levels if l in mean_curve]
    y_vals = [mean_curve[l]['mean'] for l in x_vals]
    exp_fit = fit_exponential(x_vals, y_vals)
    if exp_fit and 'tau' in exp_fit:
        print(f"  A   = {exp_fit.get('A', 'N/A')}")
        print(f"  tau = {exp_fit.get('tau', 'N/A')}")
        print(f"  C   = {exp_fit.get('C', 'N/A')}")
        print(f"  R^2 = {exp_fit.get('R2', 'N/A')}")
    else:
        print(f"  Fit result: {exp_fit}")

    # Verdict
    r2 = exp_fit.get('R2', 0) if exp_fit else 0
    success = is_monotone and pct_decay > 1.0

    print("\n" + "=" * 65)
    print("VERDICT:")
    print(f"  Monotonic decay:     {'YES' if is_monotone else 'NO'}")
    print(f"  Total decay:         {pct_decay:.2f}%")
    print(f"  Exponential R^2:     {r2:.4f}")
    print(f"  H4 (decoherence analogy): {'PASS' if success else 'FAIL'}")
    print("=" * 65)

    results = {
        'experiment': 'Exp35_DecoherenceSimulation',
        'date': '2026-05-15',
        'author': 'Emad Suleiman Alwan',
        'n_trials_per_level': N_TRIALS,
        'levels': levels,
        'level_labels': level_labels,
        'mean_curve': {str(l): v for l, v in mean_curve.items()},
        'is_monotone_decrease': is_monotone,
        'total_decay_absolute': round(total_decay, 6),
        'total_decay_percent': round(pct_decay, 4),
        'exponential_fit': exp_fit,
        'n_surahs_processed': len(surah_curves),
        'H4': {
            'pass': success,
            'description': 'Shuffling causes monotonic reduction in projection (decoherence analogy)'
        },
        'verdict': 'ACCEPT' if success else 'REJECT'
    }

    json_path = os.path.join(RESULTS_DIR, 'exp35_decoherence_curve.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved: {json_path}")
    return results


if __name__ == '__main__':
    main()
