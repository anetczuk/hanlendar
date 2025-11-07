#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2025 Arkadiusz Netczuk <dev.arnet@gmail.com>
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

from datetime import datetime

import json
import requests
import caldav

from caldav.lib import error


if __name__ == "__main__":
    _LOGGER = logging.getLogger("caldavmanager")
else:
    _LOGGER = logging.getLogger(__name__)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def read_json(file_path):
    if not os.path.isfile(file_path):
        return None
    with open(file_path, encoding="utf-8") as content_file:
        content = ""
        for line in content_file:
            ## remove comments from JSON file
            index = line.find("#")
            if index >= 0:
                content += line[:index] + "\n"
            else:
                content += line
        if not content:
            ## empty file case
            return None
        return json.loads(content)


def create_principal(auth_dict):
    caldav_url = auth_dict["url"]
    caldav_username = auth_dict["user"]
    caldav_password = auth_dict["password"]

    try:
        _LOGGER.info("connecting to %s", caldav_url)
        caldav_client = caldav.DAVClient(url=caldav_url, username=caldav_username, password=caldav_password)

    except requests.exceptions.ConnectionError:
        _LOGGER.error("unable to connect to CalDAV server '%s'", caldav_url)
        sys.exit(1)
    except error.AuthorizationError:
        _LOGGER.error(
            "unable to authorize to CalDAV server '%s' with user '%s' pass '%s'",
            caldav_url,
            caldav_username,
            caldav_password,
        )
        sys.exit(1)

    return caldav_client.principal()


def convert_to_datetime(value_string: str):
    if value_string is None:
        return None
    try:
        ## format: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        return datetime.strptime(value_string, "%Y-%m-%d %H:%M")
    except Exception as exc:  # pylint: disable=W0718
        _LOGGER.error("unable to create datetime: %s", exc)
        return None


def process_calcreate(args):
    auth_path = args.authjson
    auth_dict = read_json(auth_path)

    caldav_principal = create_principal(auth_dict)

    try:
        cal_name = args.name
        calendar: caldav.objects.Calendar = caldav_principal.make_calendar(name=cal_name, cal_id=cal_name)
        _LOGGER.info("created new calendar:")
        _LOGGER.info("  name: %s", calendar.name)
        _LOGGER.info("    id: %s", calendar.id)
        _LOGGER.info("   url: %s", calendar.url)
    except error.MkcalendarError:
        _LOGGER.error("unable to create calendar '%s'", cal_name)
        sys.exit(1)


def process_listcals(args):
    auth_path = args.authjson
    auth_dict = read_json(auth_path)

    caldav_principal = create_principal(auth_dict)
    calendars: list[caldav.objects.Calendar] = caldav_principal.calendars()

    calendars.sort(key=lambda item: item.name)

    _LOGGER.info("current calendars:")
    for calitem in calendars:
        description = calitem.get_property(caldav.elements.cdav.CalendarDescription())
        _LOGGER.info("  - name: %s id: %s url: %s description: %s", calitem.name, calitem.id, calitem.url, description)
        _LOGGER.info(
            "    events: %s journals: %s todos: %s",
            len(calitem.events()),
            len(calitem.journals()),
            len(calitem.todos()),
        )


