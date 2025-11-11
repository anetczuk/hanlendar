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
from enum import Enum, unique
from typing import Union, Any
import datetime
from datetime import timedelta
import re
import icalendar

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.local.todo import LocalToDo
from hanlendar.domainmodel.recurrent import Recurrent, RepeatType
from hanlendar.domainmodel.reminder import Reminder
from icalendar.prop import TypesFactory


_LOGGER = logging.getLogger(__name__)


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
    REMINDERS = "x-hanlendar-reminders"  ## comma separated list of 'timedelta' values

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
    DESCRIPTION = "description"
    #     LOCATION      = "location"
    DTSTAMP = "dtstamp"  ## create datetime
    CREATED = "created"
    LASTMODIFIED = "last-modified"
    SEQUENCE = "sequence"

    ## 'completed:' substring is converted in all fields in caldav, so it has to be postfixed prevent conversion
    COMPLETED = "x-hanlendar-completedx"
    PRIORITY = "priority"

    GROUP_PARENT = "x-hanlendar-parent"  ## uuid

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


## ===========================================================


def export_icalendar_content(manager: Manager) -> str:
    calendar = export_icalendar(manager)
    bytesContent = calendar.to_ical()
    return bytesContent.decode("utf-8")
    # return str( bytesContent )


def export_icalendar(manager: Manager) -> icalendar.cal.Calendar:
    calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
    calendar.add("prodid", "-//Hanlendar//EN")

    allTasks = manager.getTasksAll()
    _LOGGER.info("creating events: %s", len(allTasks))
    for task_item in allTasks:
        _LOGGER.info("exporting task: %s %s", task_item.UID, task_item.title)
        ievent: icalendar.cal.Event = convert_task_to_icalendar(task_item)
        calendar.add_component(ievent)

    allTodos = manager.getTodosAll()
    _LOGGER.info("creating todos: %s", len(allTodos))
    for todo_item in allTodos:
        _LOGGER.info("exporting todo: %s %s", todo_item.UID, todo_item.title)
        itodo: icalendar.cal.Todo = convert_todo_to_icalendar(todo_item)
        calendar.add_component(itodo)

    return calendar


def convert_task_to_icalendar(task: Task) -> icalendar.cal.Event:
    ievent: icalendar.cal.Event = icalendar.cal.Event()

    ievent.add("DTSTAMP", datetime.datetime.utcnow())

    set_ical_value(ievent, TaskField.UID, task.UID)
    set_ical_value(ievent, TaskField.SUMMARY, task.title)
    
    if task.location:
        set_ical_value(ievent, TaskField.LOCATION, task.location)
    
    if task.url:
        set_ical_value(ievent, TaskField.URL, task.url)
    
    if task.description:
        set_ical_value(ievent, TaskField.DESCRIPTION, task.description)

    if task.sequence > 0:
        set_ical_value(ievent, TaskField.SEQUENCE, task.sequence)

    value_dt = convert_to_ical_dt(task.createDateTime)
    set_ical_value(ievent, TaskField.CREATED, value_dt)

    value_dt = convert_to_ical_dt(task.lastModifiedDateTime)
    set_ical_value(ievent, TaskField.LASTMODIFIED, value_dt)

    start_date_time = None
    if task.startDateTime is not None:
        start_date_time = convert_to_ical_dt(task.startDateTime)
    else:
        ## DTSTART field cannot be None, so use end date
        start_date_time = convert_to_ical_dt(task.dueDateTime)

    end_date_time = convert_to_ical_dt(task.dueDateTime)
    if task.isAllDay():
        set_ical_value(ievent, TaskField.DTSTART, start_date_time.date())
        set_ical_value(ievent, TaskField.DTEND, end_date_time.date())
    else:
        set_ical_value(ievent, TaskField.DTSTART, start_date_time)
        set_ical_value(ievent, TaskField.DTEND, end_date_time)

    if task.completed != 0:
        set_ical_value(ievent, TaskField.COMPLETED, task.completed)

    if task.priority != 5:
        ievent.add(TaskField.PRIORITY.value, task.priority)

    taskParent = task.getParent()
    if taskParent is not None:
        set_ical_value(ievent, TaskField.GROUP_PARENT, taskParent.UID)

    recurrence = task.recurrence
    if recurrence is not None:
        ievent[RecurrentField.MODE.value] = str(recurrence.mode.name)
        ievent[RecurrentField.STEP.value] = str(recurrence.every)
        ievent[RecurrentField.ENDDATE.value] = str(recurrence.endDate)

    reminderList = task.reminderList
    set_ical_list(ievent, TaskField.REMINDERS, reminderList, value_extractor=lambda rem: str(rem.timeOffset))

    if task._unknown_props:
        factory = TypesFactory()
        for key, item in task._unknown_props.items():
            decoded_item = item.decode("utf-8")
            desired_item = factory.from_ical(key, decoded_item)
            ievent.add(key, desired_item)

    return ievent


