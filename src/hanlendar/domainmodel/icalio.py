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
import re

import icalendar

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.task import TaskField, Task
from hanlendar.domainmodel.recurrent import Recurrent, RepeatType, \
    RecurrentField
import datetime
from hanlendar.domainmodel.reminder import Reminder


_LOGGER = logging.getLogger(__name__)


##
## Translation of task field to ical field
##
ICAL_TASK_FIELD_DICT = {
    TaskField.UID:           'uid',
    TaskField.SUMMARY:       'summary',
    TaskField.DESCRIPTION:   'description',
    # TaskField.LOCATION:      'location',
    TaskField.DTSTART:       'dtstart',
    TaskField.DTEND:         'dtend',
    TaskField.COMPLETED:     'x-hanlendar-completedx',           ## 'completed:' substring is converted in all fields in caldav, so it has to be postfixed prevent conversion
    TaskField.PRIORITY:      'priority',
    TaskField.GROUP_PARENT:  'x-hanlendar-parent',               ## uuid
    TaskField.RECURRENCE:    'x-hanlendar-reccur',
    TaskField.RECCUR_OFFSET: 'x-hanlendar-reccur-offset',
    TaskField.REMINDERS:     'x-hanlendar-reminders'             ## comma separated list of 'timedelta' values
}


ICAL_RECURR_FIELD_DICT = {
    RecurrentField.MODE:     'mode',
    RecurrentField.STEP:     'step',
    RecurrentField.ENDDATE:  'enddate'
}


def export_icalendar_content( manager: Manager ) -> str:
    calendar = export_icalendar( manager )
    bytesContent = calendar.to_ical()
    return bytesContent.decode("utf-8")
    # return str( bytesContent )


def export_icalendar( manager: Manager ) -> icalendar.cal.Calendar:
    calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()

    allTasks = manager.getTasksAll()
#     if len(allTasks) > 30:
#         allTasks = allTasks[0:30]
    _LOGGER.info( "creating events: %s", len( allTasks ) )
    ## task: Task = None
    for task in allTasks:
        _LOGGER.info( "exporting task: %s %s", task.UID, task.title )

        ievent = icalendar.cal.Event()

        set_ical_value( ievent, TaskField.UID, task.UID )
        set_ical_value( ievent, TaskField.SUMMARY, task.title )
        ## no location

        if task.startDateTime is not None:
            set_ical_value( ievent, TaskField.DTSTART, task.startDateTime )
        else:
            ## DTSTART field cannot be None, so use end date
            set_ical_value( ievent, TaskField.DTSTART, task.dueDateTime )

        set_ical_value( ievent, TaskField.DTEND, task.dueDateTime )
        set_ical_value( ievent, TaskField.DESCRIPTION, task.description )
        set_ical_value( ievent, TaskField.COMPLETED, task.completed )

        taskParent = task.getParent()
        if taskParent is not None:
            set_ical_value( ievent, TaskField.GROUP_PARENT, taskParent.UID )

        reccurence = task.recurrence
        if reccurence is not None:
            recurrent_dict = {}
            recurrent_dict[ ICAL_RECURR_FIELD_DICT[ RecurrentField.MODE ] ]    = str( reccurence.mode.name )
            recurrent_dict[ ICAL_RECURR_FIELD_DICT[ RecurrentField.STEP ] ]    = str( reccurence.every )
            recurrent_dict[ ICAL_RECURR_FIELD_DICT[ RecurrentField.ENDDATE ] ] = str( reccurence.endDate )
            set_ical_dict( ievent, TaskField.RECURRENCE, task.recurrentOffset, recurrent_dict )

        reminderList = task.reminderList
        set_ical_list( ievent, TaskField.REMINDERS, reminderList, value_extractor=lambda rem: str(rem.timeOffset) )

        calendar.add_component( ievent )

    return calendar


