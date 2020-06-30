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

from datetime import date, datetime

import logging
import pickle

from .task import Task
from .reminder import Notification


_LOGGER = logging.getLogger(__name__)


class Manager():
    """Root class for domain data structure."""

    def __init__(self):
        """Constructor."""
        self.tasks = list()

    def store(self, outputFile):
        with open(outputFile, 'wb') as fp:
            pickle.dump( self.tasks, fp )

    def load(self, inputFile):
        try:
            with open( inputFile, 'rb') as fp:
                self.tasks = pickle.load(fp)
        except FileNotFoundError:
            self.tasks = list()

    def hasEntries( self, entriesDate: date ):
        for task in self.tasks:
            if task.hasEntry( entriesDate ):
                return True
        return False

#     def getEntries( self, entriesDate: date ):
#         retList = list()
#         for entry in self.tasks:
#             currDate = entry.getReferenceDateTime().date()
#             if currDate == entriesDate:
#                 retList.append( entry )
#         return retList

    def getTasks( self ):
        return list( self.tasks )       ## shallow copy of list

    def addTask( self, task: Task ):
        self.tasks.append( task )

    def addNewTask( self, taskdate: date, title ):
        task = Task()
        task.title = title
        task.setDefaultDate( taskdate )
        self.addTask( task )
        return task

    def addNewTaskDateTime( self, taskdate: datetime, title ):
        task = Task()
        task.title = title
        task.setDefaultDateTime( taskdate )
        self.addTask( task )
        return task

    def removeTask( self, task: Task ):
        self.tasks.remove( task )

    def replaceTask( self, oldTask: Task, newTask: Task ):
        for i in range(0, len(self.tasks)):
            entry = self.tasks[i]
            if entry == oldTask:
                self.tasks[i] = newTask
                break

    def addNewDeadline( self, eventdate: date, title ):
        event = Task()
        event.title = title
        event.setDeadlineDate( eventdate )
        self.addTask( event )

    def addNewDeadlineDateTime( self, eventdate: datetime, title ):
        eventTask = Task()
        eventTask.title = title
        eventTask.setDeadlineDateTime( eventdate )
        self.addTask( eventTask )
        return eventTask

    def getNotificationList(self):
        ret = list()
        for i in range(0, len(self.tasks)):
            task = self.tasks[i]
            notifs = task.getNotifications()
            ret.extend( notifs )
        ret.sort( key=Notification.sortByTime )
        return ret
