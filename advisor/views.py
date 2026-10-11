"""The AI Advisor, served by the main Django site and visible only to the owner.

Replaces the separate FastAPI service that used to run at ai.uzonwokoro.com.
Every view requires a signed-in superuser: pages redirect to the login page,
JSON/streaming endpoints answer 401 (signed out) or 403 (not the owner).
"""
import json
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from advisor.context import SYSTEM_PROMPT, build_financial_context
from advisor.html_export import wrap_html_for_export
from advisor.models import Conversation, Message
from advisor.tools import (
    EXTRACT_TOOL, MATURING_INVESTMENTS_TOOL, NETWORTH_HISTORY_TOOL,
    RECENT_TRANSACTIONS_TOOL, SEARCH_TOOL,
    get_maturing_investments, get_net_worth_summary, get_networth_history,
    get_recent_transactions, tavily_extract, tavily_search,
)

_MODEL = 'claude-sonnet-4-6'
_MAX_TOKENS = 2048
_TOOLS = [NETWORTH_HISTORY_TOOL, RECENT_TRANSACTIONS_TOOL, MATURING_INVESTMENTS_TOOL, SEARCH_TOOL, EXTRACT_TOOL]
_MAX_QUESTION = 4000      # characters
_MAX_HISTORY = 40         # messages sent back to the model


# --------------------------------------------------------------------------- access

