import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

PROMPT_HEADER = """
You are an expert in Arabic language assessment. Generate a pool of at least 10 Arabic words (not including the main word), all close in meaning to the main word, as possible distractors for an MCQ. The words should be in a list, each on a new line, and should be single words (not phrases).

Instructions:
- Do NOT include the main word itself.
- All words must be close in meaning (synonyms or semantically related).
- Do not repeat words.
- Do not include words with the same root as the main word.

Examples (use this format exactly):

الكلمة الرئيسية: "ترويج"
الخيارات:
تسويق
تغليف
تنفيذ
ترحيل

الكلمة الرئيسية: "مآثر"
الخيارات:
مساكن
مداخل
مراجع
محاسن

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
    for line in lines:
        word = line.strip().replace('-', '').replace('–', '').replace('—', '').strip()
        if word and main_word not in word and len(word.split()) == 1:
            words.append(word)
    return words

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"
الأسئلة المرجعية: {reference_questions[:3]}
اقترح 10 كلمات، كل كلمة في سطر، قريبة في المعنى من "{main_word}".
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
    if len(filtered) < 4:
        return ("تعذر توليد خيارات متوافقة في عدد الحروف. حاول بكلمة أخرى.", "")
    letters = ['أ', 'ب', 'ج', 'د']
    choices = [f"{letters[i]}) {filtered[i]}" for i in range(4)]
    question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(choices)
    answer = choices[0]
    return question, answer

def generate_meaning_test_llm(num_questions, reference_questions, grade):
    questions = []
    used_words = set()
    for _ in range(num_questions):
        prompt = "Suggest a single, exam-appropriate Arabic word (not a phrase) for a vocabulary MCQ for grade 7/8. Do not repeat previous words."
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=20,
        )
        main_word = response.choices[0].message.content.strip().split()[0]
        if main_word in used_words:
            continue
        used_words.add(main_word)
        q, a = generate_mcq_arabic_word_meaning(main_word, reference_questions, grade)
        questions.append((q, a))
    return questions
