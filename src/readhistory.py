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

# ruff: noqa: T201 (`print` found)

import os
import logging
import argparse

from hanlendar.main import initialize_qt
from hanlendar.domainmodel.local.manager import LocalManager
from hanlendar.gui.main_window import SettingsObject
from hanlendar.domainmodel.local.task import Task


_LOGGER = logging.getLogger(__name__)


def print_data(data_dict, *, detailed=False):
    print("archive:", data_dict.get("file", None))
    tasks: list[Task] = data_dict.get("tasks", [])
    all_tasks = get_tasks_all(tasks)
    all_tasks.sort(reverse=True, key=lambda task: task.dueDateTime)

    for task in all_tasks:
        if detailed is False:
            due = str(task.dueDateTime)
            completed = task.isCompleted()
            data = due + " " + task.getTitle() + " " + str(completed)
            print(data)
        else:
            due = str(task.dueDateTime)
            data = due + " " + task.getTitle() + "\n" + str(task.__dict__)
            print(data)


# Zapłacić podatek za wynajem Woli
def get_tasks_all(tasks_list: list[Task]):
    ret_list: list[Task] = []
    for task in tasks_list:
        items = task.getAllSubItems()
        ret_list += [task, *items]
    return ret_list


def handle_history(localManager: LocalManager, args):
    detailed = bool(args.detailed)

    if args.index is not None:
        index = int(args.index)
        data = localManager.loadHistory(index)
        if data is not None:
            print_data(data, detailed=detailed)
    else:
        index = -1
        while True:
            index += 1
            data = localManager.loadHistory(index)
            if data is None:
                break
            print_data(data, detailed=detailed)


def main():
    parser = argparse.ArgumentParser(description="History read")
    parser.add_argument("-la", "--logall", action="store_true", help="Log all messages")
    parser.add_argument("-i", "--index", action="store", required=False, default=None, help="Log all messages")
    parser.add_argument("--detailed", action="store_true", default=False, help="Print detailed info")

    args = parser.parse_args()

    logging.basicConfig()
    if args.logall is True:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    initialize_qt()
    settings = SettingsObject()

    dataPath = settings.getDataPath()
    os.makedirs(dataPath, exist_ok=True)
    localManager: LocalManager = LocalManager(dataPath)
    handle_history(localManager, args)


if __name__ == "__main__":
    main()
