import os
from docx import Document
import PyPDF2

def load_reference_questions(grade, skill):
    folder_path = os.path.join("data", grade, skill)
    questions = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".docx"):
            doc = Document(os.path.join(folder_path, filename))
            for para in doc.paragraphs:
                if para.text.strip():
                    questions.append(para.text.strip())
        elif filename.endswith(".pdf"):
            with open(os.path.join(folder_path, filename), "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        questions.extend([line for line in text.split("\n") if line.strip()])
    return questions
