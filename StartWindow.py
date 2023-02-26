from PyQt6.QtWidgets import (QMainWindow,
                             QWidget,
                             QLabel,
                             QGridLayout,
                             QApplication,
                             QPushButton,
                             QLineEdit,
                             QTextEdit,
                             QComboBox,
                             QCheckBox)
from PyQt6.QtCore import QRunnable, QThreadPool, QSettings
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
# TODO: вынести ширину и высоту окна в файл настроек?
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600


class Worker(QRunnable):  # отдельный поток для выполнения
    def __init__(self):
        super(Worker, self).__init__()
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)

    def run(self):
        sql1 = 'select name from pdb'
        # TODO: заменить pdb_list на результаты запроса sql1
        pdb_list = [
            'NDA_TEST_1', 'NDA_TEST_2', 'NDA_TEST_3',
            'KRP_TEST_1', 'KRP_TEST_2', 'KRP_TEST_3',
            'TMS_TEST_1', 'TMS_TEST_2', 'TMS_TEST_3'
        ]  # заполняется из БД
        for i in pdb_list:
            win.list_pdb.addItem(i)
        logger.info(f'Список заполнен существующими pdb в количестве {len(pdb_list)}')
        self.settings.setValue('list', pdb_list)


class WindowSchemas(QWidget):  # с чекбоксами
    def __init__(self):
        super(WindowSchemas, self).__init__()
        self.setWindowTitle('Управление схемами')
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        grid_layout = QGridLayout()
        self.label_login = QLabel('Пользователь sysdba')
        self.input_login = QLineEdit()  # должен быть заполнен из главного окна
        self.input_password = QLineEdit()  # должен быть заполнен из главного окна
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.label_connect = QLabel('Строка подключения')
        self.line_connect = QLineEdit()  # должен быть заполнен из главного окна
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
        self.btn_create_schema = QPushButton('Создать схему')
        self.btn_create_schema.clicked.connect(self.creating_schemas)
        self.btn_delete_schema = QPushButton('Удалить схему')
        self.btn_delete_schema.clicked.connect(self.deleting_schemas)
        self.input_main_area = QTextEdit()
        self.input_main_area.setStyleSheet('background-color: #fefefe;')
        grid_layout.addWidget(self.label_login, 0, 0)
        grid_layout.addWidget(self.input_login, 0, 1)
        grid_layout.addWidget(self.input_password, 0, 2)
        grid_layout.addWidget(self.label_connect, 1, 0)
        grid_layout.addWidget(self.line_connect, 1, 1, 1, 2)
        grid_layout.addWidget(self.label_schema1, 2, 0)
        grid_layout.addWidget(self.input_schema1_name, 2, 1)
        grid_layout.addWidget(self.input_schema1_pass, 2, 2)
        grid_layout.addWidget(self.checkbox_schema1, 2, 3)
        grid_layout.addWidget(self.label_schema2, 3, 0)
        grid_layout.addWidget(self.input_schema2_name, 3, 1)
        grid_layout.addWidget(self.input_schema2_pass, 3, 2)
        grid_layout.addWidget(self.checkbox_schema2, 3, 3)
        grid_layout.addWidget(self.label_schema3, 4, 0)
        grid_layout.addWidget(self.input_schema3_name, 4, 1)
        grid_layout.addWidget(self.input_schema3_pass, 4, 2)
        grid_layout.addWidget(self.checkbox_schema3, 4, 3)
        grid_layout.addWidget(self.label_schema4, 5, 0)
        grid_layout.addWidget(self.input_schema4_name, 5, 1)
        grid_layout.addWidget(self.input_schema4_pass, 5, 2)
        grid_layout.addWidget(self.checkbox_schema4, 5, 3)
        grid_layout.addWidget(self.btn_create_schema, 6, 1)
        grid_layout.addWidget(self.btn_delete_schema, 6, 2)
        grid_layout.addWidget(self.input_main_area, 7, 0, 1, 4)
        self.setLayout(grid_layout)
        self.input_main_area.setEnabled(False)
        self.schemas = {'credit': 0, 'deposit': 0, 'credit_ar': 0, 'deposit_ar': 0}
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        self.input_login.setText(self.settings.value('login'))
        self.input_password.setText(self.settings.value('password'))
        self.line_connect.setText(self.settings.value('connectline'))
        self.input_schema1_name.setText(self.settings.value('credit1_schemaname'))
        self.input_schema2_name.setText(self.settings.value('deposit1_schemaname'))
        self.input_schema3_name.setText(self.settings.value('credit1_ar_schemaname'))
        self.input_schema4_name.setText(self.settings.value('deposit1_ar_schemaname'))
        self.input_schema1_pass.setText(self.settings.value('credit1_schemapass'))
        self.input_schema2_pass.setText(self.settings.value('deposit1_schemapass'))
        self.input_schema3_pass.setText(self.settings.value('credit1_ar_schemapass'))
        self.input_schema4_pass.setText(self.settings.value('deposit1_ar_schemapass'))
        logger.info('Окно "Управление схемами" проинициализировано без ошибок')

    def creating_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_main_area.setText(f'Создание схем: {checked_schemas}')
        self.settings.setValue('credit1_schemaname', self.input_schema1_name.text())
        self.settings.setValue('deposit1_schemaname', self.input_schema2_name.text())
        self.settings.setValue('credit1_ar_schemaname', self.input_schema3_name.text())
        self.settings.setValue('deposit1_ar_schemaname', self.input_schema4_name.text())
        self.settings.setValue('credit1_schemapass', self.input_schema1_pass.text())
        self.settings.setValue('deposit1_schemapass', self.input_schema2_pass.text())
        self.settings.setValue('credit1_ar_schemapass', self.input_schema3_pass.text())
        self.settings.setValue('deposit1_ar_schemapass', self.input_schema4_pass.text())

    def deleting_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_main_area.setText(f'Удаление схем: {checked_schemas}')

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


