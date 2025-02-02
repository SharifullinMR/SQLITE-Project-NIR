from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QHeaderView, QMessageBox, QTableView, QVBoxLayout
from PyQt6.QtSql import *
from sqlHandler import SqlHandler
from addWindow import AddWindow, ChangeWindow
from Analysis import NIR, Subyect, Konkurs
from finans import FinancesWindow
from Views import View
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import os

class MainWindow:
    def __init__(self, db_file):
        self.Form, self.Window = uic.loadUiType("C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/Prog/ui/grant_form.ui")
        self.app = QApplication([])
        self.window = self.Window()
        self.form = self.Form()
        self.form.setupUi(self.window)
        self._last_index = -1 #для changeSorting

        self.form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.sqlHandler = SqlHandler(db_file, self)
        self.addWindow = AddWindow(self)
        self.changeWindow = ChangeWindow(self)

        self.View_VUZ = View('Gr_konk',"C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/Prog/ui/Konk_form.ui")
        self.View_Konk = View("VUZ","C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/Prog/ui/VUZ_form.ui")

        self.distr_NIR = NIR(db_file, self)
        self.distr_Konk = Konkurs(db_file, self)
        self.distr_Sub = Subyect(db_file, self)

        self.finances_form = FinancesWindow(self)

        self.combos_default_and_column = {
            self.form.fedCombo: ('Все федеральные округа', 'region'),
            self.form.subCombo: ('Все субъекты', 'oblname'), 
            self.form.gorCombo: ('Все города', 'city'), 
            self.form.vuzCombo: ('Все ВУЗы', 'z2'),
            self.form.konCombo: ('Все конкурсы', 'codkon')
        }
        self.konks = self.sqlHandler._get_konks()
        self.sqlHandler.populate_filtering_combos(self.combos_default_and_column)

        self.form.action_2.triggered.connect(lambda: self.View_VUZ.open())
        self.form.action_3.triggered.connect(lambda: self.View_Konk.open())

        self.form.action_4.triggered.connect(lambda: self.distr_NIR.open())
        self.form.action_5.triggered.connect(lambda: self.distr_Konk.open())
        self.form.action_6.triggered.connect(lambda: self.distr_Sub.open())
        self.form.openFinans.triggered.connect(lambda: self.finances_form.open())
        self.form.reset_finans.triggered.connect(lambda: self.reset_finans())

        self.form.tableView.horizontalHeader().sectionClicked.connect(lambda ind: self.changeSorting(ind, self.sqlHandler.column_names))
        self.form.addBtn.clicked.connect(lambda: self.addWindow.open())
        self.form.changeBtn.clicked.connect(lambda: self.changeWindow.open(*self.get_selected_row_values()))
        self.form.deleteBtn.clicked.connect(lambda: self.delete_row())
        self.form.closeBtn.clicked.connect(lambda: (
            self.sqlHandler.update_vuz_names(),
            self.sqlHandler.select()
        ))
        self.form.resetFilter.clicked.connect(lambda: self.sqlHandler.resetFilter())

        self.form.fedCombo.activated.connect(lambda index: self.changeFilter(self.form.fedCombo))
        self.form.subCombo.activated.connect(lambda index: self.changeFilter(self.form.subCombo))
        self.form.gorCombo.activated.connect(lambda index: self.changeFilter(self.form.gorCombo))
        self.form.vuzCombo.activated.connect(lambda index: self.changeFilter(self.form.vuzCombo))
        self.form.konCombo.activated.connect(lambda index: self.changeFilter(self.form.konCombo))
    
    def changeFilter(self, combo):
        text = combo.currentText()
        isDefault = False
        if text in map(lambda x: x[0], self.combos_default_and_column.values()):
            isDefault = True

        if isDefault:
            self.sqlHandler.deleteFilter(self.combos_default_and_column[combo][1])
        elif combo is self.form.konCombo:
            codkon = self.konks[text]
            self.sqlHandler.addFilter(combo, codkon)
        else:
            self.sqlHandler.addFilter(combo, text)
        
        self.update_data_in_windows()

    def changeSorting(self, header_index, header: QHeaderView):
        '''
        Для изменения фильтра по столбцу и направления фильтрации (по возрастанию и убыванию поочередно)
        '''
        key_columns = [0, 1]
        if header_index in key_columns:
            header_index = 0

        changeTable = {'ASC': 'DESC', 'DESC': 'ASC'}
        if header_index != self._last_index:
            self._current_sorting_dir = 'ASC'
            self._last_index = header_index
        else:
            self._current_sorting_dir = changeTable[self._current_sorting_dir]

        if header_index in key_columns:
            self.sqlHandler.query_orderBy = f'\nORDER BY codkon {self._current_sorting_dir}, g1 {self._current_sorting_dir}'
            self.sqlHandler.select()
            return
        
        col_name = header[header_index]
        self.sqlHandler.query_orderBy = f'\nORDER BY {col_name} {self._current_sorting_dir}'
        self.sqlHandler.select()
    
    def get_selected_row_values(self):
        selected_indexes = self.form.tableView.selectedIndexes()
        if not selected_indexes:
            print('Строка не выбрана')
            return (None, None)
        data = [ index.data() for index in selected_indexes ]
        
        codkon = data[0]
        codnir = data[1]
        pk = {
            'codkon': codkon,
            'g1': codnir
        }
        other_vals = data[2:]
        return (pk, other_vals)

    def delete_row(self):
        pk, row_values = self.get_selected_row_values()
        if not pk:
            msg = QMessageBox()
            msg.setText("Для удаления строки выделите её и нажмите на кнопку удаления строки")
            msg.exec()
            return

        title = row_values[14 - 2]

        msgBox = QMessageBox()
        msgBox.setText(f"Удалить грант с кодом НИР {pk['g1']}?")
        msgBox.setInformativeText(f"Будет удален грант с названием: {title}")
        msgBox.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard)
        msgBox.button(QMessageBox.StandardButton.Save).setText('Удалить')
        msgBox.button(QMessageBox.StandardButton.Discard).setText('Отмена')
        msgBox.setDefaultButton(QMessageBox.StandardButton.Save)
        ret = msgBox.exec()

        if ret == QMessageBox.StandardButton.Save:
            query = 'DELETE FROM Gr_prog WHERE codkon = "{}" AND g1 = {}'.format(pk['codkon'], pk['g1'])
            isGood = self.sqlHandler.query.exec(query)
            msg = QMessageBox()
            if not isGood:
                msg.setText("Не удалось удалить строку из базы данных")
                msg.exec()
                return
            else:
                msg.setText("Выбранная строка была удалена")
                msg.exec()

            self.sqlHandler._sum_financing()
            self.sqlHandler._count_NIRs()
            self.sqlHandler.select()
            self.update_data_in_windows()

    def reset_finans(self):
        query1 = \
            '''
            UPDATE Gr_prog SET g2 = 0, g21 = 0, g22 = 0, g23 = 0, g24 = 0;
            '''
        query2 = \
            '''
            UPDATE Gr_konk SET k4 = 0, k41 = 0, k42 = 0, k43 = 0, k44 = 0;
            '''

        self.sqlHandler.query.exec(query1)
        self.sqlHandler.query.exec(query2)

        self.sqlHandler.select()
        self.update_data_in_windows()

    def update_data_in_windows(self):
        self.distr_NIR.clean_last_row()
        self.distr_Konk.clean_last_row()
        self.distr_Sub.clean_last_row()

        self.distr_NIR.select()
        self.distr_NIR.add_total_row()
        self.distr_Konk.select()
        self.distr_Konk.add_total_row()
        self.distr_Sub.select()
        self.distr_Sub.add_total_row()

        self.View_Konk.select()
        self.View_VUZ.select()

        self.finances_form.refresh_stats()
        self.finances_form.recalculate_sums(self.finances_form.form.summ)
        self.finances_form.recalculate_kvart_sums()