import openai
from config import get_openai_api_key

# Initialize the OpenAI client
client = openai.OpenAI(api_key=get_openai_api_key())

def generate_mcq_arabic_word_meaning(main_word, reference_questions, grade):
    prompt = f"""
أنت معلم لغة عربية. أنشئ سؤال اختيار من متعدد لمعنى كلمة عربية للصف {grade}.
- الكلمة الرئيسية وجميع الخيارات يجب أن تكون باللغة العربية فقط.
- يجب أن يكون لجميع الخيارات الأربعة نفس الوزن وعدد الحروف للكلمة الرئيسية.
- جميع الخيارات يجب أن تكون متقاربة في المعنى (مرادفات أو كلمات ذات صلة).
- لا تتضمن الكلمة الأصلية نفسها في أي من الخيارات.
الكلمة الرئيسية: {main_word}
الأسئلة المرجعية: {reference_questions[:3]}
صيغة السؤال:
ما معنى كلمة "{main_word}"؟
A) ...
B) ...
C) ...
D) ...
الإجابة الصحيحة: (حدد الخيار الصحيح فقط)
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()
