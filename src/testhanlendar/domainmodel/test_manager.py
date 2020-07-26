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

import unittest

import datetime
from datetime import timedelta

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.recurrent import Recurrent


class ManagerTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

#     def test_getTaskOccurrences_entries(self):
#         manager = Manager()
#
#         taskDate1 = datetime.date( 2020, 5, 17 )
#         manager.addNewTask( taskDate1, "task1" )
#         taskDate2 = datetime.date( 2020, 5, 18 )
#         manager.addNewTask( taskDate2, "task2" )
#         eventDate1 = datetime.date( 2020, 5, 19 )
#         manager.addNewTask( eventDate1, "event1" )
#
#         entries = manager.getTaskOccurrences(taskDate2)
#         self.assertEqual( len(entries), 1 )
#         self.assertEqual( entries[0].title, "task2" )
#
#         entries = manager.getTaskOccurrences(eventDate1)
#         self.assertEqual( len(entries), 1 )
#         self.assertEqual( entries[0].title, "event1" )

    def test_getTaskOccurrencesForDate_recurrent_completed(self):
        manager = Manager()
        task = manager.addTask()
        todayDate = datetime.datetime.today()
        dueDate = todayDate.replace( day=1, hour=12 )
        task.dueDateTime = dueDate
        task.recurrence = Recurrent()
        task.recurrence.setWeekly()
        task.setCompleted()                ## mark first occurrence completed

        tasksList = manager.getTaskOccurrencesForDate( dueDate.date() )
        self.assertEqual( len( tasksList ), 1 )

    def test_getTasks(self):
        manager = Manager()
        manager.addNewTask( datetime.date.today(), "task1" )
        manager.addNewTask( datetime.date.today(), "task2" )

        self.assertEqual( len( manager.getTasks() ), 2 )

        tasksList = manager.getTasks()
        tasksList.clear()
        self.assertEqual( len( manager.getTasks() ), 2 )

    def test_getTasksAll(self):
        manager = Manager()
        task1 = manager.addTask( Task("task1") )
        task2 = manager.addTask( Task("task2") )
        subtask = task2.addSubItem( Task("subtask1") )
        subtask2 = subtask.addSubItem( Task("subtask2") )

        allTasks = manager.getTasksAll()
        self.assertEqual( len( allTasks ), 4 )
        self.assertEqual( allTasks[0], task1 )
        self.assertEqual( allTasks[1], task2 )
        self.assertEqual( allTasks[2], subtask )
        self.assertEqual( allTasks[3], subtask2 )

        allTasks.clear()
        self.assertEqual( len( manager.getTasksAll() ), 4 )

    def test_getNextDeadline_None(self):
        manager = Manager()
        manager.addTask( Task("task1") )
        manager.addTask( Task("task2") )

        deadlineTask = manager.getNextDeadline()
        self.assertEqual( deadlineTask, None )

    def test_getNextDeadline(self):
        manager = Manager()
        taskDate = datetime.datetime.today()
        manager.addNewTaskDateTime( taskDate + timedelta(seconds=5), "task1" )
        manager.addNewTaskDateTime( taskDate, "task2" )

        deadlineTask = manager.getNextDeadline()
        self.assertEqual( deadlineTask.title, "task2" )

    def test_getNextDeadline_completed(self):
        manager = Manager()
        taskDate = datetime.datetime.today()
        manager.addNewTaskDateTime( taskDate + timedelta(seconds=5), "task1" )
        task2 = manager.addNewTaskDateTime( taskDate, "task2" )
        task2.setCompleted()

        deadlineTask = manager.getNextDeadline()
        self.assertEqual( deadlineTask.title, "task1" )

    def test_removeTask(self):
        manager = Manager()

        taskDate1 = datetime.date( 2020, 5, 17 )
        task1 = manager.addNewTask( taskDate1, "task1" )
        taskDate2 = datetime.date( 2020, 5, 18 )
        manager.addNewTask( taskDate2, "task2" )

        tasks = manager.getTasks()
        self.assertEqual( len(tasks), 2 )

        manager.removeTask( task1 )

        tasks = manager.getTasks()
        self.assertEqual( len(tasks), 1 )
        self.assertEqual( tasks[0].title, "task2" )

    def test_replaceTask(self):
        manager = Manager()

        taskDate1 = datetime.date( 2020, 5, 17 )
        task1 = manager.addNewTask( taskDate1, "task1" )
        task2 = Task()
        task2.title = "new task"

        tasks = manager.getTasks()
        self.assertEqual( len(tasks), 1 )

        manager.replaceTask( task1, task2 )

        tasks = manager.getTasks()
        self.assertEqual( len(tasks), 1 )
        self.assertEqual( tasks[0].title, "new task" )

    def test_getNotificationList(self):
        manager = Manager()

        taskDate1 = datetime.datetime.today() + datetime.timedelta( seconds=60 )
        manager.addNewDeadlineDateTime( taskDate1, "task1" )
        taskDate2 = datetime.datetime.today() + datetime.timedelta( seconds=30 )
        manager.addNewDeadlineDateTime( taskDate2, "task2" )

        tasks = manager.getTasks()
        self.assertEqual( len(tasks), 2 )

        notifications = manager.getNotificationList()

        self.assertEqual( len(notifications), 2 )
        self.assertEqual( notifications[0].task.title, "task2" )
        self.assertEqual( notifications[1].task.title, "task1" )

    def test_getToDos(self):
        manager = Manager()
        manager.addToDo()
        manager.addToDo()

        self.assertEqual( len( manager.getToDos() ), 2 )

        tasksList = manager.getToDos()
        tasksList.clear()
        self.assertEqual( len( manager.getToDos() ), 2 )
