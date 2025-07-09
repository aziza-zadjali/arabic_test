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
- Do NOT include the main word itself.
- The correct answer should be a true synonym or very close in meaning
- The three distractors should be plausible but clearly different in meaning
- Do not repeat words.
- Do not include words with the same root as the main word.
- Preferably, all generated choices should have the same Arabic morphological pattern (وزن) and the same number of letters as each other, but if this is not possible, you may relax this constraint and provide the best set of distractors you can.
- **CRITICAL**: Ensure only ONE choice is semantically correct
- **FORMAT**: Respond ONLY with the structured format below, no additional text

Examples (use this format exactly):

الكلمة الرئيسية: "السخاء"
الإجابة الصحيحة: الكرم
المشتتات:
البخل
الحكمة
السرعة

الكلمة الرئيسية: "الشجاعة"
الإجابة الصحيحة: البسالة
المشتتات:
الجبانة
الحكمة
السرعة

الكلمة الرئيسية: "الأصل"
الخيارات:
الصباح (صحيح)
السحر
الغروب
الظهيرة

الكلمة الرئيسية: "الدجى"
الخيارات:
الظلام (صحيح)
الأصيل
الشفق
النور

الكلمة الرئيسية: "الخضوع"
الخيارات:
الخشوع (صحيح)
الجحود
القعود
الركوع

الكلمة الرئيسية: "برع"
الخيارات:
فاق (صحيح)
رام
نام
خاف
"""

# --- Contextual Word Meaning MCQ (معنى الكلمة حسب السياق) ---
CONTEXTUAL_PROMPT = """
أنت خبير في إعداد أسئلة اللغة العربية. أنشئ سؤال اختيار من متعدد لمعنى كلمة في سياق جملة.

التعليمات:
- الجملة يجب أن تحتوي على كلمة واحدة تحتها خط.
- أعطِ أربعة خيارات للإجابة (أ، ب، ج، د).
- خيار واحد فقط هو الصحيح (مرادف أو الأقرب معنى في السياق).
- وضّح رمز الإجابة الصحيحة في نهاية السؤال.
- **FORMAT**: استخدم التنسيق المحدد أدناه فقط، بدون نص إضافي

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

def extract_structured_response(gpt_output, expected_markers):
    """Extract content based on expected structural markers"""
    lines = [line.strip() for line in gpt_output.strip().split('\n') if line.strip()]
    
    # Filter out lines that look like introductory text
    filtered_lines = []
    found_marker = False
    
    for line in lines:
        # Check if we've found any expected marker
        if any(marker in line for marker in expected_markers):
            found_marker = True
        
        # Once we find a marker, include all subsequent lines
        if found_marker:
            filtered_lines.append(line)
        # Before finding a marker, only include lines that look like structured content
        elif any(char in line for char in [':', ')', '(', 'أ', 'ب', 'ج', 'د']) and len(line) < 100:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def is_semantically_related(main_word, candidate, client, model="gpt-4.1"):
    """Check if candidate is a true synonym of main_word"""
    prompt = f"""Are "{normalize_al(candidate)}" and "{normalize_al(main_word)}" true synonyms in Arabic? Answer only نعم or لا."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        answer = response.choices[0].message.content.strip()
        return 'نعم' in answer
    except:
        return False

def extract_candidate_words(gpt_output, main_word):
    # Clean the output first
    expected_markers = ["الخيارات:", "المشتتات:", "الإجابة الصحيحة:", "وزن:"]
    cleaned_output = extract_structured_response(gpt_output, expected_markers)
    
    lines = cleaned_output.strip().split('\n')
    words = []
    collecting = False
    correct_answer = None
    
    for line in lines:
        l = line.strip()
        
        # Extract correct answer
        if l.startswith("الإجابة الصحيحة:"):
            correct_answer = l.split(":", 1)[1].strip()
            continue
            
        # Start collecting words
        if l.startswith("كلمات:") or l.startswith("الخيارات:") or l.startswith("المشتتات:"):
            collecting = True
            continue
            
        # Stop collecting
        if l.startswith("وزن:") or l.startswith("الإجابة الصحيحة:"):
            collecting = False
            continue
            
        if collecting:
            # Clean the word
            word = l.replace('(صحيح)', '').replace('-', '').replace('–', '').replace('—', '').strip()
            if word and main_word not in word and len(word.split()) == 1:
                words.append(word)
    
    # If no structured format found, try to extract from any line with single words
    if not words:
        for line in lines:
            word = line.strip().replace('(صحيح)', '').replace('-', '').strip()
            if (word and len(word.split()) == 1 and 
                not word.startswith("وزن:") and 
                not word.startswith("الإجابة") and
                not word.startswith("الكلمة") and
                main_word not in word):
                words.append(word)
    
    return words, correct_answer

def generate_fallback_choices(main_word, client):
    """Generate fallback choices using LLM without hardcoded mappings"""
    prompt = f"""For the Arabic word "{main_word}", provide:
