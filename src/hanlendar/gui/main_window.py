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

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtWidgets import QFileDialog

from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.local.reminder import Notification
from hanlendar.domainmodel.local.todo import ToDo
from hanlendar.domainmodel.local.manager import Manager

from hanlendar.fswatchdog import FSWatcher
from hanlendar.fqueue import queue_path, get_from_queue

from . import uiloader
from . import resources
from . import tray_icon
from . import guistate

from .qt import qApp, QtCore, QtGui, QIcon

from .dataobject import DataObject
from .notifytimer import NotificationTimer
from .widget.settingsdialog import SettingsDialog, AppSettings
from .widget.navcalendar import NavCalendarHighlightModel
from .widget.tasktable import get_reminded_color, get_timeout_color


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class DataHighlightModel( NavCalendarHighlightModel ):

    def __init__(self, manager: Manager ):
        super().__init__()
        self.manager: Manager = manager

    def isHighlighted(self, date: QDate):
        entryDate = date.toPyDate()
        occurrencesList = self.manager.getTaskOccurrencesForDate( entryDate, False )
        return len(occurrencesList) > 0

    def isOccupied(self, date: QDate):
        entryDate = date.toPyDate()
        occurrencesList = self.manager.getTaskOccurrencesForDate( entryDate, True )
        occurrencesList = [ task for task in occurrencesList if task.isCompleted() ]
        return len(occurrencesList) > 0


