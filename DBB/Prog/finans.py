from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox, QTableView, QLineEdit
from PyQt6.QtSql import *
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtCore import Qt

class FinancesWindow:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow
        self.query = QSqlQuery()
        self.Form, self.Window = uic.loadUiType("ui/fin1.ui")
        self.window = self.Window()
        self.form = self.Form()
        self.form.setupUi(self.window)

        self.refresh_stats()

        validator = QRegularExpressionValidator(QRegularExpression(r'[0-9]+'))
        validator_percentage = QRegularExpressionValidator(QRegularExpression(r'[0-9]+\.?[0-9]*%$'))
        self.form.summ.setValidator(validator)
        self.form.summ.textEdited.connect(lambda: self.recalculate_sums(self.form.summ))
        self.form.perc.setValidator(validator_percentage)
        self.form.perc.textEdited.connect(lambda: self.recalculate_sums(self.form.perc))

        #На какие кварталы идет распоряжение
        self.kvartals = [True, True, True, True]

        self.form.kvart1.checkStateChanged.connect(lambda: self.setKvartal(0, self.form.kvart1.isChecked()))
        self.form.kvart2.checkStateChanged.connect(lambda: self.setKvartal(1, self.form.kvart2.isChecked()))
        self.form.kvart3.checkStateChanged.connect(lambda: self.setKvartal(2, self.form.kvart3.isChecked()))
        self.form.kvart4.checkStateChanged.connect(lambda: self.setKvartal(3, self.form.kvart4.isChecked()))

    def refresh_stats(self):
        self.query.exec(
            '''
            SELECT sum(k12), sum(k4) FROM Gr_konk
            ''')
        
        self.query.next()
        self.plan_financing = self.query.value(0)
        self.actual_financing = self.query.value(1)
        self.percentage_financing = 100 * self.actual_financing / self.plan_financing 

        self.form.infoPlan.setText(str(self.plan_financing))
        self.form.infoFact.setText(str(self.actual_financing))
        self.form.infoPerc.setText(str(self.percentage_financing) + '%')

    def recalculate_sums(self, editedLine: QLineEdit):
        text = editedLine.text()
        if text == '' or text == '%':
            return
        
        #Убираем процент для преобразования в число
        if '%' in text:
            text = text.replace('%', '')
        
        #Убираем точку, если после нее не идет дробной части
        if text[-1] == '.':
            text = text[:-1]
        
        if editedLine is self.form.summ:
            if '.' in text:
                self.summ = float(text)
            else:
                self.summ = int(text)    
            self.perc = round(100 * self.summ / self.plan_financing, 2)

        elif editedLine is self.form.perc:
            self.perc = float(text)
            self.summ = int(round(self.perc * self.plan_financing / 100))

        curPos = self.form.summ.cursorPosition()
        self.form.summ.setText(str(self.summ))
        self.form.summ.setCursorPosition(curPos)

        curPos = self.form.perc.cursorPosition()
        self.form.perc.setText(str(self.perc) + '%')
        self.form.perc.setCursorPosition(curPos)

        self.recalculate_kvart_sums()

    def recalculate_kvart_sums(self):
        self.kvart_sum = int(round(self.summ / self.kvartals.count(True)))
        self.form.infoKvart.setText(str(self.kvart_sum))

    def setKvartal(self, kvart: int, value: bool):
        checkboxes = {
            0: self.form.kvart1,
            1: self.form.kvart2,
            2: self.form.kvart3,
            3: self.form.kvart4,
        }
        if self.kvartals.count(True) == 1 and self.kvartals[kvart] == True:
            checkboxes[kvart].setChecked(True)
            checkboxes[kvart].setCheckState(Qt.CheckState.Checked)
            return
        
        self.kvartals[kvart] = value
        self.recalculate_kvart_sums()
        



    def open(self):
        self.show()
        
    def close(self):
        self.window.close()

    def show(self):
        self.window.show()

