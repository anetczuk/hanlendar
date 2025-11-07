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

import logging
import datetime
from datetime import timedelta
import re
import icalendar

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.task import TaskField, Task
from hanlendar.domainmodel.recurrent import Recurrent, RepeatType, RecurrentField
from hanlendar.domainmodel.reminder import Reminder


_LOGGER = logging.getLogger(__name__)


##
## Translation of task field to ical field
##
ICAL_TASK_FIELD_DICT = {
    TaskField.UID: "uid",
    TaskField.SUMMARY: "summary",
    TaskField.DESCRIPTION: "description",
    # TaskField.LOCATION:      'location',
    TaskField.DTSTART: "dtstart",
    TaskField.DTEND: "dtend",
    ## 'completed:' substring is converted in all fields in caldav, so it has to be postfixed prevent conversion
    TaskField.COMPLETED: "x-hanlendar-completedx",
    TaskField.PRIORITY: "priority",
    TaskField.GROUP_PARENT: "x-hanlendar-parent",  ## uuid
    TaskField.RECURRENCE: "x-hanlendar-recurrence",
    TaskField.REMINDERS: "x-hanlendar-reminders",  ## comma separated list of 'timedelta' values
}


ICAL_RECURR_FIELD_DICT = {
    RecurrentField.MODE: "x-hanlendar-recurrence-mode",
    RecurrentField.STEP: "x-hanlendar-recurrence-step",
    RecurrentField.ENDDATE: "x-hanlendar-recurrence-end-date",
}


def export_icalendar_content(manager: Manager) -> str:
    calendar = export_icalendar(manager)
    bytesContent = calendar.to_ical()
    return bytesContent.decode("utf-8")
    # return str( bytesContent )


def export_icalendar(manager: Manager) -> icalendar.cal.Calendar:
    calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()

    allTasks = manager.getTasksAll()
    #     if len(allTasks) > 30:
    #         allTasks = allTasks[0:30]
    _LOGGER.info("creating events: %s", len(allTasks))
    ## task: Task = None
    for task in allTasks:
        _LOGGER.info("exporting task: %s %s", task.UID, task.title)

        ievent: icalendar.cal.Component = icalendar.cal.Event()

        set_ical_value(ievent, TaskField.UID, task.UID)
        set_ical_value(ievent, TaskField.SUMMARY, task.title)
        ## no location

        if task.startDateTime is not None:
            set_ical_value(ievent, TaskField.DTSTART, task.startDateTime)
        else:
            ## DTSTART field cannot be None, so use end date
            set_ical_value(ievent, TaskField.DTSTART, task.dueDateTime)

        set_ical_value(ievent, TaskField.DTEND, task.dueDateTime)
        set_ical_value(ievent, TaskField.DESCRIPTION, task.description)
        set_ical_value(ievent, TaskField.COMPLETED, task.completed)

        taskParent = task.getParent()
        if taskParent is not None:
            set_ical_value(ievent, TaskField.GROUP_PARENT, taskParent.UID)

        recurrence = task.recurrence
        if recurrence is not None:
            ievent[ICAL_RECURR_FIELD_DICT[RecurrentField.MODE]] = str(recurrence.mode.name)
            ievent[ICAL_RECURR_FIELD_DICT[RecurrentField.STEP]] = str(recurrence.every)
            ievent[ICAL_RECURR_FIELD_DICT[RecurrentField.ENDDATE]] = str(recurrence.endDate)

        reminderList = task.reminderList
        set_ical_list(ievent, TaskField.REMINDERS, reminderList, value_extractor=lambda rem: str(rem.timeOffset))

        calendar.add_component(ievent)

    return calendar


def import_icalendar_content(manager: Manager, content: str):
    try:
        dangling_children = []
        extracted_ical = extract_ical(content)
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar.from_ical(extracted_ical)
        tasks, children = import_icalendar(manager, calendar)
        dangling_children.extend(children)
        for task in tasks:
            if task.reminderList is None:
                continue
            if len(task.reminderList) > 0:
                continue
            task.addReminderDays(1)
    except ValueError as ex:
        _LOGGER.warning("unable to import calendar data: %s", ex)
        return None
    return tasks, dangling_children


