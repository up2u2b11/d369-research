#!/usr/bin/env python3
"""
Experiment 13 — The Tenth Gate: Verse-Count Fingerprint
========================================================
Question: Does the Quran carry a {3,6,9} fingerprint when using ONLY
          the number of verses per Surah — with NO encoding system at all?

Logic:
  Experiments 1-12 used letter-value systems (Abjad, Special-6, Gematria).
  A critic could argue: "The fingerprint is an artifact of the encoding."
  This experiment eliminates that objection entirely:
  - Input: ayah_count per Surah (a plain integer, no encoding)
  - Method: identical G14 transformation map methodology
  - If significant → a "third system" independent of ALL letter encodings

Three batteries:
  A — 114 Surahs by ayah count (primary test)
  B — Meccan vs Medinan split (66 + 28 = 94... wait, 86+28=114)
  C — Revelation-order grouping (early/middle/late thirds)

Control:
  Torah — 54 Parashot by verse count (same methodology)

Monte Carlo: 100,000 permutations, seed=369

Intellectual property: Emad Suleiman Alwan — UP2U2B LLC — March 21, 2026
"""

import json
import sqlite3
import sys
import os
from pathlib import Path
from collections import defaultdict
import random
from datetime import datetime, timezone, timedelta

# ── Paths ──
DB_PATH = "/root/d369/d369.db"
TORAH_FILE = "/root/d369/data/torah_hebrew.jsonl"
PARASHOT_FILE = "/root/d369/data/parashot_boundaries.json"
RESULTS_DIR = Path(__file__).parent


def digit_root(n):
    """Digital root — repeated digit sum until single digit."""
    n = abs(n)
    if n == 0:
        return 0
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def build_transformation_map(values):
    """Build G14-style transformation map from a list of values."""
    groups = defaultdict(list)
    for val in values:
        dr = digit_root(val)
        groups[dr].append(val)

    transformation = {}
    group_sums = {}
    group_counts = {}

    for dr in range(1, 10):
        members = groups[dr]
        group_counts[dr] = len(members)
        if members:
            s = sum(members)
            group_sums[dr] = s
            transformation[dr] = digit_root(s)
        else:
            group_sums[dr] = 0
            transformation[dr] = 0

    return transformation, group_sums, group_counts


def analyze_map(transformation):
    """Analyze transformation map for patterns."""
    self_preserving = [dr for dr in range(1, 10)
                       if transformation.get(dr, 0) == dr]

    tesla_targets = {transformation.get(t, 0) for t in [3, 6, 9]}
    tesla_preserves = tesla_targets == {3, 6, 9}

    # Cycles
    cycles = []
    visited_global = set()
    for start in range(1, 10):
        if start in visited_global or transformation.get(start, 0) == 0:
            continue
        path, visited, current = [], set(), start
        while current not in visited and current != 0:
            visited.add(current)
            path.append(current)
            current = transformation.get(current, 0)
        if current in visited and current != 0:
            idx = path.index(current)
            cycle = path[idx:]
            if len(cycle) > 1:
                cycles.append(tuple(cycle))
            visited_global.update(cycle)

    # Attractors
    sink_counts = defaultdict(int)
    for dr in range(1, 10):
        t = transformation.get(dr, 0)
        if t != 0:
            sink_counts[t] += 1
    sinks = [(t, c) for t, c in sink_counts.items() if c >= 3]

    return {
        'self_preserving': self_preserving,
        'tesla_preserves': tesla_preserves,
        'cycles': cycles,
        'sinks': sinks,
    }


def monte_carlo(values, n_perm=100_000, seed=369):
    """Monte Carlo permutation test."""
    random.seed(seed)

    real_trans, _, _ = build_transformation_map(values)
    real_analysis = analyze_map(real_trans)
    real_self = len(real_analysis['self_preserving'])
    real_tesla = real_analysis['tesla_preserves']

    count_self_ge = 0
    count_tesla = 0
    dist = defaultdict(int)

    for _ in range(n_perm):
        groups = defaultdict(list)
        for val in values:
            groups[random.randint(1, 9)].append(val)

        perm_trans = {}
        for dr in range(1, 10):
            m = groups[dr]
            perm_trans[dr] = digit_root(sum(m)) if m else 0

        ps = sum(1 for dr in range(1, 10) if perm_trans.get(dr, 0) == dr)
        dist[ps] += 1
        if ps >= real_self and real_self > 0:
            count_self_ge += 1
        if all(perm_trans.get(t, 0) == t for t in [3, 6, 9]):
            count_tesla += 1

    return {
        'real_self_count': real_self,
        'real_self_preserving': real_analysis['self_preserving'],
        'real_tesla': real_tesla,
        'p_self': count_self_ge / n_perm if real_self > 0 else 1.0,
        'p_tesla': count_tesla / n_perm,
        'distribution': dict(dist),
        'n': n_perm,
    }