class WindowControl(QWidget):
    def __init__(self):
        super(WindowControl, self).__init__()

        self.setWindowTitle('Управление PDB')
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.label_login = QLabel('Пользователь sysdba')
        self.input_login = QLineEdit()  # должен быть заполнен из главного окна
        self.input_password = QLineEdit()  # должен быть заполнен из главного окна
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.label_connect = QLabel('Строка подключения')
        self.line_connect = QLineEdit()  # должен быть заполнен из главного окна
        self.label_pdb = QLabel('Имя PDB')
        self.list_pdb = QComboBox()
        self.input_newpdb = QLineEdit()
        self.btn_connect = QPushButton('Проверить подключение')
        self.btn_connect.clicked.connect(self.check_connect)
        self.btn_clone_pdb = QPushButton('Клонировать PDB')  # тут же сделать pdb writeble
        self.btn_clone_pdb.clicked.connect(self.cloning_pdb)
        self.btn_delete_pdb = QPushButton('Удалить PDB')
        self.btn_delete_pdb.clicked.connect(self.deleting_pdb)
        self.input_main_area = QTextEdit()
        self.input_main_area.setStyleSheet('background-color: #fefefe;')
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.label_login, 0, 0)
        grid_layout.addWidget(self.input_login, 0, 1)
        grid_layout.addWidget(self.input_password, 0, 2)
        grid_layout.addWidget(self.label_connect, 1, 0)
        grid_layout.addWidget(self.line_connect, 1, 1, 1, 2)
        grid_layout.addWidget(self.label_pdb, 2, 0)
        grid_layout.addWidget(self.list_pdb, 2, 1)
        grid_layout.addWidget(self.input_newpdb, 2, 2)
        grid_layout.addWidget(self.btn_connect, 3, 0)
        grid_layout.addWidget(self.btn_clone_pdb, 3, 1)
        grid_layout.addWidget(self.btn_delete_pdb, 3, 2)
        grid_layout.addWidget(self.input_main_area, 4, 0, 1, 3)
        self.setLayout(grid_layout)
        self.input_main_area.setEnabled(False)
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        self.input_login.setText(self.settings.value('login'))
        self.input_password.setText(self.settings.value('password'))
        self.line_connect.setText(self.settings.value('connectline'))
        for i in self.settings.value('list'):
            self.list_pdb.addItem(i)
        logger.info('Окно "Управление PDB" проинициализировано без ошибок')

    def check_connect(self):
        text_for_area = 'Проверка подключения: успешно или неуспешно'
        self.input_main_area.setText(text_for_area)

    def cloning_pdb(self):
        text_for_area = 'Клонирование выбранной PDB'
        self.input_main_area.setText(text_for_area)

    def deleting_pdb(self):
        text_for_area = 'удаление выбранной PDB'
        self.input_main_area.setText(text_for_area)


