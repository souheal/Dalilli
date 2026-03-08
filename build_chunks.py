import json

with open(r'C:\Users\Owner\Desktop\Kratos\data1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

by_id = {e['id']: e for e in data}
chunks = []

def chunk(chunk_id, parent_id, art, clause, chap, sec, level, text, kw, cite, prefix=None, items=None, meta=None, law_id="income_tax"):
    full_text = text
    if items:
        full_text = (prefix + "\n" if prefix else "") + "\n".join(items)
    c = {
        "chunk_id": chunk_id,
        "parent_chunk_id": parent_id,
        "law_id": law_id,
        "article_no": art,
        "clause": clause,
        "chapter": chap,
        "section": sec,
        "chunk_level": level,
        "context_prefix": prefix,
        "text": full_text,
        "keywords": kw,
        "citation": cite,
        "char_count": len(full_text)
    }
    if meta:
        c["metadata"] = meta
    return c

CHAP = "الباب الاول"
SEC1 = "الفصل الاول - الاشخاص الخاضعون للضريبة"
SEC2 = "الفصل الاول - تحديد الربح الصافي"

# ===== PREAMBLE =====
e = by_id['income_tax_intro_1']
chunks.append(chunk("chunk_intro", None, None, None, None, None, "main",
    e['text'], e['keywords'], "مقدمة قانون ضريبة الدخل"))

# ===== ARTICLE 1 (main: merge a+b+c+d) =====
a, b, c, d = [by_id[f'income_tax_art1_{x}'] for x in ['a','b','c','d']]
merged = a['text'] + "\n" + b['text'] + "\n" + c['text'] + "\n" + d['text']
all_kw = list(dict.fromkeys(a['keywords'] + b['keywords'] + c['keywords'] + d['keywords']))
chunks.append(chunk("chunk_art1", None, 1, None, CHAP, None, "main",
    merged, all_kw, "المادة 1 من قانون ضريبة الدخل"))
# Sub: a, b only (c,d too short)
chunks.append(chunk("chunk_art1_a", "chunk_art1", 1, "أ", CHAP, None, "sub",
    a['text'], a['keywords'], a['metadata']['citation']))
chunks.append(chunk("chunk_art1_b", "chunk_art1", 1, "ب", CHAP, None, "sub",
    b['text'], b['keywords'], b['metadata']['citation']))

# ===== ARTICLE 2 =====
PFX2 = "المادة 2 الفقرة (ا) - الجهات الخاضعة للضريبة:"

# 2.a intro
e = by_id['income_tax_art2_a_intro']
chunks.append(chunk("chunk_art2_a_intro", None, 2, "أ", CHAP, SEC1, "sub",
    e['text'], e['keywords'], e['metadata']['citation']))

# 2.a items 1-4
e1 = by_id['income_tax_art2_a_entities_1_8']
items1 = e1['items']
chunks.append(chunk("chunk_art2_a_items_1_4", "chunk_art2_a_intro", 2, "أ", CHAP, SEC1, "sub",
    PFX2, ["قطاع عام", "مؤسسات مالية", "شركات", "منشات خارجية"],
    e1['metadata']['citation'], prefix=PFX2, items=items1[0:4]))

# 2.a items 5-8, 27-33
chunks.append(chunk("chunk_art2_a_items_5_8_27_33", "chunk_art2_a_intro", 2, "أ", CHAP, SEC1, "sub",
    PFX2, ["استيراد", "تصدير", "عقارات", "جامعات", "سفريات", "نقل بضائع"],
    e1['metadata']['citation'], prefix=PFX2, items=items1[4:]))

# 2.a items 9-18
e2 = by_id['income_tax_art2_a_entities_9_26']
items2 = e2['items']
chunks.append(chunk("chunk_art2_a_items_9_18", "chunk_art2_a_intro", 2, "أ", CHAP, SEC1, "sub",
    PFX2, ["وقود", "ادوية", "مشافي", "سينما", "فنادق", "صناعة"],
    e2['metadata']['citation'], prefix=PFX2, items=items2[0:10]))

# 2.a items 19-26
chunks.append(chunk("chunk_art2_a_items_19_26", "chunk_art2_a_intro", 2, "أ", CHAP, SEC1, "sub",
    PFX2, ["سياحة", "ملاهي", "محاسبة", "خدمات بحرية"],
    e2['metadata']['citation'], prefix=PFX2, items=items2[10:]))

# 2.b
e = by_id['income_tax_art2_b']
chunks.append(chunk("chunk_art2_b", None, 2, "ب", CHAP, SEC1, "sub",
    e['text'], e['keywords'], e['metadata']['citation'],
    prefix="المادة 2 - الاشخاص الخاضعون للضريبة:"))

# 2.d
e = by_id['income_tax_art2_d']
chunks.append(chunk("chunk_art2_d", None, 2, "د", CHAP, SEC1, "sub",
    e['text'], e['keywords'], e['metadata']['citation']))

# 2.e
e = by_id['income_tax_art2_e']
chunks.append(chunk("chunk_art2_e", None, 2, "هـ", CHAP, SEC1, "sub",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 3 =====
e = by_id['income_tax_art3']
chunks.append(chunk("chunk_art3", None, 3, None, CHAP, SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 4 (split items 1-5, 6-9) =====
e = by_id['income_tax_art4_exemptions']
PFX4 = "المادة 4 - الاعفاءات الضريبية:"
chunks.append(chunk("chunk_art4_items_1_5", None, 4, "أ", CHAP, SEC1, "sub",
    PFX4, ["اعفاء ضريبي", "جمعيات تعاونية", "زراعة", "تاليف", "عزف"],
    e['metadata']['citation'], prefix=PFX4, items=e['items'][0:5]))
chunks.append(chunk("chunk_art4_items_6_9", None, 4, "أ", CHAP, SEC1, "sub",
    PFX4, ["حضانة", "احتياجات خاصة", "نقل جوي", "نقل بحري", "مزارع"],
    e['metadata']['citation'], prefix=PFX4, items=e['items'][5:]))

# ===== ARTICLE 5 (merge a+b) =====
a5a = by_id['income_tax_art5_a']
a5b = by_id['income_tax_art5_b']
chunks.append(chunk("chunk_art5", None, 5, None, CHAP, SEC1, "main",
    a5a['text'] + "\n" + a5b['text'],
    list(dict.fromkeys(a5a['keywords'] + a5b['keywords'])),
    "المادة 5 من قانون ضريبة الدخل"))

# ===== ARTICLE 6 (split items 1-5, 6-9) =====
e = by_id['income_tax_art6_non_deductible']
PFX6 = "المادة 6 - لا تخصم من الضرائب:"
chunks.append(chunk("chunk_art6_items_1_5", None, 6, "أ", CHAP, SEC1, "sub",
    PFX6, ["عدم خصم", "جمعيات تعاونية", "زراعة"],
    e['metadata']['citation'], prefix=PFX6, items=e['items'][0:5]))
chunks.append(chunk("chunk_art6_items_6_9", None, 6, "أ", CHAP, SEC1, "sub",
    PFX6, ["حضانة", "نقل", "مزارع"],
    e['metadata']['citation'], prefix=PFX6, items=e['items'][5:]))

# ===== ARTICLE 7 =====
e = by_id['income_tax_art7_a']
chunks.append(chunk("chunk_art7_a", None, 7, "أ", CHAP, SEC2, "sub",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"incomplete_text": True}))

# ===== ARTICLE 8 =====
e = by_id['income_tax_art8_non_deductible_expenses']
items_text = e['text'] + "\n" + "\n".join(e['items'])
chunks.append(chunk("chunk_art8", None, 8, None, CHAP, SEC2, "main",
    items_text, e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 9 =====
e = by_id['income_tax_art9']
chunks.append(chunk("chunk_art9", None, 9, None, CHAP, SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 10 =====
e = by_id['income_tax_art10']
chunks.append(chunk("chunk_art10", None, 10, None, CHAP, SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 11 (main: merge a+b_text+c; sub: b with items, c) =====
a11a = by_id['income_tax_art11_a']
a11b = by_id['income_tax_art11_b']
a11c = by_id['income_tax_art11_c']
merged_11 = a11a['text'] + "\n" + a11b['text'] + "\n" + a11c['text']
kw_11 = list(dict.fromkeys(a11a['keywords'] + a11b['keywords'] + a11c['keywords']))
chunks.append(chunk("chunk_art11", None, 11, None, CHAP, SEC2, "main",
    merged_11, kw_11, "المادة 11 من قانون ضريبة الدخل"))

PFX11 = "المادة 11 - الاعباء والنفقات القابلة للتنزيل:"
items_11b = a11b['text'] + "\n" + "\n".join(a11b['items'])
chunks.append(chunk("chunk_art11_b", "chunk_art11", 11, "ب", CHAP, SEC2, "sub",
    items_11b, a11b['keywords'], a11b['metadata']['citation'],
    prefix=PFX11))

chunks.append(chunk("chunk_art11_c", "chunk_art11", 11, "ج", CHAP, SEC2, "sub",
    a11c['text'], a11c['keywords'], a11c['metadata']['citation']))

# ===== ARTICLE 12 =====
e = by_id['income_tax_art12']
chunks.append(chunk("chunk_art12", None, 12, None, CHAP, SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 13 (main: merge a_text+b; sub: a with items) =====
a13a = by_id['income_tax_art13_a']
a13b = by_id['income_tax_art13_b']
merged_13 = a13a['text'] + "\n" + a13b['text']
kw_13 = list(dict.fromkeys(a13a['keywords'] + a13b['keywords']))
chunks.append(chunk("chunk_art13", None, 13, None, CHAP, SEC2, "main",
    merged_13, kw_13, "المادة 13 من قانون ضريبة الدخل"))

items_13a = a13a['text'] + "\n" + "\n".join(a13a['items'])
chunks.append(chunk("chunk_art13_a", "chunk_art13", 13, "أ", CHAP, SEC2, "sub",
    items_13a, a13a['keywords'], a13a['metadata']['citation']))

# ===== ARTICLE 14 =====
a14a = by_id['income_tax_art14_a']
a14b = by_id['income_tax_art14_b']
a14c = by_id['income_tax_art14_c']
chunks.append(chunk("chunk_art14_a", None, 14, "أ", CHAP, SEC2, "sub",
    a14a['text'], a14a['keywords'], a14a['metadata']['citation']))
chunks.append(chunk("chunk_art14_b", None, 14, "ب", CHAP, SEC2, "sub",
    a14b['text'], a14b['keywords'], a14b['metadata']['citation']))
chunks.append(chunk("chunk_art14_c", None, 14, "ج", CHAP, SEC2, "sub",
    a14c['text'], a14c['keywords'], a14c['metadata']['citation']))

# ===== ARTICLE 16 (main: merge a+b; sub: a split into two bracket groups, b) =====
CHAP3 = "الفصل الثالث - معدلات الضريبة وتحقيقها واستحقاقها"
a16a = by_id['income_tax_art16_a']
a16b = by_id['income_tax_art16_b']

# Main chunk: merge a text + b text
merged_16 = a16a['text'] + "\n" + "\n".join(a16a['items']) + "\n" + a16b['text']
kw_16 = list(dict.fromkeys(a16a['keywords'] + a16b['keywords']))
chunks.append(chunk("chunk_art16", None, 16, None, CHAP, CHAP3, "main",
    merged_16, kw_16, "المادة 16 من قانون ضريبة الدخل"))

# Sub: a brackets 1-6 (10% to 35% - up to 500,000)
PFX16 = "المادة 16 - الشرائح الضريبية التصاعدية على الارباح الصافية:"
chunks.append(chunk("chunk_art16_a_brackets_1_6", "chunk_art16", 16, "أ", CHAP, CHAP3, "sub",
    PFX16, ["شرائح ضريبية", "نسبة تصاعدية", "حد ادنى معفي", "ارباح صافية"],
    a16a['metadata']['citation'], prefix=PFX16, items=a16a['items'][0:6]))

# Sub: a brackets 7-19 (40% to 100% - above 500,000)
chunks.append(chunk("chunk_art16_a_brackets_7_19", "chunk_art16", 16, "أ", CHAP, CHAP3, "sub",
    PFX16, ["شرائح ضريبية مرتفعة", "نسبة تصاعدية", "ارباح كبيرة", "مليون ليرة"],
    a16a['metadata']['citation'], prefix=PFX16, items=a16a['items'][6:]))

# Sub: b - companies
chunks.append(chunk("chunk_art16_b", "chunk_art16", 16, "ب", CHAP, CHAP3, "sub",
    a16b['text'], a16b['keywords'], a16b['metadata']['citation'],
    meta={"text_quality": "heavily_reconstructed_from_ocr"}))

# ===== ARTICLE 19 (main: merge a+b; sub: a only, b too short) =====
a19a = by_id['income_tax_art19_a']
a19b = by_id['income_tax_art19_b']
merged_19 = a19a['text'] + "\n" + a19b['text']
kw_19 = list(dict.fromkeys(a19a['keywords'] + a19b['keywords']))
chunks.append(chunk("chunk_art19", None, 19, None, CHAP, CHAP3, "main",
    merged_19, kw_19, "المادة 19 من قانون ضريبة الدخل"))

chunks.append(chunk("chunk_art19_a", "chunk_art19", 19, "أ", CHAP, CHAP3, "sub",
    a19a['text'], a19a['keywords'], a19a['metadata']['citation']))

# ===== ARTICLE 20 (main: merge a+b+c; sub: a, b, c) =====
a20a = by_id['income_tax_art20_a']
a20b = by_id['income_tax_art20_b']
a20c = by_id['income_tax_art20_c']
merged_20 = a20a['text'] + "\n" + a20b['text'] + "\n" + a20c['text']
kw_20 = list(dict.fromkeys(a20a['keywords'] + a20b['keywords'] + a20c['keywords']))
chunks.append(chunk("chunk_art20", None, 20, None, CHAP, CHAP3, "main",
    merged_20, kw_20, "المادة 20 من قانون ضريبة الدخل"))

chunks.append(chunk("chunk_art20_a", "chunk_art20", 20, "أ", CHAP, CHAP3, "sub",
    a20a['text'], a20a['keywords'], a20a['metadata']['citation']))

chunks.append(chunk("chunk_art20_b", "chunk_art20", 20, "ب", CHAP, CHAP3, "sub",
    a20b['text'], a20b['keywords'], a20b['metadata']['citation']))

chunks.append(chunk("chunk_art20_c", "chunk_art20", 20, "ج", CHAP, CHAP3, "sub",
    a20c['text'], a20c['keywords'], a20c['metadata']['citation']))

# ===== ARTICLE 21 (complex: definition + penalties + transfer tax) =====
a21a = by_id['income_tax_art21_a']
a21b = by_id['income_tax_art21_b']
a21c = by_id['income_tax_art21_c']
a21d = by_id['income_tax_art21_d']
a21_tax = by_id['income_tax_art21_transfer_tax']
a21_exc = by_id['income_tax_art21_transfer_exceptions']
a21_txb = by_id['income_tax_art21_transfer_taxable']
a21h = by_id['income_tax_art21_h']

# Main: merge definition + transfer tax + deductibility
merged_21 = a21a['text'] + "\n" + a21_tax['text'] + "\n" + a21h['text']
kw_21 = list(dict.fromkeys(a21a['keywords'] + a21_tax['keywords'] + a21h['keywords']))
chunks.append(chunk("chunk_art21", None, 21, None, CHAP, CHAP3, "main",
    merged_21, kw_21, "المادة 21 من قانون ضريبة الدخل"))

chunks.append(chunk("chunk_art21_a", "chunk_art21", 21, "أ", CHAP, CHAP3, "sub",
    a21a['text'], a21a['keywords'], a21a['metadata']['citation']))

chunks.append(chunk("chunk_art21_b", "chunk_art21", 21, "ب", CHAP, CHAP3, "sub",
    a21b['text'], a21b['keywords'], a21b['metadata']['citation']))

chunks.append(chunk("chunk_art21_c", "chunk_art21", 21, "ج", CHAP, CHAP3, "sub",
    a21c['text'], a21c['keywords'], a21c['metadata']['citation']))

chunks.append(chunk("chunk_art21_d", "chunk_art21", 21, "د", CHAP, CHAP3, "sub",
    a21d['text'], a21d['keywords'], a21d['metadata']['citation']))

chunks.append(chunk("chunk_art21_transfer_tax", "chunk_art21", 21, None, CHAP, CHAP3, "sub",
    a21_tax['text'], a21_tax['keywords'], a21_tax['metadata']['citation']))

chunks.append(chunk("chunk_art21_transfer_exceptions", "chunk_art21", 21, None, CHAP, CHAP3, "sub",
    a21_exc['text'], a21_exc['keywords'], a21_exc['metadata']['citation']))

PFX21 = "المادة 21 - التصرفات الخاضعة وغير الخاضعة لضريبة التصرفات العقارية:"
chunks.append(chunk("chunk_art21_transfer_taxable", "chunk_art21", 21, None, CHAP, CHAP3, "sub",
    PFX21, a21_txb['keywords'],
    a21_txb['metadata']['citation'], prefix=PFX21, items=a21_txb['items']))

chunks.append(chunk("chunk_art21_h", "chunk_art21", 21, "هـ", CHAP, CHAP3, "sub",
    a21h['text'], a21h['keywords'], a21h['metadata']['citation']))

# ===== ARTICLE 23 =====
e = by_id['income_tax_art23']
chunks.append(chunk("chunk_art23", None, 23, None, CHAP, CHAP3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 24 =====
e = by_id['income_tax_art24']
chunks.append(chunk("chunk_art24", None, 24, None, CHAP, CHAP3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 25 (main: merge a+b; sub: b only, a short) =====
a25a = by_id['income_tax_art25_a']
a25b = by_id['income_tax_art25_b']
merged_25 = a25a['text'] + "\n" + a25b['text']
kw_25 = list(dict.fromkeys(a25a['keywords'] + a25b['keywords']))
chunks.append(chunk("chunk_art25", None, 25, None, CHAP, CHAP3, "main",
    merged_25, kw_25, "المادة 25 من قانون ضريبة الدخل"))

chunks.append(chunk("chunk_art25_b", "chunk_art25", 25, "ب", CHAP, CHAP3, "sub",
    a25b['text'], a25b['keywords'], a25b['metadata']['citation']))

# ===== ARTICLE 26 =====
e = by_id['income_tax_art26']
chunks.append(chunk("chunk_art26", None, 26, None, CHAP, CHAP3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 27 (intro incomplete; sub: c with items, d, h) =====
a27_intro = by_id['income_tax_art27_intro']
a27c = by_id['income_tax_art27_c']
a27d = by_id['income_tax_art27_d']
a27h = by_id['income_tax_art27_h']

# Main: merge intro + c text + d + h
merged_27 = a27_intro['text'] + "\n" + a27c['text'] + "\n" + a27d['text'] + "\n" + a27h['text']
kw_27 = list(dict.fromkeys(a27_intro['keywords'] + a27c['keywords'] + a27d['keywords'] + a27h['keywords']))
chunks.append(chunk("chunk_art27", None, 27, None, CHAP, CHAP3, "main",
    merged_27, kw_27, "المادة 27 من قانون ضريبة الدخل",
    meta={"incomplete_text": True}))

# Sub: c - committee composition with items
PFX27 = "المادة 27 - تشكيل لجنة فرض الضريبة:"
items_27c = a27c['text'] + "\n" + "\n".join(a27c['items'])
chunks.append(chunk("chunk_art27_c", "chunk_art27", 27, "ج", CHAP, CHAP3, "sub",
    items_27c, a27c['keywords'], a27c['metadata']['citation']))

# Sub: d - procedures
chunks.append(chunk("chunk_art27_d", "chunk_art27", 27, "د", CHAP, CHAP3, "sub",
    a27d['text'], a27d['keywords'], a27d['metadata']['citation']))

# Sub: h - public sector
chunks.append(chunk("chunk_art27_h", "chunk_art27", 27, "هـ", CHAP, CHAP3, "sub",
    a27h['text'], a27h['keywords'], a27h['metadata']['citation']))

# Sub: art27 notification
a27_notif = by_id['income_tax_art27_notification']
chunks.append(chunk("chunk_art27_notification", "chunk_art27", 27, None, CHAP, CHAP3, "sub",
    a27_notif['text'], a27_notif['keywords'], a27_notif['metadata']['citation']))

# ===== ARTICLE 28 (main: merge a+b) =====
a28a = by_id['income_tax_art28_a']
a28b = by_id['income_tax_art28_b']
merged_28 = a28a['text'] + "\n" + a28b['text']
kw_28 = list(dict.fromkeys(a28a['keywords'] + a28b['keywords']))
chunks.append(chunk("chunk_art28", None, 28, None, CHAP, CHAP3, "main",
    merged_28, kw_28, "المادة 28 من قانون ضريبة الدخل"))

# ===== ARTICLE 29 (main: merge a+b+powers; sub: a, powers) =====
a29a = by_id['income_tax_art29_a']
a29b = by_id['income_tax_art29_b']
a29p = by_id['income_tax_art29_powers']
merged_29 = a29a['text'] + "\n" + a29b['text'] + "\n" + a29p['text']
kw_29 = list(dict.fromkeys(a29a['keywords'] + a29b['keywords'] + a29p['keywords']))
chunks.append(chunk("chunk_art29", None, 29, None, CHAP, CHAP3, "main",
    merged_29, kw_29, "المادة 29 من قانون ضريبة الدخل"))

chunks.append(chunk("chunk_art29_a", "chunk_art29", 29, "أ", CHAP, CHAP3, "sub",
    a29a['text'], a29a['keywords'], a29a['metadata']['citation']))

chunks.append(chunk("chunk_art29_powers", "chunk_art29", 29, None, CHAP, CHAP3, "sub",
    a29p['text'], a29p['keywords'], a29p['metadata']['citation']))

# ===== ARTICLE 30 (main + sub: penalty) =====
e = by_id['income_tax_art30']
chunks.append(chunk("chunk_art30", None, 30, None, CHAP, CHAP3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# Sub: penalty for refusing to provide documents
art30_penalty = "المادة 30 - عقوبة رفض تقديم المعلومات: كل من تكون لديه المعلومات والوثائق التي تطلبها الدوائر المالية بخصوص الفقرة السابقة ويرفض إعطائها يعاقب بغرامة نقدية قدرها /5000/ ليرة سورية عن كل مخالفة بقرار من وزير المالية وفي حال التكرار تضاعف الغرامات"
chunks.append(chunk("chunk_art30_penalty", "chunk_art30", 30, None, CHAP, CHAP3, "sub",
    art30_penalty, ["غرامة نقدية", "5000 ليرة سورية", "رفض إعطاء معلومات", "تضاعف الغرامات", "وزير المالية"],
    "المادة 30 من قانون ضريبة الدخل - عقوبة رفض المعلومات"))

# ===== ARTICLE 31 (main: merge a+b1; sub: a, b1, b2+c+d) =====
a31a = by_id['income_tax_art31_a']
a31b1 = by_id['income_tax_art31_b1']
a31b2 = by_id['income_tax_art31_b2']
a31c = by_id['income_tax_art31_c']
a31d = by_id['income_tax_art31_d']

# Main: merge a + b1 (core: finality + interest)
merged_31 = a31a['text'] + "\n" + a31b1['text']
kw_31 = list(dict.fromkeys(a31a['keywords'] + a31b1['keywords']))
chunks.append(chunk("chunk_art31", None, 31, None, CHAP, CHAP3, "main",
    merged_31, kw_31, "المادة 31 من قانون ضريبة الدخل"))

# Sub: a - finality of assessments + notification
chunks.append(chunk("chunk_art31_a", "chunk_art31", 31, "أ", CHAP, CHAP3, "sub",
    a31a['text'], a31a['keywords'], a31a['metadata']['citation']))

# Sub: b1 - interest rate on unpaid taxes
chunks.append(chunk("chunk_art31_b1", "chunk_art31", 31, "ب", CHAP, CHAP3, "sub",
    a31b1['text'], a31b1['keywords'], a31b1['metadata']['citation']))

# Sub: b2+c+d - interest details (short clauses merged)
merged_31_bcd = a31b2['text'] + "\n" + a31c['text'] + "\n" + a31d['text']
kw_31_bcd = list(dict.fromkeys(a31b2['keywords'] + a31c['keywords'] + a31d['keywords']))
chunks.append(chunk("chunk_art31_interest_details", "chunk_art31", 31, None, CHAP, CHAP3, "sub",
    merged_31_bcd, kw_31_bcd,
    "المادة 31 الفقرات (ب/2، ج، د) من قانون ضريبة الدخل"))

# ===== ARTICLE 32 (main: merge a+h+finality; sub: finality, h) =====
a32a = by_id['income_tax_art32_a']
a32h = by_id['income_tax_art32_h']
a32f = by_id['income_tax_art32_finality']

merged_32 = a32a['text'] + "\n" + a32h['text'] + "\n" + a32f['text']
kw_32 = list(dict.fromkeys(a32a['keywords'] + a32h['keywords'] + a32f['keywords']))
chunks.append(chunk("chunk_art32", None, 32, None, CHAP, CHAP3, "main",
    merged_32, kw_32, "المادة 32 من قانون ضريبة الدخل",
    meta={"incomplete_text": True}))

# Sub: 5-year finality rule (distinct searchable concept)
chunks.append(chunk("chunk_art32_finality", "chunk_art32", 32, None, CHAP, CHAP3, "sub",
    a32f['text'], a32f['keywords'], a32f['metadata']['citation']))

# Sub: h - committee sessions location
chunks.append(chunk("chunk_art32_h", "chunk_art32", 32, "هـ", CHAP, CHAP3, "sub",
    a32h['text'], a32h['keywords'], a32h['metadata']['citation']))

# ===== ARTICLE 33 (new section: الفصل الرابع) =====
CHAP4 = "الفصل الرابع - إعادة النظر والتصحيح والطعن"

a33a = by_id['income_tax_art33_a']
a33g = by_id['income_tax_art33_a_grounds']
a33b = by_id['income_tax_art33_b']

# Main: merge a + b (overview of review rights and deadlines)
merged_33 = a33a['text'] + "\n" + a33b['text']
kw_33 = list(dict.fromkeys(a33a['keywords'] + a33b['keywords']))
chunks.append(chunk("chunk_art33", None, 33, None, CHAP, CHAP4, "main",
    merged_33, kw_33, "المادة 33 من قانون ضريبة الدخل"))

# Sub: grounds for review (enumeration)
PFX33 = "المادة 33 - حالات طلب إعادة النظر من قبل الدوائر المالية:"
chunks.append(chunk("chunk_art33_grounds", "chunk_art33", 33, "أ", CHAP, CHAP4, "sub",
    PFX33, a33g['keywords'],
    a33g['metadata']['citation'], prefix=PFX33, items=a33g['items']))

# Sub: b - deadline + finality
chunks.append(chunk("chunk_art33_b", "chunk_art33", 33, "ب", CHAP, CHAP4, "sub",
    a33b['text'], a33b['keywords'], a33b['metadata']['citation']))

# ===== ARTICLE 34 (main: merge a+b; short clauses) =====
a34a = by_id['income_tax_art34_a']
a34b = by_id['income_tax_art34_b']
merged_34 = a34a['text'] + "\n" + a34b['text']
kw_34 = list(dict.fromkeys(a34a['keywords'] + a34b['keywords']))
chunks.append(chunk("chunk_art34", None, 34, None, CHAP, CHAP4, "main",
    merged_34, kw_34, "المادة 34 من قانون ضريبة الدخل"))

# ===== ARTICLE 35 (main: merge a+b; sub: a) =====
a35a = by_id['income_tax_art35_a']
a35b = by_id['income_tax_art35_b']
merged_35 = a35a['text'] + "\n" + a35b['text']
kw_35 = list(dict.fromkeys(a35a['keywords'] + a35b['keywords']))
chunks.append(chunk("chunk_art35", None, 35, None, CHAP, CHAP4, "main",
    merged_35, kw_35, "المادة 35 من قانون ضريبة الدخل"))

# Sub: a - review procedure, experts, advance payment
chunks.append(chunk("chunk_art35_a", "chunk_art35", 35, "أ", CHAP, CHAP4, "sub",
    a35a['text'], a35a['keywords'], a35a['metadata']['citation']))

# ===== ARTICLE 36 (single main chunk) =====
e = by_id['income_tax_art36']
chunks.append(chunk("chunk_art36", None, 36, None, CHAP, CHAP4, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 37 (complex: correction + committee + procedures) =====
a37a = by_id['income_tax_art37_a']
a37com = by_id['income_tax_art37_committee']
a37ps = by_id['income_tax_art37_public_sector']
a37b = by_id['income_tax_art37_b']
a37c = by_id['income_tax_art37_c']
a37d = by_id['income_tax_art37_d']

# Main: merge a (cases) + d (quorum rules)
a37a_full = a37a['text'] + "\n" + "\n".join(a37a['items'])
merged_37 = a37a_full + "\n" + a37d['text']
kw_37 = list(dict.fromkeys(a37a['keywords'] + a37d['keywords']))
chunks.append(chunk("chunk_art37", None, 37, None, CHAP, CHAP4, "main",
    merged_37, kw_37, "المادة 37 من قانون ضريبة الدخل"))

# Sub: committee composition (enumeration)
PFX37 = "المادة 37 - تشكيل لجنة إعادة النظر:"
chunks.append(chunk("chunk_art37_committee", "chunk_art37", 37, None, CHAP, CHAP4, "sub",
    PFX37, a37com['keywords'],
    a37com['metadata']['citation'], prefix=PFX37, items=a37com['items']))

# Sub: b - additional committee + c work distribution
merged_37_bc = a37b['text'] + "\n" + a37c['text']
kw_37_bc = list(dict.fromkeys(a37b['keywords'] + a37c['keywords']))
chunks.append(chunk("chunk_art37_b", "chunk_art37", 37, "ب", CHAP, CHAP4, "sub",
    merged_37_bc, kw_37_bc, a37b['metadata']['citation']))

# Sub: public sector representative note
chunks.append(chunk("chunk_art37_public_sector", "chunk_art37", 37, None, CHAP, CHAP4, "sub",
    a37ps['text'], a37ps['keywords'], a37ps['metadata']['citation']))

# ===== ARTICLE 40 (main: merge a + b items) =====
a40a = by_id['income_tax_art40_a']
a40b = by_id['income_tax_art40_b']
merged_40 = a40a['text'] + "\n" + a40b['text'] + "\n" + "\n".join(a40b['items'])
kw_40 = list(dict.fromkeys(a40a['keywords'] + a40b['keywords']))
chunks.append(chunk("chunk_art40", None, 40, None, CHAP, CHAP4, "main",
    merged_40, kw_40, "المادة 40 من قانون ضريبة الدخل"))

# ===== ARTICLE 41 (new chapter: الباب الثاني - الدخل المقطوع) =====
CHAP2 = "الباب الثاني"

a41a = by_id['income_tax_art41_a']
a41b = by_id['income_tax_art41_b']
merged_41 = a41a['text'] + "\n" + a41b['text']
kw_41 = list(dict.fromkeys(a41a['keywords'] + a41b['keywords']))
chunks.append(chunk("chunk_art41", None, 41, None, CHAP2, None, "main",
    merged_41, kw_41, "المادة 41 من قانون ضريبة الدخل"))

# ===== ARTICLE 37 ADDITIONS (cases 3-5 + deadline) =====
a37a2 = by_id['income_tax_art37_cases_additional']
PFX37A2 = "المادة 37 - أ - حالات تقديم طلب التصحيح (تكملة):"
chunks.append(chunk("chunk_art37_cases_additional", "chunk_art37", 37, "أ", CHAP, CHAP4, "sub",
    PFX37A2, a37a2['keywords'],
    a37a2['metadata']['citation'], prefix=PFX37A2, items=a37a2['items']))

a37dl = by_id['income_tax_art37_deadline']
chunks.append(chunk("chunk_art37_deadline", "chunk_art37", 37, None, CHAP, CHAP4, "sub",
    a37dl['text'], a37dl['keywords'], a37dl['metadata']['citation']))

# ===== ARTICLE 42 (single main chunk) =====
e = by_id['income_tax_art42']
chunks.append(chunk("chunk_art42", None, 42, None, CHAP2, None, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 43 (short - clause أ only so far) =====
e = by_id['income_tax_art43_a']
chunks.append(chunk("chunk_art43", None, 43, "أ", CHAP2, None, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 44 (main: merge أ+ب; ب too short for sub) =====
a44a = by_id['income_tax_art44_a']
a44b = by_id['income_tax_art44_b']
merged_44 = a44a['text'] + "\n" + a44b['text']
kw_44 = list(dict.fromkeys(a44a['keywords'] + a44b['keywords']))
chunks.append(chunk("chunk_art44", None, 44, None, CHAP2, None, "main",
    merged_44, kw_44, "المادة 44 من قانون ضريبة الدخل"))

# ===== ARTICLE 45 (main: merge a+b+c+d; sub: a, b, c+d merged) =====
a45a = by_id['income_tax_art45_a']
a45b = by_id['income_tax_art45_b']
a45c = by_id['income_tax_art45_c']
a45d = by_id['income_tax_art45_d']

# Main: merge all clauses
merged_45 = a45a['text'] + "\n" + a45b['text'] + "\n" + a45c['text'] + "\n" + a45d['text']
kw_45 = list(dict.fromkeys(a45a['keywords'] + a45b['keywords'] + a45c['keywords'] + a45d['keywords']))
chunks.append(chunk("chunk_art45", None, 45, None, CHAP2, None, "main",
    merged_45, kw_45, "المادة 45 من قانون ضريبة الدخل"))

# Sub: a - doctors/engineers tax classification
chunks.append(chunk("chunk_art45_a", "chunk_art45", 45, "أ", CHAP2, None, "sub",
    a45a['text'], a45a['keywords'], a45a['metadata']['citation']))

# Sub: b - surgical fees + reclassification rules
chunks.append(chunk("chunk_art45_b", "chunk_art45", 45, "ب", CHAP2, None, "sub",
    a45b['text'], a45b['keywords'], a45b['metadata']['citation']))

# Sub: c+d merged - classification committee + expiry rules (related concepts)
merged_45_cd = a45c['text'] + "\n" + a45d['text']
kw_45_cd = list(dict.fromkeys(a45c['keywords'] + a45d['keywords']))
chunks.append(chunk("chunk_art45_cd", "chunk_art45", 45, "ج-د", CHAP2, None, "sub",
    merged_45_cd, kw_45_cd, "المادة 45 الفقرتان (ج، د) من قانون ضريبة الدخل"))

# ===== ARTICLE 46 (single main chunk) =====
e = by_id['income_tax_art46']
chunks.append(chunk("chunk_art46", None, 46, None, CHAP2, None, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 47 (main: merge a+b+c+d; short clauses) =====
a47a = by_id['income_tax_art47_a']
a47b = by_id['income_tax_art47_b']
a47c = by_id['income_tax_art47_c']
a47d = by_id['income_tax_art47_d']
merged_47 = a47a['text'] + "\n" + a47b['text'] + "\n" + a47c['text'] + "\n" + a47d['text']
kw_47 = list(dict.fromkeys(a47a['keywords'] + a47b['keywords'] + a47c['keywords'] + a47d['keywords']))
chunks.append(chunk("chunk_art47", None, 47, None, CHAP2, None, "main",
    merged_47, kw_47, "المادة 47 من قانون ضريبة الدخل"))

# ===== ARTICLE 48 (main: merge committee+b+c; sub: b reclassification) =====
a48_com = by_id['income_tax_art48_committee']
a48b = by_id['income_tax_art48_b']
a48c = by_id['income_tax_art48_c']

# Main: merge all
com_text = a48_com['text'] + "\n" + "\n".join(a48_com['items'])
merged_48 = com_text + "\n" + a48b['text'] + "\n" + a48c['text']
kw_48 = list(dict.fromkeys(a48_com['keywords'] + a48b['keywords'] + a48c['keywords']))
chunks.append(chunk("chunk_art48", None, 48, None, CHAP2, None, "main",
    merged_48, kw_48, "المادة 48 من قانون ضريبة الدخل",
    meta={"incomplete_text": True}))

# Sub: b - reclassification and cessation rules
chunks.append(chunk("chunk_art48_b", "chunk_art48", 48, "ب", CHAP2, None, "sub",
    a48b['text'], a48b['keywords'], a48b['metadata']['citation']))

# ===== ARTICLE 49 (complex: classification appeals + tax payment + vehicles) =====
a49a = by_id['income_tax_art49_a']
a49b = by_id['income_tax_art49_b']
a49c = by_id['income_tax_art49_c']
a49d = by_id['income_tax_art49_d']
a49_tax = by_id['income_tax_art49_tax_due']
a49_vc = by_id['income_tax_art49_vehicles_c']
a49_vd = by_id['income_tax_art49_vehicles_d']
a49_vh = by_id['income_tax_art49_vehicles_h']
a49_vw = by_id['income_tax_art49_vehicles_w']

# Main: merge appeals overview (a+b+d) + tax payment
merged_49 = a49a['text'] + "\n" + a49b['text'] + "\n" + a49d['text'] + "\n" + a49_tax['text']
kw_49 = list(dict.fromkeys(a49a['keywords'] + a49b['keywords'] + a49d['keywords'] + a49_tax['keywords']))
chunks.append(chunk("chunk_art49", None, 49, None, CHAP2, None, "main",
    merged_49, kw_49, "المادة 49 من قانون ضريبة الدخل"))

# Sub: c - deposit/guarantee rules
chunks.append(chunk("chunk_art49_c", "chunk_art49", 49, "ج", CHAP2, None, "sub",
    a49c['text'], a49c['keywords'], a49c['metadata']['citation']))

# Sub: vehicles (merge c+d+h+w)
merged_49_v = a49_vc['text'] + "\n" + a49_vd['text'] + "\n" + a49_vh['text'] + "\n" + a49_vw['text']
kw_49_v = list(dict.fromkeys(a49_vc['keywords'] + a49_vd['keywords'] + a49_vh['keywords'] + a49_vw['keywords']))
chunks.append(chunk("chunk_art49_vehicles", "chunk_art49", 49, None, CHAP2, None, "sub",
    merged_49_v, kw_49_v, "المادة 49 من قانون ضريبة الدخل - أحكام السيارات"))

# ===== ARTICLE 50 (complex: committee + tax rules + appeals) =====
a50a = by_id['income_tax_art50_a']
a50a2 = by_id['income_tax_art50_a2']
a50a3 = by_id['income_tax_art50_a3']
a50b = by_id['income_tax_art50_b']
a50c = by_id['income_tax_art50_c']
a50_2 = by_id['income_tax_art50_2']
a50_3 = by_id['income_tax_art50_3']
a50_4 = by_id['income_tax_art50_4']

# Main: committee composition (a + members) + b + c
com_text_50 = a50a['text'] + "\n" + "\n".join(a50a['items']) + "\n" + a50a2['text'] + "\n" + a50a3['text']
merged_50_main = com_text_50 + "\n" + a50b['text'] + "\n" + a50c['text']
kw_50_main = list(dict.fromkeys(a50a['keywords'] + a50a2['keywords'] + a50a3['keywords'] + a50b['keywords'] + a50c['keywords']))
chunks.append(chunk("chunk_art50", None, 50, None, CHAP2, None, "main",
    merged_50_main, kw_50_main, "المادة 50 من قانون ضريبة الدخل"))

# Sub: committee member 3 (detailed selection process)
chunks.append(chunk("chunk_art50_a3", "chunk_art50", 50, None, CHAP2, None, "sub",
    a50a3['text'], a50a3['keywords'], a50a3['metadata']['citation']))

# Sub: tax rules (2+3+4 - garbled OCR parts)
merged_50_tax = a50_2['text'] + "\n" + a50_3['text'] + "\n" + a50_4['text']
kw_50_tax = list(dict.fromkeys(a50_2['keywords'] + a50_3['keywords'] + a50_4['keywords']))
chunks.append(chunk("chunk_art50_tax", "chunk_art50", 50, None, CHAP2, None, "sub",
    merged_50_tax, kw_50_tax, "المادة 50 من قانون ضريبة الدخل - أحكام ضريبية",
    meta={"text_quality": "suspected_ocr_distortion"}))

# ===== ARTICLE 54 (main: merge a+b) =====
CHAP2_SEC3 = "الفصل الثالث - تحقيق الفريضة واستحقاقها وتحصيلها"
a54a = by_id['income_tax_art54_a']
a54b = by_id['income_tax_art54_b']
merged_54 = a54a['text'] + "\n" + a54b['text']
kw_54 = list(dict.fromkeys(a54a['keywords'] + a54b['keywords']))
chunks.append(chunk("chunk_art54", None, 54, None, CHAP2, CHAP2_SEC3, "main",
    merged_54, kw_54, "المادة 54 من قانون ضريبة الدخل"))

# Sub: a - detailed calculation rules (long enough)
chunks.append(chunk("chunk_art54_a", "chunk_art54", 54, "أ", CHAP2, CHAP2_SEC3, "sub",
    a54a['text'], a54a['keywords'], a54a['metadata']['citation']))

# ===== ARTICLE 55 (single main chunk) =====
e = by_id['income_tax_art55']
chunks.append(chunk("chunk_art55", None, 55, None, CHAP2, CHAP2_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 56 (single main chunk) =====
e = by_id['income_tax_art56']
chunks.append(chunk("chunk_art56", None, 56, None, CHAP2, CHAP2_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 57 (main: merge a1+a2; sub: a2 cases) =====
a57a1 = by_id['income_tax_art57_a1']
a57a2 = by_id['income_tax_art57_a2']

# Main: merge both parts
a57a2_full = a57a2['text'] + "\n" + "\n".join(a57a2['items'])
merged_57 = a57a1['text'] + "\n" + a57a2_full
kw_57 = list(dict.fromkeys(a57a1['keywords'] + a57a2['keywords']))
chunks.append(chunk("chunk_art57", None, 57, None, CHAP2, CHAP2_SEC3, "main",
    merged_57, kw_57, "المادة 57 من قانون ضريبة الدخل"))

# Sub: a2 cases (enumeration of events requiring declaration)
chunks.append(chunk("chunk_art57_a2", "chunk_art57", 57, "أ", CHAP2, CHAP2_SEC3, "sub",
    a57a2_full, a57a2['keywords'], a57a2['metadata']['citation']))

# ===== CHAPTER 4: MISCELLANEOUS PROVISIONS =====
CHAP2_SEC4 = "الفصل الرابع - الأحكام المختلفة"

# ===== ARTICLE 55 CH4 (single main chunk) =====
e = by_id['income_tax_art55_ch4']
chunks.append(chunk("chunk_art55_ch4", None, 55, None, CHAP2, CHAP2_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 56 CH4 (single main chunk) =====
e = by_id['income_tax_art56_ch4']
chunks.append(chunk("chunk_art56_ch4", None, 56, None, CHAP2, CHAP2_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 57 CH4 (single main chunk) =====
e = by_id['income_tax_art57_ch4']
chunks.append(chunk("chunk_art57_ch4", None, 57, None, CHAP2, CHAP2_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 58 (single main chunk) =====
e = by_id['income_tax_art58']
chunks.append(chunk("chunk_art58", None, 58, None, CHAP2, CHAP2_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 59 (single main chunk) =====
e = by_id['income_tax_art59']
chunks.append(chunk("chunk_art59", None, 59, "أ", CHAP2, CHAP2_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 24 CH4 (single main chunk) =====
e = by_id['income_tax_art24_ch4']
chunks.append(chunk("chunk_art24_ch4", None, 24, None, CHAP2, CHAP2_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 25 CH4 (single main chunk) =====
e = by_id['income_tax_art25_ch4']
chunks.append(chunk("chunk_art25_ch4", None, 25, None, CHAP2, CHAP2_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ==================== الباب الرابع ====================
BAB4 = "الباب الرابع"
BAB4_SEC1 = "الفصل الأول - الدخل الخاضع للضريبة ونسبة الضريبة واستحقاقاتها"

# ===== ARTICLE 26 B4 (single main chunk) =====
e = by_id['income_tax_art26_b4']
chunks.append(chunk("chunk_art26_b4", None, 26, None, BAB4, BAB4_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 27 B4 - EXEMPTIONS (main + sub) =====
e = by_id['income_tax_art27_b4_exempt']
chunks.append(chunk("chunk_art27_b4", None, 27, "أ-د", BAB4, BAB4_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

e2 = by_id['income_tax_art27_b4_rates']
chunks.append(chunk("chunk_art27_b4_rates", "chunk_art27_b4", 27, "أحكام إضافية", BAB4, BAB4_SEC1, "sub",
    e2['text'], e2['keywords'], e2['metadata']['citation'],
    meta={"duplicate_article_no": True, "note": "محتوى مختلط من OCR"}))

# ===== ARTICLE 28 B4 (single main chunk) =====
e = by_id['income_tax_art28_b4']
chunks.append(chunk("chunk_art28_b4", None, 28, None, BAB4, BAB4_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 29 B4 (single main chunk) =====
e = by_id['income_tax_art29_b4']
chunks.append(chunk("chunk_art29_b4", None, 29, None, BAB4, BAB4_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 71 (single main chunk) =====
e = by_id['income_tax_art71']
chunks.append(chunk("chunk_art71", None, 71, None, BAB4, BAB4_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 72 (single main chunk) =====
e = by_id['income_tax_art72']
chunks.append(chunk("chunk_art72", None, 72, None, BAB4, BAB4_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 73 (single main chunk) =====
e = by_id['income_tax_art73']
chunks.append(chunk("chunk_art73", None, 73, None, BAB4, BAB4_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 27 B4 - EXEMPTIONS CONT. (هـ-ح) =====
e = by_id['income_tax_art27_b4_exempt2']
chunks.append(chunk("chunk_art27_b4_exempt2", "chunk_art27_b4", 27, "هـ-ح", BAB4, BAB4_SEC1, "sub",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ==================== الباب الرابع - الفصل الثاني ====================
BAB4_SEC2 = "الفصل الثاني - واجبات صاحب العمل والعامل"

# ===== ARTICLE 74 (single main chunk) =====
e = by_id['income_tax_art74']
chunks.append(chunk("chunk_art74", None, 74, None, BAB4, BAB4_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 78 (main + sub for brackets) =====
e = by_id['income_tax_art78']
full = e['text']
intro_end = full.index('\n5%')
intro = full[:intro_end]
brackets = full[intro_end+1:]

chunks.append(chunk("chunk_art78", None, 78, None, BAB4, BAB4_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

chunks.append(chunk("chunk_art78_brackets", "chunk_art78", 78, "شرائح", BAB4, BAB4_SEC2, "sub",
    brackets, ["شرائح ضريبية", "5%", "7%", "9%", "11%", "13%", "20%"],
    e['metadata']['citation']))

# ===== ARTICLE 79 (single main chunk) =====
e = by_id['income_tax_art79']
chunks.append(chunk("chunk_art79", None, 79, None, BAB4, BAB4_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 70 (main + subs) =====
e_a = by_id['income_tax_art70_a']
e_b = by_id['income_tax_art70_b']
e_m = by_id['income_tax_art70_mixed']

# main: merge أ + ب
merged_70 = e_a['text'] + "\n" + e_b['text']
chunks.append(chunk("chunk_art70", None, 70, None, BAB4, BAB4_SEC1, "main",
    merged_70, e_a['keywords'] + e_b['keywords'],
    e_a['metadata']['citation']))

# sub: mixed content
chunks.append(chunk("chunk_art70_mixed", "chunk_art70", 70, "محتوى مختلط", BAB4, BAB4_SEC2, "sub",
    e_m['text'], e_m['keywords'], e_m['metadata']['citation'],
    meta={"note": "محتوى مختلط من OCR"}))

# ===== ARTICLE 78 PENALTIES (main + sub) =====
e_a = by_id['income_tax_art78_penalties_a']
e_b = by_id['income_tax_art78_penalties_b']
merged_78p = e_a['text'] + "\n" + e_b['text']
chunks.append(chunk("chunk_art78_penalties", None, 78, "أ-ب", BAB4, BAB4_SEC2, "main",
    merged_78p, e_a['keywords'] + e_b['keywords'],
    e_a['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ==================== الباب الرابع - الفصل الثالث ====================
BAB4_SEC3 = "الفصل الثالث - تحقق الضريبة وتأثيرها"

# ===== ARTICLE 79 SEC3 (single main chunk) =====
e = by_id['income_tax_art79_sec3']
chunks.append(chunk("chunk_art79_sec3", None, 79, None, BAB4, BAB4_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 76 (single main chunk) =====
e = by_id['income_tax_art76']
chunks.append(chunk("chunk_art76", None, 76, None, BAB4, BAB4_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 77 (single main chunk) =====
e = by_id['income_tax_art77']
chunks.append(chunk("chunk_art77", None, 77, None, BAB4, BAB4_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 80 (single main chunk) =====
e = by_id['income_tax_art80']
chunks.append(chunk("chunk_art80", None, 80, None, BAB4, BAB4_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 75 (single main chunk) =====
e = by_id['income_tax_art75']
chunks.append(chunk("chunk_art75", None, 75, None, BAB4, BAB4_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 81 (single main chunk) =====
e = by_id['income_tax_art81']
chunks.append(chunk("chunk_art81", None, 81, None, BAB4, BAB4_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 82 (single main chunk) =====
e = by_id['income_tax_art82']
chunks.append(chunk("chunk_art82", None, 82, None, BAB4, BAB4_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ==================== الباب الخامس ====================
BAB5 = "الباب الخامس"
BAB5_SEC1 = "الفصل الأول - أحكام عامة"

# ===== ARTICLE 83 (single main chunk) =====
e = by_id['income_tax_art83']
chunks.append(chunk("chunk_art83", None, 83, "أ", BAB5, BAB5_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

BAB5_SEC2 = "الفصل الثاني - الأموال السورية المتداولة"

# ===== ARTICLE 85 (single main chunk) =====
e = by_id['income_tax_art85']
chunks.append(chunk("chunk_art85", None, 85, None, BAB5, BAB5_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 86 (single main chunk) =====
e = by_id['income_tax_art86']
chunks.append(chunk("chunk_art86", None, 86, None, BAB5, BAB5_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 87 (single main chunk) =====
e = by_id['income_tax_art87']
chunks.append(chunk("chunk_art87", None, 87, None, BAB5, BAB5_SEC2, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

BAB5_SEC3 = "الفصل الثالث - الأموال الأجنبية المتداولة"

# ===== ARTICLE 91 (single main chunk) =====
e = by_id['income_tax_art91']
chunks.append(chunk("chunk_art91", None, 91, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 92 (single main chunk) =====
e = by_id['income_tax_art92']
chunks.append(chunk("chunk_art92", None, 92, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 93 (single main chunk) =====
e = by_id['income_tax_art93']
chunks.append(chunk("chunk_art93", None, 93, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 94 (single main chunk) =====
e = by_id['income_tax_art94']
chunks.append(chunk("chunk_art94", None, 94, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 95 (single main chunk) =====
e = by_id['income_tax_art95']
chunks.append(chunk("chunk_art95", None, 95, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 96 (single main chunk) =====
e = by_id['income_tax_art96']
chunks.append(chunk("chunk_art96", None, 96, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 97 (single main chunk) =====
e = by_id['income_tax_art97']
chunks.append(chunk("chunk_art97", None, 97, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 98 (single main chunk) =====
e = by_id['income_tax_art98']
chunks.append(chunk("chunk_art98", None, 98, None, BAB5, BAB5_SEC3, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

BAB5_SEC4 = "الفصل الرابع - طرق المراجعة"

# ===== ARTICLE 103 (single main chunk) =====
e = by_id['income_tax_art103']
chunks.append(chunk("chunk_art103", None, 103, None, BAB5, BAB5_SEC4, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

BAB5_SEC5 = "الفصل الخامس - الإعفاءات"

# ===== ARTICLE 104 (single main chunk) =====
e = by_id['income_tax_art104']
chunks.append(chunk("chunk_art104", None, 104, None, BAB5, BAB5_SEC5, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 105 (single main chunk) =====
e = by_id['income_tax_art105']
chunks.append(chunk("chunk_art105", None, 105, None, BAB5, BAB5_SEC5, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 106 (single main chunk) =====
e = by_id['income_tax_art106']
chunks.append(chunk("chunk_art106", None, 106, None, BAB5, BAB5_SEC5, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ==================== الباب السادس ====================
BAB6 = "الباب السادس"
BAB6_SEC = "أحكام عامة ومشتركة"

# ===== ARTICLE 107 (single main chunk) =====
e = by_id['income_tax_art107']
chunks.append(chunk("chunk_art107", None, 107, "أ", BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 108 (single main chunk) =====
e = by_id['income_tax_art108']
chunks.append(chunk("chunk_art108", None, 108, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 109 (single main chunk) =====
e = by_id['income_tax_art109']
chunks.append(chunk("chunk_art109", None, 109, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 110 (single main chunk) =====
e = by_id['income_tax_art110']
chunks.append(chunk("chunk_art110", None, 110, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 111 (single main chunk) =====
e = by_id['income_tax_art111']
chunks.append(chunk("chunk_art111", None, 111, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 112 (single main chunk) =====
e = by_id['income_tax_art112']
chunks.append(chunk("chunk_art112", None, 112, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 113 (single main chunk) =====
e = by_id['income_tax_art113']
chunks.append(chunk("chunk_art113", None, 113, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 114 (single main chunk) =====
e = by_id['income_tax_art114']
chunks.append(chunk("chunk_art114", None, 114, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 115 (single main chunk) =====
e = by_id['income_tax_art115']
chunks.append(chunk("chunk_art115", None, 115, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 116 (single main chunk) =====
e = by_id['income_tax_art116']
chunks.append(chunk("chunk_art116", None, 116, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 117 (single main chunk) =====
e = by_id['income_tax_art117']
chunks.append(chunk("chunk_art117", None, 117, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 118 (single main chunk) =====
e = by_id['income_tax_art118']
chunks.append(chunk("chunk_art118", None, 118, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 119 (single main chunk) =====
e = by_id['income_tax_art119']
chunks.append(chunk("chunk_art119", None, 119, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 107 B+C (sub of art107) =====
e = by_id['income_tax_art107_bc']
chunks.append(chunk("chunk_art107_bc", "chunk_art107", 107, "ب-ج", BAB6, BAB6_SEC, "sub",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 118 B6 (duplicate - single main chunk) =====
e = by_id['income_tax_art118_b6']
chunks.append(chunk("chunk_art118_b6", None, 118, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 119 B6 (duplicate - single main chunk) =====
e = by_id['income_tax_art119_b6']
chunks.append(chunk("chunk_art119_b6", None, 119, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 120 (single main chunk) =====
e = by_id['income_tax_art120']
chunks.append(chunk("chunk_art120", None, 120, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 121 (single main chunk) =====
e = by_id['income_tax_art121']
chunks.append(chunk("chunk_art121", None, 121, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 124 (single main chunk) =====
e = by_id['income_tax_art124']
chunks.append(chunk("chunk_art124", None, 124, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 125 (single main chunk) =====
e = by_id['income_tax_art125']
chunks.append(chunk("chunk_art125", None, 125, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 126 (single main chunk) =====
e = by_id['income_tax_art126']
chunks.append(chunk("chunk_art126", None, 126, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 127 (single main chunk) =====
e = by_id['income_tax_art127']
chunks.append(chunk("chunk_art127", None, 127, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 128 (single main chunk) =====
e = by_id['income_tax_art128']
chunks.append(chunk("chunk_art128", None, 128, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 129 (single main chunk) =====
e = by_id['income_tax_art129']
chunks.append(chunk("chunk_art129", None, 129, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 130 (single main chunk) =====
e = by_id['income_tax_art130']
chunks.append(chunk("chunk_art130", None, 130, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 131 (single main chunk) =====
e = by_id['income_tax_art131']
chunks.append(chunk("chunk_art131", None, 131, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation']))

# ===== ARTICLE 128 B6 (duplicate - single main chunk) =====
e = by_id['income_tax_art128_b6']
chunks.append(chunk("chunk_art128_b6", None, 128, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===== ARTICLE 129 B6 (duplicate - single main chunk) =====
e = by_id['income_tax_art129_b6']
chunks.append(chunk("chunk_art129_b6", None, 129, None, BAB6, BAB6_SEC, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    meta={"duplicate_article_no": True}))

# ===========================================================================
# قانون الاستعلام الضريبي رقم 25 لعام 2003
# ===========================================================================
TI_LAW = "tax_investigation"
TI_CH1 = "الفصل الأول"
TI_SEC1 = "تعاريف"
TI_CH2 = "الفصل الثاني"
TI_SEC2 = "الاستعلام الضريبي"

# ===== PREAMBLE (tax investigation) =====
e = by_id['tax_inv_intro']
chunks.append(chunk("chunk_ti_intro", None, None, None, None, None, "main",
    e['text'], e['keywords'], "مقدمة قانون الاستعلام الضريبي رقم 25 لعام 2003",
    law_id=TI_LAW))

# ===== ARTICLE 1 (tax investigation - definitions) =====
e = by_id['tax_inv_art1']
chunks.append(chunk("chunk_ti_art1", None, 1, None, TI_CH1, TI_SEC1, "main",
    e['text'], e['keywords'], e['metadata']['citation'],
    law_id=TI_LAW))

# ===== ARTICLE 2 (tax investigation - main: merge a+b) =====
a, b = by_id['tax_inv_art2_a'], by_id['tax_inv_art2_b']
merged = a['text'] + "\n" + b['text']
all_kw = list(dict.fromkeys(a['keywords'] + b['keywords']))
chunks.append(chunk("chunk_ti_art2", None, 2, None, TI_CH2, TI_SEC2, "main",
    merged, all_kw, "المادة 2 من قانون الاستعلام الضريبي رقم 25 لعام 2003",
    law_id=TI_LAW))
# Sub: a
chunks.append(chunk("chunk_ti_art2_a", "chunk_ti_art2", 2, "أ", TI_CH2, TI_SEC2, "sub",
    a['text'], a['keywords'], a['metadata']['citation'],
    law_id=TI_LAW))
# Sub: b
chunks.append(chunk("chunk_ti_art2_b", "chunk_ti_art2", 2, "ب", TI_CH2, TI_SEC2, "sub",
    b['text'], b['keywords'], b['metadata']['citation'],
    law_id=TI_LAW))

# ===== WRITE OUTPUT =====
with open(r'C:\Users\Owner\Desktop\Kratos\data1_chunked.json', 'w', encoding='utf-8') as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

# ===== REPORT =====
main_c = [c for c in chunks if c['chunk_level'] == 'main']
sub_c = [c for c in chunks if c['chunk_level'] == 'sub']
print(f"Total: {len(chunks)} chunks | Main: {len(main_c)} | Sub: {len(sub_c)}")
print(f"\n{'chunk_id':<42} {'level':<6} {'chars':>5}  notes")
print("-" * 75)
for c in chunks:
    n = c['char_count']
    flag = ''
    if n < 100: flag = '<< SHORT'
    elif n > 700: flag = '>> WATCH'
    elif 200 <= n <= 600: flag = 'optimal'
    print(f"  {c['chunk_id']:<40} {c['chunk_level']:<6} {n:>5}  {flag}")

sizes = [c['char_count'] for c in chunks]
print(f"\nMin: {min(sizes)} | Max: {max(sizes)} | Avg: {sum(sizes)//len(sizes)}")
short = sum(1 for s in sizes if s < 100)
opt = sum(1 for s in sizes if 200 <= s <= 600)
print(f"Short(<100): {short} | Optimal(200-600): {opt} | Total: {len(sizes)}")
