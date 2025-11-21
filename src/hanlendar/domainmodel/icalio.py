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

# pylint: disable=W0212,C0302

import logging
from enum import Enum, unique
from typing import Union, Any
import datetime
from datetime import timedelta
import re

import icalendar
from icalendar.prop import TypesFactory

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.local.todo import LocalToDo
from hanlendar.domainmodel.recurrent import Recurrent, RepeatType, RepeatUntilMode
from hanlendar.domainmodel.reminder import Reminder, RelatedType


_LOGGER = logging.getLogger(__name__)


UNHANDLED_SUBS_KEY = "subcomponents"


def export_icalendar_content(manager: Manager) -> str:
    calendar = export_icalendar(manager)
    bytes_content = calendar.to_ical()
    return bytes_content.decode("utf-8")


def export_icalendar(manager: Manager) -> icalendar.cal.Calendar:
    calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
    calendar.add("prodid", "-//Hanlendar//EN")

    allTasks: list[Task] = manager.getTasksAll()
    _LOGGER.info("creating events: %s", len(allTasks))
    for task_item in allTasks:
        _LOGGER.info("exporting task: %s %s", task_item.UID, task_item.title)
        ievent: icalendar.cal.Event = TaskSerialization.to_ical(task_item)
        calendar.add_component(ievent)

    allTodos = manager.getTodosAll()
    _LOGGER.info("creating todos: %s", len(allTodos))
    for todo_item in allTodos:
        _LOGGER.info("exporting todo: %s %s", todo_item.UID, todo_item.title)
        itodo: icalendar.cal.Todo = ToDoSerialization.to_ical(todo_item)

        calendar.add_component(itodo)

    ## export unhandled props
    write_unknown_props(calendar, manager.unknownProps)

    return calendar


## ===========================================================


def import_icalendar_content(manager: Manager, content: str):
    try:
        dangling_children = []
        extracted_ical = extract_ical(content)
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar.from_ical(extracted_ical)
        imported_items, children = import_icalendar(manager, calendar)
        dangling_children.extend(children)
    except ValueError as ex:
        _LOGGER.warning("unable to import calendar data: %s", ex)
        return None
    return imported_items, dangling_children


def import_icalendar(manager: Manager, calendar: icalendar.cal.Calendar) -> tuple[list[Task], list[Any]]:
    tasks: list[Task] = []
    dangling_children = []

    for component in calendar.subcomponents:
        if component.name == "VEVENT":
            imported_tasks, imported_dangling_children = TaskSerialization.from_ical(component, manager)
            tasks.extend(imported_tasks)
            dangling_children.extend(imported_dangling_children)
            continue

        if component.name == "VTODO":
            imported_tasks, imported_dangling_children = ToDoSerialization.from_ical(component, manager)
            tasks.extend(imported_tasks)
            dangling_children.extend(imported_dangling_children)
            continue

        ## unhandled items
        item = component.to_ical()
        subitems = manager.unknownProps.get(UNHANDLED_SUBS_KEY, [])
        subitems.append(item)
        manager.unknownProps[UNHANDLED_SUBS_KEY] = subitems

    return tasks, dangling_children


def extract_ical(content: str):
    cal_begin_pos = content.find("BEGIN:VCALENDAR")
    if cal_begin_pos < 0:
        return content
    END_SUB = "END:VCALENDAR"
    cal_end_pos = content.find(END_SUB, cal_begin_pos)
    if cal_end_pos < 0:
        return content
    cal_end_pos += len(END_SUB)
    return content[cal_begin_pos:cal_end_pos]


## =================================================================
## =================================================================


class PropsDict:

    def __init__(self):
        self.props: dict[str, Any] = {}

    def join(self, props: "PropsDict"):
        self.props = self.props | props.props

    def add(self, key, value):
        self.props[key] = value

    def add_prop(self, component, prop_key):
        prop_item = component.get(prop_key)
        if prop_item is None:
            return
        if isinstance(prop_item, list):
            data_list = [item.to_ical() for item in prop_item]
            self.props[prop_key] = data_list
        else:
            self.props[prop_key] = prop_item.to_ical()

    def add_props(self, component):
        for key, val in component.items():
            if isinstance(val, list):
                data_list = [item.to_ical() for item in val]
                self.props[key] = data_list
            else:
                self.props[key] = val.to_ical()

    def pop(self, key):
        return self.props.pop(key, None)


##
## Translation of task field to ical field
##
@unique
class TaskField(Enum):
    UID = "uid"
    SUMMARY = "summary"
    LOCATION = "location"
    URL = "url"
    DESCRIPTION = "description"
    CLASS = "class"
    STATUS = "status"

    DTSTAMP = "dtstamp"  ## create datetime
    DTSTART = "dtstart"
    DTEND = "dtend"
    CREATED = "created"
    LASTMODIFIED = "last-modified"
    SEQUENCE = "sequence"

    ## 'completed:' substring is converted in all fields in caldav, so it has to be postfixed prevent conversion
    COMPLETED = "x-hanlendar-completedx"
    PRIORITY = "priority"

    GROUP_PARENT = "x-hanlendar-parent"  ## uuid
    RECURRENCE = "x-hanlendar-recurrence"

    @classmethod
    def findByName(cls, name, defaultValue=None):
        for item in cls:
            if item.name == name:
                return item
        return defaultValue

    @classmethod
    def indexOf(cls, key):
        index = 0
        for item in cls:
            if item == key:
                return index
            if item.name == key:
                return index
            index = index + 1
        return -1


