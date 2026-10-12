import json
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



# ------------------------------------------------------------------ Fair Rota Scheduler
import datetime as _dt
from collections import Counter

from .tinyproject.rota import Person, Rota, Slot, replay

MONDAY = _dt.date(2026, 10, 12)


def _rota(writers, reviewers=None, today=MONDAY, **kw):
    reviewers = reviewers or [Person('grace', 'Grace'), Person('femi', 'Femi')]
    return Rota(writers, reviewers, today, **kw)


def _held(rota, pid, *days):
    for d in days:
        rota.slots.append(Slot(day=MONDAY + _dt.timedelta(days=d), type='devotion', writer=pid, status='assigned'))


class RotaRulesTest(SimpleTestCase):

    def test_lowest_load_wins_design_example(self):
        rota = _rota([Person('ada', 'Ada', capacity=8), Person('ben', 'Ben', capacity=4)])
        _held(rota, 'ada', 0, 7, 14, 21)            # 4 of 8   -> 0.50
        _held(rota, 'ben', 2, 9, 16)                # 3 of 4   -> 0.75
        self.assertEqual(rota.load('ada'), 0.5)
        self.assertEqual(rota.load('ben'), 0.75)
        slot = Slot(day=MONDAY + _dt.timedelta(days=4), type='devotion')
        self.assertEqual(rota.pick_writer(slot)['winner'], 'ada')

    def test_missed_deadlines_raise_load(self):
        rota = _rota([Person('ada', 'Ada', capacity=8, missed=1)])
        self.assertEqual(rota.load('ada'), 0.5)

    def test_tie_goes_to_earliest_latest_slot(self):
        rota = _rota([Person('ada', 'Ada', 8), Person('ben', 'Ben', 8)])
        _held(rota, 'ada', 10)
        _held(rota, 'ben', 3)                       # same load; Ben's latest slot is earlier
        decision = rota.pick_writer(Slot(day=MONDAY + _dt.timedelta(days=20), type='devotion'))
        self.assertEqual(decision['winner'], 'ben')
        self.assertTrue(decision['tie_break'])

    def test_back_to_back_blocks_then_relaxed_pass_assigns(self):
        rota = _rota([Person('ada', 'Ada', 8)])
        _held(rota, 'ada', 4)
        decision = rota.pick_writer(Slot(day=MONDAY + _dt.timedelta(days=5), type='devotion'))
        self.assertEqual(decision['winner'], 'ada')
        self.assertTrue(decision['relaxed'])

    def test_max_per_week(self):
        rota = _rota([Person('ada', 'Ada', 28)])
        _held(rota, 'ada', 0, 2, 4)                 # Mon, Wed, Fri
        ok, reason = rota.eligibility('ada', Slot(day=MONDAY + _dt.timedelta(days=6), type='devotion'), strict=False)
        self.assertFalse(ok)
        self.assertIn('3 slots that week', reason)

    def test_unavailable_and_same_day(self):
        rota = _rota([Person('ada', 'Ada', 8, unavailable={MONDAY})])
        self.assertEqual(rota.eligibility('ada', Slot(day=MONDAY, type='devotion'))[1], 'unavailable that day')
        rota = _rota([Person('ada', 'Ada', 8)])
        _held(rota, 'ada', 2)
        self.assertEqual(rota.eligibility('ada', Slot(day=MONDAY + _dt.timedelta(days=2), type='music'))[1],
                         'already writing that day')

    def test_reviewer_is_never_the_writer(self):
        rota = _rota([Person('ada', 'Ada', 8)], reviewers=[Person('ada', 'Ada'), Person('femi', 'Femi')])
        self.assertEqual(rota.pick_reviewer(Slot(day=MONDAY, type='devotion', writer='ada')), 'femi')


class RotaGenerationTest(SimpleTestCase):

    def team(self):
        return [Person('ada', 'Ada', 12), Person('ben', 'Ben', 6), Person('chi', 'Chi', 10), Person('dayo', 'Dayo', 10)]

    def test_month_invariants(self):
        rota = _rota(self.team()).generate()
        self.assertEqual(Counter(s.type for s in rota.slots), {'devotion': 28, 'music': 4, 'story': 4})
        self.assertTrue(all(s.writer for s in rota.slots))
        pairs = Counter((s.writer, s.day) for s in rota.slots)
        self.assertEqual(max(pairs.values()), 1)                     # never two slots a day
        weeks = Counter((s.writer, s.day.isocalendar()[:2]) for s in rota.slots)
        self.assertLessEqual(max(weeks.values()), 3)                 # weekly limit
        self.assertTrue(all(s.reviewer != s.writer for s in rota.slots))

    def test_deterministic(self):
        a = _rota(self.team()).generate().to_dict()
        b = _rota(self.team()).generate().to_dict()
        self.assertEqual(a['slots'], b['slots'])


