from openai_utils import (
    generate_mcq_arabic_word_meaning,
    generate_meaning_test_llm,
    generate_mcq_contextual_word_meaning,
    generate_contextual_test_llm
)

# Word meaning MCQ
def create_question(main_word, reference_questions, grade):
    return generate_mcq_arabic_word_meaning(main_word, reference_questions, grade)

def generate_meaning_test(num_questions, reference_questions, grade):
    return generate_meaning_test_llm(num_questions, reference_questions, grade)

# Contextual word meaning MCQ (single)
def generate_contextual_question(reference_questions, grade):
    return generate_mcq_contextual_word_meaning(reference_questions, grade)

# Contextual word meaning MCQ (test)
def generate_contextual_test(num_questions, reference_questions, grade):
    return generate_contextual_test_llm(num_questions, reference_questions, grade)
