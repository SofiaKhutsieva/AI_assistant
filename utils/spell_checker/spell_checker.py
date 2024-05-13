from spellchecker import SpellChecker

spell = SpellChecker()

def spell_check(text):
    words = text.split()
    misspelled = spell.unknown(words)

    corrected_text = ""
    for word in words:
        if word in misspelled:
            corrected_text += spell.correction(word) + " "
        else:
            corrected_text += word + " "

    return corrected_text.strip()

# Пример использования
user_input = "Helo, howw are yu?"
corrected_input = spell_check(user_input)
print(corrected_input)