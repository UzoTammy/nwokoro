import random
import re

from django.test import SimpleTestCase, override_settings

from .tinyproject.numtoword import LIMIT, convert, normalise

# --- an independent words -> number parser, used to check convert() by round trip ---
_SMALL = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
    'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
    'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60,
    'seventy': 70, 'eighty': 80, 'ninety': 90,
}
_SCALE = {'thousand': 10 ** 3, 'million': 10 ** 6, 'billion': 10 ** 9, 'trillion': 10 ** 12}


def words_to_number(text):
    total = group = 0
    for token in re.split(r'[\s,-]+', text.lower()):
        if token == 'and' or not token:
            continue
        if token in _SMALL:
            group += _SMALL[token]
        elif token == 'hundred':
            group *= 100
        elif token in _SCALE:
            total += group * _SCALE[token]
            group = 0
        else:
            raise ValueError(f'unknown word {token!r}')
    return total + group


class NumberToWordsExamplesTest(SimpleTestCase):
    """The documented British style, pinned by exact examples."""

    EXAMPLES = {
        0: 'Zero',
        7: 'Seven',
        14: 'Fourteen',
        20: 'Twenty',
        21: 'Twenty-One',
        99: 'Ninety-Nine',
        100: 'One Hundred',
        101: 'One Hundred and One',
        110: 'One Hundred and Ten',
        999: 'Nine Hundred and Ninety-Nine',
        1000: 'One Thousand',
        1001: 'One Thousand and One',
        1010: 'One Thousand and Ten',
        1100: 'One Thousand, One Hundred',
        1101: 'One Thousand, One Hundred and One',
        123456: 'One Hundred and Twenty-Three Thousand, Four Hundred and Fifty-Six',
        1000000: 'One Million',
        1000099: 'One Million and Ninety-Nine',
        1000100: 'One Million, One Hundred',
        1001001: 'One Million, One Thousand and One',
        2000050000: 'Two Billion, Fifty Thousand',
        12000000050: 'Twelve Billion and Fifty',
        LIMIT - 1: (
            'Nine Hundred and Ninety-Nine Trillion, Nine Hundred and Ninety-Nine Billion, '
            'Nine Hundred and Ninety-Nine Million, Nine Hundred and Ninety-Nine Thousand, '
            'Nine Hundred and Ninety-Nine'
        ),
    }

    def test_examples(self):
        for number, words in self.EXAMPLES.items():
            with self.subTest(number=number):
                self.assertEqual(convert(number), words)
                self.assertEqual(convert(f'{number:,}'), words)  # string input with commas


class NumberToWordsRoundTripTest(SimpleTestCase):
    """Every output must parse back to the original number, with tidy formatting."""

    def check(self, number):
        words = convert(number)
        self.assertEqual(words_to_number(words), number, words)
        self.assertNotIn('  ', words)
        self.assertFalse(words.endswith((',', ' ', '-')), words)
        if number:
            self.assertNotIn('Zero', words)

    def test_exhaustive_to_one_million(self):
        for number in range(1_000_001):
            self.check(number)

    def test_random_up_to_limit(self):
        rng = random.Random(2026)
        for digits in range(7, 16):
            for _ in range(2000):
                self.check(rng.randrange(10 ** (digits - 1), 10 ** digits))


class NumberToWordsInputTest(SimpleTestCase):

    def test_accepted_strings(self):
        self.assertEqual(convert('007'), 'Seven')
        self.assertEqual(convert('000'), 'Zero')
        self.assertEqual(convert(' 1 000 '), 'One Thousand')
        self.assertEqual(normalise('0' * 40 + '42'), 42)

    def test_rejected_values(self):
        for bad in ['', ' ', '-5', '+5', '12.5', '1e3', 'abc', '1_000', '²', '٣', '１２', None, 1.5, True, -1]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    convert(bad)

    def test_limit(self):
        self.assertTrue(convert(LIMIT - 1))
        for big in [LIMIT, '1,000,000,000,000,000', '9' * 5000]:
            with self.subTest(big=str(big)[:20]):
                with self.assertRaises(OverflowError):
                    convert(big)


# tests run with DEBUG=False, where the manifest storage needs `collectstatic` output
@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class NumberToWordsViewTest(SimpleTestCase):
    url = '/portfolio/miniproject/number-to-word/'

    def test_empty_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'will appear here')

    def test_conversion(self):
        response = self.client.get(self.url, {'enter_number': '1,001'})
        self.assertContains(response, 'One Thousand and One')

    def test_bad_input_never_errors(self):
        for bad in ['abc', '²', '-5', '9' * 5000, '<script>alert(1)</script>']:
            with self.subTest(bad=bad[:20]):
                response = self.client.get(self.url, {'enter_number': bad})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'tool-error')
                self.assertNotContains(response, '<script>alert(1)</script>')


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class CaseStudyPagesTest(SimpleTestCase):

    def test_case_studies_render(self):
        for url, text in [
            ('/portfolio-scush/', 'distribution business'),
            ('/portfolio/ai-advisor/', 'Ask your money'),
            ('/portfolio/cp-devotional/', 'reviewed by people'),
        ]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), text)

    def test_home_links_to_cp_devotional_page_not_artifact(self):
        response = self.client.get('/')
        self.assertContains(response, 'href="/portfolio/cp-devotional/"')
        self.assertNotContains(response, 'claude.ai/code/artifact')
