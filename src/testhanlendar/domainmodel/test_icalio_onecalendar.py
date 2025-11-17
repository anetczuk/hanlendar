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

import unittest

import datetime

from hanlendar.domainmodel.icalio import (
    import_icalendar_content,
    export_icalendar_content,
    sort_ical_content,
    replace_line,
    remove_line,
)

from hanlendar.domainmodel.local.manager import LocalManager as Manager
from hanlendar.domainmodel.local.task import LocalTask

from testhanlendar.data import get_data_path
from testhanlendar.domainmodel.caldav.radicalemock import read_file


class IcalioOneCalendarTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        self.maxDiff = None

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_onecalendar_item_all_day(self):
        ## compatibility with onecalendar

        event_path = get_data_path("onecalendar_item_all_day.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("be4f8f17-1cd6-4432-9686-c113391b6058", new_item.UID)
        self.assertEqual(None, new_item.createDateTime)
        self.assertEqual(
            datetime.datetime(2025, 11, 6, 23, 12, 3),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 20, 0, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 11, 21, 0, 0), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("🌴 Onecal all day item", new_item.summary)
        self.assertEqual("Loc", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("desc", new_item.description)
        self.assertEqual(1, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "RRULE": b"FREQ=WEEKLY;UNTIL=20251130;INTERVAL=1;BYDAY=WE,SA",
                "X-ONECAL-CATEGORYID": b"107",
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T221203Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_onecalendar_item_reminder(self):
        ## compatibility with onecalendar

        event_path = get_data_path("onecalendar_item_reminder.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "subcomponents": [
                    b"BEGIN:VTIMEZONE\r\nTZID:Europe/Warsaw\r\nBEGIN:STANDARD\r\nDTS"
                    b"TART:20001029T030000\r\nRRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=1"
                    b"0\r\nTZNAME:CET\r\nTZOFFSETFROM:+0200\r\nTZOFFSETTO:+0100\r"
                    b"\nEND:STANDARD\r\nBEGIN:DAYLIGHT\r\nDTSTART:20000326T020000\r\n"
                    b"RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3\r\nTZNAME:CEST\r\nTZO"
                    b"FFSETFROM:+0100\r\nTZOFFSETTO:+0200\r\nEND:DAYLIGHT\r\nEND:VTI"
                    b"MEZONE\r\n",
                ],
            },
            manager.unknownProps,
        )

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("b6909c08-af3a-4686-82de-07126cc6f9ba", new_item.UID)
        self.assertEqual(None, new_item.createDateTime)
        self.assertEqual(
            datetime.datetime(2025, 11, 11, 22, 45, 27),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 12, 18, 12, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 12, 18, 13, 0), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("Xxx onecal", new_item.summary)
        self.assertEqual("Loc data", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("desc data with reminder 45mins", new_item.description)
        self.assertEqual(1, new_item.sequence)
        self.assertDictEqual(
            {
                "X-ONECAL-CATEGORYID": b"110",
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251111T214527Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTEND;TZID=Europe/Warsaw:20251218T130000",
            "DTEND:20251218T120000Z",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTSTART;TZID=Europe/Warsaw:20251218T120000",
            "DTSTART:20251218T110000Z",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )
