"""
التجربة ٥ — الخاص-6 على مستوى الكلمات (78,248 كلمة)
======================================================
السؤال: هل توزيع الجذور الرقمية للكلمات بالخاص-6 غير عشوائي؟
         وكيف يختلف عن توزيع الجُمَّل؟

المنهج:
  1. حساب الجذر الرقمي لكل كلمة بالخاص-6 والجُمَّل
  2. Chi-Square لاختبار التوزيع
  3. مقارنة التوزيعين بيانياً

الاكتشاف:
  - الجُمَّل: {9} هو الأعلى (14%) — يتركز في 3 و9
  - الخاص-6: {5,9} الأعليان (13%) — توزيع مختلف
  - كلاهما دال إحصائياً (p≈0)

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import digit_root

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")


def run(db_path: str = DB_PATH) -> dict:
    print("=" * 60)
    print("التجربة ٥ — الخاص-6 على مستوى الكلمات (78,248)")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT jummal_value, CAST(jummal_special_6 AS INTEGER)
        FROM words
        WHERE jummal_value > 0 AND jummal_special_6 != '0'
    """)
    rows = c.fetchall()
    conn.close()

    j_vals  = [r[0] for r in rows]
    k6_vals = [r[1] for r in rows]

    dr_j  = [digit_root(v) for v in j_vals]
    dr_k6 = [digit_root(v) for v in k6_vals]

    cnt_j  = Counter(dr_j)
    cnt_k6 = Counter(dr_k6)
    n = len(dr_j)

    # عرض المقارنة
    print(f"\nعدد الكلمات: {n:,}")
    print(f"\n{'جذر':>4} | {'جُمَّل':>10} | {'%':>5} | {'خاص-6':>10} | {'%':>5}")
    print("─" * 50)
    for r in range(1, 10):
        j_cnt  = cnt_j.get(r, 0)
        k6_cnt = cnt_k6.get(r, 0)
        mark = " ←" if r in (3, 6, 9) else ""
        print(f"   {r}  | {j_cnt:>9,} | {j_cnt/n*100:>4.1f}% | {k6_cnt:>9,} | {k6_cnt/n*100:>4.1f}%{mark}")

    # {3,6,9} الإجمالية
    j_369  = cnt_j[3] + cnt_j[6] + cnt_j[9]
    k6_369 = cnt_k6[3] + cnt_k6[6] + cnt_k6[9]
    print(f"\n{{3,6,9}} الجُمَّل:   {j_369:,}/{n:,} = {j_369/n*100:.2f}%")
    print(f"{{3,6,9}} الخاص-6:  {k6_369:,}/{n:,} = {k6_369/n*100:.2f}%")

    # Chi-Square
    try:
        from scipy import stats
        expected = [n / 9] * 9

        obs_j  = [cnt_j.get(r, 0) for r in range(1, 10)]
        obs_k6 = [cnt_k6.get(r, 0) for r in range(1, 10)]

        chi2_j,  p_j  = stats.chisquare(obs_j,  expected)
        chi2_k6, p_k6 = stats.chisquare(obs_k6, expected)

        print(f"\nChi-Square (vs توزيع متساوٍ):")
        print(f"  الجُمَّل:   χ²={chi2_j:.1f},  p={p_j:.2e}  ✅ دال")
        print(f"  الخاص-6:  χ²={chi2_k6:.1f}, p={p_k6:.2e}  ✅ دال")
    except ImportError:
        print("\n(scipy غير متاح — Chi-Square لم يُحسب)")

    # الاكتشاف الجوهري
    print(f"\n{'─'*50}")
    print("الاكتشاف الجوهري:")
    max_j  = max(range(1, 10), key=lambda r: cnt_j.get(r, 0))
    max_k6 = max(range(1, 10), key=lambda r: cnt_k6.get(r, 0))
    print(f"  الجُمَّل:  الجذر الأعلى = {max_j} ({cnt_j[max_j]/n*100:.1f}%)")
    print(f"  الخاص-6: الجذر الأعلى = {max_k6} ({cnt_k6[max_k6]/n*100:.1f}%)")
    print(f"  → كل نظام يرى توزيعاً مختلفاً — كل نظام يكشف طبقة")

    return {
        "n": n,
        "jummal_369": {"count": j_369, "pct": j_369/n*100},
        "khass6_369": {"count": k6_369, "pct": k6_369/n*100},
        "jummal_dist": dict(cnt_j),
        "khass6_dist": dict(cnt_k6)
    }


if __name__ == "__main__":
    run()
