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
from typing import Any
import glob

from hanlendar import persist
from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.local.task import fill_completed_list, update_start_due_date


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

    ##  1 - renamed modules from 'todocalendar' to 'hanlendar'
    ##  2 - renamed modules from 'hanlendar.domainmodel.*' to 'hanlendar.domainmodel.local.*'
    ##  3 - renamed modules from 'hanlendar.domainmodel.local.item' to 'hanlendar.domainmodel.item'
    ##  4 - renamed modules from 'hanlendar.domainmodel.local.recurrent' to 'hanlendar.domainmodel.recurrent'
    ##      renamed modules from 'hanlendar.domainmodel.local.reminder' to 'hanlendar.domainmodel.reminder'
    ##  5 - renamed class from 'hanlendar.domainmodel.local.task.Task' to 'hanlendar.domainmodel.local.task.LocalTask'
    ##  6 - moved data to 'local' subdirectory
    ##  7 - renamed class from 'hanlendar.domainmodel.local.todo.ToDo' to 'hanlendar.domainmodel.local.todo.LocalToDo'
    ##  8 - removed "_recurrentOffset" from LocalTask
    ##  9 - moved Task from "hanlendar.domainmodel.task" to "hanlendar.domainmodel.local.task"
    ##      moved remaining content from "hanlendar.domainmodel.task" to "hanlendar.domainmodel.taskoccurence"
    ## 10 - replaced tasks.obj, todos.obj, notes.obj with data.obj
    ## 11 - added "_unknown_props"
    ## 12 - added "_calendar_id"
    _class_version = 12

    def __init__(self, ioDir=None):
        self._calendar_id: str = None  ## None for default calendar
        self._tasks = []
        self._todos = []
        self.notes = {"notes": ""}  ## default notes

        self._ioDir = ioDir  ## do not persist

        ## unknown icalendar properties
        self._unknown_props: dict[Any, Any] = None

    def storeToDisk(self, outputDir) -> bool:
        if outputDir:
            self._ioDir = outputDir
            if self._calendar_id:
                self._ioDir = os.path.join(self._ioDir, self._calendar_id)
        return self.storeData()

    # override
    def storeData(self) -> bool:
        outputDir = self._getDataPath()
        _LOGGER.info("storing calendar '%s' data to %s", self._calendar_id, outputDir)
        if outputDir is None:
            _LOGGER.warning("unable to store data -- no root directory given")
            return False

        changed = False

        outputFile = os.path.join(outputDir, "version.obj")
        if persist.store_object(self._class_version, outputFile) is True:
            changed = True

        data_dict = {
            "calendar_id": self._calendar_id,
            "tasks": self.tasks,
            "todos": self.todos,
            "notes": self.notes,
            "unknown_props": self._unknown_props,
        }
        outputFile = os.path.join(outputDir, "data.obj")
        if persist.store_object(data_dict, outputFile) is True:
            changed = True

        ## backup data
        objFiles = glob.glob(outputDir + "/*.obj")
        storedZipFile = os.path.join(outputDir, "data.zip")
        persist.backup_files(objFiles, storedZipFile)

        return changed

    def loadFromDisk(self, inputDir):
        if inputDir:
            self._ioDir = inputDir
            if self._calendar_id:
                self._ioDir = os.path.join(self._ioDir, self._calendar_id)
        self.loadData()

    # pylint: disable=R0915
    # override
    def loadData(self):
        if self._ioDir is None:
            _LOGGER.warning("unable to load data -- no root directory given")
            return

        inputDir = self._getDataPath()

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

        if mngrVersion < 10:
            self._calendar_id = None

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

        else:
            try:
                inputFile = os.path.join(inputDir, "data.obj")
                data_dict = persist.load_object(inputFile, class_mapper=mapperObject)
            except FileNotFoundError:
                _LOGGER.warning("unable to load file: %s", inputFile)
                data_dict = {"calendar_id": self._calendar_id}

            self._calendar_id = data_dict.get("calendar_id")
            self.tasks = data_dict.get("tasks", [])
            self.todos = data_dict.get("todos", [])
            self.notes = data_dict.get("notes", {"notes": ""})
            self._unknown_props = data_dict.get("unknown_props")

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

        _LOGGER.info("loaded tasks: %s todos: %s", len(self.tasks), len(self.todos))

    ## load data from local storage only (do not perform any connection)
    # override
    def loadDataLocal(self):
        self.loadData()

    ## index meaning:
    ##    negative: current
    ##           0: first history entry
    ##    positive: history entry by index
    def loadHistory(self, index=-1) -> dict[str, Any]:
        if index < 0:
            self.loadData()
            return {
                "file": None,
                "version": self._class_version,
                "tasks": self.tasks,
                "todos": self.todos,
                "notes": self.notes,
            }

        outputDir = self._getDataPath()
        if index <= 0:
            storedZipFile = os.path.join(outputDir, "data.zip")
        else:
            storedZipFile = os.path.join(outputDir, f"data.zip.{index}")

        if not os.path.exists(storedZipFile):
            return None

        _LOGGER.info("loading file: %s", storedZipFile)
        hist_data_raw = persist.load_backup(storedZipFile)

        _LOGGER.info("found files: %s", list(hist_data_raw.keys()))

        version_raw = hist_data_raw.get("version.obj", None)
        mngrVersion = persist.load_data(version_raw)
        if mngrVersion != self._class_version:
            _LOGGER.info("converting object from version %s to %s", mngrVersion, self._class_version)
            ## do nothing for now
        _LOGGER.info("found data version: %s", mngrVersion)

        tasks = None
        todos = None
        notes = None

        if mngrVersion < 10:
            ## old style
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

        else:
            ## new style
            mapperObject = ModuleMapper(mngrVersion)
            data_raw = hist_data_raw.get("data.obj", None)
            data_dict = persist.load_data(data_raw, class_mapper=mapperObject)
            if data_dict is None:
                return None

            tasks = data_dict.get("tasks", [])
            todos = data_dict.get("todos", [])
            notes = data_dict.get("notes", [])

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

    def _getDataPath(self):
        if self._ioDir is None:
            return None
        return self._ioDir

    ## overriden
    def synchronize_data(self):
        pass
        ## do nothing

    ## ======================================================================

    ## overriden
    def _getUnknownProps(self) -> dict[Any, Any]:
        if self._unknown_props is None:
            self._unknown_props = {}
        return self._unknown_props

    # override
    def getCalendarId(self) -> str:
        return self._calendar_id

    def setCalendarId(self, cal_id: str):
        self._calendar_id = cal_id

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
    def _getToDos(self):
        return self._todos

    # override
    def _setToDos(self, value):
        self._todos = value

    # override
    def getTodosAll(self):
        return Item.getAllSubItemsFromList(self.todos)

    # override
    def _getNotes(self):
        return self.notes

    # override
    def _setNotes(self, value):
        self.notes = value
