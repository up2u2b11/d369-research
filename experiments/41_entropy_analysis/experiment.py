"""
Experiment 41 — Entropy Analysis: Shannon H + KL Divergence + JSD
==================================================================
Date: May 15, 2026
Author: Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
Phase: Internal Research — NO PUBLICATION

THE QUESTION:
  Is the Quran's digit-root distribution closer to G14's stationary
  attractor pi_G14 than control texts?

MEASURES:
  1. Shannon entropy:    H = -sum pᵢ log2(pᵢ)        [0 .. log2(9)=3.17 bits]
  2. KL from uniform:   D_KL(P || U)                  [0 = perfectly uniform]
  3. JSD from pi_G14:   JSD(P || pi_G14)              [0 = identical to attractor]

G14 STATIONARY DISTRIBUTION pi_G14 (classical Markov, uniform start):
  Computed via power iteration of G14 transition matrix.
  Converges in 2 steps:
    pi_3 = 5/9 ~= 55.6%   (absorbs states 1,2,5,8)
    pi_4 = 1/9 ~= 11.1%   (in 4<->7 cycle)
    pi_6 = 1/9 ~= 11.1%   (fixed point)
    pi_7 = 1/9 ~= 11.1%   (in 4<->7 cycle)
    pi_9 = 1/9 ~= 11.1%   (fixed point)
    pi_1 = pi_2 = pi_5 = pi_8 = 0

  JSD is used (not raw KL) because pi_G14 has zero entries -> KL diverges.

SUCCESS CRITERION:
  JSD(Quran || pi_G14) < JSD(all controls || pi_G14), p < 0.05 (Mann-Whitney)
"""

import sqlite3
import json
import os
import sys
import math
import re
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))
from utils import digit_root, word_value, JUMMAL_5

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
DB_PATH   = os.path.join(DATA_DIR, 'd369_research.db')

BLOCK_SIZE = 50   # words per block for control texts
EPS        = 1e-12

G14_MAP = {1:5, 2:3, 3:3, 4:7, 5:3, 6:6, 7:4, 8:3, 9:9}


# ── G14 stationary distribution ──────────────────────────────────────────────

def compute_pi_g14(n_iter=100):
    """Power iteration of G14 Markov chain from uniform start."""
    v = [1/9] * 9
    for _ in range(n_iter):
        new_v = [0.0] * 9
        for j in range(1, 10):
            target = G14_MAP[j] - 1
            new_v[target] += v[j - 1]
        v = new_v
    return v   # index 0 = digit 1


PI_G14  = compute_pi_g14()
UNIFORM = [1/9] * 9


# ── Core entropy functions ────────────────────────────────────────────────────

def shannon_entropy(p):
    return -sum(pi * math.log2(pi) for pi in p if pi > EPS)


def kl_divergence(p, q):
    """D_KL(P||Q). Returns +inf if q[i]=0 and p[i]>0."""
    result = 0.0
    for pi, qi in zip(p, q):
        if pi < EPS:
            continue
        if qi < EPS:
            return float('inf')
        result += pi * math.log(pi / qi)
    return result


def jsd(p, q):
    """Jensen-Shannon Divergence (log base 2). Range [0, 1]. Handles zeros."""
    m   = [(pi + qi) / 2 for pi, qi in zip(p, q)]
    val = 0.0
    for pi, qi, mi in zip(p, q, m):
        if mi < EPS:
            continue
        if pi > EPS:
            val += pi * math.log2(pi / mi)
        if qi > EPS:
            val += qi * math.log2(qi / mi)
    return val / 2


def vec_from_roots(roots):
    if not roots:
        return None
    total  = len(roots)
    counts = Counter(roots)
    return [counts.get(k, 0) / total for k in range(1, 10)]


def all_metrics(p):
    H_max = math.log2(9)
    H     = shannon_entropy(p)
    return {
        'H':            round(H, 6),
        'H_norm':       round(H / H_max, 6),
        'kl_uniform':   round(kl_divergence(p, UNIFORM), 6),
        'jsd_pi_G14':   round(jsd(p, PI_G14), 6),
        'proj_369':     round(sum(p[i] for i in [2, 5, 8]), 6),
    }


# ── Data loaders ─────────────────────────────────────────────────────────────

def load_quran_per_surah():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT surah_id FROM words ORDER BY surah_id")
    surah_ids = [r[0] for r in cur.fetchall()]

    results = []
    for sid in surah_ids:
        cur.execute(
            "SELECT digit_root FROM words "
            "WHERE surah_id=? ORDER BY ayah_number, word_position",
            (sid,)
        )
        roots = [r[0] for r in cur.fetchall() if r[0] and r[0] > 0]
        if len(roots) < 10:
            continue
        p = vec_from_roots(roots)
        m = all_metrics(p)
        m['surah_id'] = sid
        m['n_words']  = len(roots)
        results.append(m)

    conn.close()
    return results


