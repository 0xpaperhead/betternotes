# SPDX-License-Identifier: GPL-3.0-or-later

DEFAULT_COLOR = 'yellow'

# (name, light_bg, dark_bg, light_header, dark_header, light_fg, dark_fg)
NOTE_COLORS = {
    'yellow':  ('#FFF9C4', '#4A4520', '#FFE082', '#6B5F1E', '#2E2A05', '#F5E6A0'),
    'blue':    ('#BBDEFB', '#1A3A5C', '#90CAF9', '#1B3F6B', '#0D1F33', '#90B8E0'),
    'green':   ('#C8E6C9', '#1B3D1E', '#A5D6A7', '#1E5023', '#0D260F', '#8EC690'),
    'pink':    ('#F8BBD0', '#4A1B30', '#F48FB1', '#6B1E45', '#33101F', '#E08AAA'),
    'orange':  ('#FFE0B2', '#4A3018', '#FFCC80', '#6B4420', '#331F0D', '#E6C090'),
    'purple':  ('#E1BEE7', '#3A1B4A', '#CE93D8', '#4A1E6B', '#260F33', '#C690E0'),
    'red':     ('#FFCDD2', '#4A1B1B', '#EF9A9A', '#6B1E1E', '#33100F', '#E09090'),
    'teal':    ('#B2DFDB', '#1B3D3A', '#80CBC4', '#1E5046', '#0D2623', '#90C6C0'),
}

COLOR_NAMES = list(NOTE_COLORS.keys())


def get_css():
    """Generate CSS for all note colors with light/dark variants."""
    lines = []

    for name, (light_bg, dark_bg, light_header, dark_header, light_fg_unused, dark_fg_unused) in NOTE_COLORS.items():
        lines.append(f'''
.note-color-{name} {{
    background-color: {light_bg};
}}
.note-color-{name} headerbar {{
    background-color: {light_header};
}}
.note-color-{name}-card {{
    background-color: {light_bg};
    border-radius: 12px;
    padding: 12px;
}}

.dark .note-color-{name} {{
    background-color: {dark_bg};
}}
.dark .note-color-{name} headerbar {{
    background-color: {dark_header};
}}
.dark .note-color-{name}-card {{
    background-color: {dark_bg};
}}''')

    return '\n'.join(lines)
