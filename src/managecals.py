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
from hanlendar.gui.widget.settingsdialog import AppSettings, LocalCalendarItem, CalendarItem
from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.item import CommonData


_LOGGER = logging.getLogger(__name__)


## ========================================================================================


def list_cals(_args) -> int:
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
    return 0


## ========================================================================================


def move_items(args) -> int:
    initialize_qt()
    settings = SettingsObject()
    settings.loadSettings()
    appSettings: AppSettings = settings.getAppSettings()

    from_cal_id = args.fromcalid
    if from_cal_id == "None":
        from_cal_id = None
    to_cal_id = args.tocalid
    if to_cal_id == "None":
        to_cal_id = None

    if from_cal_id == to_cal_id:
        _LOGGER.warning("unable to move items to the same calendar")
        return 1

    from_cal_item: CalendarItem = appSettings.getCalendarById(from_cal_id)
    to_cal_item: CalendarItem = appSettings.getCalendarById(to_cal_id)

    from_manager: Manager = settings.createManager(from_cal_item)
    to_manager: Manager = settings.createManager(to_cal_item)

    if from_manager is None:
        _LOGGER.warning("unable to get manager by id: %s", from_cal_id)
        return 1
    if to_manager is None:
        _LOGGER.warning("unable to get manager by id: %s", to_cal_id)
        return 1

    from_manager.loadDataLocal()
    to_manager.loadDataLocal()

    ## move instances between managers
    from_tasks = from_manager.tasks
    from_todos = from_manager.todos
    to_tasks = to_manager.tasks
    to_todos = to_manager.todos
    from_manager.tasks = to_tasks
    from_manager.todos = to_todos
    to_manager.tasks = from_tasks
    to_manager.todos = from_todos

    ## update calendar id
    fix_items_id(from_manager)
    fix_items_id(to_manager)

    ## store data
    from_manager.storeDataLocal()
    to_manager.storeDataLocal()

    print("changed")
    return 0


def fix_items_id(manager: Manager):
    calendar_id = manager.getCalendarId()
    tasks = manager.getTasksAll()
    todos = manager.getTodosAll()

    for item in tasks:
        task_data: CommonData = item.commonData
        task_data.calendar_id = calendar_id

    for item in todos:
        todo_data: CommonData = item.commonData
        todo_data.calendar_id = calendar_id


## ========================================================================================


def save_to_server(_args) -> int:
    initialize_qt()
    settings = SettingsObject()
    settings.loadSettings()
    appSettings: AppSettings = settings.getAppSettings()

    calendar_items = list(appSettings.calendar_items)
    default_manager = LocalCalendarItem()
    default_manager.calendar_id = None
    calendar_items.insert(0, default_manager)

    for cal_item in calendar_items:
        print("storing calendar:", cal_item.getCalendarId())
        manager: Manager = settings.createManager(cal_item)
        manager.loadDataLocal()
        manager.storeData()

    print("done")
    return 0


## ========================================================================================


def remove_repeated(args) -> int:
    initialize_qt()
    settings = SettingsObject()
    settings.loadSettings()
    appSettings: AppSettings = settings.getAppSettings()

    cal_id = args.calid
    if cal_id == "None":
        cal_id = None

    cal_item: CalendarItem = appSettings.getCalendarById(cal_id)
    manager: Manager = settings.createManager(cal_item)
    if manager is None:
        _LOGGER.warning("unable to get manager by id: %s", cal_id)
        return 1

    manager.loadDataLocal()

    dry_run = args.dryrun
    changed = False

    ## removing repeated tasks
    items_set = set()
    items_list = manager.getTasksAll()
    for task_item in items_list:
        item_id = task_item.UID
        if item_id not in items_set:
            items_set.add(item_id)
            continue
        ## repeated - remove
        changed = True
        print("found repeated task:", task_item.title)
        if dry_run:
            continue
        manager.removeTask(task_item)

    ## removing repeated todos
    items_set = set()
    items_list = manager.getTodosAll()
    for todo_item in items_list:
        item_id = todo_item.UID
        if item_id not in items_set:
            items_set.add(item_id)
            continue
        ## repeated - remove
        changed = True
        print("found repeated todo:", todo_item.title)
        if dry_run:
            continue
        manager.removeToDo(todo_item)  # type: ignore[arg-type]

    if changed:
        manager.storeDataLocal()
        print("done")
    else:
        print("no repetitions found")

    return 0


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

    description = "move items between calendars"
    subparser = subparsers.add_parser(
        "moveitems",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=move_items)
    subparser.add_argument(
        "-f",
        "--fromcalid",
        action="store",
        required=True,
        help="From calendar indicated by ID",
    )
    subparser.add_argument(
        "-t",
        "--tocalid",
        action="store",
        required=True,
        help="To calendar indicated by ID",
    )

    ## =================================================

    description = "store calendars to server"
    subparser = subparsers.add_parser(
        "storecals",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=save_to_server)

    ## =================================================

    description = "remove repeated items from calendar"
    subparser = subparsers.add_parser(
        "removerepeated",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=remove_repeated)
    subparser.add_argument(
        "--calid",
        action="store",
        required=True,
        help="Calendar indicated by ID",
    )
    subparser.add_argument(
        "--dryrun",
        action="store_true",
        help="Dry run",
    )

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