def load_quran_global():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT digit_root FROM words WHERE digit_root > 0")
    roots = [r[0] for r in cur.fetchall()]
    conn.close()
    return roots


def load_control_blocks(filepath, label):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"  WARNING: {label} file not found: {filepath}")
        return []

    words = re.findall(r'[؀-ۿ]+', text)
    if not words:
        return []

    blocks = []
    for i in range(0, len(words) - BLOCK_SIZE + 1, BLOCK_SIZE):
        chunk = words[i:i + BLOCK_SIZE]
        roots = []
        for w in chunk:
            try:
                val = word_value(w, JUMMAL_5)
                if val and val > 0:
                    dr = digit_root(val)
                    if dr and dr > 0:
                        roots.append(dr)
            except Exception:
                continue
        if len(roots) < 10:
            continue
        p = vec_from_roots(roots)
        m = all_metrics(p)
        m['source']      = label
        m['block_start'] = i
        m['n_words']     = len(roots)
        blocks.append(m)

    return blocks


# ── Statistical tests ─────────────────────────────────────────────────────────

def mann_whitney_u(a, b):
    """Mann-Whitney U (normal approximation). Returns U, z, p (two-tailed)."""
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return None, None, None

    combined = sorted([(v, i) for i, v in enumerate(a)] +
                      [(v, i + n1) for i, v in enumerate(b)])
    n = len(combined)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    rank_sum_a = sum(ranks[k] for k, (v, idx) in enumerate(combined) if idx < n1)
    U1 = rank_sum_a - n1 * (n1 + 1) / 2
    U2 = n1 * n2 - U1

    mu_U    = n1 * n2 / 2
    sigma_U = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sigma_U < EPS:
        return min(U1, U2), 0.0, 1.0

    z = (min(U1, U2) - mu_U) / sigma_U
    p = 2 * (1 - _norm_cdf(abs(z)))
    return round(min(U1, U2), 1), round(z, 4), round(p, 6)


def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def cliffs_delta(a, b):
    if not a or not b:
        return None
    count = sum(1 if ai > bj else (-1 if ai < bj else 0)
                for ai in a for bj in b)
    return round(count / (len(a) * len(b)), 4)


