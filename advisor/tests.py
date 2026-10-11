"""The advisor must be private: only a signed-in superuser can reach any of it."""
import datetime
import json
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from advisor.models import Conversation

STATIC = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
BASE = '/networth/advisor/'

# (method, path) for every advisor endpoint; pages first
PAGES = [('get', BASE), ('get', BASE + 'capabilities/')]
APIS = [
    ('get', BASE + 'summary/'),
    ('post', BASE + 'chat/'),
    ('get', BASE + 'convs/'),
    ('post', BASE + 'convs/'),
    ('delete', BASE + 'convs/1/'),
    ('patch', BASE + 'convs/1/title/'),
    ('get', BASE + 'convs/1/messages/'),
    ('post', BASE + 'convs/1/messages/'),
    ('post', BASE + 'share/email/'),
    ('post', BASE + 'share/pdf/'),
]


def make_user(email, superuser=False):
    User = get_user_model()
    create = User.objects.create_superuser if superuser else User.objects.create_user
    return create(email=email, username=email.split('@')[0], date_of_birth=datetime.date(1980, 1, 1),
                  password='a-strong-test-password')


@override_settings(STORAGES=STATIC)
class AdvisorAccessTest(TestCase):

    def call(self, client, method, path):
        if method == 'get':
            return client.get(path)
        return getattr(client, method)(path, data='{}', content_type='application/json')

    def test_signed_out_pages_redirect_to_login(self):
        for method, path in PAGES:
            with self.subTest(path=path):
                response = self.call(self.client, method, path)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response['Location'].startswith('/accounts/login/?next='))

    def test_signed_out_apis_return_401(self):
        for method, path in APIS:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.call(self.client, method, path).status_code, 401)

    def test_non_owner_is_refused_everywhere(self):
        self.client.force_login(make_user('member@example.com'))
        for method, path in PAGES + APIS:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.call(self.client, method, path).status_code, 403)

    def test_old_public_endpoints_do_not_exist_on_main_site(self):
        for path in ['/tools/net-worth', '/chat', '/convs/', '/mcp/sse', '/advisor']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


@override_settings(STORAGES=STATIC)
class AdvisorOwnerTest(TestCase):

    def setUp(self):
        self.owner = make_user('owner@example.com', superuser=True)
        self.client.force_login(self.owner)

    def post_json(self, path, payload, method='post', client=None):
        client = client or self.client
        return getattr(client, method)(path, data=json.dumps(payload), content_type='application/json')

    def test_pages_render_with_private_urls(self):
        response = self.client.get(BASE)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'const ADVISOR = "/networth/advisor/"')
        self.assertIn('csrftoken', response.cookies)
        self.assertEqual(self.client.get(BASE + 'capabilities/').status_code, 200)

    @mock.patch('advisor.views.get_net_worth_summary', return_value={'net_worth_usd': 1})
    def test_summary(self, _):
        self.assertEqual(self.client.get(BASE + 'summary/').json(), {'net_worth_usd': 1})

    def test_conversation_lifecycle(self):
        conv = self.client.post(BASE + 'convs/').json()
        cid = conv['id']
        self.assertEqual(self.post_json(f'{BASE}convs/{cid}/title/', {'title': 'Plan'}, 'patch').status_code, 200)
        self.assertEqual(self.post_json(f'{BASE}convs/{cid}/messages/', {'role': 'user', 'content': 'Hi'}).status_code, 200)
        self.assertEqual(self.post_json(f'{BASE}convs/{cid}/messages/', {'role': 'system', 'content': 'x'}).status_code, 400)
        self.assertEqual(self.client.get(f'{BASE}convs/{cid}/messages/').json(), [{'role': 'user', 'content': 'Hi'}])
        self.assertEqual(self.client.get(BASE + 'convs/').json()[0]['title'], 'Plan')
        self.assertEqual(self.client.delete(f'{BASE}convs/{cid}/').status_code, 200)
        self.assertFalse(Conversation.objects.exists())

    def test_share_email_goes_to_signed_in_owner(self):
        from django.core import mail
        response = self.post_json(BASE + 'share/email/', {'content_html': '<p>Note</p>', 'title': 'T'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mail.outbox[0].to, ['owner@example.com'])

    @mock.patch('advisor.views.build_financial_context', return_value='')
    @mock.patch('anthropic.Anthropic')
    def test_chat_streams_an_answer(self, anthropic_cls, _):
        anthropic_cls.return_value.messages.create.return_value = SimpleNamespace(
            stop_reason='end_turn', content=[SimpleNamespace(type='text', text='Hello there')])
        response = self.post_json(BASE + 'chat/', {'question': 'Hi', 'history': []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        body = b''.join(response.streaming_content).decode()
        self.assertIn('data: "Hello there"', body)
        self.assertTrue(body.rstrip().endswith('data: [DONE]'))

    def test_chat_requires_a_question(self):
        self.assertEqual(self.post_json(BASE + 'chat/', {'question': '  '}).status_code, 400)

    def test_writes_need_the_csrf_token(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.owner)
        self.assertEqual(self.post_json(BASE + 'chat/', {'question': 'Hi'}, client=strict).status_code, 403)
        self.assertEqual(strict.post(BASE + 'convs/').status_code, 403)
