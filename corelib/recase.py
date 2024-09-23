import re


class ReCase:
    _upper_alpha_regex = re.compile(r'[A-Z]')
    symbol_set = {' ', '.', '/', '_', '\\', '-'}

    def __init__(self, text):
        self.original_text = text
        self._words = self._tokenize(text)

    def _tokenize(self, text):
        buffer = []
        words = []
        is_all_caps = text.upper() == text

        for i, char in enumerate(text):
            next_char = text[i + 1] if i + 1 < len(text) else None

            if char in self.symbol_set:
                continue

            buffer.append(char)

            is_end_of_word = (
                next_char is None
                or (self._upper_alpha_regex.match(next_char) and not is_all_caps)
                or next_char in self.symbol_set
            )

            if is_end_of_word:
                words.append(''.join(buffer))
                buffer.clear()

        return words

    @property
    def camel_case(self):
        return self._get_camel_case()

    @property
    def constant_case(self):
        return self._get_constant_case()

    @property
    def sentence_case(self):
        return self._get_sentence_case()

    @property
    def snake_case(self):
        return self._get_snake_case()

    @property
    def dot_case(self):
        return self._get_snake_case(separator='.')

    @property
    def param_case(self):
        return self._get_snake_case(separator='-')

    @property
    def path_case(self):
        return self._get_snake_case(separator='/')

    @property
    def pascal_case(self):
        return self._get_pascal_case()

    @property
    def header_case(self):
        return self._get_pascal_case(separator='-')

    @property
    def title_case(self):
        return self._get_pascal_case(separator=' ')

    def _get_camel_case(self, separator=''):
        words = [self._upper_case_first_letter(word) for word in self._words]
        if self._words:
            words[0] = words[0].lower()

        return separator.join(words)

    def _get_constant_case(self, separator='_'):
        words = [word.upper() for word in self._words]

        return separator.join(words)

    def _get_pascal_case(self, separator=''):
        words = [self._upper_case_first_letter(word) for word in self._words]

        return separator.join(words)

    def _get_sentence_case(self, separator=' '):
        words = [word.lower() for word in self._words]
        if self._words:
            words[0] = self._upper_case_first_letter(words[0])

        return separator.join(words)

    def _get_snake_case(self, separator='_'):
        words = [word.lower() for word in self._words]

        return separator.join(words)

    def _upper_case_first_letter(self, word):  # noqa
        return word[0].upper() + word[1:].lower()
