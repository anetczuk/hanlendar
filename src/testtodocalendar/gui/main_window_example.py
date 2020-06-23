#!/usr/bin/python3
#
# MIT License
#
# Copyright (c) 2017 Arkadiusz Netczuk <dev.arnet@gmail.com>
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


import sys
import os


#### append local library
sys.path.append(os.path.abspath( os.path.join(os.path.dirname(__file__), "../..") ))


import argparse
import logging

import todocalendar.logger as logger

from todocalendar.gui.qt import QApplication
from todocalendar.gui.sigint import setup_interrupt_handling
from todocalendar.gui.main_window import MainWindow

from datetime import date, timedelta


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


_LOGGER = logging.getLogger(__name__)


def prepareExampleData( window: MainWindow ):
    dataManager = window.getManager()
    taskDate = date.today()
    dataManager.addTask( taskDate, "test task 1" )
    
    if taskDate.day > 15:
        taskDate = taskDate - timedelta(2)
    else:
        taskDate = taskDate + timedelta(2)
    dataManager.addTask( taskDate, "test task 2" )
    window.reloadData()


parser = argparse.ArgumentParser(description='ToDo Calendar')
parser.add_argument('--profile', action='store_const', const=True, default=False, help='Profile the code' )
parser.add_argument('--pfile', action='store', default=None, help='Profile the code and output data to file' )
# parser.add_argument('--mode', action='store', required=True, choices=["BF", "POLY", "COMMON"], help='Mode' )
# parser.add_argument('--file', action='store', required=True, help='File with data' )
parser.add_argument('--connect', action='store', default=None, help='BT address to connect to' )
parser.add_argument('--minimized', action='store_const', const=True, default=False, help='Start minimized' )


args = parser.parse_args()


logFile = logger.getLoggingOutputFile()
logger.configure( logFile )


_LOGGER = logging.getLogger(__name__)

_LOGGER.debug("Starting the test application")

_LOGGER.debug("Logger log file: %s" % logFile)


exitCode = 0

try:

    app = QApplication(sys.argv)
    app.setApplicationName("ToDoCalendar")
    app.setOrganizationName("arnet")
    ### app.setOrganizationDomain("www.my-org.com")

    window = MainWindow()
    window.loadSettings()

    prepareExampleData( window )

    if args.minimized is False:
        window.show()

    setup_interrupt_handling()

    exitCode = app.exec_()

    if exitCode == 0:
        window.saveSettings()

    _LOGGER.info("Done with exit code: %s", exitCode)

except BaseException:
    exitCode = 1
    _LOGGER.exception("Exception occurred")
    raise

sys.exit(exitCode)
