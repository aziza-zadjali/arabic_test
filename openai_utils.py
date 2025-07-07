import openai
from config import get_openai_api_key

# Initialize the OpenAI client
client = openai.OpenAI(api_key=get_openai_api_key())

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""
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
Note: The correct answer for "مآثر" is "د" (محاسن), as it is closest in meaning. The other options do not match the correct meaning.

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
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()
