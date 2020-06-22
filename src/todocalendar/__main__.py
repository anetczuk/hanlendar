##
## Entry file when package is used as the main program.
##


if __name__ == '__main__':
    from .main import main
 
    main()


# import sys
# #from PyQt4 import QtGui, QtCore
# from todocalendar.gui.qt import QApplication, qApp, QtCore, QEvent, QIcon, QtGui, QWidget, QtWidgets
# 
# 
# # class Example(QWidget):
# # 
# #     def __init__(self):
# #         super(Example, self).__init__()
# # 
# #         self.initUI()
# # 
# # 
# #     def initUI(self):
# # 
# #         cal = QtWidgets.QCalendarWidget(self)
# #         cal.setGridVisible(True)
# #         cal.move(20, 20)
# #         cal.setFirstDayOfWeek(QtCore.Qt.Monday)
# #         cal.clicked[QtCore.QDate].connect(self.showDate)
# # 
# #         self.lbl = QtWidgets.QLabel(self)
# #         date = cal.selectedDate()
# #         self.lbl.setText(date.toString())
# #         self.lbl.move(130, 260)
# # 
# #         self.setGeometry(300, 300, 300, 300)
# #         self.setWindowTitle('Calendar')
# #         self.show()
# # 
# #     def showDate(self, date):
# #         self.lbl.setText(date.toString())
# 
# 
# def main():
# 
#     app = QApplication(sys.argv)
#     ex = Example()
#     sys.exit(app.exec_())
# 
# 
# if __name__ == '__main__':
#     main()
