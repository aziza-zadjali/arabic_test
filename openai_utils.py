import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

# --- Word Meaning MCQ (معاني الكلمات) ---
PROMPT_HEADER = """
You are an expert in Arabic language assessment. Generate a pool of at least 10 Arabic words (not including the main word), all close in meaning to the main word, as possible distractors for an MCQ.

Instructions:
- Do NOT include the main word itself.
- All words must be close in meaning (synonyms or semantically related).
- Do not repeat words.
- Do not include words with the same root as the main word.
- Preferably, all generated choices should have the same Arabic morphological pattern (وزن) and the same number of letters as each other (e.g., all on وزن فعيل, or all on وزن مفاعل, etc.), but if this is not possible, you may relax this constraint and provide the best set of distractors you can.
- List the pattern (وزن) you used (if any), then list the words (each on a new line, no phrases).

Examples (use this format exactly):

وزن: تفعيل
كلمات:
تسويق
تغليف
تنفيذ
ترحيل

وزن: مفاعل
كلمات:
مآثر
مداخل
مراجع
محاسن

الكلمة الرئيسية: "الأصل"
الخيارات:
الصباح
السحر
الغروب
الظهيرة

الكلمة الرئيسية: "الدجى"
الخيارات:
الأصيل
الظلام
الشفق
النور

الكلمة الرئيسية: "الخضوع"
الخيارات:
الجحود
القعود
الركوع
الخشوع

الكلمة الرئيسية: "برع"
الخيارات:
فاق
رام
نام
خاف
"""

# --- Contextual Word Meaning MCQ (معنى الكلمة حسب السياق) ---
CONTEXTUAL_PROMPT = """
أنت خبير في إعداد أسئلة اللغة العربية. أنشئ سؤال اختيار من متعدد لمعنى كلمة في سياق جملة.
يتكون كل سؤال من جملة تحتوي على كلمة تحتها خط، والمطلوب منك أن تستنتج المعنى الأقرب لتلك الكلمة من بين البدائل الأربعة المعطاة، بحيث إذا استخدم البديل الصحيح فإنه سيعطي المعنى نفسه للجملة.

التعليمات:
- الجملة يجب أن تحتوي على كلمة واحدة تحتها خط.
- أعطِ أربعة خيارات للإجابة (أ، ب، ج، د).
- خيار واحد فقط هو الصحيح (مرادف أو الأقرب معنى في السياق).
- وضّح رمز الإجابة الصحيحة في نهاية السؤال.
- يُفضّل أن تكون جميع البدائل على نفس الوزن وعدد الحروف بعضها مع بعض (لكن ليس بالضرورة نفس الكلمة الرئيسية أو الكلمة التي تحتها خط). إذا لم يكن ذلك ممكنًا، يمكنك تخفيف هذا الشرط وتقديم أفضل مجموعة متاحة من البدائل.
- لا تدرج كلمات تشترك في الجذر مع الكلمة التي تحتها خط.

أمثلة:
1. ما رمز الكلمة الصحيحة التي تعتبر الأقرب معنى للكلمة التي تحتها خط في الجملة الموجودة في رأس السؤال؟
وَجَمَ الرجل بعد أن طُرد من عمله:
أ- شرد
ب- تعب
ج- عبس
د- سكت

نلاحظ أن رمز الإجابة الصحيحة هو (ج) حيث أن كلمة (عبس) هي الأقرب معنى لكلمة (وَجَم)، وفي حالة استخدامها في الجملة كبديل لكلمة (وجم) فإنها تعطي المعنى الصحيح للجملة، أما بقية البدائل الأخرى فلا تدل على المعنى الصحيح.

2. ما رمز الكلمة الصحيحة التي تعتبر الأقرب معنى للكلمة التي تحتها خط في الجملة الموجودة في رأس السؤال؟
يحظى المواطن بالحرية في بلاده:
أ- يدعو
ب- يفرح
ج- يحيى
د- ينال

نلاحظ أن رمز الإجابة الصحيحة هو (د) حيث أن كلمة (ينال) هي الأقرب معنى لكلمة (يحظى)، وفي حالة استخدامها في الجملة كبديل لكلمة (يحظى) فإنها تعطي المعنى الصحيح للجملة، أما بقية البدائل الأخرى فلا تدل على المعنى الصحيح.

3. بهرَ فلانٌ نظراءهُ:
أ- سادَ
ب- قادَ
ج- فاقَ
د- لامَ

نلاحظ أن رمز الإجابة الصحيحة هو (ج) حيث أن كلمة (فاقَ) هي الأقرب معنى لكلمة (بهرَ) في هذا السياق.

4. "والليل إذا عسعس":
أ- طال
ب- أظلم
ج- قصر
د- أمطر

نلاحظ أن رمز الإجابة الصحيحة هو (ب) حيث أن كلمة (أظلم) هي الأقرب معنى لكلمة (عسعس) في هذا السياق.

5. انبثق الماء غزيرا:
أ- انحصر
ب- انتشر
ج- انقطع
د- اندفع

نلاحظ أن رمز الإجابة الصحيحة هو (د) حيث أن كلمة (اندفع) هي الأقرب معنى لكلمة (انبثق) في هذا السياق.

6. اشرأبت الزرافات بأعناقها:
أ- امتدّت
ب- اشتدّت
ج- قصرت
د- ابتهجت

نلاحظ أن رمز الإجابة الصحيحة هو (أ) حيث أن كلمة (امتدّت) هي الأقرب معنى لكلمة (اشرأبت) في هذا السياق.
"""

