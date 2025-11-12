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

import os
import logging

import glob

from hanlendar import persist
from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.local.task import LocalTask, fill_completed_list, update_start_due_date
from hanlendar.domainmodel.local.todo import LocalToDo


_LOGGER = logging.getLogger(__name__)


class ModuleMapper:
    """Convert module names for given versions to properly deserialize data."""

    def __init__(self, version):
        self.version = version

    def __call__(self, module, name):
        version = self.version
        if version < 1:
            ## convert from version 0
            module = module.replace("todocalendar", "hanlendar")
            version = 1
        if version == 1:
            ## convert from version 1
            module = module.replace("hanlendar.domainmodel.", "hanlendar.domainmodel.local.")
            version += 1
        if version == 2:
            ## convert from version 2
            if module == "hanlendar.domainmodel.local.item":
                module = "hanlendar.domainmodel.item"
            version += 1
        if version == 3:
            ## convert from version 3
            if module == "hanlendar.domainmodel.local.recurrent":
                module = "hanlendar.domainmodel.recurrent"
            if module == "hanlendar.domainmodel.local.reminder":
                module = "hanlendar.domainmodel.reminder"
            version += 1
        if version == 4:
            ## convert from version 4
            if module == "hanlendar.domainmodel.local.task" and name == "Task":
                name = "LocalTask"
            version += 1
        if version == 5:
            ## do nothing
            version += 1
        if version == 6:
            if module == "hanlendar.domainmodel.local.todo" and name == "ToDo":
                name = "LocalToDo"
            version += 1
        if version == 7:
            ## do nothing
            version += 1
        if version == 8:
            if module == "hanlendar.domainmodel.task":
                module = {
                    "DateRange": "hanlendar.domainmodel.taskoccurrence",
                    "DateTimeRange": "hanlendar.domainmodel.taskoccurrence",
                    "TaskOccurrence": "hanlendar.domainmodel.taskoccurrence",
                    "Task": "hanlendar.domainmodel.local.task",
                }.get(name, module)
            version += 1

        return (module, name)


