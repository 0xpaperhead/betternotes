# SPDX-License-Identifier: GPL-3.0-or-later
"""
Rich text serialization between GtkTextBuffer and JSON.

JSON format:
{
  "blocks": [
    {
      "type": "paragraph" | "bullet",
      "runs": [
        {"text": "hello ", "tags": []},
        {"text": "world", "tags": ["bold", "italic"]}
      ]
    }
  ]
}

Supported tags: bold, italic, underline, strikethrough, bullet
"""

import json

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


TAG_NAMES = {'bold', 'italic', 'underline', 'strikethrough'}


def serialize_buffer(text_buffer) -> str:
    """Serialize a GtkTextBuffer to JSON string."""
    blocks = []
    start = text_buffer.get_start_iter()
    end = text_buffer.get_end_iter()

    if start.equal(end):
        return json.dumps({'blocks': []})

    full_text = text_buffer.get_text(start, end, True)
    lines = full_text.split('\n')

    line_start = text_buffer.get_start_iter()

    for line_idx, line_text in enumerate(lines):
        line_end = line_start.copy()
        line_end.forward_chars(len(line_text))

        runs = _extract_runs(text_buffer, line_start, line_end)

        # Determine block type
        block_type = 'paragraph'
        bullet_tag = text_buffer.get_tag_table().lookup('bullet')
        if bullet_tag and line_start.has_tag(bullet_tag):
            block_type = 'bullet'

        blocks.append({'type': block_type, 'runs': runs})

        # Move past the newline
        if line_idx < len(lines) - 1:
            line_start = line_end.copy()
            line_start.forward_char()
        else:
            line_start = line_end

    return json.dumps({'blocks': blocks})


def _extract_runs(text_buffer, start, end):
    """Extract formatted text runs from a range in the buffer."""
    runs = []
    if start.equal(end):
        return [{'text': '', 'tags': []}]

    it = start.copy()
    while it.compare(end) < 0:
        # Get active tags at this position
        active_tags = _get_tag_names(it)

        # Find how far this tag combination extends
        run_end = it.copy()
        while run_end.compare(end) < 0:
            if not run_end.forward_to_tag_toggle(None):
                run_end = end.copy()
                break
            if run_end.compare(end) >= 0:
                run_end = end.copy()
                break
            # Check if tags actually changed
            if _get_tag_names(run_end) != active_tags:
                break

        text = text_buffer.get_text(it, run_end, True)
        if text:
            runs.append({'text': text, 'tags': sorted(active_tags)})

        it = run_end.copy()

    if not runs:
        runs = [{'text': '', 'tags': []}]

    return runs


def _get_tag_names(text_iter):
    """Get recognized formatting tag names at a text iterator position."""
    tags = text_iter.get_tags()
    names = set()
    for tag in tags:
        name = tag.get_property('name')
        if name in TAG_NAMES:
            names.add(name)
    return names


def deserialize_to_buffer(text_buffer, json_str):
    """Deserialize JSON string into a GtkTextBuffer, applying formatting tags."""
    text_buffer.set_text('')

    if not json_str:
        return

    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        # Treat as plain text fallback
        text_buffer.set_text(json_str)
        return

    blocks = data.get('blocks', [])
    if not blocks:
        return

    _ensure_tags(text_buffer)

    for block_idx, block in enumerate(blocks):
        if block_idx > 0:
            text_buffer.insert(text_buffer.get_end_iter(), '\n')

        block_start_offset = text_buffer.get_end_iter().get_offset()
        block_type = block.get('type', 'paragraph')

        for run in block.get('runs', []):
            text = run.get('text', '')
            if not text:
                continue

            start_offset = text_buffer.get_end_iter().get_offset()
            text_buffer.insert(text_buffer.get_end_iter(), text)

            # Apply formatting tags
            run_start = text_buffer.get_iter_at_offset(start_offset)
            run_end = text_buffer.get_end_iter()
            for tag_name in run.get('tags', []):
                if tag_name in TAG_NAMES:
                    tag = text_buffer.get_tag_table().lookup(tag_name)
                    if tag:
                        text_buffer.apply_tag(tag, run_start, run_end)

        # Apply bullet tag to entire line
        if block_type == 'bullet':
            line_start = text_buffer.get_iter_at_offset(block_start_offset)
            line_end = text_buffer.get_end_iter()
            bullet_tag = text_buffer.get_tag_table().lookup('bullet')
            if bullet_tag:
                text_buffer.apply_tag(bullet_tag, line_start, line_end)


def _ensure_tags(text_buffer):
    """Ensure all formatting tags exist in the buffer's tag table."""
    table = text_buffer.get_tag_table()

    tag_props = {
        'bold': {'weight': 700},
        'italic': {'style': 2},  # Pango.Style.ITALIC
        'underline': {'underline': 1},  # Pango.Underline.SINGLE
        'strikethrough': {'strikethrough': True},
        'bullet': {},
    }

    for name, props in tag_props.items():
        if table.lookup(name) is None:
            tag = text_buffer.create_tag(name, **props)


def get_plain_text(json_str) -> str:
    """Extract plain text from rich-text JSON (for search indexing)."""
    if not json_str:
        return ''
    try:
        data = json.loads(json_str)
        lines = []
        for block in data.get('blocks', []):
            text = ''.join(run.get('text', '') for run in block.get('runs', []))
            lines.append(text)
        return '\n'.join(lines)
    except (json.JSONDecodeError, TypeError):
        return json_str