@unique
class RecurrentField(Enum):
    MODE = "x-hanlendar-recurrence-mode"
    STEP = "x-hanlendar-recurrence-step"
    ENDDATE = "x-hanlendar-recurrence-end-date"

    @classmethod
    def findByName(cls, name, defaultValue=None):
        for item in cls:
            if item.name == name:
                return item
        return defaultValue

    @classmethod
    def indexOf(cls, key):
        index = 0
        for item in cls:
            if item == key:
                return index
            if item.name == key:
                return index
            index = index + 1
        return -1


##
## Translation of task field to ical field
##
@unique
class ToDoField(Enum):
    UID = "uid"
    SUMMARY = "summary"
    LOCATION = "location"
    URL = "url"
    DESCRIPTION = "description"
    CLASS = "class"
    STATUS = "status"

    DTSTAMP = "dtstamp"  ## create datetime
    CREATED = "created"
    LASTMODIFIED = "last-modified"
    SEQUENCE = "sequence"

    ## 'completed:' substring is converted in all fields in caldav, so it has to be postfixed prevent conversion
    COMPLETED = "x-hanlendar-completedx"
    PRIORITY = "priority"

    GROUP_PARENT = "x-hanlendar-parent"  ## uuid of parent

    @classmethod
    def findByName(cls, name, defaultValue=None):
        for item in cls:
            if item.name == name:
                return item
        return defaultValue

    @classmethod
    def indexOf(cls, key):
        index = 0
        for item in cls:
            if item == key:
                return index
            if item.name == key:
                return index
            index = index + 1
        return -1


