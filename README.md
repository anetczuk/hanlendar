# Hanlendar

Handy Calendar -- calendar and todo list in one application.


## Handling custom classes from Qt Designer

It is possible to promote widgets to custom classes from within Qt Designer. Steps:
1. from context menu choose *Promote to ...*
2. select proper base class from combo box, e.g. `QCalendarWidget`
3. put *Promoted class name*, e.g. `NavCalendar`
3. in *Header file* put full path to module, e.g. `hanlendar.gui.navcalendar`

