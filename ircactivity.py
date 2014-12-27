# Copyright (C) 2007, Eduardo Silva <edsiper@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import logging
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
import json

from sugar3.activity import activity
from sugar3 import env
import purk
import purk.conf
import purk.windows


class IRCActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        logging.debug('Starting the IRC Activity')
        self.set_title(_('IRC Activity'))

        self.add_events(Gdk.EventMask.VISIBILITY_NOTIFY_MASK)
        self.connect('visibility-notify-event',
                     self.__visibility_notify_event_cb)

        self.is_visible = False

        self.client = purk.Client()
        if handle.object_id is None:
            self.default_config()
        self.client.show()
        widget = self.client.get_widget()

        # CANVAS
        self.set_canvas(widget)

        # TOOLBAR
        from sugar3.graphics.toolbarbox import ToolbarBox, ToolbarButton
        from sugar3.activity.widgets import ActivityToolbarButton, StopButton, ShareButton, TitleEntry, ActivityButton

        toolbar_box = ToolbarBox()
        self.activity_button = ActivityButton(self)
        toolbar_box.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        title_entry = TitleEntry(self)
        toolbar_box.toolbar.insert(title_entry, -1)
        title_entry.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

    def __visibility_notify_event_cb(self, window, event):
        self.is_visible = event.state != Gdk.VisibilityState.FULLY_OBSCURED

        #Configuracion por defecto

    def default_config(self):
        self.client.join_server('us.freenode.net')
        self.client.add_channel('#sugar')
        self.client.add_channel_other('#sugar-es')

    def read_file(self, file_path):
        if self.metadata['mime_type'] != 'text/plain':
            return

        fd = open(file_path, 'r')
        text = fd.read()
        data = json.loads(text)
        fd.close()

        self.client.run_command('NICK %s' % (data['nick']))

        self.client.join_server(data['server'])
        for chan in data['channels']:
            self.client.add_channel(chan)
            self.client.add_channel_other(chan)
        self.client.core.window.network.requested_joins = set()
        for winid in data['scrollback'].keys():
            if winid in data['channels']:
                win = purk.windows.new(purk.windows.ChannelWindow,
                                       self.client.core.window.network,
                                       winid, self.client.core)
            else:
                win = purk.windows.new(purk.windows.QueryWindow,
                                       self.client.core.window.network,
                                       winid, self.client.core)
            win.output.get_buffer().set_text(data['scrollback'][winid])
            if winid == data['current-window']:
                self.client.core.window.network.requested_joins = set([winid])

    def write_file(self, file_path):
        if not self.metadata['mime_type']:
            self.metadata['mime_type'] = 'text/plain'

        data = {}
        data['nick'] = self.client.core.window.network.me
        data['server'] = self.client.core.window.network.server
        data['username'] = self.client.core.window.network.server
        data['fullname'] = self.client.core.window.network.fullname
        data['password'] = self.client.core.window.network.password
        data['current-window'] = self.client.core.manager.get_active().id
        data['channels'] = []
        data['scrollback'] = {}

        for i in range(self.client.core.manager.tabs.get_n_pages()):
            win = self.client.core.manager.tabs.get_nth_page(i)
            if win.id == "status":
                continue
            if win.is_channel():
                data['channels'].append(win.id)
            buf = win.output.get_buffer()
            data['scrollback'][win.id] = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

        fd = open(file_path, 'w')
        text = json.dumps(data)
        fd.write(text)
        fd.close()