def process_calitems(args):
    auth_path = args.authjson
    auth_dict = read_json(auth_path)

    caldav_principal = create_principal(auth_dict)

    try:
        cal_id = args.calid
        calendar: caldav.objects.Calendar = caldav_principal.calendar(cal_id=cal_id)

        ## check if calendar exists by just access it's properties
        cal_name = calendar.get_display_name()  # type: ignore[attr-defined]
        events: list[caldav.objects.Event] = calendar.events()
        todos: list[caldav.objects.Todo] = calendar.todos()
        journals: list[caldav.objects.Journal] = calendar.journals()

        _LOGGER.info("calendar name: %s id: %s url: %s", cal_name, calendar.id, calendar.url)
        _LOGGER.info("events: %s todos: %s journals: %s", len(events), len(todos), len(journals))

        _LOGGER.info("events:")
        for event in events:
            name = event.name
            if name is not None:
                name = f"'{name}'"
            start = event.icalendar_component.get("DTSTART")  # type: ignore[attr-defined]
            if start:
                start = start.dt
            end = event.icalendar_component.get("DTEND")  # type: ignore[attr-defined]
            if end:
                end = end.dt
            summary = event.icalendar_component.get("SUMMARY")  # type: ignore[attr-defined]
            if summary is not None:
                summary = f"'{summary}'"

            _LOGGER.info(
                "  - name: %s start: %s end: %s duration: %s summary: %s url: %s",
                name,
                start,
                end,
                event.get_duration(),
                summary,
                event.url,
            )
            _LOGGER.info("    raw data: %s", event.icalendar_component)  # type: ignore[attr-defined]

        _LOGGER.info("todos:")
        for todo in todos:
            name = todo.name
            if name is not None:
                name = f"'{name}'"
            _LOGGER.info(
                "  - name: %s due: %s duration: %s url: %s",
                name,
                todo.get_due(),  # type: ignore[attr-defined]
                todo.get_duration(),
                todo.url,
            )

        _LOGGER.info("journals:")
        for journal in journals:
            name = journal.name
            if name is not None:
                name = f"'{name}'"
            _LOGGER.info(
                "  - name: %s due: %s duration: %s url: %s",
                name,
                journal.get_due(),  # type: ignore[attr-defined]
                journal.get_duration(),
                journal.url,
            )

    except error.NotFoundError:
        _LOGGER.error("calendar with given id '%s' does not exist", cal_id)
        sys.exit(1)


def process_addevent(args):
    auth_path = args.authjson
    auth_dict = read_json(auth_path)

    caldav_principal = create_principal(auth_dict)

    try:
        cal_id = args.calid
        calendar: caldav.objects.Calendar = caldav_principal.calendar(cal_id=cal_id)

        event_dict = {}
        start_time = convert_to_datetime(args.start)
        if start_time:
            event_dict["dtstart"] = start_time
        end_time = convert_to_datetime(args.end)
        if end_time:
            event_dict["dtend"] = end_time
        summary = args.summary
        if summary:
            event_dict["summary"] = summary
        # freq = args.freq
        # if freq:
        #     # rrule={"FREQ": "YEARLY"},
        #     event_dict["rrule"] = freq

        _LOGGER.info("creating event: %s", event_dict)
        new_event: caldav.objects.Event = calendar.save_event(**event_dict)
        if new_event.data is None:
            _LOGGER.warning("could not create event")
            sys.exit(1)

        _LOGGER.info("event created: %s", new_event.url)
        _LOGGER.info("raw data: %s", new_event.icalendar_component)  # type: ignore[attr-defined]

    except error.NotFoundError:
        _LOGGER.error("calendar with given id '%s' does not exist", cal_id)
        sys.exit(1)


## =====================================


def main():
    SCRIPT_NAME = os.path.basename(__file__)

    parser = argparse.ArgumentParser(description="CalDAV manager")
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="CalDAV manager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--authjson", action="store", default=None, help="Path to JSON with credentials")
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(help="commands", description="commands", dest="command", required=False)

    ## =================================================

    description = "create new calendar"
    subparser = subparsers.add_parser(
        "calcreate",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=process_calcreate)
    subparser.add_argument("--name", action="store", required=True, help="Name of new calendar")

    ## =================================================

    description = "list calendars"
    subparser = subparsers.add_parser(
        "listcals",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=process_listcals)

    ## =================================================

    description = "list calendar content"
    subparser = subparsers.add_parser(
        "calitems",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=process_calitems)
    subparser.add_argument("--calid", action="store", required=True, help="Id of calendar")

    ## =================================================

    description = "add event"
    subparser = subparsers.add_parser(
        "addevent",
        help=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparser.description = description
    subparser.set_defaults(func=process_addevent)
    subparser.add_argument("--calid", action="store", required=True, help="Calendar ID")
    subparser.add_argument(
        "--start",
        action="store",
        required=True,
        help="Event start, in format '%Y-%M-%D %H-%m' (quote required)",
    )
    subparser.add_argument(
        "--end",
        action="store",
        required=False,
        help="Event end, in format '%Y-%M-%D %H-%m' (quote required)",
    )
    subparser.add_argument("--summary", action="store", required=False, help="Summary of event")

    ## =================================================

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if "func" not in args or args.func is None:
        ## no command given -- print help message
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    main()
