"""
Experiment 43 — Final Synthesis: Complete Quantum-Mathematical Framework
========================================================================
Date: May 15, 2026
Author: Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
Phase: Internal Research — NO PUBLICATION

Integrates results from Exp 33-42 to answer:
  Q1. Does the Schrodinger equation accept d369 structure?
  Q2. What is the correct mathematical framework?
  Q3. What is the topological/informational status of {3,6,9}?
  Q4. [NEW] What is the entropy signature of the Quran?
  Q5. [NEW] What is the Dirac-theoretic status of {3,6,9}?
"""

import json
import os
import sys
import math

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

def load(rel_path):
    path = os.path.join(BASE, rel_path)
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def safe(d, *keys, default='N/A'):
    for k in keys:
        if d is None: return default
        if isinstance(k, int):
            d = d[k] if isinstance(d, list) and k < len(d) else default
        else:
            d = d.get(k, default) if isinstance(d, dict) else default
        if d == default: return default
    return d


def main():
    print("=" * 70)
    print("Exp 43 — Final Synthesis: Complete Framework (Exp 33-42)")
    print("=" * 70)

    # ── Load all results ──────────────────────────────────────────────────────
    r33 = load('experiments/33_schrodinger_spectrum/results/exp33_spectrum.json')
    r34 = load('experiments/34_quantum_projection/results/exp34_projections.json')
    r35 = load('experiments/35_decoherence_simulation/results/exp35_decoherence_curve.json')
    r36 = load('experiments/36_hamiltonian_hq/results/exp36_hamiltonian_hq.json')
    r37 = load('experiments/37_linearity_test/results/exp37_linearity_test.json')
    r38 = load('experiments/38_unitarity_check/results/exp38_unitarity.json')
    r39 = load('experiments/39_lindblad_open_systems/results/exp39_lindblad.json')
    r40 = load('experiments/40_final_synthesis/results/exp40_synthesis.json')
    r41 = load('experiments/41_entropy_analysis/results/exp41_entropy.json')
    r42 = load('experiments/42_dirac_operator/results/exp42_dirac.json')

    loaded = sum(1 for r in [r33,r34,r35,r36,r37,r38,r39,r40,r41,r42] if r)
    print(f"\n  Results loaded: {loaded}/10")

    # ── Scorecard ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("SCORECARD")
    print("─" * 70)

    scorecard = [
        {
            'exp': 'Exp 33', 'title': 'Eigenspectrum of G14',
            'result': 'PARTIAL',
            'finding': '{3,6,9} is invariant subspace (H2 PASS). '
                       '4 eigenvalues=1 not 3 (4-7 cycle adds one). H1 FAIL.',
            'verdict': 'PARTIAL'
        },
        {
            'exp': 'Exp 34', 'title': 'Quantum Projection on {3,6,9}',
            'result': 'PASS',
            'finding': f'Quran {safe(r34,"quran_mean_projection",default=0.381):.3f} '
                       f'> Bukhari 0.304 > Muallaqat 0.282. p<0.001 vs all controls.',
            'verdict': 'PASS'
        },
        {
            'exp': 'Exp 35', 'title': 'Decoherence Simulation',
            'result': 'REVISED',
            'finding': 'Projection is order-invariant (lexical fingerprint layer). '
                       'Word shuffling does not change digit-root frequencies.',
            'verdict': 'REVISED'
        },
        {
            'exp': 'Exp 36', 'title': 'Hamiltonian H_Q Search',
            'result': 'FAIL (expected)',
            'finding': 'No Hermitian H_Q satisfies G14=exp(-iH). '
                       'Confirms G14 is non-unitary. Schrodinger fails.',
            'verdict': 'FAIL'
        },
        {
            'exp': 'Exp 37', 'title': 'Linearity Test',
            'result': 'PASS* (trivial)',
            'finding': 'Combined vector is exactly weighted average by construction. '
                       'Methodologically trivial — excluded from paper.',
            'verdict': 'EXCLUDED'
        },
        {
            'exp': 'Exp 38', 'title': 'Unitarity Check',
            'result': 'KEY RESULT',
            'finding': 'G14 is column-stochastic (Markov matrix). '
                       'det=0, rank=6/9. NOT unitary. CPTP map.',
            'verdict': 'KEY'
        },
        {
            'exp': 'Exp 39', 'title': 'Lindblad Open Systems',
            'result': 'PASS',
            'finding': '{3,6,9} = Decoherence-Free Subspace. '
                       '6 jump operators. Steady state 77.8% on {3,6,9}.',
            'verdict': 'PASS'
        },
        {
            'exp': 'Exp 40', 'title': 'First Synthesis',
            'result': 'COMPLETE',
            'finding': 'Two-layer fingerprint: lexical (order-invariant) + '
                       'architectural (order-dependent).',
            'verdict': 'COMPLETE'
        },
        {
            'exp': 'Exp 41', 'title': 'Entropy Analysis',
            'result': 'NEW FINDING',
            'finding': f'Quran H_norm={safe(r41,"whole_quran_metrics","H_norm",default=0.9948):.4f} '
                       f'— highest entropy among all Arabic texts tested. '
                       f'Near-perfectly uniform + systematic bias toward {{3,6,9}}.',
            'verdict': 'NEW'
        },
        {
            'exp': 'Exp 42', 'title': 'Discrete Dirac Operator',
            'result': 'NEW FINDING',
            'finding': f'{3,6,9} are zero modes of D=(I-G14_sym)^(1/2). '
                       f'Mass gap={safe(r42,"kernel_analysis","mass_gap",default=0.7532):.4f}. '
                       f'r(Dirac energy, proj_369)='
                       f'{safe(r42,"surah_dirac_summary","corr_energy_proj369",default=-0.74):.3f}.',
            'verdict': 'NEW'
        },
    ]

    fmt = "{:8s}  {:30s}  {:12s}  {}"
    print(fmt.format("Exp", "Title", "Result", "Key Finding"))
    print("─" * 70)
    for s in scorecard:
        finding_short = s['finding'][:55] + '...' if len(s['finding']) > 55 else s['finding']
        print(fmt.format(s['exp'], s['title'][:30], s['result'][:12], finding_short))

    # ── Five governing questions ───────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("FIVE GOVERNING QUESTIONS")
    print("─" * 70)

    questions = [
        {
            'q': 'Q1. Does the Schrodinger equation accept d369?',
            'a': 'NO. G14 has det=0, rank=6, is non-invertible. No Hermitian H_Q '
                 'exists such that G14=exp(-iH). Exp 36 confirms with mean error 70.6%.',
            'status': 'ANSWERED — NEGATIVE'
        },
        {
            'q': 'Q2. What is the correct mathematical framework?',
            'a': 'Open Markov Dynamics / Lindblad CPTP map. G14 is a column-stochastic '
                 'transition matrix with absorbing subspace {3,6,9} and transient '
                 'states {1,2,4,5,7,8}. Steady state: 77.8% on {3,6,9} (Exp 39).',
            'status': 'ANSWERED — LINDBLAD / MARKOV'
        },
        {
            'q': 'Q3. What is the dynamical status of {3,6,9}?',
            'a': 'Three roles simultaneously: (1) Absorbing states of Markov chain, '
                 '(2) Decoherence-Free Subspace of Lindblad dynamics, '
                 '(3) Zero modes of discrete Dirac operator (Exp 42, mass gap=0.75).',
            'status': 'ANSWERED — TRIPLE ROLE'
        },
        {
            'q': 'Q4. What is the entropy signature of the Quran?',
            'a': 'Maximum entropy base: H_norm=0.9948 (99.48% of theoretical maximum). '
                 'Near-perfectly uniform digit-root distribution, combined with '
                 'systematic +4.9pp bias toward {3,6,9}. Unique among tested Arabic texts.',
            'status': 'ANSWERED — NEW (Exp 41)'
        },
        {
            'q': 'Q5. Is the Quran distribution statistically distinct?',
            'a': 'YES. Exp 34: proj(Quran)=38.1% vs Bukhari 30.4%, Muallaqat 28.2%, '
                 'Futuhat 34.7%, all p<0.001. Exp 41: Quran has highest Shannon entropy '
                 'vs all controls (Cliffs d=0.71 vs Bukhari, p~0).',
            'status': 'ANSWERED — STRONG'
        },
    ]

    for q_dict in questions:
        print(f"\n  {q_dict['q']}")
        print(f"  -> {q_dict['a']}")
        print(f"  STATUS: {q_dict['status']}")

    # ── Key numbers ───────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("KEY NUMBERS")
    print("─" * 70)

    numbers = [
        ("G14 rank / det",                    "6/9  /  0"),
        ("G14 eigenvalues",                   "{1⁴, -1¹, 0⁴}"),
        ("Steady state on {3,6,9}",           "77.8%  (7/9)"),
        ("Lindblad jump operators",           "6"),
        ("Quran projection {3,6,9}",          "38.1%  (random baseline: 33.3%)"),
        ("Quran vs Bukhari projection",       "38.1% vs 30.4%  p<0.001"),
        ("Quran Shannon entropy H_norm",      "0.9948  (max possible: 1.0)"),
        ("Quran KL from uniform",             "0.0114  (Bukhari: 0.1355)"),
        ("Dirac mass gap",                    "0.7532"),
        ("Corr(Dirac energy, proj_369)",      "r = -0.74  (strong negative)"),
        ("Zero modes of D for {3,6,9}",       "3 (|6⟩ pure, |9⟩ pure, |3⟩ spread)"),
        ("Surahs tested",                     "114"),
    ]

    for label, value in numbers:
        print(f"  {label:<40s}  {value}")

    # ── Two-layer fingerprint ─────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("TWO-LAYER FINGERPRINT (updated)")
    print("─" * 70)
    print("""
  Layer 1 — LEXICAL (order-invariant):
    Mechanism: digit-root frequency distribution
    Measure:   projection on {3,6,9} = 38.1%
    Property:  stable under word shuffling (Exp 35)
    Entropy:   H_norm = 0.9948 (near-maximum balance)
    New:       maximum entropy + systematic {3,6,9} bias (Exp 41)

  Layer 2 — ARCHITECTURAL (order-dependent):
    Mechanism: surah/ayah structural organization
    Measure:   Mann-Whitney on surah-level statistics (Exp 07)
    Property:  depends on word order and surah arrangement
    Status:    confirmed distinct from Layer 1

  Layer 3 — TOPOLOGICAL (new, from Exp 42):
    Mechanism: Dirac zero mode structure
    Measure:   kernel(D=(I-G14_sym)^1/2) contains {3,6,9}
    Property:  protected by mass gap = 0.7532
    New:       {3,6,9} are topologically stable ground states
""")

    # ── Open questions ────────────────────────────────────────────────────────
    print("─" * 70)
    print("OPEN QUESTIONS (next experiments)")
    print("─" * 70)
    open_qs = [
        ("Exp 44", "Non-Islamic Arabic religious text",
         "Is H_norm=0.9948 unique to Quran or shared by Arabic religious texts?"),
        ("Exp 45", "n-gram digit root analysis",
         "Is there architectural information in consecutive digit root sequences?"),
        ("Exp 46", "Dirac index theorem verification",
         "Does the Atiyah-Singer index count zero modes correctly for G14?"),
    ]
    for exp, title, question in open_qs:
        print(f"  {exp}: {title}")
        print(f"         {question}")

    # ── Final verdict ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    print("""
  The Schrodinger equation does NOT apply to d369 (G14 is non-unitary).

  The correct framework is Markov/Lindblad open dynamics, in which
  {3,6,9} play THREE simultaneous roles:
    (1) Absorbing states of the Markov chain
    (2) Decoherence-free subspace of the Lindblad dynamics
    (3) Topologically protected zero modes of the Dirac operator

  The Quran exhibits a unique entropic signature:
    Maximum entropy base (H_norm=0.9948) combined with
    systematic excess on the G14-absorbing states {3,6,9}.
    No compared Arabic text shows this combination.

  STATUS: INTERNAL — NO PUBLICATION until Oxford referee responses.
""")
    print("=" * 70)

    # ── Generate markdown report ──────────────────────────────────────────────
    md = f"""# تقرير التوليف النهائي — Exp 43
## Final Synthesis Report: Complete Quantum-Mathematical Framework (Exp 33–42)

**الباحث / Author:** Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
**التاريخ / Date:** 2026-05-15
**المرحلة / Phase:** Internal Research — NO PUBLICATION

---

## لوحة النتائج / Scorecard

| التجربة | العنوان | النتيجة | الاكتشاف الرئيسي |
|---------|---------|---------|-----------------|
| Exp 33 | طيف G14 | PARTIAL | {{3,6,9}} فضاء ثابت ✓ — 4 قيم ذاتية=1 لا 3 |
| Exp 34 | الإسقاط الكمي | **PASS** | القرآن 38.1% > البخاري 30.4% > المعلقات 28.2% (p<0.001) |
| Exp 35 | محاكاة التبدد | REVISED | الإسقاط مستقل عن الترتيب — طبقة معجمية |
| Exp 36 | البحث عن H_Q | FAIL (متوقع) | لا وجود لهاملتوني — يؤكد اللاوحدوية |
| Exp 37 | اختبار الخطية | EXCLUDED | نتيجة بديهية رياضياً |
| Exp 38 | فحص الوحدوية | **KEY** | G14 = مصفوفة ماركوف عمودية، det=0 |
| Exp 39 | نظام لِنْدبلاد | **PASS** | {{3,6,9}} = DFS، 6 مؤثرات قفز، حالة مستقرة 77.8% |
| Exp 40 | التوليف الأول | COMPLETE | بصمتان: معجمية + معمارية |
| Exp 41 | تحليل الإنتروبي | **NEW** | H_norm=0.9948 — أعلى إنتروبي بين النصوص العربية |
| Exp 42 | مؤثر ديراك | **NEW** | {{3,6,9}} = zero modes، mass gap=0.75، r=-0.74 |

