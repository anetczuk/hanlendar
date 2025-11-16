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
from hanlendar.domainmodel.local.todo import LocalToDo

from testhanlendar.data import get_data_path
from testhanlendar.domainmodel.caldav.radicalemock import read_file


class IcalioEvolutionTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        self.maxDiff = None

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_evolution_all_day_event_basic(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_all_day_event_basic.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("49c4245a00131e320f35c0b1ba360d7d23b0a0af", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 11, 14, 3, 31), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 11, 15, 3, 31),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 28, 0, 0), new_item.startDateTime)
        self.assertEqual(datetime.datetime(2025, 11, 29, 0, 0), new_item.endDateTime)
        self.assertEqual("summary data", new_item.summary)
        self.assertEqual("location data", new_item.location)
        self.assertEqual("webpage data", new_item.url)
        self.assertEqual("description data", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual({"CLASS": b"PUBLIC", "COLOR": b"fuchsia", "TRANSP": b"OPAQUE"}, new_item.unknownProps)

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T211247Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_all_day_event_full(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_all_day_event_full.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("061269e77012385c9d603051e26a8a43a534e9a8", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 6, 22, 52, 59), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 6, 22, 52, 59),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 25, 0, 0), new_item.startDateTime)
        self.assertEqual(datetime.datetime(2025, 11, 26, 0, 0), new_item.dueDateTime)
        self.assertEqual("evolution all day event", new_item.summary)
        self.assertEqual("loc", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "CLASS": b"PUBLIC",
                "EXDATE": b"20251106",
                "RRULE": b"FREQ=DAILY;COUNT=2",
                "STATUS": b"TENTATIVE",
                "TRANSP": b"OPAQUE",
                "subcomponents": [
                    b"BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:ev"
                    b"olution all day event\r\nTRIGGER;RELATED=END:-"
                    b"PT15M\r\nX-EVOLUTION-ALARM-UID:234e78a29144053"
                    b"f40193800fb08a18722cb0f79\r\nEND:VALARM\r\n",
                ],
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T211247Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(event_ical_content, "EXDATE;", "EXDATE:20251106", replace_whole_line=True)

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_appointment_full(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_appointment_full.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("a9029b2d-bb58-11f0-ad88-80fa5b58053f", new_item.UID)
        self.assertEqual(None, new_item.createDateTime)
        self.assertEqual(
            datetime.datetime(2025, 11, 6, 22, 48, 19),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 24, 10, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 11, 24, 11, 0), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("evolution full example", new_item.summary)
        self.assertEqual("location", new_item.location)
        self.assertEqual("web", new_item.url)
        self.assertEqual("descr", new_item.description)
        self.assertEqual(1, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "ATTACH": b"https://google.pl",
                "CLASS": b"PUBLIC",
                "COLOR": b"yellow",
                "RRULE": b"FREQ=DAILY;COUNT=2;INTERVAL=3",
                "STATUS": b"CANCELLED",
                "TRANSP": b"OPAQUE",
                "subcomponents": [
                    b"BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:ev"
                    b"olution full example\r\nTRIGGER;RELATED=START:"
                    b"-PT15M\r\nX-EVOLUTION-ALARM-UID:98686f444ce13b"
                    b"e455218bfc72170a45a8c25e32\r\nEND:VALARM\r\n",
                ],
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T213631Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "ATTACH;",
            "ATTACH:https://google.pl",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "RRULE;",
            "RRULE:FREQ=DAILY;COUNT=2;INTERVAL=3",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_appointment_multi_reminders(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_appointment_multi_reminders.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "subcomponents": [
                    b"BEGIN:VTIMEZONE\r\nTZID:Europe/Warsaw\r\nX-L"
                    b"IC-LOCATION:Europe/Warsaw\r\nBEGIN:STANDAR"
                    b"D\r\nDTSTART:19961027T030000\r\nRRULE:FREQ=Y"
                    b"EARLY;UNTIL=20361026T010000Z;BYDAY=-1SU;BYMO"
                    b"NTH=10\r\nTZNAME:CET\r\nTZOFFSETFROM:+02"
                    b"00\r\nTZOFFSETTO:+0100\r\nEND:STANDARD\r\n"
                    b"BEGIN:DAYLIGHT\r\nDTSTART:19880327T020000\r"
                    b"\nRRULE:FREQ=YEARLY;UNTIL=20370329T010000Z;BY"
                    b"DAY=-1SU;BYMONTH=3\r\nTZNAME:CEST\r\nTZOFFSE"
                    b"TFROM:+0100\r\nTZOFFSETTO:+0200\r\nEND:DAYLI"
                    b"GHT\r\nEND:VTIMEZONE\r\n",
                ],
            },
            manager.unknownProps,
        )

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("8766de5b308b5fc332d7f525ea058e23fa5f6a43", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 16, 2, 5, 34), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 16, 2, 5, 34),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 12, 11, 9, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 12, 11, 9, 25), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("multiple reminders", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "CLASS": b"PUBLIC",
                "TRANSP": b"OPAQUE",
                "subcomponents": [
                    b"BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:multiple r"
                    b"eminders\r\nTRIGGER;RELATED=START:-PT15M\r\nX-EVOLUTION-"
                    b"ALARM-UID:9892d2f34689401854031bad2d3e7168680f73ac\r\nEND:"
                    b"VALARM\r\n",
                    b"BEGIN:VALARM\r\nACTION:AUDIO\r\nTRIGGER;RELATED=START:-P"
                    b"T2H\r\nX-EVOLUTION-ALARM-UID:8bc796cda97b3d7b35add94b999be"
                    b"1b1a19b2ea5\r\nEND:VALARM\r\n",
                    b"BEGIN:VALARM\r\nACTION:PROCEDURE\r\nATTACH:prog_xxx\r\nDUR"
                    b"ATION:PT5M\r\nREPEAT:1\r\nTRIGGER;RELATED=END:P3D\r\nX-EVO"
                    b"LUTION-ALARM-UID:30e05dbbdef65a603da399415ee1652c35e34b8"
                    b"1\r\nEND:VALARM\r\n",
                ],
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T211247Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTEND;",
            "DTEND:20251211T082500Z",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTSTART;",
            "DTSTART:20251211T080000Z",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_task_basic(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_task_basic.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalToDo = new_items[0]
        self.assertEqual(LocalToDo, type(new_item))
        self.assertEqual("7c72ab99414ca6dfe803be5765508d9055909706", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 8, 1, 2, 51), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 11, 8, 1, 2, 51), new_item.lastModifiedDateTime.replace(tzinfo=None))
        self.assertEqual("evolution task sample", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(1, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {"CLASS": b"CONFIDENTIAL", "DUE": b"20251122", "PERCENT-COMPLETE": b"45", "STATUS": b"IN-PROCESS"},
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251104T195837Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_task_completed(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_task_completed.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalToDo = new_items[0]
        self.assertEqual(LocalToDo, type(new_item))
        self.assertEqual("f5dccad88abe34db1e29b7432b1c2dd9d1169316", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 13, 21, 34, 59), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 13, 21, 35, 38),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual("evolution todo start end", new_item.summary)
        self.assertEqual("todo location", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("todo descr", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "CLASS": b"PUBLIC",
                "COMPLETED": b"20251113T000000Z",
                "DTSTART": b"20251114",
                "DUE": b"20251116",
                "ESTIMATED-DURATION": b"P1DT2H3M",
                "PERCENT-COMPLETE": b"100",
                "STATUS": b"COMPLETED",
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251108T000146Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")

        self.assertEqual(
            event_ical_content,
            content,
        )
