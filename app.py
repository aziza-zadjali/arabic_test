import streamlit as st

from reference_loader import load_reference_questions

from question_generator import (
    create_question,
    generate_meaning_test,
    generate_contextual_question,
    generate_contextual_test
)

grades = ["الصف السابع والثامن"]
skills = {"الأسئلة اللفظية": "الأسئلة_اللفظية"}

st.title("مولد أسئلة اللغة العربية")

selected_grade = st.selectbox("اختر الصف الدراسي:", grades)
selected_skill_label = st.selectbox("اختر المهارة:", list(skills.keys()))
selected_skill_folder = skills[selected_skill_label]

question_type = st.selectbox(
    "اختر نوع السؤال:",
    [
        "معنى الكلمة",
        "اختبار معاني الكلمات (تلقائي)",
        "معنى الكلمة حسب السياق"
    ]
)

selected_grade = grades[0]
selected_skill_label = list(skills.keys())[0]
selected_skill_folder = skills[selected_skill_label]

if question_type == "معنى الكلمة":
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
                question, answer, msg = create_question(main_word, reference_questions, selected_grade)
                if msg:
                    st.warning(msg)
                st.markdown(question)
                st.success(f"الإجابة الصحيحة: {answer}")

elif question_type == "اختبار معاني الكلمات (تلقائي)":
    num_questions = st.slider("عدد الأسئلة في الاختبار", 1, 5, 3)
    if st.button("توليد اختبار"):
        with st.spinner("يتم توليد الاختبار..."):
            grade_folder = "الصف_السابع_والثامن"
            reference_questions = load_reference_questions(grade_folder, selected_skill_folder)
            if not reference_questions:
                st.error("لا توجد أسئلة مرجعية في هذه المرحلة/المهارة. تأكد من وجود الملفات في المسار الصحيح.")
            else:
                test = generate_meaning_test(num_questions, reference_questions, selected_grade)
                if not test:
                    st.error("تعذر توليد عدد كافٍ من الأسئلة بمعنى صحيح. حاول مجددًا أو قلل عدد الأسئلة.")
                for idx, (question, answer, msg) in enumerate(test, 1):
                    if msg:
                        st.warning(f"سؤال {idx}: {msg}")
                    st.markdown(f"**{idx}. {question}**")
                    st.success(f"الإجابة الصحيحة: {answer}")

elif question_type == "معنى الكلمة حسب السياق":
    num_questions = st.slider("عدد الأسئلة في الاختبار", 1, 5, 1)
    if st.button("توليد سؤال/اختبار"):
        with st.spinner("يتم توليد السؤال..."):
            grade_folder = "الصف_السابع_والثامن"
            reference_questions = load_reference_questions(grade_folder, selected_skill_folder)
            if not reference_questions:
                st.error("لا توجد أسئلة مرجعية في هذه المرحلة/المهارة. تأكد من وجود الملفات في المسار الصحيح.")
            else:
                if num_questions == 1:
                    question, answer_line = generate_contextual_question(reference_questions, selected_grade)
                    if question and answer_line:
                        # Format the question with proper line breaks
                        formatted_question = question.replace('\n\n', '\n\n')
                        st.markdown(f"**السؤال:**\n\n{formatted_question}")
                        st.success(answer_line)
                    else:
                        st.error("تعذر توليد السؤال. حاول مجددًا.")
                else:
                    test = generate_contextual_test(num_questions, reference_questions, selected_grade)
                    if not test:
                        st.error("تعذر توليد عدد كافٍ من الأسئلة السياقية. حاول مجددًا أو قلل العدد.")
                    else:
                        for idx, (question, answer_line) in enumerate(test, 1):
                            # Format each question with proper line breaks
                            formatted_question = question.replace('\n\n', '\n\n')
                            st.markdown(f"**السؤال {idx}:**\n\n{formatted_question}")
                            if answer_line:
                                st.success(answer_line)
                            st.markdown("---")  # Add separator between questions
