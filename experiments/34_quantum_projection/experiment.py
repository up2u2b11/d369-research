"""
Experiment 34 — Quantum Projection for All Texts
=================================================
Date: May 15, 2026
Author: Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
Phase: Internal Research — NO PUBLICATION

THE QUESTION:
  Does the Quran show a statistically higher projection onto the
  {3,6,9} eigenspace compared to all control texts?

METHOD:
  For each text block, compute DR distribution -> probability vector |Psi|^2
  Projection = p3 + p6 + p9
  Compare Quran vs Bukhari, Muallaqat, Futuhat via Mann-Whitney U + Cliff delta

SUCCESS: Quran projection significantly higher (p < 0.001) than all controls.
"""

import sqlite3
import json
import os
import sys
import re
import math
import random
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))
from utils import digit_root, word_value, JUMMAL_5

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'd369_research.db')

random.seed(369)


# ─── Quran: surah-level projections from DB ───────────────────────────────────

def get_quran_projections():
    """Compute projection p3+p6+p9 for each of the 114 surahs."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    projections = []
    surah_details = []

    cur.execute("SELECT DISTINCT surah_id FROM words ORDER BY surah_id")
    surah_ids = [r[0] for r in cur.fetchall()]

    for sid in surah_ids:
        cur.execute("SELECT digit_root FROM words WHERE surah_id=?", (sid,))
        roots = [r[0] for r in cur.fetchall() if r[0] is not None and r[0] > 0]
        if not roots:
            continue
        total = len(roots)
        counts = Counter(roots)
        proj = (counts.get(3, 0) + counts.get(6, 0) + counts.get(9, 0)) / total
        projections.append(proj)
        surah_details.append({
            'surah_id': sid,
            'n_words': total,
            'projection_369': round(proj, 6),
            'dr_distribution': {str(k): counts.get(k, 0) / total for k in range(1, 10)}
        })

    conn.close()
    return projections, surah_details


# ─── Control texts: block-level projections ──────────────────────────────────

def arabic_word_to_dr(word):
    """Compute digit root of a word using Jummal."""
    val = word_value(word, JUMMAL_5)
    return digit_root(val) if val > 0 else None


def get_text_projections(filepath, block_size=50):
    """
    Split a text file into blocks of ~block_size words,
    compute projection for each block.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        return [], f"File not found: {filepath}"

    # Tokenize Arabic words (keep Arabic letters only)
    words = re.findall(r'[؀-ۿ]+', text)
    if not words:
        return [], "No Arabic words found"

    projections = []
    blocks = [words[i:i+block_size] for i in range(0, len(words), block_size)]

    for block in blocks:
        if len(block) < 10:  # skip tiny blocks
            continue
        roots = [arabic_word_to_dr(w) for w in block]
        roots = [r for r in roots if r is not None and r > 0]
        if not roots:
            continue
        total = len(roots)
        counts = Counter(roots)
        proj = (counts.get(3, 0) + counts.get(6, 0) + counts.get(9, 0)) / total
        projections.append(proj)

    return projections, None


# ─── Statistical tests ────────────────────────────────────────────────────────

def mann_whitney_u(x, y):
    """
    Mann-Whitney U test (two-sided).
    Returns U, p-value (normal approximation for large samples).
    """
    nx, ny = len(x), len(y)
    if nx == 0 or ny == 0:
        return None, None

    # Compute U
    combined = [(val, 0) for val in x] + [(val, 1) for val in y]
    combined.sort(key=lambda t: t[0])

    # Assign ranks (with ties handled as midpoints)
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) - 1 and combined[j+1][0] == combined[j][0]:
            j += 1
        avg_rank = (i + j + 2) / 2.0  # 1-indexed
        for k in range(i, j+1):
            ranks[k] = avg_rank
        i = j + 1

    rank_sum_x = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == 0)
    U_x = rank_sum_x - nx * (nx + 1) / 2.0
    U_y = nx * ny - U_x

    U = min(U_x, U_y)

    # Normal approximation
    mean_U = nx * ny / 2.0
    std_U = math.sqrt(nx * ny * (nx + ny + 1) / 12.0)
    if std_U == 0:
        return U, 1.0
    z = (U - mean_U) / std_U
    # p-value two-sided (approximation)
    p = 2.0 * (1.0 - _normal_cdf(abs(z)))
    return float(U), float(p)


