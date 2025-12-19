#!/usr/bin/env python3
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
import os

import argparse
import logging

import pidfile

from hanlendar import logger
from hanlendar.gui.main_window import MainWindow
from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.widget.menustyle import MenuStyle
from hanlendar.fqueue import put_to_queue


script_dir = os.path.dirname(__file__)
tmp_dir = os.path.realpath(os.path.join(script_dir, os.pardir, os.pardir, "tmp"))


logger.configure()
_LOGGER = logging.getLogger(__name__)


def initialize_qt():
    app = QApplication(sys.argv)
    app.setApplicationName("Hanlendar")
    app.setOrganizationName("arnet")
    ### app.setOrganizationDomain("www.my-org.com")
    app.setQuitOnLastWindowClosed(False)

    ## disable Alt key switching to application menu
    app.setStyle(MenuStyle())

    setup_interrupt_handling()

    return app


def run_app(args):
    ## GUI
    app = initialize_qt()

    window = MainWindow()
    local_data_path = args.localdatadir
    window.setLocalDataRootPath(local_data_path)
    if args.blocksave is True:
        window.disableSaving()
    if args.exportlocal is True:
        caldav_address = args.caldavaddress
        caldav_user = args.caldavuser
        caldav_pass = args.caldavpass
        caldav_calendar = args.caldavcalendar
        window.exportLocalToCalDAV(caldav_address, caldav_user, caldav_pass, caldav_calendar)
    window.loadSettings(apply=False)
    if args.caldav is True:
        caldav_address = args.caldavaddress
        caldav_user = args.caldavuser
        caldav_pass = args.caldavpass
        caldav_calendar = args.caldavcalendar
        window.setCalDAVManager(caldav_address, caldav_user, caldav_pass, caldav_calendar)
    window.applySettings()

    if args.minimized is False:
        window.show()

    exitCode = app.exec_()

    if exitCode == 0:
        window.saveAll()

    return exitCode


def create_parser(parser: argparse.ArgumentParser = None):
    if parser is None:
        parser = argparse.ArgumentParser(description="Hanlendar")
    parser.add_argument("--minimized", action="store_const", const=True, default=False, help="Start minimized")
    parser.add_argument("--blocksave", "-bs", action="store_const", const=True, default=None, help="Block save data")
    parser.add_argument("--localdatadir", action="store", default=None, help="Path to custom local data")
    parser.add_argument("--caldav", action="store_const", const=True, default=None, help="Run in CalDAV mode")
    parser.add_argument("--caldavaddress", action="store", default=None, help="Address of CalDAV server")
    parser.add_argument("--caldavuser", action="store", default=None, help="User for CalDAV connection")
    parser.add_argument("--caldavpass", action="store", default=None, help="Password for CalDAV connection")
    parser.add_argument("--caldavcalendar", action="store", default=None, help="CalDAV calendar name")
    parser.add_argument(
        "--exportlocal",
        action="store_const",
        const=True,
        default=None,
        help="Export local database to CalDAV server (use caldav... options to connect)",
    )
    return parser


def start(args):
    _LOGGER.debug("Starting the application")
    _LOGGER.debug("Logger log file: %s", logger.output_file)
    _LOGGER.debug("Arguments: %s", sys.argv[1:])

    exitCode = 1

    try:
        exitCode = run_app(args)

    except BaseException:
        _LOGGER.exception("Exception occurred")
        raise

    finally:
        sys.exit(exitCode)

    return exitCode


def start_single(args=None):
    if args is None:
        parser = create_parser()
        args = parser.parse_args()

    ## check if instance already running
    pid_path = os.path.join(tmp_dir, "hanlendar.pid")
    with pidfile.PidFile(pid_path):
        ## first instance -- start
        start(args)


def main(args=None):
    if len(sys.argv) != 2:
        ## run as usual
        start_single(args)
        return

    ## only one argument passed -- it should be *.ics file path
    file_path = sys.argv[1]
    if os.path.isfile(file_path) is False:
        ## not file -- run as usual
        start_single(args)
        return

    ## file passed -- add to queue
    sys.argv = sys.argv[:1]
    put_to_queue("file", file_path)

    ## run application
    start_single(args)


if __name__ == "__main__":
    main()
