from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox, QTableView, QLineEdit, QHeaderView
from PyQt6.QtSql import *
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtCore import Qt
import pandas as pd

class FinancesWindow:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow
        self.query = QSqlQuery()
        self.Form, self.Window = uic.loadUiType("C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/Prog/ui/fin1.ui")
        self.window = self.Window()
        self.form = self.Form()
        self.form.setupUi(self.window)

        self.model = QSqlTableModel()
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.form.tableView.setModel(self.model)
        self.form.tableView.setSortingEnabled(True)
        self.form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        #На какие кварталы идет распоряжение
        self.kvartals = [True, True, True, True]

        self.form.kvart1.checkStateChanged.connect(lambda: self.setKvartal(0, self.form.kvart1.isChecked()))
        self.form.kvart2.checkStateChanged.connect(lambda: self.setKvartal(1, self.form.kvart2.isChecked()))
        self.form.kvart3.checkStateChanged.connect(lambda: self.setKvartal(2, self.form.kvart3.isChecked()))
        self.form.kvart4.checkStateChanged.connect(lambda: self.setKvartal(3, self.form.kvart4.isChecked()))

        self.refresh_stats()
        self.recalculate_sums(self.form.summ)

        validator = QRegularExpressionValidator(QRegularExpression(r'[0-9]+'))
        validator_percentage = QRegularExpressionValidator(QRegularExpression(r'[0-9]+\.?[0-9]*%$'))
        self.form.summ.setValidator(validator)
        self.form.summ.textEdited.connect(lambda: self.recalculate_sums(self.form.summ))
        self.form.perc.setValidator(validator_percentage)
        self.form.perc.textEdited.connect(lambda: self.recalculate_sums(self.form.perc))

        self.form.calcBtn.clicked.connect(lambda: self.calc_finans_distribution())
        self.form.commit.clicked.connect(lambda: self.apply_finans_distribution())
        self.form.print.clicked.connect(lambda: self.save_to_excel())
        self.form.cancel.clicked.connect(lambda: self.close())

    def refresh_stats(self):
        self.query.exec(
            '''
            SELECT sum(k12), sum(k4) FROM Gr_konk
            ''')
        
        self.query.next()
        self.plan_financing = int(self.query.value(0))
        self.actual_financing = int(self.query.value(1))
        if self.plan_financing !=0:
            self.percentage_financing = 100 * self.actual_financing / self.plan_financing 
        else:
            self.percentage_financing = 0
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
            if self.plan_financing !=0:  
                self.perc = round(100 * self.summ / self.plan_financing, 2)
            else:
                self.perc = 0

        elif editedLine is self.form.perc:
            self.perc = float(text)
            if self.plan_financing !=0:  
                self.summ = int(round(self.perc * self.plan_financing / 100))
            else:
                self.summ = 0

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

    def calc_finans_distribution(self):
        query = \
            f'''
            WITH data AS (
                SELECT
                    z2,
                    SUM(g5) AS g5_sum,
                    {int(self.kvartals[0])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k1,
                    {int(self.kvartals[1])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k2,
                    {int(self.kvartals[2])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k3,
                    {int(self.kvartals[3])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k4
                FROM
                    Gr_prog
                GROUP BY
                    codvuz
            )
            SELECT z2 as "ВУЗ", g5_sum as "Плановое финансирование", k1 as "1 квартал", k2 as "2 квартал", 
                k3 as "3 квартал", k4 as "4 квартал", (k1 + k2 + k3 + k4) AS "Финансирование на год"
                FROM data
            UNION ALL
            SELECT 'Итого', SUM(g5_sum), SUM(k1), SUM(k2), SUM(k3), SUM(k4), SUM(k1 + k2 + k3 + k4) FROM data;
            '''
        print(query)
        self.model.setQuery(query)
        self.model.select()

    def apply_finans_distribution(self):
        self.calc_finans_distribution()
        query1 = \
            f'''
            UPDATE Gr_prog SET g21 = g21 + d1, g22 = g22 + d2, g23 = g23 + d3, 
                g24 = g23 + d4, g2 = g2 + d1 + d2 + d3 + d4 
            FROM (SELECT
            Gr_prog.codkon,
            Gr_prog.g1,
            k1 * Gr_prog.g5 / Finans.g5_sum as d1,
            k2 * Gr_prog.g5 / Finans.g5_sum as d2,
            k3 * Gr_prog.g5 / Finans.g5_sum as d3,
            k4 * Gr_prog.g5 / Finans.g5_sum as d4
                    FROM (
                        SELECT
                            z2,
                            codvuz,
                            Gr_prog.codkon,
                            SUM(g5) AS g5_sum,
                            {int(self.kvartals[0])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k1,
                            {int(self.kvartals[1])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k2,
                            {int(self.kvartals[2])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k3,
                            {int(self.kvartals[3])} * (SUM(g5) * {self.kvart_sum} / {self.plan_financing}) AS k4
                        FROM
                            Gr_prog
                        GROUP BY
                            codvuz
                    ) as Finans, Gr_prog 
                        WHERE Finans.codvuz = Gr_prog.codvuz
                ) as Info
                WHERE Gr_prog.codkon = Info.codkon AND Gr_prog.g1 = Info.g1;
            '''
        
        query2 = \
        '''
        UPDATE Gr_konk
            SET k4 = (
                SELECT SUM(g2) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
            ),
            k41 = (
                SELECT SUM(g21) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
            ),
            k42 = (
                SELECT SUM(g22) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
            ),
            k43 = (
                SELECT SUM(g23) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
            ),
            k44 = (
                SELECT SUM(g24) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
            )
        '''

        
        isSuccess1 = self.query.exec(query1)
        isSuccess2 = self.query.exec(query2)
        self.mainWindow.sqlHandler.select()
        self.mainWindow.update_data_in_windows()
        msg = QMessageBox()
        msg.setText("Приказ утверждён")
        msg.exec()
        
        if not isSuccess1 or not isSuccess2:
            msg = QMessageBox()
            msg.setText("Ошибка")
            msg.exec()


    def open(self):
        self.show()
        
    def close(self):
        self.window.close()

    def show(self):
        self.window.show()
        self.window.showMinimized()
        self.window.setWindowState(self.window.windowState() and (not Qt.WindowState.WindowMinimized or Qt.WindowState.WindowActive))

    def save_to_excel(self):
        """Сохраняет данные из QTableView в CSV-файл."""
        # Получаем данные из модели QTableView
        try:
            model = self.form.tableView.model()
            data = []
            for row in range(model.rowCount()):
                row_data = []
                for column in range(model.columnCount()):
                    index = model.index(row, column)
                    row_data.append(model.data(index))
                data.append(row_data)

            # Создаем DataFrame из данных
            stroke = {
                'Сумма к распределению': self.summ,
                'Процентов от плана': self.perc,
                'Сумма к распределению на один квартал': self.kvart_sum,
                '1 квартал': 'Финансируется' if self.kvartals[0] else 'Не финансируется',
                '2 квартал': 'Финансируется' if self.kvartals[1] else 'Не финансируется',
                '3 квартал': 'Финансируется' if self.kvartals[2] else 'Не финансируется',
                '4 квартал': 'Финансируется' if self.kvartals[3] else 'Не финансируется'
            }
            dff = pd.DataFrame(list(stroke.items()), columns=["Параметры приказа", "Приказ финансирования по ВУЗам"])

            existing_file = 'finances.xlsx'
            dff.to_excel(existing_file, index=False)

            cols=["ВУЗ","1 квартал", "2 квартал", "3 квартал", "4 квартал"]
            df = pd.DataFrame(data, columns=cols)

            df_existing = pd.read_excel(existing_file)
            df_combined = pd.concat([df_existing, df], axis=0)
            df_combined.to_excel(existing_file, index=False)

            msg = QMessageBox()
            msg.setText(f"Данные сохранены в файл: {existing_file}")
            msg.exec()
        except Exception as e:
            QMessageBox.warning(self.window, "Ошибка", f"Ошибка при сохранении данных: {e}")