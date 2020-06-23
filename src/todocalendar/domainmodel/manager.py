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

from datetime import date

import logging


_LOGGER = logging.getLogger(__name__)


class Manager():
    """Root class for domain data structure."""

    def __init__(self):
        """Constructor."""
        self.tasks = list()

    def hasEntries( self, entriesDate: date ):
        for taskDate, _ in self.tasks:
            if taskDate == entriesDate:
                return True
        return False

    def getEntries( self, entriesDate: date ):
        retList = list()
        for taskDate, taskText in self.tasks:
            if taskDate == entriesDate:
                retList.append( taskText )
        return retList

    def addTask( self, taskdate: date, title ):
        self.tasks.append( (taskdate, title) )