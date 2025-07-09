import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

# --- Word Meaning MCQ (معاني الكلمات) ---
PROMPT_HEADER = """
You are an expert in Arabic language assessment. For the given main word, generate:
1. ONE correct synonym (closest in meaning)
2. THREE plausible distractors (words that could confuse students but are NOT synonyms)

Instructions:
- **CRITICAL**: Do NOT include the main word itself in any of the choices
- The correct answer should be a true synonym or very close in meaning
- The three distractors should be plausible but clearly different in meaning
- Avoid words with the same root as the main word
- **PREFERRED**: Try to ensure all four answer choices have the same Arabic morphological pattern (وزن) and similar letter count when possible
- **FLEXIBILITY**: If better educational distractors are available that don't match the pattern, prioritize educational value over pattern consistency
- The morphological pattern matching applies ONLY to the answer choices themselves, NOT to the main word
- Format: You may list the words in any order - no need to list the correct answer first
- IMPORTANT: Only provide the word list, no introductory text or explanations

Examples showing different approaches:

الكلمة الرئيسية: "الخضوع"
وزن الخيارات: فعول (pattern consistency prioritized)
الخيارات:
الخشوع (صحيح)
الجحود
القعود
الركوع

الكلمة الرئيسية: "برع"
وزن الخيارات: فعل (pattern consistency prioritized)
الخيارات:
فاق (صحيح)
رام
نام
خاف

الكلمة الرئيسية: "الأصل"
وزن الخيارات: متنوع (educational value prioritized over pattern)
الخيارات:
الصباح (صحيح - time reference)
السحر
الغروب
الظهيرة
"""

# --- Contextual Word Meaning MCQ (معنى الكلمة حسب السياق) ---
CONTEXTUAL_PROMPT = """
أنت خبير في إعداد أسئلة اللغة العربية. أنشئ سؤال اختيار من متعدد لمعنى كلمة في سياق جملة.

التعليمات:
- أنشئ جملة تحتوي على كلمة واحدة مهمة (الكلمة المستهدفة يمكن أن تكون في أي مكان في الجملة)
- أعطِ أربعة خيارات للإجابة (أ، ب، ج، د)
- **CRITICAL**: Do NOT include the target word itself in any of the answer choices
- خيار واحد فقط هو الصحيح (مرادف أو الأقرب معنى في السياق)
- **PREFERRED**: Try to ensure all four answer choices have the same Arabic morphological pattern (وزن) and similar letter count when possible
- **FLEXIBILITY**: If better educational distractors are available that don't match the pattern, prioritize educational value over pattern consistency
- The morphological pattern matching applies ONLY to the answer choices themselves, NOT to the target word
- لا تدرج كلمات تشترك في الجذر مع الكلمة المستهدفة
- اكتب السؤال بوضوح مع الخيارات منفصلة
- IMPORTANT: Only provide the question and choices, no introductory text or explanations

تنسيق الإجابة المطلوب:
السؤال: [الجملة هنا]
ما معنى كلمة "[الكلمة المستهدفة]" في السياق أعلاه؟

أ) [الخيار الأول]
ب) [الخيار الثاني]  
ج) [الخيار الثالث]
د) [الخيار الرابع]

الإجابة الصحيحة: ([الحرف])

أمثلة:

السؤال: وَجَمَ الرجل بعد أن طُرد من عمله
ما معنى كلمة "وَجَم" في السياق أعلاه؟

أ) شرد
ب) تعب
ج) عبس
د) سكت

الإجابة الصحيحة: (ج)

السؤال: والليل إذا عسعس
ما معنى كلمة "عسعس" في السياق أعلاه؟

أ) طال
ب) أظلم
ج) قصر
د) أمطر

الإجابة الصحيحة: (ب)

السؤال: انبثق الماء غزيرا
ما معنى كلمة "انبثق" في السياق أعلاه؟

أ) انحصر
ب) انتشر
ج) انقطع
د) اندفع

الإجابة الصحيحة: (د)

السؤال: اشرأبت الزرافات بأعناقها
ما معنى كلمة "اشرأبت" في السياق أعلاه؟

أ) امتدّت
ب) اشتدّت
ج) قصرت
د) ابتهجت

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

def format_question_with_line_breaks(question_text):
    """Format question to ensure each choice is on a separate line"""
    lines = question_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line contains multiple choices
        choice_pattern = r'([أ-د][\)\-])'
        choices_in_line = re.findall(choice_pattern, line)
        
        if len(choices_in_line) > 1:
            # Split multiple choices into separate lines
            parts = re.split(choice_pattern, line)
            current_choice = ""
            
            for i, part in enumerate(parts):
                if re.match(r'[أ-د][\)\-]', part):
                    if current_choice.strip():
                        formatted_lines.append(current_choice.strip())
                    current_choice = part
                else:
                    current_choice += part
            
            if current_choice.strip():
                formatted_lines.append(current_choice.strip())
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"

أنشئ إجابة صحيحة واحدة (مرادف) وثلاثة مشتتات مناسبة للكلمة "{main_word}".
حاول جعل الخيارات الأربعة لها نفس الوزن الصرفي عند الإمكان، لكن إذا كانت هناك مشتتات تعليمية أفضل بأوزان مختلفة، فاختر القيمة التعليمية.
**مهم جداً: لا تدرج الكلمة الرئيسية "{main_word}" نفسها في أي من الخيارات.**
"""
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=300,
    )
    
    gpt_output = response.choices[0].message.content.strip()
    cleaned_output = clean_llm_response(gpt_output)
    
    # Extract choices and identify correct answer
    correct_answer = None
    all_choices = []
    
    lines = cleaned_output.split('\n')
    collecting_choices = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("الخيارات:"):
            collecting_choices = True
            continue
        elif collecting_choices and line:
            if "(صحيح)" in line:
                correct_answer = line.replace("(صحيح)", "").strip()
                all_choices.append(correct_answer)
            elif line and not line.startswith("الكلمة") and not line.startswith("وزن"):
                all_choices.append(line)
    
    # Filter out the main word from all choices
    all_choices = [choice for choice in all_choices if not words_are_same(choice, main_word)]
    
    if correct_answer and words_are_same(correct_answer, main_word):
        correct_answer = None
    
    # Fallback if parsing fails or main word was included
    if not correct_answer or len(all_choices) < 4:
        return generate_fallback_mcq(main_word, client)
    
    # Ensure consistent "ال" usage
    if has_al(main_word):
        correct_answer = correct_answer if correct_answer.startswith("ال") else "ال" + correct_answer
        all_choices = [choice if choice.startswith("ال") else "ال" + choice for choice in all_choices]
    else:
        correct_answer = correct_answer[2:] if correct_answer.startswith("ال") else correct_answer
        all_choices = [choice[2:] if choice.startswith("ال") else choice for choice in all_choices]
    
    # Remove words with same root and ensure no main word
    filtered_choices = [choice for choice in all_choices if not share_root(main_word, choice) and not words_are_same(choice, main_word)]
    
    if len(filtered_choices) < 4:
        filtered_choices = all_choices[:4]
    
    choices = filtered_choices[:4]
    
    # Find correct answer in filtered choices
    if correct_answer in choices:
        correct_index = choices.index(correct_answer)
    else:
        correct_index = 0
        correct_answer = choices[0]
    
    # Final check to ensure main word is not in choices
    choices = [choice for choice in choices if not words_are_same(choice, main_word)]
    
    if len(choices) < 4:
        return generate_fallback_mcq(main_word, client)
    
    # Shuffle choices but keep track of correct answer position
    import random
    random.shuffle(choices)
    correct_index = choices.index(correct_answer)
    
    letters = ['أ', 'ب', 'ج', 'د']
    display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
    
    # Format question with proper line breaks for each choice
    question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
    answer = display_choices[correct_index]
    
    return question, answer, None

