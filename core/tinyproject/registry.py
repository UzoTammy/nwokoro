"""Catalogue of tiny projects shown on the /tinyproject/ hub.

To add a project, append a dict to PROJECTS. Only `slug`, `title`, `summary`,
`category` and `status` are required:

    status    'live'      -> shown on the hub; card links to `url_name` (a Django URL name)
              'workshop'  -> hidden from the public hub until reviewed and approved;
                             approve a project by changing its status to 'live'
    date      'YYYY-MM'   -> display, and sorting (live first, then newest first)
    icon      a Font Awesome 5 class, e.g. 'fas fa-calculator'
    docs      optional external documentation link
"""
from datetime import datetime

from django.urls import NoReverseMatch, reverse

PROJECTS = [
    {
        'slug': 'fair-rota',
        'title': 'Fair Rota Scheduler',
        'summary': 'Assigns a writer and reviewer to every publishing day fairly, explains each decision, and simulates missed deadlines.',
        'category': 'Scheduling',
        'tags': ['Python', 'Algorithms', 'Fairness'],
        'date': '2026-10',
        'status': 'workshop',      # awaiting review before going public
        'url_name': 'rota',
        'docs': '/portfolio/miniproject/rota/#documentation',
        'icon': 'fas fa-calendar-check',
    },
    {
        'slug': 'number-to-words',
        'title': 'Number to Words',
        'summary': 'Turns any whole number up to 999 trillion into words, using a recursive split by scale.',
        'category': 'Algorithms',
        'tags': ['Python', 'Recursion'],
        'date': '2024-01',
        'status': 'live',
        'url_name': 'number-to-word',
        'docs': '/portfolio/miniproject/number-to-word/#documentation',
        'icon': 'fas fa-spell-check',
    },
    {
        'slug': 'canada-tax',
        'title': 'Canada Income Tax Estimator',
        'summary': 'Federal and Nova Scotia income tax across a range of incomes, with average rates and take-home pay.',
        'category': 'Finance',
        'tags': ['Python', 'Tax brackets', 'Nova Scotia'],
        'date': '2024-08',
        'status': 'workshop',
        'icon': 'fas fa-calculator',
    },
    {
        'slug': 'profile-capture',
        'title': 'Profile Capture',
        'summary': 'A friendly multi-step form that validates input, previews it, then saves it to the server.',
        'category': 'Web forms',
        'tags': ['Django', 'Forms API'],
        'date': '2024-07',
        'status': 'workshop',
        'icon': 'fas fa-id-card',
    },
    {
        'slug': 'auto-email',
        'title': 'Automated Email Sender',
        'summary': 'Scheduling routine emails with Python and cron, so the regular jobs run themselves.',
        'category': 'Automation',
        'tags': ['Python', 'cron', 'SMTP'],
        'date': '2024-05',
        'status': 'workshop',
        'icon': 'fas fa-paper-plane',
    },
    {
        'slug': 'learn-sql',
        'title': 'Learn SQL with PostgreSQL',
        'summary': 'A fast, practical path to SQL fluency, built around real queries on PostgreSQL.',
        'category': 'Learning',
        'tags': ['SQL', 'PostgreSQL'],
        'date': '2024-01',
        'status': 'workshop',
        'icon': 'fas fa-database',
    },
]


def get_projects(include_workshop=False):
    """Projects to show, live first then newest first, with resolved `url` and display date.

    Workshop projects are excluded unless `include_workshop` is True.
    """
    items = []
    for project in PROJECTS:
        item = {'tags': [], 'icon': 'fas fa-cube', **project}
        item['url'] = None
        if item['status'] == 'live' and item.get('url_name'):
            try:
                item['url'] = reverse(item['url_name'])
            except NoReverseMatch:
                item['status'] = 'workshop'
        stamp = datetime.strptime(item.get('date', '1970-01'), '%Y-%m')
        item['date_display'] = stamp.strftime('%b %Y')
        items.append(item)
    if not include_workshop:
        items = [p for p in items if p['status'] == 'live']
    # live projects first, then newest first within each group
    items.sort(key=lambda p: p.get('date', ''), reverse=True)
    return sorted(items, key=lambda p: p['status'] != 'live')