def _normal_cdf(x):
    """Standard normal CDF approximation."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def cliffs_delta(x, y):
    """
    Cliff's delta effect size: proportion of (xi > yj) minus (xi < yj)
    Range: [-1, 1]. |d| > 0.474 = large, > 0.33 = medium, > 0.147 = small.
    """
    if not x or not y:
        return None
    count_greater = sum(1 for xi in x for yj in y if xi > yj)
    count_less    = sum(1 for xi in x for yj in y if xi < yj)
    d = (count_greater - count_less) / (len(x) * len(y))
    return round(float(d), 6)


def describe(values):
    if not values:
        return {}
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(variance)
    sorted_v = sorted(values)
    median = sorted_v[n // 2] if n % 2 == 1 else (sorted_v[n//2-1] + sorted_v[n//2]) / 2
    return {
        'n': n,
        'mean': round(mean, 6),
        'std': round(std, 6),
        'median': round(median, 6),
        'min': round(min(values), 6),
        'max': round(max(values), 6)
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("Exp 34 — Quantum Projection onto {3,6,9} Eigenspace")
    print("=" * 65)

    # ── Quran ────────────────────────────────────────────────────────────────
    print("\n[1] Computing Quran projections (114 surahs)...")
    quran_proj, quran_details = get_quran_projections()
    print(f"  Surahs processed: {len(quran_proj)}")
    quran_stats = describe(quran_proj)
    print(f"  Mean projection: {quran_stats['mean']:.4f}  std: {quran_stats['std']:.4f}")

    # ── Control texts ────────────────────────────────────────────────────────
    controls = {
        'bukhari':    os.path.join(DATA_DIR, 'bukhari_sample.txt'),
        'muallaqat':  os.path.join(DATA_DIR, 'muallaqat.txt'),
        'futuhat':    os.path.join(DATA_DIR, 'futuhat_v1.txt'),
    }

    control_results = {}
    print("\n[2] Computing control text projections...")
    for name, path in controls.items():
        projs, err = get_text_projections(path, block_size=50)
        if err:
            print(f"  {name}: ERROR — {err}")
            control_results[name] = {'error': err}
            continue
        stats = describe(projs)
        print(f"  {name}: n={stats['n']}  mean={stats['mean']:.4f}  std={stats['std']:.4f}")
        control_results[name] = {'projections': projs, 'stats': stats}

    # ── Statistical comparisons ──────────────────────────────────────────────
    print("\n[3] Statistical comparisons (Mann-Whitney U + Cliff's delta):")
    comparisons = {}
    for name, data in control_results.items():
        if 'error' in data:
            comparisons[name] = {'error': data['error']}
            continue
        ctrl_proj = data['projections']
        U, p = mann_whitney_u(quran_proj, ctrl_proj)
        d = cliffs_delta(quran_proj, ctrl_proj)

        # Effect size label
        if d is None:
            effect = 'N/A'
        elif abs(d) > 0.474:
            effect = 'LARGE'
        elif abs(d) > 0.33:
            effect = 'MEDIUM'
        elif abs(d) > 0.147:
            effect = 'SMALL'
        else:
            effect = 'NEGLIGIBLE'

        sig = 'p<0.001' if (p is not None and p < 0.001) else \
              'p<0.01'  if (p is not None and p < 0.01)  else \
              'p<0.05'  if (p is not None and p < 0.05)  else 'n.s.'

        print(f"  Quran vs {name:12s}: U={U:.0f}  p={p:.4e}  Cliff_d={d:+.4f}  "
              f"effect={effect}  {sig}")
        comparisons[name] = {
            'U': U, 'p_value': p, 'cliffs_delta': d,
            'effect_size': effect, 'significance': sig,
            'quran_mean': quran_stats['mean'],
            'control_mean': data['stats']['mean'],
            'quran_higher': bool(quran_stats['mean'] > data['stats']['mean'])
        }

    # ── Overall verdict ───────────────────────────────────────────────────────
    all_sig = all(
        c.get('p_value', 1.0) < 0.001 and c.get('quran_higher', False)
        for c in comparisons.values() if 'error' not in c
    )
    print(f"\n[4] H3 (Quran projection highest, p<0.001 vs all): "
          f"{'PASS' if all_sig else 'PARTIAL/FAIL'}")

    print("\n" + "=" * 65)
    print("PROJECTION SUMMARY:")
    print(f"  Quran mean: {quran_stats['mean']:.4f}")
    for name, c in comparisons.items():
        if 'error' not in c:
            print(f"  {name:12s}: {c.get('control_mean', 'N/A'):.4f}  "
                  f"(Quran higher: {c.get('quran_higher', 'N/A')}  {c.get('significance', 'N/A')})")
    print("=" * 65)

    # ── Save ──────────────────────────────────────────────────────────────────
    results = {
        'experiment': 'Exp34_QuantumProjection',
        'date': '2026-05-15',
        'author': 'Emad Suleiman Alwan',
        'quran': {
            'projections': quran_proj,
            'stats': quran_stats,
            'surah_details': quran_details
        },
        'controls': {
            name: {
                'stats': data.get('stats', {}),
                'n_blocks': len(data.get('projections', []))
            }
            for name, data in control_results.items()
        },
        'comparisons': comparisons,
        'H3': {
            'pass': all_sig,
            'description': 'Quran projection onto {3,6,9} is significantly higher than all controls'
        },
        'verdict': 'ACCEPT' if all_sig else 'PARTIAL'
    }

    # Save full CSV-style data
    csv_path = os.path.join(RESULTS_DIR, 'exp34_projections.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('text,block_id,projection_369\n')
        for i, p in enumerate(quran_proj):
            f.write(f'quran,{i+1},{p:.6f}\n')
        for name, data in control_results.items():
            if 'projections' in data:
                for i, p in enumerate(data['projections']):
                    f.write(f'{name},{i+1},{p:.6f}\n')

    json_path = os.path.join(RESULTS_DIR, 'exp34_projections.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nCSV saved:  {csv_path}")
    print(f"JSON saved: {json_path}")
    return results


if __name__ == '__main__':
    main()
