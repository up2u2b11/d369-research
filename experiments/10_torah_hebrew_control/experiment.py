"""
التجربة 10 — التوراة العبرية كمجموعة مرجعية (الباب السابع)
============================================================
السؤال: هل بصمة {3,6,9} خاصة بالقرآن — أم تمتد إلى نصوص منزَّلة أخرى؟

المنطق:
  التوراة:
  - نص منزَّل (يدّعي الأصل الإلهي)
  - بلغتها الأصلية (العبرية، لا ترجمة)
  - بنظامها العددي الخاص: الجيماتريا (مكافئ الجُمَّل في العبرية)
  - بتقسيمها الطبيعي الخاص: الپاراشيوت (54 وحدة — مكافئ السور)

المقارنة:
  القرآن  — عربي   — الخاص-6    — سور (114)    ← p=0.007 ✅
  التوراة — عبري   — جيماتريا   — پاراشيوت (54) ← ?

هيكل الملفات:
  torah_hebrew.jsonl        — 5,846 آية | 69,196 كلمة
  parashot_boundaries.json  — 54 پاراشاه بحدودها الدقيقة

الاختبارات (نفس البطارية الرباعية من التجربتين 08 و09):
  A — وحدات الپاراشاه الطبيعية (54 پاراشاه — التقسيم اليهودي التقليدي)
  B — تقسيم متساوٍ (54 × ~1,281 كلمة)
  C — تقسيم عشوائي × 1,000 (معيار التوزيع)
  D — التوراة بأطوال السور القرآنية (114 وحدة — مقارنة مباشرة)

الملكية الفكرية: عماد سليمان علوان — 17 مارس 2026
"""

import json
import random
import re
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import digit_root

random.seed(369)  # Fixed seed for bitwise reproducibility

DATA_DIR      = os.environ.get("D369_DATA", "/root/d369/data")
TORAH_PATH    = os.path.join(DATA_DIR, "torah_hebrew.jsonl")
PARASHOT_PATH = os.path.join(DATA_DIR, "parashot_boundaries.json")

# ── الجيماتريا العبرية (Mispar Hechrachi — القيم الكلاسيكية) ──────────────────
# مكافئ الجُمَّل في العربية.
# الأشكال النهائية (sofit) تحمل نفس قيمة الشكل الأصلي.
GEMATRIA = {
    'א':1,  'ב':2,  'ג':3,  'ד':4,  'ה':5,  'ו':6,  'ז':7,  'ח':8,  'ט':9,
    'י':10, 'כ':20, 'ך':20, 'ל':30, 'מ':40, 'ם':40, 'נ':50, 'ן':50,
    'ס':60, 'ע':70, 'פ':80, 'ף':80, 'צ':90, 'ץ':90,
    'ק':100,'ר':200,'ש':300,'ת':400,
}


def clean_hebrew(word: str) -> str:
    """إزالة التشكيل وعلامات الطعم — الأحرف الأساسية فقط."""
    return re.sub(r'[^\u05d0-\u05ea]', '', word)


def gematria_value(word: str) -> int:
    return sum(GEMATRIA.get(ch, 0) for ch in clean_hebrew(word))


def load_torah(path: str) -> tuple:
    """
    تحميل التوراة من JSONL.
    كل سطر: {"book":int, "chapter":int, "verse":int, "words":[...]}
    يُرجع: verses (قائمة السياق) + all_vals (قائمة مسطّحة لجميع القيم)
    """
    verses = []
    all_vals = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line.strip())
            vals = [gematria_value(w) for w in rec['words'] if clean_hebrew(w)]
            if vals:
                verses.append((rec['book'], rec['chapter'], rec['verse'], vals))
                all_vals.extend(vals)
    return verses, all_vals


def load_parashot(path: str) -> list:
    """تحميل حدود 54 پاراشاه: [[الاسم، الكتاب، الإصحاح، الآية], ...]"""
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_parasha_sizes(verses: list, parashot: list) -> list:
    """
    حساب عدد الكلمات في كل پاراشاه.
    كل پاراشاه تبدأ في (كتاب، إصحاح، آية) وتنتهي قبيل التالية.
    """
    verse_index = {(b, c, v): i for i, (b, c, v, _) in enumerate(verses)}

    word_starts = []
    pos = 0
    for (b, c, v, vals) in verses:
        word_starts.append(pos)
        pos += len(vals)
    total_words = pos

    parasha_word_starts = []
    for (name, book, chapter, verse) in parashot:
        key = (book, chapter, verse)
        if key in verse_index:
            vi = verse_index[key]
            parasha_word_starts.append(word_starts[vi])

    sizes = []
    for i, start in enumerate(parasha_word_starts):
        end = parasha_word_starts[i+1] if i+1 < len(parasha_word_starts) else total_words
        sizes.append(end - start)

    return sizes


