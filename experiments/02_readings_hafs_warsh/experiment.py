"""
التجربة ٢ — ثبات البصمة عبر القراءتين: حفص وورش
==================================================
السؤال: هل بصمة {3,6,9} تبقى حين نتحول من قراءة حفص إلى قراءة ورش؟

المنهج:
  1. حساب جُمَّل القرآن بقراءة حفص (المصحف العثماني)
  2. حساب جُمَّل القرآن بقراءة ورش (quran_warsh.txt)
  3. مقارنة:
     أ) إجمالي الجُمَّل والفرق النسبي
     ب) خريطة التحوّلات في كل رواية
     ج) هل {3,6,9} تثبت في الروايتين؟

النتيجة المتوقعة:
  - الفرق الكلي < 0.01%
  - {3,9} ثابتتان في الروايتين
  - {6} محمية بآلية مختلفة في كل رواية (البسملة في حفص، النص في ورش)

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
import re
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import JUMMAL_5, digit_root

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")
WARSH_PATH = os.environ.get("WARSH_PATH", "/home/emad/quran_warsh.txt")


def load_hafs_by_surah(db_path: str) -> dict:
    """تحميل جُمَّل حفص من قاعدة البيانات"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT surah_id, text_uthmani FROM words ORDER BY surah_id, word_pos_in_quran")
    rows = c.fetchall()
    conn.close()

    sums = defaultdict(int)
    for surah_id, text in rows:
        sums[surah_id] += sum(JUMMAL_5.get(ch, 0) for ch in text)
    return dict(sums)


def load_warsh_by_surah(warsh_path: str) -> dict:
    """تحميل جُمَّل ورش من ملف النص"""
    try:
        with open(warsh_path, encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"  ⚠️ ملف ورش غير موجود: {warsh_path}")
        return {}

    sums = defaultdict(int)
    for line in lines:
        # تنسيق: رقم_السورة|رقم_الآية|النص
        parts = line.strip().split('|')
        if len(parts) >= 3:
            try:
                surah_id = int(parts[0])
                text = parts[2]
                sums[surah_id] += sum(JUMMAL_5.get(ch, 0) for ch in text)
            except (ValueError, IndexError):
                continue
    return dict(sums)


def transformation_map(surah_sums: dict) -> dict:
    groups = defaultdict(int)
    counts = defaultdict(int)
    for sid, total in surah_sums.items():
        dr = digit_root(total)
        groups[dr] += total
        counts[dr] += 1
    return {dr: {"group_sum": groups[dr], "group_dr": digit_root(groups[dr]),
                 "count": counts[dr], "preserves": digit_root(groups[dr]) == dr}
            for dr in range(1, 10)}


def run(db_path: str = DB_PATH, warsh_path: str = WARSH_PATH) -> dict:
    print("=" * 60)
    print("التجربة ٢ — ثبات البصمة: حفص vs ورش")
    print("=" * 60)

    hafs = load_hafs_by_surah(db_path)
    warsh = load_warsh_by_surah(warsh_path)

    total_hafs = sum(hafs.values())
    total_warsh = sum(warsh.values()) if warsh else 0

    print(f"\nإجمالي جُمَّل حفص:  {total_hafs:,}  → جذر {digit_root(total_hafs)}")
    if warsh:
        diff = abs(total_hafs - total_warsh)
        pct = diff / total_hafs * 100
        print(f"إجمالي جُمَّل ورش:   {total_warsh:,}  → جذر {digit_root(total_warsh)}")
        print(f"الفرق: {diff:,} ({pct:.4f}%)")

    # خريطة التحولات لحفص
    hafs_map = transformation_map(hafs)
    print(f"\n{'─'*50}")
    print("خريطة التحوّلات — حفص")
    print(f"{'─'*50}")
    hafs_stable = set()
    for dr in range(1, 10):
        info = hafs_map[dr]
        mark = "✅ ثابت" if info["preserves"] else f"→ {info['group_dr']}"
        if info["preserves"]:
            hafs_stable.add(dr)
        print(f"  جذر {dr} ({info['count']} سور): → {info['group_dr']}  {mark}")
    print(f"  الثابتة: {sorted(hafs_stable)}")

    # خريطة التحولات لورش
    if warsh:
        warsh_map = transformation_map(warsh)
        print(f"\n{'─'*50}")
        print("خريطة التحوّلات — ورش")
        print(f"{'─'*50}")
        warsh_stable = set()
        for dr in range(1, 10):
            info = warsh_map[dr]
            mark = "✅ ثابت" if info["preserves"] else f"→ {info['group_dr']}"
            if info["preserves"]:
                warsh_stable.add(dr)
            print(f"  جذر {dr} ({info['count']} سور): → {info['group_dr']}  {mark}")
        print(f"  الثابتة: {sorted(warsh_stable)}")

        common = hafs_stable & warsh_stable
        print(f"\nمشتركة في الروايتين: {sorted(common)}")

    return {"hafs_total": total_hafs, "hafs_stable": sorted(hafs_stable)}


if __name__ == "__main__":
    run()