def has_al(word):
    return word.strip().startswith("ال")

def ensure_al(words):
    return [w if w.startswith("ال") else "ال" + w for w in words]

def ensure_al_in_choices_contextual(choices, underlined_word):
    # Only add "ال" if the underlined word itself starts with "ال"
    if not underlined_word or not has_al(underlined_word):
        return choices
    ensured = []
    for c in choices:
        m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', c)
        if m:
            label, word = m.group(1), m.group(2)
            if not word.startswith("ال"):
                word = "ال" + word
            ensured.append(f"{label} {word}")
        else:
            ensured.append(c)
    return ensured

def normalize_al(word):
    return word[2:] if word.startswith("ال") else word

def filter_by_length(words):
    if not words:
        return []
    target_len = len(words[0])
    filtered = [w for w in words if len(w) == target_len]
    return filtered if len(filtered) >= 4 else words[:4]

def share_root(word1, word2):
    w1 = normalize_al(word1)
    w2 = normalize_al(word2)
    return w1[:3] == w2[:3] or w1[:4] == w2[:4]

def is_semantically_related(main_word, candidate, client, model="gpt-4.1"):
    prompt = f"""In Arabic, is "{normalize_al(candidate)}" a synonym (or the closest in meaning) to "{normalize_al(main_word)}"? Answer only with نعم (yes) or لا (no), or explain if close."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=20,
    )
    answer = response.choices[0].message.content.strip()
    if 'نعم' in answer:
        return True
    if 'قريب' in answer and 'لا' not in answer:
        return True
    return False

def extract_mcq_choices_and_answer(gpt_output, main_word):
    lines = gpt_output.strip().split('\n')
    choices = []
    correct = None
    for line in lines:
        m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', line.strip())
        if m:
            choices.append((m.group(1), m.group(2)))
        if line.strip().startswith("الإجابة الصحيحة"):
            correct = line.strip().split(":", 1)[-1].strip()
    filtered_choices = [(label, word) for label, word in choices if not share_root(main_word, word)]
    return filtered_choices, correct

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"
الأسئلة المرجعية: {reference_questions[:3]}
"""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=512,
    )
    gpt_output = response.choices[0].message.content.strip()
    choices, correct = extract_mcq_choices_and_answer(gpt_output, main_word)

    # Enforce "ال" if main word has it
    if has_al(main_word):
        choices = [(label, word if word.startswith("ال") else "ال" + word) for label, word in choices]
        if correct and not correct.split(")", 1)[-1].strip().startswith("ال"):
            correct_label = correct.split(")")[0]
            correct_word = correct.split(")", 1)[-1].strip()
            correct = f"{correct_label}) {'ال'+correct_word}"

    if len(choices) < 4 or not correct:
        candidate_words = [w for _, w in choices]
        filtered = filter_by_length(candidate_words)
        filtered = [w for w in filtered if not share_root(main_word, w)]
        correct_synonym = None
        distractors = []
        for w in filtered:
            if is_semantically_related(main_word, w, client) and not correct_synonym:
                correct_synonym = w
            else:
                distractors.append(w)
        if correct_synonym and len(distractors) >= 3:
            letters = ['أ', 'ب', 'ج', 'د']
            display_choices = [f"{letters[i]}) {w}" for i, w in enumerate([correct_synonym] + distractors[:3])]
            if has_al(main_word):
                display_choices = ensure_al_in_choices_contextual(display_choices, main_word)
            question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
            answer = display_choices[0]
            return question, answer, None
        return None, None, "تعذر توليد خيارات مناسبة."
    else:
        display_choices = [f"{label}) {word}" for label, word in choices]
        question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
        answer = correct
        return question, answer, None

