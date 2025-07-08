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

def ensure_al_in_choices(choices):
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

def generate_fallback_choices(main_word, client):
    """Generate fallback choices when the main prompt fails"""
    prompt = f"""Generate 4 Arabic words that are synonyms or closely related in meaning to "{main_word}". Use the same form (with or without ال) as the main word. List one word per line, no explanations."""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100,
    )
    words = []
    for line in response.choices[0].message.content.strip().split('\n'):
        word = line.strip()
        if word and len(word.split()) == 1:
            words.append(word)
    return words[:4]

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"
الأسئلة المرجعية: {reference_questions[:3]}
اكتب وزن الكلمات التي ستستخدمها (إن أمكن)، ثم قائمة بـ10 كلمات، كل كلمة في سطر، قريبة في المعنى من "{main_word}".
"""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=400,
    )
    gpt_output = response.choices[0].message.content.strip()
    candidate_words = extract_candidate_words(gpt_output, main_word)
    
    # Remove words with same root
    candidate_words = [w for w in candidate_words if not share_root(main_word, w)]
    
    if len(candidate_words) < 4:
        # Fallback: generate simple synonyms
        fallback_words = generate_fallback_choices(main_word, client)
        candidate_words.extend(fallback_words)
        candidate_words = [w for w in candidate_words if not share_root(main_word, w)]

    if len(candidate_words) < 4:
        # Ultimate fallback: create basic choices with correct form
        if has_al(main_word):
            candidate_words.extend(["الكرم", "الجود", "العطاء", "البذل"])
        else:
            candidate_words.extend(["كرم", "جود", "عطاء", "بذل"])

    # Ensure we have at least 4 unique words
    candidate_words = list(dict.fromkeys(candidate_words))  # Remove duplicates while preserving order
    candidate_words = candidate_words[:4]  # Take first 4

    # Enforce "ال" consistency if main word has it
    if has_al(main_word):
        candidate_words = [w if w.startswith("ال") else "ال" + w for w in candidate_words]
    else:
        candidate_words = [w[2:] if w.startswith("ال") else w for w in candidate_words]

    # Try to find semantic matches
    correct_synonym = None
    distractors = []
    for w in candidate_words:
        if is_semantically_related(main_word, w, client) and not correct_synonym:
            correct_synonym = w
        else:
            distractors.append(w)

    # If no semantic match found, just use first word as correct
    if not correct_synonym and candidate_words:
        correct_synonym = candidate_words[0]
        distractors = candidate_words[1:]

    # Ensure we have 4 choices
    choices = [correct_synonym] + distractors[:3]
    while len(choices) < 4:
        if has_al(main_word):
            choices.append("الخير")
        else:
            choices.append("خير")

    letters = ['أ', 'ب', 'ج', 'د']
    display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
    question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
    answer = display_choices[0]
    
    msg = None
    if len(extract_candidate_words(gpt_output, main_word)) < 4:
        msg = "تم استخدام خيارات احتياطية لضمان توليد السؤال."
    
    return question, answer, msg

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
    return None

def enforce_al_in_context_choices(choices, underlined_word):
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

def generate_mcq_contextual_word_meaning(reference_questions, grade):
    prompt = CONTEXTUAL_PROMPT + "\n\nيرجى توليد سؤال واحد فقط بالتنسيق أعلاه."
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=400,
        )
        gpt_output = response.choices[0].message.content.strip()
        question_part, answer_line = extract_contextual_mcq_parts(gpt_output)

        # Basic validation - ensure we have both question and answer
        if not question_part or not answer_line:
            return None, None

        lines = question_part.split('\n')
        choices = []
        for line in lines:
            m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', line.strip())
            if m:
                choices.append(f"{m.group(1)}) {m.group(2)}")
        
        # Ensure we have at least 4 choices
        if len(choices) < 4:
            return None, None
            
        underlined_word = extract_underlined_word(question_part)

        filtered_choices = []
        for c in choices:
            m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', c)
            if m and underlined_word:
                if not share_root(underlined_word, m.group(2)):
                    filtered_choices.append(c)
            else:
                filtered_choices.append(c)
        
        # If we filtered out too many choices, use original choices
        if len(filtered_choices) < 4:
            filtered_choices = choices
            
        filtered_choices = enforce_al_in_context_choices(filtered_choices, underlined_word)
        question_lines = [l for l in lines if not re.match(r'^([أ-د][\)\-]?)\s*(.+)', l.strip())]
        question_part_final = "\n".join(question_lines + filtered_choices)
        return question_part_final.strip(), answer_line
    except Exception as e:
        return None, None

def generate_contextual_test_llm(num_questions, reference_questions, grade):
    questions = []
    max_attempts = num_questions * 15  # Increased attempts
    attempts = 0
    
    while len(questions) < num_questions and attempts < max_attempts:
        attempts += 1
        try:
            q, answer_line = generate_mcq_contextual_word_meaning(reference_questions, grade)
            if q and answer_line and len(q.strip()) > 50:  # Basic quality check
                questions.append((q, answer_line))
        except Exception as e:
            continue  # Skip failed attempts and try again
    
    return questions
