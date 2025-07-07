import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

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

الكلمة الرئيسية: "عتيق"
الخيارات:
حديث
جميل
قديم
عنيف

الكلمة الرئيسية: "طأطأ"
الخيارات:
خفض
رفع
مال
دفع
"""

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
            # Try other candidates (different length)
            for w in candidate_words:
                if w not in distractors and w != correct_synonym:
                    distractors.append(w)
                if len(distractors) == 3:
                    break
        # Compose choices: correct answer always A
        choices = [correct_synonym] + distractors[:3]
        letters = ['أ', 'ب', 'ج', 'د']
        display_choices = [f"{letters[i]}) {choices[i]}" for i in range(len(choices))]
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
    max_attempts = num_questions * 10  # Allow more attempts to find valid questions
    attempts = 0

    # 1. Ask the LLM for a list of Arabic words relevant to the grade
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
    
    # 2. For each candidate word, try to generate a valid MCQ
    for main_word in candidate_words:
        if len(questions) >= num_questions:
            break
        if main_word in used_words:
            continue
        used_words.add(main_word)
        q, a, msg = generate_mcq_arabic_word_meaning(main_word, reference_questions, grade)
        # Only accept questions where a correct answer (synonym/meaning) is found and no warning message
        if q and a and not msg:
            questions.append((q, a, msg))
    return questions