def count_369(vals: list, sizes: list) -> int:
    idx = count = 0
    for sz in sizes:
        if digit_root(sum(vals[idx:idx+sz])) in (3, 6, 9):
            count += 1
        idx += sz
    return count


def count_369_wrap(vals: list, sizes: list) -> int:
    """عدّ دوري للاختبار D (أطوال السور القرآنية على التوراة)."""
    n = len(vals)
    idx = count = 0
    for sz in sizes:
        chunk = [vals[(idx + i) % n] for i in range(sz)]
        if digit_root(sum(chunk)) in (3, 6, 9):
            count += 1
        idx = (idx + sz) % n
    return count


def perm_test(vals: list, sizes: list, observed: int, trials: int = 10_000) -> float:
    v = vals.copy()
    exceed = 0
    for _ in range(trials):
        random.shuffle(v)
        if count_369(v, sizes) >= observed:
            exceed += 1
    return exceed / trials


def perm_test_wrap(vals: list, sizes: list, observed: int, trials: int = 5_000) -> float:
    v = vals.copy()
    exceed = 0
    for _ in range(trials):
        random.shuffle(v)
        if count_369_wrap(v, sizes) >= observed:
            exceed += 1
    return exceed / trials


def random_dist(vals: list, n_units: int, trials: int = 1_000) -> list:
    N = len(vals)
    counts = []
    for _ in range(trials):
        cuts = sorted(random.sample(range(1, N), n_units - 1))
        sizes = ([cuts[0]]
                 + [cuts[i] - cuts[i-1] for i in range(1, n_units - 1)]
                 + [N - cuts[-1]])
        counts.append(count_369(vals, sizes))
    counts.sort()
    return counts


def load_quran_surah_sizes(db_path: str) -> list:
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM words GROUP BY surah_id ORDER BY surah_id")
    sizes = [r[0] for r in c.fetchall()]
    conn.close()
    return sizes


