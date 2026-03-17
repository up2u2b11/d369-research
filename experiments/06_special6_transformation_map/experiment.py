"""
التجربة ٦ — خريطة التحوّلات بالخاص-6 (مقارنة مع G14)
=========================================================
السؤال: هل الخاص-6 يُنتج نفس خريطة التحوّلات التي أنتجها الجُمَّل؟
         هل {3,6,9} تثبت عند تجميع مجموعاتها بالخاص-6؟

المنهج:
  1. حساب جذر كل سورة بالخاص-6
  2. تجميع السور حسب جذر الخاص-6 (9 مجموعات)
  3. حساب جذر مجموع كل مجموعة
  4. مقارنة مع G14 (الجُمَّل)

الاكتشاف:
  - الجُمَّل: {3,6,9} ثابتة (G14)
  - الخاص-6: {9} فقط يثبت
  → نظامان مختلفان — كل منهما يرى طبقة مختلفة

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import JUMMAL_5, KHASS_6, digit_root, word_value

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")


def load_surah_values(db_path: str) -> dict:
    """تحميل مجاميع الجُمَّل والخاص-6 لكل سورة"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, text_uthmani, CAST(jummal_special_6 AS INTEGER)
        FROM words ORDER BY surah_id, word_pos_in_quran
    """)
    rows = c.fetchall()
    conn.close()

    sums_j5 = defaultdict(int)
    sums_k6 = defaultdict(int)
    for sid, txt, k6 in rows:
        sums_j5[sid] += sum(JUMMAL_5.get(ch, 0) for ch in txt)
        sums_k6[sid]  += k6
    return dict(sums_j5), dict(sums_k6)


def build_map(surah_sums: dict) -> dict:
    """بناء خريطة التحوّلات"""
    groups = defaultdict(lambda: {"sum": 0, "count": 0})
    for sid, total in sorted(surah_sums.items()):
        dr = digit_root(total)
        groups[dr]["sum"] += total
        groups[dr]["count"] += 1

    return {
        dr: {
            "count": groups[dr]["count"],
            "group_sum": groups[dr]["sum"],
            "group_dr": digit_root(groups[dr]["sum"]),
            "preserves": digit_root(groups[dr]["sum"]) == dr
        }
        for dr in range(1, 10)
    }


def run(db_path: str = DB_PATH) -> dict:
    print("=" * 65)
    print("التجربة ٦ — خريطة التحوّلات: الجُمَّل vs الخاص-6")
    print("=" * 65)

    sums_j5, sums_k6 = load_surah_values(db_path)
    map_j5 = build_map(sums_j5)
    map_k6 = build_map(sums_k6)

    # عرض G14 الجُمَّل
    print(f"\n{'─'*55}")
    print("الجُمَّل ة=5 — G14 الأصلي")
    print(f"{'─'*55}")
    print(f"{'جذر':>4} | {'عدد':>4} | {'مجموع الجُمَّل':>18} | {'→':>2} | النتيجة")
    print("─" * 55)
    j5_stable = set()
    for dr in range(1, 10):
        info = map_j5[dr]
        mark = "✅ ثابت" if info["preserves"] else f"→ {info['group_dr']}"
        if info["preserves"]:
            j5_stable.add(dr)
        print(f"   {dr}  |  {info['count']:>2}  | {info['group_sum']:>18,}  | {info['group_dr']:>2} | {mark}")

    # عرض خريطة الخاص-6
    print(f"\n{'─'*55}")
    print("الخاص-6 — خريطته الخاصة")
    print(f"{'─'*55}")
    print(f"{'جذر':>4} | {'عدد':>4} | {'مجموع الخاص-6':>20} | {'→':>2} | النتيجة")
    print("─" * 55)
    k6_stable = set()
    for dr in range(1, 10):
        info = map_k6[dr]
        mark = "✅ ثابت" if info["preserves"] else f"→ {info['group_dr']}"
        if info["preserves"]:
            k6_stable.add(dr)
        print(f"   {dr}  |  {info['count']:>2}  | {info['group_sum']:>20,}  | {info['group_dr']:>2} | {mark}")

    # المقارنة
    print(f"\n{'─'*55}")
    print("المقارنة")
    print(f"{'─'*55}")
    print(f"{'جذر':>4} | {'الجُمَّل':>8} | {'الخاص-6':>9} | متطابق؟")
    print("─" * 38)
    matches = 0
    for dr in range(1, 10):
        j_out = map_j5[dr]["group_dr"]
        k_out = map_k6[dr]["group_dr"]
        same = "✅" if j_out == k_out else "✗"
        if j_out == k_out:
            matches += 1
        print(f"   {dr}  |  {dr}→{j_out}    |  {dr}→{k_out}    | {same}")

    print(f"\nتطابق: {matches}/9 جذور")
    print(f"الجُمَّل المحافظة:   {sorted(j5_stable)}")
    print(f"الخاص-6 المحافظة:  {sorted(k6_stable)}")
    print(f"\nالقاسم المشترك: {sorted(j5_stable & k6_stable)}")

    return {
        "jummal_stable": sorted(j5_stable),
        "khass6_stable": sorted(k6_stable),
        "common": sorted(j5_stable & k6_stable),
        "matches": matches
    }


if __name__ == "__main__":
    run()