def convert_todo_to_icalendar(todo: LocalToDo) -> icalendar.cal.Todo:
    itodo: icalendar.cal.Todo = icalendar.cal.Todo()

    itodo.add("DTSTAMP", datetime.datetime.utcnow())

    itodo.add(ToDoField.UID.value, todo.UID)
    itodo.add(ToDoField.SUMMARY.value, todo.title)

    value_dt = convert_to_ical_dt(todo.createDateTime)
    set_ical_value(itodo, ToDoField.CREATED, value_dt)

    value_dt = convert_to_ical_dt(todo.lastModifiedDateTime)
    set_ical_value(itodo, ToDoField.LASTMODIFIED, value_dt)

    if todo.description:
        itodo.add(ToDoField.DESCRIPTION.value, todo.description)

    if todo.sequence > 0:
        set_ical_value(itodo, TaskField.SEQUENCE, todo.sequence)

    if todo.completed != 0:
        itodo.add(ToDoField.COMPLETED.value, todo.completed)

    if todo.priority != 5:
        itodo.add(ToDoField.PRIORITY.value, todo.priority)

    taskParent = todo.getParent()
    if taskParent is not None:
        itodo.add(ToDoField.GROUP_PARENT.value, taskParent.UID)

    if todo._unknown_props:
        factory = TypesFactory()
        for key, item in todo._unknown_props.items():
            decoded_item = item.decode("utf-8")
            desired_item = factory.from_ical(key, decoded_item)
            itodo.add(key, desired_item)

    return itodo


def convert_to_ical_dt(dt_value):
    return dt_value


## ===========================================================


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


def import_icalendar(manager: Manager, calendar: icalendar.cal.Calendar) -> (list[Task], list[Any]):
    tasks: list[Task] = []
    dangling_children = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            imported_tasks, imported_dangling_children = import_task_from_ical(component, manager)
            tasks.extend(imported_tasks)
            dangling_children.extend(imported_dangling_children)
        if component.name == "VTODO":
            imported_tasks, imported_dangling_children = import_todo_from_ical(component, manager)
            tasks.extend(imported_tasks)
            dangling_children.extend(imported_dangling_children)

    return tasks, dangling_children


def import_task_from_ical(component, manager):
    new_items = []
    dangling_children = []

    task: Task = manager.createEmptyTask()

    # TODO: class, transp
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

    sequence = component.get(TaskField.SEQUENCE.value)
    if sequence is not None:
        task.sequence = int(sequence)

    created_date = get_ical_value_dt(component, TaskField.CREATED)
    task._createDate = created_date

    modified_date = get_ical_value_dt(component, TaskField.LASTMODIFIED)
    task._lastModifiedDate = modified_date

    start_date = get_ical_value_dt(component, TaskField.DTSTART)
    end_date = get_ical_value_dt(component, TaskField.DTEND)

    if start_date == end_date:
        start_date = None
    task.setOccurrence(start_date, end_date)

    task.completed = get_ical_value_int(component, TaskField.COMPLETED, 0)
    task.priority = get_ical_value_int(component, TaskField.PRIORITY, 5)

    try:
        recurrMode = component.get(RecurrentField.MODE.value)
        recurrMode = RepeatType.findByName(recurrMode)

        recurrStep = component.get(RecurrentField.STEP.value)
        recurrStep = int(recurrStep)

        recurrEnd = component.get(RecurrentField.ENDDATE.value)
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

    unhandled_props = {}
    for key, val in component.items():
        unhandled_props[ key ] = val.to_ical()
    for item in TaskField:
        prop_name = item.value.upper()
        if prop_name in unhandled_props:
            del unhandled_props[prop_name]
    task._unknown_props = unhandled_props

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


