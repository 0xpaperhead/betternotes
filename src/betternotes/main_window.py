# SPDX-License-Identifier: GPL-3.0-or-later

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from betternotes.constants import APP_ID
from betternotes.note_card import NoteCard


class MainWindow(Adw.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = self.get_application()
        self._current_tag_filter = None
        self._search_query = ''
        self._showing_trash = False
        self._search_timeout_id = None

        self.set_title('BetterNotes')
        self.set_default_size(900, 650)
        self.set_icon_name(APP_ID)

        self._build_ui()
        self._connect_signals()
        self._refresh_notes()
        self._refresh_tags()

    def _build_ui(self):
        # Main layout
        self._toolbar_view = Adw.ToolbarView()

        # Header bar
        header = Adw.HeaderBar()

        # Search button
        self._search_btn = Gtk.ToggleButton(icon_name='system-search-symbolic')
        self._search_btn.connect('toggled', self._on_search_toggled)
        header.pack_start(self._search_btn)

        # View switcher (Notes / Trash)
        self._view_stack = Gtk.Stack()
        self._view_switcher = Gtk.StackSwitcher(stack=self._view_stack)
        header.set_title_widget(self._view_switcher)

        # Menu
        menu = Gio.Menu()
        menu.append('Keyboard Shortcuts', 'app.shortcuts')
        menu.append('Preferences', 'app.preferences')
        menu.append('About BetterNotes', 'app.about')

        menu_btn = Gtk.MenuButton(
            icon_name='open-menu-symbolic',
            menu_model=menu,
        )
        header.pack_end(menu_btn)

        self._toolbar_view.add_top_bar(header)

        # Search bar
        self._search_bar = Gtk.SearchBar()
        self._search_entry = Gtk.SearchEntry(
            placeholder_text='Search notes...',
        )
        self._search_entry.add_css_class('search-entry')
        self._search_entry.connect('search-changed', self._on_search_changed)
        self._search_bar.set_child(self._search_entry)
        self._search_bar.connect_entry(self._search_entry)
        self._toolbar_view.add_top_bar(self._search_bar)

        # Notes page
        notes_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Tag filter bar
        tag_scroll = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            vscrollbar_policy=Gtk.PolicyType.NEVER,
        )
        self._tag_bar = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )
        self._tag_bar.set_margin_start(12)
        self._tag_bar.set_margin_end(12)
        self._tag_bar.set_margin_top(6)
        self._tag_bar.set_margin_bottom(6)
        tag_scroll.set_child(self._tag_bar)
        self._tag_scroll = tag_scroll
        self._tag_scroll.set_visible(False)
        notes_page.append(tag_scroll)

        # Notes grid
        notes_scroll = Gtk.ScrolledWindow(vexpand=True)
        self._notes_grid = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=False,
            max_children_per_line=6,
            min_children_per_line=2,
            row_spacing=8,
            column_spacing=8,
        )
        self._notes_grid.add_css_class('notes-grid')
        self._notes_grid.set_margin_start(12)
        self._notes_grid.set_margin_end(12)
        self._notes_grid.set_margin_top(8)
        self._notes_grid.set_margin_bottom(8)
        notes_scroll.set_child(self._notes_grid)

        # Empty state
        self._empty_state = Adw.StatusPage(
            icon_name='document-new-symbolic',
            title='No Notes Yet',
            description='Press + or Ctrl+N to create your first note',
        )
        self._empty_state.add_css_class('empty-state')

        self._notes_stack = Gtk.Stack()
        self._notes_stack.add_named(notes_scroll, 'grid')
        self._notes_stack.add_named(self._empty_state, 'empty')
        notes_page.append(self._notes_stack)

        # Trash page
        trash_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Trash banner
        self._trash_banner = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )
        self._trash_banner.add_css_class('trash-banner')
        trash_label = Gtk.Label(
            label='Items in trash are deleted after 30 days',
            hexpand=True,
            xalign=0,
        )
        self._trash_banner.append(trash_label)
        empty_trash_btn = Gtk.Button(label='Empty Trash')
        empty_trash_btn.add_css_class('destructive-action')
        empty_trash_btn.connect('clicked', self._on_empty_trash)
        self._trash_banner.append(empty_trash_btn)
        trash_page.append(self._trash_banner)

        # Trash grid
        trash_scroll = Gtk.ScrolledWindow(vexpand=True)
        self._trash_grid = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=False,
            max_children_per_line=6,
            min_children_per_line=2,
            row_spacing=8,
            column_spacing=8,
        )
        self._trash_grid.set_margin_start(12)
        self._trash_grid.set_margin_end(12)
        self._trash_grid.set_margin_top(8)
        self._trash_grid.set_margin_bottom(8)
        trash_scroll.set_child(self._trash_grid)

        self._trash_empty_state = Adw.StatusPage(
            icon_name='user-trash-symbolic',
            title='Trash is Empty',
            description='Deleted notes will appear here',
        )

        self._trash_stack = Gtk.Stack()
        self._trash_stack.add_named(trash_scroll, 'grid')
        self._trash_stack.add_named(self._trash_empty_state, 'empty')
        trash_page.append(self._trash_stack)

        # Add to view stack
        self._view_stack.add_titled(notes_page, 'notes', 'Notes')
        self._view_stack.add_titled(trash_page, 'trash', 'Trash')
        self._view_stack.connect('notify::visible-child', self._on_view_changed)

        self._toolbar_view.set_content(self._view_stack)

        # Toast overlay (must wrap everything for toasts to display)
        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(self._toolbar_view)

        # FAB overlay
        overlay = Gtk.Overlay()
        overlay.set_child(self._toast_overlay)

        fab = Gtk.Button(
            icon_name='list-add-symbolic',
            tooltip_text='New Note (Ctrl+N)',
        )
        fab.add_css_class('fab')
        fab.add_css_class('suggested-action')
        fab.add_css_class('circular')
        fab.set_halign(Gtk.Align.END)
        fab.set_valign(Gtk.Align.END)
        fab.set_margin_end(24)
        fab.set_margin_bottom(24)
        fab.connect('clicked', lambda b: self._app.activate_action('new-note'))
        overlay.add_overlay(fab)
        self._fab = fab

        self.set_content(overlay)

    def _connect_signals(self):
        self._app.connect('note-changed', self._on_note_signal)
        self._app.connect('note-created', self._on_note_signal)
        self._app.connect('note-trashed', self._on_note_signal)
        self._app.connect('note-restored', self._on_note_signal)
        self._app.connect('note-deleted', self._on_note_signal)

    def _on_note_signal(self, app, note_id):
        self._refresh_notes()
        self._refresh_tags()
        self._refresh_trash()

    def _on_search_toggled(self, btn):
        active = btn.get_active()
        self._search_bar.set_search_mode(active)
        if active:
            self._search_entry.grab_focus()
        else:
            self._search_query = ''
            self._search_entry.set_text('')
            self._refresh_notes()

    def _on_search_changed(self, entry):
        self._search_query = entry.get_text()
        # Debounce search
        if self._search_timeout_id:
            GLib.source_remove(self._search_timeout_id)
        self._search_timeout_id = GLib.timeout_add(200, self._do_search)

    def _do_search(self):
        self._search_timeout_id = None
        self._refresh_notes()
        return GLib.SOURCE_REMOVE

    def _on_view_changed(self, stack, pspec):
        is_trash = stack.get_visible_child_name() == 'trash'
        self._showing_trash = is_trash
        self._fab.set_visible(not is_trash)
        if is_trash:
            self._refresh_trash()

    def _refresh_notes(self):
        # Clear grid
        child = self._notes_grid.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._notes_grid.remove(child)
            child = next_child

        # Get notes
        if self._search_query:
            notes = self._app.store.search_notes(self._search_query)
        elif self._current_tag_filter:
            notes = self._app.store.get_notes_by_tag(self._current_tag_filter)
        else:
            notes = self._app.store.get_all_notes()

        if not notes:
            self._notes_stack.set_visible_child_name('empty')
            return

        self._notes_stack.set_visible_child_name('grid')
        for note in notes:
            card = NoteCard(note)
            card.connect('activated', self._on_note_activated)
            card.connect('trash-requested', self._on_note_trash_requested)
            self._notes_grid.append(card)

    def _refresh_trash(self):
        child = self._trash_grid.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._trash_grid.remove(child)
            child = next_child

        trashed = self._app.store.get_trashed_notes()
        if not trashed:
            self._trash_stack.set_visible_child_name('empty')
            self._trash_banner.set_visible(False)
            return

        self._trash_stack.set_visible_child_name('grid')
        self._trash_banner.set_visible(True)
        for note in trashed:
            card = NoteCard(note, is_trash=True)
            card.connect('restore-requested', self._on_note_restore_requested)
            card.connect('delete-requested', self._on_note_delete_requested)
            self._trash_grid.append(card)

    def _refresh_tags(self):
        # Clear tag bar
        child = self._tag_bar.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._tag_bar.remove(child)
            child = next_child

        tags = self._app.store.get_all_tags()
        if not tags:
            self._tag_scroll.set_visible(False)
            return

        self._tag_scroll.set_visible(True)

        # "All" button
        all_btn = Gtk.ToggleButton(label='All')
        all_btn.add_css_class('tag-chip')
        all_btn.set_active(self._current_tag_filter is None)
        all_btn.connect('toggled', self._on_tag_filter, None)
        self._tag_bar.append(all_btn)

        for tag in tags:
            btn = Gtk.ToggleButton(label=f'{tag.name} ({tag.note_count})')
            btn.add_css_class('tag-chip')
            btn.set_active(self._current_tag_filter == tag.name)
            btn.connect('toggled', self._on_tag_filter, tag.name)
            self._tag_bar.append(btn)

    def _on_tag_filter(self, btn, tag_name):
        if btn.get_active():
            self._current_tag_filter = tag_name
        else:
            self._current_tag_filter = None
        # Untoggle other tag buttons
        child = self._tag_bar.get_first_child()
        while child:
            if isinstance(child, Gtk.ToggleButton) and child != btn:
                child.set_active(False)
            child = child.get_next_sibling()
        self._refresh_notes()

    def _on_note_activated(self, card, note_id):
        self._app.open_note(note_id)

    def _on_note_trash_requested(self, card, note_id):
        self._app.store.trash_note(note_id)
        self._app.close_note_window(note_id)
        self._app.emit('note-trashed', note_id)
        self._show_toast('Note moved to trash', 'Undo', self._undo_trash, note_id)

    def _on_note_restore_requested(self, card, note_id):
        self._app.store.restore_note(note_id)
        self._app.emit('note-restored', note_id)
        self._show_toast('Note restored')

    def _on_note_delete_requested(self, card, note_id):
        dialog = Adw.AlertDialog(
            heading='Delete Note Permanently?',
            body='This action cannot be undone.',
        )
        dialog.add_response('cancel', 'Cancel')
        dialog.add_response('delete', 'Delete')
        dialog.set_response_appearance('delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect('response', self._on_delete_confirmed, note_id)
        dialog.present(self)

    def _on_delete_confirmed(self, dialog, response, note_id):
        if response == 'delete':
            self._app.store.delete_note(note_id)
            self._app.emit('note-deleted', note_id)

    def _on_empty_trash(self, btn):
        dialog = Adw.AlertDialog(
            heading='Empty Trash?',
            body='All trashed notes will be permanently deleted.',
        )
        dialog.add_response('cancel', 'Cancel')
        dialog.add_response('empty', 'Empty Trash')
        dialog.set_response_appearance('empty', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect('response', self._on_empty_trash_confirmed)
        dialog.present(self)

    def _on_empty_trash_confirmed(self, dialog, response):
        if response == 'empty':
            self._app.store.empty_trash()
            self._refresh_trash()

    def _undo_trash(self, note_id):
        self._app.store.restore_note(note_id)
        self._app.emit('note-restored', note_id)

    def _show_toast(self, message, button_label=None, callback=None, callback_data=None):
        toast = Adw.Toast(title=message, timeout=5)
        if button_label and callback:
            toast.set_button_label(button_label)
            toast.connect('button-clicked', lambda t: callback(callback_data))
        self._toast_overlay.add_toast(toast)
