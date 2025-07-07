import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

PROMPT_HEADER = """
You are an expert in Arabic language assessment. For the given main word, generate a multiple-choice question (MCQ) with four choices.

Instructions:
- Only one choice should be the closest in meaning (a true synonym or the best possible equivalent) to the main word; the other three must be plausible distractors (semantically related but not synonyms).
- Do NOT include the main word itself.
- Do not repeat words.
- Do not include words with the same root as the main word.
- Preferably, all choices should have the same Arabic morphological pattern (وزن) and the same number of letters as each other (e.g., all on وزن فعيل, or all on وزن مفاعل, etc.), but if this is not possible, relax this constraint and provide the best set of distractors you can.
- List the pattern (وزن) you used (if any), then show the four choices (each on a new line, no phrases).
- Clearly indicate the correct answer.

Examples (use this format exactly):

الكلمة الرئيسية: "الدجى"
الخيارات:
أ) الظلام
ب) الشفق
ج) النور
د) الأصيل

الإجابة الصحيحة: أ) الظلام

الكلمة الرئيسية: "الأصل"
الخيارات:
أ) الصباح
ب) السحر
ج) الغروب
د) الظهيرة

الإجابة الصحيحة: ب) السحر

الكلمة الرئيسية: "الخضوع"
الخيارات:
أ) الركوع
ب) الجحود
ج) القعود
د) الخشوع

الإجابة الصحيحة: أ) الركوع
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

def extract_mcq_choices_and_answer(gpt_output, main_word):
    # Extract choices and correct answer from model output
    lines = gpt_output.strip().split('\n')
    choices = []
    correct = None
    for line in lines:
        m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', line.strip())
        if m:
            choices.append((m.group(1), m.group(2)))
        if line.strip().startswith("الإجابة الصحيحة"):
            correct = line.strip().split(":", 1)[-1].strip()
    # Remove words with same root as main word
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
        # Fallback: try to generate as before with semantic filtering
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
                display_choices = ensure_al_in_choices(display_choices)
            question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
            answer = display_choices[0]
            return question, answer, None
        return None, None, "تعذر توليد خيارات مناسبة."
    else:
        # Compose question
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

    underlined_word = extract_underlined_word(question_part)
    if underlined_word and has_al(underlined_word):
        question_part = enforce_al_in_context_choices(question_part)

    return question_part.strip(), answer_line

def extract_underlined_word(question_text):
    match = re.search(r'_(\w+)_', question_text)
    if match:
        return match.group(1)
    for word in question_text.split():
        if word.startswith("ال"):
            return word
    return None

def enforce_al_in_context_choices(question_text):
    def repl(m):
        label = m.group(1)
        word = m.group(2)
        if not word.startswith("ال"):
            word = "ال" + word
        return f"{label}- {word}"
    return re.sub(r'([أ-د][\)\-]?)\s*([^\n]+)', repl, question_text)

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

    # Remove choices with same root as underlined word
    underlined_word = extract_underlined_word(question_part)
    if underlined_word:
        lines = question_part.split('\n')
        new_lines = []
        for line in lines:
            m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', line.strip())
            if m:
                choice_word = m.group(2)
                if not share_root(underlined_word, choice_word):
                    new_lines.append(line)
            else:
                new_lines.append(line)
        question_part = '\n'.join(new_lines)

    return question_part.strip(), answer_line

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
