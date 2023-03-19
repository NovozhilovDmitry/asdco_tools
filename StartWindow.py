import time
import sys
import traceback
from myLogging import logger
from PyQt6.QtCore import QRunnable, QThreadPool, QSettings, QObject, pyqtSignal, pyqtSlot
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
from functions import (get_string_show_pdbs,
                       delete_temp_directory,
                       runnings_sqlplus_scripts_with_subprocess,
                       get_string_check_oracle_connection)


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600


class WorkerSignals(QObject):
    finish = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:  # выполняем переданный из window метод
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()  # формирует ошибку?
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:  # если ошибок не было, то формируем сигнал .result и передаем результат `result`
            self.signals.result.emit(result)  # Вернуть результат обработки
        finally:
            self.signals.finish.emit()  # Готово


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
        self.schemas = {'Схема_1': 0, 'Схема_2': 0, 'Схема_3': 0, 'Схема_4': 0, 'Схема_5': 0}
        self.header_layout()  # функция с добавленными элементами интерфейса для верхней части
        self.footer_layout()  # функция с добавленными элементами интерфейса для нижней части
        # добавление на макеты
        self.tab_schemas.setLayout(self.tab_schemas.layout)
        self.main_layout.addLayout(self.top_grid_layout)
        self.main_layout.addWidget(self.tabs)
        self.layout.setLayout(self.main_layout)
        self.setCentralWidget(self.layout)
        self.initialization_settings()  # вызов функции с инициализацией сохраненных значений

    def thread_print_output(self, s):  # слот для сигнала из потока о завершении выполнения функции
        logger.info(s)

    def thread_print_complete(self):  # слот для сигнала о завершении потока
        logger.info(self)

    def thread_check_pdb(self):
        logger.info("Функция 'ПОКАЗАТЬ СУЩЕСТВУЮЩИЕ PDB' запущена")
        worker = Worker(self.fn_check_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_check_pdb(self, progress_callback):
        pdb_list = []  # заполняется из БД
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        oracle_string = get_string_show_pdbs(sysdba_name, sysdba_password, connection_string)
        # print('echo exit | sqlplus.exe c##devop/123devop@192.168.1.1:1521 @script_file')
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        self.input_main_area.append(result)
        # for i in pdb_list:
        #     if len(pdb_list) > 1:
        #         win.list_pdb.addItem(i)
        #     elif len(pdb_list) == 1:
        #         win.list_pdb.addItem(pdb_list[0])
        #     else:
        #         pass
        return "Функция 'ПОКАЗАТЬ СУЩЕСТВУЮЩИЕ PDB' выполнена успешно"

    def thread_check_connection(self):
        logger.info("Функция 'ПРОВЕРИТЬ ПОДКЛЮЧЕНИЕ' запущена")
        worker = Worker(self.fn_check_connect)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_check_connect(self):
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        sschema_password = self.input_main_password.text()
        # get_string_check_oracle_connection

    def cloning_pdb(self):
        text_for_area = 'Клонирование выбранной PDB'
        success = 'УСПЕШНО'
        self.input_main_area.append(text_for_area)
        # self.input_main_area.setHtml(
        #     f"""<font color='black'>{text_for_area}</font><br>
        #     <font color='green'>{success}</font>""")

    def deleting_pdb(self):
        text_for_area = 'Удаление выбранной PDB провалено'
        self.input_main_area.append(text_for_area)

    def creating_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.setText(f'Создание схем: {checked_schemas}')

    def deleting_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.setText(f'Удаление схем: {checked_schemas}')

    def fn_checkbox_clicked(self, checked):
        checkbox = self.sender()
        if checked:
            self.schemas[checkbox.text()] = 1
            print(checkbox)
        else:
            self.schemas[checkbox.text()] = 0

    def check_connect(self, n):
        logger.info("Функция 'ПРОВЕРИТЬ ПОДКЛЮЧЕНИЕ' запущена")
        worker = Worker(self.input_list_to_main_area)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.print_output)
        worker.signals.finish.connect(self.thread_complete)
        self.threadpool.start(worker)

    def input_list_to_main_area(self, progress_callback):
        return "Функция 'ПРОВЕРИТЬ ПОДКЛЮЧЕНИЕ' выполнена успешно"

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
        # сохранение размеров и положения окна
        self.settings.beginGroup('GUI')
        self.settings.setValue('width', self.geometry().width())
        self.settings.setValue('height', self.geometry().height())
        self.settings.setValue('x', self.geometry().x())
        self.settings.setValue('y', self.geometry().y())
        self.settings.endGroup()
        delete_temp_directory()  # удалить каталог temp
        logger.debug('Пользовательские настройки сохранены')
        logger.info(f'Файл {__file__} закрыт')

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
        try:
            for i in self.settings.value('list'):
                self.list_pdb.addItem(i)
            logger.debug('Настройки для поля с именами БД загружены.')
        except TypeError:
            pass
            logger.debug('Настройки для поля с именами БД НЕ загружены.')

        try:
            width = int(self.settings.value('GUI/width'))
            height = int(self.settings.value('GUI/height'))
            x = int(self.settings.value('GUI/x'))
            y = int(self.settings.value('GUI/y'))
            self.setGeometry(x, y, width, height)
            logger.debug('Настройки размеров окна загружены.')
        except TypeError:
            pass
            logger.info('Настройки размеров окна НЕ загружены. Установлены размеры по умолчанию')
        logger.debug('Файл с пользовательскими настройками проинициализирован')

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
        self.btn_current_pdb.clicked.connect(self.thread_check_pdb)
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
        # управление pdb
        self.tab_control.layout.addWidget(self.input_newpdb, 1, 0)
        self.tab_control.layout.addWidget(self.btn_connect, 1, 1)
        self.tab_control.layout.addWidget(self.btn_clone_pdb, 1, 2)
        self.tab_control.layout.addWidget(self.input_main_area, 2, 0, 1, 3)
        self.tab_control.layout.addWidget(self.btn_delete_pdb, 3, 0)
        self.tab_control.setLayout(self.tab_control.layout)
        # управление схемами
        self.input_schema1_name = QLineEdit()
        self.input_schema1_pass = QLineEdit()
        self.input_schema1_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema1 = QCheckBox('Схема_1')
        self.checkbox_schema1.stateChanged.connect(self.fn_checkbox_clicked)
        self.input_schema2_name = QLineEdit()
        self.input_schema2_pass = QLineEdit()
        self.input_schema2_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema2 = QCheckBox('Схема_2')
        self.checkbox_schema2.stateChanged.connect(self.fn_checkbox_clicked)
        self.input_schema3_name = QLineEdit()
        self.input_schema3_pass = QLineEdit()
        self.input_schema3_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema3 = QCheckBox('Схема_3')
        self.checkbox_schema3.stateChanged.connect(self.fn_checkbox_clicked)
        self.input_schema4_name = QLineEdit()
        self.input_schema4_pass = QLineEdit()
        self.input_schema4_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema4 = QCheckBox('Схема_4')
        self.checkbox_schema4.stateChanged.connect(self.fn_checkbox_clicked)
        self.input_schema5_name = QLineEdit()
        self.input_schema5_pass = QLineEdit()
        self.input_schema5_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema5 = QCheckBox('Схема_5')
        self.checkbox_schema5.stateChanged.connect(self.fn_checkbox_clicked)
        self.btn_create_schema = QPushButton('Создать схему')
        self.btn_create_schema.clicked.connect(self.creating_schemas)
        self.btn_delete_schema = QPushButton('Удалить схему')
        self.btn_delete_schema.clicked.connect(self.deleting_schemas)
        self.input_schemas_area = QTextEdit()
        self.tab_schemas.layout.addWidget(self.checkbox_schema1, 0, 0)
        self.tab_schemas.layout.addWidget(self.input_schema1_name, 0, 1)
        self.tab_schemas.layout.addWidget(self.input_schema1_pass, 0, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema2, 1, 0)
        self.tab_schemas.layout.addWidget(self.input_schema2_name, 1, 1)
        self.tab_schemas.layout.addWidget(self.input_schema2_pass, 1, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema3, 2, 0)
        self.tab_schemas.layout.addWidget(self.input_schema3_name, 2, 1)
        self.tab_schemas.layout.addWidget(self.input_schema3_pass, 2, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema4, 3, 0)
        self.tab_schemas.layout.addWidget(self.input_schema4_name, 3, 1)
        self.tab_schemas.layout.addWidget(self.input_schema4_pass, 3, 2)
        self.tab_schemas.layout.addWidget(self.checkbox_schema5, 4, 0)
        self.tab_schemas.layout.addWidget(self.input_schema5_name, 4, 1)
        self.tab_schemas.layout.addWidget(self.input_schema5_pass, 4, 2)
        self.tab_schemas.layout.addWidget(self.btn_create_schema, 5, 1)
        self.tab_schemas.layout.addWidget(self.btn_delete_schema, 5, 2)
        self.tab_schemas.layout.addWidget(self.input_schemas_area, 6, 0, 1, 4)


if __name__ == '__main__':
    logger.info(f'Запущен файл {__file__}')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
