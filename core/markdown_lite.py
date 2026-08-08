"""Minimal Markdown-to-HTML renderer for static policy pages.

Supports only the subset of Markdown used by files under `policies/`:
headers (#, ##, ###), bold (**text**), and unordered lists (- item).
Avoids pulling in a third-party Markdown dependency for a handful of
static legal documents.
"""
import re
from html import escape

_BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
_HEADER_RE = re.compile(r'^(#{1,6})\s+(.*)$')
_LIST_ITEM_RE = re.compile(r'^-\s+(.*)$')


def _inline(text: str) -> str:
    return _BOLD_RE.sub(r'<strong>\1</strong>', escape(text))


def render_markdown_lite(text: str) -> str:
    html_parts = []
    paragraph_lines = []
    list_items = []

    def flush_paragraph():
        if paragraph_lines:
            html_parts.append(f'<p>{" ".join(_inline(l) for l in paragraph_lines)}</p>')
            paragraph_lines.clear()

    def flush_list():
        if list_items:
            items = ''.join(f'<li>{_inline(item)}</li>' for item in list_items)
            html_parts.append(f'<ul>{items}</ul>')
            list_items.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            flush_paragraph()
            flush_list()
            continue

        header_match = _HEADER_RE.match(line)
        list_match = _LIST_ITEM_RE.match(line)

        if header_match:
            flush_paragraph()
            flush_list()
            level = len(header_match.group(1))
            html_parts.append(f'<h{level}>{_inline(header_match.group(2))}</h{level}>')
        elif list_match:
            flush_paragraph()
            list_items.append(list_match.group(1))
        else:
            flush_list()
            paragraph_lines.append(line)

    flush_paragraph()
    flush_list()

    return '\n'.join(html_parts)
