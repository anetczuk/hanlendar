#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2026 Arkadiusz Netczuk <dev.arnet@gmail.com>
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

# ruff: noqa: T201 (`print` found)

import sys
import logging
import argparse

from hanlendar.main import initialize_qt
from hanlendar.gui.main_window import SettingsObject
from hanlendar.gui.widget.settingsdialog import AppSettings, LocalCalendarItem
from hanlendar.domainmodel.manager import Manager


_LOGGER = logging.getLogger(__name__)


## ========================================================================================


def list_cals(_args):
    initialize_qt()
    settings = SettingsObject()
    settings.loadSettings()
    appSettings: AppSettings = settings.getAppSettings()

    calendar_items = list(appSettings.calendar_items)
    default_manager = LocalCalendarItem()
    default_manager.calendar_id = None
    calendar_items.insert(0, default_manager)

    cals_num = len(calendar_items)
    print(f"calendars list[{cals_num}]:")
    for cal_item in calendar_items:
        manager: Manager = settings.createManager(cal_item)
        manager.loadDataLocal()
        tasks_num = len(manager.tasks)
        todos_num = len(manager.todos)

        print(
            f" - id: {cal_item.getCalendarId()} name: {cal_item.getCalendarName()} mode: {cal_item.getCalendarMode()}"
            f" enabled: {cal_item.isEnabled()}"
            f" | tasks: {tasks_num} todos: {todos_num}",
        )


## ========================================================================================


def main() -> int:
    parser = argparse.ArgumentParser(description="History read")
    parser.add_argument("-la", "--logall", action="store_true", help="Log all messages")
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(help="commands", description="commands", dest="command", required=False)

    ## =================================================

    description = "list configured calendars"
    subparser = subparsers.add_parser(
        "listcals",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=list_cals)

    ## =================================================

    args = parser.parse_args()

    logging.basicConfig()
    if args.logall is True:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    if "func" not in args or args.func is None:
        ## no command given -- print help message
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