def import_icalendar_content( manager: Manager, content: str ):
    try:
        dangling_children = []
        extracted_ical = extract_ical( content )
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar.from_ical( extracted_ical )
        tasks, children = import_icalendar( manager, calendar )
        dangling_children.extend( children )
        for task in tasks:
            if task.reminderList is None:
                continue
            if len(task.reminderList) > 0:
                continue
            task.addReminderDays( 1 )
        return tasks, dangling_children
    except ValueError as ex:
        _LOGGER.warning( "unable to import calendar data: %s", ex )
    return None


def import_icalendar( manager: Manager, calendar: icalendar.cal.Calendar ):
    tasks = []
    dangling_children = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            task: Task = manager.createEmptyTask()

            #TODO: class, created, last-modified, sequence, transp
            task.UID = get_ical_str( component, TaskField.UID )

            summary    = get_ical_str( component, TaskField.SUMMARY )
            location   = component.get( 'location' )
            if location is not None:
                task.title = f"{summary}, {location}"
            else:
                task.title = f"{summary}"

            task.description = get_ical_str( component, TaskField.DESCRIPTION )
            if task.description is None:
                task.description = ""
            task.description = task.description.replace( "=0D=0A", "\n" )

            start_date = get_ical_value_dt( component, TaskField.DTSTART )
            end_date   = get_ical_value_dt( component, TaskField.DTEND )

            if start_date == end_date:
                start_date = None
            task.startDateTime = start_date
            task.dueDateTime   = end_date

            task.completed = get_ical_value_int( component, TaskField.COMPLETED, 0 )

            try:
                recurr_dict = get_ical_dict( component, TaskField.RECURRENCE )
                reccurMode = recurr_dict[ get_field( ICAL_RECURR_FIELD_DICT, RecurrentField.MODE ) ]
                reccurMode = RepeatType.findByName( reccurMode )
                reccurStep = recurr_dict[ get_field( ICAL_RECURR_FIELD_DICT, RecurrentField.STEP ) ]
                reccurStep = int( reccurStep )
                reccurEnd  = recurr_dict[ get_field( ICAL_RECURR_FIELD_DICT, RecurrentField.ENDDATE ) ]
                reccurEnd  = convert_to_date( reccurEnd )
                task.recurrence = Recurrent( reccurMode, reccurStep, reccurEnd )
                task.recurrentOffset = get_ical_value_int( component, TaskField.RECURRENCE, 0 )
            except Exception:  # as ex:
                pass

            try:
                task.reminderList = get_ical_list( component, TaskField.REMINDERS, value_converter=lambda raw: Reminder.from_timedelta_string(raw) )
                if task.reminderList is not None:
                    task.reminderList = [ item for item in task.reminderList if item is not None ]
            except Exception:  # as ex:
                print( "unable to import remainder list:", task.title, task.dueDateTime )
                raise

            parentUID  = get_ical_str( component, TaskField.GROUP_PARENT )
            if parentUID is None:
                ## regular task
                addedTask = manager.addTask( task )
                tasks.append( addedTask )
                continue
            taskParent: Task = manager.findTaskByUID( parentUID )
            if taskParent is not None:
                ## add as subitem
                taskParent.addSubItem( task )
                tasks.append( task )
            else:
                ## invalid case -- parent still not added
                dangling_children.append( (task, parentUID) )

    return tasks, dangling_children


def fix_dangling_tasks( manager: Manager, dangling_children ):
    ## handle dangling children
    while len(dangling_children) > 0:
        handled = False
        for i in range( len(dangling_children) - 1, -1, -1 ):
            child, parent_uid = dangling_children[ i ]
            taskParent: Task = manager.findTaskByUID( parent_uid )
            if taskParent is not None:
                ## add as subitem
                taskParent.addSubItem( child )
                del dangling_children[ i ]
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
            child, _ = item
            manager.addTask( child )
        break


## ========================================================


def extract_ical( content: str ):
    cal_begin_pos = content.find( "BEGIN:VCALENDAR" )
    if cal_begin_pos < 0:
        return content
    END_SUB = "END:VCALENDAR"
    cal_end_pos = content.find( END_SUB, cal_begin_pos )
    if cal_end_pos < 0:
        return content
    cal_end_pos += len( END_SUB )
    return content[ cal_begin_pos:cal_end_pos ]