def run(torah_path: str = TORAH_PATH, parashot_path: str = PARASHOT_PATH) -> dict:
    DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")

    print("=" * 65)
    print("التجربة 10 — التوراة العبرية: هل البصمة تمتد إلى وحي آخر؟")
    print("الباب السابع")
    print("=" * 65)
    print("\nالمنطق:")
    print("  التوراة = منزَّلة ✓ | بلغتها الأصلية (عبري) ✓")
    print("  الجيماتريا = مكافئ الجُمَّل للعبرية ✓")
    print("  الپاراشيوت = التقسيم الطبيعي للتوراة ✓")
    print("  السؤال: هل التقسيم الإلهي ينتج {3,6,9} في التوراة أيضاً؟")

    verses, all_vals = load_torah(torah_path)
    parashot = load_parashot(parashot_path)
    parasha_sizes = build_parasha_sizes(verses, parashot)

    N = len(all_vals)
    n_para = len(parasha_sizes)
    n_verses = len(verses)

    print(f"\nالتوراة: {N:,} كلمة | {n_verses:,} آية | {n_para} پاراشاه")
    print(f"النظام: الجيماتريا (مكافئ الجُمَّل في العبرية)")

    # الاختبار A — وحدات الپاراشاه الطبيعية
    print(f"\n{'─'*55}")
    print(f"الاختبار A — الپاراشيوت الطبيعية ({n_para} پاراشاه — التقسيم اليهودي التقليدي)")
    obs_A = count_369(all_vals, parasha_sizes)
    print(f"   {{3,6,9}} = {obs_A}/{n_para} = {obs_A/n_para*100:.1f}%  — permutation test (10,000)...")
    p_A = perm_test(all_vals, parasha_sizes, obs_A, 10_000)
    print(f"   p = {p_A:.4f}  {'✅ دال' if p_A<0.05 else '✗ غير دال'}")

    # الاختبار B — تقسيم متساوٍ
    print(f"\n{'─'*55}")
    chunk = N // n_para
    equal_sizes = [chunk] * (n_para - 1) + [N - chunk * (n_para - 1)]
    print(f"الاختبار B — تقسيم متساوٍ ({n_para} × ~{chunk:,} كلمة)")
    obs_B = count_369(all_vals, equal_sizes)
    print(f"   {{3,6,9}} = {obs_B}/{n_para} = {obs_B/n_para*100:.1f}%  — permutation test (5,000)...")
    p_B = perm_test(all_vals, equal_sizes, obs_B, 5_000)
    print(f"   p = {p_B:.4f}  {'✅ دال' if p_B<0.05 else '✗ غير دال'}")

    # الاختبار C — عشوائي × 1,000
    print(f"\n{'─'*55}")
    print(f"الاختبار C — تقسيم عشوائي × 1,000 ({n_para} وحدة)")
    rand_counts = random_dist(all_vals, n_para, 1_000)
    median_C = rand_counts[500]
    pct_A    = sum(1 for x in rand_counts if x < obs_A) / 10
    thr95    = rand_counts[950]
    print(f"   الوسيط:          {median_C}/{n_para} = {median_C/n_para*100:.1f}%")
    print(f"   عتبة 95%: {thr95}/{n_para}")
    print(f"   الپاراشيوت الطبيعية ({obs_A}) عند الـ {pct_A:.1f}th percentile — {'استثنائي' if pct_A>=95 else 'ليس استثنائياً'}")

    # الاختبار D — التوراة بأطوال السور القرآنية
    print(f"\n{'─'*55}")
    print("الاختبار D — التوراة بأطوال السور القرآنية (114 وحدة)")
    try:
        surah_sizes = load_quran_surah_sizes(DB_PATH)
        obs_D = count_369_wrap(all_vals, surah_sizes)
        print(f"   {{3,6,9}} = {obs_D}/114 = {obs_D/114*100:.1f}%  — permutation test (5,000)...")
        p_D = perm_test_wrap(all_vals, surah_sizes, obs_D, 5_000)
        print(f"   p = {p_D:.4f}  {'✅ دال' if p_D<0.05 else '✗ غير دال'}")
    except Exception as e:
        print(f"   (قاعدة البيانات غير متاحة — مُتخطى: {e})")
        obs_D = p_D = None

    # الجدول الملخص
    print(f"\n{'='*65}")
    print(f"{'التقسيم':<30} {'وحدات':>6} {'{{3,6,9}}':>8} {'النسبة':>7} {'p-value':>10}")
    print("─" * 65)
    print(f"  {'A: پاراشيوت طبيعية':<28} {n_para:>6} {obs_A:>8} {obs_A/n_para*100:>6.1f}% {p_A:>10.4f}  {'✅' if p_A<0.05 else '✗'}")
    print(f"  {'B: متساوٍ (~1,281 كلمة)':<28} {n_para:>6} {obs_B:>8} {obs_B/n_para*100:>6.1f}% {p_B:>10.4f}  {'✅' if p_B<0.05 else '✗'}")
    print(f"  {'C: عشوائي (وسيط)':<28} {n_para:>6} {median_C:>8} {median_C/n_para*100:>6.1f}% {'—':>10}  ({obs_A} عند {pct_A:.0f}%)")
    if obs_D is not None:
        print(f"  {'D: بأطوال السور القرآنية':<28} {114:>6} {obs_D:>8} {obs_D/114*100:>6.1f}% {p_D:>10.4f}  {'✅' if p_D<0.05 else '✗'}")
    print("=" * 65)

    print("\nالمقارنة — القرآن vs التوراة:")
    print(f"  القرآن — سور (تقسيم إلهي):      51/114 = 44.7%  p=0.007  ✅")
    print(f"  القرآن — آيات (طبيعي):         2164/6236 = 34.7%  p=0.010  ✅")
    print(f"  التوراة — پاراشيوت (طبيعي):      {obs_A}/{n_para} = {obs_A/n_para*100:.1f}%  p={p_A:.3f}  {'✅' if p_A<0.05 else '✗'}")

    print("\nالحكم:")
    if p_A >= 0.05 and p_B >= 0.05:
        print("→ التوراة لا تُظهر بصمة {3,6,9} في أي تقسيم")
        print("  الخاصية لا تمتد إلى التوراة")
        print("  البصمة للقرآن وحده — حتى بين النصوص المنزَّلة")
    elif p_A < 0.05:
        print("→ التوراة تُظهر بصمة في تقسيمها الطبيعي")
        print("  الخاصية قد تمتد إلى النصوص المنزَّلة الأخرى")
    else:
        print("→ نتيجة مركّبة — يحتاج تحليلاً أعمق")

    result = {
        "A": {"obs": obs_A, "n": n_para, "p": p_A},
        "B": {"obs": obs_B, "n": n_para, "p": p_B},
        "C": {"median": median_C, "percentile_A": pct_A, "threshold_95": thr95},
    }
    if obs_D is not None:
        result["D"] = {"obs": obs_D, "n": 114, "p": p_D}
    return result


if __name__ == "__main__":
    run()