class TaskSerialization:

    # pylint: disable=R0914
    @staticmethod
    def from_ical(component: icalendar.cal.Component, manager):
        new_items = []
        dangling_children: list[tuple[Any, Any]] = []

        task: Task = manager.createEmptyTask()

        task.UID = get_ical_str(component, TaskField.UID)

        summary = get_ical_str(component, TaskField.SUMMARY)
        if summary is not None:
            task.title = f"{summary}"

        location = component.get(TaskField.LOCATION.value)
        if location is not None:
            task.location = f"{location}"

        url = component.get(TaskField.URL.value)
        if url is not None:
            task.url = f"{url}"

        task.description = get_ical_str(component, TaskField.DESCRIPTION)
        if task.description is None:
            task.description = ""
        task.description = task.description.replace("=0D=0A", "\n")

        task.class_prop = get_ical_str(component, TaskField.CLASS)
        if task.class_prop is None:
            task.class_prop = ""

        task.status = get_ical_str(component, TaskField.STATUS)
        if task.status is None:
            task.status = ""

        sequence = component.get(TaskField.SEQUENCE.value)
        if sequence is not None:
            task.sequence = int(sequence)

        created_date = get_ical_value_dt(component, TaskField.CREATED)
        task._createDate = created_date  # type: ignore[attr-defined]

        modified_date = get_ical_value_dt(component, TaskField.LASTMODIFIED)
        task._lastModifiedDate = modified_date  # type: ignore[attr-defined]

        start_date = get_ical_value_dt(component, TaskField.DTSTART)
        end_date = get_ical_value_dt(component, TaskField.DTEND)

        if start_date == end_date:
            start_date = None
        task.setOccurrence(start_date, end_date)

        task.completed = get_ical_value_int(component, TaskField.COMPLETED, 0)
        task.priority = get_ical_value_int(component, TaskField.PRIORITY, 5)

        ## restore reminders
        reminders_list, unhandled_alarms = ReminderSerialization.from_ical(component)
        for reminder in reminders_list:
            task.addReminder(reminder)
        if task.reminderList is None:
            task.reminderList = []

        ## restore recurrence
        task.recurrence, unhandled_recurrent = RecurrentSerialization.from_ical(component)

        unhandled_props = PropsDict()
        unhandled_props.add_props(component)
        unhandled_props.pop("RRULE")
        unhandled_props.pop("RDATE")
        unhandled_props.pop("EXDATE")
        for item in TaskField:
            prop_name = item.value.upper()
            unhandled_props.pop(prop_name)
        unhandled_props.join(unhandled_recurrent)
        unhandled_subs = unhandled_alarms
        for subitem in component.subcomponents:
            if subitem.name == "VALARM":
                continue
            ical_item = subitem.to_ical()
            unhandled_subs.append(ical_item)
        if unhandled_subs:
            unhandled_props.add(UNHANDLED_SUBS_KEY, unhandled_subs)
        task._unknown_props = unhandled_props.props  # type: ignore[attr-defined]

        parentUID = get_ical_str(component, TaskField.GROUP_PARENT)
        if parentUID is None:
            ## regular task
            addedTask = manager.addTask(task)
            new_items.append(addedTask)
            return (new_items, dangling_children)

        taskParent: Task = manager.findTaskByUID(parentUID)
        if taskParent is not None:
            ## add as subitem
            taskParent.addSubItem(task)
            new_items.append(task)
        else:
            ## invalid case -- parent still not added
            dangling_children.append((task, parentUID))

        return (new_items, dangling_children)

    @staticmethod
    def to_ical(task: Task) -> icalendar.cal.Event:
        ievent: icalendar.cal.Event = icalendar.cal.Event()

        curr_time = datetime.datetime.now(tz=datetime.timezone.utc)
        curr_time = curr_time.replace(tzinfo=None)
        ievent.add("DTSTAMP", curr_time)

        ievent.add(TaskField.UID.value, task.UID)
        ievent.add(TaskField.SUMMARY.value, task.title)

        if task.location:
            ievent.add(TaskField.LOCATION.value, task.location)

        if task.url:
            ievent.add(TaskField.URL.value, task.url)

        if task.description:
            ievent.add(TaskField.DESCRIPTION.value, task.description)

        if task.class_prop:
            ievent.add(TaskField.CLASS.value, task.class_prop)

        if task.status:
            ievent.add(TaskField.STATUS.value, task.status)

        if task.sequence > 0:
            ievent.add(TaskField.SEQUENCE.value, task.sequence)

        value_dt = convert_to_ical_dt(task.createDateTime)
        if value_dt is not None:
            ievent.add(TaskField.CREATED.value, value_dt)

        value_dt = convert_to_ical_dt(task.lastModifiedDateTime)
        ievent.add(TaskField.LASTMODIFIED.value, value_dt)

        start_date_time = None
        if task.startDateTime is not None:
            start_date_time = convert_to_ical_dt(task.startDateTime)
        else:
            ## DTSTART field cannot be None, so use end date
            start_date_time = convert_to_ical_dt(task.dueDateTime)

        end_date_time = convert_to_ical_dt(task.dueDateTime)
        if task.isAllDay():
            ievent.add(TaskField.DTSTART.value, start_date_time.date())
            ievent.add(TaskField.DTEND.value, end_date_time.date())
        else:
            if start_date_time:
                ievent.add(TaskField.DTSTART.value, start_date_time.astimezone(tz=datetime.timezone.utc))
            if end_date_time:
                ievent.add(TaskField.DTEND.value, end_date_time.astimezone(tz=datetime.timezone.utc))

        if task.completed != 0:
            ievent.add(TaskField.COMPLETED.value, task.completed)

        if task.priority != 5:
            ievent.add(TaskField.PRIORITY.value, task.priority)

        taskParent = task.getParent()
        if taskParent is not None:
            ievent.add(TaskField.GROUP_PARENT.value, taskParent.UID)

        ## store reminders
        reminderList = task.reminderList
        if reminderList is None:
            reminderList = []
        for reminder in reminderList:
            subcomponent = ReminderSerialization.to_ical(reminder)
            if subcomponent is None:
                continue
            ievent.add_component(subcomponent)

        ## store recurrent
        RecurrentSerialization.to_ical(task.recurrence, ievent)

        write_unknown_props(ievent, task.unknownProps)

        return ievent


