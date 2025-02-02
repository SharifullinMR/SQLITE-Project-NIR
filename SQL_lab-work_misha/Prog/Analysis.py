from operator import index
from PyQt6.QtWidgets import QComboBox, QMessageBox, QHeaderView, QFileDialog
from PyQt6.QtSql import *
from PyQt6 import uic
from PyQt6.QtCore import Qt
import pandas as pd

class NIR:
    def __init__(self,db_file, mainWindow):
        self.mainWindow = mainWindow
        self.query = QSqlQuery()
        self.Form, self.Window = uic.loadUiType("C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/Prog/ui/distribution_NIR.ui")
        self.window = self.Window()
        self.form = self.Form()
        self.form.setupUi(self.window)

        self.current_filter = dict()

        self.sqlModel = QSqlTableModel()
        self.sqlModel.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.form.tableView.setModel(self.sqlModel)
        self.form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.form.tableView.setSortingEnabled(True)
        self.form.tableView.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.select()
        self.add_total_row()
        
        self.form.closeBtn.clicked.connect(lambda: self.closeWindow())
        self.form.saveBtn.clicked.connect(lambda: self.save_to_excel())

    def clean_last_row (self):
        self.sqlModel.removeRows(self.sqlModel.rowCount() - 1, 1)

    def add_total_row(self):
        """Добавляет строку "Итог" с суммами по столбцам."""
        column_count = self.sqlModel.columnCount()

        # Создаем список для хранения значений итоговой строки
        total_row = ["Итог"]
        for column in range(1, column_count-1):
            total = 0
            for row in range(self.sqlModel.rowCount()):
                index = self.sqlModel.index(row, column)
                value = self.sqlModel.data(index)
                if value is not None and isinstance(value, (int, float)):
                    total += value
            total_row.append(total)

        where_filter = self.mainWindow.sqlHandler.query_where
        self.query.exec(f'''select count(DISTINCT Gr_prog.codkon) FROM Gr_prog 
                            JOIN Gr_konk on Gr_konk.codkon = Gr_prog.codkon
                            JOIN VUZ ON Gr_prog.codvuz = VUZ.codvuz {where_filter}''')
        while self.query.next():
            total_row.append(self.query.value(0))


        # Добавляем строку в модель
        self.sqlModel.insertRows(self.sqlModel.rowCount(), 1)
        for i, value in enumerate(total_row):
            index = self.sqlModel.index(self.sqlModel.rowCount() - 1, i)
            self.sqlModel.setData(index, value)

        # Обновить QTableView
        self.form.tableView.resizeColumnsToContents()


    def generate_filter_description(self):
        stroka=self.mainWindow.sqlHandler.filter_for_table
        res=''
        for column,value in stroka.items():
            res+=f'{column}: {value}\n'

        return res


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
            stroke = self.mainWindow.sqlHandler.filter_for_table
            if len(stroke)==0: stroke={'Федеральный округ': "Все округа","Субъект": "Все субъекты","Город": "Все города", "ВУЗ": "Все ВУЗы", "Конкурс": "Все конкурсы"}
            dff = pd.DataFrame(list(stroke.items()),columns=["Критерий","Значение"])

            existing_file = 'NIR_on_VUZ.xlsx'
            dff.to_excel(existing_file, index=False)

            cols=["ВУЗ","Количество НИР","Суммарное плановое финансирование","Количество конкурсов, в которых участвует"]
            df = pd.DataFrame(data, columns=cols)

            '''res= self.generate_filter_description()
            #print(res)
    
            #df1=pd.Dataframe(res)
            #print(df1)
    
            df.to_excel('NIR_on_VUZ.xlsx', index=False, columns=df.columns)'''
            df_existing = pd.read_excel(existing_file)
            df_combined = pd.concat([df_existing, df], axis=0)
            df_combined.to_excel(existing_file, index = False)

            msg = QMessageBox()
            msg.setText(f"Данные сохранены в файл: {existing_file}")
            msg.exec()
        except Exception as e:
            QMessageBox.warning(self.window, "Ошибка", f"Ошибка при сохранении данных: {e}")
        #QMessageBox.information'''

    def save_to_txt(self):
        """Сохраняет данные из QTableView в TXT-файл."""
        # Получаем данные из модели QTableView
        model = self.form.tableView.model()
        data = []
        for row in range(model.rowCount()):
            row_data = []
            for column in range(model.columnCount()):
                index = model.index(row, column)
                row_data.append(model.data(index))
            data.append(row_data)

        # Открываем диалог сохранения файла
        with open('NIR_on_VUZ1.txt', 'w') as f:
            for row in data:
                f.write("\t".join(str(x) for x in row) + "\n")  #
            f.close()

        msg = QMessageBox()
        msg.setText("Данные сохранены в файл: NIR_on_VUZ.txt")
        msg.exec()



    def select(self):
        where_filter = self.mainWindow.sqlHandler.query_where
        if 'WHERE' in where_filter:
            query_having = 'HAVING ' + self.mainWindow.sqlHandler.query_where.replace('WHERE ', '')
        else:
            query_having = ''
        query = \
        f'''SELECT Gr_prog.z2 as "ВУЗ", 
            COUNT(*) as "Количество НИР", 
            SUM(g5) as "Суммарное плановое финансирование", 
            COUNT(DISTINCT codkon) as "Количество конкурсов, в которых участвует" 
        FROM Gr_prog
        JOIN VUZ ON Gr_prog.codvuz = VUZ.codvuz 
        GROUP BY Gr_prog.z2 {query_having}'''
        self.sqlModel.setQuery(query)
        self.sqlModel.select()
        while self.sqlModel.canFetchMore(): self.sqlModel.fetchMore()

    def open(self):
        self.window.show()
        self.window.showMinimized()
        self.window.setWindowState(self.window.windowState() and (not Qt.WindowState.WindowMinimized or Qt.WindowState.WindowActive))

    def closeWindow(self):
        self.window.close()

