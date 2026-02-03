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

from PyQt5.QtCore import QDate
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtWidgets import QFileDialog

from hanlendar.fswatchdog import FSWatcher
from hanlendar.fqueue import queue_path, get_from_queue

from hanlendar.domainmodel.caldav.manager import CalDAVManager, CalDAVConnector
from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.local.todo import LocalToDo
from hanlendar.domainmodel.local.manager import LocalManager
from hanlendar.domainmodel.calendardata import CalendarData
from hanlendar.domainmodel.manager import Manager, MultiManager

from hanlendar.gui import uiloader
from hanlendar.gui import resources
from hanlendar.gui import tray_icon
from hanlendar.gui import guistate
from hanlendar.gui.qt import qApp, QtCore, QtGui, QIcon
from hanlendar.gui.dataobject import DataObject
from hanlendar.gui.notifytimer import NotificationTimer
from hanlendar.gui.widget.settingsdialog import SettingsDialog, AppSettings, CalendarItem
from hanlendar.gui.widget.navcalendar import NavCalendarHighlightModel
from hanlendar.gui.widget.tasktable import get_reminded_color, get_timeout_color
from hanlendar.gui.widget.settingsdialog import LocalCalendarItem, CalDAVCalendarItem


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


class DataHighlightModel(NavCalendarHighlightModel):

    def __init__(self, dataObject: DataObject):
        super().__init__()
        self.dataObject: DataObject = dataObject

    def isHighlighted(self, date: QDate):
        entryDate = date.toPyDate()
        manager: MultiManager = self.dataObject.getManager()
        occurrencesList = manager.getTaskOccurrencesForDate(entryDate, includeCompleted=False)
        return len(occurrencesList) > 0

    def isOccupied(self, date: QDate):
        entryDate = date.toPyDate()
        manager: MultiManager = self.dataObject.getManager()
        occurrencesList = manager.getTaskOccurrencesForDate(entryDate, includeCompleted=True)
        occurrencesList = [task for task in occurrencesList if task.isCompleted()]
        return len(occurrencesList) > 0


