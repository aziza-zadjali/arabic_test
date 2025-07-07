import openai
import re
from config import get_openai_api_key

client = openai.OpenAI(api_key=get_openai_api_key())

PROMPT_HEADER = """
You are an expert in Arabic language assessment. Generate a multiple-choice question (MCQ) for the meaning of an Arabic word.

Instructions:
- All four answer choices must have the same morphological pattern (وزن) and the same number of letters as each other (not necessarily as the main word).
- Do NOT include the main word as a choice.
- All choices must be close in meaning (synonyms or related words).
- Present the choices in the following format, each on a new line:
أ) ...
ب) ...
ج) ...
د) ...
- Clearly indicate the correct answer.

Examples:
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

الكلمة الرئيسية: "الدجى"
الخيارات:
أ - الأصيل
ب - الظلام
ج - الشفق
د - النور

الكلمة الرئيسية: "الخضوع"
الخيارات:
أ - الجحود
ب - القعود
ج - الركوع
د - الخشوع

الكلمة الرئيسية: "برع"
الخيارات:
أ - فاق
ب - رام
ج - نام
د - خاف

الكلمة الرئيسية: "عتيق"
الخيارات:
أ - حديث
ب - جميل
ج - قديم
د - عنيف

الكلمة الرئيسية: "طأطأ"
الخيارات:
أ - خفض
ب - رفع
ج - مال
د - دفع
---
أنت خبير في إعداد أسئلة اللغة العربية. أنشئ سؤال اختيار من متعدد لمعنى كلمة عربية.

التعليمات:
- الكلمة الرئيسية وجميع الخيارات يجب أن تكون باللغة العربية فقط.
- يجب أن يكون لجميع الخيارات الأربعة نفس الوزن الصرفي (مثل: تفعيل، فعيل، مفعول، إلخ) ونفس عدد الحروف مع بعضها البعض (ليس بالضرورة مع الكلمة الرئيسية).
- لا يجب أن تتكرر الكلمة الرئيسية في الخيارات.
- جميع الخيارات يجب أن تكون متقاربة في المعنى (مرادفات أو كلمات ذات صلة).
- قدم الخيارات بالتنسيق التالي، كل خيار في سطر جديد:
أ) ...
ب) ...
ج) ...
د) ...
- حدد بوضوح الخيار الصحيح.

أمثلة:
(نفس الأمثلة أعلاه)
---
"""

def extract_choices_and_answer(gpt_output, main_word=None):
    lines = gpt_output.strip().split('\n')
    choices = []
    answer = ""
    question = ""
    for line in lines:
        if "ما معنى" in line:
            question = line.strip()
        elif re.match(r'^[أ-د]\)?[\s\-–—]+', line.strip()):
            choices.append(line.strip())
        elif "الإجابة الصحيحة" in line or "الإجابة" in line:
            answer = line.strip()
    if not choices:
        choices = [l for l in lines if l.strip().startswith(('أ', 'ب', 'ج', 'د'))]

    if main_word:
        choices = [c for c in choices if main_word not in c]

    # Enforce same length for all choices
    def clean_choice(choice):
        return re.sub(r'^[أ-د]\)?[\s\-–—]+', '', choice).strip()
    if choices:
        target_len = len(clean_choice(choices[0]))
        filtered = [c for c in choices if len(clean_choice(c)) == target_len]
        if len(filtered) == 4:
            choices = filtered

    formatted_choices = "\n".join(choices)
    formatted_question = f"{question}\n\n{formatted_choices}"

    correct = ""
    if answer:
        m = re.search(r'([أ-د])\)?[ \-–—]*(\\S+)?', answer)
        if m:
            letter = m.group(1)
            for ch in choices:
                if ch.startswith(letter):
                    correct = ch
                    break
            else:
                correct = answer
        else:
            correct = answer
    else:
        correct = "غير محدد"

    return formatted_question, correct

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
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
    return extract_choices_and_answer(gpt_output, main_word=main_word)

def generate_meaning_test_llm(num_questions, reference_questions, grade):
    prompt = f"""{PROMPT_HEADER}
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

    blocks = re.split(r'\n(?=\d+\.\s|ما معنى)', gpt_output)
    questions = []
    for block in blocks:
        if "ما معنى" in block:
            q, a = extract_choices_and_answer(block)
            questions.append((q, a))
        if len(questions) >= num_questions:
            break
    if len(questions) < num_questions:
        more_blocks = gpt_output.split('\n\n')
        for block in more_blocks:
            if "ما معنى" in block and (block, "") not in questions:
                q, a = extract_choices_and_answer(block)
                questions.append((q, a))
            if len(questions) >= num_questions:
                break
    return questions[:num_questions]
