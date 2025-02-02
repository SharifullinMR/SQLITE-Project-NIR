from mainWindow import MainWindow

def main():
    db_file = 'C:/Users/Marsohodik/Desktop/BD/SQL_lab-work_misha/v7_data/db_filled.sqlite'
    mainWindow = MainWindow(db_file)
    mainWindow.window.show()
    mainWindow.app.exec()

if __name__ == '__main__':
    main()