def describe(vals):
    if not vals:
        return {}
    n    = len(vals)
    mean = sum(vals) / n
    std  = math.sqrt(sum((v - mean)**2 for v in vals) / n)
    return {
        'n':    n,
        'mean': round(mean, 6),
        'std':  round(std, 6),
        'min':  round(min(vals), 6),
        'max':  round(max(vals), 6),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("Exp 41 — Entropy Analysis: Shannon H + KL + JSD from pi_G14")
    print("=" * 65)

    H_MAX = math.log2(9)

    # ── pi_G14 ────────────────────────────────────────────────────────────────
    print("\n[0] G14 Stationary Distribution pi_G14:")
    for i, p in enumerate(PI_G14):
        if p > EPS:
            print(f"  pi_{i+1} = {p:.6f}  ({p*100:.2f}%)")
    print(f"  JSD(pi_G14 || Uniform) = {jsd(PI_G14, UNIFORM):.4f}")

    # ── Whole Quran ───────────────────────────────────────────────────────────
    print("\n[1] Whole-Quran aggregate metrics...")
    all_roots    = load_quran_global()
    p_quran_agg  = vec_from_roots(all_roots)
    m_agg        = all_metrics(p_quran_agg)
    print(f"  Total words:     {len(all_roots)}")
    print(f"  H (Shannon):     {m_agg['H']:.4f} / {H_MAX:.4f} bits  (norm={m_agg['H_norm']:.4f})")
    print(f"  KL from uniform: {m_agg['kl_uniform']:.4f}")
    print(f"  JSD from pi_G14: {m_agg['jsd_pi_G14']:.4f}")
    print(f"  Proj on {{3,6,9}}: {m_agg['proj_369']:.4f}  ({m_agg['proj_369']*100:.2f}%)")
    print(f"  Dist vector:     {[round(x,4) for x in p_quran_agg]}")

    # ── Per-surah ─────────────────────────────────────────────────────────────
    print("\n[2] Per-surah metrics...")
    surahs = load_quran_per_surah()
    print(f"  Surahs loaded: {len(surahs)}")

    q_jsd  = [s['jsd_pi_G14'] for s in surahs]
    q_kl   = [s['kl_uniform']  for s in surahs]
    q_H    = [s['H']           for s in surahs]
    q_proj = [s['proj_369']    for s in surahs]

    print(f"\n  {'Metric':<22}  {'Mean':>8}  {'Std':>7}  {'Min':>7}  {'Max':>7}")
    for label, vals in [
        ('H (Shannon)',       q_H),
        ('KL from uniform',   q_kl),
        ('JSD from pi_G14',   q_jsd),
        ('Proj {3,6,9}',      q_proj),
    ]:
        d = describe(vals)
        print(f"  {label:<22}  {d['mean']:>8.4f}  {d['std']:>7.4f}  {d['min']:>7.4f}  {d['max']:>7.4f}")

    # Top 5 closest / farthest
    s_sorted = sorted(surahs, key=lambda x: x['jsd_pi_G14'])
    print(f"\n  Top 5 closest to pi_G14 (lowest JSD):")
    for s in s_sorted[:5]:
        print(f"    Surah {s['surah_id']:3d}: JSD={s['jsd_pi_G14']:.4f}  "
              f"H={s['H']:.3f}  proj={s['proj_369']:.3f}  n={s['n_words']}")
    print(f"\n  Top 5 farthest from pi_G14 (highest JSD):")
    for s in s_sorted[-5:]:
        print(f"    Surah {s['surah_id']:3d}: JSD={s['jsd_pi_G14']:.4f}  "
              f"H={s['H']:.3f}  proj={s['proj_369']:.3f}  n={s['n_words']}")

    # ── Control texts ─────────────────────────────────────────────────────────
    print("\n[3] Loading and processing control texts...")
    controls = {
        'Bukhari':   load_control_blocks(
                         os.path.join(DATA_DIR, 'bukhari_sample.txt'), 'Bukhari'),
        'Muallaqat': load_control_blocks(
                         os.path.join(DATA_DIR, 'muallaqat.txt'), 'Muallaqat'),
        'Futuhat':   load_control_blocks(
                         os.path.join(DATA_DIR, 'futuhat_v1.txt'), 'Futuhat'),
    }
    for label, blocks in controls.items():
        print(f"  {label}: {len(blocks)} blocks")

    # ── Comparison table ──────────────────────────────────────────────────────
    print("\n[4] Comparison table (per-surah for Quran, per-block for controls):")
    print(f"\n  {'Source':<12}  {'n':>5}  {'H mean':>8}  {'KL mean':>8}  "
          f"{'JSD mean':>9}  {'proj mean':>10}")

    all_data = {'Quran': {'jsd': q_jsd, 'kl': q_kl, 'H': q_H, 'proj': q_proj}}

    def _mean(lst): return sum(lst)/len(lst) if lst else float('nan')

    print(f"  {'Quran':<12}  {len(surahs):>5}  {_mean(q_H):>8.4f}  "
          f"{_mean(q_kl):>8.4f}  {_mean(q_jsd):>9.4f}  {_mean(q_proj):>10.4f}")

    for label, blocks in controls.items():
        if not blocks:
            continue
        c_jsd  = [b['jsd_pi_G14'] for b in blocks]
        c_kl   = [b['kl_uniform']  for b in blocks]
        c_H    = [b['H']           for b in blocks]
        c_proj = [b['proj_369']    for b in blocks]
        all_data[label] = {'jsd': c_jsd, 'kl': c_kl, 'H': c_H, 'proj': c_proj}
        print(f"  {label:<12}  {len(blocks):>5}  {_mean(c_H):>8.4f}  "
              f"{_mean(c_kl):>8.4f}  {_mean(c_jsd):>9.4f}  {_mean(c_proj):>10.4f}")

    # ── Statistical tests ─────────────────────────────────────────────────────
    print("\n[5] Statistical tests on JSD from pi_G14  (Quran vs each control):")
    print(f"  {'Comparison':<22}  {'U':>10}  {'z':>7}  {'p':>9}  {'Cliff d':>8}  sig")

    stat_results = {}
    for label in ['Bukhari', 'Muallaqat', 'Futuhat']:
        if label not in all_data:
            continue
        U, z, p   = mann_whitney_u(all_data['Quran']['jsd'], all_data[label]['jsd'])
        cd        = cliffs_delta(all_data['Quran']['jsd'], all_data[label]['jsd'])
        sig       = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'ns'))
        comp      = f"Quran vs {label}"
        print(f"  {comp:<22}  {str(U):>10}  {str(z):>7}  {str(p):>9}  {str(cd):>8}  {sig}")
        stat_results[label] = {
            'U': U, 'z': z, 'p': p, 'cliffs_d': cd, 'significant': sig != 'ns'
        }

    # Also test entropy H
    print(f"\n[6] Statistical tests on Shannon H (lower H = more concentrated):")
    print(f"  {'Comparison':<22}  {'z':>7}  {'p':>9}  {'Cliff d':>8}  sig")
    stat_H = {}
    for label in ['Bukhari', 'Muallaqat', 'Futuhat']:
        if label not in all_data:
            continue
        _, z, p = mann_whitney_u(all_data['Quran']['H'], all_data[label]['H'])
        cd      = cliffs_delta(all_data['Quran']['H'], all_data[label]['H'])
        sig     = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'ns'))
        print(f"  {'Quran vs ' + label:<22}  {str(z):>7}  {str(p):>9}  {str(cd):>8}  {sig}")
        stat_H[label] = {'z': z, 'p': p, 'cliffs_d': cd}

    # ── Verdict ───────────────────────────────────────────────────────────────
    q_mean_jsd = _mean(q_jsd)
    controls_beat = [
        label for label in ['Bukhari', 'Muallaqat', 'Futuhat']
        if label in all_data and q_mean_jsd < _mean(all_data[label]['jsd'])
    ]
    success = len(controls_beat) == len([l for l in ['Bukhari','Muallaqat','Futuhat']
                                         if l in all_data])

    print("\n" + "=" * 65)
    print("CONCLUSION:")
    print(f"  Quran mean JSD(pi_G14):  {q_mean_jsd:.4f}")
    for label in ['Bukhari', 'Muallaqat', 'Futuhat']:
        if label in all_data:
            print(f"  {label:<12} JSD(pi_G14): {_mean(all_data[label]['jsd']):.4f}")
    print(f"\n  Quran closer to G14 attractor than ALL controls: "
          f"{'YES — PASS' if success else 'PARTIAL/FAIL'}")
    print(f"  Controls beaten: {controls_beat}")
    print("=" * 65)

    # ── Save ──────────────────────────────────────────────────────────────────
    summary = {
        'experiment':           'Exp41_EntropyAnalysis',
        'date':                 '2026-05-15',
        'author':               'Emad Suleiman Alwan',
        'ORCID':                '0009-0004-5797-6140',
        'PI_G14':               [round(x, 8) for x in PI_G14],
        'PI_G14_jsd_uniform':   round(jsd(PI_G14, UNIFORM), 6),
        'whole_quran_metrics':  m_agg,
        'whole_quran_n_words':  len(all_roots),
        'quran_per_surah_stats': {
            'H':         describe(q_H),
            'kl_uniform': describe(q_kl),
            'jsd_pi_G14': describe(q_jsd),
            'proj_369':   describe(q_proj),
        },
        'top5_closest_pi_G14':  [
            {'surah': s['surah_id'], 'jsd': s['jsd_pi_G14'],
             'proj': s['proj_369'], 'n': s['n_words']}
            for s in s_sorted[:5]
        ],
        'top5_farthest_pi_G14': [
            {'surah': s['surah_id'], 'jsd': s['jsd_pi_G14'],
             'proj': s['proj_369'], 'n': s['n_words']}
            for s in s_sorted[-5:]
        ],
        'control_summary': {
            label: {
                'n_blocks':        len(all_data[label]['jsd']),
                'jsd_stats':       describe(all_data[label]['jsd']),
                'H_stats':         describe(all_data[label]['H']),
                'kl_stats':        describe(all_data[label]['kl']),
                'proj_stats':      describe(all_data[label]['proj']),
            }
            for label in ['Bukhari', 'Muallaqat', 'Futuhat']
            if label in all_data
        },
        'statistical_tests_jsd': stat_results,
        'statistical_tests_H':   stat_H,
        'verdict': {
            'success':          success,
            'controls_beaten':  controls_beat,
            'key_metric':       'JSD(P || pi_G14)',
            'interpretation': (
                'JSD from pi_G14 measures how far a text distribution is from '
                'the G14 Markov attractor. Lower JSD = more aligned with the '
                'absorbing structure {3,6,9}. '
                'If Quran < all controls => Quranic digit-root distribution '
                'is structurally closest to the G14 dynamical attractor.'
            )
        },
        'quran_per_surah_full':  surahs,
    }

    out_path = os.path.join(RESULTS_DIR, 'exp41_entropy.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved: {out_path}")
    return summary


if __name__ == '__main__':
    main()