class Window(QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("ASDCO tools")  # заголовок главного окна
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # начальные размеры главного окна
        self.label_login = QLabel('Пользователь sysdba')
        self.input_login = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.label_connect = QLabel('Строка подключения')
        self.line_connect = QLineEdit()
        self.label_pdb = QLabel('Имя PDB')
        self.list_pdb = QComboBox()
        self.btn_current_pdb = QPushButton('Показать существующие pdb')
        self.btn_current_pdb.clicked.connect(self.check_pdb)
        self.input_main_area = QTextEdit()
        self.input_main_area.setStyleSheet('background-color: #fefefe;')
        self.btn_control = QPushButton('Управление PDB')
        self.btn_control.clicked.connect(self.control_pdb)
        self.btn_scheme = QPushButton('Управление схемами')
        self.btn_scheme.clicked.connect(self.control_schemas)
        self.btn_export_import = QPushButton('Импорт/экспорт схем')
        self.btn_export_import.clicked.connect(self.make_export_and_import)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.label_login, 0, 0)
        grid_layout.addWidget(self.input_login, 0, 1)
        grid_layout.addWidget(self.input_password, 0, 2)
        grid_layout.addWidget(self.label_connect, 1, 0)
        grid_layout.addWidget(self.line_connect, 1, 1, 1, 2)
        grid_layout.addWidget(self.label_pdb, 2, 0)
        grid_layout.addWidget(self.list_pdb, 2, 1)
        grid_layout.addWidget(self.btn_current_pdb, 2, 2)
        grid_layout.addWidget(self.input_main_area, 3, 0, 1, 3)
        grid_layout.addWidget(self.btn_control, 4, 0)
        grid_layout.addWidget(self.btn_scheme, 4, 1)
        grid_layout.addWidget(self.btn_export_import, 4, 2)
        widget = QWidget()
        widget.setLayout(grid_layout)
        self.setCentralWidget(widget)
        self.threadpool = QThreadPool()  # пул потоков
        self.input_main_area.setEnabled(False)  # блокировка области от редактирования
        self.windowschemas = WindowSchemas()
        self.windowcontrol = WindowControl()
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        self.input_login.setText(self.settings.value('login'))
        self.input_password.setText(self.settings.value('password'))
        self.line_connect.setText(self.settings.value('connectline'))
        logger.info('Главное окно проинициализировано без ошибок')

    def control_pdb(self):
        logger.info(f'Вызвано окно управления PDB')
        text_for_area = 'Управление PDB'
        self.input_main_area.setText(text_for_area)
        self.windowcontrol.show()

    def control_schemas(self):
        logger.info(f'Вызвано окно по созданию и удалению схем')
        text_for_area = 'Управление схемами (создание и удаление)'
        self.input_main_area.setText(text_for_area)
        self.windowschemas.show()

    def make_export_and_import(self):
        logger.info(f'Вызвано окно по экспорту и импорту схем')
        text_for_area = 'Экспорт и импорт схем'
        self.input_main_area.setText(text_for_area)

    def check_pdb(self):
        self.input_main_area.setText('Существующие PDB')
        self.settings.setValue('login', self.input_login.text())
        self.settings.setValue('connectline', self.line_connect.text())
        self.settings.setValue('password', self.input_password.text())
        logger.info('Выполнение задачи с запросом существующих PDB в отдельном потоке. Настройки приложения сохранены')
        worker = Worker()
        self.threadpool.start(worker)


if __name__ == '__main__':
    logger.info(f'Start {__file__}')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
