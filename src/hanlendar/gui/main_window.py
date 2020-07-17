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

from .dataobject import DataObject
from .navcalendar import NavCalendarHighlightModel
from .tasktable import getRemindedColor, getTimeoutColor
from .settingsdialog import SettingsDialog, AppSettings
from .notifytimer import NotificationTimer

from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.todo import ToDo


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


class DataHighlightModel( NavCalendarHighlightModel ):

    def __init__(self, manager ):
        self.manager = manager

    def isHighlighted(self, date: QDate):
        entryDate = date.toPyDate()
        return self.manager.hasTaskOccurrences( entryDate )


class MainWindow( QtBaseClass ):           # type: ignore

    logger: logging.Logger = None
    toolTip = "Hanlendar"

    def __init__(self):
        super().__init__()
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.data = DataObject( self )
        self.appSettings = AppSettings()

        self.trayIcon = tray_icon.TrayIcon(self)
        self.updateTrayToolTip()

        self.notifsTimer = NotificationTimer( self )

        self.ui.navcalendar.highlightModel = DataHighlightModel( self.data.getManager() )

        self.setDayViewDate()

        ## === connecting signals ===

        self.data.taskChanged.connect( self._handleTasksChange )
        self.data.todoChanged.connect( self._handleToDosChange )

        self.notifsTimer.remindTask.connect( self.handleNotification )

        self.ui.navcalendar.addTask.connect( self.data.addNewTask )
        self.ui.navcalendar.currentPageChanged.connect( self.ui.monthCalendar.setCurrentPage )
        self.ui.navcalendar.selectionChanged.connect( self.setDayViewDate )

        self.ui.tasksTable.connectData( self.data )
        self.ui.tasksTable.selectedTask.connect( self.showDetails )
        self.ui.tasksTable.taskUnselected.connect( self.hideDetails )
        self.ui.showCompletedTasksListCB.toggled.connect( self.ui.tasksTable.showCompletedTasks )

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
        self.ui.showCompletedToDosCB.toggled.connect( self.ui.todosTable.showCompletedToDos )

        self.ui.notesWidget.notesChanged.connect( self.saveData )

        ## === main menu settings ===

        self.ui.actionSave_data.triggered.connect( self.saveData )
        self.ui.actionImportNotes.triggered.connect( self.importXfceNotes )

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

    def saveData(self):
        self._saveData()
        self.setStatusMessage( "Data saved", [ "Data saved +", "Data saved =" ], 6000 )

    def _saveData(self):
        ## having separate slot allows to monkey patch / mock "_saveData()" method
        _LOGGER.info( "storing data" )
        dataPath = self.getDataPath()
        notes = self.ui.notesWidget.getNotes()
        self.data.getManager().setNotes( notes )
        self.data.store( dataPath )

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
        _LOGGER.warn( "unsupported entity: %s", entity )
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
        self.updateTasksView()

    ## ====================================================================

    def _handleTasksChange(self):
        self.saveData()
        self.refreshTasksView()

    def refreshTasksView(self):
        self.updateNotificationTimer()
        self.updateTasksView()
        self.ui.dayList.updateView()
        self.ui.navcalendar.repaint()
        self.updateTrayToolTip()

    def updateTasksView(self):
        self.ui.tasksTable.updateView()
        #self.ui.dayList.updateView()
        self.ui.monthCalendar.updateCells()
        self._updateTrayIndicator()

    ## ====================================================================

    def setDayViewDate(self):
        calendarDate = self.ui.navcalendar.selectedDate()
        self.ui.dayList.setCurrentDate( calendarDate )

    ## ====================================================================

    def _handleToDosChange(self):
        self.saveData()
        self.ui.todosTable.updateView()
        self.updateTrayToolTip()

    ## ====================================================================

    def updateNotesView(self):
        notesDict = self.data.getManager().getNotes()
        self.ui.notesWidget.setNotes( notesDict )

    def importXfceNotes(self):
        retButton = QMessageBox.question(self, "Import Notes", "Do you want to import Xfce Notes (previous notes will be lost)?")
        if retButton == QMessageBox.Yes:
            self.data.getManager().importXfceNotes()
            self.updateNotesView()

    ## ====================================================================

    def updateTrayToolTip(self):
        toolTip = ""
        deadlineTask = self.data.getManager().getNextDeadline()
        if deadlineTask is not None:
            toolTip += "\n" + "Next deadline: " + deadlineTask.title
        nextToDo = self.data.getManager().getNextToDo()
        if nextToDo is not None:
            toolTip += "\n" + "Next ToDo: " + nextToDo.title
        if len(toolTip) > 0:
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
        deadlinedTasks = self.data.getManager().getDeadlinedTasks()
        num = len(deadlinedTasks)
        if num > 0:
            color = getTimeoutColor()
            self.trayIcon.drawNumber( num, color )
            return
        remindedTasks = self.data.getManager().getRemindedTasks()
        num = len(remindedTasks)
        if num > 0:
            color = getRemindedColor()
            self.trayIcon.drawNumber( num, color )
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

    ## slot
    def closeApplication(self):
        ##self.close()
        qApp.quit()

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
