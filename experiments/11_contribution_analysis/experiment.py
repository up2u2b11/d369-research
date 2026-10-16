"""
تجربة الإسهام — أي السور تحمل البصمة؟
Leave-one-out analysis × 114 سورة | الخاص-6

المنطق:
  الأساس: 51/114 = 44.7%  p≈0.007
  لكل سورة i (1→114):
    - أُزيلها من المجموعة
    - أُشغّل permutation test على الـ 113 الباقية
    - أقيس: هل p ارتفع (حاملة) أم انخفض (مُعزِّزة) أم ثبت (محايدة)؟

الملكية الفكرية: عماد سليمان علوان — 18 مارس 2026
"""

import sqlite3, random, sys, time

sys.path.insert(0, '/tmp/d369-research/shared')
from utils import digit_root

DB = '/root/d369/d369.db'

SURAH_NAMES = {
    1:'الفاتحة',2:'البقرة',3:'آل عمران',4:'النساء',5:'المائدة',
    6:'الأنعام',7:'الأعراف',8:'الأنفال',9:'التوبة',10:'يونس',
    11:'هود',12:'يوسف',13:'الرعد',14:'إبراهيم',15:'الحجر',
    16:'النحل',17:'الإسراء',18:'الكهف',19:'مريم',20:'طه',
    21:'الأنبياء',22:'الحج',23:'المؤمنون',24:'النور',25:'الفرقان',
    26:'الشعراء',27:'النمل',28:'القصص',29:'العنكبوت',30:'الروم',
    31:'لقمان',32:'السجدة',33:'الأحزاب',34:'سبأ',35:'فاطر',
    36:'يس',37:'الصافات',38:'ص',39:'الزمر',40:'غافر',
    41:'فصلت',42:'الشورى',43:'الزخرف',44:'الدخان',45:'الجاثية',
    46:'الأحقاف',47:'محمد',48:'الفتح',49:'الحجرات',50:'ق',
    51:'الذاريات',52:'الطور',53:'النجم',54:'القمر',55:'الرحمن',
    56:'الواقعة',57:'الحديد',58:'المجادلة',59:'الحشر',60:'الممتحنة',
    61:'الصف',62:'الجمعة',63:'المنافقون',64:'التغابن',65:'الطلاق',
    66:'التحريم',67:'الملك',68:'القلم',69:'الحاقة',70:'المعارج',
    71:'نوح',72:'الجن',73:'المزمل',74:'المدثر',75:'القيامة',
    76:'الإنسان',77:'المرسلات',78:'النبأ',79:'النازعات',80:'عبس',
    81:'التكوير',82:'الانفطار',83:'المطففين',84:'الانشقاق',85:'البروج',
    86:'الطارق',87:'الأعلى',88:'الغاشية',89:'الفجر',90:'البلد',
    91:'الشمس',92:'الليل',93:'الضحى',94:'الشرح',95:'التين',
    96:'العلق',97:'القدر',98:'البينة',99:'الزلزلة',100:'العاديات',
    101:'القارعة',102:'التكاثر',103:'العصر',104:'الهمزة',105:'الفيل',
    106:'قريش',107:'الماعون',108:'الكوثر',109:'الكافرون',110:'النصر',
    111:'المسد',112:'الإخلاص',113:'الفلق',114:'الناس',
}

TRIALS = 3000  # لكل سورة — 114 × 3000 = 342,000 إجمالاً


def load_data():
    """تحميل قيم الخاص-6 لكل سورة من قاعدة البيانات"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, jummal_special_6
        FROM words
        ORDER BY surah_id, word_pos_in_quran
    """)
    rows = c.fetchall()
    conn.close()

    surahs = {}
    for sid, val in rows:
        val = int(val) if val is not None else 0
        if val > 0:
            surahs.setdefault(sid, []).append(val)
    return surahs


def perm_test(all_vals, sizes, observed, trials=TRIALS):
    v = all_vals.copy()
    exceed = 0
    for _ in range(trials):
        random.shuffle(v)
        idx = cnt = 0
        for sz in sizes:
            if digit_root(sum(v[idx:idx+sz])) in (3, 6, 9):
                cnt += 1
            idx += sz
        if cnt >= observed:
            exceed += 1
    return exceed / trials


