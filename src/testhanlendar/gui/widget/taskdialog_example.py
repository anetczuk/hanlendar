#!/usr/bin/python3
#
# MIT License
#
# Copyright (c) 2017 Arkadiusz Netczuk <dev.arnet@gmail.com>
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


try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError as error:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import sys
from datetime import datetime

from hanlendar.gui.qt import QApplication, renderToPixmap
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.resources import get_root_path
from hanlendar.gui.widget.taskdialog import TaskDialog

from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.local.recurrent import Recurrent


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

parentTask = Task()
parentTask.recurrence = Recurrent()
parentTask.recurrence.setWeekly( 1 )

task = Task()
task.setParent( parentTask )
task.title = "Task 1"
# pylint: disable=C0301
task.description = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
                    '<html><head><meta name="qrichtext" content="1" /><style type="text/css">'
                    'p, li { white-space: pre-wrap; }'
                    '</style></head><body style=" font-family:\'Noto Sans\'; font-size:9pt; font-weight:400; font-style:normal;">'
                    '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">A description</p>'
                    '<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>'
                    '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="www.google.pl"><span style=" text-decoration: underline; color:#0000ff;">www.google.pl</span></a> </p>'
                    '<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>'
                    '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="file:///var/log/kern.log"><span style=" text-decoration: underline; color:#0000ff;">file:///var/log/kern.log</span></a> </p>'
                    '<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html>')

task.completed = 50
task.priority = 5
task.setDefaultDateTime( datetime.today().replace( hour=12, minute=0, second=0 ) )

setup_interrupt_handling()

dialog = TaskDialog( task )
dialog.resize(400, 450)

root_path = get_root_path()
renderToPixmap( dialog, root_path + "/tmp/taskdialog-big.png" )

dialogCode = dialog.exec_()

print( "Dialog return:", dialogCode )
print( "Created task:", dialog.task )
