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

from . import uiloader
from . import resources

from .qt import qApp, QtCore, QIcon
from .qt import QWidget, QSplitter, QTabWidget
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog

from .navcalendar import NavCalendarHighlightModel
from .taskdialog import TaskDialog
from .eventdialog import EventDialog

from todocalendar.domainmodel.manager import Manager
from todocalendar.domainmodel.task import Task
from todocalendar.domainmodel.event import Event


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


class DataHighlightModel( NavCalendarHighlightModel ):

    def __init__(self, manager ):
        self.manager = manager

    def isHighlighted(self, date: QDate):
        entryDate = date.toPyDate()
        return self.manager.hasEntries( entryDate )


class MainWindow( QtBaseClass ):           # type: ignore

    logger: logging.Logger = None

    def __init__(self):
        super().__init__()
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.domainModel = Manager()

        self.settingsFilePath = None

        iconPath = resources.getImagePath( "calendar-white.png" )
        appIcon = QIcon( iconPath )
        self.setWindowIcon( appIcon )

        self.ui.navcalendar.highlightModel = DataHighlightModel( self.domainModel )

        self.ui.navcalendar.selectionChanged.connect( self.updateTasksView )
        self.ui.navcalendar.addTask.connect( self.addNewTask )
        self.ui.navcalendar.addEvent.connect( self.addNewEvent )

        #self.statusBar().showMessage("Ready")

    def getManager(self):
        return self.domainModel

    def reloadData(self):
        self.updateTasksView()

    def loadSettings(self):
        settings = self.getSettings()
        self.logger.debug( "loading app state from %s", settings.fileName() )
        #self.ui.appSettings.loadSettings( settings )

        ## restore widget state and geometry
        settings.beginGroup( self.objectName() )
        geometry = settings.value("geometry")
        state = settings.value("windowState")
        if geometry is not None:
            self.restoreGeometry( geometry )
        if state is not None:
            self.restoreState( state )
        settings.endGroup()

        ## store geometry of all widgets
        widgets = self.findChildren(QWidget)
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            geometry = settings.value("geometry")
            if geometry is not None:
                w.restoreGeometry( geometry )
            settings.endGroup()

        widgets = self.findChildren(QSplitter)
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            state = settings.value("widgetState")
            if state is not None:
                w.restoreState( state )
            settings.endGroup()

        widgets = self.findChildren(QTabWidget)
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            state = settings.value("currentIndex")
            if state is not None:
                currIndex = int(state)
                w.setCurrentIndex( currIndex )
            settings.endGroup()

    def saveSettings(self):
        settings = self.getSettings()
        self.logger.debug( "saving app state to %s", settings.fileName() )
#         self.ui.appSettings.saveSettings( settings )

        ## store widget state and geometry
        settings.beginGroup( self.objectName() )
        settings.setValue("geometry", self.saveGeometry() )
        settings.setValue("windowState", self.saveState() )
        settings.endGroup()

        ## store geometry of all widgets
        widgets = self.findChildren(QWidget)
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            settings.setValue("geometry", w.saveGeometry() )
            settings.endGroup()

        widgets = self.findChildren(QSplitter)
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            settings.setValue("widgetState", w.saveState() )
            settings.endGroup()

        widgets = self.findChildren(QTabWidget)
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            settings.setValue("currentIndex", w.currentIndex() )
            settings.endGroup()

        ## force save to file
        settings.sync()

    def getSettings(self):
#         ## store in app directory
#         if self.settingsFilePath is None:
# #             scriptDir = os.path.dirname(os.path.realpath(__file__))
# #             self.settingsFilePath = os.path.realpath( scriptDir + "../../../../tmp/settings.ini" )
#             self.settingsFilePath = "settings.ini"
#         settings = QtCore.QSettings(self.settingsFilePath, QtCore.QSettings.IniFormat, self)

        ## store in home directory
        orgName = qApp.organizationName()
        appName = qApp.applicationName()
        settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, orgName, appName, self)
        return settings

    ## ===============================================================

    def addNewTask( self, date: QDate ):
        task = Task()
        startDate = date.toPyDate()
        task.setDefaultDate( startDate )

        taskDialog = TaskDialog( task, self )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.addTask( taskDialog.task )
        self.updateTasksView()

    def addNewEvent( self, date: QDate ):
        event = Event()
        startDate = date.toPyDate()
        event.setDefaultDate( startDate )

        eventDialog = EventDialog( event, self )
        eventDialog.setModal( True )
        dialogCode = eventDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.addEvent( eventDialog.event )
        self.updateTasksView()

    def updateTasksView(self):
        selectedDate: QDate = self.ui.navcalendar.selectedDate()
        _LOGGER.debug( "navcalendar selection changed: %s", selectedDate )
        self.updateTasksTable()

    def updateTasksTable(self):
        self.ui.tasksTable.clear()
        tasksList = self.domainModel.getTasks()
        self.ui.tasksTable.setTasks( tasksList )


MainWindow.logger = _LOGGER.getChild(MainWindow.__name__)


def getWidgetKey(widget):
    if widget is None:
        return None
    retKey = widget.objectName()
    widget = widget.parent()
    while widget is not None:
        retKey = widget.objectName() + "-" + retKey
        widget = widget.parent()
    return retKey

