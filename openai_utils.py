import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

# --- Word Meaning MCQ (معاني الكلمات) ---
PROMPT_HEADER = """
You are an expert in Arabic language assessment. For the given main word, generate:
1. ONE correct synonym (closest in meaning)
2. THREE plausible distractors (words that are clearly different in meaning but could confuse students)

Instructions:
- **CRITICAL**: Do NOT include the main word itself in any of the choices
- The correct answer should be a true synonym or very close in meaning
- The three distractors should be plausible but clearly different in meaning from both the main word AND the correct answer
- Avoid words with the same root as the main word
- **IMPORTANT**: Ensure distractors are NOT synonyms of the main word or the correct answer
- **PREFERRED**: Try to ensure all four answer choices have the same Arabic morphological pattern (وزن) and similar letter count when possible
- **FLEXIBILITY**: If better educational distractors are available that don't match the pattern, prioritize educational value over pattern consistency
- Format: List the correct answer first, then the three distractors

Example format:
الكلمة الرئيسية: "السخاء"
الإجابة الصحيحة: الكرم
المشتتات:
البخل (opposite meaning)
الحكمة (different concept)
السرعة (unrelated)

الكلمة الرئيسية: "الشجاعة"
الإجابة الصحيحة: البسالة
المشتتات:
الجبانة (opposite)
الحكمة (different virtue)
السرعة (different quality)

الكلمة الرئيسية: "برع"
الإجابة الصحيحة: فاق
المشتتات:
فشل (opposite)
نام (unrelated action)
أكل (unrelated action)
"""

# --- Contextual Word Meaning MCQ (معنى الكلمة حسب السياق) ---
CONTEXTUAL_PROMPT = """
أنت خبير في إعداد أسئلة اللغة العربية. أنشئ سؤال اختيار من متعدد لمعنى كلمة في سياق جملة.

التعليمات:
- أنشئ جملة تحتوي على كلمة واحدة مهمة (الكلمة المستهدفة يمكن أن تكون في أي مكان في الجملة)
- أعطِ أربعة خيارات للإجابة (أ، ب، ج، د)
- **CRITICAL**: خيار واحد فقط هو الصحيح، والثلاثة الأخرى يجب أن تكون مختلفة المعنى وليست مرادفات
- **IMPORTANT**: تأكد من أن المشتتات ليست مرادفات للكلمة المستهدفة أو للإجابة الصحيحة
- وضّح رمز الإجابة الصحيحة في نهاية السؤال
- لا تدرج كلمات تشترك في الجذر مع الكلمة المستهدفة

تنسيق الإجابة المطلوب:
السؤال: [الجملة هنا]
ما معنى كلمة "[الكلمة المستهدفة]" في السياق أعلاه؟

أ) [الإجابة الصحيحة]
ب) [مشتت مختلف المعنى]
ج) [مشتت مختلف المعنى]
د) [مشتت مختلف المعنى]

الإجابة الصحيحة: ([الحرف])

أمثلة:

السؤال: وَجَمَ الرجل بعد أن طُرد من عمله
ما معنى كلمة "وَجَم" في السياق أعلاه؟

أ) عبس
ب) فرح
ج) نام
د) أكل

الإجابة الصحيحة: (أ)

السؤال: والليل إذا عسعس
ما معنى كلمة "عسعس" في السياق أعلاه؟

أ) أظلم
ب) أشرق
ج) هطل
د) هدأ

الإجابة الصحيحة: (أ)
"""

def has_al(word):
    return word.strip().startswith("ال")

def normalize_al(word):
    return word[2:] if word.startswith("ال") else word

def share_root(word1, word2):
    w1 = normalize_al(word1)
    w2 = normalize_al(word2)
    return w1[:3] == w2[:3] or w1[:4] == w2[:4]

def words_are_same(word1, word2):
    """Check if two words are the same, considering ال prefix"""
    w1 = normalize_al(word1.strip())
    w2 = normalize_al(word2.strip())
    return w1.lower() == w2.lower()

def clean_llm_response(response_text):
    """Remove common LLM introductory phrases and clean the response"""
    intro_phrases = [
        "بالطبع، إليك",
        "إليك قائمة",
        "فيما يلي",
        "هذه قائمة",
        "بالتأكيد",
        "نعم، يمكنني",
        "سأقوم بتوليد",
        "سأنشئ لك",
        "إليك السؤال",
        "هنا السؤال"
    ]
    
    cleaned_text = response_text.strip()
    lines = cleaned_text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        should_keep = True
        
        for phrase in intro_phrases:
            if phrase in line and len(line) > 50:
                should_keep = False
                break
        
        if should_keep and line:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def normalize_al_consistency(choices, main_word):
    """Ensure ال consistency based on main word usage"""
    main_has_al = has_al(main_word)
    normalized_choices = []
    
    for choice in choices:
        choice = choice.strip()
        
        if main_has_al:
            if not choice.startswith("ال"):
                normalized_choices.append("ال" + choice)
            else:
                normalized_choices.append(choice)
        else:
            if choice.startswith("ال"):
                without_al = choice[2:]
                if len(without_al) > 2:
                    normalized_choices.append(without_al)
                else:
                    normalized_choices.append(choice)
            else:
                normalized_choices.append(choice)
    
    return normalized_choices

