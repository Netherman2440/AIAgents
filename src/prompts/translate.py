def translate_prompt(target_language: str) -> str:
    return f"""Translate the user conversation transcript to {target_language}.
    Carefully save text structure and punctuation.
    Keep in mind that some words must stay in English as they are technical or business terms.
    Return the translated text in {target_language} language."""

def fix_translation_prompt() -> str:
    return f"""Your main task is to fix the translation of the user text.
    Focus on fixing words which have no sense in the context of the sentence.
    Make sure that your change is not changing the original meaning of the sentence.
    Return all text with the same structure and punctuation as the original text."""