def run_battery(name, values, labels):
    """Run a complete battery."""
    n = len(values)
    print(f"\n{'='*70}")
    print(f"  Battery {name} — {n} units")
    print(f"{'='*70}")

    trans, sums, counts = build_transformation_map(values)
    analysis = analyze_map(trans)

    print(f"\n  Transformation Map:")
    print(f"  {'Root':>6} -> {'Result':>6} | {'Count':>5} | {'Sum':>10} | Status")
    print(f"  {'-'*55}")
    for dr in range(1, 10):
        t = trans.get(dr, 0)
        c = counts.get(dr, 0)
        s = sums.get(dr, 0)
        mark = "SELF-PRESERVING" if t == dr else ""
        print(f"  {dr:>6} -> {t:>6} | {c:>5} | {s:>10,} | {mark}")

    print(f"\n  Patterns:")
    print(f"    Self-preserving: {analysis['self_preserving'] or 'NONE'}")
    print(f"    Tesla {{3,6,9}}: {'YES' if analysis['tesla_preserves'] else 'NO'}")
    print(f"    Cycles: {analysis['cycles'] or 'NONE'}")
    print(f"    Attractors: {analysis['sinks'] or 'NONE'}")

    print(f"\n  Monte Carlo (100,000 permutations)...")
    mc = monte_carlo(values)
    print(f"    Observed self-preserving: {mc['real_self_count']}")
    print(f"    p-value (self-preserving): {mc['p_self']:.5f}")
    print(f"    p-value (Tesla): {mc['p_tesla']:.5f}")
    print(f"    Null distribution:")
    for k in sorted(mc['distribution'].keys()):
        pct = mc['distribution'][k] / mc['n'] * 100
        print(f"      {k}: {mc['distribution'][k]:>7,} ({pct:.2f}%)")

    return {
        'name': name, 'n': n, 'values': values, 'labels': labels,
        'transformation': trans, 'sums': sums, 'counts': counts,
        'analysis': analysis, 'mc': mc,
    }


def load_torah_verse_counts():
    """Load Torah verse counts per Parashah."""
    with open(TORAH_FILE, 'r') as f:
        verses = [json.loads(line) for line in f]
    with open(PARASHOT_FILE, 'r') as f:
        parashot = json.load(f)

    boundaries = [(p[0], p[1], p[2], p[3]) for p in parashot]
    pcounts = defaultdict(int)

    for v in verses:
        vb, vc, vv = v['book'], v['chapter'], v['verse']
        assigned = None
        for i in range(len(boundaries) - 1, -1, -1):
            pn, pb, pc, pv = boundaries[i]
            if (vb > pb or (vb == pb and vc > pc) or
                (vb == pb and vc == pc and vv >= pv)):
                assigned = i
                break
        if assigned is not None:
            pcounts[assigned] += 1

    names = [b[0] for b in boundaries]
    values = [pcounts[i] for i in range(len(boundaries))]
    return names, values


