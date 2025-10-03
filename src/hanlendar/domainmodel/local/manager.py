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

import os
import logging
from typing import List

import glob
from icalendar import cal

from hanlendar import persist
from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.task import TaskOccurrence
from hanlendar.domainmodel.local.task import LocalTask
from hanlendar.domainmodel.local.todo import LocalToDo
import icalendar


_LOGGER = logging.getLogger(__name__)


class ModuleMapper():
    """Convert module names for given versions to properly deserialize data."""

    def __init__(self, version):
        self.version = version

    def __call__(self, module, name):
        version = self.version
        if version < 1:
            ## convert from version 0
            module = module.replace( "todocalendar", "hanlendar" )
            version = 1
        if version == 1:
            ## convert from version 1
            module = module.replace( "hanlendar.domainmodel.", "hanlendar.domainmodel.local." )
            version = 2
        if version == 2:
            ## convert from version 2
            if module == "hanlendar.domainmodel.local.item":
                return ("hanlendar.domainmodel.item", name)
            version = 3
        if version == 3:
            ## convert from version 3
            if module == "hanlendar.domainmodel.local.recurrent":
                return ("hanlendar.domainmodel.recurrent", name)
            if module == "hanlendar.domainmodel.local.reminder":
                return ("hanlendar.domainmodel.reminder", name)
            version = 4
        if version == 4:
            ## convert from version 4
            if module == "hanlendar.domainmodel.local.task" and name == "Task":
                return ("hanlendar.domainmodel.local.task", "LocalTask")
            version = 5
        if version == 5:
            ## do nothing
            version = 6
        if version == 6:
            if module == "hanlendar.domainmodel.local.todo" and name == "ToDo":
                return ("hanlendar.domainmodel.local.todo", "LocalToDo")
            version = 7
        return (module, name)


