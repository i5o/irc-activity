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

import os
import logging
from gettext import gettext as _

import gtk
import dbus

from sugar.activity import activity
from sugar import env
import purk

class IRCActivity(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        logging.debug('Starting the XoIRC Activity')
        self.set_title(_('Xo IRC Activity'))

        self.add_events(gtk.gdk.VISIBILITY_NOTIFY_MASK)
        self.connect('visibility-notify-event',
                     self.__visibility_notify_event_cb)

        self.is_visible = False

        client = purk.Client()
        client.add_channel('#sugar')
        client.join_server('irc.freenode.net')
        client.show()
        widget = client.get_widget()

        # CANVAS
        self.set_canvas(widget)

        # TOOLBAR
        toolbox = activity.ActivityToolbox(self)
        self.set_toolbox(toolbox)
        self.show_all()

    def __visibility_notify_event_cb(self, window, event):
        self.is_visible = event.state != gtk.gdk.VISIBILITY_FULLY_OBSCURED

    def read_file(self, file_path):
        try:
            data_file = open(file_path, 'r')
            data = data_file.readlines()
            
            # looking for nickname
            for part in data:
                if 'nck:' in part:
                    self.client.run_command('/nick %s' % part[4:])
                
                if 'ch:' in part:
                    self.client.add_channel(part[3:])
                
                if 'svr:' in part:
                    self.client.join_server(part[4:])
        except:
            logging.debug("error when reading")
			
    def write_file(self, file_path):
        logging.debug("executing write_file")
        try:
            saved_data = open(file_path, 'w')
            saved_data.write("nck:%s\n" % self.client.core.window.network.me)
            
            for channel in self.client.core.channels:
                saved_data.write("ch:%s\n" % channel)
            
            saved_data.write("svr:%s\n" % self.client.core.window.network.server)
            
            saved_data.close()
            
        except:
            logging.debug("error when writing")
