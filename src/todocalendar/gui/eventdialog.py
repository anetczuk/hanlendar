# # MIT License
# #
# # Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
# #
# # Permission is hereby granted, free of charge, to any person obtaining a copy
# # of this software and associated documentation files (the "Software"), to deal
# # in the Software without restriction, including without limitation the rights
# # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# # copies of the Software, and to permit persons to whom the Software is
# # furnished to do so, subject to the following conditions:
# #
# # The above copyright notice and this permission notice shall be included in all
# # copies or substantial portions of the Software.
# #
# # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# # SOFTWARE.
# #
#
# import logging
# from datetime import datetime
# import copy
#
# from . import uiloader
#
# from todocalendar.domainmodel.event import Event
#
#
# UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )
#
#
# _LOGGER = logging.getLogger(__name__)
#
#
# class EventDialog( QtBaseClass ):           # type: ignore
#
#     def __init__(self, eventObject, parentWidget=None):
#         super().__init__(parentWidget)
#         self.ui = UiTargetClass()
#         self.ui.setupUi(self)
#
#         if eventObject is not None:
#             self.event = copy.deepcopy( eventObject )
#         else:
#             self.event = Event()
#
#         if self.event.startDate is None:
#             self.event.startDate = datetime.today()
#
#         self.ui.titleEdit.setText( self.event.title )
#         self.ui.descriptionEdit.setText( self.event.description )
#         self.ui.completionSlider.setValue( self.event.completed )
#         self.ui.startDateTime.setDateTime( self.event.startDate )
#
#         self.ui.titleEdit.textChanged.connect( self._titleChanged )
#         self.ui.descriptionEdit.textChanged.connect( self._descriptionChanged )
#         self.ui.completionSlider.valueChanged.connect( self._completedChanged )
#         self.ui.startDateTime.dateTimeChanged.connect( self._startChanged )
#
#     def _titleChanged(self, newValue):
#         self.event.title = newValue
#
#     def _descriptionChanged(self):
#         newValue = self.ui.descriptionEdit.toPlainText()
#         self.event.description = newValue
#
#     def _completedChanged(self, newValue):
#         self.event.completed = newValue
#
#     def _startChanged(self, newValue):
#         self.event.startDate = newValue.toPyDateTime()
