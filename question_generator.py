from openai_utils import generate_mcq_arabic_word_meaning, generate_meaning_test

def create_question(main_word, reference_questions, grade):
    return generate_mcq_arabic_word_meaning(main_word, reference_questions, grade)

def generate_meaning_test(num_questions, reference_questions, grade):
    return generate_meaning_test(num_questions, reference_questions, grade)