def import_icalendar(manager: Manager, calendar: icalendar.cal.Calendar):
    tasks = []
    dangling_children = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            task: Task = manager.createEmptyTask()

            # TODO: class, created, last-modified, sequence, transp
            task.UID = get_ical_str(component, TaskField.UID)

            summary = get_ical_str(component, TaskField.SUMMARY)
            location = component.get("location")
            if location is not None:
                task.title = f"{summary}, {location}"
            else:
                task.title = f"{summary}"

            task.description = get_ical_str(component, TaskField.DESCRIPTION)
            if task.description is None:
                task.description = ""
            task.description = task.description.replace("=0D=0A", "\n")

            start_date = get_ical_value_dt(component, TaskField.DTSTART)
            end_date = get_ical_value_dt(component, TaskField.DTEND)

            if start_date == end_date:
                start_date = None
            task.setOccurrence(start_date, end_date)

            task.completed = get_ical_value_int(component, TaskField.COMPLETED, 0)

            try:
                recurrMode = component.get(ICAL_RECURR_FIELD_DICT[RecurrentField.MODE])
                recurrMode = RepeatType.findByName(recurrMode)

                recurrStep = component.get(ICAL_RECURR_FIELD_DICT[RecurrentField.STEP])
                recurrStep = int(recurrStep)

                recurrEnd = component.get(ICAL_RECURR_FIELD_DICT[RecurrentField.ENDDATE])
                recurrEnd = convert_to_date(recurrEnd)

                task.recurrence = Recurrent(recurrMode, recurrStep, recurrEnd)

            # ruff: noqa: S110
            except Exception:  # pylint: disable=W0718 # nosec
                pass

            try:
                task.reminderList = get_ical_list(
                    component,
                    TaskField.REMINDERS,
                    value_converter=reminder_from_string,
                )
                if task.reminderList is not None:
                    task.reminderList = [item for item in task.reminderList if item is not None]
            except Exception:  # as ex:
                _LOGGER.warning("unable to import remainder list: %s %s", task.title, task.dueDateTime)
                raise

            parentUID = get_ical_str(component, TaskField.GROUP_PARENT)
            if parentUID is None:
                ## regular task
                addedTask = manager.addTask(task)
                tasks.append(addedTask)
                continue
            taskParent: Task = manager.findTaskByUID(parentUID)
            if taskParent is not None:
                ## add as subitem
                taskParent.addSubItem(task)
                tasks.append(task)
            else:
                ## invalid case -- parent still not added
                dangling_children.append((task, parentUID))

    return tasks, dangling_children


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


def fix_dangling_tasks(manager: Manager, dangling_children):
    ## handle dangling children
    while len(dangling_children) > 0:
        handled = False
        for i in range(len(dangling_children) - 1, -1, -1):
            child, parent_uid = dangling_children[i]
            taskParent: Task = manager.findTaskByUID(parent_uid)
            if taskParent is not None:
                ## add as subitem
                taskParent.addSubItem(child)
                del dangling_children[i]
                handled = True
        if handled is True:
            continue

        #         _LOGGER.warning( "not all children could be handled properly" )
        #
        #         print( "dangling children:" )
        #         for item in dangling_children:
        #             child, parent_uuid = item
        #             print( "item:", child.UID, parent_uuid )
        #         print( "tasks:" )
        #         for item in manager.getTasksAll():
        #             print( "item:", item.UID )

        ## add remaining dangling children as regular tasks
        for item in dangling_children:
            child, _other = item
            manager.addTask(child)
        break


## ========================================================


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


###
def get_ical_dict(component, field: TaskField, _value_converter=None):
    field_name = ICAL_TASK_FIELD_DICT.get(field, field)
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
def get_ical_list(component, field: TaskField, value_converter=None):
    field_name = ICAL_TASK_FIELD_DICT.get(field, field)
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


###
def get_ical_value_int(component, field: TaskField, defaultValue):
    try:
        value_str = get_ical_str(component, field)
        return int(value_str)
    # ruff: noqa: S110
    except Exception:  # pylint: disable=W0718 # nosec
        pass
    return defaultValue


###
def get_ical_value_date(component, field: TaskField):
    value_str = get_ical_str(component, field)
    return convert_to_date(value_str)


def convert_to_date(value_string: str):
    try:
        ## format: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        date_time_obj = datetime.datetime.strptime(value_string, "%Y-%m-%d")
        return date_time_obj.date()
    except Exception:  # pylint: disable=W0718
        return None


def convert_to_datetime(value_string: str):
    try:
        ## format: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        return datetime.datetime.strptime(value_string, "%Y-%m-%d %H:%M:%S")
    except Exception:  # pylint: disable=W0718
        return None


###
def get_ical_value_dt(component, field: TaskField):
    value_raw = get_ical_value(component, field)
    if value_raw is None:
        return None
    valueDate = value_raw.dt
    valueDate = valueDate.astimezone()  ## convert to local timezone
    return valueDate.replace(tzinfo=None)


###
def get_ical_str(component, field: TaskField):
    field_name = ICAL_TASK_FIELD_DICT.get(field, field)
    val = component.get(field_name)
    if val is None:
        return None
    return str(val)


###
def get_ical_value(component, field: TaskField):
    field_name = ICAL_TASK_FIELD_DICT.get(field, field)
    return component.get(field_name)


###
def set_ical_dict(component: icalendar.cal.Component, field: TaskField, value, values_dict, _value_extractor=None):
    if values_dict is None:
        return
    if len(values_dict) < 1:
        return
    field_name = ICAL_TASK_FIELD_DICT.get(field, field)
    component.add(field_name, value, parameters=values_dict)


###
def set_ical_list(component, field: TaskField, values_list, value_extractor=None):
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

    field_name = ICAL_TASK_FIELD_DICT.get(field, field)
    component.set_inline(field_name, data_list)


###
def set_ical_value(component, field: TaskField, value):
    if value is None:
        return
    field_name = ICAL_TASK_FIELD_DICT.get(field, field)
    component.add(field_name, value)


###
def set_ical_value_raw(component, field_name, value):
    if value is None:
        return
    component.add(field_name, value)


def get_field(field_dict, key):
    value = field_dict[key]
    value = str(value)
    return value.upper()