def import_todo_from_ical(component, manager):
    new_items = []
    dangling_children = []

    todo: LocalToDo = manager.createEmptyToDo()

    # TODO: class, transp
    todo.UID = get_ical_str(component, TaskField.UID)

    summary = get_ical_str(component, TaskField.SUMMARY)
    if summary is not None:
        todo.title = f"{summary}"

    location = component.get(TaskField.LOCATION.value)
    if location is not None:
        todo.location = f"{location}"

    url = component.get(TaskField.URL.value)
    if url is not None:
        todo.url = f"{url}"

    todo.description = get_ical_str(component, TaskField.DESCRIPTION)
    if todo.description is None:
        todo.description = ""
    todo.description = todo.description.replace("=0D=0A", "\n")

    sequence = component.get(TaskField.SEQUENCE.value)
    if sequence is not None:
        todo.sequence = int(sequence)

    created_date = get_ical_value_dt(component, TaskField.CREATED)
    todo._createDate = created_date

    modified_date = get_ical_value_dt(component, TaskField.LASTMODIFIED)
    todo._lastModifiedDate = modified_date

    todo.completed = get_ical_value_int(component, TaskField.COMPLETED, 0)
    todo.priority = get_ical_value_int(component, TaskField.PRIORITY, 5)

    try:
        recurrMode = component.get(RecurrentField.MODE.value)
        recurrMode = RepeatType.findByName(recurrMode)

        recurrStep = component.get(RecurrentField.STEP.value)
        recurrStep = int(recurrStep)

        recurrEnd = component.get(RecurrentField.ENDDATE.value)
        recurrEnd = convert_to_date(recurrEnd)

        todo.recurrence = Recurrent(recurrMode, recurrStep, recurrEnd)

    # ruff: noqa: S110
    except Exception:  # pylint: disable=W0718 # nosec
        pass

    try:
        todo.reminderList = get_ical_list(
            component,
            TaskField.REMINDERS,
            value_converter=reminder_from_string,
        )
        if todo.reminderList is not None:
            todo.reminderList = [item for item in todo.reminderList if item is not None]
    except Exception:  # as ex:
        _LOGGER.warning("unable to import remainder list: %s %s", todo.title, todo.dueDateTime)
        raise

    unhandled_props = {}
    for key, val in component.items():
        unhandled_props[ key ] = val.to_ical()
    for item in TaskField:
        prop_name = item.value.upper()
        if prop_name in unhandled_props:
            del unhandled_props[prop_name]
    todo._unknown_props = unhandled_props

    parentUID = get_ical_str(component, TaskField.GROUP_PARENT)
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
def get_ical_dict(component, field: Union[TaskField, str], _value_converter=None):
    field_name = field
    if isinstance(field, TaskField):
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
def get_ical_list(component, field: Union[TaskField, str], value_converter=None):
    field_name = field
    if isinstance(field, TaskField):
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
    value_raw = component.get(field.value)
    if value_raw is None:
        return None
    value_type = value_raw.params.get("VALUE")
    if value_type is None:
        valueDate = value_raw.dt
        valueDate = valueDate.astimezone()  ## convert to local timezone
        return valueDate
        #return valueDate.replace(tzinfo=None)
    if value_type == "DATE":
        value_date: datetime.date = value_raw.dt
        value_dt = datetime.datetime(value_date.year, value_date.month, value_date.day)
        return value_dt
    _LOGGER.warning("unhandled ical date type: %s", value_type)
    return None


###
def get_ical_str(component, field: TaskField):
    val = component.get(field.value)
    if val is None:
        return None
    return str(val)


###
def get_ical_value(component, field: Union[TaskField, str]):
    field_name = field
    if isinstance(field, TaskField):
        field_name = field.value
    return component.get(field_name)


###
def set_ical_dict(
    component: icalendar.cal.Component,
    field: Union[TaskField, str],
    value,
    values_dict,
    _value_extractor=None,
):
    if values_dict is None:
        return
    if len(values_dict) < 1:
        return
    field_name = field
    if isinstance(field, TaskField):
        field_name = field.value
    component.add(field_name, value, parameters=values_dict)


###
def set_ical_list(component, field: Union[TaskField, str], values_list, value_extractor=None):
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
    if isinstance(field, TaskField):
        field_name = field.value
    component.set_inline(field_name, data_list)


###
def set_ical_value(component, field: TaskField, value):
    if value is None:
        return
    component.add(field.value, value)


###
def set_ical_value_raw(component, field_name, value):
    if value is None:
        return
    component.add(field_name, value)


def get_field(field_dict, key):
    value = field_dict[key]
    value = str(value)
    return value.upper()


## ============================================================


def replace_line(content, line_prefix, new_content):
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(line_prefix):
            lines[i] = f"{line_prefix}{new_content}"
    return "\n".join(lines) + "\n"


def remove_line(content, line_prefix):
    out_lines = []
    lines = content.splitlines()
    for line in lines:
        if not line.startswith(line_prefix):
            out_lines.append( line )
    return "\n".join(out_lines) + "\n"


def sort_ical_content(content):
    lines = content.splitlines()
    cal_index = lines.index("BEGIN:VCALENDAR")
    cal_lines = lines[ cal_index + 1 : ]
    item_start_index = find_starting_index(cal_lines, "BEGIN:")
    item_end_index = find_starting_index(cal_lines, "END:")
    item_lines = cal_lines[ item_start_index + 1 : item_end_index ]
    item_lines.sort()
    
    out_lines = []
    out_lines.extend( lines[ : cal_index + 1] )
    out_lines.extend( cal_lines[ : item_start_index + 1] )
    out_lines.extend( item_lines )
    out_lines.extend( cal_lines[ item_end_index : ] )

    return "\n".join(out_lines) + "\n"


def find_starting_index(content_list, line_start):
    for i, item in enumerate(content_list):
        if item.startswith(line_start):
            return i
    return -1