class RotaSweepTest(SimpleTestCase):

    def team(self):
        return [Person('ada', 'Ada', 12), Person('ben', 'Ben', 6), Person('chi', 'Chi', 10), Person('dayo', 'Dayo', 10)]

    def slot_on(self, rota, day_offset):
        return next(s for s in rota.slots if s.type == 'devotion' and s.day == MONDAY + _dt.timedelta(days=day_offset))

    def test_miss_with_time_left_reassigns(self):
        rota = _rota(self.team()).generate()
        slot = self.slot_on(rota, 12)              # draft due day 7
        first = slot.writer
        rota.mark_will_miss(slot.key)
        for _ in range(8):
            rota.advance()                          # today = day 8, 4 days left
        self.assertNotEqual(slot.writer, first)
        self.assertIn(first, slot.missed_by)
        self.assertEqual(rota.writers[first].missed, 1)
        self.assertEqual(slot.draft_due, rota.today + _dt.timedelta(days=1))

    def test_late_miss_uses_reserve_then_marks_missed(self):
        rota = _rota(self.team(), reserve=1).generate()
        for offset in (9, 10):
            slot = self.slot_on(rota, offset)
            rota.mark_will_miss(slot.key)
            slot.draft_due = MONDAY + _dt.timedelta(days=offset - 2)   # deadline 2 days before publishing
        for _ in range(9):
            rota.advance()                          # both noticed with < 3 days left
        self.assertEqual(self.slot_on(rota, 9).source, 'reserve')
        self.assertEqual(self.slot_on(rota, 10).status, 'missed')
        self.assertEqual(rota.reserve, 0)

    def test_replay_is_repeatable(self):
        key = self.slot_on(_rota(self.team()).generate(), 12).key
        actions = [{'type': 'miss', 'slot': key}] + [{'type': 'advance'}] * 8
        a = replay(self.team(), [Person('grace', 'Grace')], MONDAY, actions).to_dict()
        b = replay(self.team(), [Person('grace', 'Grace')], MONDAY, actions).to_dict()
        self.assertEqual(a['slots'], b['slots'])
        self.assertEqual(a['log'], b['log'])


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class RotaPageTest(SimpleTestCase):
    api = '/portfolio/miniproject/rota/api/'

    def payload(self, **over):
        body = {
            'start': _dt.date.today().isoformat(), 'reserve': 5,
            'writers': [{'id': 'ada', 'name': 'Ada', 'capacity': 12, 'unavailable': []},
                        {'id': 'ben', 'name': 'Ben', 'capacity': 6, 'unavailable': []}],
            'reviewers': [{'id': 'grace', 'name': 'Grace'}],
            'actions': [],
        }
        body.update(over)
        return json.dumps(body)

    def test_page_renders(self):
        response = self.client.get('/portfolio/miniproject/rota/')
        self.assertContains(response, 'Fair Rota')
        self.assertContains(response, 'def pick_writer')            # live source panel

    def test_api_returns_a_rota(self):
        response = self.client.post(self.api, self.payload(), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len([s for s in response.json()['slots'] if s['type'] == 'devotion']), 28)

    def test_api_rejects_bad_input(self):
        bad = [
            self.payload(start='not-a-date'), self.payload(start='2000-01-01'),
            self.payload(writers=[]), self.payload(writers=[{'id': 'A B', 'name': 'x', 'capacity': 3}]),
            self.payload(writers=[{'id': 'ada', 'name': 'Ada', 'capacity': 0}]),
            self.payload(reserve=99), self.payload(actions=[{'type': 'advance'}] * 61),
            '[1, 2]', '{bad json',
        ]
        for body in bad:
            with self.subTest(body=body[:60]):
                self.assertEqual(self.client.post(self.api, body, content_type='application/json').status_code, 400)
