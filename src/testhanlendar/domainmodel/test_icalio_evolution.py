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
        self.assertEqual(datetime.datetime(2025, 11, 28, 0, 0).astimezone(), new_item.startDateTime)
        self.assertEqual(datetime.datetime(2025, 11, 29, 0, 0).astimezone(), new_item.endDateTime)
        self.assertEqual("summary data", new_item.summary)
        self.assertEqual("location data", new_item.location)
        self.assertEqual("webpage data", new_item.url)
        self.assertEqual("description data", new_item.description)
        self.assertEqual(2, new_item.sequence)
        self.assertEqual(0, len(new_item.reminderList))
        # TODO: all unknown props should be handled
        self.assertDictEqual({"COLOR": b"fuchsia", "TRANSP": b"OPAQUE"}, new_item.unknownProps)

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
        self.assertEqual(datetime.datetime(2025, 11, 25, 0, 0).astimezone(), new_item.startDateTime)
        self.assertEqual(datetime.datetime(2025, 11, 26, 0, 0).astimezone(), new_item.dueDateTime)
        self.assertEqual("evolution all day event", new_item.summary)
        self.assertEqual("loc", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "TRANSP": b"OPAQUE",
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
            "EXDATE;VALUE=DATE:20251106",
            "EXDATE:20251106",
            replace_whole_line=True,
        )
        event_ical_content = replace_line(
            event_ical_content,
            "EXDATE;VALUE=DATE:20251118",
            "EXDATE:20251118",
            replace_whole_line=True,
        )

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
            {"ATTACH": b"https://google.pl", "COLOR": b"yellow", "TRANSP": b"OPAQUE"},
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
            "ATTACH;FMTTYPE=application/x-perl:https://google.pl",
            "ATTACH:https://google.pl",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "RRULE;X-EVOLUTION-ENDDATE=20251127T090000Z:FREQ=DAILY;COUNT=2;INTERVAL=3",
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
        self.assertDictEqual({"TRANSP": b"OPAQUE"}, new_item.unknownProps)

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
            "DTEND;TZID=Europe/Warsaw:20251211T092500",
            "DTEND:20251211T082500Z",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTSTART;TZID=Europe/Warsaw:20251211T090000",
            "DTSTART:20251211T080000Z",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_appointment_recurrent(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_appointment_recurrent.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "subcomponents": [
                    b"BEGIN:VTIMEZONE\r\nTZID:Europe/Warsaw\r\nX-LIC-LOCATION:"
                    b"Europe/Warsaw\r\nBEGIN:STANDARD\r\nDTSTART:19961027T0300"
                    b"00\r\nRRULE:FREQ=YEARLY;UNTIL=20361026T010000Z;BYDAY=-1SU;"
                    b"BYMONTH=10\r\nTZNAME:CET\r\nTZOFFSETFROM:+0200\r\nTZOFFSET"
                    b"TO:+0100\r\nEND:STANDARD\r\nBEGIN:STANDARD\r\nDTSTART:2037"
                    b"1025T030000\r\nRRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10"
                    b"\r\nTZNAME:CET\r\nTZOFFSETFROM:+0200\r\nTZOFFSETTO:+01"
                    b"00\r\nEND:STANDARD\r\nBEGIN:DAYLIGHT\r\nDTSTART:19880327T0"
                    b"20000\r\nRRULE:FREQ=YEARLY;UNTIL=20370329T010000Z;BYDAY=-1"
                    b"SU;BYMONTH=3\r\nTZNAME:CEST\r\nTZOFFSETFROM:+0100\r\nTZOFF"
                    b"SETTO:+0200\r\nEND:DAYLIGHT\r\nBEGIN:DAYLIGHT\r\nDTSTART:2"
                    b"0380328T020000\r\nRRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH"
                    b"=3\r\nTZNAME:CEST\r\nTZOFFSETFROM:+0100\r\nTZOFFSETTO:+020"
                    b"0\r\nEND:DAYLIGHT\r\nEND:VTIMEZONE\r\n",
                ],
            },
            manager.unknownProps,
        )

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("852294732a8d21a4af0993fdbbfd09caf6f7eadf", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 17, 22, 32, 57), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 17, 22, 32, 57),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 12, 5, 9, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 12, 5, 9, 25), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("evolution appointment recurrent", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("started 05.12.2025", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual({"TRANSP": b"OPAQUE"}, new_item.unknownProps)

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
            "DTEND;TZID=Europe/Warsaw:20251205T092500",
            "DTEND:20251205T082500Z",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTSTART;TZID=Europe/Warsaw:20251205T090000",
            "DTSTART:20251205T080000Z",
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
        self.assertIsNone(new_item.startDateTime)
        self.assertEqual(datetime.datetime(2025, 11, 22, 0, 0), new_item.dueDateTime.replace(tzinfo=None))
        self.assertIsNone(new_item.completedDateTime)
        self.assertEqual("evolution task sample", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(1, new_item.sequence)
        self.assertDictEqual({}, new_item.unknownProps)

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
        self.assertEqual(
            datetime.datetime(2025, 11, 14, 0, 0),
            new_item.startDateTime.replace(tzinfo=None),
        )
        self.assertEqual(
            datetime.datetime(2025, 11, 16, 0, 0),
            new_item.dueDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 13, 1, 0), new_item.completedDateTime.replace(tzinfo=None))
        self.assertEqual("evolution todo start end", new_item.summary)
        self.assertEqual("todo location", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("todo descr", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual({"ESTIMATED-DURATION": b"P1DT2H3M"}, new_item.unknownProps)

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251108T000146Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "COMPLETED:20251113T000000Z",
            "COMPLETED;VALUE=DATE:20251113",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_task_recurrent(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_task_recurrent.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalToDo = new_items[0]
        self.assertEqual(LocalToDo, type(new_item))
        self.assertEqual("b5ca5750aae3021469829d2e8dae3d761030c0f4", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 17, 17, 39, 19), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 17, 17, 39, 19),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(
            datetime.datetime(2025, 11, 20, 0, 0),
            new_item.startDateTime.replace(tzinfo=None),
        )
        self.assertEqual(
            datetime.datetime(2025, 11, 24, 0, 0),
            new_item.dueDateTime.replace(tzinfo=None),
        )
        self.assertIsNone(new_item.completedDateTime)
        self.assertEqual("evolution task repeated 1", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(1, new_item.sequence)
        self.assertDictEqual({}, new_item.unknownProps)

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251108T000146Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        event_ical_content = remove_line(event_ical_content, "PERCENT-COMPLETE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "EXDATE;VALUE=DATE:20251122",
            "EXDATE:20251122",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_task_recurrent_completed(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_task_recurrent_completed.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalToDo = new_items[0]
        self.assertEqual(LocalToDo, type(new_item))
        self.assertEqual("f69520b625348c108feb96b2815247ed5dff8600", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 17, 22, 0, 26), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 17, 22, 2, 4),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(
            datetime.datetime(2026, 2, 1, 0, 0),
            new_item.startDateTime.replace(tzinfo=None),
        )
        self.assertEqual(
            datetime.datetime(2026, 2, 2, 0, 0),
            new_item.dueDateTime.replace(tzinfo=None),
        )
        self.assertIsNone(new_item.completedDateTime)
        self.assertEqual("evolution recurrent task", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("completed twice, first started 5.12.2025", new_item.description)
        self.assertEqual(3, new_item.sequence)
        self.assertDictEqual({}, new_item.unknownProps)

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

    def test_evolution_task_reminder(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_task_reminder.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalToDo = new_items[0]
        self.assertEqual(LocalToDo, type(new_item))
        self.assertEqual("5b0e9a12d0a7c37551a07a5e173c61a371629717", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 22, 22, 37, 19), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 22, 22, 39, 49),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertIsNone(new_item.startDateTime)
        self.assertIsNone(new_item.dueDateTime)
        self.assertIsNone(new_item.completedDateTime)
        self.assertEqual("evolution todo eample", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("with simple reminder", new_item.description)
        self.assertEqual(2, new_item.sequence)
        self.assertDictEqual({}, new_item.unknownProps)

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251104T195837Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        event_ical_content = remove_line(event_ical_content, "PERCENT-COMPLETE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "EXDATE;VALUE=DATE:20251122",
            "EXDATE:20251122",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )
