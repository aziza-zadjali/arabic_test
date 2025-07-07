from openai_utils import generate_mcq_arabic_word_meaning

def create_question(main_word, reference_questions, grade):
    return generate_mcq_arabic_word_meaning(main_word, reference_questions, grade)
