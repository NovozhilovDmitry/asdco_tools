from PyQt6.QtWidgets import (QMainWindow,
                             QWidget,
                             QLabel,
                             QGridLayout,
                             QApplication,
                             QPushButton,
                             QLineEdit,
                             QTextEdit,
                             QCheckBox,
                             QComboBox,
                             QVBoxLayout,
                             QTabWidget)
from PyQt6.QtCore import QRunnable, QThreadPool, QSettings, QSize
from myLogging import logger
import sys
import os
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


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600


class Worker(QRunnable):  # отдельный поток для выполнения
    def __init__(self):
        super(Worker, self).__init__()
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)

    def run(self):
        sql1 = 'select name from pdb'
        pdb_list = [
            'NDA_TEST_1', 'NDA_TEST_2', 'NDA_TEST_3',
            'KRP_TEST_1', 'KRP_TEST_2', 'KRP_TEST_3',
            'TMS_TEST_1', 'TMS_TEST_2', 'TMS_TEST_3'
        ]  # заполняется из БД
        for i in pdb_list:
            win.list_pdb.addItem(i)
        logger.info(f'Список заполнен существующими pdb в количестве {len(pdb_list)}')
        self.settings.setValue('list', pdb_list)


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("ASDCO tools с вкладками")  # заголовок главного окна
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.layout = QWidget()
        self.main_layout = QVBoxLayout()
        self.top_grid_layout = QGridLayout()
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        self.threadpool = QThreadPool()
        self.schemas = {'credit': 0, 'deposit': 0, 'credit_ar': 0, 'deposit_ar': 0, 'reserve': 0}
        self.header_layout()  # функция с добавленными элементами интерфейса для верхней части
        self.footer_layout()  # функция с добавленными элементами интерфейса для нижней части
        # добавление на макеты
        self.tab_schemas.setLayout(self.tab_schemas.layout)
        self.main_layout.addLayout(self.top_grid_layout)
        self.main_layout.addWidget(self.tabs)
        self.layout.setLayout(self.main_layout)
        self.setCentralWidget(self.layout)
        self.initialization_settings()  # вызов функции с инициализацией сохраненных значений

    def check_connect(self):
        text_for_area = 'Проверка подключения: успешно или неуспешно'
        self.input_main_area.setText(text_for_area)

    def cloning_pdb(self):
        text_for_area = 'Клонирование выбранной PDB'
        success = 'УСПЕШНО'
        self.input_main_area.append(text_for_area)
        # self.input_main_area.setHtml(
        #     f"""<font color='black'>{text_for_area}</font><br>
        #     <font color='green'>{success}</font>""")
        self.input_main_area.append(success)

    def deleting_pdb(self):
        text_for_area = 'Удаление выбранной PDB провалено'
        self.input_main_area.append(text_for_area)

    def check_pdb(self):
        self.input_main_area.setText('Существующие PDB')
        logger.info('Выполнение задачи с запросом существующих PDB в отдельном потоке. Настройки приложения сохранены')
        worker = Worker()
        self.threadpool.start(worker)

    def creating_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.setText(f'Создание схем: {checked_schemas}')

    def deleting_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.setText(f'Удаление схем: {checked_schemas}')
        # self.input_schemas_area.append(f'Нажаты следующие чекбоксы: {self.checkbox_schema5.isChecked()}')

    def checkschema1(self, checked):
        if checked:
            self.schemas['credit'] = 1
        else:
            self.schemas['credit'] = 0

    def checkschema2(self, checked):
        if checked:
            self.schemas['deposit'] = 1
        else:
            self.schemas['deposit'] = 0

    def checkschema3(self, checked):
        if checked:
            self.schemas['credit_ar'] = 1
        else:
            self.schemas['credit_ar'] = 0

    def checkschema4(self, checked):
        if checked:
            self.schemas['deposit_ar'] = 1
        else:
            self.schemas['deposit_ar'] = 0

    def checkschema5(self, checked):
        if checked:
            self.schemas['reserve'] = 1
        else:
            self.schemas['reserve'] = 0

    def closeEvent(self, event):
        """
        :param event: событие, которое можно принять или переопределить при закрытии
        :return: охранение настроек при закрытии приложения
        """
        # настройки значений из верхней панели
        self.settings.setValue('login', self.input_main_login.text())
        self.settings.setValue('connectline', self.line_main_connect.text())
        self.settings.setValue('password', self.input_main_password.text())
        # настройки вкладки со схемами
        self.settings.setValue('credit1_schemaname', self.input_schema1_name.text())
        self.settings.setValue('deposit1_schemaname', self.input_schema2_name.text())
        self.settings.setValue('credit1_ar_schemaname', self.input_schema3_name.text())
        self.settings.setValue('deposit1_ar_schemaname', self.input_schema4_name.text())
        self.settings.setValue('reserve_schemaname', self.input_schema5_name.text())
        self.settings.setValue('credit1_schemapass', self.input_schema1_pass.text())
        self.settings.setValue('deposit1_schemapass', self.input_schema2_pass.text())
        self.settings.setValue('credit1_ar_schemapass', self.input_schema3_pass.text())
        self.settings.setValue('deposit1_ar_schemapass', self.input_schema4_pass.text())
        self.settings.setValue('reserve_schemapass', self.input_schema5_pass.text())

    def initialization_settings(self):
        """
        :return: заполнение полей из настроек
        """
        # главное окно
        self.input_main_login.setText(self.settings.value('login'))
        self.input_main_password.setText(self.settings.value('password'))
        self.line_main_connect.setText(self.settings.value('connectline'))
        # вкладка со схемами
        self.input_schema1_name.setText(self.settings.value('credit1_schemaname'))
        self.input_schema2_name.setText(self.settings.value('deposit1_schemaname'))
        self.input_schema3_name.setText(self.settings.value('credit1_ar_schemaname'))
        self.input_schema4_name.setText(self.settings.value('deposit1_ar_schemaname'))
        self.input_schema1_pass.setText(self.settings.value('credit1_schemapass'))
        self.input_schema2_pass.setText(self.settings.value('deposit1_schemapass'))
        self.input_schema3_pass.setText(self.settings.value('credit1_ar_schemapass'))
        self.input_schema4_pass.setText(self.settings.value('deposit1_ar_schemapass'))
        # список
        for i in self.settings.value('list'):
            self.list_pdb.addItem(i)

    def header_layout(self):
        """
        :return: добавлние виджетов в верхнюю часть интерфейса на главном окне
        """
        self.label_main_login = QLabel('Пользователь sysdba')
        self.input_main_login = QLineEdit()
        self.input_main_password = QLineEdit()
        self.input_main_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.label_main_connect = QLabel('Строка подключения')
        self.line_main_connect = QLineEdit()
        self.label_pdb = QLabel('Имя PDB')
        self.list_pdb = QComboBox()
        self.line_for_combobox = QLineEdit()
        self.list_pdb.setLineEdit(self.line_for_combobox)
        self.btn_current_pdb = QPushButton('Показать существующие pdb')
        self.btn_current_pdb.clicked.connect(self.check_pdb)
        self.top_grid_layout.addWidget(self.label_main_login, 0, 0)
        self.top_grid_layout.addWidget(self.input_main_login, 0, 1)
        self.top_grid_layout.addWidget(self.input_main_password, 0, 2)
        self.top_grid_layout.addWidget(self.label_main_connect, 1, 0)
        self.top_grid_layout.addWidget(self.line_main_connect, 1, 1, 1, 2)
        self.top_grid_layout.addWidget(self.label_pdb, 2, 0)
        self.top_grid_layout.addWidget(self.list_pdb, 2, 1)
        self.top_grid_layout.addWidget(self.btn_current_pdb, 2, 2)

    def footer_layout(self):
        """
        :return: добавление вкладок в интерфейсе со своими виджетами
        """
        self.tabs = QTabWidget()
        self.tab_control = QWidget()
        self.tab_schemas = QWidget()
        self.tab_control.layout = QGridLayout()
        self.tab_schemas.layout = QGridLayout()
        self.tabs.addTab(self.tab_control, "Управление PDB")
        self.tabs.addTab(self.tab_schemas, "Управление схемами")
        self.tabs.setMovable(True)
        # self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.input_newpdb = QLineEdit()
        self.btn_connect = QPushButton('Проверить подключение')
        self.btn_connect.clicked.connect(self.check_connect)
        self.btn_connect.setStyleSheet('width: 300')
        self.btn_clone_pdb = QPushButton('Клонировать PDB')  # тут же сделать pdb writeble
        self.btn_clone_pdb.clicked.connect(self.cloning_pdb)
        self.btn_clone_pdb.setStyleSheet('width: 300')
        self.btn_delete_pdb = QPushButton('Удалить PDB')
        self.btn_delete_pdb.clicked.connect(self.deleting_pdb)
        self.input_main_area = QTextEdit()
        self.input_main_area.setStyleSheet('background-color: #fefefe;')
        # управление pdb
        self.tab_control.layout.addWidget(self.input_newpdb, 1, 0)
        self.tab_control.layout.addWidget(self.btn_connect, 1, 1)
        self.tab_control.layout.addWidget(self.btn_clone_pdb, 1, 2)
        self.tab_control.layout.addWidget(self.input_main_area, 2, 0, 1, 3)
        self.tab_control.layout.addWidget(self.btn_delete_pdb, 3, 0)
        self.tab_control.setLayout(self.tab_control.layout)
        # управление схемами
        self.label_schema1 = QLabel('Имя схемы')
        self.input_schema1_name = QLineEdit()
        self.input_schema1_pass = QLineEdit()
        self.input_schema1_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema1 = QCheckBox()
        self.checkbox_schema1.stateChanged.connect(self.checkschema1)
        self.label_schema2 = QLabel('Имя схемы')
        self.input_schema2_name = QLineEdit()
        self.input_schema2_pass = QLineEdit()
        self.input_schema2_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema2 = QCheckBox()
        self.checkbox_schema2.stateChanged.connect(self.checkschema2)
        self.label_schema3 = QLabel('Имя схемы')
        self.input_schema3_name = QLineEdit()
        self.input_schema3_pass = QLineEdit()
        self.input_schema3_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema3 = QCheckBox()
        self.checkbox_schema3.stateChanged.connect(self.checkschema3)
        self.label_schema4 = QLabel('Имя схемы')
        self.input_schema4_name = QLineEdit()
        self.input_schema4_pass = QLineEdit()
        self.input_schema4_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema4 = QCheckBox()
        self.checkbox_schema4.stateChanged.connect(self.checkschema4)
        self.label_schema5 = QLabel('Имя схемы')
        self.input_schema5_name = QLineEdit()
        self.input_schema5_pass = QLineEdit()
        self.input_schema5_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema5 = QCheckBox()
        self.checkbox_schema5.stateChanged.connect(self.checkschema5)
        self.btn_create_schema = QPushButton('Создать схему')
        self.btn_create_schema.clicked.connect(self.creating_schemas)
        self.btn_delete_schema = QPushButton('Удалить схему')
        self.btn_delete_schema.clicked.connect(self.deleting_schemas)
        self.input_schemas_area = QTextEdit()
        self.input_main_area.setStyleSheet('background-color: #fefefe;')
        self.tab_schemas.layout.addWidget(self.label_schema1, 2, 0)
        self.tab_schemas.layout.addWidget(self.input_schema1_name, 2, 1)
        self.tab_schemas.layout.addWidget(self.input_schema1_pass, 2, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema1, 2, 3)
        self.tab_schemas.layout.addWidget(self.label_schema2, 3, 0)
        self.tab_schemas.layout.addWidget(self.input_schema2_name, 3, 1)
        self.tab_schemas.layout.addWidget(self.input_schema2_pass, 3, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema2, 3, 3)
        self.tab_schemas.layout.addWidget(self.label_schema3, 4, 0)
        self.tab_schemas.layout.addWidget(self.input_schema3_name, 4, 1)
        self.tab_schemas.layout.addWidget(self.input_schema3_pass, 4, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema3, 4, 3)
        self.tab_schemas.layout.addWidget(self.label_schema4, 5, 0)
        self.tab_schemas.layout.addWidget(self.input_schema4_name, 5, 1)
        self.tab_schemas.layout.addWidget(self.input_schema4_pass, 5, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema4, 5, 3)
        self.tab_schemas.layout.addWidget(self.label_schema5, 6, 0)
        self.tab_schemas.layout.addWidget(self.input_schema5_name, 6, 1)
        self.tab_schemas.layout.addWidget(self.input_schema5_pass, 6, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema5, 6, 3)
        self.tab_schemas.layout.addWidget(self.btn_create_schema, 7, 1)
        self.tab_schemas.layout.addWidget(self.btn_delete_schema, 7, 2)
        self.tab_schemas.layout.addWidget(self.input_schemas_area, 8, 0, 1, 4)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