class ToDoSerialization:

    @staticmethod
    def from_ical(component: icalendar.cal.Component, manager):
        new_items = []
        dangling_children: list[Any] = []

        todo: LocalToDo = manager.createEmptyToDo()

        todo.UID = get_ical_str(component, ToDoField.UID)

        summary = get_ical_str(component, ToDoField.SUMMARY)
        if summary is not None:
            todo.title = f"{summary}"

        location = component.get(ToDoField.LOCATION.value)
        if location is not None:
            todo.location = f"{location}"

        url = component.get(ToDoField.URL.value)
        if url is not None:
            todo.url = f"{url}"

        todo.description = get_ical_str(component, ToDoField.DESCRIPTION)
        if todo.description is None:
            todo.description = ""
        todo.description = todo.description.replace("=0D=0A", "\n")

        todo.class_prop = get_ical_str(component, ToDoField.CLASS)
        if todo.class_prop is None:
            todo.class_prop = ""

        todo.status = get_ical_str(component, ToDoField.STATUS)
        if todo.status is None:
            todo.status = ""

        sequence = component.get(ToDoField.SEQUENCE.value)
        if sequence is not None:
            todo.sequence = int(sequence)

        created_date = get_ical_value_dt(component, ToDoField.CREATED)
        todo._createDate = created_date

        modified_date = get_ical_value_dt(component, ToDoField.LASTMODIFIED)
        todo._lastModifiedDate = modified_date

        todo.completed = get_ical_value_int(component, ToDoField.COMPLETED, 0)
        todo.priority = get_ical_value_int(component, ToDoField.PRIORITY, 5)

        # ## restore reminders
        # reminders_list = ReminderSerialization.from_ical(component)
        # for reminder in reminders_list:
        #     task.addReminder(reminder)
        # if task.reminderList is None:
        #     task.reminderList = []

        unhandled_props = PropsDict()
        unhandled_props.add_props(component)
        for item in ToDoField:
            prop_name = item.value.upper()
            unhandled_props.pop(prop_name)
        unhandled_subs = []
        for subitem in component.subcomponents:
            ical_item = subitem.to_ical()
            unhandled_subs.append(ical_item)
        if unhandled_subs:
            unhandled_props.add(UNHANDLED_SUBS_KEY, unhandled_subs)
        todo._unknown_props = unhandled_props.props

        parentUID = get_ical_str(component, ToDoField.GROUP_PARENT)
        if parentUID is None:
            ## regular todo
            added_item = manager.addToDo(todo)
            new_items.append(added_item)
            return (new_items, dangling_children)

        taskParent: LocalToDo = manager.findTaskByUID(parentUID)
        if taskParent is not None:
            ## add as subitem
            taskParent.addSubItem(todo)
            new_items.append(todo)
        else:
            ## invalid case -- parent still not added
            dangling_children.append((todo, parentUID))

        return (new_items, dangling_children)

    @staticmethod
    def to_ical(todo: LocalToDo) -> icalendar.cal.Todo:
        itodo: icalendar.cal.Todo = icalendar.cal.Todo()

        curr_time = datetime.datetime.now(tz=datetime.timezone.utc)
        curr_time = curr_time.replace(tzinfo=None)
        itodo.add("DTSTAMP", curr_time)

        value_dt = convert_to_ical_dt(todo.createDateTime)
        itodo.add(ToDoField.CREATED.value, value_dt)

        value_dt = convert_to_ical_dt(todo.lastModifiedDateTime)
        itodo.add(ToDoField.LASTMODIFIED.value, value_dt)

        itodo.add(ToDoField.UID.value, todo.UID)
        itodo.add(ToDoField.SUMMARY.value, todo.title)

        if todo.location:
            itodo.add(ToDoField.LOCATION.value, todo.location)

        if todo.url:
            itodo.add(ToDoField.URL.value, todo.url)

        if todo.description:
            itodo.add(ToDoField.DESCRIPTION.value, todo.description)

        if todo.class_prop:
            itodo.add(ToDoField.CLASS.value, todo.class_prop)

        if todo.status:
            itodo.add(ToDoField.STATUS.value, todo.status)

        if todo.sequence > 0:
            itodo.add(ToDoField.SEQUENCE.value, todo.sequence)

        if todo.completed != 0:
            itodo.add(ToDoField.COMPLETED.value, todo.completed)

        if todo.priority != 5:
            itodo.add(ToDoField.PRIORITY.value, todo.priority)

        taskParent = todo.getParent()
        if taskParent is not None:
            itodo.add(ToDoField.GROUP_PARENT.value, taskParent.UID)

        # TODO: activate reminders
        # ## store reminders
        # reminderList = todo.reminderList
        # if reminderList is None:
        #     reminderList = []
        # for reminder in reminderList:
        #     subcomponent = ReminderSerialization.to_ical(reminder)
        #     if subcomponent is None:
        #         continue
        #     itodo.add_component(subcomponent)

        write_unknown_props(itodo, todo.unknownProps)

        return itodo


