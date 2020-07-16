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
# from datetime import datetime

from . import uiloader

from PyQt5.QtCore import QDir
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QMenu, QInputDialog
from PyQt5.QtWidgets import QLineEdit

# from hanlendar.domainmodel.task import Task
# from hanlendar.domainmodel.recurrent import RepeatType, Recurrent
# from datetime import date


UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


_LOGGER = logging.getLogger(__name__)


NOTES_BG_COLOR = "#f7ec9d"


class SinglePageWidget( QWidget ):

    contentChanged = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.content = ""
        self.changeCounter = 0

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.textEdit = QTextEdit(self)

#         self.textEdit.setStyleSheet( "background-color: #f7ec9d;" )
        self.setStyleSheet(
            """
            QTextEdit {
                background: %s;
            }
            """ % NOTES_BG_COLOR
        )

        vlayout.addWidget( self.textEdit )
        
        self.textEdit.textChanged.connect( self.textChanged )

    def getText(self):
        return self.textEdit.toPlainText()
    
    def textChanged(self):
        contentText = self.getText()
        newLength  = len( contentText )
        currLength = len( self.content )
        diff = abs( newLength - currLength )
        self.changeCounter += diff
        self.content = contentText
        if self.changeCounter > 24:
            self.changeCounter = 0
            self.contentChanged.emit()


class NotesWidget( QtBaseClass ):           # type: ignore

    notesChanged = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.ui.notes_tabs.setStyleSheet(
            """
            QTabWidget {
                background: %s;
            }
            QTabBar {
                background: %s;
            }
            """ % (NOTES_BG_COLOR, NOTES_BG_COLOR)
        )

        self.ui.notes_tabs.clear()
        self.addTab( "notes" )

    def getNotes(self):
        notes = dict()
        notesSize = self.ui.notes_tabs.count()
        for tabIndex in range(0, notesSize):
            title = self.ui.notes_tabs.tabText( tabIndex )
            pageWidget = self.ui.notes_tabs.widget( tabIndex )
            text = pageWidget.getText()
            notes[ title ] = text
        return notes

    def setNotes(self, notesDict):
        self.ui.notes_tabs.clear()
        for key, value in notesDict.items():
            self.addTab( key, value )

    def addTab(self, title, text=""):
        pageWidget = SinglePageWidget(self)
        pageWidget.textEdit.setText( text )
        pageWidget.contentChanged.connect( self.notesChanged )
        self.ui.notes_tabs.addTab( pageWidget, title )

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.mapToGlobal( evPos )
        tabBar    = self.ui.notes_tabs.tabBar()
        tabPos    = tabBar.mapFromGlobal( globalPos )
        tabIndex  = tabBar.tabAt( tabPos )

        contextMenu   = QMenu(self)
        newAction     = contextMenu.addAction("New")
        renameAction  = contextMenu.addAction("Rename")
        deleteAction  = contextMenu.addAction("Delete")

        if tabIndex < 0:
            renameAction.setEnabled( False )
            deleteAction.setEnabled( False )

        action = contextMenu.exec_( globalPos )

        if action == newAction:
            self._newTabRequest()
        elif action == renameAction:
            self._renameTabRequest( tabIndex )
        elif action == deleteAction:
            self.ui.notes_tabs.removeTab( tabIndex )
            self.notesChanged.emit()

    def _newTabRequest( self ):
        newTitle = self._requestTabName( "notes" )
        if len(newTitle) < 1:
            return
        self.addTab( newTitle )
        self.notesChanged.emit()

    def _renameTabRequest( self, tabIndex ):
        if tabIndex < 0:
            return

        tabText = self.ui.notes_tabs.tabText( tabIndex )
        newText = self._requestTabName(tabText)
        if len(newText) < 1:
            return
        self.ui.notes_tabs.setTabText( tabIndex, newText )
        self.notesChanged.emit()

    def _requestTabName( self, currName ):
        newText, ok = QInputDialog.getText( self,
                                            "Rename Note",
                                            "Note name:",
                                            QLineEdit.Normal,
                                            currName )
        if ok and len(newText) > 0:
            return newText
        return ""
