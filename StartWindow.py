from additions import MAIN_WINDOW_TITLE, VERSION
from PyQt6.QtWidgets import (QMainWindow,
                             QWidget,
                             QLabel,
                             QGridLayout,
                             QApplication,
                             QPushButton,
                             QLineEdit,
                             QTextEdit)
from PyQt6.QtCore import QRunnable, QThreadPool, Qt
import os
import sys
import argparse
from myLogging import logger
from oracle.OracleDelete import OracleDelete
from oracle.OracleCreate import OracleCreate
from oracle.OracleImport import OracleImport
from oracle.OracleExport import OracleExport
from oracle.OracleImpdp import OracleImpdp
from oracle.OracleExpdp import OracleExpdp
from oracle.OracleRemoteManagePDB import OracleRemoteManagePDB
from oracle.OracleRemoteDeletePDB import OracleRemoteDeletePDB
from oracle.OracleRemoteExpdp import OracleRemoteExpdp
from oracle.OracleRemoteImpdp import OracleRemoteImpdp
from additions import load_config

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600


class Worker(QRunnable):
    def run(self):
        print('Начинается выполнение потока')
        print('Выполнение потока завершено')


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Генератор конвертов")  # заголовок главного окна
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # начальные размеры главного окна
        # self.get_directory_path = QPushButton('Выбор каталога', self)
        # self.get_directory_path.clicked.connect('какая-то функция')
        self.connect_label = QLabel()
        self.connect_line = QLineEdit()
        self.login_label = QLabel()
        self.login_line = QLineEdit()
        self.pdb_from = QLineEdit()
        self.pdb_to = QLineEdit()
        self.main_area = QTextEdit()

        self.clone_btn = QPushButton('Склонировать базу')
        self.clone_btn.clicked.connect(self.make_clone)
        self.write_btn = QPushButton('Убрать "только для чтения"')
        self.write_btn.clicked.connect(self.make_write)

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.connect_label, 0, 0)
        grid_layout.addWidget(self.connect_line, 0, 1, 1, 2)
        grid_layout.addWidget(self.login_label, 1, 0)
        grid_layout.addWidget(self.login_line, 1, 1, 1, 2)
        grid_layout.addWidget(self.pdb_from, 2, 0)
        grid_layout.addWidget(self.pdb_to, 2, 1)
        grid_layout.addWidget(self.main_area, 3, 0, 1, 2)
        grid_layout.addWidget(self.clone_btn, 4, 0)
        grid_layout.addWidget(self.write_btn, 4, 1)
        widget = QWidget()
        widget.setLayout(grid_layout)
        self.setCentralWidget(widget)
        self.connect_label.setText('Строка подключения')
        self.login_label.setText('Логин/пароль')
        self.threadpool = QThreadPool()
        self.main_area.setEnabled(False)

    def make_clone(self):
        self.main_area.setText('Hello world + test')

    def make_write(self):
        if self.main_area.isEnabled():  # переключение поля редактирования
            self.main_area.setEnabled(False)
        else:
            self.main_area.setEnabled(True)


if __name__ == '__main__':
    # logger.info(f'Start {__file__}')
    app = QApplication(sys.argv)
    style = """QMainWindow {background-color: #fff;}"""
    app.setStyleSheet(style)
    win = Window()
    win.show()
    sys.exit(app.exec())
