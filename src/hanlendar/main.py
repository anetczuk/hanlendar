#!/usr/bin/python3
#
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


import sys

import argparse
import logging

import hanlendar.logger as logger

from hanlendar.gui.main_window import MainWindow

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.widget.menustyle import MenuStyle


logger.configure()
_LOGGER = logging.getLogger(__name__)


def run_app(args):
    ## GUI
    app = QApplication(sys.argv)
    app.setApplicationName("Hanlendar")
    app.setOrganizationName("arnet")
    ### app.setOrganizationDomain("www.my-org.com")

    ## disable Alt key switching to application menu
    app.setStyle( MenuStyle() )

    window = MainWindow()
    if args.blocksave is True:
        window.disableSaving()
    window.loadSettings()
    window.loadData()

    if args.minimized is False:
        window.show()

    setup_interrupt_handling()

    exitCode = app.exec_()

    if exitCode == 0:
        window.saveSettings()
        window.saveData()

    return exitCode


def create_parser( parser: argparse.ArgumentParser = None ):
    if parser is None:
        parser = argparse.ArgumentParser(description='Hanlendar')
    parser.add_argument('--minimized', action='store_const', const=True, default=False, help='Start minimized' )
    parser.add_argument('--blocksave', '-bs', action='store_const', const=True, default=None, help='Block save data' )
    return parser


def main( args=None ):
    if args is None:
        parser = create_parser()
        args = parser.parse_args()

    _LOGGER.debug( "Starting the application" )
    _LOGGER.debug( "Logger log file: %s", logger.log_file )

    exitCode = 1

    try:
        exitCode = run_app(args)

    except BaseException:
        _LOGGER.exception("Exception occurred")
        raise

    finally:
        sys.exit(exitCode)

    return exitCode


if __name__ == '__main__':
    main()
