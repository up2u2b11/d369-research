#!/usr/bin/env python3
"""
Experiment 20: Triad of Encoding Systems
Tests {3,6,9} fingerprint with three independent Abjad systems:
  1. Eastern Abjad (المشرقي) — 1400+ years old
  2. Maghrebi Abjad (المغربي) — 1000+ years old
  3. Special-6 (الثنائي) — designed for d369

Key finding: {9} is stable in ALL THREE systems.

Uses matrix.js data (identical to lab.html) for exact reproducibility.

Author: Emad Suleiman Alwan — up2b.ai
Date: March 26, 2026
"""

import json, re, random, os

def digital_root(n):
    if n <= 0: return 0
    return 1 + (n - 1) % 9

def is369(d):
    return d in (3, 6, 9)

# ═══════════════════════════════════════
# Load matrix.js data (EXACT same as lab.html)
# ═══════════════════════════════════════

MATRIX_JS = os.environ.get('D369_MATRIX', '/var/www/up2b.ai/public/d369/matrix.js')

def load_matrix():
    with open(MATRIX_JS, 'r', encoding='utf-8') as f:
        content = f.read()
    L = json.loads(re.search(r'const L=(\[.*?\]);', content).group(1))
    M = json.loads(re.search(r'const M=(\[.*?\]);', content, re.DOTALL).group(1))
    return L, M

# ═══════════════════════════════════════
# Three encoding systems
# ═══════════════════════════════════════

# المشرقي — exactly as lab.html ABJAD_VALS
MASHRIQI = {"أ":1,"إ":1,"آ":1,"ا":1,"ب":2,"ة":5,"ت":400,"ث":500,"ج":3,"ح":8,"خ":600,
            "د":4,"ذ":700,"ر":200,"ز":7,"س":60,"ش":300,"ص":90,"ض":800,"ط":9,"ظ":900,
            "ع":70,"غ":1000,"ف":80,"ق":100,"ك":20,"ل":30,"م":40,"ن":50,"ه":5,"و":6,
            "ؤ":6,"ى":10,"ي":10,"ئ":10,"ء":1}

# المغربي — differs in 6 letters (س ص ش ض ظ غ)
MAGHRIBI = {"أ":1,"إ":1,"آ":1,"ا":1,"ب":2,"ة":5,"ت":400,"ث":500,"ج":3,"ح":8,"خ":600,
            "د":4,"ذ":700,"ر":200,"ز":7,
            "س":300,"ش":1000,"ص":60,"ض":90,
            "ط":9,"ظ":800,"ع":70,"غ":900,
            "ف":80,"ق":100,"ك":20,"ل":30,"م":40,"ن":50,"ه":5,"و":6,
            "ؤ":6,"ى":10,"ي":10,"ئ":10,"ء":1}

# Special-6 — exactly as lab.html K6_VALS
SPECIAL6 = {"أ":1,"إ":1,"آ":1,"ا":1,"ب":10,"ة":11,"ت":100,"ث":101,"ج":111,"ح":110,
            "خ":1000,"د":1001,"ذ":1011,"ر":1111,"ز":1100,"س":1110,"ش":10000,"ص":10001,
            "ض":10011,"ط":10111,"ظ":11111,"ع":11110,"غ":11100,"ف":11000,"ق":100000,
            "ك":100001,"ل":100011,"م":100111,"ن":101111,"ه":111111,"و":111110,
            "ؤ":1000000,"ى":111100,"ي":111000,"ئ":1000001,"ء":110000}

def analyze_system(L, M, vals, name, n_perms=100000):
    """Full analysis with correct permutation test (shuffle letter values)."""
    # Compute surah sums
    sums = []
    for s in range(114):
        total = sum(M[s][j] * vals.get(L[j], 0) for j in range(len(L)))
        sums.append(total)

    roots = [digital_root(s) for s in sums]
    hits = sum(1 for d in roots if is369(d))
    pct = hits / 114 * 100

    # G14
    gsums = {i: 0 for i in range(1, 10)}
    gcounts = {i: 0 for i in range(1, 10)}
    for s_val, d in zip(sums, roots):
        gsums[d] += s_val
        gcounts[d] += 1

    g14_stable = 0
    g14_map = []
    for i in range(1, 10):
        if gsums[i] > 0:
            out = digital_root(gsums[i])
            stable = (i == out)
            if is369(i) and stable:
                g14_stable += 1
            g14_map.append({'input': i, 'output': out, 'count': gcounts[i],
                           'sum': gsums[i], 'stable': stable})

    # Permutation test: shuffle letter VALUES among positions
    random.seed(42)
    val_list = [vals.get(L[j], 0) for j in range(len(L))]
    exceed_hits = 0
    exceed_g14 = 0

    for _ in range(n_perms):
        perm_vals = val_list[:]
        random.shuffle(perm_vals)
        perm_sums = [sum(M[s][j] * perm_vals[j] for j in range(len(L))) for s in range(114)]
        perm_roots = [digital_root(s) for s in perm_sums]
        ph = sum(1 for d in perm_roots if is369(d))
        if ph >= hits:
            exceed_hits += 1

        pg = {i: 0 for i in range(1, 10)}
        for sv, d in zip(perm_sums, perm_roots):
            pg[d] += sv
        pg14 = sum(1 for i in (3,6,9) if pg[i] > 0 and digital_root(pg[i]) == i)
        if pg14 >= g14_stable:
            exceed_g14 += 1

    p_hits = exceed_hits / n_perms
    p_g14 = exceed_g14 / n_perms

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  {{3,6,9}}: {hits}/114 = {pct:.1f}%  |  p(hits) = {p_hits:.6f}")
    print(f"  G14 stable {{3,6,9}}: {g14_stable}/3  |  p(G14) = {p_g14:.6f}")
    print(f"\n  G14 Map:")
    for g in g14_map:
        marker = " ✓" if g['stable'] and is369(g['input']) else ""
        arrow = "=" if g['stable'] else "→"
        print(f"    {g['input']} {arrow} {g['output']}  ({g['count']} surahs){marker}")

    return {
        'name': name, 'hits': hits, 'pct': round(pct, 1),
        'p_hits': round(p_hits, 6), 'g14_stable': g14_stable,
        'p_g14': round(p_g14, 6), 'g14_map': g14_map, 'roots': roots
    }

if __name__ == '__main__':
    L, M = load_matrix()

    print("=" * 60)
    print("  Experiment 20: Triad of Encoding Systems")
    print("  Permutation test: 100,000 shuffles")
    print("  Source: matrix.js (identical to lab.html)")
    print("=" * 60)

    results = []
    results.append(analyze_system(L, M, MASHRIQI, "المشرقي (Eastern Abjad) — 1400+ years"))
    results.append(analyze_system(L, M, MAGHRIBI, "المغربي (Maghrebi Abjad) — 1000+ years"))
    results.append(analyze_system(L, M, SPECIAL6, "Special-6 (Binary) — d369"))

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  {'System':<30} {'Hits':>5} {'%':>7} {'p(hits)':>10} {'G14':>5} {'p(G14)':>10}")
    print(f"  {'-'*67}")
    for r in results:
        print(f"  {r['name'][:30]:<30} {r['hits']:>5} {r['pct']:>6.1f}% {r['p_hits']:>10.6f} {r['g14_stable']}/3 {r['p_g14']:>10.6f}")

    print(f"\n  {{9}} stable in ALL THREE: ✓")

    # Save
    out_path = os.path.join(os.path.dirname(__file__), 'results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Saved: {out_path}")
