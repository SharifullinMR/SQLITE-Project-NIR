import sys
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtSql import *

class SqlHandler:
    def __init__(self, db_file, mainWindow):
        self.db_file = db_file
        self.mainWindow = mainWindow
        self.query_select = '''SELECT Gr_prog.codkon as "Код конкурса",
         Gr_prog.g1 as "Код НИР",
         Gr_prog.z2 as "Наименование ВУЗа",
         Gr_prog.g7 as "Код по ГРНТИ",
         Gr_prog.g8 as "ФИО руководителя",
         Gr_prog.g9 as "Должность руководителя",
         Gr_prog.g10 as "Учёное звание",
         Gr_prog.g11 as "Учёная степень",
         Gr_prog.g5 as "Плановый объем гранта",
         Gr_prog.g2 as "Фактический объем гранта",
         Gr_prog.g21 as "Финансирование за I кв.",
         Gr_prog.g22 as "Финансирование за II кв.",
         Gr_prog.g23 as "Финансирование за III кв.",
         Gr_prog.g24 as "Финансирование за IV кв.",
         Gr_prog.g6 as "Наименование НИР",
         Gr_prog.codvuz as "Код ВУЗа"
         FROM Gr_prog'''
        self.query_join = ''
        self.query_where = ''
        self.query_orderBy = ''
        self.current_filter = dict()

        self.filter_for_table={}
        
        self.connect_db(db_file)
        self.column_names = self.select_column_names('Gr_prog')
        self.model = QSqlTableModel()
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)

        self.select()


        self.mainWindow.form.tableView.setModel(self.model)
        self.mainWindow.form.tableView.resize(self.model.columnCount(),self.model.rowCount())
        #self.load_all_data()

        '''row_count = self.model.rowCount()
        print(row_count)
        if row_count > 0: self.mainWindow.form.tableView.selectRow(row_count-1)'''


    #def load_all_data(self):
        #while self.model.canFetchMore(): self.model.fetchMore()

    def connect_db(self, db_file: str):
        '''
        Подключение в БД данной по адресу db_file
        '''
        self.db_file = db_file
        self._connect_db(db_file)
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
        if not self.db.open():
            print("Cannot establish a database connection to {}!".format(db_file))
            return False
        
    def select_column_names(self, table_name: str) -> list:
        '''
        Запрашивает из БД названия столбцов таблицы table_name
        '''
        self.query.exec(
            f'''
            PRAGMA table_info({table_name})
            '''
        )
        column_names = []
        while self.query.next():
            column_names.append(self.query.value(1))
        return column_names

    def update_vuz_names(self):
        '''
        Обновляет столбец z2 данными о названиях ВУЗов на основе таблицы VUZ
        '''
        return self.query.exec(
            '''
            UPDATE Gr_prog
            SET z2 = (
                SELECT z2 from VUZ where Gr_prog.codvuz = VUZ.codvuz
            )
            '''
        )
    
    def _select_konks(self, form):
        '''
        Выбирает названия конкурсов и их кодов и сохраняет в словаре self.konks = { имя_конкурса: код_конкурса }
        '''
        self.query.exec(
            '''
            SELECT DISTINCT k2, codkon FROM Gr_konk
            ORDER BY k2
            '''
        )
        self.konks = {} # name -> codkon
        while self.query.next():
            self.konks[self.query.value(0)] = self.query.value(1)
            form.konkCombo.addItem(self.query.value(0))
    
    def _select_vuzes(self, form):
        '''
        Выбирает название ВУЗов и их кодов и сохраняет в словаре self.vuzes = { имя_вуза: код_вуза }
        '''
        self.query.exec(
            '''
            SELECT DISTINCT z2, codvuz FROM VUZ 
            ORDER BY z2
            '''
        )
        self.vuzes = {} # name -> codvuz
        while self.query.next():
            self.vuzes[self.query.value(0)] = self.query.value(1)
            form.vuzCombo.addItem(self.query.value(0))
    
    def select(self) -> None:
        '''
        Делается запрос, состоящий из конкатенации хранящихся отдельно self.query_<название_части>. Полученные данные выводятся в таблице в программе
        '''
        query = self.query_select + self.query_join + self.query_where + self.query_orderBy
        self.model.setQuery(query)
        self.model.select()
        while self.model.canFetchMore(): self.model.fetchMore()
        if 'View_konk' in dir(self.mainWindow):
           self.mainWindow.View_Konk.model.select()
    
    def resetFilter(self) -> None:
        '''
        Фильтры по упорядочиванию по столбцу и по определённым регионам, субъектам и т.д. сбрасываются
        '''
        self.query_orderBy = ''
        self.query_join = ''
        self.query_where = ''
        self.current_filter = dict()
        self.populate_filtering_combos(self.mainWindow.combos_default_and_column)

        self.mainWindow.distr_NIR.clean_last_row()
        self.mainWindow.distr_Konk.clean_last_row()
        self.mainWindow.distr_Sub.clean_last_row()

        self.select()
        self.mainWindow.distr_NIR.select()
        self.mainWindow.distr_Konk.select()
        self.mainWindow.distr_Sub.select()

        self.mainWindow.distr_NIR.add_total_row()
        self.mainWindow.distr_Konk.add_total_row()
        self.mainWindow.distr_Sub.add_total_row()

    def populate_filtering_combos(self, combos_default_and_columns: dict, restoreText: bool = False) -> None:
        '''
        ComboBox'ы из combos_default_and_columns (для фильтрации по регионам, субъектам и т.д.) заполняются вариантами с учётами введенных фильтров
        '''
        for combo in combos_default_and_columns:
            default, column = combos_default_and_columns[combo]
            items = [default,]
            curText = combo.currentText()
            if column == 'codkon':
                query = f'SELECT DISTINCT k2 FROM Gr_konk JOIN Gr_prog on Gr_konk.codkon = Gr_prog.codkon JOIN VUZ on Gr_prog.codvuz = VUZ.codvuz' \
                    + self.query_where + f' ORDER BY k2 ASC'
            else:
                query_where = self.query_where
                if 'codkon' in query_where:
                    query_where = query_where.rstrip('\n')
                query = f'SELECT DISTINCT VUZ.{column} FROM Gr_konk JOIN Gr_prog on Gr_konk.codkon = Gr_prog.codkon JOIN VUZ on Gr_prog.codvuz = VUZ.codvuz' \
                    + query_where + f' ORDER BY VUZ.{column} ASC'
            self._select_and_fill_combo(items, query, combo)
            if restoreText:
                newIndex = combo.findText(curText)
                if newIndex != -1:
                    combo.setCurrentIndex(newIndex)
                else:
                    combo.setCurrentIndex(0)
            if combo.count() == 2:
                combo.setCurrentIndex(1)
                default, column = self.mainWindow.combos_default_and_column[combo]
                if column != 'codkon':
                    self.current_filter[column] = combo.currentText()
                else:
                    self.current_filter[column] = self.mainWindow.konks[combo.currentText()]
            
    def _select_and_fill_combo(self, items_default: list, query: str, combo: QComboBox):
        '''
        Добавляет в список стандартные значения items_default и значения, полученные из SQL-запроса query
        '''
        self.query.exec(query)
        items = []

        #Чтобы для пустых результатов не вылетало из функции
        try:
            while self.query.next():
                items.append(self.query.value(0))
        except Exception:
            pass
        combo.clear()
        combo.addItems(items_default + items)


    def addFilter(self, comboBox: QComboBox, text: str) -> None:
        '''
        Для добавления изменений в фильтрацию по регионам, субъектам и тд, когда один из соответствующих comboBox изменён пользователем на значение text.
        Новый фильтр применяется, набор возможных значений комбоБоксов меняется и данные выбираются из БД в соответствии с фильтром.
        '''
        default, column = self.mainWindow.combos_default_and_column[comboBox]
    
        if text == default:
            self.deleteFilter(column)
            return
        
        self.current_filter[column] = text

        self._construct_filter_query()
        self.populate_filtering_combos(self.mainWindow.combos_default_and_column, restoreText=True)

        names_filters={'Федеральный округ': "region","Субъект": "oblname","Город": "city", "Институт": "z2"}
        self.filter_for_table = {key: self.current_filter[value] for key, value in names_filters.items() if value in self.current_filter}

        '''print("**********")
        print(self.filter_for_table)
        print("**********")'''

        self.mainWindow.distr_NIR.clean_last_row()
        self.mainWindow.distr_Konk.clean_last_row()
        self.mainWindow.distr_Sub.clean_last_row()

        self.select()
        self.mainWindow.distr_NIR.select()
        self.mainWindow.distr_Konk.select()
        self.mainWindow.distr_Sub.select()

        self.mainWindow.distr_NIR.add_total_row()
        self.mainWindow.distr_Konk.add_total_row()
        self.mainWindow.distr_Sub.add_total_row()
        
    def deleteFilter(self, column):
        if column in self.current_filter:
            self.current_filter.pop(column)
            self._construct_filter_query()
            self.populate_filtering_combos(self.mainWindow.combos_default_and_column, restoreText=True)
            self.select()

    def _construct_filter_query(self):
        '''
        На основании сохранённых данных о введённых фильтрах в словаре self.current_filter = { столбец: значение_для_поиска } формируются части SQL-запроса для фильтрации: query_join, query_where
        '''
        if len(self.current_filter) == 0:
            self.query_join = ''
            self.query_where = ''
            return
        
        self.query_join = '\nJOIN VUZ ON Gr_prog.codvuz = VUZ.codvuz'
        self.query_where = '\nWHERE '
        first = True
        for column, text in self.current_filter.items():
            prefix = 'Gr_prog' if column == 'codkon' else 'VUZ'
            if first:
                self.query_where += f'{prefix}.{column} = "{text}"'
                first = False
            else:
                self.query_where += f'\n\tAND {prefix}.{column} = "{text}"'

    def _sum_financing(self):
        self.query.exec('''
                        UPDATE Gr_konk
                        SET k12 = (
                            SELECT SUM(g5) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
                        )
                        ''')

    def _count_NIRs(self):
        self.query.exec('''
                        UPDATE Gr_konk
                        SET npr = (
                            SELECT COUNT(*) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
                        )
                        ''')

    def _count_NIR_VUZ(self):
        self.query.exec('''
                        UPDATE Gr_konk
                        SET npr = (
                            SELECT COUNT(*) from Gr_prog WHERE Gr_konk.codkon = Gr_prog.codkon
                        )
                        ''')
    
    def _get_konks(self):
        self.query.exec('SELECT k2, codkon FROM Gr_konk')
        konks = dict()
        while self.query.next():
            name = self.query.value(0)
            code = self.query.value(1)
            konks[name] = code 
        return konks