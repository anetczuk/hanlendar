# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import logging

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from hanlendar.domainmodel.local.reminder import Notification


_LOGGER = logging.getLogger(__name__)


class NotificationTimer( QObject ):

    remindTask = pyqtSignal( Notification )

    def __init__( self, *args ):
        QObject.__init__( self, *args )
        self.timer = QTimer(self)
        self.notifs = list()
        self.nextNotif = None
        self.timer.timeout.connect( self.handleTimeout )

    def setNotifications(self, notifList):
        self.notifs = notifList
        self.processNotifs()

    def processNotifs(self):
        self.timer.stop()
        if len(self.notifs) < 1:
            _LOGGER.info("no notifications")
            self.nextNotif = None
            return
        self.nextNotif = self.notifs.pop(0)
        secs = self.nextNotif.remainingSeconds()
        _LOGGER.info( "next notification: %s[s] %s", secs, self.nextNotif )
        if secs > 0:
            millis = secs * 1000
            self.timer.start( millis )
        else:
            self.handleTimeout()

    def handleTimeout(self):
        self.remindTask.emit( self.nextNotif )
        self.processNotifs()
