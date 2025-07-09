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
- Do NOT include the main word itself
- The correct answer should be a true synonym or very close in meaning
- The three distractors should be plausible but clearly different in meaning
- Avoid words with the same root as the main word
- **PREFERRED**: Try to ensure all four answer choices (correct answer + 3 distractors) have the same Arabic morphological pattern (وزن) and similar letter count when possible
- **FLEXIBILITY**: If better educational distractors are available that don't match the pattern, prioritize educational value over pattern consistency
- The morphological pattern matching applies ONLY to the answer choices themselves, NOT to the main word
- Format: You may list the words in any order - no need to list the correct answer first

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

الكلمة الرئيسية: "ترويج"
وزن الخيارات: تفعيل (pattern consistency prioritized)
الخيارات:
تسويق (صحيح)
تغليف
تنفيذ
ترحيل

الكلمة الرئيسية: "مآثر"
وزن الخيارات: مفاعل (pattern consistency prioritized)
الخيارات:
محاسن (صحيح)
مساكن
مداخل
مراجع

الكلمة الرئيسية: "الأصل"
وزن الخيارات: متنوع (educational value prioritized over pattern)
الخيارات:
الصباح (صحيح - time reference)
السحر
الغروب
الظهيرة

الكلمة الرئيسية: "الدجى"
وزن الخيارات: متنوع (educational value prioritized over pattern)
الخيارات:
الظلام (صحيح)
الأصيل
الشفق
النور

الكلمة الرئيسية: "عتيق"
وزن الخيارات: متنوع (educational value prioritized over pattern)
الخيارات:
قديم (صحيح)
حديث
جميل
عنيف

الكلمة الرئيسية: "طأطأ"
وزن الخيارات: متنوع (educational value prioritized over pattern)
الخيارات:
خفض (صحيح)
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
- **PREFERRED**: Try to ensure all four answer choices have the same Arabic morphological pattern (وزن) and similar letter count when possible
- **FLEXIBILITY**: If better educational distractors are available that don't match the pattern, prioritize educational value over pattern consistency
- The morphological pattern matching applies ONLY to the answer choices themselves, NOT to the underlined word
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

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"
الأسئلة المرجعية: {reference_questions[:3]}

أنشئ إجابة صحيحة واحدة (مرادف) وثلاثة مشتتات مناسبة للكلمة "{main_word}".
حاول جعل الخيارات الأربعة لها نفس الوزن الصرفي عند الإمكان، لكن إذا كانت هناك مشتتات تعليمية أفضل بأوزان مختلفة، فاختر القيمة التعليمية.
الخيارات لا تحتاج لنفس وزن الكلمة الرئيسية - ركز على جعل الخيارات الأربعة متسقة مع بعضها البعض أو ذات قيمة تعليمية عالية.
"""
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=300,
    )
    
    gpt_output = response.choices[0].message.content.strip()
    
    # Extract choices and identify correct answer
    correct_answer = None
    all_choices = []
    
    lines = gpt_output.split('\n')
    collecting_choices = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("الخيارات:"):
            collecting_choices = True
            continue
        elif collecting_choices and line:
            # Check if this line contains the correct answer marker
            if "(صحيح)" in line:
                correct_answer = line.replace("(صحيح)", "").strip()
                all_choices.append(correct_answer)
            elif line and not line.startswith("الكلمة") and not line.startswith("وزن"):
                all_choices.append(line)
    
    # Fallback if parsing fails
    if not correct_answer or len(all_choices) < 4:
        return generate_fallback_mcq(main_word, client)
    
    # Ensure consistent "ال" usage
    if has_al(main_word):
        correct_answer = correct_answer if correct_answer.startswith("ال") else "ال" + correct_answer
        all_choices = [choice if choice.startswith("ال") else "ال" + choice for choice in all_choices]
    else:
        correct_answer = correct_answer[2:] if correct_answer.startswith("ال") else correct_answer
        all_choices = [choice[2:] if choice.startswith("ال") else choice for choice in all_choices]
    
    # Remove words with same root
    filtered_choices = [choice for choice in all_choices if not share_root(main_word, choice)]
    
    # Ensure we have exactly 4 choices
    if len(filtered_choices) < 4:
        filtered_choices = all_choices[:4]
    
    choices = filtered_choices[:4]
    
    # Find correct answer in filtered choices, or use first as fallback
    if correct_answer in choices:
        correct_index = choices.index(correct_answer)
    else:
        correct_index = 0
        correct_answer = choices[0]
    
    # Shuffle choices but keep track of correct answer position
    import random
    random.shuffle(choices)
    correct_index = choices.index(correct_answer)
    
    letters = ['أ', 'ب', 'ج', 'د']
    display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
    question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
    answer = display_choices[correct_index]
    
    return question, answer, None

def generate_fallback_mcq(main_word, client):
    """Generate fallback MCQ when main prompt fails"""
    prompt = f"""
    للكلمة العربية "{main_word}":
    1. اكتب مرادف واحد صحيح
    2. اكتب 3 كلمات مختلفة المعنى كمشتتات
    3. حاول جعل الكلمات الأربعة لها نفس الوزن الصرفي عند الإمكان، لكن إذا كانت هناك مشتتات تعليمية أفضل بأوزان مختلفة، فاختر القيمة التعليمية
    4. الخيارات لا تحتاج لنفس وزن الكلمة الرئيسية - ركز على جعل الخيارات الأربعة متسقة مع بعضها البعض أو ذات قيمة تعليمية عالية
    
    استخدم نفس الشكل (مع أو بدون ال) مثل الكلمة الأصلية.
    اكتب كل كلمة في سطر منفصل.
    """
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150,
    )
    
    words = []
    for line in response.choices[0].message.content.strip().split('\n'):
        word = line.strip()
        if word and len(word.split()) == 1:
            words.append(word)
    
    if len(words) < 4:
        # Ultimate fallback
        if has_al(main_word):
            words = ["الفهم", "الجهل", "السرعة", "القوة"]
        else:
            words = ["فهم", "جهل", "سرعة", "قوة"]
    
    choices = words[:4]
    letters = ['أ', 'ب', 'ج', 'د']
    display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
    question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
    answer = display_choices[0]  # First word is assumed correct
    
    return question, answer, "تم استخدام خيارات احتياطية لضمان توليد السؤال."

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

def format_contextual_question(question_text):
    """Format contextual question for better readability"""
    lines = question_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a choice line (starts with أ- ب- ج- د-)
        if re.match(r'^[أ-د][\)\-]', line):
            formatted_lines.append(f"  {line}")
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

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
        question_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if it's a choice line
            m = re.match(r'^([أ-د][\)\-]?)\s*(.+)', line)
            if m:
                choices.append(f"{m.group(1)}) {m.group(2)}")
            else:
                question_lines.append(line)
        
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
        
        # Format the final question with proper line breaks
        formatted_question = '\n'.join(question_lines) + '\n\n' + '\n'.join(filtered_choices)
        
        return formatted_question.strip(), answer_line
    except Exception as e:
        return None, None

def generate_contextual_test_llm(num_questions, reference_questions, grade):
    questions = []
    max_attempts = num_questions * 20  # Increased attempts to ensure we get the requested number
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
