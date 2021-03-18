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

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QObject


def get_label_url( url: str ):
    return "<a href=\"%s\">%s</a>" % (url, url)


def set_label_url( label: QtWidgets.QLabel, url: str ):
    htmlText = get_label_url(url)
    label.setText( htmlText )


def find_parent(widget: QObject, objectType ):
    if widget is None:
        return None
    widget = get_parent( widget )
    while widget is not None:
        if isinstance(widget, objectType):
            return widget
        widget = get_parent( widget )
    return None


def get_parent( widget: QObject ):
    if callable(widget.parent) is False:
        ## some objects has "parent" attribute instead of "parent" method
        ## e.g. matplotlib's NavigationToolbar
        return None
    return widget.parent()


def render_to_pixmap( widget: QtWidgets.QWidget, outputPath=None ):
    rectangle = widget.geometry()
    pixmap = QtGui.QPixmap( rectangle.size() )
    widget.render( pixmap, QtCore.QPoint(), QtGui.QRegion(rectangle) )
    if outputPath is not None:
        pixmap.save( outputPath )
    return pixmap
