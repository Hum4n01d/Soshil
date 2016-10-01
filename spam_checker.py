import difflib
import enchant
from profanity import profanity


REPEAT_SIMILARITY_THRESHOLD = 0.75
SYMBOLS = r"!@#$%^&*()-_=+[{]}\|;:'\",<.>/?"
SPAM_SIMILARITY_THRESHOLD = 0.5

repeat_frequency = {}


def is_spam(text, user):
    # Check repeat frequency.
    if user not in repeat_frequency:
        repeat_frequency[user] = (1, text)
    else:
        repeat_count, repeat_text = repeat_frequency[user]

        if __get_text_similarity(repeat_text, text) >= REPEAT_SIMILARITY_THRESHOLD:
            repeat_frequency[user] = (repeat_count + 1, text)
        else:
            repeat_frequency[user] = (1, text)

    repeat_level = repeat_frequency[user][0]

    # Check if individual words are spam.
    words = text.split()
    spell = SpellChecker()

    probably_spam = False

    for word in words:
        for s in SYMBOLS:
            word = word.strip(s)

        if not spell.is_word(word):
            suggestions = spell.get_suggestions(word)

            set_spam = True

            if len(suggestions) <= 0:
                probably_spam = True
                break

            for s in suggestions:
                if __get_text_similarity(word, s) >= SPAM_SIMILARITY_THRESHOLD:
                    set_spam = False

            if set_spam:
                probably_spam = True
                break

    return probably_spam, repeat_level


def is_profound(text):
    return profanity.contains_profanity(text)


def __get_text_similarity(text_a, text_b):
    sm = difflib.SequenceMatcher(None, text_a, text_b)

    return sm.ratio()


class SpellChecker:

    LANG = "en_US"

    def __init__(self):
        self.d = enchant.Dict(self.LANG)

    def is_word(self, text):
        return self.d.check(text)

    def get_suggestions(self, text):
        return self.d.suggest(text)