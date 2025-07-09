import streamlit as st
import re
from reference_loader import load_reference_questions
from question_generator import (
    create_question,
    generate_meaning_test,
    generate_contextual_question,
    generate_contextual_test
)

# Custom CSS for better formatting without markdown symbols
st.markdown("""
<style>
.question-title {
    color: #1f77b4;
    font-weight: bold;
    font-size: 18px;
    margin: 15px 0 10px 0;
    padding: 0;
}

.question-text {
    font-size: 16px;
    line-height: 1.6;
    margin: 10px 0;
    color: #333;
}

.choice-item {
    background-color: #f8f9fa;
    padding: 8px 15px;
    margin: 5px 0;
    border-radius: 5px;
    border-left: 3px solid #007bff;
    font-size: 16px;
    color: #333;
}

.correct-answer {
    background-color: #d4edda;
    color: #155724;
    padding: 10px 15px;
    border-radius: 5px;
    border-left: 4px solid #28a745;
    margin: 15px 0;
    font-weight: bold;
}

.question-separator {
    border: none;
    height: 2px;
    background: linear-gradient(to right, #007bff, transparent);
    margin: 25px 0;
}

.contextual-question {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #17a2b8;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

grades = ["الصف السابع والثامن"]
skills = {"الأسئلة اللفظية": "الأسئلة_اللفظية"}

st.title("🎓 مولد أسئلة اللغة العربية")

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

# Set defaults
selected_grade = grades[0]
selected_skill_label = list(skills.keys())[0]
selected_skill_folder = skills[selected_skill_label]

def display_formatted_question(question_text, question_number=None):
    """Display question with enhanced formatting without markdown"""
    lines = question_text.split('\n')
    
    # Extract question title and choices
    question_title = ""
    choices = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if re.match(r'^[أ-د][\)\-]', line):
            choices.append(line)
        else:
            if question_title:
                question_title += " " + line
            else:
                question_title = line
    
    # Display with custom formatting
    if question_number:
        st.markdown(f'<div class="question-title">السؤال {question_number}:</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="question-text">{question_title}</div>', unsafe_allow_html=True)
    
    # Display choices with better formatting
    for choice in choices:
        st.markdown(f'<div class="choice-item">{choice}</div>', unsafe_allow_html=True)

def display_contextual_question(question_text, question_number=None):
    """Display contextual questions with special formatting - no markdown"""
    if question_number:
        st.markdown(f'<div class="question-title">السؤال {question_number}:</div>', unsafe_allow_html=True)
    
    # Parse the question content - remove any markdown formatting
    lines = question_text.split('\n')
    question_content = []
    choices = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove markdown formatting
        line = line.replace('**', '')
        if re.match(r'^[أ-د][\)\-]', line):
            choices.append(line)
        else:
            question_content.append(line)
    
    # Display question content
    content_text = '\n'.join(question_content)
    st.markdown(f'<div class="contextual-question">{content_text}</div>', unsafe_allow_html=True)
    
    # Display choices
    for choice in choices:
        st.markdown(f'<div class="choice-item">{choice}</div>', unsafe_allow_html=True)

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
                
                # Display formatted question
                display_formatted_question(question)
                
                # Display answer with custom styling
                st.markdown(f'<div class="correct-answer">✅ الإجابة الصحيحة: {answer}</div>', unsafe_allow_html=True)

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
                else:
                    st.success(f"✅ تم توليد {len(test)} أسئلة بنجاح!")
                    
                    for idx, (question, answer, msg) in enumerate(test, 1):
                        if msg:
                            st.warning(f"سؤال {idx}: {msg}")
                        
                        # Display formatted question
                        display_formatted_question(question, idx)
                        
                        # Display answer with custom styling
                        st.markdown(f'<div class="correct-answer">✅ الإجابة الصحيحة: {answer}</div>', unsafe_allow_html=True)
                        
                        # Add separator between questions
                        if idx < len(test):
                            st.markdown('<hr class="question-separator">', unsafe_allow_html=True)

elif question_type == "معنى الكلمة حسب السياق":
    num_questions = st.slider("عدد الأسئلة في الاختبار", 1, 5, 1)
    if st.button("توليد سؤال/اختبار"):
        with st.spinner("يتم توليد الأسئلة..."):
            grade_folder = "الصف_السابع_والثامن"
            reference_questions = load_reference_questions(grade_folder, selected_skill_folder)
            if not reference_questions:
                st.error("لا توجد أسئلة مرجعية في هذه المرحلة/المهارة. تأكد من وجود الملفات في المسار الصحيح.")
            else:
                # Always use the test function to ensure consistent behavior
                test = generate_contextual_test(num_questions, reference_questions, selected_grade)
                
                if not test or len(test) < num_questions:
                    st.error(f"تعذر توليد العدد المطلوب من الأسئلة السياقية ({num_questions}). تم توليد {len(test) if test else 0} أسئلة فقط. حاول مجددًا.")
                    
                    # Display whatever questions were generated
                    if test:
                        for idx, (question, answer_line) in enumerate(test, 1):
                            display_contextual_question(question, idx)
                            st.markdown(f'<div class="correct-answer">✅ {answer_line}</div>', unsafe_allow_html=True)
                            if idx < len(test):
                                st.markdown('<hr class="question-separator">', unsafe_allow_html=True)
                else:
                    st.success(f"✅ تم توليد {len(test)} أسئلة بنجاح!")
                    
                    for idx, (question, answer_line) in enumerate(test, 1):
                        display_contextual_question(question, idx)
                        st.markdown(f'<div class="correct-answer">✅ {answer_line}</div>', unsafe_allow_html=True)
                        
                        # Add separator between questions (except for the last one)
                        if idx < len(test):
                            st.markdown('<hr class="question-separator">', unsafe_allow_html=True)