def generate_fallback_mcq(main_word, client):
    """Generate fallback MCQ when main prompt fails"""
    prompt = f"""
    للكلمة العربية "{main_word}":
    1. اكتب مرادف واحد صحيح
    2. اكتب 3 كلمات مختلفة المعنى كمشتتات
    
    **مهم جداً: لا تدرج الكلمة الرئيسية "{main_word}" نفسها في أي من الخيارات.**
    استخدم نفس الشكل (مع أو بدون ال) مثل الكلمة الأصلية.
    اكتب كل كلمة في سطر منفصل.
    لا تكتب أي نص تمهيدي.
    """
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150,
    )
    
    cleaned_output = clean_llm_response(response.choices[0].message.content.strip())
    words = []
    for line in cleaned_output.split('\n'):
        word = line.strip()
        if word and len(word.split()) == 1 and not words_are_same(word, main_word):
            words.append(word)
    
    if len(words) < 4:
        # Ultimate fallback
        if has_al(main_word):
            fallback_words = ["الفهم", "الجهل", "السرعة", "القوة"]
        else:
            fallback_words = ["فهم", "جهل", "سرعة", "قوة"]
        
        fallback_words = [w for w in fallback_words if not words_are_same(w, main_word)]
        words.extend(fallback_words)
    
    choices = words[:4]
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

def format_contextual_question(question_sentence, target_word, choices, correct_answer):
    """Format the contextual question properly with line breaks"""
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
    
    # Format the question with proper spacing and line breaks
    formatted_question = f"**السؤال:** {question_sentence}\n\n"
    formatted_question += f"**ما معنى كلمة \"{target_word}\" في السياق أعلاه؟**\n\n"
    
    # Add choices with proper formatting - each on a new line
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
            
            formatted_question, formatted_answer = format_contextual_question(
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