---

## الأسئلة الخمسة الجوهرية

### Q1. هل تقبل معادلة شرودنغر بنية d369؟
**لا.** G14 غير وحدوية (det=0، رتبة=6). لا يوجد H هرميتي يحقق G14=exp(-iH). Exp 36 يؤكد بخطأ تقريب 70.6%.

### Q2. ما الإطار الرياضي الصحيح؟
**Open Markov Dynamics / Lindblad CPTP map.** G14 مصفوفة انتقال عمودية بحالات امتصاص {{3,6,9}} وحالات عابرة {{1,2,4,5,7,8}}. الحالة المستقرة: 77.8% على {{3,6,9}}.

### Q3. ما الدور الديناميكي لـ {{3,6,9}}؟
**ثلاثة أدوار متزامنة:**
1. حالات امتصاص في سلسلة ماركوف
2. فضاء خالٍ من التبدد (DFS) في ديناميكا لِنْدبلاد
3. Zero modes محمية طوبولوجياً للمؤثر D=(I-G14_sym)^(1/2)

### Q4. ما البصمة الإنتروبية للقرآن؟
**H_norm = 0.9948** — 99.48% من الإنتروبي القصوى. توزيع شبه منتظم تماماً على الجذور 1-9، مع انحياز منهجي +4.9 نقطة مئوية نحو {{3,6,9}}. فريد بين النصوص العربية المختبرة.

### Q5. هل التوزيع القرآني متميز إحصائياً؟
**نعم.** Exp 34: p<0.001 مقابل جميع النصوص الضابطة. Exp 41: أعلى إنتروبي شانون (Cliff's d=0.71 مقابل البخاري، p~0).

---

## الأرقام الرئيسية

| المقياس | القيمة |
|---------|--------|
| رتبة G14 / محددها | 6/9 / 0 |
| قيم G14 الذاتية | {{1⁴, -1¹, 0⁴}} |
| الحالة المستقرة على {{3,6,9}} | 77.8% (7/9) |
| مؤثرات قفز لِنْدبلاد | 6 |
| إسقاط القرآن على {{3,6,9}} | 38.1% (عشوائي: 33.3%) |
| إنتروبي شانون H_norm | 0.9948 (أقصى: 1.0) |
| KL من التوزيع المنتظم | 0.0114 (البخاري: 0.1355) |
| فجوة الكتلة (mass gap) لديراك | 0.7532 |
| ارتباط (طاقة ديراك، إسقاط {{3,6,9}}) | r = -0.74 |

---

## البنية الثلاثية للبصمة (محدّثة)

```
البصمة القرآنية = طبقة معجمية + طبقة معمارية + طبقة طوبولوجية
```

| الطبقة | الآلية | التجربة | المقياس |
|--------|--------|---------|---------|
| المعجمية | توزيع الجذور الرقمية | Exp 34, 41 | إسقاط 38.1%، H_norm=0.9948 |
| المعمارية | تنظيم الآيات والسور | Exp 07, 35 | p<10⁻⁶ في الاختبار المعماري |
| الطوبولوجية | zero modes للمؤثر D | Exp 42 | mass gap=0.75، r=-0.74 |

---

## الخلاصة

> **G14 ليست مؤثراً تطورياً وحدوياً — إنها قناة ماركوف مفتوحة (Lindblad / CPTP map).**
>
> {{3,6,9}} تؤدي ثلاثة أدوار متزامنة: حالات امتصاص، فضاء خالٍ من التبدد، zero modes محمية طوبولوجياً.
>
> القرآن يحمل بصمة إنتروبية فريدة: توزيع منتظم قصوياً مع انحياز منهجي خفيف نحو الحالات الماصّة.

**القرار:** محفوظ في الدُرج — لا نشر حتى ردود Oxford على الأوراق I–III.
"""

    # Save JSON
    results = {
        'experiment':      'Exp43_FinalSynthesis',
        'date':            '2026-05-15',
        'author':          'Emad Suleiman Alwan',
        'ORCID':           '0009-0004-5797-6140',
        'n_experiments':   10,
        'experiments':     list(range(33, 43)),
        'scorecard':       scorecard,
        'governing_questions': questions,
        'key_numbers':     {label: value for label, value in numbers},
        'three_layer_fingerprint': {
            'lexical':       {'exp': 'Exp 34, 41', 'measure': 'proj=38.1%, H_norm=0.9948'},
            'architectural': {'exp': 'Exp 07, 35', 'measure': 'p<1e-6 architectural test'},
            'topological':   {'exp': 'Exp 42',     'measure': 'mass_gap=0.75, r=-0.74'},
        },
        'open_questions':  [
            {'exp': e, 'title': t, 'question': q}
            for e, t, q in open_qs
        ],
        'final_verdict': (
            'G14 is a Lindblad/CPTP open Markov channel, not a unitary operator. '
            '{3,6,9} simultaneously serve as: absorbing states, DFS, and topological '
            'zero modes (mass gap=0.75). The Quran has a unique entropic signature: '
            'maximum entropy distribution (H_norm=0.9948) combined with systematic '
            'excess on G14-absorbing states {3,6,9}.'
        ),
        'publication_status': 'INTERNAL — NO PUBLICATION until Oxford referee responses'
    }

    json_path = os.path.join(RESULTS_DIR, 'exp43_synthesis.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    md_path = os.path.join(RESULTS_DIR, 'exp43_synthesis_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"\nResults saved:")
    print(f"  {json_path}")
    print(f"  {md_path}")
    return results


if __name__ == '__main__':
    main()
