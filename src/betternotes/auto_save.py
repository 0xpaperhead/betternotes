# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GLib

from betternotes.constants import AUTOSAVE_DELAY_MS


class AutoSave:
    """Debounced auto-save using GLib.timeout_add."""

    def __init__(self, save_callback, delay_ms=AUTOSAVE_DELAY_MS):
        self._save_callback = save_callback
        self._delay_ms = delay_ms
        self._timeout_id = None

    def trigger(self):
        """Schedule a save after the debounce delay. Resets if called again."""
        self.cancel()
        self._timeout_id = GLib.timeout_add(self._delay_ms, self._do_save)

    def cancel(self):
        """Cancel any pending save."""
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

    def save_now(self):
        """Save immediately, canceling any pending debounce."""
        self.cancel()
        self._save_callback()

    def _do_save(self):
        self._timeout_id = None
        self._save_callback()
        return GLib.SOURCE_REMOVE
