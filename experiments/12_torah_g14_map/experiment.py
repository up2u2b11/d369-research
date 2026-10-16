#!/usr/bin/env python3
"""
التجربة 12 — البوابة التاسعة: خريطة تحوّلات G14 للتوراة العبرية
Experiment 12 — The Ninth Gate: G14 State Transformation Map for the Hebrew Torah

السؤال البحثي:
هل التوراة العبرية تحمل بنية تحوّلات منظّمة عند تجميع الفَرَاشُوت بالجذر الرقمي —
كما يحمل القرآن بنية G14 ذات الطبقات الأربع؟

الملكية الفكرية: عماد سليمان علوان — UP2U2B LLC
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict
import random
from datetime import datetime, timezone, timedelta

# ─── المسارات ───
D369_DIR = Path("/root/d369")
DATA_DIR = D369_DIR / "data"
TORAH_FILE = DATA_DIR / "torah_hebrew.jsonl"
PARASHOT_FILE = DATA_DIR / "parashot_boundaries.json"
RESULTS_DIR = Path(__file__).parent

# ─── الجماتريا العبرية القياسية (Mispar Gadol) ───
HEBREW_GEMATRIA = {
    'א': 1,   'ב': 2,   'ג': 3,   'ד': 4,   'ה': 5,
    'ו': 6,   'ז': 7,   'ח': 8,   'ט': 9,   'י': 10,
    'כ': 20,  'ל': 30,  'מ': 40,  'נ': 50,  'ס': 60,
    'ע': 70,  'פ': 80,  'צ': 90,  'ק': 100, 'ר': 200,
    'ש': 300, 'ת': 400,
    # الأشكال النهائية (sofiyot) — نفس قيم الأشكال العادية
    'ך': 20,  'ם': 40,  'ן': 50,  'ף': 80,  'ץ': 90,
}


def digit_root(n: int) -> int:
    """الجذر الرقمي — المجموع المتكرر حتى رقم واحد"""
    n = abs(n)
    if n == 0:
        return 0
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def compute_hebrew_gematria(word: str) -> int:
    """حساب الجماتريا لكلمة عبرية"""
    total = 0
    for ch in word:
        total += HEBREW_GEMATRIA.get(ch, 0)
    return total


def load_torah():
    """تحميل نص التوراة — إرجاع قائمة الآيات"""
    verses = []
    with open(TORAH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            verses.append(json.loads(line.strip()))
    return verses


def load_parashot():
    """تحميل حدود الفَرَاشُوت الـ54"""
    with open(PARASHOT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # كل عنصر: [name, book, chapter, verse]
    return data


def assign_verses_to_parashot(verses, parashot):
    """تعيين كل آية إلى فرشاتها"""
    # بناء حدود البداية لكل فرشاه
    boundaries = []
    for p in parashot:
        name, book, ch, vs = p
        boundaries.append((name, book, ch, vs))

    # تعيين كل آية
    parashah_verses = defaultdict(list)
    parashah_names = []

    for i, (name, book, ch, vs) in enumerate(boundaries):
        parashah_names.append(name)

    # لكل آية — ابحث عن آخر فرشاه تبدأ قبلها أو عندها
    for v in verses:
        vbook, vch, vvs = v['book'], v['chapter'], v['verse']
        assigned = None
        for i in range(len(boundaries) - 1, -1, -1):
            pname, pbook, pch, pvs = boundaries[i]
            if (vbook > pbook or
                (vbook == pbook and vch > pch) or
                (vbook == pbook and vch == pch and vvs >= pvs)):
                assigned = i
                break
        if assigned is not None:
            parashah_verses[assigned].append(v)

    return parashah_names, parashah_verses


def compute_gematria_for_unit(verses_list):
    """حساب مجموع الجماتريا لمجموعة آيات"""
    total = 0
    for v in verses_list:
        for word in v['words']:
            # تجاهل علامات الفقرات (פ و ס)
            if word in ('פ', 'ס'):
                continue
            total += compute_hebrew_gematria(word)
    return total


def build_transformation_map(values, labels=None):
    """
    بناء خريطة التحوّلات:
    1. تجميع القيم بالجذر الرقمي (1-9)
    2. جمع القيم داخل كل مجموعة
    3. حساب الجذر الرقمي لكل مجموع
    4. تسجيل التحوّل: الجذر الأصلي → الجذر الناتج
    """
    # خطوة 1: تصنيف كل قيمة بجذرها الرقمي
    groups = defaultdict(list)
    for i, val in enumerate(values):
        dr = digit_root(val)
        groups[dr].append(val)

    # خطوة 2+3: جمع كل مجموعة وحساب الجذر الرقمي للمجموع
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
            transformation[dr] = 0  # مجموعة فارغة

    return transformation, group_sums, group_counts, groups


def analyze_transformation_map(transformation):
    """تحليل خريطة التحوّلات — استخراج الأنماط"""
    results = {
        'self_preserving': [],      # جذور تحفظ نفسها
        'cycles': [],               # دورات مغلقة
        'sinks': [],                # مجذوبات (نقاط جذب)
        'tesla_preserves': False,   # هل {3,6,9} تحفظ نفسها مجتمعة؟
        'transformation': transformation,
    }

    # الجذور التي تحفظ نفسها
    for dr in range(1, 10):
        if transformation.get(dr, 0) == dr:
            results['self_preserving'].append(dr)

    # تسلا {3,6,9}
    tesla = {3, 6, 9}
    tesla_targets = set()
    for t in tesla:
        if t in transformation:
            tesla_targets.add(transformation[t])
    results['tesla_preserves'] = tesla_targets == tesla

    # اكتشاف الدورات
    visited_global = set()
    for start in range(1, 10):
        if start in visited_global or transformation.get(start, 0) == 0:
            continue
        path = []
        current = start
        visited = set()
        while current not in visited and current != 0:
            visited.add(current)
            path.append(current)
            current = transformation.get(current, 0)
        if current in visited and current != 0:
            cycle_start = path.index(current)
            cycle = path[cycle_start:]
            if len(cycle) > 1:
                results['cycles'].append(tuple(cycle))
            visited_global.update(cycle)

    # اكتشاف المجذوبات (نقاط الجذب)
    sink_counts = defaultdict(int)
    for dr in range(1, 10):
        target = transformation.get(dr, 0)
        if target != 0:
            sink_counts[target] += 1
    for target, count in sink_counts.items():
        if count >= 3:  # 3 جذور أو أكثر تتجه إلى نفس النقطة
            results['sinks'].append((target, count))

    return results


def monte_carlo_test(values, n_permutations=100_000, seed=369):
    """
    اختبار مونتي كارلو:
    نأخذ القيم الحقيقية ونعيّن لكل واحدة مجموعة عشوائية من {1,...,9}
    نقيس: عدد الجذور المحافظة على نفسها
    """
    random.seed(seed)

    # النتيجة الحقيقية
    real_trans, _, _, _ = build_transformation_map(values)
    real_analysis = analyze_transformation_map(real_trans)
    real_self_count = len(real_analysis['self_preserving'])
    real_tesla = real_analysis['tesla_preserves']

    # عدّادات
    count_self_ge = 0       # عدد المحاولات بنفس العدد أو أكثر من المحافظين
    count_tesla = 0         # عدد المحاولات حيث {3,6,9} تحفظ نفسها
    self_distribution = defaultdict(int)  # توزيع عدد المحافظين

    for _ in range(n_permutations):
        # تعيين عشوائي لمجموعات
        shuffled_groups = defaultdict(list)
        for val in values:
            assigned_dr = random.randint(1, 9)
            shuffled_groups[assigned_dr].append(val)

        # حساب التحوّلات
        perm_trans = {}
        for dr in range(1, 10):
            members = shuffled_groups[dr]
            if members:
                s = sum(members)
                perm_trans[dr] = digit_root(s)
            else:
                perm_trans[dr] = 0

        # عدد المحافظين
        perm_self = sum(1 for dr in range(1, 10) if perm_trans.get(dr, 0) == dr)
        self_distribution[perm_self] += 1
        if perm_self >= real_self_count and real_self_count > 0:
            count_self_ge += 1

        # تسلا
        tesla_ok = all(perm_trans.get(t, 0) == t for t in [3, 6, 9])
        if tesla_ok:
            count_tesla += 1

    p_self = count_self_ge / n_permutations if real_self_count > 0 else 1.0
    p_tesla = count_tesla / n_permutations

    return {
        'real_self_count': real_self_count,
        'real_self_preserving': real_analysis['self_preserving'],
        'real_tesla_preserves': real_tesla,
        'p_self': p_self,
        'p_tesla': p_tesla,
        'self_distribution': dict(self_distribution),
        'n_permutations': n_permutations,
    }


def run_battery(name, values, labels, n_units):
    """تشغيل بطارية كاملة على مجموعة بيانات"""
    print(f"\n{'='*70}")
    print(f"  البطارية {name} — {n_units} وحدة")
    print(f"{'='*70}")

    # بناء خريطة التحوّلات
    trans, sums, counts, groups = build_transformation_map(values)
    analysis = analyze_transformation_map(trans)

    # طباعة الخريطة
    print(f"\n  خريطة التحوّلات:")
    print(f"  {'الجذر':>8} → {'الناتج':>8} | {'العدد':>6} | {'المجموع':>15} | الحكم")
    print(f"  {'-'*65}")
    for dr in range(1, 10):
        target = trans.get(dr, 0)
        count = counts.get(dr, 0)
        s = sums.get(dr, 0)
        preserve = "✓ يحفظ نفسه" if target == dr else ""
        print(f"  {dr:>8} → {target:>8} | {count:>6} | {s:>15,} | {preserve}")

    # الأنماط المكتشفة
    print(f"\n  الأنماط المكتشفة:")
    print(f"    جذور تحفظ نفسها: {analysis['self_preserving'] or 'لا يوجد'}")
    print(f"    تسلا {{3,6,9}} تحفظ نفسها: {'نعم' if analysis['tesla_preserves'] else 'لا'}")
    print(f"    دورات مغلقة: {analysis['cycles'] or 'لا يوجد'}")
    print(f"    مجذوبات: {analysis['sinks'] or 'لا يوجد'}")

    # مونتي كارلو
    print(f"\n  اختبار مونتي كارلو (100,000 تبديل)...")
    mc = monte_carlo_test(values, n_permutations=100_000)
    print(f"    عدد المحافظين الحقيقي: {mc['real_self_count']}")
    print(f"    p-value (المحافظين): {mc['p_self']:.5f}")
    print(f"    p-value (تسلا): {mc['p_tesla']:.5f}")
    print(f"    توزيع المحافظين في التبديلات:")
    for k in sorted(mc['self_distribution'].keys()):
        pct = mc['self_distribution'][k] / mc['n_permutations'] * 100
        print(f"      {k} محافظين: {mc['self_distribution'][k]:>7,} ({pct:.2f}%)")

    return {
        'name': name,
        'n_units': n_units,
        'transformation': trans,
        'sums': sums,
        'counts': counts,
        'analysis': analysis,
        'monte_carlo': mc,
        'values': values,
        'labels': labels,
    }


def format_results(battery_a, battery_b, battery_c):
    """تنسيق النتائج النهائية"""
    KSA = timezone(timedelta(hours=3))
    now = datetime.now(KSA).strftime("%Y-%m-%d %H:%M KSA")

    lines = []
    lines.append("=" * 70)
    lines.append("  التجربة 12 — البوابة التاسعة")
    lines.append("  خريطة تحوّلات G14 للتوراة العبرية")
    lines.append(f"  التاريخ: {now}")
    lines.append("  الملكية الفكرية: عماد سليمان علوان — UP2U2B LLC")
    lines.append("=" * 70)

    # ملخص تنفيذي
    lines.append("\n" + "─" * 70)
    lines.append("  الملخص التنفيذي")
    lines.append("─" * 70)

    all_results = [battery_a, battery_b, battery_c]
    for r in all_results:
        name = r['name']
        mc = r['monte_carlo']
        analysis = r['analysis']
        sp = analysis['self_preserving']
        tesla = analysis['tesla_preserves']
        lines.append(f"\n  البطارية {name} ({r['n_units']} وحدة):")
        lines.append(f"    جذور محافظة: {sp if sp else 'لا يوجد'}")
        lines.append(f"    تسلا {{3,6,9}}: {'✓ تحفظ نفسها' if tesla else '✗ لا تحفظ نفسها'}")
        lines.append(f"    p-value (محافظين): {mc['p_self']:.5f}")
        lines.append(f"    p-value (تسلا): {mc['p_tesla']:.5f}")

    # مقارنة مع القرآن
    lines.append("\n" + "─" * 70)
    lines.append("  المقارنة مع القرآن")
    lines.append("─" * 70)
    lines.append("  القرآن (114 سورة):")
    lines.append("    ✓ {3,6,9} تحفظ نفسها (p = 0.00146)")
    lines.append("    ✓ 4 طبقات: ثالوث مستقر + مجموعة منجذبة + دورة + مسار")
    lines.append("    ✓ بنية G14 رباعية الطبقات (p < 0.00001)")
    lines.append(f"\n  التوراة ({battery_a['n_units']} فرشاه):")
    sp_a = battery_a['analysis']['self_preserving']
    tesla_a = battery_a['analysis']['tesla_preserves']
    if sp_a:
        lines.append(f"    الجذور المحافظة: {sp_a}")
    else:
        lines.append("    ✗ لا جذور محافظة")
    lines.append(f"    تسلا: {'✓' if tesla_a else '✗'}")
    pa = battery_a['monte_carlo']['p_self']
    lines.append(f"    p-value: {pa:.5f}")

    # الخلاصة
    lines.append("\n" + "─" * 70)
    lines.append("  الخلاصة")
    lines.append("─" * 70)

    # تحديد النتيجة بناءً على البيانات
    any_significant = any(
        r['monte_carlo']['p_self'] < 0.05 or r['monte_carlo']['p_tesla'] < 0.05
        for r in all_results
    )

    if any_significant:
        lines.append("  التوراة تحمل بنية تحوّلات دالة إحصائياً.")
        lines.append("  يجب فحص ما إذا كانت مطابقة أو مختلفة عن بنية القرآن.")
    else:
        lines.append("  التوراة لا تحمل بنية تحوّلات منظّمة دالة إحصائياً.")
        lines.append("  الفرق بين القرآن والتوراة ليس في النسبة فقط")
        lines.append("  بل في المعمارية العميقة — بنية G14 خاصية قرآنية فريدة.")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


def main():
    print("تحميل البيانات...")

    # تحميل التوراة
    verses = load_torah()
    parashot = load_parashot()
    parashah_names, parashah_verses = assign_verses_to_parashot(verses, parashot)

    print(f"  الآيات: {len(verses)}")
    print(f"  الفَرَاشُوت: {len(parashot)}")

    # ─── البطارية A: الفَرَاشُوت (54 وحدة) ───
    parashah_values = []
    parashah_labels = []
    for i in range(len(parashot)):
        vlist = parashah_verses.get(i, [])
        val = compute_gematria_for_unit(vlist)
        parashah_values.append(val)
        parashah_labels.append(parashah_names[i])
        print(f"    {parashah_names[i]:20s} — {len(vlist):>4} آيات — جماتريا: {val:>10,} — جذر: {digit_root(val)}")

    battery_a = run_battery("A — الفَرَاشُوت", parashah_values, parashah_labels, 54)

    # ─── البطارية B: الأسفار الخمسة (5 وحدات) ───
    book_names = ["بريشيت (التكوين)", "شموت (الخروج)", "ويقرا (اللاويين)",
                  "بمدبار (العدد)", "دفاريم (التثنية)"]
    book_verses = defaultdict(list)
    for v in verses:
        book_verses[v['book']].append(v)

    book_values = []
    book_labels = []
    for b in range(1, 6):
        val = compute_gematria_for_unit(book_verses[b])
        book_values.append(val)
        book_labels.append(book_names[b-1])
        print(f"    {book_names[b-1]:25s} — {len(book_verses[b]):>5} آيات — جماتريا: {val:>12,} — جذر: {digit_root(val)}")

    battery_b = run_battery("B — الأسفار الخمسة", book_values, book_labels, 5)

    # ─── البطارية C: الآيات (5,846 وحدة) ───
    verse_values = []
    verse_labels = []
    for v in verses:
        val = 0
        for word in v['words']:
            if word in ('פ', 'ס'):
                continue
            val += compute_hebrew_gematria(word)
        verse_values.append(val)
        verse_labels.append(f"{v['book']}:{v['chapter']}:{v['verse']}")

    battery_c = run_battery("C — الآيات", verse_values, verse_labels, len(verses))

    # ─── النتائج النهائية ───
    report = format_results(battery_a, battery_b, battery_c)
    print(report)

    # حفظ النتائج
    results_file = RESULTS_DIR / "results.md"
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nالنتائج محفوظة في: {results_file}")

    # حفظ البيانات الخام (JSON)
    raw_data = {
        'battery_a': {
            'values': battery_a['values'],
            'labels': battery_a['labels'],
            'transformation': battery_a['transformation'],
            'sums': battery_a['sums'],
            'counts': battery_a['counts'],
            'self_preserving': battery_a['analysis']['self_preserving'],
            'tesla_preserves': battery_a['analysis']['tesla_preserves'],
            'p_self': battery_a['monte_carlo']['p_self'],
            'p_tesla': battery_a['monte_carlo']['p_tesla'],
        },
        'battery_b': {
            'values': battery_b['values'],
            'labels': battery_b['labels'],
            'transformation': battery_b['transformation'],
            'sums': battery_b['sums'],
            'counts': battery_b['counts'],
            'self_preserving': battery_b['analysis']['self_preserving'],
            'tesla_preserves': battery_b['analysis']['tesla_preserves'],
            'p_self': battery_b['monte_carlo']['p_self'],
            'p_tesla': battery_b['monte_carlo']['p_tesla'],
        },
        'battery_c': {
            'values': battery_c['values'],
            'labels': battery_c['labels'],
            'transformation': battery_c['transformation'],
            'sums': battery_c['sums'],
            'counts': battery_c['counts'],
            'self_preserving': battery_c['analysis']['self_preserving'],
            'tesla_preserves': battery_c['analysis']['tesla_preserves'],
            'p_self': battery_c['monte_carlo']['p_self'],
            'p_tesla': battery_c['monte_carlo']['p_tesla'],
        },
    }
    raw_file = RESULTS_DIR / "raw_data.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"البيانات الخام: {raw_file}")


if __name__ == "__main__":
    main()