## info:
## https://icalendar.org/iCalendar-RFC-5545/3-6-6-alarm-component.html
class ReminderSerialization:

    @staticmethod
    def from_ical(component: icalendar.cal.Component) -> tuple[list[Reminder], list[Any]]:
        ret_list: list[Reminder] = []
        unhandled_subs = []

        for subcomponent in component.subcomponents:
            if subcomponent.name != "VALARM":
                continue
            alarm_props = subcomponent.items()
            if not alarm_props:
                ## no props - sometimes component has empty alarm
                continue

            reminder = None
            alarm_action = subcomponent.get("ACTION")

            if alarm_action == "DISPLAY":
                reminder = ReminderSerialization.from_display(subcomponent)
            elif alarm_action == "AUDIO":
                reminder = ReminderSerialization.from_audio(subcomponent)
            elif alarm_action == "PROCEDURE":
                reminder = ReminderSerialization.from_procedure(subcomponent)
            else:
                _LOGGER.warning("unahndled Alarm ACTION: '%s'", alarm_action)

            if reminder:
                ret_list.append(reminder)
            else:
                ical_item = component.to_ical()
                unhandled_subs.append(ical_item)

        return ret_list, unhandled_subs

    @staticmethod
    def from_display(component: icalendar.cal.Alarm) -> Reminder:
        alarm_props = component.items()

        reminder = Reminder()
        reminder.action = component.get("ACTION")
        reminder.description = component.get("DESCRIPTION")

        unknown_props = {}

        for prop_name, prop_val in alarm_props:
            if prop_name in ("ACTION", "DESCRIPTION"):
                ## already handled
                continue

            if prop_name == "TRIGGER":
                if prop_val.params is None:
                    _LOGGER.warning("unhandled alarm case - no properties: %s", component)
                    return None
                related = prop_val.params.get("RELATED")
                if related:
                    if related == "START":
                        reminder.related = RelatedType.START
                    elif related == "END":
                        reminder.related = RelatedType.END
                    else:
                        _LOGGER.warning("unhandled alarm case - unknown RELATED: %s", component)
                        return None

                reminder.timeOffset = prop_val.dt
                continue

            if prop_name not in (" X-EVOLUTION-ALARM-UID"):
                _LOGGER.warning("unhandled alarm property: %s", prop_name)

            unknown_props[prop_name] = prop_val.to_ical()

        reminder.unknownProps = unknown_props
        return reminder

    @staticmethod
    def from_audio(component: icalendar.cal.Alarm) -> Reminder:
        return ReminderSerialization.from_display(component)

    @staticmethod
    def from_procedure(component: icalendar.cal.Alarm) -> Reminder:
        return ReminderSerialization.from_display(component)

    @staticmethod
    def to_ical(reminder: Reminder) -> icalendar.cal.Alarm:
        action = reminder.get_action()
        if action in ("DISPLAY", "AUDIO", "PROCEDURE"):
            ialarm: icalendar.cal.Alarm = icalendar.cal.Alarm()

            ialarm["ACTION"] = action
            description = reminder.get_description()
            if description:
                ialarm["DESCRIPTION"] = reminder.get_description()
            trigger_props = None
            if reminder.related:
                trigger_props = {"RELATED": reminder.get_related_value()}
            ialarm.add("TRIGGER", reminder.timeOffset, parameters=trigger_props)

            write_unknown_props(ialarm, reminder.unknownProps)
            return ialarm

        _LOGGER.warning("unhandled action: %s", action)
        return None