def validate_semantic_uniqueness(main_word, correct_answer, distractors, client):
    """Validate that distractors are not synonyms of main word or correct answer"""
    valid_distractors = []
    
    for distractor in distractors:
        # Check if distractor is synonym of main word
        prompt1 = f"""Are "{normalize_al(distractor)}" and "{normalize_al(main_word)}" synonyms in Arabic? Answer only نعم or لا."""
        response1 = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt1}],
            temperature=0,
            max_tokens=10,
        )
        
        # Check if distractor is synonym of correct answer
        prompt2 = f"""Are "{normalize_al(distractor)}" and "{normalize_al(correct_answer)}" synonyms in Arabic? Answer only نعم or لا."""
        response2 = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt2}],
            temperature=0,
            max_tokens=10,
        )
        
        answer1 = response1.choices[0].message.content.strip()
        answer2 = response2.choices[0].message.content.strip()
        
        # Only include if it's NOT a synonym of either
        if 'لا' in answer1 and 'لا' in answer2:
            valid_distractors.append(distractor)
    
    return valid_distractors

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"

أنشئ إجابة صحيحة واحدة (مرادف دقيق) وثلاثة مشتتات واضحة المعنى المختلف للكلمة "{main_word}".
**مهم جداً: لا تدرج الكلمة الرئيسية "{main_word}" نفسها في أي من الخيارات.**
**مهم جداً: تأكد من أن المشتتات ليست مرادفات للكلمة الرئيسية أو للإجابة الصحيحة.**
**مهم: اتبع نفس استخدام "ال" كما في الكلمة الرئيسية.**
"""
    
    max_retries = 3
    for attempt in range(max_retries):
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=300,
        )
        
        gpt_output = response.choices[0].message.content.strip()
        cleaned_output = clean_llm_response(gpt_output)
        
        # Extract correct answer and distractors
        correct_answer = None
        distractors = []
        
        lines = cleaned_output.split('\n')
        collecting_distractors = False
        
        for line in lines:
            line = line.strip()
            if line.startswith("الإجابة الصحيحة:"):
                correct_answer = line.split(":", 1)[1].strip()
            elif line.startswith("المشتتات:"):
                collecting_distractors = True
            elif collecting_distractors and line and not line.startswith("الكلمة"):
                word = line.replace('-', '').replace('–', '').replace('—', '').strip()
                if word and len(word.split()) == 1:
                    distractors.append(word)
        
        # Filter out main word from all choices
        if correct_answer and words_are_same(correct_answer, main_word):
            correct_answer = None
        distractors = [d for d in distractors if not words_are_same(d, main_word)]
        
        if not correct_answer or len(distractors) < 3:
            continue
        
        # Apply ال consistency
        all_choices = [correct_answer] + distractors
        all_choices = normalize_al_consistency(all_choices, main_word)
        correct_answer = all_choices[0]
        distractors = all_choices[1:]
        
        # Validate semantic uniqueness
        valid_distractors = validate_semantic_uniqueness(main_word, correct_answer, distractors, client)
        
        if len(valid_distractors) >= 3:
            # Remove words with same root
            filtered_distractors = [d for d in valid_distractors if not share_root(main_word, d)]
            
            if len(filtered_distractors) >= 3:
                final_distractors = filtered_distractors[:3]
            else:
                final_distractors = valid_distractors[:3]
            
            # Create final choices
            choices = [correct_answer] + final_distractors
            
            # Shuffle choices but keep track of correct answer position
            import random
            random.shuffle(choices)
            correct_index = choices.index(correct_answer)
            
            letters = ['أ', 'ب', 'ج', 'د']
            display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
            question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
            answer = display_choices[correct_index]
            
            return question, answer, None
    
    # Fallback if all attempts fail
    return generate_fallback_mcq(main_word, client)

def generate_fallback_mcq(main_word, client):
    """Generate fallback MCQ with guaranteed unique semantics"""
    # Use opposite and unrelated words as distractors
    if has_al(main_word):
        base_word = normalize_al(main_word)
        if base_word in ["سخاء", "كرم", "جود"]:
            choices = ["الكرم", "البخل", "الحكمة", "السرعة"]
        elif base_word in ["شجاعة", "بسالة"]:
            choices = ["البسالة", "الجبانة", "الحكمة", "السرعة"]
        else:
            choices = ["الفهم", "الجهل", "السرعة", "القوة"]
    else:
        base_word = normalize_al(main_word)
        if base_word in ["سخاء", "كرم", "جود"]:
            choices = ["كرم", "بخل", "حكمة", "سرعة"]
        elif base_word in ["شجاعة", "بسالة"]:
            choices = ["بسالة", "جبانة", "حكمة", "سرعة"]
        else:
            choices = ["فهم", "جهل", "سرعة", "قوة"]
    
    # Remove any that match the main word
    choices = [c for c in choices if not words_are_same(c, main_word)][:4]
    
    letters = ['أ', 'ب', 'ج', 'د']
    display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
    question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
    answer = display_choices[0]
    
    return question, answer, "تم استخدام خيارات احتياطية لضمان توليد السؤال."

def generate_meaning_test_llm(num_questions, reference_questions, grade):
    questions = []
    used_words = set()
    max_attempts = num_questions * 10
    attempts = 0
    
    prompt = (
        f"اكتب 15 كلمة عربية مناسبة لاختبار معاني الكلمات للصف {grade}. "
        "كل كلمة في سطر منفصل. لا تكتب أي نص تمهيدي أو تفسيري."
    )
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100,
    )
    
    cleaned_output = clean_llm_response(response.choices[0].message.content.strip())
    candidate_words = [w.strip() for w in cleaned_output.split('\n') if w.strip()]
    
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
def parse_contextual_response(gpt_output):
    """Parse the structured contextual response"""
    cleaned_output = clean_llm_response(gpt_output)
    lines = cleaned_output.strip().split('\n')
    
    question_sentence = ""
    target_word = ""
    choices = []
    correct_answer = ""
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("السؤال:"):
            question_sentence = line.replace("السؤال:", "").strip()
        elif line.startswith("ما معنى كلمة"):
            match = re.search(r'"([^"]+)"', line)
            if match:
                target_word = match.group(1)
        elif re.match(r'^[أ-د][\)\s]', line):
            choices.append(line)
        elif line.startswith("الإجابة الصحيحة:"):
            match = re.search(r'\(([أ-د])\)', line)
            if match:
                correct_answer = match.group(1)
        
        i += 1
    
    return question_sentence, target_word, choices, correct_answer

def format_contextual_question_with_breaks(question_sentence, target_word, choices, correct_answer):
    """Format the contextual question with proper line breaks and semantic validation"""
    if not all([question_sentence, target_word, choices, correct_answer]):
        return None, None
    
    # Filter out target word from choices
    filtered_choices = []
    for choice in choices:
        choice_word = choice
        if re.match(r'^[أ-د][\)\-]', choice):
            choice_word = re.sub(r'^[أ-د][\)\-]\s*', '', choice)
        
        if not words_are_same(choice_word, target_word):
            filtered_choices.append(choice)
    
    if len(filtered_choices) < 4:
        return None, None
    
    # Format with proper line breaks
    formatted_question = "السؤال:\n"
    formatted_question += f"{question_sentence}\n\n"
    formatted_question += f"ما معنى كلمة \"{target_word}\" في السياق أعلاه؟\n\n"
    
    # Add choices with proper formatting
    for choice in filtered_choices[:4]:
        formatted_question += f"{choice}\n"
    
    formatted_answer = f"الإجابة الصحيحة: ({correct_answer})"
    
    return formatted_question.strip(), formatted_answer

def generate_mcq_contextual_word_meaning(reference_questions, grade):
    prompt = CONTEXTUAL_PROMPT + "\n\nيرجى توليد سؤال واحد فقط بالتنسيق المحدد أعلاه. لا تكتب أي نص تمهيدي."
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=400,
            )
            
            gpt_output = response.choices[0].message.content.strip()
            question_sentence, target_word, choices, correct_answer = parse_contextual_response(gpt_output)
            
            if not all([question_sentence, target_word, choices, correct_answer]) or len(choices) < 4:
                continue
            
            formatted_question, formatted_answer = format_contextual_question_with_breaks(
                question_sentence, target_word, choices, correct_answer
            )
            
            if formatted_question and formatted_answer:
                return formatted_question, formatted_answer
                
        except Exception as e:
            continue
    
    return None, None

def generate_contextual_test_llm(num_questions, reference_questions, grade):
    questions = []
    max_attempts = num_questions * 30
    attempts = 0
    
    while len(questions) < num_questions and attempts < max_attempts:
        attempts += 1
        try:
            q, answer_line = generate_mcq_contextual_word_meaning(reference_questions, grade)
            if q and answer_line:
                questions.append((q, answer_line))
        except Exception as e:
            continue
    
    return questions
