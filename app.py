import streamlit as st
from reference_loader import load_reference_questions
from question_generator import create_question, generate_meaning_test

grades = ["الصف السابع والثامن"]
skills = {"الأسئلة اللفظية": "الأسئلة_اللفظية"}

st.title("مولد أسئلة معاني الكلمات")
st.write("اختر أحد الخيارين: توليد سؤال لمعنى كلمة، أو توليد اختبار معاني كلمات كامل.")

option = st.radio(
    "اختر نوع التوليد:",
    ("توليد سؤال لمعنى كلمة", "توليد اختبار معاني الكلمات (تلقائي)")
)

selected_grade = grades[0]
selected_skill_label = list(skills.keys())[0]
selected_skill_folder = skills[selected_skill_label]

if option == "توليد سؤال لمعنى كلمة":
    main_word = st.text_input("أدخل الكلمة الرئيسية (بالعربية)")
    if st.button("توليد سؤال"):
        with st.spinner("يتم توليد السؤال..."):
            grade_folder = "الصف_السابع_والثامن"
            reference_questions = load_reference_questions(grade_folder, selected_skill_folder)
            if not reference_questions:
                st.error("لا توجد أسئلة مرجعية في هذه المرحلة/المهارة. تأكد من وجود الملفات في المسار الصحيح.")
            elif not main_word.strip():
                st.error("يرجى إدخال كلمة رئيسية.")
            else:
                question, answer = create_question(main_word, reference_questions, selected_grade)
                st.markdown(question)
                st.success(f"الإجابة الصحيحة: {answer}")

else:
    num_questions = st.slider("عدد الأسئلة في الاختبار", 1, 5, 3)
    if st.button("توليد اختبار"):
        with st.spinner("يتم توليد الاختبار..."):
            grade_folder = "الصف_السابع_والثامن"
            reference_questions = load_reference_questions(grade_folder, selected_skill_folder)
            if not reference_questions:
                st.error("لا توجد أسئلة مرجعية في هذه المرحلة/المهارة. تأكد من وجود الملفات في المسار الصحيح.")
            else:
                test = generate_meaning_test(num_questions, reference_questions, selected_grade)
                for idx, (question, answer) in enumerate(test, 1):
                    st.markdown(f"**{idx}. {question}**")
                    st.success(f"الإجابة الصحيحة: {answer}")
