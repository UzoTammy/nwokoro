"""Fair Rota Scheduler: who writes and who reviews each day's content.

Ported from the CP Devotional role-scheduler prototype (OzoneFL/dailydevotional,
cp-scheduler-handoff/docs/scheduler). Pure Python, no database: a `Rota` holds the
team, the slots and an injectable clock, so a simulation (and the tests) can
advance one day at a time.

Rules
-----
A *slot* is one piece of content due on one date: (day, content type).

A writer is eligible for a slot only if they
  * have not already missed this slot,
  * are not unavailable that day,
  * have no other slot that day,
  * have fewer than `max_per_week` slots that ISO week,
  * have no slot the day before or after (no back-to-back days).
If nobody qualifies, the back-to-back rule is relaxed and the search repeats.

Among eligible writers the lowest load score wins:

    L = A / K + 0.5 * M

A = slots held in the 28-day planning window (reserve slots excluded),
K = capacity (slots per 28 days), M = missed deadlines.
Ties go to the writer whose latest slot is earliest, then to team order.

The reviewer is the one with the fewest unpublished reviews, never the writer.

When a draft deadline passes without a draft, the writer's M goes up and
  * with 3 or more days left, the slot is reassigned with 24 hours to draft,
  * otherwise a reserve piece is used, or, if the reserve is empty, the slot
    is marked missed.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

WINDOW = 28
HISTORY = 14          # past days kept for display
DRAFT_LEAD = 5        # draft due 5 days before publishing
REVIEW_LEAD = 2       # review due 2 days before publishing
MAX_PER_WEEK = 3
REASSIGN_MIN_DAYS = 3

# content type -> weekday it runs on (None = every day); Monday is 0
CADENCE = {'devotion': None, 'music': 2, 'story': 5}
TYPE_LABEL = {'devotion': 'Devotion', 'music': 'Music', 'story': 'Real story'}


@dataclass
class Person:
    id: str
    name: str
    capacity: int = 8                     # slots per 28 days
    unavailable: set = field(default_factory=set)
    missed: int = 0


@dataclass
class Slot:
    day: date
    type: str
    writer: str = None
    reviewer: str = None
    status: str = 'open'      # open, assigned, approved, published, missed
    draft_due: date = None
    review_due: date = None
    missed_by: list = field(default_factory=list)
    source: str = None        # 'reserve' when filled from the reserve bank
    will_miss: bool = False   # simulation flag: this writer won't deliver
    explanation: dict = None

    @property
    def key(self):
        return f'{self.day.isoformat()}:{self.type}'


class Rota:
    def __init__(self, writers, reviewers, today, reserve=5, owner='Owner',
                 window=WINDOW, max_per_week=MAX_PER_WEEK):
        self.writers = {p.id: p for p in writers}
        self.reviewers = {p.id: p for p in reviewers}
        self.order = [p.id for p in writers]          # stable tie-break order
        self.today = today
        self.reserve = reserve
        self.owner = owner
        self.window = window
        self.max_per_week = max_per_week
        self.slots = []
        self.log = []

    # ----------------------------------------------------------- generation

    def generate(self):
        """Create and assign every slot in the planning window, oldest first."""
        for offset in range(self.window):
            self._make_slots_for(self.today + timedelta(days=offset))
        return self

    def _make_slots_for(self, day):
        for ctype, weekday in CADENCE.items():
            if weekday is not None and day.weekday() != weekday:
                continue
            slot = Slot(day=day, type=ctype,
                        draft_due=day - timedelta(days=DRAFT_LEAD),
                        review_due=day - timedelta(days=REVIEW_LEAD))
            self.slots.append(slot)
            decision = self.pick_writer(slot)
            slot.explanation = decision
            if decision['winner']:
                slot.writer, slot.status = decision['winner'], 'assigned'
                if slot.draft_due < self.today:
                    slot.status = 'approved'   # too close to start from scratch: treat as already in hand
            slot.reviewer = self.pick_reviewer(slot)

    # ------------------------------------------------------------- the rules

    def eligibility(self, pid, slot, strict=True):
        """(eligible, reason) for one writer and one slot."""
        person = self.writers[pid]
        if pid in slot.missed_by:
            return False, 'already missed this slot'
        if slot.day in person.unavailable:
            return False, 'unavailable that day'
        mine = [s for s in self.slots if s is not slot and s.writer == pid]
        if any(s.day == slot.day for s in mine):
            return False, 'already writing that day'
        week = slot.day.isocalendar()[:2]
        if sum(1 for s in mine if s.day.isocalendar()[:2] == week) >= self.max_per_week:
            return False, f'already has {self.max_per_week} slots that week'
        if strict and any(abs((s.day - slot.day).days) == 1 for s in mine):
            return False, 'back-to-back with another slot'
        return True, None

    def held(self, pid):
        """A: non-reserve slots in the planning window."""
        end = self.today + timedelta(days=self.window)
        return sum(1 for s in self.slots
                   if s.writer == pid and s.source != 'reserve' and self.today <= s.day < end)

    def load(self, pid):
        """L = A / K + 0.5 * M"""
        person = self.writers[pid]
        return self.held(pid) / person.capacity + 0.5 * person.missed

    def last_day(self, pid):
        days = [s.day for s in self.slots if s.writer == pid]
        return max(days) if days else date.min

    def pick_writer(self, slot):
        """Strict pass, then relaxed; lowest load wins; explain everything."""
        for strict in (True, False):
            candidates, excluded = [], []
            for pid in self.order:
                ok, reason = self.eligibility(pid, slot, strict)
                if ok:
                    candidates.append({'id': pid, 'load': round(self.load(pid), 4),
                                       'held': self.held(pid), 'capacity': self.writers[pid].capacity,
                                       'missed': self.writers[pid].missed, 'last': self.last_day(pid)})
                else:
                    excluded.append({'id': pid, 'reason': reason})
            if candidates:
                candidates.sort(key=lambda c: (c['load'], c['last'], self.order.index(c['id'])))
                tie = len(candidates) > 1 and candidates[0]['load'] == candidates[1]['load']
                for c in candidates:
                    c['last'] = None if c['last'] == date.min else c['last'].isoformat()
                return {'winner': candidates[0]['id'], 'relaxed': not strict, 'tie_break': tie,
                        'candidates': candidates, 'excluded': excluded}
        return {'winner': None, 'relaxed': True, 'tie_break': False, 'candidates': [], 'excluded': excluded}

    def pick_reviewer(self, slot):
        """Fewest unpublished reviews; never the slot's writer; team order breaks ties."""
        options = [rid for rid in self.reviewers if rid != slot.writer]
        if not options:
            return self.owner

        def open_reviews(rid):
            return sum(1 for s in self.slots if s.reviewer == rid and s.status != 'published')
        return min(options, key=lambda rid: (open_reviews(rid), list(self.reviewers).index(rid)))

    # ------------------------------------------------------------ simulation

    def mark_will_miss(self, key):
        slot = self.find(key)
        if slot and slot.status == 'assigned':
            slot.will_miss = True
            self._log('info', f'{self.name(slot.writer)} will miss the {self.label(slot)} draft (simulated).')

    def advance(self):
        """Move the clock one day: publish, sweep deadlines, roll the window."""
        self.today += timedelta(days=1)

        for slot in self.slots:                                  # 1. publish
            if slot.day <= self.today and slot.status == 'approved':
                slot.status = 'published'
                note = ' from the reserve' if slot.source == 'reserve' else ''
                self._log('ok', f'Published {self.label(slot)}{note}.')

        for slot in sorted(self.slots, key=lambda s: s.day):     # 2. deadline sweep
            if slot.status != 'assigned' or self.today <= slot.draft_due:
                continue
            if slot.will_miss:
                writer = self.writers[slot.writer]
                writer.missed += 1
                slot.missed_by.append(writer.id)
                self._reassign(slot, f'{writer.name} missed the draft deadline')
            else:
                slot.status = 'approved'   # simulation: drafted on time and reviewed

        horizon_day = self.today + timedelta(days=self.window - 1)   # 3. roll the window
        self.slots = [s for s in self.slots if s.day >= self.today - timedelta(days=HISTORY)]
        self._make_slots_for(horizon_day)
        return self

    def _reassign(self, slot, reason):
        left = (slot.day - self.today).days
        if left >= REASSIGN_MIN_DAYS:
            slot.writer = None
            decision = self.pick_writer(slot)
            if decision['winner']:
                slot.explanation = decision
                slot.writer, slot.will_miss, slot.status = decision['winner'], False, 'assigned'
                slot.draft_due = self.today + timedelta(days=1)
                slot.review_due = min(slot.day - timedelta(days=1),
                                      max(slot.draft_due + timedelta(days=1),
                                          slot.day - timedelta(days=REVIEW_LEAD)))
                slot.reviewer = self.pick_reviewer(slot)
                self._log('warn', f'{self.label(slot)}: {reason}. Reassigned to '
                                  f'{self.name(slot.writer)} with 24 hours to draft.')
                return
        self._use_reserve_or_miss(slot, reason)

    def _use_reserve_or_miss(self, slot, reason):
        slot.writer, slot.will_miss = None, False
        if self.reserve > 0:
            self.reserve -= 1
            slot.source, slot.status = 'reserve', 'approved'
            self._log('warn', f'{self.label(slot)}: {reason}. Too late to reassign, so a reserve '
                              f'piece was used ({self.reserve} left).')
        else:
            slot.status = 'missed'
            self._log('warn', f'{self.label(slot)}: {reason}. The reserve is empty; '
                              f'the reviewer must write it.')

    # --------------------------------------------------------------- helpers

    def find(self, key):
        return next((s for s in self.slots if s.key == key), None)

    def name(self, pid):
        person = self.writers.get(pid) or self.reviewers.get(pid)
        return person.name if person else (self.owner if pid == self.owner else 'Reserve')

    def label(self, slot):
        return f"{TYPE_LABEL[slot.type]} on {slot.day.strftime('%a %d %b')}"

    def _log(self, kind, text):
        self.log.append({'day': self.today.isoformat(), 'kind': kind, 'text': text})

    def to_dict(self):
        return {
            'today': self.today.isoformat(),
            'reserve': self.reserve,
            'people': [{'id': p.id, 'name': p.name, 'capacity': p.capacity, 'missed': p.missed,
                        'held': self.held(p.id), 'load': round(self.load(p.id), 2)}
                       for p in self.writers.values()],
            'reviewers': [{'id': p.id, 'name': p.name} for p in self.reviewers.values()],
            'slots': [{'key': s.key, 'day': s.day.isoformat(), 'type': s.type, 'writer': s.writer,
                       'reviewer': s.reviewer, 'status': s.status, 'source': s.source,
                       'draft_due': s.draft_due.isoformat(), 'review_due': s.review_due.isoformat(),
                       'missed_by': s.missed_by, 'will_miss': s.will_miss, 'explanation': s.explanation}
                      for s in sorted(self.slots, key=lambda s: (s.day, list(CADENCE).index(s.type)))],
            'log': list(reversed(self.log)),
        }


def replay(writers, reviewers, start, actions, reserve=5):
    """Rebuild a rota from its inputs and the visitor's actions, deterministically."""
    rota = Rota(writers, reviewers, start, reserve=reserve).generate()
    rota._log('info', 'Rota generated: each slot went to the eligible writer with the lowest load score.')
    for action in actions:
        if action.get('type') == 'advance':
            rota.advance()
        elif action.get('type') == 'miss':
            rota.mark_will_miss(str(action.get('slot', '')))
    return rota