## info:
## https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html
class RecurrentSerialization:

    @staticmethod
    def from_ical(component: icalendar.cal.Component) -> tuple[Recurrent, PropsDict]:
        rrule: icalendar.prop.vRecur = component.get("RRULE")

        if rrule is None:
            return RecurrentSerialization.get_unhandled(component)

        recurrence = Recurrent()
        prop_freq_list = rrule.get("FREQ")
        if not prop_freq_list:
            return RecurrentSerialization.get_unhandled(component)
        if len(prop_freq_list) > 1:
            _LOGGER.warning("unable to handle RRULE: %s", rrule)
            return RecurrentSerialization.get_unhandled(component)

        prop_freq = prop_freq_list[0]
        freq_dict = {
            "DAILY": RepeatType.DAILY,
            "WEEKLY": RepeatType.WEEKLY,
            "MONTHLY": RepeatType.MONTHLY,
            "YEARLY": RepeatType.YEARLY,
        }
        recurrence.mode = freq_dict.get(prop_freq, RepeatType.NEVER)

        recurrence.occurenceMode = RepeatUntilMode.FOREVER
        prop_count_list = rrule.get("COUNT", [])
        if prop_count_list:
            if len(prop_count_list) > 1:
                _LOGGER.warning("unable to handle RRULE: %s", rrule)
                return RecurrentSerialization.get_unhandled(component)
            recurrence.occurenceMode = RepeatUntilMode.OCCURENCES
            recurrence.occurences = prop_count_list[0]
            recurrence.endDate = None

        prop_until_list = rrule.get("UNTIL", [])
        if prop_until_list:
            if len(prop_until_list) > 1:
                _LOGGER.warning("unable to handle RRULE: %s", rrule)
                return RecurrentSerialization.get_unhandled(component)
            recurrence.occurenceMode = RepeatUntilMode.UNTIL_DATE
            recurrence.occurences = None
            recurrence.endDate = prop_until_list[0]

        prop_interval_list = rrule.get("INTERVAL", [])
        if prop_interval_list:
            if len(prop_interval_list) > 1:
                _LOGGER.warning("unable to handle RRULE: %s", rrule)
                return RecurrentSerialization.get_unhandled(component)
            recurrence.every = prop_interval_list[0]

        if recurrence.mode == RepeatType.WEEKLY:
            ## WEEKLY: BYDAY=SU,MO,TU,WE,TH,FR,SA
            prop_byday_list = rrule.get("BYDAY")
            recurrence.weekday = convert_weekday_to_index(prop_byday_list)

        elif recurrence.mode == RepeatType.MONTHLY:
            prop_byday_list = rrule.get("BYDAY")
            prop_bymonthday_list = rrule.get("BYMONTHDAY")
            if prop_byday_list and prop_bymonthday_list:
                _LOGGER.warning("invalid RRULE: %s", rrule)
                return RecurrentSerialization.get_unhandled(component)
            if prop_byday_list:
                ## MONTHLY: BYDAY=1SU,1WE,2SU,3FR,4TU,5TU,-1WE
                weekday_list, monthday_list = convert_monthday_to_index(prop_byday_list)
                recurrence.weekday = weekday_list
                recurrence.monthweek = monthday_list
            if prop_bymonthday_list:
                ## if there is no day in month, then no event (eg. there is no 30th of February)
                ## MONTHLY: BYMONTHDAY=7,30
                recurrence.monthday = [int(day) for day in prop_bymonthday_list]

        elif recurrence.mode == RepeatType.YEARLY:
            prop_bymonth_list = rrule.get("BYMONTH")
            prop_byday_list = rrule.get("BYDAY")
            prop_bymonthday_list = rrule.get("BYMONTHDAY")
            if prop_byday_list and prop_bymonthday_list:
                _LOGGER.warning("invalid RRULE: %s", rrule)
                return RecurrentSerialization.get_unhandled(component)
            ## YEARLY: BYMONTH=11;BYDAY=1SU,1WE,2SU,3FR,4TU,5TU,-1WE
            recurrence.month = [int(month) for month in prop_bymonth_list]
            weekday_list, monthday_list = convert_monthday_to_index(prop_byday_list)
            recurrence.weekday = weekday_list
            recurrence.monthweek = monthday_list
            ## YEARLY: BYMONTH=11;BYMONTHDAY=7,30
            recurrence.monthday = [int(day) for day in prop_bymonthday_list]

        unhandled_props = PropsDict()

        rdate = component.get("RDATE")
        if rdate is not None:
            # TODO: implement
            _LOGGER.warning("RDATE is not supported")
            unhandled_props.add_prop(component, "RDATE")

        exdate = component.get("EXDATE")
        if exdate is not None:
            exdate_list = []
            if not isinstance(exdate, list):
                exdate_list.append(exdate)
            else:
                exdate_list = exdate
            ex_dates = []
            for item in exdate_list:
                ex_dates.extend(item.dts)
            date_list = [item.dt for item in ex_dates]
            recurrence.exception_dates = date_list

        return (recurrence, unhandled_props)

    @staticmethod
    def get_unhandled(component: icalendar.cal.Component):
        unhandled_props = PropsDict()
        unhandled_props.add_prop(component, "RRULE")
        unhandled_props.add_prop(component, "RDATE")
        unhandled_props.add_prop(component, "EXDATE")
        return (None, unhandled_props)

    @staticmethod
    def to_ical(recurrence: Recurrent, component: icalendar.cal.Component):
        if recurrence is None:
            return

        rrule = icalendar.prop.vRecur()

        freq_dict = {
            RepeatType.DAILY: "DAILY",
            RepeatType.WEEKLY: "WEEKLY",
            RepeatType.MONTHLY: "MONTHLY",
            RepeatType.YEARLY: "YEARLY",
        }
        freq_mode = freq_dict.get(recurrence.mode)
        if freq_mode is not None:
            rrule["FREQ"] = freq_mode
        else:
            _LOGGER.warning("unhandled mode: %s", recurrence.mode)
            return

        if recurrence.occurenceMode is None:
            if recurrence.endDate is not None:
                rrule["UNTIL"] = recurrence.endDate
        elif recurrence.occurenceMode == RepeatUntilMode.FOREVER:
            ## do nothing
            pass
        elif recurrence.occurenceMode == RepeatUntilMode.OCCURENCES:
            rrule["COUNT"] = recurrence.occurences
        elif recurrence.occurenceMode == RepeatUntilMode.UNTIL_DATE:
            rrule["UNTIL"] = recurrence.endDate
        else:
            _LOGGER.warning("unhandled occurrence: %s", recurrence.occurenceMode)
            return

        if recurrence.every > 0:
            rrule["INTERVAL"] = recurrence.every

        if recurrence.mode == RepeatType.WEEKLY:
            ## WEEKLY: BYDAY=SU,MO,TU,WE,TH,FR,SA
            rrule["BYDAY"] = convert_index_to_weekday(recurrence.weekday)

        elif recurrence.mode == RepeatType.MONTHLY:
            if recurrence.weekday and recurrence.monthweek:
                ## MONTHLY: BYDAY=1SU,1WE,2SU,3FR,4TU,5TU,-1WE
                rrule["BYDAY"] = convert_index_to_monthday(recurrence.weekday, recurrence.monthweek)
            if recurrence.monthday:
                ## if there is no day in month, then no event (eg. there is no 30th of February)
                ## MONTHLY: BYMONTHDAY=7,30
                rrule["BYMONTHDAY"] = ",".join(recurrence.monthday)  # type: ignore[arg-type]

        elif recurrence.mode == RepeatType.YEARLY:
            if recurrence.weekday and recurrence.monthweek:
                ## YEARLY: BYMONTH=11;BYDAY=1SU,1WE,2SU,3FR,4TU,5TU,-1WE
                rrule["BYMONTH"] = recurrence.month
                rrule["BYDAY"] = convert_index_to_monthday(recurrence.weekday, recurrence.monthweek)
            if recurrence.monthday:
                ## YEARLY: BYMONTH=11;BYMONTHDAY=7,30
                rrule["BYMONTH"] = recurrence.month
                rrule["BYMONTHDAY"] = recurrence.monthday

        component.add("RRULE", rrule)

        exdates = list(recurrence.exception_dates)
        for item in exdates:
            component.add("EXDATE", item)


