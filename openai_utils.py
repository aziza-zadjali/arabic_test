import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

PROMPT_HEADER = """
You are an expert in Arabic language assessment. Generate a multiple-choice question (MCQ) for the meaning of an Arabic word.

Instructions:
- The main word and all answer choices must be in Arabic only.
- All four answer choices must have the same morphological pattern (وزن) and the same number of letters as each other. The pattern and letter count do NOT need to match the main word.
- None of the choices should be the same as the main word.
- All choices must be close in meaning (synonyms or related words).
- Clearly indicate which option is the correct answer.
- If you cannot find four suitable options, do your best to create plausible distractors.

Examples:
Main word: "ترويج"
Choices:
أ - تسويق
ب - تغليف
ج - تنفيذ
د - ترحيل

Main word: "مآثر"
Choices:
أ - مساكن
ب - مداخل
ج - مراجع
د - محاسن
Note: The correct answer for "مآثر" is "د" (محاسن), as it is closest in meaning.

معاني الكلمات MCQ examples:
1. الدجى:
أ- الأصيل    ب- الظلام    ج- الشفق    د- النور

2. الخضوع:
أ- الجحود    ب- القعود    ج- الركوع    د- الخشوع

3. برع:
أ- فاق    ب- رام    ج- نام    د- خاف

4. عتيق:
أ- حديث    ب- جميل    ج- قديم    د- عنيف

5. طأطأ:
أ- خفض    ب- رفع    ج- مال    د- دفع

---

أنت خبير في إعداد أسئلة اللغة العربية. أنشئ سؤال اختيار من متعدد لمعنى كلمة عربية.

التعليمات:
- الكلمة الرئيسية وجميع الخيارات يجب أن تكون باللغة العربية فقط.
- يجب أن يكون لجميع الخيارات الأربعة نفس الوزن الصرفي (مثل: تفعيل، فعيل، مفعول، إلخ) ونفس عدد الحروف مع بعضها البعض (ليس بالضرورة مع الكلمة الرئيسية).
- لا يجب أن تتكرر الكلمة الرئيسية في الخيارات.
- جميع الخيارات يجب أن تكون متقاربة في المعنى (مرادفات أو كلمات ذات صلة).
- حدد بوضوح الخيار الصحيح.

أمثلة:
الكلمة الرئيسية: "ترويج"
الخيارات:
أ - تسويق
ب - تغليف
ج - تنفيذ
د - ترحيل

الكلمة الرئيسية: "مآثر"
الخيارات:
أ - مساكن
ب - مداخل
ج - مراجع
د - محاسن
ملاحظة: رمز الإجابة الصحيحة لمعنى كلمة "مآثر" هو "د" (محاسن)، إذ أن كلمة "محاسن" هي الأقرب معنى لكلمة "مآثر"، أما بقية البدائل الأخرى فلا تدل على المعنى الصحيح.

اختبار معاني الكلمات:
1. الدجى:
أ- الأصيل    ب- الظلام    ج- الشفق    د- النور

2. الخضوع:
أ- الجحود    ب- القعود    ج- الركوع    د- الخشوع

3. برع:
أ- فاق    ب- رام    ج- نام    د- خاف

4. عتيق:
أ- حديث    ب- جميل    ج- قديم    د- عنيف

5. طأطأ:
أ- خفض    ب- رفع    ج- مال    د- دفع
"""

def extract_choices_and_answer(gpt_output):
    """
    Extracts choices and the correct answer from the GPT output.
    Returns (formatted_question, correct_answer)
    """
    # Find the question line
    lines = gpt_output.strip().split('\n')
    question_line = ""
    choices_lines = []
    answer_line = ""
    for line in lines:
        if "ما معنى" in line:
            question_line = line.strip()
        elif re.match(r'^[أ-د]\)?[\s\-–—]+', line.strip()):
            choices_lines.append(line.strip())
        elif "الإجابة الصحيحة" in line or "الإجابة" in line:
            answer_line = line.strip()

    # If choices are not found, try alternative extraction
    if not choices_lines:
        choices_lines = [l for l in lines if l.strip().startswith(('أ', 'ب', 'ج', 'د'))]

    # Format choices for display
    formatted_choices = "\n".join(choices_lines)
    formatted_question = f"{question_line}\n\n{formatted_choices}"

    # Extract answer letter or text
    answer = ""
    if answer_line:
        # Try to extract letter and text
        m = re.search(r'([أ-د])\)?[ \-–—]*(\S+)?', answer_line)
        if m:
            letter = m.group(1)
            # Try to find full text for this letter
            for ch in choices_lines:
                if ch.startswith(letter):
                    answer = ch
                    break
            else:
                answer = answer_line
        else:
            answer = answer_line
    else:
        answer = "غير محدد"

    return formatted_question, answer

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}

الآن:
الكلمة الرئيسية: "{main_word}"
الأسئلة المرجعية: {reference_questions[:3]}

Question format:
ما معنى كلمة "{main_word}"؟
أ) ...
ب) ...
ج) ...
د) ...
الإجابة الصحيحة: (حدد الخيار الصحيح فقط)
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=400,
    )
    gpt_output = response.choices[0].message.content.strip()
    return extract_choices_and_answer(gpt_output)

def generate_meaning_test(num_questions, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}

الآن:
أنشئ اختبار معاني كلمات مكون من {num_questions} أسئلة، كل سؤال في سطر منفصل، مع عرض الخيارات بشكل واضح، وتوضيح الإجابة الصحيحة لكل سؤال.
الأسئلة المرجعية: {reference_questions[:3]}
صيغة كل سؤال:
ما معنى كلمة "...."؟
أ) ...
ب) ...
ج) ...
د) ...
الإجابة الصحيحة: (حدد الخيار الصحيح فقط)
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1200,
    )
    gpt_output = response.choices[0].message.content.strip()

    # Split questions by finding lines that start with a number or "ما معنى"
    questions = []
    blocks = re.split(r'\n(?=\d+\.\s|ما معنى)', gpt_output)
    for block in blocks:
        if "ما معنى" in block:
            q, a = extract_choices_and_answer(block)
            questions.append((q, a))
        if len(questions) >= num_questions:
            break
    # Fallback: if not enough, try to parse more blocks
    if len(questions) < num_questions:
        # Try to split by double newlines
        more_blocks = gpt_output.split('\n\n')
        for block in more_blocks:
            if "ما معنى" in block and (block, "") not in questions:
                q, a = extract_choices_and_answer(block)
                questions.append((q, a))
            if len(questions) >= num_questions:
                break
    return questions[:num_questions]