def main():
    KSA = timezone(timedelta(hours=3))
    now = datetime.now(KSA).strftime("%Y-%m-%d %H:%M KSA")

    print("=" * 70)
    print("  Experiment 13 — The Tenth Gate: Verse-Count Fingerprint")
    print(f"  Date: {now}")
    print("  IP: Emad Suleiman Alwan — UP2U2B LLC")
    print("=" * 70)

    # ── Load Quran data ──
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT surah_id, name_ar, ayah_count, revelation_type FROM surahs ORDER BY surah_id")
    surahs = cur.fetchall()
    conn.close()

    # ── Battery A: 114 Surahs by ayah count ──
    values_a = [s[2] for s in surahs]
    labels_a = [s[1] for s in surahs]

    # Show DR distribution
    dr_dist = defaultdict(list)
    for s in surahs:
        dr = digit_root(s[2])
        dr_dist[dr].append((s[0], s[1], s[2]))

    print("\n  Digital root distribution of ayah counts:")
    for dr in range(1, 10):
        members = dr_dist[dr]
        print(f"    DR={dr}: {len(members)} surahs")
        if dr in (3, 6, 9):
            ratio_369 = sum(len(dr_dist[d]) for d in [3, 6, 9])

    total_369 = sum(len(dr_dist[d]) for d in [3, 6, 9])
    pct_369 = total_369 / 114 * 100
    print(f"\n  {{3,6,9}} count: {total_369}/114 = {pct_369:.1f}%")

    battery_a = run_battery("A — 114 Surahs (ayah count)", values_a, labels_a)

    # ── Battery B: Meccan vs Medinan ──
    meccan = [(s[1], s[2]) for s in surahs if s[3] and 'مك' in s[3]]
    medinan = [(s[1], s[2]) for s in surahs if s[3] and 'مدن' in s[3]]

    if meccan:
        battery_b1 = run_battery(f"B1 — Meccan ({len(meccan)} surahs)",
                                 [m[1] for m in meccan],
                                 [m[0] for m in meccan])
    if medinan:
        battery_b2 = run_battery(f"B2 — Medinan ({len(medinan)} surahs)",
                                 [m[1] for m in medinan],
                                 [m[0] for m in medinan])

    # ── Battery C: Torah control (verse counts per Parashah) ──
    torah_names, torah_values = load_torah_verse_counts()
    battery_c = run_battery("C — Torah Control (54 Parashot verse counts)",
                            torah_values, torah_names)

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  SUMMARY — Experiment 13")
    print("=" * 70)

    results = [battery_a]
    if meccan:
        results.append(battery_b1)
    if medinan:
        results.append(battery_b2)
    results.append(battery_c)

    print(f"\n  {'Battery':<45} | {'Self-P':>6} | {'Tesla':>5} | {'p(self)':>8} | {'p(Tesla)':>8}")
    print(f"  {'-'*85}")
    for r in results:
        sp = r['analysis']['self_preserving']
        tesla = 'YES' if r['analysis']['tesla_preserves'] else 'NO'
        print(f"  {r['name']:<45} | {str(sp):>6} | {tesla:>5} | {r['mc']['p_self']:>8.5f} | {r['mc']['p_tesla']:>8.5f}")

    # ── Comparison table ──
    print(f"\n  CROSS-SYSTEM COMPARISON:")
    print(f"  {'System':<30} | {'Tesla':>5} | {'p-value':>8} | {'Layers':>6}")
    print(f"  {'-'*60}")
    print(f"  {'Abjad (letter values)':<30} | {'YES':>5} | {'<0.00001':>8} | {'4':>6}")
    print(f"  {'Special-6 (letter values)':<30} | {'  9 ':>5} | {'0.007':>8} | {'1':>6}")
    sp_a = battery_a['analysis']['self_preserving']
    tesla_a = 'YES' if battery_a['analysis']['tesla_preserves'] else 'NO'
    p_a = battery_a['mc']['p_self']
    print(f"  {'Verse count (NO encoding)':<30} | {tesla_a:>5} | {p_a:>8.5f} | {'?':>6}")
    sp_c = battery_c['analysis']['self_preserving']
    tesla_c = 'YES' if battery_c['analysis']['tesla_preserves'] else 'NO'
    p_c = battery_c['mc']['p_self']
    print(f"  {'Torah verse count (control)':<30} | {tesla_c:>5} | {p_c:>8.5f} | {'?':>6}")

    # ── Conclusion ──
    print(f"\n  CONCLUSION:")
    if battery_a['analysis']['tesla_preserves']:
        print("  The Quran carries the {3,6,9} fingerprint even in VERSE COUNTS —")
        print("  a third independent system with NO encoding dependency.")
        print("  This eliminates the 'encoding artifact' objection entirely.")
    elif len(battery_a['analysis']['self_preserving']) > 0 and battery_a['mc']['p_self'] < 0.05:
        print(f"  Self-preserving roots {sp_a} are statistically significant (p={p_a:.5f})")
        print("  but the Tesla triad {3,6,9} does not fully preserve.")
        print("  Partial structure exists in verse counts.")
    else:
        print("  Verse counts do NOT carry a significant transformation structure.")
        print("  The fingerprint requires letter-value encoding to manifest.")
        if not battery_c['analysis']['tesla_preserves']:
            print("  Torah also fails — confirming this is encoding-dependent.")

    print("\n" + "=" * 70)

    # ── Save results ──
    report_lines = []
    for r in results:
        report_lines.append(f"\n## Battery {r['name']}")
        report_lines.append(f"Units: {r['n']}")
        report_lines.append(f"Self-preserving: {r['analysis']['self_preserving']}")
        report_lines.append(f"Tesla: {r['analysis']['tesla_preserves']}")
        report_lines.append(f"p(self): {r['mc']['p_self']:.5f}")
        report_lines.append(f"p(Tesla): {r['mc']['p_tesla']:.5f}")
        report_lines.append("Transformation:")
        for dr in range(1, 10):
            t = r['transformation'].get(dr, 0)
            report_lines.append(f"  {dr} -> {t} (n={r['counts'].get(dr,0)}, sum={r['sums'].get(dr,0)})")

    with open(RESULTS_DIR / "results.md", 'w') as f:
        f.write(f"# Experiment 13 — Verse-Count Fingerprint\n")
        f.write(f"Date: {now}\n")
        f.write(f"IP: Emad Suleiman Alwan — UP2U2B LLC\n\n")
        f.write("\n".join(report_lines))

    # Raw JSON
    raw = {}
    for r in results:
        key = r['name'].split(' — ')[0].replace(' ', '_').lower()
        raw[key] = {
            'values': r['values'], 'labels': r['labels'],
            'transformation': r['transformation'],
            'sums': r['sums'], 'counts': r['counts'],
            'self_preserving': r['analysis']['self_preserving'],
            'tesla': r['analysis']['tesla_preserves'],
            'p_self': r['mc']['p_self'], 'p_tesla': r['mc']['p_tesla'],
        }
    with open(RESULTS_DIR / "raw_data.json", 'w') as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    print(f"\nResults: {RESULTS_DIR / 'results.md'}")
    print(f"Raw data: {RESULTS_DIR / 'raw_data.json'}")


if __name__ == "__main__":
    main()
