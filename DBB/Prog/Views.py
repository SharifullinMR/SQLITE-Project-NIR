from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSql import *
import sys

from sqlHandler import SqlHandler
from addWindow import AddWindow, ChangeWindow
from Analysis import NIR, Subyect, Konkurs

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
        if table_name == 'Gr_konk':
            self.form.resetBtn.clicked.connect(lambda: (
                self.select(),
                self.showMessage("Данные успешно обновлены")
            ))

    def select(self):
        self.model.setTable(self.table_name)
        self.model.select()

        # Задание имен столбцов
        if self.table_name in self.column_names:
            for i, name in enumerate(self.column_names[self.table_name]):
                self.model.setHeaderData(i, Qt.Orientation.Horizontal, name)  
        
        

    def update_database(self):
        """Обновляет данные в базе данных."""
        if self.model.submitAll():
            QMessageBox.information(self, "Информация", "Данные успешно обновлены.")
        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка при обновлении данных.")

        self.form.tableView.sortByColumn(0, Qt.SortOrder.AscendingOrder)  
        

    def open(self):
        self.window.show()

    def closeWindow(self):
        self.window.close()

    def connect_db(self, db_file: str,db_name):
        '''
        Подключение в БД данной по адресу db_file
        '''
        self.db_file = db_file
        self._connect_db(db_name)
        if not self.db:
            sys.exit(-1)
        else:
            self.query = QSqlQuery()
            print("connection ok")

    def _connect_db(self, db_file: str):
        '''
        Открывает БД и сохраняет данные для работы с ней
        '''
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(db_file)
        #self.tableView.setModel()
        if not self.db.open():
            print("Cannot establish a database connection to {}!".format(db_file))
            return False
        self.form.closeBtn2.clicked.connect(lambda: self.closeWindow())

    def showMessage(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.exec()