###
def get_ical_dict( component, field: TaskField, value_converter=None ):
    field_name = field
    if field in ICAL_TASK_FIELD_DICT:
        field_name = ICAL_TASK_FIELD_DICT[ field ]
    if component.has_key(field_name) is False:
        return None
    raw_list = component.get( field_name )
    if raw_list is None:
        return None
    raw_params = raw_list.params
    if raw_params is None:
        return None
    if len(raw_params) < 1:
        return None
    ret_dict = {}
    for key, val in raw_params.items():
        ret_dict[ key ] = val
    return ret_dict


###
def get_ical_list( component, field: TaskField, value_converter=None ):
    field_name = field
    if field in ICAL_TASK_FIELD_DICT:
        field_name = ICAL_TASK_FIELD_DICT[ field ]
    if component.has_key(field_name) is False:
        return None
    raw_list = component.get_inline( field_name )
    if raw_list is None:
        return None
    if len(raw_list) < 1:
        return None

#     print( "xxxxxxxxxx:", raw_list )
    retList = []
    for item in raw_list:
        value = item.decode("utf-8")
        if value_converter is not None:
            value = value_converter( value )
        retList.append( value )
    return retList


###
def get_ical_value_int( component, field: TaskField, defaultValue ):
    try:
        value_str = get_ical_str( component, field )
        return int( value_str )
    except Exception:  # as ex:
        pass
    return defaultValue


###
def get_ical_value_date( component, field: TaskField ):
    value_str = get_ical_str( component, field )
    return convert_to_date( value_str )


def convert_to_date(value_string: str):
    try:
        date_time_obj = datetime.datetime.strptime( value_string, '%Y-%m-%d' )
        return date_time_obj.date()
    except Exception:
        return None


###
def get_ical_value_dt(component, field: TaskField):
    value_raw = get_ical_value( component, field )
    if value_raw is None:
        return None
    valueDate = value_raw.dt
    valueDate = valueDate.astimezone()                  ## convert to local timezone
    valueDate = valueDate.replace(tzinfo=None)
    return valueDate


###
def get_ical_str( component, field: TaskField ):
    field_name = field
    if field in ICAL_TASK_FIELD_DICT:
        field_name = ICAL_TASK_FIELD_DICT[ field ]
    val = component.get( field_name )
    if val is None:
        return None
    return str( val )


###
def get_ical_value( component, field: TaskField ):
    field_name = field
    if field in ICAL_TASK_FIELD_DICT:
        field_name = ICAL_TASK_FIELD_DICT[ field ]
    return component.get( field_name )


###
def set_ical_dict( component, field: TaskField, value, values_dict, value_extractor=None ):
    if values_dict is None:
        return
    if len(values_dict) < 1:
        return
    field_name = field
    if field in ICAL_TASK_FIELD_DICT:
        field_name = ICAL_TASK_FIELD_DICT[ field ]
    component.add( field_name, value, parameters=values_dict )


###
def set_ical_list( component, field: TaskField, values_list, value_extractor=None ):
    if values_list is None:
        return
    if len(values_list) < 1:
        return

    data_list = []
    for item in values_list:
        value = item
        if value_extractor:
            value = value_extractor( value )
        data_list.append( value )

    field_name = field
    if field in ICAL_TASK_FIELD_DICT:
        field_name = ICAL_TASK_FIELD_DICT[ field ]
    component.set_inline( field_name, data_list )


###
def set_ical_value( component, field: TaskField, value ):
    if value is None:
        return
    field_name = field
    if field in ICAL_TASK_FIELD_DICT:
        field_name = ICAL_TASK_FIELD_DICT[ field ]
    component.add( field_name, value )


def get_field( field_dict, key ):
    value = field_dict[ key ]
    value = str( value )
    return value.upper()
