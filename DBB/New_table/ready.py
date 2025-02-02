from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
import sys
from PyQt6.QtSql import *
from pandas.io.sql import SQLTable
import pandas as pd
import sqlite3

def on_click():
    print('Hello world!')

def connect_db(db_file):
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(db_file)
    if not db.open():
        print("false")
        return False
    return db

app = QApplication([])
db_file = "DataBases/db_filled.sqlite"
table_name='Gr_prog'
table_name1='Gr_prog1'

if not connect_db(db_file):
    sys.exit(-1)
else:
    print("connection ok")
Form, Window = uic.loadUiType("MainForm.ui")

Gr_prog=QSqlTableModel()
Gr_prog.setTable('Gr_prog')
Gr_prog.select()

window = Window()
form = Form()
form.setupUi(window)
form.pushButton.clicked.connect(on_click)
form.tableView.setSortingEnabled(True)
form.tableView.setModel(Gr_prog)
form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
#form.tableView.setColumnWidth(0, 30)
#form.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
window.show()
app.exec()