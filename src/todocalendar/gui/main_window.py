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
from . import tray_icon

from .qt import qApp, QtCore, QIcon
from .qt import QWidget, QSplitter, QTabWidget
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QDialog, QMessageBox

from .navcalendar import NavCalendarHighlightModel
from .taskdialog import TaskDialog
from .settingsdialog import SettingsDialog
from .settingsdialog import AppSettings
from .notifytimer import NotificationTimer

from todocalendar.domainmodel.manager import Manager
from todocalendar.domainmodel.task import Task
from todocalendar.domainmodel.reminder import Notification


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
        self.appSettings = AppSettings()

        self.trayIcon = tray_icon.TrayIcon(self)
        self.updateTrayToolTip()

        self.notifsTimer = NotificationTimer( self )

        self.ui.navcalendar.highlightModel = DataHighlightModel( self.domainModel )

#         self.ui.navcalendar.selectionChanged.connect( self.updateTasksView )
        self.ui.navcalendar.addTask.connect( self.addNewTask )

        self.ui.tasksTable.selectedTask.connect( self.tasksTableSelectionChanged )
        self.ui.tasksTable.addNewTask.connect( self.addNewTask )
        self.ui.tasksTable.editTask.connect( self.editTask )
        self.ui.tasksTable.removeTask.connect( self.removeTask )
        self.ui.tasksTable.markCompleted.connect( self.markTaskCompleted )

        self.ui.actionOptions.triggered.connect( self.openSettingsDialog )

        self.ui.showCompletedCB.toggled.connect( self.showCompletedTasks )

        self.notifsTimer.remindTask.connect( self.showTaskNotification )

        self.ui.actionSave_data.triggered.connect( self.saveData )
        self.ui.actionImportNotes.triggered.connect( self.importXfceNotes )

        self.applySettings()
        self.trayIcon.show()

        #self.statusBar().showMessage("Ready")

    def getManager(self):
        return self.domainModel

    def refreshView(self):
        self.updateNotificationTimer()
        self.updateTasksView()
        self.updateTrayToolTip()
        self._updateTasksTrayIndicator()
        self.updateNotesView()
        self.setDetails( None )

    ## ===============================================================

    def loadData(self):
        dataPath = self.getDataPath()
        self.domainModel.load( dataPath )
        self.refreshView()

    def saveData(self):
        dataPath = self.getDataPath()
        notes = self.ui.notesWidget.getNotes()
        self.domainModel.setNotes( notes )
        self.domainModel.store( dataPath )

    def getDataPath(self):
        settings = self.getSettings()
        settingsDir = settings.fileName()
        settingsDir = settingsDir[0:-4]       ## remove extension
        settingsDir += "-data"
        return settingsDir

    ## ===============================================================

    def addNewTask( self, date: QDate = None ):
        task = Task()
        if date is not None:
            startDate = date.toPyDate()
            task.setDefaultDate( startDate )

        taskDialog = TaskDialog( task, self )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.addTask( taskDialog.task )
        self._handleTasksChange()

    def editTask(self, task: Task ):
        taskDialog = TaskDialog( task, self )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.replaceTask( task, taskDialog.task )
        self._handleTasksChange()

    def removeTask(self, task: Task ):
        self.domainModel.removeTask( task )
        self._handleTasksChange()

    def markTaskCompleted(self, task: Task ):
        task.setCompleted()
        self._handleTasksChange()

    def updateTasksView(self):
        selectedDate: QDate = self.ui.navcalendar.selectedDate()
        _LOGGER.debug( "navcalendar selection changed: %s", selectedDate )
        self.updateTasksTable()

    def updateTasksTable(self):
        tasksList = self.domainModel.getTasks()
        self.ui.tasksTable.setTasks( tasksList )

    def setDetails(self, entity):
        if isinstance(entity, Task):
            self.ui.taskDetails.setTask( entity )
            self.ui.entityDetailsStack.setCurrentIndex( 1 )
            return
        # unknown entity
        self.ui.entityDetailsStack.setCurrentIndex( 0 )

    def tasksTableSelectionChanged(self, taskIndex):
        selectedTask = self.ui.tasksTable.getTask( taskIndex )
        self.setDetails( selectedTask )

    def showCompletedTasks(self, checked):
        self.ui.tasksTable.showCompletedTasks( checked )
        self.updateTasksTable()

    def updateNotificationTimer(self):
        notifs = self.domainModel.getNotificationList()
        self.notifsTimer.setNotifications( notifs )

    def showTaskNotification( self, notification: Notification ):
        self.trayIcon.displayMessage( notification.message )
        self.updateTasksTable()
        self._updateTasksTrayIndicator()

    def updateTrayToolTip(self):
        deadlineTask = self.domainModel.getNextDeadline()
        toolTip = "ToDo Calendar"
        if deadlineTask is not None:
            toolTip += "\n" + "Next deadline: " + deadlineTask.title
        self.trayIcon.setToolTip( toolTip )

    def _handleTasksChange(self):
        self.updateNotificationTimer()
        self.updateTasksTable()
        self.ui.navcalendar.repaint()
        self.updateTrayToolTip()
        self._updateTasksTrayIndicator()

    ## ====================================================================

    def updateNotesView(self):
        notesDict = self.domainModel.getNotes()
        self.ui.notesWidget.setNotes( notesDict )

    def importXfceNotes(self):
        retButton = QMessageBox.question(self, "Import Notes", "Do you want to import Xfce Notes (previous notes will be lost)?")
        if retButton == QMessageBox.Yes:
            self.domainModel.importXfceNotes()
            self.updateNotesView()

    ## ====================================================================

    ## slot
    def closeApplication(self):
        ##self.close()
        qApp.quit()

    ## ====================================================================

    def setIconTheme(self, theme: tray_icon.TrayIconTheme):
        _LOGGER.debug("setting tray theme: %r", theme)
        self._updateIconTheme( theme )
        self._setTasksTrayIndicator( theme )

    def _updateTasksTrayIndicator(self):
        self._setTasksTrayIndicator( self.appSettings.trayIcon )              ## required to clear old number

    def _setTasksTrayIndicator(self, theme: tray_icon.TrayIconTheme):
        self._updateIconTheme( theme )                                  ## required to clear old number
        deadlinedTasks = self.domainModel.getDeadlinedTasks()
        num = len(deadlinedTasks)
        if num > 0:
            self.trayIcon.drawNumber( num, "red" )
            return
        remindedTasks = self.domainModel.getRemindedTasks()
        num = len(remindedTasks)
        if num > 0:
            self.trayIcon.drawNumber( num, "orange" )
            return

    def _updateIconTheme(self, theme: tray_icon.TrayIconTheme):
        fileName = theme.value
        iconPath = resources.getImagePath( fileName )
        appIcon = QIcon( iconPath )

        self.setWindowIcon( appIcon )
        self.trayIcon.setIcon( appIcon )

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.trayIcon.show()

    def showEvent(self, event):
        self.trayIcon.updateLabel()

    def hideEvent(self, event):
        self.trayIcon.updateLabel()

    ## ====================================================================

    def openSettingsDialog(self):
        dialog = SettingsDialog( self.appSettings, self )
        dialog.setModal( True )
        dialog.iconThemeChanged.connect( self.setIconTheme )
        dialogCode = dialog.exec_()
        if dialogCode == QDialog.Rejected:
            self.applySettings()
            return
        self.appSettings = dialog.appSettings
        self.applySettings()

    def applySettings(self):
        self.setIconTheme( self.appSettings.trayIcon )

    def loadSettings(self):
        settings = self.getSettings()
        self.logger.debug( "loading app state from %s", settings.fileName() )

        self.appSettings.loadSettings( settings )
        self.applySettings()

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

        widgets = self.findChildren( QTableWidget )
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            colsNum = w.columnCount()
            for c in range(0, colsNum):
                state = settings.value( "column" + str(c) )
                if state is not None:
                    currWidth = int(state)
                    w.setColumnWidth( c, currWidth )
            sortColumn = settings.value( "sortColumn" )
            sortOrder = settings.value( "sortOrder" )
            if sortColumn is not None and sortOrder is not None:
                w.sortByColumn( int(sortColumn), int(sortOrder) )
            settings.endGroup()

    def saveSettings(self):
        settings = self.getSettings()
        self.logger.debug( "saving app state to %s", settings.fileName() )

        self.appSettings.saveSettings( settings )

        ## store widget state and geometry
        settings.beginGroup( self.objectName() )
        settings.setValue("geometry", self.saveGeometry() )
        settings.setValue("windowState", self.saveState() )
        settings.endGroup()

        ## store geometry of all widgets
        widgets = self.findChildren( QWidget )
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            settings.setValue("geometry", w.saveGeometry() )
            settings.endGroup()

        widgets = self.findChildren( QSplitter )
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            settings.setValue("widgetState", w.saveState() )
            settings.endGroup()

        widgets = self.findChildren( QTabWidget )
        for w in widgets:
            wKey = getWidgetKey(w)
            settings.beginGroup( wKey )
            settings.setValue("currentIndex", w.currentIndex() )
            settings.endGroup()

        widgets = self.findChildren( QTableWidget )
        for w in widgets:
            wKey = getWidgetKey(w)
            colsNum = w.columnCount()
            settings.beginGroup( wKey )
            for c in range(0, colsNum):
                settings.setValue( "column" + str(c), w.columnWidth(c) )
            header = w.horizontalHeader()
            sortColumn = header.sortIndicatorSection()
            settings.setValue( "sortColumn", sortColumn )
            sortOrder = header.sortIndicatorOrder()
            settings.setValue( "sortOrder", sortOrder )
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