##
class SettingsObject(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.appSettings = AppSettings()
        self._data_custom_path = None

    def getAppSettings(self) -> AppSettings:
        return self.appSettings

    def getSettings(self) -> QtCore.QSettings:
        #         ## store in app directory
        #         if self.settingsFilePath is None:
        # #             scriptDir = os.path.dirname(os.path.realpath(__file__))
        # #             self.settingsFilePath = os.path.realpath( scriptDir + "../../../../tmp/settings.ini" )
        #             self.settingsFilePath = "settings.ini"
        #         settings = QtCore.QSettings(self.settingsFilePath, QtCore.QSettings.IniFormat, self)

        ## store in home directory
        orgName = qApp.organizationName()
        appName = qApp.applicationName()
        return QtCore.QSettings(
            QtCore.QSettings.IniFormat,  # type: ignore[attr-defined]
            QtCore.QSettings.UserScope,  # type: ignore[attr-defined]
            orgName,
            appName,
            self,
        )

    def getSettingsFilePath(self) -> str:
        settings = self.getSettings()
        return settings.fileName()

    def getDataPath(self):
        settings = self.getSettings()
        settingsDir = settings.fileName()
        settingsDir = settingsDir[0:-4]  ## remove extension
        settingsDir += "-data"
        return settingsDir

    def getLocalDataRootPath(self):
        if self._data_custom_path:
            return self._data_custom_path
        return self.getDataPath()

    def setLocalDataRootPath(self, custom_path):
        self._data_custom_path = custom_path

    def getLocalDataPath(self):
        dataPath = self.getLocalDataRootPath()
        dataPath = os.path.join(dataPath, "local")
        os.makedirs(dataPath, exist_ok=True)
        return dataPath

    def saveSettings(self):
        settings: QtCore.QSettings = self.getSettings()
        self.appSettings.saveSettings(settings)
        ## force save to file
        settings.sync()

    def loadSettings(self):
        settings: QtCore.QSettings = self.getSettings()
        self.appSettings.loadSettings(settings)

    ## ===================================================================

    def createLocalManager(self, calendar_id: str = None) -> LocalManager:
        dataPath = self.getLocalDataPath()
        if dataPath and calendar_id:
            dataPath = os.path.join(dataPath, calendar_id)
        local_man = LocalManager(dataPath)
        local_man.setCalendarId(calendar_id)
        return local_man

    def createCalDAVManager(self, connector: CalDAVConnector) -> CalDAVManager:
        dataPath = self.getLocalDataRootPath()
        dataPath = os.path.join(dataPath, "caldav")
        os.makedirs(dataPath, exist_ok=True)
        return CalDAVManager(connector, dataPath)

    def createCalDAVManagerFromData(self, serverURL, serverUser, serverPassword, calendarName) -> CalDAVManager:
        _LOGGER.info("connecting to CalDAV server: %s calendar: %s", serverURL, calendarName)
        connector = CalDAVConnector(serverURL, serverUser, serverPassword, calendarName)
        return self.createCalDAVManager(connector)

    def createCalDAVManagerFromCalendarItem(self, caldav_cal: CalDAVCalendarItem) -> CalDAVManager:
        _LOGGER.info("connecting to CalDAV server: %s calendar: %s", caldav_cal.serverURL, caldav_cal.calendarName)
        connector = CalDAVConnector(
            caldav_cal.serverURL,
            caldav_cal.serverUser,
            caldav_cal.serverPassword,
            caldav_cal.calendarName,
        )
        manager = self.createCalDAVManager(connector)
        calendar_id = caldav_cal.getCalendarId()
        manager.setCalendarId(calendar_id)
        return manager

    def createManager(self, calendar_item: CalendarItem) -> Manager:
        if isinstance(calendar_item, LocalCalendarItem):
            # local_cal: LocalCalendarItem = cal_item
            calendar_id = calendar_item.getCalendarId()
            local_man: LocalManager = self.createLocalManager(calendar_id)
            return local_man

        if isinstance(calendar_item, CalDAVCalendarItem):
            caldav_cal: CalDAVCalendarItem = calendar_item
            caldav_man: CalDAVManager = self.createCalDAVManagerFromCalendarItem(caldav_cal)
            return caldav_man

        _LOGGER.warning("unhandled calendar item: %s", calendar_item)
        return None

    def createManagersList(self) -> list[Manager]:
        manager_list: list[Manager] = []

        ## cal_item: CalendarItem
        for cal_item in self.appSettings.calendar_items:
            _LOGGER.info("adding manager: %s %s", cal_item.getCalendarMode(), cal_item.getCalendarName())
            manager: Manager = self.createManager(cal_item)
            if manager:
                manager_list.append(manager)

        return manager_list


##
class MainWindow(QtBaseClass):  # type: ignore[valid-type,misc]

    logger: logging.Logger = None
    toolTip = "Hanlendar"

    def __init__(self):
        super().__init__()
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.qtSettings = SettingsObject(self)

        self.data = DataObject(self)

        self.messagesQueueWatchdog = FSWatcher()
        self.messagesQueueWatchdog.start(queue_path, self._handleNextMessage)

        ## =============================

        undoStack = self.data.undoStack

        undoAction = undoStack.createUndoAction(self, "&Undo")
        undoAction.setShortcuts(QtGui.QKeySequence.Undo)
        redoAction = undoStack.createRedoAction(self, "&Redo")
        redoAction.setShortcuts(QtGui.QKeySequence.Redo)

        self.ui.menuEdit.insertAction(self.ui.actionUndo, undoAction)
        self.ui.menuEdit.removeAction(self.ui.actionUndo)
        self.ui.menuEdit.insertAction(self.ui.actionRedo, redoAction)
        self.ui.menuEdit.removeAction(self.ui.actionRedo)

        ## =============================

        self.trayIcon = tray_icon.TrayIcon(self)
        self.updateTrayToolTip()

        self.notifsTimer = NotificationTimer(self)

        self.ui.navcalendar.highlightModel = DataHighlightModel(self.data)

        self.setDayViewDate()

        ## === connecting signals ===

        self.data.tasksChanged.connect(self._handleTasksChange)
        self.data.todosChanged.connect(self._handleToDosChange)
        self.data.notesChanged.connect(self._handleNotesChange)

        self.notifsTimer.remindTask.connect(self.handleNotification)

        self.ui.navcalendar.addTask.connect(self.data.addNewTask)
        self.ui.navcalendar.currentPageChanged.connect(self.ui.monthCalendar.setCurrentPage)
        self.ui.navcalendar.selectionChanged.connect(self.setDayViewDate)

        self.ui.tasksTable.connectData(self.data)
        self.ui.tasksTable.selectedTask.connect(self.showDetails)
        self.ui.tasksTable.taskUnselected.connect(self.hideDetails)
        self.ui.showCompletedTasksListCB.toggled.connect(self.ui.tasksTable.showCompletedItems)
        self.ui.expandAllTasksCB.toggled.connect(self.ui.tasksTable.expandAllItems)

        self.ui.dayList.connectData(self.data)
        self.ui.dayList.selectedTask.connect(self.showDetails)
        self.ui.dayList.taskUnselected.connect(self.hideDetails)
        self.ui.showCompletedTasksDayCB.toggled.connect(self.ui.dayList.showCompletedTasks)

        self.ui.monthCalendar.connectData(self.data)
        self.ui.monthCalendar.selectedTask.connect(self.showDetails)
        self.ui.monthCalendar.taskUnselected.connect(self.hideDetails)
        self.ui.showCompletedTasksMonthCB.toggled.connect(self.ui.monthCalendar.showCompletedTasks)

        self.ui.todosTable.connectData(self.data)
        self.ui.todosTable.selectedToDo.connect(self.showDetails)
        self.ui.todosTable.todoUnselected.connect(self.hideDetails)
        self.ui.showCompletedToDosCB.toggled.connect(self.ui.todosTable.showCompletedItems)

        self.ui.notesWidget.addNote.connect(self.data.addNote)
        self.ui.notesWidget.renameNote.connect(self.data.renameNote)
        self.ui.notesWidget.removeNote.connect(self.data.removeNote)
        self.ui.notesWidget.notesChanged.connect(self.triggerSaveTimer)
        self.ui.notesWidget.createToDo.connect(self.data.addNewToDo)

        ## === main menu settings ===

        self.ui.actionSave_data.triggered.connect(self.saveData)
        self.ui.actionSync_calendars.triggered.connect(self.synchronize_calendars)
        self.ui.actionImportNotes.triggered.connect(self.importXfceNotes)
        self.ui.actionImport_iCalendar.triggered.connect(self.importICalendar)

        self.ui.actionOptions.triggered.connect(self.openSettingsDialog)

        self._updateIconTheme(tray_icon.TrayIconTheme.WHITE)  ## set default icon
        self.trayIcon.show()

        self.statusBar().showMessage("Ready", 10000)

    def setLocalDataRootPath(self, custom_path):
        self.qtSettings.setLocalDataRootPath(custom_path)

    def setCalDAVManager(self, caldav_address, caldav_user, caldav_pass, caldav_calendar):
        appSettings = self.qtSettings.getAppSettings()
        appSettings.calendar_items.clear()
        appSettings.addCalDAVCalendar(caldav_address, caldav_user, caldav_pass, caldav_calendar)

    def exportLocalToCalDAV(self, caldav_address, caldav_user, caldav_pass, caldav_calendar):
        _LOGGER.info("connecting to CalDAV server: %s calendar: %s", caldav_address, caldav_calendar)
        connector = CalDAVConnector(caldav_address, caldav_user, caldav_pass, caldav_calendar)
        self.exportLocalDB(connector)

    def exportLocalDB(self, connector: CalDAVConnector):
        manager: LocalManager = self.qtSettings.createLocalManager()
        caldavManager = self.qtSettings.createCalDAVManager(connector)
        caldavManager.setData(manager)
        caldavManager.saveToServer()

    def getManager(self) -> MultiManager:
        return self.data.getManager()

    def loadData(self):
        dataPath = self.qtSettings.getLocalDataPath()
        self.data.loadData(custom_path=dataPath)
        self.refreshView()

    def triggerSaveTimer(self):
        timeout = 30000
        _LOGGER.info("triggering save timer with timeout %s", timeout)
        QtCore.QTimer.singleShot(timeout, self.saveData)

    def saveData(self):
        if self._saveData():
            self.setStatusMessage("Data saved", ["Data saved +", "Data saved ="], 6000)
        else:
            self.setStatusMessage("Nothing to save", ["Nothing to save +", "Nothing to save ="], 6000)

    # pylint: disable=E0202
    def _saveData(self) -> bool:
        ## having separate slot allows to monkey patch / mock "_saveData()" method
        _LOGGER.info("storing data")
        notes = self.ui.notesWidget.getNotes()
        manager: MultiManager = self.data.getManager()
        manager.setNotes(notes)
        dataPath = self.qtSettings.getLocalDataPath()
        return self.data.storeData(custom_path=dataPath)

    def disableSaving(self):
        def save_data_mock():
            _LOGGER.info("saving data is disabled")

        _LOGGER.info("disabling saving data")
        self._saveData = save_data_mock  # type: ignore[method-assign]

    def synchronize_calendars(self):
        self.data.synchronize_data()
        self.refreshView()

    ## ===============================================================

    def refreshView(self):
        self.refreshTasksView()
        self.ui.todosTable.updateView()
        self.updateNotesView()
        self.showDetails(None)

    def showDetails(self, entity):
        if entity is None:
            self.hideDetails()
            return
        if isinstance(entity, Task):
            appSettings = self.qtSettings.getAppSettings()
            calendar_data = appSettings.getCalendarData()
            self.ui.taskDetails.setCalendarData(calendar_data)
            self.ui.taskDetails.setTask(entity)
            self.ui.taskDetails.setReadOnly(read_only=True)
            self.ui.entityDetailsStack.setCurrentIndex(1)
            return
        if isinstance(entity, LocalToDo):
            appSettings = self.qtSettings.getAppSettings()
            calendar_data = appSettings.getCalendarData()
            self.ui.todoDetails.setCalendarData(calendar_data)
            self.ui.todoDetails.setToDo(entity)
            self.ui.entityDetailsStack.setCurrentIndex(2)
            return
        # unknown entity
        _LOGGER.warning("unsupported entity: %s", entity)
        self.hideDetails()

    def hideDetails(self):
        self.ui.entityDetailsStack.setCurrentIndex(0)

    def setStatusMessage(self, firstStatus, changeStatus: list, timeout):
        statusBar = self.statusBar()
        message = statusBar.currentMessage()
        if message == firstStatus:
            statusBar.showMessage(changeStatus[0], timeout)
            return
        try:
            currIndex = changeStatus.index(message)
            nextIndex = (currIndex + 1) % len(changeStatus)
            statusBar.showMessage(changeStatus[nextIndex], timeout)
        except ValueError:
            statusBar.showMessage(firstStatus, timeout)

    ## ====================================================================

    def updateNotificationTimer(self):
        manager: MultiManager = self.data.getManager()
        notifs: list[Notification] = manager.getNotificationList()
        self.notifsTimer.setNotifications(notifs)

    def handleNotification(self, notification: Notification):
        self.trayIcon.displayMessage(notification.message)
        self.updateTasksView(notification.task)
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

    def updateTasksView(self, updatedTask: Task = None):
        self.ui.tasksTable.updateView(updatedTask)
        self.ui.monthCalendar.updateCells()
        self._updateTrayIndicator()

    ## ====================================================================

    def setDayViewDate(self):
        calendarDate = self.ui.navcalendar.selectedDate()
        self.ui.dayList.setCurrentDate(calendarDate)

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
        manager: MultiManager = self.data.getManager()
        notesDict = manager.getNotes()
        self.ui.notesWidget.setNotes(notesDict)

    def importXfceNotes(self):
        retButton = QMessageBox.question(
            self,
            "Import Notes",
            "Do you want to import Xfce Notes (previous notes will be lost)?",
        )
        if retButton == QMessageBox.Yes:
            self.data.importXfceNotes()

    def importICalendar(self):
        fielDialog = QFileDialog(self)
        fielDialog.setFileMode(QFileDialog.ExistingFile)
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        self.data.importICalendar(selectedFile)

    def _handleNextMessage(self):
        with self.messagesQueueWatchdog.ignoreEvents():
            message = get_from_queue(nowait=True)

        if message is None:
            _LOGGER.warning("received None message")
            return

        message_type, message_value = message
        if message_type == "file":
            self.data.importICalendar(message_value, silent=True)
            return

        _LOGGER.warning("unknown message: %s", message)

    ## ====================================================================

    def updateTrayToolTip(self):
        toolTip = ""
        manager: MultiManager = self.data.getManager()
        deadlineTask = manager.getNextDeadline()
        if deadlineTask is not None:
            toolTip += "\n" + "Next deadline: " + deadlineTask.title
        nextToDo = manager.getNextToDo()
        if nextToDo is not None:
            toolTip += "\n" + "Next ToDo: " + nextToDo.title
        toolTip = self.toolTip + "\n" + toolTip if toolTip else self.toolTip
        self.trayIcon.setToolTip(toolTip)

    def setIconTheme(self, theme: tray_icon.TrayIconTheme):
        _LOGGER.debug("setting tray theme: %r", theme)
        self._setTrayIndicator(theme)

    def _updateTrayIndicator(self):
        appSettings = self.qtSettings.getAppSettings()
        self._setTrayIndicator(appSettings.trayIcon)  ## required to clear old number

    def _setTrayIndicator(self, theme: tray_icon.TrayIconTheme):
        self._updateIconTheme(theme)  ## required to clear old number
        manager: MultiManager = self.data.getManager()
        deadlinedTasks = manager.getDeadlinedTasks()
        remindedTasks = manager.getRemindedTasks()
        indicationTasks = set(deadlinedTasks + remindedTasks)
        indicationSum = len(indicationTasks)
        num = len(deadlinedTasks)
        if num > 0:
            color = get_timeout_color()
            self.trayIcon.drawNumber(indicationSum, color)
            return
        num = len(remindedTasks)
        if num > 0:
            color = get_reminded_color()
            self.trayIcon.drawNumber(indicationSum, color)
            return

    def _updateIconTheme(self, theme: tray_icon.TrayIconTheme):
        fileName = theme.value
        iconPath = resources.get_image_path(fileName)
        appIcon = QIcon(iconPath)

        self.setWindowIcon(appIcon)
        self.trayIcon.setIcon(appIcon)

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        _LOGGER.info("received close event, saving session: %s", qApp.isSavingSession())
        if qApp.isSavingSession():
            ## closing application due to system shutdown
            self.saveAll()
            return
        ## windows close requested by user -- hide the window
        event.ignore()
        self.hide()
        self.trayIcon.show()

    def showEvent(self, _event):
        self.trayIcon.updateLabel()

    def hideEvent(self, _event):
        self.trayIcon.updateLabel()

    ## ====================================================================

    ## slot
    def closeApplication(self):
        ##self.close()
        qApp.quit()

    def saveAll(self):
        _LOGGER.info("saving application state")
        self.saveSettings()
        self.saveData()

    ## ====================================================================

    def openSettingsDialog(self):
        appSettings = self.qtSettings.getAppSettings()
        dialog = SettingsDialog(appSettings, self)
        dialog.setModal(True)
        dialog.iconThemeChanged.connect(self.setIconTheme)
        dialog.exportLocal.connect(self.exportLocalDB)
        dialogCode = dialog.exec_()
        if dialogCode == QDialog.Rejected:
            self.setIconTheme(appSettings.trayIcon)
            return
        self.qtSettings.appSettings = dialog.appSettings
        self.applySettings()

    def applySettings(self, *, load_user_data=True):
        _LOGGER.info("applying settings")
        appSettings = self.qtSettings.getAppSettings()
        self.setIconTheme(appSettings.trayIcon)

        calendar_data: CalendarData = appSettings.getCalendarData()
        self.data.setCalendarData(calendar_data)

        manager_list: list[Manager] = self.qtSettings.createManagersList()

        self.data.setManagerList(manager_list)
        if load_user_data:
            self.loadData()

    def loadSettings(self, *, apply=True, load_user_data=True):
        self.logger.debug("loading app state from %s", self.qtSettings.getSettingsFilePath())

        self.qtSettings.loadSettings()

        if apply:
            self.applySettings(load_user_data=load_user_data)

        self.loadGeometry()

    ## restore widget state and geometry
    def loadGeometry(self):
        settings: QtCore.QSettings = self.qtSettings.getSettings()
        guistate.load_state(self, settings)

    def saveSettings(self):
        self.logger.debug("saving app state to %s", self.qtSettings.getSettingsFilePath())

        self.qtSettings.saveSettings()

        ## store widget state and geometry
        settings: QtCore.QSettings = self.qtSettings.getSettings()
        guistate.save_state(self, settings)

        ## force save to file
        settings.sync()


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
