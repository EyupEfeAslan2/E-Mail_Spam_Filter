import re

import emoji


def clean_text(text: str) -> str:
    """Basic normalization used by both training and inference paths."""
    text = emoji.demojize(text, delimiters=(" ", " "))
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"http\S+|www\S+|https\S+", "[URL]", text, flags=re.MULTILINE)
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text
