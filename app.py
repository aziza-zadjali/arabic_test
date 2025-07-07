import streamlit as st
from reference_loader import load_reference_questions
from question_generator import create_question

grades = ["الصف السابع", "الصف الثامن"]
skills = ["الأسئلة اللفظية"]
question_types = ["معنى الكلمة"]

st.title("مولد أسئلة اللغة العربية")
st.write("اختر المرحلة والمهارة ونوع السؤال، ثم أدخل الكلمة الرئيسية لتوليد سؤال اختيار من متعدد.")

grade = st.selectbox("اختر المرحلة", grades)
skill = st.selectbox("اختر المهارة", skills)
question_type = st.selectbox("اختر نوع السؤال", question_types)

main_word = st.text_input("أدخل الكلمة الرئيسية (بالعربية)")

if st.button("توليد سؤال"):
    with st.spinner("يتم توليد السؤال..."):
        reference_questions = load_reference_questions(grade, skill)
        if not reference_questions:
            st.error("لا توجد أسئلة مرجعية في هذه المرحلة/المهارة.")
        elif not main_word.strip():
            st.error("يرجى إدخال كلمة رئيسية.")
        else:
            question = create_question(main_word, reference_questions, grade)
            st.markdown("### السؤال:")
            st.markdown(question)