class Konkurs:
    def __init__(self,db_file, mainWindow):
        self.mainWindow = mainWindow
        self.query = QSqlQuery()
        self.Form, self.Window = uic.loadUiType("C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/Prog/ui/distribution_Konkurs.ui")
        self.window = self.Window()
        self.form = self.Form()
        self.form.setupUi(self.window)
        self.current_filter = dict()

        self.sqlModel = QSqlTableModel()
        self.sqlModel.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.form.tableView.setModel(self.sqlModel)
        self.form.tableView.setSortingEnabled(True)
        self.form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.select()
        self.add_total_row()
        
        self.form.saveBtn1.clicked.connect(lambda: self.save_to_excel())
        self.form.closeBtn1.clicked.connect(lambda: self.closeWindow())

    def clean_last_row(self):
        self.sqlModel.removeRows(self.sqlModel.rowCount() - 1, 1)

    def add_total_row(self):
        """Добавляет строку "Итог" с суммами по столбцам."""
        column_count = self.sqlModel.columnCount()

        # Создаем список для хранения значений итоговой строки
        total_row = ["Итог"]
        for column in range(1, column_count-1):
            total = 0
            for row in range(self.sqlModel.rowCount()):
                index = self.sqlModel.index(row, column)
                value = self.sqlModel.data(index)
                if value is not None and isinstance(value, (int, float)):
                    total += value
            total_row.append(total)

        where_filter = self.mainWindow.sqlHandler.query_where
        self.query.exec(
            f'''SELECT COUNT(DISTINCT Gr_prog.z2) FROM Gr_prog JOIN VUZ ON Gr_prog.codvuz = VUZ.codvuz {where_filter}''')
        while self.query.next():
            total_row.append(self.query.value(0))

        # Добавляем строку в модель
        self.sqlModel.insertRows(self.sqlModel.rowCount(), 1)
        for i, value in enumerate(total_row):
            index = self.sqlModel.index(self.sqlModel.rowCount() - 1, i)
            self.sqlModel.setData(index, value)

        # Обновить QTableView
        self.form.tableView.resizeColumnsToContents()

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
            stroke = self.mainWindow.sqlHandler.filter_for_table
            if len(stroke) == 0: stroke = {'Федеральные округа': "Все", "Субъекты": "Все", "Города": "Все",
                                           "Институты": "Все"}
            dff = pd.DataFrame(list(stroke.items()), columns=["Критерий", "Значение"])

            existing_file = 'NIR_on_Konk.xlsx'
            dff.to_excel(existing_file, index=False)

            cols=["Конкурс","Количество НИР","Суммарное плановое финансирование","Количество ВУЗов"]
            df = pd.DataFrame(data, columns=cols)

            '''res= self.generate_filter_description()
            #print(res)

            #df1=pd.Dataframe(res)
            #print(df1)

            df.to_excel('NIR_on_VUZ.xlsx', index=False, columns=df.columns)'''
            df_existing = pd.read_excel(existing_file)
            df_combined = pd.concat([df_existing, df], axis=0)
            df_combined.to_excel(existing_file, index=False)

            msg = QMessageBox()
            msg.setText(f"Данные сохранены в файл: {existing_file}")
            msg.exec()
        except Exception as e:
            QMessageBox.warning(self.window, "Ошибка", f"Ошибка при сохранении данных: {e}")

    def open(self):
        self.window.show()
        self.window.showMinimized()
        self.window.setWindowState(self.window.windowState() and (not Qt.WindowState.WindowMinimized or Qt.WindowState.WindowActive))

    def closeWindow(self):
        self.window.close()

    def select(self):
        where_filter = self.mainWindow.sqlHandler.query_where
        query = \
        f'''SELECT k2 as "Конкурс", 
            COUNT(DISTINCT g1) as "Количество НИР",
            SUM(g5) as "Суммарное плановое финансирование", 
            COUNT(DISTINCT Gr_prog.codvuz) as "Количество ВУЗов"
        FROM Gr_konk
        JOIN Gr_prog on Gr_konk.codkon = Gr_prog.codkon
        JOIN VUZ on Gr_prog.codvuz = VUZ.codvuz
        {where_filter}
        GROUP BY k2'''
        self.sqlModel.setQuery(query)
        self.sqlModel.select()
        while self.sqlModel.canFetchMore(): self.sqlModel.fetchMore()

