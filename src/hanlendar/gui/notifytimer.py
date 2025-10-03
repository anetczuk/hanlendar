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
import datetime
from typing import List

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from hanlendar.domainmodel.reminder import Notification


_LOGGER = logging.getLogger(__name__)


class NotificationTimer( QObject ):

    remindTask = pyqtSignal( Notification )

    def __init__( self, *args ):
        QObject.__init__( self, *args )
        self.timer = QTimer(self)
        self.notifs: List[ Notification ] = list()
        self.nextNotif: Notification = None
        self.timer.timeout.connect( self.handleTimeout )

    def setNotifications( self, notifList: List[ Notification ] ):
        self.notifs = notifList
        self.processNotifs()

    def processNotifs(self):
        self.timer.stop()
        if len(self.notifs) < 1:
            _LOGGER.info("no notifications")
            self.nextNotif = None
            return
        self.nextNotif = self.notifs.pop(0)
        remainingTime: datetime.timedelta = self.nextNotif.remainingTime()
        secs = remainingTime.total_seconds()
        _LOGGER.info( "next notification: %s[s] %s", secs, self.nextNotif )
        if secs < 1:
            self.handleTimeout()
            return
        millis = int(secs * 1000)
        ## 2147483647ms is ~24 days -- enough to skip
        if millis >= 2147483647:
            _LOGGER.warning( "unable to set timer for time delta %s", remainingTime )
            return
        self.timer.start( millis )      ## 2147483647 maximum accepted value

    def handleTimeout(self):
        self.remindTask.emit( self.nextNotif )
        self.processNotifs()