def convert_weekday_to_index(weekday_list) -> list[int]:
    weekday_index_dict = {
        "MO": 0,
        "TU": 1,
        "WE": 2,
        "TH": 3,
        "FR": 4,
        "SA": 5,
        "SU": 6,
    }
    ret_list = []
    for day in weekday_list:
        index = weekday_index_dict.get(day)
        if index is None:
            _LOGGER.warning("unhandled week day: %s", day)
            continue
        ret_list.append(index)
    return ret_list


def convert_index_to_weekday(index_list) -> list[str]:
    weekday_index_dict = {
        0: "MO",
        1: "TU",
        2: "WE",
        3: "TH",
        4: "FR",
        5: "SA",
        6: "SU",
    }
    ret_list = []
    for index in index_list:
        day = weekday_index_dict.get(index)
        if day is None:
            _LOGGER.warning("unhandled week index: %s", index)
            continue
        ret_list.append(day)
    return ret_list


def convert_monthday_to_index(monthday_list) -> tuple[list[int], list[int]]:
    ret_weekday_list = []
    ret_monthday_list = []
    for day in monthday_list:
        match = re.match(r"(-?\d+)(.*)", day)
        number = int(match.group(1))
        name = match.group(2)
        day_index = convert_weekday_to_index([name])
        if not day_index:
            _LOGGER.warning("unhandled month day: %s", day)
            continue
        ret_weekday_list.append(day_index[0])
        ret_monthday_list.append(number)
    return (ret_weekday_list, ret_monthday_list)


def convert_index_to_monthday(weekday_list: list[int], monthday_list: list[int]) -> list[str]:
    weekday_names: list[str] = convert_index_to_weekday(weekday_list)
    return [f"{day_name}{week_index}" for day_name, week_index in zip(monthday_list, weekday_names)]


def write_unknown_props(component, props_dict):
    if not props_dict:
        return
    type_factory = TypesFactory()
    for key, item in props_dict.items():
        if key != UNHANDLED_SUBS_KEY:
            item_list = item if isinstance(item, list) else [item]
            for sub_item in item_list:
                decoded_item = sub_item.decode("utf-8")
                desired_item = type_factory.from_ical(key, decoded_item)
                component.add(key, desired_item)
            continue

        ## subcomponents
        for subitem in item:
            decoded_item = subitem.decode("utf-8")
            isubcomponent: icalendar.cal.Component = icalendar.cal.Component.from_ical(decoded_item)
            component.add_component(isubcomponent)


## =================================================================


def convert_to_ical_dt(dt_value):
    return dt_value


def convert_to_date(value_string: str):
    try:
        ## format: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        date_time_obj = datetime.datetime.strptime(value_string, "%Y-%m-%d")
        return date_time_obj.date()
    except Exception:  # pylint: disable=W0718
        return None


###
def set_ical_list(component, field: Union[Enum, str], values_list, value_extractor=None):
    if values_list is None:
        return
    if len(values_list) < 1:
        return

    data_list = []
    for item in values_list:
        value = item
        if value_extractor:
            value = value_extractor(value)
        data_list.append(value)

    field_name = field
    if isinstance(field, Enum):
        field_name = field.value
    component.set_inline(field_name, data_list)


###
def get_ical_str(component, field: Enum):
    val = component.get(field.value)
    if val is None:
        return None
    return str(val)


###
def get_ical_value_dt(component, field: Enum):
    value_raw = component.get(field.value)
    if value_raw is None:
        return None
    value_type = value_raw.params.get("VALUE")
    if value_type is None:
        valueDate = value_raw.dt
        return valueDate.astimezone()  ## convert to local timezone
    if value_type == "DATE":
        value_date: datetime.date = value_raw.dt
        return datetime.datetime(value_date.year, value_date.month, value_date.day)
    _LOGGER.warning("unhandled ical date type: %s", value_type)
    return None


###
def get_ical_value_int(component, field: Enum, defaultValue):
    try:
        value_str = get_ical_str(component, field)
        return int(value_str)
    # ruff: noqa: S110
    except Exception:  # pylint: disable=W0718 # nosec
        pass
    return defaultValue


###
def get_ical_list(component, field: Union[Enum, str], value_converter=None):
    field_name = field
    if isinstance(field, Enum):
        field_name = field.value

    if component.has_key(field_name) is False:
        return None
    raw_list = component.get_inline(field_name)
    if raw_list is None:
        return None
    if len(raw_list) < 1:
        return None

    #     print( "xxxxxxxxxx:", raw_list )
    retList = []
    for item in raw_list:
        value = item.decode("utf-8")
        if value_converter is not None:
            value = value_converter(value)
        retList.append(value)
    return retList


def reminder_from_string(time_delta: str):
    delta = timedelta_from_string(time_delta)
    if delta is not None:
        return Reminder(timeOffset=delta)

    reminder = Reminder.from_timedelta_string(time_delta)
    if reminder is not None:
        return reminder

    _LOGGER.warning("unable to convert time delta: '%s'", time_delta)
    return None