class LocalManager(Manager):
    """Root class for domain data structure."""

    ## 1 - renamed modules from 'todocalendar' to 'hanlendar'
    ## 2 - renamed modules from 'hanlendar.domainmodel.*' to 'hanlendar.domainmodel.local.*'
    ## 3 - renamed modules from 'hanlendar.domainmodel.local.item' to 'hanlendar.domainmodel.item'
    ## 4 - renamed modules from 'hanlendar.domainmodel.local.recurrent' to 'hanlendar.domainmodel.recurrent'
    ##     renamed modules from 'hanlendar.domainmodel.local.reminder' to 'hanlendar.domainmodel.reminder'
    ## 5 - renamed class from 'hanlendar.domainmodel.local.task.Task' to 'hanlendar.domainmodel.local.task.LocalTask'
    ## 6 - moved data to 'local' subdirectory
    ## 7 - renamed class from 'hanlendar.domainmodel.local.todo.ToDo' to 'hanlendar.domainmodel.local.todo.LocalToDo'
    ## 8 - removed "_recurrentOffset" from LocalTask
    ## 9 - moved Task from "hanlendar.domainmodel.task" to "hanlendar.domainmodel.local.task"
    ##     moved remaining content from "hanlendar.domainmodel.task" to "hanlendar.domainmodel.taskoccurence"
    _class_version = 9

    def __init__(self, ioDir=None):
        self._tasks = []
        self._todos = []
        self.notes = {"notes": ""}  ## default notes

        self._ioDir = ioDir  ## do not persist

    def storeToDisk(self, outputDir):
        if outputDir:
            self._ioDir = outputDir
        self.storeData()

    # override
    def storeData(self):
        _LOGGER.info("storing data")
        if self._ioDir is None:
            _LOGGER.warning("unable to store data -- no root directory given")
            return False

        outputDir = self._ioDir

        changed = False

        outputFile = os.path.join(outputDir, "version.obj")
        if persist.store_object(self._class_version, outputFile) is True:
            changed = True

        outputFile = os.path.join(outputDir, "tasks.obj")
        if persist.store_object(self.tasks, outputFile) is True:
            changed = True

        outputFile = os.path.join(outputDir, "todos.obj")
        if persist.store_object(self.todos, outputFile) is True:
            changed = True

        outputFile = os.path.join(outputDir, "notes.obj")
        if persist.store_object(self.notes, outputFile) is True:
            changed = True

        ## backup data
        objFiles = glob.glob(outputDir + "/*.obj")
        storedZipFile = os.path.join(outputDir, "data.zip")
        persist.backup_files(objFiles, storedZipFile)

        return changed

    def loadFromDisk(self, inputDir):
        if inputDir:
            self._ioDir = inputDir
        self.loadData()

    # override
    def loadData(self):
        if self._ioDir is None:
            _LOGGER.warning("unable to load data -- no root directory given")
            return

        inputDir = self._ioDir

        mngrVersion = self._class_version
        try:
            inputFile = os.path.join(inputDir, "version.obj")
            mngrVersion = persist.load_object(inputFile)
            if mngrVersion != self._class_version:
                _LOGGER.info("converting object from version %s to %s", mngrVersion, self._class_version)
                ## do nothing for now
        except FileNotFoundError:
            _LOGGER.warning("unable to load file: %s", inputFile)

        mapperObject = ModuleMapper(mngrVersion)

        try:
            inputFile = os.path.join(inputDir, "tasks.obj")
            self.tasks = persist.load_object(inputFile, class_mapper=mapperObject)
            if self.tasks is None:
                self.tasks = []
        except FileNotFoundError:
            _LOGGER.warning("unable to load file: %s", inputFile)
            self.tasks = []

        try:
            inputFile = os.path.join(inputDir, "todos.obj")
            self.todos = persist.load_object(inputFile, class_mapper=mapperObject)
            if self.todos is None:
                self.todos = []
        except FileNotFoundError:
            _LOGGER.warning("unable to load file: %s", inputFile)
            self.todos = []

        try:
            inputFile = os.path.join(inputDir, "notes.obj")
            self.notes = persist.load_object(inputFile, class_mapper=mapperObject)
            if self.notes is None:
                self.notes = {"notes": ""}
        except FileNotFoundError:
            _LOGGER.warning("unable to load file: %s", inputFile)
            self.notes = {"notes": ""}
        self.fixData()

        if mngrVersion < 8:
            all_tasks = self.getTasksAll()
            for task in all_tasks:
                if hasattr(task, "_fix_completedList_") and task._fix_completedList_:  # pylint: disable=W0212
                    start_date, due_date, recurr_offset = task._fix_completedList_  # pylint: disable=W0212
                    recurrence = task.getAppliedRecurrence()
                    if recurrence is not None:
                        fill_completed_list(start_date, due_date, recurr_offset, recurrence)
                    del task._fix_completedList_

                if hasattr(task, "_fix_recurrentOffset_") and task._fix_recurrentOffset_:  # pylint: disable=W0212
                    start_date, due_date, recurr_offset = task._fix_recurrentOffset_  # pylint: disable=W0212
                    recurrence = task.getAppliedRecurrence()
                    if recurrence is not None:
                        next_start_date, next_due_date = update_start_due_date(
                            start_date,
                            due_date,
                            recurr_offset,
                            recurrence,
                        )
                        if next_due_date is not None:
                            task.setOccurrence(next_start_date, next_due_date)
                    del task._fix_recurrentOffset_

        ## check tasks validity
        all_tasks = self.getTasksAll()
        for task in all_tasks:
            if task.recurrence is not None:
                recurr = task.getAppliedRecurrence()
                if recurr is None:
                    _LOGGER.warning("task '%s' %s has invalid recurrence", task.title, task.dueDateTime)

            if task.dueDateTime is None:
                _LOGGER.warning("task '%s' has invalid occurrence due date", task.title)

    ## index meaning:
    ##    negative: current
    ##           0: first history entry
    ##    positive: history entry by index
    def loadHistory(self, index=-1):
        if index < 0:
            self.loadData()
            return {
                "file": None,
                "version": self._class_version,
                "tasks": self.tasks,
                "todos": self.todos,
                "notes": self.notes,
            }

        outputDir = self._ioDir
        if index <= 0:
            storedZipFile = os.path.join(outputDir, "data.zip")
        else:
            storedZipFile = os.path.join(outputDir, f"data.zip.{index}")

        hist_data_raw = persist.load_backup(storedZipFile)

        version_raw = hist_data_raw.get("version.obj", None)
        mngrVersion = persist.load_data(version_raw)
        if mngrVersion != self._class_version:
            _LOGGER.info("converting object from version %s to %s", mngrVersion, self._class_version)
            ## do nothing for now

        mapperObject = ModuleMapper(mngrVersion)

        tasks_raw = hist_data_raw.get("tasks.obj", None)
        tasks = persist.load_data(tasks_raw, class_mapper=mapperObject)
        if tasks is None:
            tasks = []

        todos_raw = hist_data_raw.get("todos.obj", None)
        todos = persist.load_data(todos_raw, class_mapper=mapperObject)
        if todos is None:
            todos = []

        notes_raw = hist_data_raw.get("notes.obj", None)
        notes = persist.load_data(notes_raw, class_mapper=mapperObject)
        if notes is None:
            notes = []

        return {"file": storedZipFile, "version": mngrVersion, "tasks": tasks, "todos": todos, "notes": notes}

    def restoreTaskByTitle(self, _history_index, task_title):
        data_dict = self.loadHistory(160)
        tasks: list[Task] = data_dict.get("tasks", [])
        found_task = self.findTaskByTitle(tasks, task_title)
        if found_task is not None:
            self.addTask(found_task)
            return True
        return False

    def findTaskByTitle(self, tasks_list, title):
        flat_set = set(Item.getAllSubItemsFromList(tasks_list))
        for task in flat_set:
            task_title = task.getTitle()
            if task_title == title:
                return task
        return None

    ## ======================================================================

    # override
    def _getTasks(self):
        return self._tasks

    # override
    def _setTasks(self, value):
        self._tasks = value

    # override
    def getTasksAll(self):
        return Item.getAllSubItemsFromList(self.tasks)

    # override
    def createEmptyTask(self):
        return LocalTask()

    # override
    def _getToDos(self):
        return self._todos

    # override
    def _setToDos(self, value):
        self._todos = value

    # override
    def getTodosAll(self):
        return Item.getAllSubItemsFromList(self.todos)

    # override
    def createEmptyToDo(self) -> LocalToDo:
        return LocalToDo()

    # override
    def _getNotes(self):
        return self.notes

    # override
    def _setNotes(self, value):
        self.notes = value