class Subyect:
    def __init__(self,db_file, mainWindow):
        self.mainWindow = mainWindow
        self.query = QSqlQuery()
        self.Form, self.Window = uic.loadUiType("C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/Prog/ui/distribution_oblast.ui")
        self.window = self.Window()
        self.form = self.Form()
        self.form.setupUi(self.window)
        self.current_filter = dict()

        self.sqlModel = QSqlTableModel()
        self.sqlModel.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.select()
        self.add_total_row()
        self.form.tableView.setModel(self.sqlModel)

        self.form.tableView.setSortingEnabled(True)
        self.form.tableView.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.form.saveBtn2.clicked.connect(lambda: self.save_to_excel())
        self.form.closeBtn2.clicked.connect(lambda: self.closeWindow())


    def clean_last_row(self):
        self.sqlModel.removeRows(self.sqlModel.rowCount() - 1, 1)

    def add_total_row(self):
        """Добавляет строку "Итог" с суммами по столбцам."""
        column_count = self.sqlModel.columnCount()

        # Создаем список для хранения значений итоговой строки
        total_row = ["Итог"]
        for column in range(1, column_count):
            total = 0
            for row in range(self.sqlModel.rowCount()):
                index = self.sqlModel.index(row, column)
                value = self.sqlModel.data(index)
                if value is not None and isinstance(value, (int, float)):
                    total += value
            total_row.append(total)

        # Добавляем строку в модель
        self.sqlModel.insertRows(self.sqlModel.rowCount(), 1)
        for i, value in enumerate(total_row):
            index = self.sqlModel.index(self.sqlModel.rowCount() - 1, i)
            self.sqlModel.setData(index, value)

        # Обновить QTableView
        self.form.tableView.resizeColumnsToContents()

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
            stroke = self.mainWindow.sqlHandler.filter_for_table
            if len(stroke) == 0: stroke = {'Федеральные округа': "Все", "Субъекты": "Все", "Города": "Все",
                                           "Институты": "Все"}
            dff = pd.DataFrame(list(stroke.items()), columns=["Критерий", "Значение"])

            existing_file = 'NIR_on_Sub.xlsx'
            dff.to_excel(existing_file, index=False)

            cols=["Субъект","Число конкурсов в субъекте","Суммарное плановое финансирование"]
            df = pd.DataFrame(data, columns=cols)

            '''res= self.generate_filter_description()
            #print(res)

            #df1=pd.Dataframe(res)
            #print(df1)

            df.to_excel('NIR_on_VUZ.xlsx', index=False, columns=df.columns)'''
            df_existing = pd.read_excel(existing_file)
            df_combined = pd.concat([df_existing, df], axis=0)
            df_combined.to_excel(existing_file, index=False)

            msg = QMessageBox()
            msg.setText(f"Данные сохранены в файл: {existing_file}")
            msg.exec()
        except Exception as e:
            QMessageBox.warning(self.window, "Ошибка", f"Ошибка при сохранении данных: {e}")

    def select(self):
        where_filter = self.mainWindow.sqlHandler.query_where
        if 'WHERE' in where_filter:
            query_having = 'HAVING ' + self.mainWindow.sqlHandler.query_where.replace('WHERE ', '')
        else:
            query_having = ''
        query = \
        f'''SELECT DISTINCT oblname as "Субъект",
            count(codkon) as "Количество НИР в субъекте",
            SUM(g5) as "Суммарное плановое финансирование"
            FROM VUZ 
            JOIN Gr_prog on  Gr_prog.codvuz=VUZ.codvuz
            GROUP BY oblname {query_having}'''
        self.sqlModel.setQuery(query)
        self.sqlModel.select()
        while self.sqlModel.canFetchMore(): self.sqlModel.fetchMore()

    def open(self):
        self.window.show()
        self.window.showMinimized()
        self.window.setWindowState(self.window.windowState() and (not Qt.WindowState.WindowMinimized or Qt.WindowState.WindowActive))

    def closeWindow(self):
        self.window.close()