def timedelta_from_string(time_delta: str) -> timedelta:
    if time_delta == "1 day":
        return timedelta(days=1)

    matched = re.search(r"(\d+)\s+days", time_delta)
    if matched:
        grp = matched.group(1)
        days_number = int(grp)
        return timedelta(days=days_number)

    return None


## =================================================================
## =================================================================


###
def get_ical_dict(component, field: Union[Enum, str], _value_converter=None):
    field_name = field
    if isinstance(field, Enum):
        field_name = field.value

    if component.has_key(field_name) is False:
        return None
    raw_list = component.get(field_name)
    if raw_list is None:
        return None
    raw_params = raw_list.params
    if raw_params is None:
        return None
    if len(raw_params) < 1:
        return None
    return dict(raw_params.items())


###
def set_ical_dict(
    component: icalendar.cal.Component,
    field: Union[Enum, str],
    value,
    values_dict,
    _value_extractor=None,
):
    if values_dict is None:
        return
    if len(values_dict) < 1:
        return
    field_name = field
    if isinstance(field, Enum):
        field_name = field.value
    component.add(field_name, value, parameters=values_dict)


## =================================================================


def replace_line(content, line_prefix, new_content, *, replace_whole_line=False, element_index=None):
    lines = content.splitlines()
    counter = element_index
    for i, line in enumerate(lines):
        if line.startswith(line_prefix):
            if element_index is not None:
                counter -= 1
                if counter == -1:
                    if replace_whole_line is False:
                        lines[i] = f"{line_prefix}{new_content}"
                    else:
                        lines[i] = new_content
            elif replace_whole_line is False:
                lines[i] = f"{line_prefix}{new_content}"
            else:
                lines[i] = new_content
    return "\n".join(lines) + "\n"


def remove_line(content, line_prefix, element_index=None):
    lines = content.splitlines()
    out_lines = []
    if element_index is None:
        out_lines = [line for line in lines if not line.startswith(line_prefix)]
    else:
        counter = element_index
        for line in lines:
            if line.startswith(line_prefix):
                counter -= 1
                if counter == -1:
                    continue
            out_lines.append(line)
    return "\n".join(out_lines) + "\n"


def sort_ical_content(content):
    lines = content.splitlines()
    sorted_lines = sort_ical_list(lines)
    return "\n".join(sorted_lines) + "\n"


# def sort_ical_list(content_lines):
#     if not content_lines:
#         return []

# start_index = find_starting_index(content_lines, "BEGIN:")
# end_index = find_ending_index(content_lines, "END:")
# if start_index < 0 and end_index < 0:
#     return sorted(content_lines)
#
# props_lines = content_lines[:start_index] + content_lines[end_index + 1 :]
# props_sorted = sort_ical_list(props_lines)
#
# sub_lines = content_lines[start_index + 1 : end_index]
# sub_sorted = sort_ical_list(sub_lines)
#
# return [*props_sorted, content_lines[start_index], *sub_sorted, content_lines[end_index]]


def sort_ical_list(content_lines):
    if not content_lines:
        return []

    ## build tree
    ret_tree: dict[Any, Any] = {"start": None, "items": [], "end": None}
    item_stack = [ret_tree]
    for line in content_lines:
        curr_item = item_stack[-1]
        if line.startswith("BEGIN:"):
            new_item = {"start": line, "items": [], "end": None}
            items = curr_item["items"]
            items.append(new_item)
            item_stack.append(new_item)
            continue
        if line.startswith("END:"):
            curr_item["end"] = line
            items = curr_item["items"]
            items = _sort_ical_tree_list(items)
            curr_item["items"] = items
            item_stack.pop()
            continue
        items = curr_item["items"]
        items.append(line)

    items = ret_tree["items"]
    items = _sort_ical_tree_list(items)
    ret_tree["items"] = items

    return _ical_tree_to_list(items)


def _sort_ical_tree_list(tree_list):
    props_list = []
    sub_list = []
    for item in tree_list:
        if isinstance(item, dict):
            sub_list.append(item)
        else:
            props_list.append(item)
    props_list.sort()
    sub_list.sort(key=lambda tree_item: tree_item["start"])
    return [*props_list, *sub_list]


def _ical_tree_to_list(ical_tree_list):
    content_list = []
    for item in ical_tree_list:
        if isinstance(item, dict):
            content_list.append(item["start"])
            items = item["items"]
            subcontent = _ical_tree_to_list(items)
            content_list.extend(subcontent)
            content_list.append(item["end"])
        else:
            content_list.append(item)
    return content_list


def find_starting_index(content_list, line_start):
    for i, item in enumerate(content_list):
        if item.startswith(line_start):
            return i
    return -1


def find_ending_index(content_list, line_start):
    found = -1
    for i, item in enumerate(content_list):
        if item.startswith(line_start):
            found = i
    return found


def index_from_end(content_list, content):
    # reverse the list and find index in the reversed version
    rev_index = content_list[::-1].index(content)
    return len(content_list) - 1 - rev_index
