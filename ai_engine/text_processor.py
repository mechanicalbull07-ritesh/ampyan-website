import re

def clean_text(text):

    text = text.lower()

    # remove punctuation
    text = re.sub(r'[^\w\s]', '', text)

    return text