def run():
    print("=" * 68)
    print("تجربة الإسهام — أي السور تحمل بصمة {3,6,9}؟")
    print(f"Leave-one-out × 114 سورة | {TRIALS:,} تجربة لكل سورة")
    print("=" * 68)

    surahs = load_data()
    sids   = sorted(surahs.keys())

    # الأساس
    baseline_obs = sum(1 for sid in sids if digit_root(sum(surahs[sid])) in (3, 6, 9))
    print(f"\nالأساس: {baseline_obs}/{len(sids)} = {baseline_obs/len(sids)*100:.1f}%  p≈0.007\n")

    results = []
    t0 = time.time()

    for i, sid in enumerate(sids, 1):
        # الـ 113 الباقية
        remaining = [s for s in sids if s != sid]
        vals_113  = []
        sizes_113 = []
        obs_113   = 0
        for s in remaining:
            vals_113.extend(surahs[s])
            sizes_113.append(len(surahs[s]))
            if digit_root(sum(surahs[s])) in (3, 6, 9):
                obs_113 += 1

        p = perm_test(vals_113, sizes_113, obs_113)

        dr_i    = digit_root(sum(surahs[sid]))
        in_369  = dr_i in (3, 6, 9)
        delta   = p - 0.007

        results.append({
            'surah': sid,
            'name':  SURAH_NAMES.get(sid, f'{sid}'),
            'dr':    dr_i,
            'in_369': in_369,
            'n_words': len(surahs[sid]),
            'obs_113': obs_113,
            'p':     p,
            'delta': delta,
        })

        # تقدم كل 10 سور
        if i % 10 == 0 or i == 1 or i == len(sids):
            eta = (time.time()-t0)/i * (len(sids)-i)
            mark = '✅' if in_369 else '  '
            print(f"  [{i:3d}/114] {SURAH_NAMES.get(sid,''):>10}  "
                  f"dr={dr_i}  {mark}  p_بدونها={p:.4f}  Δ={delta:+.4f}  ETA={eta:.0f}s")

    elapsed = time.time() - t0
    print(f"\nاكتمل في {elapsed:.0f}s\n")

    # ── التصنيف ───────────────────────────────────────────────────────────────
    THRESHOLD_LOAD  =  0.020   # إزالتها ترفع p > +0.02  → حاملة
    THRESHOLD_BOOST = -0.005   # إزالتها تُحسّن p < -0.005 → مُعزِّزة

    load_b  = [r for r in results if r['delta'] >  THRESHOLD_LOAD]
    boosters= [r for r in results if r['delta'] <  THRESHOLD_BOOST]
    neutral = [r for r in results if THRESHOLD_BOOST <= r['delta'] <= THRESHOLD_LOAD]

    # ── جدول كامل مرتب تنازلياً بـ delta ─────────────────────────────────────
    results.sort(key=lambda x: x['delta'], reverse=True)

    print(f"{'='*68}")
    print(f"{'السورة':>6} {'الاسم':>12} {'dr':>4} {'369?':>5} {'كلمات':>6} {'p_بدونها':>10} {'Δ':>8}  {'الحكم'}")
    print("─" * 68)
    for r in results:
        mark = '✅' if r['in_369'] else '  '
        if r['delta'] > THRESHOLD_LOAD:
            tag = "🔴 حاملة"
        elif r['delta'] < THRESHOLD_BOOST:
            tag = "🟢 مُعزِّزة"
        else:
            tag = "◻ محايدة"
        print(f"  {r['surah']:>4}  {r['name']:>12}  {r['dr']:>3}  {mark:>4}  "
              f"{r['n_words']:>5}  {r['p']:>9.4f}  {r['delta']:>+7.4f}  {tag}")

    # ── ملخص ─────────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"التصنيف النهائي (Δ من p_أساسي=0.007):")
    print(f"  🔴 حاملة  (Δ > +0.020):  {len(load_b):>3} سورة  — إزالتها تُضعف الإشارة")
    print(f"  ◻  محايدة:               {len(neutral):>3} سورة  — لا تأثير يُذكر")
    print(f"  🟢 مُعزِّزة (Δ < -0.005): {len(boosters):>3} سورة  — إزالتها تُقوّي الإشارة")

    if load_b:
        print(f"\n📍 أكثر 10 سور حملاً للبصمة:")
        for r in sorted(load_b, key=lambda x: x['delta'], reverse=True)[:10]:
            mark = '✅' if r['in_369'] else '  '
            print(f"     سورة {r['surah']:>3} — {r['name']:>12}  dr={r['dr']}  {mark}  "
                  f"p_بدونها={r['p']:.4f}  Δ={r['delta']:+.4f}  كلمات={r['n_words']}")

    if boosters:
        print(f"\n📍 أكثر 10 سور تقليلاً للضوضاء:")
        for r in sorted(boosters, key=lambda x: x['delta'])[:10]:
            mark = '✅' if r['in_369'] else '  '
            print(f"     سورة {r['surah']:>3} — {r['name']:>12}  dr={r['dr']}  {mark}  "
                  f"p_بدونها={r['p']:.4f}  Δ={r['delta']:+.4f}  كلمات={r['n_words']}")

    # توزيع الجذور في السور الحاملة
    if load_b:
        dr_dist = {}
        for r in load_b:
            dr_dist[r['dr']] = dr_dist.get(r['dr'], 0) + 1
        print(f"\nتوزيع الجذور في السور الحاملة:")
        for dr in sorted(dr_dist):
            mark = "← {3,6,9}" if dr in (3,6,9) else ""
            print(f"  جذر {dr}: {dr_dist[dr]:>2} سورة  {mark}")

    return results


if __name__ == '__main__':
    results = run()
