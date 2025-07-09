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

def words_are_same(word1, word2):
    """Check if two words are the same, considering ال prefix"""
    w1 = normalize_al(word1.strip())
    w2 = normalize_al(word2.strip())
    return w1.lower() == w2.lower()

def is_semantically_related(main_word, candidate, client, model="gpt-4.1"):
    """Check if candidate is a true synonym of main_word"""
    prompt = f"""Are "{normalize_al(candidate)}" and "{normalize_al(main_word)}" true synonyms in Arabic? Answer only نعم (yes) if they are synonyms, or لا (no) if they are different in meaning."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )
    answer = response.choices[0].message.content.strip()
    return 'نعم' in answer

def extract_candidate_words(gpt_output, main_word):
    lines = gpt_output.strip().split('\n')
    words = []
    collecting = False
    for line in lines:
        l = line.strip()
        if l.startswith("كلمات:") or l.startswith("الخيارات:") or l.startswith("المشتتات:"):
            collecting = True
            continue
        if l.startswith("وزن:") or l.startswith("الإجابة الصحيحة:"):
            collecting = False
            continue
        if collecting:
            # Remove markers like (صحيح)
            word = l.replace('(صحيح)', '').replace('-', '').replace('–', '').replace('—', '').strip()
            if word and main_word not in word and len(word.split()) == 1 and word != "الخيارات:":
                words.append(word)
    
    # Also look for correct answer
    correct_answer = None
    for line in lines:
        if line.startswith("الإجابة الصحيحة:"):
            correct_answer = line.split(":", 1)[1].strip()
            break
    
    if not words:
        for line in lines:
            word = line.strip().replace('(صحيح)', '').replace('-', '').replace('–', '').replace('—', '').strip()
            if word and main_word not in word and len(word.split()) == 1 and word != "الخيارات:" and not word.startswith("وزن:") and not word.startswith("الإجابة"):
                words.append(word)
    
    return words, correct_answer

def generate_intelligent_fallback(main_word, client):
    """Generate fallback choices using LLM with specific instructions"""
    prompt = f"""
    للكلمة العربية "{main_word}":
    1. اكتب مرادف واحد دقيق (الإجابة الصحيحة)
    2. اكتب 3 كلمات مختلفة المعنى تماماً كمشتتات (ليست مرادفات)
    
    **مهم جداً:**
    - لا تدرج الكلمة الرئيسية "{main_word}" نفسها
    - تأكد من أن المشتتات ليست مرادفات للكلمة الرئيسية
    - استخدم نفس الشكل (مع أو بدون ال) مثل الكلمة الأصلية
    
    تنسيق الإجابة:
    الإجابة الصحيحة: [المرادف]
    المشتتات:
    [مشتت 1]
    [مشتت 2]
    [مشتت 3]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        
        gpt_output = response.choices[0].message.content.strip()
        words, correct_answer = extract_candidate_words(gpt_output, main_word)
        
        if correct_answer and len(words) >= 3:
            # Apply ال consistency
            if has_al(main_word):
                correct_answer = correct_answer if correct_answer.startswith("ال") else "ال" + correct_answer
                words = [w if w.startswith("ال") else "ال" + w for w in words]
            else:
                correct_answer = correct_answer[2:] if correct_answer.startswith("ال") else correct_answer
                words = [w[2:] if w.startswith("ال") else w for w in words]
            
            # Filter out main word and root-sharing words
            filtered_words = [w for w in words if not words_are_same(w, main_word) and not share_root(main_word, w)]
            
            if len(filtered_words) >= 3:
                return [correct_answer] + filtered_words[:3]
    
    except Exception as e:
        pass
    
    # Ultimate fallback - generic but semantically safe choices
    if has_al(main_word):
        return ["الفهم", "الجهل", "السرعة", "القوة"]
    else:
        return ["فهم", "جهل", "سرعة", "قوة"]

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
الكلمة الرئيسية: "{main_word}"
الأسئلة المرجعية: {reference_questions[:3]}
أنشئ إجابة صحيحة واحدة (مرادف دقيق) وثلاثة مشتتات واضحة المعنى المختلف للكلمة "{main_word}".
"""
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=400,
            )
            gpt_output = response.choices[0].message.content.strip()
            candidate_words, correct_answer = extract_candidate_words(gpt_output, main_word)
            
            # Remove words with same root and main word itself
            candidate_words = [w for w in candidate_words if not share_root(main_word, w) and not words_are_same(w, main_word)]
            
            if len(candidate_words) >= 3 and correct_answer:
                # Apply ال consistency
                if has_al(main_word):
                    correct_answer = correct_answer if correct_answer.startswith("ال") else "ال" + correct_answer
                    candidate_words = [w if w.startswith("ال") else "ال" + w for w in candidate_words]
                else:
                    correct_answer = correct_answer[2:] if correct_answer.startswith("ال") else correct_answer
                    candidate_words = [w[2:] if w.startswith("ال") else w for w in candidate_words]
                
                # Validate semantic correctness
                if is_semantically_related(main_word, correct_answer, client):
                    # Use the validated correct answer
                    choices = [correct_answer] + candidate_words[:3]
                    break
        except Exception as e:
            continue
    else:
        # All attempts failed, use intelligent fallback
        choices = generate_intelligent_fallback(main_word, client)
    
    # Ensure we have exactly 4 choices
    while len(choices) < 4:
        if has_al(main_word):
            choices.append("الخير")
        else:
            choices.append("خير")
    
    choices = choices[:4]
    
    # Find correct answer position (first choice is correct by design)
    correct_synonym = choices[0]
    
    # Shuffle choices but keep track of correct answer position
    import random
    random.shuffle(choices)
    correct_index = choices.index(correct_synonym)

    letters = ['أ', 'ب', 'ج', 'د']
    display_choices = [f"{letters[i]}) {choices[i]}" for i in range(4)]
    question = f"ما معنى كلمة \"{main_word}\"؟\n\n" + "\n".join(display_choices)
    answer = display_choices[correct_index]
    
    msg = None
    if len(candidate_words) < 3:
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
        
        # Format with proper line breaks
        formatted_question = "السؤال:\n"
        formatted_question += "\n".join(question_lines) + "\n\n"
        formatted_question += "\n".join(filtered_choices)
        
        return formatted_question.strip(), answer_line
    except Exception as e:
        return None, None

def generate_contextual_test_llm(num_questions, reference_questions, grade):
    questions = []
    max_attempts = num_questions * 15
    attempts = 0
    
    while len(questions) < num_questions and attempts < max_attempts:
        attempts += 1
        try:
            q, answer_line = generate_mcq_contextual_word_meaning(reference_questions, grade)
            if q and answer_line and len(q.strip()) > 50:
                questions.append((q, answer_line))
        except Exception as e:
            continue
    
    return questions
