# SPDX-License-Identifier: GPL-3.0-or-later

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio, Gtk

from betternotes.colors import COLOR_NAMES
from betternotes.constants import APP_ID


class PreferencesWindow(Adw.PreferencesDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title('Preferences')

        self._settings = None
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source and schema_source.lookup(APP_ID, True):
            self._settings = Gio.Settings.new(APP_ID)

        self._build_ui()

    def _build_ui(self):
        # General page
        page = Adw.PreferencesPage(title='General', icon_name='preferences-system-symbolic')

        # Appearance group
        appearance_group = Adw.PreferencesGroup(title='Appearance')

        # Default color
        color_row = Adw.ComboRow(title='Default Note Color')
        color_list = Gtk.StringList()
        for name in COLOR_NAMES:
            color_list.append(name.capitalize())
        color_row.set_model(color_list)

        if self._settings:
            current = self._settings.get_string('default-color')
            try:
                idx = COLOR_NAMES.index(current)
                color_row.set_selected(idx)
            except ValueError:
                pass
            color_row.connect('notify::selected', self._on_color_changed)

        appearance_group.add(color_row)
        page.add(appearance_group)

        # Trash group
        trash_group = Adw.PreferencesGroup(title='Trash')

        retention_row = Adw.SpinRow(
            title='Auto-delete after (days)',
            subtitle='Trashed notes are permanently deleted after this many days',
        )
        adjustment = Gtk.Adjustment(
            lower=1, upper=365, step_increment=1, page_increment=7, value=30,
        )
        retention_row.set_adjustment(adjustment)

        if self._settings:
            retention_row.set_value(self._settings.get_int('trash-retention-days'))
            retention_row.connect('notify::value', self._on_retention_changed)

        trash_group.add(retention_row)
        page.add(trash_group)

        self.add(page)

    def _on_color_changed(self, row, pspec):
        if self._settings:
            idx = row.get_selected()
            if 0 <= idx < len(COLOR_NAMES):
                self._settings.set_string('default-color', COLOR_NAMES[idx])

    def _on_retention_changed(self, row, pspec):
        if self._settings:
            self._settings.set_int('trash-retention-days', int(row.get_value()))