class LocalManager( Manager ):
    """Root class for domain data structure."""

    ## 1 - renamed modules from 'todocalendar' to 'hanlendar'
    ## 2 - renamed modules from 'hanlendar.domainmodel.*' to 'hanlendar.domainmodel.local.*'
    ## 3 - renamed modules from 'hanlendar.domainmodel.local.item' to 'hanlendar.domainmodel.item'
    ## 4 - renamed modules from 'hanlendar.domainmodel.local.recurrent' to 'hanlendar.domainmodel.recurrent'
    ##     renamed modules from 'hanlendar.domainmodel.local.reminder' to 'hanlendar.domainmodel.reminder'
    ## 5 - renamed class from 'hanlendar.domainmodel.local.task.Task' to 'hanlendar.domainmodel.local.task.LocalTask'
    ## 6 - moved data to 'local' subdirectory
    ## 7 - renamed class from 'hanlendar.domainmodel.local.todo.ToDo' to 'hanlendar.domainmodel.local.todo.LocalToDo'
    _class_version = 7

    def __init__(self, ioDir=None):
        """Constructor."""
        self._tasks = list()
        self._todos = list()
        self.notes = { "notes": "" }        ## default notes

        self._ioDir = ioDir                 ## do not persist

    def store( self, outputDir ):
        self._ioDir = outputDir
        self.storeData()

    # override
    def storeData( self ):
        if self._ioDir is None:
            _LOGGER.warning( "unable to store data -- no root directory given" )
            return

        outputDir = self._ioDir

        changed = False

        outputFile = os.path.join( outputDir, "version.obj" )
        if persist.store_object( self._class_version, outputFile ) is True:
            changed = True

        outputFile = os.path.join( outputDir, "tasks.obj" )
        if persist.store_object( self.tasks, outputFile ) is True:
            changed = True

        outputFile = os.path.join( outputDir, "todos.obj" )
        if persist.store_object( self.todos, outputFile ) is True:
            changed = True

        outputFile = os.path.join( outputDir, "notes.obj" )
        if persist.store_object( self.notes, outputFile ) is True:
            changed = True

        ## backup data
        objFiles = glob.glob( outputDir + "/*.obj" )
        storedZipFile = os.path.join( outputDir, "data.zip" )
        persist.backup_files( objFiles, storedZipFile )

        return changed

    def load( self, inputDir ):
        self._ioDir = inputDir
        self.loadData()

    # override
    def loadData( self ):
        if self._ioDir is None:
            _LOGGER.warning( "unable to load data -- no root directory given" )
            return

        inputDir = self._ioDir

        inputFile = os.path.join( inputDir, "version.obj" )
        mngrVersion = persist.load_object( inputFile )
        if mngrVersion != self. _class_version:
            _LOGGER.info( "converting object from version %s to %s", mngrVersion, self._class_version )
            ## do nothing for now

        mapperObject = ModuleMapper( mngrVersion )

        inputFile = os.path.join( inputDir, "tasks.obj" )
        self.tasks = persist.load_object( inputFile, class_mapper=mapperObject )
        if self.tasks is None:
            self.tasks = list()

        inputFile = os.path.join( inputDir, "todos.obj" )
        self.todos = persist.load_object( inputFile, class_mapper=mapperObject )
        if self.todos is None:
            self.todos = list()

        inputFile = os.path.join( inputDir, "notes.obj" )
        self.notes = persist.load_object( inputFile, class_mapper=mapperObject )
        if self.notes is None:
            self.notes = { "notes": "" }

        self.fixData()

    ## index meaning:
    ##    negative: current
    ##           0: first history entry
    ##    positive: history entry by index
    def loadHistory( self, index=-1 ):
        if index < 0:
            self.loadData()
            ret_dict = { 'file': None,
                         'version': self. _class_version,
                         'tasks': self.tasks,
                         'todos': self.todos,
                         'notes': self.notes
                         }
            return ret_dict

        outputDir = self._ioDir
        if index <= 0:
            storedZipFile = os.path.join( outputDir, "data.zip" )
        else:
            storedZipFile = os.path.join( outputDir, "data.zip.%s" % index )

        hist_data_raw = persist.load_backup( storedZipFile )

        version_raw = hist_data_raw.get( "version.obj", None )
        mngrVersion = persist.load_data( version_raw )
        if mngrVersion != self. _class_version:
            _LOGGER.info( "converting object from version %s to %s", mngrVersion, self._class_version )
            ## do nothing for now

        mapperObject = ModuleMapper( mngrVersion )

        tasks_raw = hist_data_raw.get( "tasks.obj", None )
        tasks = persist.load_data( tasks_raw, class_mapper=mapperObject )
        if tasks is None:
            tasks = list()

        todos_raw = hist_data_raw.get( "todos.obj", None )
        todos = persist.load_data( todos_raw, class_mapper=mapperObject )
        if todos is None:
            todos = list()

        notes_raw = hist_data_raw.get( "notes.obj", None )
        notes = persist.load_data( notes_raw, class_mapper=mapperObject )
        if notes is None:
            notes = list()

        ret_dict = { 'file': storedZipFile,
                     'version': mngrVersion,
                     'tasks': tasks,
                     'todos': todos,
                     'notes': notes
                     }
        return ret_dict

    def restoreTaskByTitle( self, history_index, task_title ):
        data_dict = self.loadHistory( 160 )
        tasks: List[ Task ] = data_dict.get( 'tasks', [] )
        found_task = self.findTaskByTitle( tasks, task_title )
        if found_task is not None:
            self.addTask( found_task )
            return True
        return False

    def findTaskByTitle( self, tasks_list, title ):
        flat_set = set( Item.getAllSubItemsFromList( tasks_list ) )
        for task in flat_set:
            task_title = task.getTitle()
            if task_title == title:
                return task
        return None

    ## ======================================================================

    # override
    def _getTasks( self ):
        return self._tasks

    # override
    def _setTasks( self, value ):
        self._tasks = value

    # override
    def getTasksAll(self):
        return Item.getAllSubItemsFromList( self.tasks )

    # override
    def createEmptyTask(self):
        return LocalTask()

    # override
    def _getToDos( self ):
        return self._todos

    # override
    def _setToDos( self, value ):
        self._todos = value

    # override
    def getTodosAll(self):
        return Item.getAllSubItemsFromList( self.todos )

    # override
    def createEmptyToDo(self) -> LocalToDo:
        return LocalToDo()

    # override
    def _getNotes(self):
        return self.notes

    # override
    def _setNotes(self, value):
        self.notes = value
