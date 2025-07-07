import streamlit as st
from reference_loader import load_reference_questions
from question_generator import create_question

# Only one grade option
grades = ["الصف السابع والثامن"]

# Skill mapping: display name -> folder name
skills = {"الأسئلة اللفظية": "الأسئلة_اللفظية"}
question_types = ["معنى الكلمة"]

st.title("مولد أسئلة اللغة العربية")
st.write("اختر المرحلة والمهارة ونوع السؤال، ثم أدخل الكلمة الرئيسية لتوليد سؤال اختيار من متعدد.")

# User selections
selected_grade = st.selectbox("اختر المرحلة", grades)
selected_skill_label = st.selectbox("اختر المهارة", list(skills.keys()))
selected_skill_folder = skills[selected_skill_label]
selected_qtype = st.selectbox("اختر نوع السؤال", question_types)

main_word = st.text_input("أدخل الكلمة الرئيسية (بالعربية)")

if st.button("توليد سؤال"):
    with st.spinner("يتم توليد السؤال..."):
        # Use the unified grade folder and mapped skill folder
        grade_folder = "الصف_السابع_والثامن"
        reference_questions = load_reference_questions(grade_folder, selected_skill_folder)
        if not reference_questions:
            st.error("لا توجد أسئلة مرجعية في هذه المرحلة/المهارة. تأكد من وجود الملفات في المسار الصحيح.")
        elif not main_word.strip():
            st.error("يرجى إدخال كلمة رئيسية.")
        else:
            question = create_question(main_word, reference_questions, selected_grade)
            st.markdown("### السؤال:")
            st.markdown(question)