def owner_required(api=False):
    """Allow only a signed-in superuser. Pages redirect to login; APIs get 401/403 JSON."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                if api:
                    return JsonResponse({'detail': 'Sign in required.'}, status=401)
                return redirect_to_login(request.get_full_path())
            if not user.is_superuser:
                return JsonResponse({'detail': 'Not allowed.'}, status=403) if api \
                    else HttpResponse('Not allowed.', status=403)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def _json_body(request):
    try:
        return json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------- pages

@require_GET
@owner_required()
@ensure_csrf_cookie
def advisor_home(request):
    return render(request, 'advisor/index.html')


@require_GET
@owner_required()
def capabilities(request):
    return render(request, 'advisor/capabilities.html')


@require_GET
@owner_required(api=True)
def summary(request):
    """Net-worth totals for the sidebar chart."""
    return JsonResponse(get_net_worth_summary())


# --------------------------------------------------------------------------- chat

def _sse(text):
    return f'data: {json.dumps(text)}\n\n'


def _run_tool(block):
    """Execute one tool call; return (progress note, tool result content)."""
    args = block.input or {}
    if block.name == 'get_networth_history':
        return '📊 *Loading net worth history…*', json.dumps(get_networth_history(args.get('months', 6)))
    if block.name == 'get_recent_transactions':
        return '📋 *Loading recent transactions…*', json.dumps(get_recent_transactions(args.get('days', 30)))
    if block.name == 'get_maturing_investments':
        return '⏳ *Checking maturing investments…*', json.dumps(get_maturing_investments(args.get('days', 60)))
    if block.name == 'web_search':
        query = args.get('query', '')
        return f'🔍 *Searching: {query}…*', tavily_search(query)
    if block.name == 'read_url':
        url = args.get('url', '')
        return f'📄 *Reading: {url}…*', tavily_extract(url)
    return None, f'Unknown tool {block.name!r}.'


@require_POST
@owner_required(api=True)
def chat(request):
    """Stream an answer as server-sent events, calling tools when the model asks for them."""
    body = _json_body(request)
    if not body or not str(body.get('question', '')).strip():
        return JsonResponse({'detail': 'A question is required.'}, status=400)
    question = str(body['question'])[:_MAX_QUESTION]
    history = [
        {'role': m['role'], 'content': str(m['content'])}
        for m in (body.get('history') or [])[-_MAX_HISTORY:]
        if isinstance(m, dict) and m.get('role') in ('user', 'assistant') and m.get('content')
    ]

    from anthropic import Anthropic
    client = Anthropic()
    system = f'{SYSTEM_PROMPT}\n\n{build_financial_context()}'
    messages = history + [{'role': 'user', 'content': question}]

    def generate():
        # first bytes immediately, so the platform router doesn't time out while tools run
        yield ': connected\n\n'
        current = list(messages)
        tools_used = False
        response = client.messages.create(
            model=_MODEL, max_tokens=_MAX_TOKENS, system=system, messages=current, tools=_TOOLS,
        )
        while response.stop_reason == 'tool_use':
            tools_used = True
            results = []
            for block in response.content:
                if block.type != 'tool_use':
                    continue
                note, content = _run_tool(block)
                if note:
                    yield _sse(f'\n{note}\n\n')
                results.append({'type': 'tool_result', 'tool_use_id': block.id, 'content': content})
            current = current + [
                {'role': 'assistant', 'content': response.content},
                {'role': 'user', 'content': results},
            ]
            response = client.messages.create(
                model=_MODEL, max_tokens=_MAX_TOKENS, system=system, messages=current, tools=_TOOLS,
            )

        if tools_used:
            with client.messages.stream(
                model=_MODEL, max_tokens=_MAX_TOKENS, system=system, messages=current,
            ) as stream:
                for text in stream.text_stream:
                    yield _sse(text)
        else:
            for block in response.content:
                text = getattr(block, 'text', '') or ''
                for i in range(0, len(text), 80):
                    yield _sse(text[i:i + 80])
        yield 'data: [DONE]\n\n'

    resp = StreamingHttpResponse(generate(), content_type='text/event-stream')
    resp['Cache-Control'] = 'no-cache'
    resp['X-Accel-Buffering'] = 'no'
    return resp


# --------------------------------------------------------------------------- conversations

@require_http_methods(['GET', 'POST'])
@owner_required(api=True)
def conversations(request):
    if request.method == 'POST':
        conv = Conversation.objects.create()
        return JsonResponse({'id': conv.id, 'title': conv.title})
    return JsonResponse([
        {'id': c.id, 'title': c.title, 'updated_at': c.updated_at.isoformat()}
        for c in Conversation.objects.all()
    ], safe=False)


@require_http_methods(['DELETE'])
@owner_required(api=True)
def conversation_delete(request, conv_id):
    deleted, _ = Conversation.objects.filter(pk=conv_id).delete()
    if not deleted:
        return JsonResponse({'detail': 'Conversation not found'}, status=404)
    return JsonResponse({'status': 'deleted'})


@require_http_methods(['PATCH'])
@owner_required(api=True)
def conversation_title(request, conv_id):
    body = _json_body(request) or {}
    title = str(body.get('title', '')).strip()[:120]
    if not title:
        return JsonResponse({'detail': 'A title is required.'}, status=400)
    if not Conversation.objects.filter(pk=conv_id).update(title=title):
        return JsonResponse({'detail': 'Conversation not found'}, status=404)
    return JsonResponse({'status': 'ok'})


@require_http_methods(['GET', 'POST'])
@owner_required(api=True)
def conversation_messages(request, conv_id):
    try:
        conv = Conversation.objects.get(pk=conv_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'detail': 'Conversation not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse([{'role': m.role, 'content': m.content} for m in conv.messages.all()], safe=False)

    body = _json_body(request) or {}
    role, content = body.get('role'), str(body.get('content', ''))
    if role not in ('user', 'assistant') or not content:
        return JsonResponse({'detail': 'role (user|assistant) and content are required.'}, status=400)
    Message.objects.create(conversation=conv, role=role, content=content)
    conv.updated_at = timezone.now()
    conv.save(update_fields=['updated_at'])
    return JsonResponse({'status': 'ok'})


# --------------------------------------------------------------------------- share (owner only)

def _share_payload(request):
    body = _json_body(request) or {}
    html = str(body.get('content_html', ''))
    title = str(body.get('title') or 'Financial Advisor Note')[:120]
    return html, title


@require_POST
@owner_required(api=True)
def share_email(request):
    """Email an advisor answer to the signed-in owner."""
    html, title = _share_payload(request)
    msg = EmailMessage(
        subject=f'Advisor Note — {title}',
        body=wrap_html_for_export(html, title),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[request.user.email],
    )
    msg.content_subtype = 'html'
    msg.send()
    return JsonResponse({'status': 'success', 'message': f'Sent to {request.user.email}'})


@require_POST
@owner_required(api=True)
def share_pdf(request):
    """Return an advisor answer as a downloadable PDF."""
    from weasyprint import HTML
    html, title = _share_payload(request)
    pdf_bytes = HTML(string=wrap_html_for_export(html, title), base_url='').write_pdf()
    safe = title.encode('ascii', 'ignore').decode('ascii')
    filename = (safe.replace(' ', '_').strip('_')[:40] or 'advisor_note') + '.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
