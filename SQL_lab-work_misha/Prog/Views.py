from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtSql import *
import sys

class View:
    def __init__(self, table_name, form_view):
        self.Form, self.Window = uic.loadUiType(form_view)
        self.app = QApplication([])
        self.window = self.Window()
        self.form = self.Form()
        self.form.setupUi(self.window)

        self.column_names = {
            'VUZ': [
                "Сокращ. наименование ВУЗа",
                "Наименование ВУЗа",
                "Полное наименование ВУЗа",
                "Статус",
                "Город",
                "Федеральный округ",
                "Субъект Федерации",
                "Направление",
                "Номер субъекта",
                "Номер ВУЗа",
                "Категория ВУЗа",
            ],
            'Gr_konk': [
                "Код конкурса",
                "Название конкурса",
                "План. объем финансирования",
                "Фактич. объем финансирования",
                "I Квартал",
                "II Квартал",
                "III Квартал",
                "IV Квартал",
                "Количество НИР",
            ]
        }

        self.table_name=table_name
        self.model = QSqlTableModel()
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.form.tableView.setModel(self.model)
        self.form.tableView.setSortingEnabled(True)
        self.form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.select()

        self.form.closeBtn1.clicked.connect(lambda: self.closeWindow())

    def select(self):
        self.model.setTable(self.table_name)
        self.model.select()

        # Задание имен столбцов
        if self.table_name in self.column_names:
            for i, name in enumerate(self.column_names[self.table_name]):
                self.model.setHeaderData(i, Qt.Orientation.Horizontal, name)  
        
    def open(self):
        self.window.show()
        self.window.showMinimized()
        self.window.setWindowState(self.window.windowState() and (not Qt.WindowState.WindowMinimized or Qt.WindowState.WindowActive))

    def closeWindow(self):
        self.window.close()

    def showMessage(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.exec()