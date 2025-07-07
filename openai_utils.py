import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

# --- Word Meaning MCQ (معاني الكلمات) ---
PROMPT_HEADER = """
You are an expert in Arabic language assessment. Generate a pool of at least 10 Arabic words (not including the main word), all close in meaning to the main word, as possible distractors for an MCQ. 
All generated words must have the same Arabic morphological pattern (وزن) as each other (e.g., all on وزن فعيل, or all on وزن مفاعل, etc.) and the same number of letters as each other. 
List the pattern (وزن) you used, then list the words (each on a new line, no phrases).

Instructions:
- Do NOT include the main word itself.
- All words must be close in meaning (synonyms or semantically related).
- Do not repeat words.
- Do not include words with the same root as the main word.

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

وزن: فعيل
كلمات:
قديم
جميل
أصيل
أثري

وزن: فعول
كلمات:
رسول
صبور
شكور
حقود

وزن: مفعول
كلمات:
محسود
مشكور
مرفوع
مكتوب

الكلمة الرئيسية": الدجى"
الخيارات:
الأصيل
الظلام
الشفق
النور

الكلمة الرئيسية": الخضوع"
الخيارات:
الجحود
القعود
الركوع
الخشوع

الكلمة الرئيسية": برع"
الخيارات:
فاق
رام
نام
خاف

الكلمة الرئيسية": عتيق"
الخيارات:
حديث
جميل
قديم
عنيف

الكلمة الرئيسية": طأطأ"
الخيارات:
خفض
رفع
مال
دفع
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

# --- Utility functions for "ال" enforcement ---
def has_al(word):
    return word.strip().startswith("ال")

def ensure_al(words):
    return [w if w.startswith("ال") else "ال" + w for w in words]

def ensure_al_in_choices(choices):
    # choices in format: "أ) كلمة"
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

# --- Word Meaning MCQ (معاني الكلمات) ---
def filter_by_length(words):
    if not words:
        return []
    target_len = len(words[0])
    filtered = [w for w in words if len(w) == target_len]
    return filtered if len(filtered) >= 4 else words[:4]

def extract_candidate_words(gpt_output, main_word):
    lines = gpt_output.strip().split('\n')
    words = []
    collecting = False
    for line in lines:
        l = line.strip()
        if l.startswith("كلمات:") or l.startswith("الخيارات:"):
            collecting = True
            continue
        if l.startswith("وزن:"):
            collecting = False
            continue
        if collecting:
            word = l.replace('-', '').replace('–', '').replace('—', '').strip()
            if word and main_word not in word and len(word.split()) == 1 and word != "الخيارات:":
                words.append(word)
    if not words:
        for line in lines:
            word = line.strip().replace('-', '').replace('–', '').replace('—', '').strip()
            if word and main_word not in word and len(word.split()) == 1 and word != "الخيارات:" and not word.startswith("وزن:"):
                words.append(word)
    return words

def is_semantically_related(main_word, candidate, client, model="gpt-4.1"):
    prompt = f"""In Arabic, is "{candidate}" a synonym or closely related in meaning to "{main_word}"? Answer only with نعم (yes) or لا (no)."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )
    answer = response.choices[0].message.content.strip()
    return "نعم" in answer

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"
الأسئلة المرجعية: {reference_questions[:3]}
اكتب وزن الكلمات التي ستستخدمها، ثم قائمة بـ10 كلمات، كل كلمة في سطر، قريبة في المعنى من "{main_word}"، وجميعها على نفس الوزن وعدد الحروف.
"""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=400,
    )
    gpt_output = response.choices[0].message.content.strip()
    candidate_words = extract_candidate_words(gpt_output, main_word)
    filtered = filter_by_length(candidate_words)

    # Enforce "ال" if main word has it
    if has_al(main_word):
        filtered = ensure_al(filtered)

    # 1. Find at least one correct synonym/meaning match
    correct_synonym = None
    distractors = []
    for w in filtered:
        if is_semantically_related(main_word, w, client) and not correct_synonym:
            correct_synonym = w
        else:
            distractors.append(w)
    msg = None

    if correct_synonym:
        # Fill up to 3 distractors (even if not synonyms)
        while len(distractors) < 3 and len(candidate_words) > len(filtered):
            for w in candidate_words:
                if w not in distractors and w != correct_synonym:
                    distractors.append(w)
                if len(distractors) == 3:
                    break
        choices = [correct_synonym] + distractors[:3]
        letters = ['أ', 'ب', 'ج', 'د']
        display_choices = [f"{letters[i]}) {choices[i]}" for i in range(len(choices))]
        # Enforce "ال" in choices as well
        if has_al(main_word):
            display_choices = ensure_al_in_choices(display_choices)
        question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
        answer = display_choices[0]
        if len(display_choices) < 4:
            msg = "تم توليد أقل من 4 خيارات بسبب عدم توفر مشتتات كافية."
        return question, answer, msg

    # 2. If no correct synonym, return empty answer (will be skipped in test mode)
    return None, None, None

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
        if q and a and not msg:
            questions.append((q, a, msg))
    return questions

# --- Contextual Word Meaning MCQ (معنى الكلمة حسب السياق) ---
def extract_contextual_mcq_parts(gpt_output):
    # Extract the main question block (up to first "نلاحظ" or end)
    question_part = gpt_output.split('\n\nنلاحظ')[0] if '\n\nنلاحظ' in gpt_output else gpt_output

    # Find the answer letter (أ|ب|ج|د) from any answer line
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

    # Enforce "ال" in choices if underlined word has "ال"
    underlined_word = extract_underlined_word(question_part)
    if underlined_word and has_al(underlined_word):
        question_part = enforce_al_in_context_choices(question_part)

    return question_part.strip(), answer_line

def extract_underlined_word(question_text):
    # Try to find a word between underscores or with <u>...</u> or similar
    match = re.search(r'_(\w+)_', question_text)
    if match:
        return match.group(1)
    # Fallback: find the first word with "ال" in the question
    for word in question_text.split():
        if word.startswith("ال"):
            return word
    return None

def enforce_al_in_context_choices(question_text):
    # Replace all choices (أ|ب|ج|د)- كلمة with (أ|ب|ج|د)- الكلمة (if not already)
    def repl(m):
        label = m.group(1)
        word = m.group(2)
        if not word.startswith("ال"):
            word = "ال" + word
        return f"{label}- {word}"
    # Arabic dash or parenthesis formats
    return re.sub(r'([أ-د][\)\-]?)\s*([^\n]+)', repl, question_text)

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
    return question_part, answer_line

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