def generate_meaning_test_llm(num_questions, reference_questions, grade):
    questions = []
    used_words = set()
    max_attempts = num_questions * 10
    attempts = 0
    prompt = (
        f"اقترح قائمة من 15 كلمة عربية مناسبة لاختبار معاني الكلمات للصف {grade} "
        "يُفضل أن تكون الكلمات شائعة في مناهج هذا الصف، وليست أسماء أعلام أو كلمات تخصصية."
        "اكتب كل كلمة في سطر منفصل، ولا تكرر الكلمات."
    )
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100,
    )
    candidate_words = [w.strip() for w in response.choices[0].message.content.strip().split('\n') if w.strip()]
    for main_word in candidate_words:
        if len(questions) >= num_questions:
            break
        if main_word in used_words:
            continue
        used_words.add(main_word)
        q, a, msg = generate_mcq_arabic_word_meaning(main_word, reference_questions, grade)
        if q and a:
            questions.append((q, a, msg))
    return questions

# --- Contextual Word Meaning MCQ (معنى الكلمة حسب السياق) ---
def extract_contextual_mcq_parts(gpt_output):
    question_part = gpt_output.split('\n\nنلاحظ')[0] if '\n\nنلاحظ' in gpt_output else gpt_output

    answer_letter = None
    answer_line = None
    for line in gpt_output.split('\n'):
        line = line.strip()
        match = re.search(r'رمز الإجابة الصحيحة(?: هو)?\s*[\:\(]?\s*([أ-د])[\)\s]*', line)
        if match:
            answer_letter = match.group(1)
            answer_line = f"الإجابة الصحيحة: ({answer_letter})"
            break
        match2 = re.search(r'الإجابة الصحيحة\s*[:\(]?\s*([أ-د])[\)\s]*', line)
        if match2:
            answer_letter = match2.group(1)
            answer_line = f"الإجابة الصحيحة: ({answer_letter})"
            break

    return question_part.strip(), answer_line

def extract_underlined_word(question_text):
    match = re.search(r'_(\w+)_', question_text)
    if match:
        return match.group(1)
    for word in question_text.split():
        if word.startswith("ال"):
            return word
    return None

def enforce_al_in_context_choices(choices, underlined_word):
    # Only add "ال" if the underlined word itself starts with "ال"
    if not underlined_word or not has_al(underlined_word):
        return choices
    ensured = []
    for c in choices:
        m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', c)
        if m:
            label, word = m.group(1), m.group(2)
            if not word.startswith("ال"):
                word = "ال" + word
            ensured.append(f"{label} {word}")
        else:
            ensured.append(c)
    return ensured

def share_root(word1, word2):
    w1 = normalize_al(word1)
    w2 = normalize_al(word2)
    return w1[:3] == w2[:3] or w1[:4] == w2[:4]

def generate_mcq_contextual_word_meaning(reference_questions, grade):
    prompt = CONTEXTUAL_PROMPT + "\n\nيرجى توليد سؤال واحد فقط بالتنسيق أعلاه."
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=400,
    )
    gpt_output = response.choices[0].message.content.strip()
    question_part, answer_line = extract_contextual_mcq_parts(gpt_output)

    # Extract choices and underlined word
    lines = question_part.split('\n')
    choices = []
    for line in lines:
        m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', line.strip())
        if m:
            choices.append(f"{m.group(1)}) {m.group(2)}")
    underlined_word = extract_underlined_word(question_part)

    # Remove choices with same root as underlined word
    filtered_choices = []
    for c in choices:
        m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', c)
        if m and underlined_word:
            if not share_root(underlined_word, m.group(2)):
                filtered_choices.append(c)
        else:
            filtered_choices.append(c)
    # Only enforce "ال" if underlined word has it
    filtered_choices = enforce_al_in_context_choices(filtered_choices, underlined_word)
    # Rebuild question_part with filtered choices
    question_lines = [l for l in lines if not re.match(r'^([أ-د][\)\-]?)\s*(.+)', l.strip())]
    question_part_final = "\n".join(question_lines + filtered_choices)
    return question_part_final.strip(), answer_line

def generate_contextual_test_llm(num_questions, reference_questions, grade):
    questions = []
    max_attempts = num_questions * 6
    attempts = 0
    while len(questions) < num_questions and attempts < max_attempts:
        attempts += 1
        q, answer_line = generate_mcq_contextual_word_meaning(reference_questions, grade)
        if q and answer_line:
            questions.append((q, answer_line))
    return questions