1. One true synonym
2. Three different words (not synonyms)

Format:
صحيح: [synonym]
مشتتات:
[word1]
[word2] 
[word3]

Use same ال pattern as main word. No explanations."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100,
        )
        
        output = response.choices[0].message.content.strip()
        words, correct = extract_candidate_words(output, main_word)
        
        if correct:
            choices = [correct] + words[:3]
        else:
            choices = words[:4]
            
        # Apply ال consistency
        if has_al(main_word):
            choices = [w if w.startswith("ال") else "ال" + w for w in choices]
        else:
            choices = [w[2:] if w.startswith("ال") else w for w in choices]
            
        return choices[:4]
    except:
        # Ultimate fallback
        if has_al(main_word):
            return ["الفهم", "الجهل", "السرعة", "القوة"]
        else:
            return ["فهم", "جهل", "سرعة", "قوة"]

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}

الكلمة الرئيسية: "{main_word}"

أنشئ إجابة صحيحة واحدة (مرادف دقيق) وثلاثة مشتتات واضحة المعنى المختلف للكلمة "{main_word}".
استخدم التنسيق المحدد فقط، بدون نص إضافي."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=300,
        )
        
        gpt_output = response.choices[0].message.content.strip()
        candidate_words, correct_answer = extract_candidate_words(gpt_output, main_word)
        
        # Remove words with same root and main word itself
        candidate_words = [w for w in candidate_words if not share_root(main_word, w) and not words_are_same(w, main_word)]
        
        if len(candidate_words) < 3 or not correct_answer:
            # Use fallback
            fallback_choices = generate_fallback_choices(main_word, client)
            choices = fallback_choices
            correct_answer = choices[0]
        else:
            # Use extracted choices
            if correct_answer in candidate_words:
                choices = [correct_answer] + [w for w in candidate_words if w != correct_answer][:3]
            else:
                choices = [correct_answer] + candidate_words[:3]
        
        # Ensure we have exactly 4 choices
        while len(choices) < 4:
            choices.append("خير" if not has_al(main_word) else "الخير")
        
        choices = choices[:4]
        
        # Apply ال consistency
        if has_al(main_word):
            choices = [w if w.startswith("ال") else "ال" + w for w in choices]
        else:
            choices = [w[2:] if w.startswith("ال") else w for w in choices]
        
        # Validate semantic correctness of first choice
        if not is_semantically_related(main_word, choices[0], client):
            # Try fallback
            fallback_choices = generate_fallback_choices(main_word, client)
            choices = fallback_choices
        
        # Shuffle choices but keep track of correct answer position
        import random
        correct_synonym = choices[0]
        random.shuffle(choices)
        correct_index = choices.index(correct_synonym)
        
        letters = ['أ', 'ب', 'ج', 'د']
        display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
        question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
        answer = display_choices[correct_index]
        
        return question, answer, None
        
    except Exception as e:
        # Final fallback
        fallback_choices = generate_fallback_choices(main_word, client)
        choices = fallback_choices[:4]
        
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
    
    # Generate candidate words
    prompt = f"اكتب 15 كلمة عربية مناسبة للصف {grade}. كل كلمة في سطر منفصل. بدون نص إضافي."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100,
        )
        
        # Extract words using structural parsing
        output = response.choices[0].message.content.strip()
        candidate_words = [w.strip() for w in output.split('\n') if w.strip() and len(w.strip().split()) == 1]
        
    except:
        candidate_words = ["الكرم", "الشجاعة", "الحكمة", "العلم", "الصبر"]
    
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
    expected_markers = ["السؤال:", "ما معنى كلمة", "الإجابة الصحيحة:"]
    cleaned_output = extract_structured_response(gpt_output, expected_markers)
    lines = cleaned_output.strip().split('\n')
    
    question_sentence = ""
    target_word = ""
    choices = []
    correct_answer = ""
    
    for line in lines:
        line = line.strip()
        
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
    
    return question_sentence, target_word, choices, correct_answer

def format_contextual_question_with_breaks(question_sentence, target_word, choices, correct_answer):
    """Format the contextual question with proper line breaks"""
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
    prompt = CONTEXTUAL_PROMPT + "\n\nأنشئ سؤال واحد فقط بالتنسيق المحدد. بدون نص إضافي."
    
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

# Keep compatibility functions
def extract_contextual_mcq_parts(gpt_output):
    question_sentence, target_word, choices, correct_answer = parse_contextual_response(gpt_output)
    if question_sentence and choices:
        question_part = f"السؤال: {question_sentence}\nما معنى كلمة \"{target_word}\" في السياق أعلاه؟\n" + "\n".join(choices)
        answer_line = f"الإجابة الصحيحة: ({correct_answer})" if correct_answer else None
        return question_part, answer_line
    return None, None

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