class MainWindow( QtBaseClass ):           # type: ignore

    logger: logging.Logger = None
    toolTip = "Hanlendar"

    def __init__(self):
        super().__init__()
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.data = DataObject( self )
        self.appSettings = AppSettings()
        
        self.messagesQueueWatchdog = FSWatcher()
        self.messagesQueueWatchdog.start( queue_path, self._handleNextMessage )

        ## =============================

        undoStack = self.data.undoStack

        undoAction = undoStack.createUndoAction( self, "&Undo" )
        undoAction.setShortcuts( QtGui.QKeySequence.Undo )
        redoAction = undoStack.createRedoAction( self, "&Redo" )
        redoAction.setShortcuts( QtGui.QKeySequence.Redo )

        self.ui.menuEdit.insertAction( self.ui.actionUndo, undoAction )
        self.ui.menuEdit.removeAction( self.ui.actionUndo )
        self.ui.menuEdit.insertAction( self.ui.actionRedo, redoAction )
        self.ui.menuEdit.removeAction( self.ui.actionRedo )

        ## =============================

        self.trayIcon = tray_icon.TrayIcon(self)
        self.updateTrayToolTip()

        self.notifsTimer = NotificationTimer( self )

        self.ui.navcalendar.highlightModel = DataHighlightModel( self.data.getManager() )

        self.setDayViewDate()

        ## === connecting signals ===

        self.data.tasksChanged.connect( self._handleTasksChange )
        self.data.todosChanged.connect( self._handleToDosChange )
        self.data.notesChanged.connect( self._handleNotesChange )

        self.notifsTimer.remindTask.connect( self.handleNotification )

        self.ui.navcalendar.addTask.connect( self.data.addNewTask )
        self.ui.navcalendar.currentPageChanged.connect( self.ui.monthCalendar.setCurrentPage )
        self.ui.navcalendar.selectionChanged.connect( self.setDayViewDate )

        self.ui.tasksTable.connectData( self.data )
        self.ui.tasksTable.selectedTask.connect( self.showDetails )
        self.ui.tasksTable.taskUnselected.connect( self.hideDetails )
        self.ui.showCompletedTasksListCB.toggled.connect( self.ui.tasksTable.showCompletedItems )
        self.ui.expandAllTasksCB.toggled.connect( self.ui.tasksTable.expandAllItems )

        self.ui.dayList.connectData( self.data )
        self.ui.dayList.selectedTask.connect( self.showDetails )
        self.ui.dayList.taskUnselected.connect( self.hideDetails )
        self.ui.showCompletedTasksDayCB.toggled.connect( self.ui.dayList.showCompletedTasks )

        self.ui.monthCalendar.connectData( self.data )
        self.ui.monthCalendar.selectedTask.connect( self.showDetails )
        self.ui.monthCalendar.taskUnselected.connect( self.hideDetails )
        self.ui.showCompletedTasksMonthCB.toggled.connect( self.ui.monthCalendar.showCompletedTasks )

        self.ui.todosTable.connectData( self.data )
        self.ui.todosTable.selectedToDo.connect( self.showDetails )
        self.ui.todosTable.todoUnselected.connect( self.hideDetails )
        self.ui.showCompletedToDosCB.toggled.connect( self.ui.todosTable.showCompletedItems )

        self.ui.notesWidget.addNote.connect( self.data.addNote )
        self.ui.notesWidget.renameNote.connect( self.data.renameNote )
        self.ui.notesWidget.removeNote.connect( self.data.removeNote )
        self.ui.notesWidget.notesChanged.connect( self.triggerSaveTimer )
        self.ui.notesWidget.createToDo.connect( self.data.addNewToDo )

        ## === main menu settings ===

        self.ui.actionSave_data.triggered.connect( self.saveData )
        self.ui.actionImportNotes.triggered.connect( self.importXfceNotes )
        self.ui.actionImport_iCalendar.triggered.connect( self.importICalendar )

        self.ui.actionOptions.triggered.connect( self.openSettingsDialog )

        self.applySettings()
        self.trayIcon.show()

        self.statusBar().showMessage("Ready", 10000)

    def getManager(self):
        return self.data.getManager()

    def loadData(self):
        dataPath = self.getDataPath()
        self.data.load( dataPath )
        self.refreshView()

    def triggerSaveTimer(self):
        timeout = 30000
        _LOGGER.info("triggering save timer with timeout %s", timeout)
        QtCore.QTimer.singleShot( timeout, self.saveData )

    def saveData(self):
        if self._saveData():
            self.setStatusMessage( "Data saved", [ "Data saved +", "Data saved =" ], 6000 )
        else:
            self.setStatusMessage( "Nothing to save", [ "Nothing to save +", "Nothing to save =" ], 6000 )

    # pylint: disable=E0202
    def _saveData(self):
        ## having separate slot allows to monkey patch / mock "_saveData()" method
        _LOGGER.info( "storing data" )
        dataPath = self.getDataPath()
        notes = self.ui.notesWidget.getNotes()
        self.data.getManager().setNotes( notes )
        return self.data.store( dataPath )

    def disableSaving(self):
        def save_data_mock():
            _LOGGER.info("saving data is disabled")
        _LOGGER.info("disabling saving data")
        self._saveData = save_data_mock           # type: ignore

    def getDataPath(self):
        settings = self.getSettings()
        settingsDir = settings.fileName()
        settingsDir = settingsDir[0:-4]       ## remove extension
        settingsDir += "-data"
        return settingsDir

    ## ===============================================================

    def refreshView(self):
        self.refreshTasksView()
        self.ui.todosTable.updateView()
        self.updateNotesView()
        self.showDetails( None )

    def showDetails(self, entity):
        if entity is None:
            self.hideDetails()
            return
        if isinstance(entity, Task):
            self.ui.taskDetails.setTask( entity )
            self.ui.entityDetailsStack.setCurrentIndex( 1 )
            return
        if isinstance(entity, ToDo):
            self.ui.todoDetails.setToDo( entity )
            self.ui.entityDetailsStack.setCurrentIndex( 2 )
            return
        # unknown entity
        _LOGGER.warning( "unsupported entity: %s", entity )
        self.hideDetails()

    def hideDetails(self):
        self.ui.entityDetailsStack.setCurrentIndex( 0 )

    def setStatusMessage(self, firstStatus, changeStatus: list, timeout):
        statusBar = self.statusBar()
        message = statusBar.currentMessage()
        if message == firstStatus:
            statusBar.showMessage( changeStatus[0], timeout )
            return
        try:
            currIndex = changeStatus.index( message )
            nextIndex = ( currIndex + 1 ) % len(changeStatus)
            statusBar.showMessage( changeStatus[nextIndex], timeout )
        except ValueError:
            statusBar.showMessage( firstStatus, timeout )

    ## ====================================================================

    def updateNotificationTimer(self):
        notifs = self.data.getManager().getNotificationList()
        self.notifsTimer.setNotifications( notifs )

    def handleNotification( self, notification: Notification ):
        self.trayIcon.displayMessage( notification.message )
        self.updateTasksView( notification.task )
        self.ui.todosTable.updateView()

    ## ====================================================================

    def _handleTasksChange(self):
        self.triggerSaveTimer()
        self.refreshTasksView()

    def refreshTasksView(self):
        self.updateNotificationTimer()
        self.updateTasksView()
        self.ui.dayList.updateView()
        self.ui.navcalendar.repaint()
        self.updateTrayToolTip()

    def updateTasksView(self, updatedTask: Task=None ):
        self.ui.tasksTable.updateView( updatedTask )
        #self.ui.dayList.updateView()
        self.ui.monthCalendar.updateCells()
        self._updateTrayIndicator()

    ## ====================================================================

    def setDayViewDate(self):
        calendarDate = self.ui.navcalendar.selectedDate()
        self.ui.dayList.setCurrentDate( calendarDate )

    ## ====================================================================

    def _handleToDosChange(self):
        self.triggerSaveTimer()
        self.ui.todosTable.updateView()
        self.updateTrayToolTip()

    ## ====================================================================

    def _handleNotesChange(self):
        self.triggerSaveTimer()
        self.updateNotesView()

    def updateNotesView(self):
        notesDict = self.data.getManager().getNotes()
        self.ui.notesWidget.setNotes( notesDict )

    def importXfceNotes(self):
        retButton = QMessageBox.question( self, "Import Notes",
                                          "Do you want to import Xfce Notes (previous notes will be lost)?")
        if retButton == QMessageBox.Yes:
            self.data.importXfceNotes()

    def importICalendar(self):
        fielDialog = QFileDialog( self )
        fielDialog.setFileMode( QFileDialog.ExistingFile )
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        self.data.importICalendar( selectedFile )
        
    def _handleNextMessage(self):
        with self.messagesQueueWatchdog.ignoreEvents():
            message = get_from_queue( True )

        if message is None:
            _LOGGER.warning( "received None message" )
            return
        
        message_type, message_value = message
        if message_type == "file":
            self.data.importICalendar( message_value, silent=True )
            return

        _LOGGER.warning( "unknown message: %s", message )

    ## ====================================================================

    def updateTrayToolTip(self):
        toolTip = ""
        deadlineTask = self.data.getManager().getNextDeadline()
        if deadlineTask is not None:
            toolTip += "\n" + "Next deadline: " + deadlineTask.title
        nextToDo = self.data.getManager().getNextToDo()
        if nextToDo is not None:
            toolTip += "\n" + "Next ToDo: " + nextToDo.title
        if toolTip:
            # not empty
            toolTip = self.toolTip + "\n" + toolTip
        else:
            toolTip = self.toolTip
        self.trayIcon.setToolTip( toolTip )

    def setIconTheme(self, theme: tray_icon.TrayIconTheme):
        _LOGGER.debug("setting tray theme: %r", theme)
        self._setTrayIndicator( theme )

    def _updateTrayIndicator(self):
        self._setTrayIndicator( self.appSettings.trayIcon )              ## required to clear old number

    def _setTrayIndicator(self, theme: tray_icon.TrayIconTheme):
        self._updateIconTheme( theme )                                  ## required to clear old number
        deadlinedTasks  = self.data.getManager().getDeadlinedTasks()
        remindedTasks   = self.data.getManager().getRemindedTasks()
        indicationTasks = set( deadlinedTasks + remindedTasks )
        indicationSum = len(indicationTasks)
        num = len(deadlinedTasks)
        if num > 0:
            color = get_timeout_color()
            self.trayIcon.drawNumber( indicationSum, color )
            return
        num = len(remindedTasks)
        if num > 0:
            color = get_reminded_color()
            self.trayIcon.drawNumber( indicationSum, color )
            return

    def _updateIconTheme(self, theme: tray_icon.TrayIconTheme):
        fileName = theme.value
        iconPath = resources.get_image_path( fileName )
        appIcon = QIcon( iconPath )

        self.setWindowIcon( appIcon )
        self.trayIcon.setIcon( appIcon )

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        _LOGGER.info("received close event, saving session: %s", qApp.isSavingSession() )
        if qApp.isSavingSession():
            ## closing application due to system shutdown
            self.saveAll()
            return
        ## windows close requested by user -- hide the window
        event.ignore()
        self.hide()
        self.trayIcon.show()

    def showEvent(self, _):
        self.trayIcon.updateLabel()

    def hideEvent(self, _):
        self.trayIcon.updateLabel()

    ## ====================================================================

    ## slot
    # pylint: disable=R0201
    def closeApplication(self):
        ##self.close()
        qApp.quit()

    def saveAll(self):
        _LOGGER.info("saving application state")
        self.saveSettings()
        self.saveData()

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

        ## restore widget state and geometry
        guistate.load_state( self, settings )

    def saveSettings(self):
        settings = self.getSettings()
        self.logger.debug( "saving app state to %s", settings.fileName() )

        self.appSettings.saveSettings( settings )

        ## store widget state and geometry
        settings.beginGroup( self.objectName() )
        settings.setValue("geometry", self.saveGeometry() )
        settings.setValue("windowState", self.saveState() )
        settings.endGroup()

        ## store widget state and geometry
        guistate.save_state(self, settings)

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


def get_widget_key(widget):
    if widget is None:
        return None
    retKey = widget.objectName()
    widget = widget.parent()
    while widget is not None:
        retKey = widget.objectName() + "-" + retKey
        widget = widget.parent()
    return retKey
