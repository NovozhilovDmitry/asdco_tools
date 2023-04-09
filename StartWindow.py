import pathlib
import sys
import traceback
from myLogging import logger
from PyQt6.QtGui import QPixmap, QIcon
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
                             QTabWidget,
                             QTableWidget,
                             QTableWidgetItem,
                             QHeaderView,
                             QPlainTextEdit,
                             QProgressBar,
                             QFileDialog)
from functions import (get_string_show_pdbs,
                       delete_temp_directory,
                       runnings_sqlplus_scripts_with_subprocess,
                       get_string_check_oracle_connection,
                       formating_sqlplus_results_and_return_pdb_names,
                       get_string_clone_pdb,
                       get_string_make_pdb_writable,
                       get_string_delete_pdb,
                       runnings_check_connect,
                       format_list_result)


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
        self.setWindowTitle("ASDCO TOOLS")  # заголовок главного окна
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.btn_icon = QPixmap("others/hedgehog.png")
        self.layout = QWidget()
        self.main_layout = QVBoxLayout()
        self.top_grid_layout = QGridLayout()
        self.tabs = QTabWidget()
        self.tab_control = QWidget()
        self.tab_schemas = QWidget()
        self.threadpool = QThreadPool()
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        self.schemas = {'Схема_1': 0, 'Схема_2': 0, 'Схема_3': 0, 'Схема_4': 0, 'Схема_5': 0}
        self.header_layout()  # функция с добавленными элементами интерфейса для верхней части
        self.pdb_tab()  # функция с добавленными элементами вкладки pdb
        self.schemas_tab()  # функция с добавленными элементами вкладки со схемами
        # добавление на макеты
        self.tab_schemas.setLayout(self.tab_schemas.layout)
        self.main_layout.addLayout(self.top_grid_layout)
        self.main_layout.addWidget(self.tabs)
        self.layout.setLayout(self.main_layout)
        self.setCentralWidget(self.layout)
        self.initialization_settings()  # вызов функции с инициализацией сохраненных значений

    def thread_print_output(self, s):
        """
        :param s: передается результат из вызванной функции потока
        :return: слот для сигнала из потока о завершении выполнения функции
        """
        logger.info(s)

    def thread_print_complete(self):
        """
        :return: слот для сигнала о завершении потока
        """
        logger.info(self)

    def thread_check_pdb(self):
        """
        :return: передача функции по проверки pdb в отдельном потоке
        """
        logger.info("Функция 'ПОКАЗАТЬ СУЩЕСТВУЮЩИЕ PDB' запущена")
        worker = Worker(self.fn_check_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_check_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        oracle_string = get_string_show_pdbs(sysdba_name, sysdba_password, connection_string)
        result, list_result = runnings_sqlplus_scripts_with_subprocess(oracle_string, return_split_result=True)
        self.input_main_area.appendPlainText(result)
        self.pdb_name_list = formating_sqlplus_results_and_return_pdb_names(list_result)
        self.table.setRowCount(len(self.pdb_name_list))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Имя', 'Дата создания', 'Статус', 'Размер'])
        new_list = format_list_result(list_result)
        row = 0
        for i in new_list:
            self.table.setItem(row, 0, QTableWidgetItem(i[0]))
            self.table.setItem(row, 1, QTableWidgetItem(i[1]))
            self.table.setItem(row, 2, QTableWidgetItem(i[2]))
            self.table.setItem(row, 3, QTableWidgetItem(i[3]))
            row += 1
        self.list_pdb.clear()
        for i in self.pdb_name_list:
            self.list_pdb.addItem(i)
        self.input_main_area.verticalScrollBar().setValue(self.input_main_area.verticalScrollBar().maximum())
        return "Функция 'ПОКАЗАТЬ СУЩЕСТВУЮЩИЕ PDB' выполнена успешно"

    def thread_check_connection(self):
        """
        :return: передача функции по ппроверке подключения к cdb в отдельном потоке
        """
        logger.info("Функция 'ПРОВЕРИТЬ ПОДКЛЮЧЕНИЕ под ролью SYSDBA на базе CDB запущена, на базе PDB' запущена")
        worker = Worker(self.fn_check_connect)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_check_connect(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        oracle_string, sql = get_string_check_oracle_connection(connection_string,
                                                                sysdba_name,
                                                                sysdba_password)
        result = runnings_check_connect(oracle_string, sql)
        self.input_main_area.appendPlainText(result)
        self.input_main_area.verticalScrollBar().setValue(self.input_main_area.verticalScrollBar().maximum())
        logger.info(result)
        if self.input_newpdb.text().upper() == '':
            self.input_main_area.appendPlainText('Имя PDB не указано')
            logger.info('Имя PDB не указано. Кнопка осталась заблокирована')
        elif self.input_newpdb.text().upper() == self.list_pdb.currentText().upper():
            self.input_main_area.appendPlainText('Указанная PDB и существующая база данных идентичны')
            logger.info('Указанная PDB и существующая база данных идентичны. Кнопка осталась заблокирована')
        elif self.input_newpdb.text().upper() in self.pdb_name_list:
            self.input_main_area.appendPlainText('Указанная база данных ПРИСУТСТВУЕТ в списке')
            self.btn_clone_pdb.setEnabled(True)
            self.btn_delete_pdb.setEnabled(True)
            self.btn_make_pdb_for_write.setEnabled(True)
            logger.info('Указанная база данных ПРИСУТСТВУЕТ в списке. Кнопка разблокирована')
        elif self.input_newpdb.text().upper() not in self.pdb_name_list:
            self.input_main_area.appendPlainText('Указанная база данных ОТСУТСТВУЕТ в списке. Это новая PDB?')
            self.btn_clone_pdb.setEnabled(True)
            self.btn_delete_pdb.setEnabled(True)
            self.btn_make_pdb_for_write.setEnabled(True)
            logger.info('Указанная база данных ОТСУТСТВУЕТ в списке. Это новая PDB? Кнопка разблокирована')
        self.input_main_area.verticalScrollBar().setValue(self.input_main_area.verticalScrollBar().maximum())
        return "Функция 'ПРОВЕРКА СОЕДИНЕНИЯ С БД' выполнена успешно"

    def thread_cloning_pdb(self):
        """
        :return: передача функции клонирования pdb в отдельном потоке
        """
        logger.info("Функция 'КЛОНИРОВАНИЕ PDB' запущена")
        worker = Worker(self.fn_cloning_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_cloning_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        schema_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        pdb_name_clone = self.input_newpdb.text().upper()
        self.btn_clone_pdb.setEnabled(False)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write.setEnabled(False)
        oracle_string = get_string_clone_pdb(connection_string,
                                             schema_name,
                                             schema_password,
                                             pdb_name,
                                             pdb_name_clone)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        self.btn_clone_pdb.setEnabled(True)
        self.btn_delete_pdb.setEnabled(True)
        self.btn_make_pdb_for_write.setEnabled(True)
        self.input_main_area.appendPlainText(result)
        self.input_main_area.verticalScrollBar().setValue(self.input_main_area.verticalScrollBar().maximum())
        return f"Клонирование PDB завершено. Имя новой PDB {pdb_name_clone}"

    def thread_deleting_pdb(self):
        """
        :return: передача функции удаления pdb в отдельном потоке
        """
        logger.info("Функция 'УДАЛИТЬ PDB' запущена")
        worker = Worker(self.fn_deleting_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_deleting_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        schema_password = self.input_main_password.text()
        pdb_name = self.input_newpdb.text().upper()
        self.btn_clone_pdb.setEnabled(False)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write.setEnabled(False)
        oracle_string = get_string_delete_pdb(connection_string,
                                              schema_name,
                                              schema_password,
                                              pdb_name)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        self.btn_clone_pdb.setEnabled(True)
        self.btn_delete_pdb.setEnabled(True)
        self.btn_make_pdb_for_write.setEnabled(True)
        self.input_main_area.appendPlainText(result)
        self.input_main_area.verticalScrollBar().setValue(self.input_main_area.verticalScrollBar().maximum())
        return f"{pdb_name} удалена"

    def thread_make_pdb_writable(self):
        """
        :return: передача функции по переводу pdb из режима только для чтения в отдельном потоке
        """
        logger.info("Функция 'СДЕЛАТЬ PDB ДОСТУПНОЙ ДЛЯ ЗАПИСИ' запущена")
        worker = Worker(self.fn_writable_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_writable_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        schema_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        oracle_string = get_string_make_pdb_writable(connection_string,
                                                     schema_name,
                                                     schema_password,
                                                     pdb_name)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        self.input_main_area.appendPlainText('PDB переведена в режим доступной для записи \n' + result)
        self.input_main_area.verticalScrollBar().setValue(self.input_main_area.verticalScrollBar().maximum())
        return f'PDB {pdb_name} переведена в режим доступной для записи'

    def creating_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.setText(f'Создание схем: {checked_schemas}')

    def deleting_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.setText(f'Удаление схем: {checked_schemas}')

    def fn_checkbox_clicked_for_schemas(self, checked):
        checkbox = self.sender()
        if checked:
            self.schemas[checkbox.text()] = 1
        else:
            self.schemas[checkbox.text()] = 0

    def fn_set_path_for_dumps(self):
        button = self.sender()
        project_path = pathlib.Path.cwd()
        get_dir = QFileDialog.getExistingDirectory(self, caption='Выбрать файл')
        if get_dir:
            get_dir = get_dir
        else:
            get_dir = 'Путь не выбран'
        if button is self.btn_path_schema1:
            self.path_schema1.setText(get_dir)
        elif button is self.btn_path_schema2:
            self.path_schema2.setText(get_dir)
        elif button is self.btn_path_schema3:
            self.path_schema3.setText(get_dir)
        elif button is self.btn_path_schema4:
            self.path_schema4.setText(get_dir)
        elif button is self.btn_path_schema5:
            self.path_schema5.setText(get_dir)

    def closeEvent(self, event):
        """
        :param event: событие, которое можно принять или переопределить при закрытии
        :return: охранение настроек при закрытии приложения
        """
        # настройки значений из верхней панели
        self.settings.setValue('login', self.input_main_login.text())
        self.settings.setValue('connectline', self.line_main_connect.text())
        self.settings.setValue('password', self.input_main_password.text())
        self.settings.setValue('PDB_name', self.list_pdb.currentText())
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
        self.list_pdb.setCurrentText(self.settings.value('PDB_name'))
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

    def pdb_tab(self):
        """
        :return: добавление виджетов на вкладку с pdb
        """
        self.tab_control.layout = QGridLayout()
        self.tabs.addTab(self.tab_control, "Управление PDB")
        self.input_newpdb = QLineEdit()
        self.input_newpdb.setPlaceholderText('Введите имя PDB')
        self.btn_connect = QPushButton('Проверить подключение')
        self.btn_connect.clicked.connect(self.thread_check_connection)
        self.btn_connect.setStyleSheet('width: 300')
        self.btn_clone_pdb = QPushButton('Клонировать PDB')  # тут же сделать pdb writeble
        self.btn_clone_pdb.setEnabled(False)
        self.btn_clone_pdb.clicked.connect(self.thread_cloning_pdb)
        self.btn_clone_pdb.setStyleSheet('width: 300')
        self.btn_delete_pdb = QPushButton('Удалить PDB')
        self.btn_delete_pdb.clicked.connect(self.thread_deleting_pdb)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write = QPushButton('Сделать PDB доступной для записи')
        self.btn_make_pdb_for_write.clicked.connect(self.thread_make_pdb_writable)
        self.btn_make_pdb_for_write.setEnabled(False)
        self.input_main_area = QPlainTextEdit()
        self.input_main_area.setFixedSize(WINDOW_WIDTH, 100)
        self.progressbar = QProgressBar()
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tab_control.layout.addWidget(self.input_newpdb, 1, 0)
        self.tab_control.layout.addWidget(self.btn_connect, 1, 1)
        self.tab_control.layout.addWidget(self.btn_clone_pdb, 1, 2)
        self.tab_control.layout.addWidget(self.table, 2, 0, 1, 3)
        self.tab_control.layout.addWidget(self.btn_make_pdb_for_write, 3, 0)
        self.tab_control.layout.addWidget(self.progressbar, 3, 1)
        self.tab_control.layout.addWidget(self.btn_delete_pdb, 3, 2)
        self.tab_control.layout.addWidget(self.input_main_area, 5, 0, 1, 3)
        self.tab_control.setLayout(self.tab_control.layout)

    def schemas_tab(self):
        """
        :return: добавление виджетов на вкладку с схемами
        """
        self.tab_schemas.layout = QGridLayout()
        self.tabs.addTab(self.tab_schemas, "Управление схемами")
        self.input_schema1_name = QLineEdit()
        self.input_schema1_pass = QLineEdit()
        self.input_schema1_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema1 = QCheckBox('Схема_1')
        self.checkbox_schema1.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.input_schema2_name = QLineEdit()
        self.input_schema2_pass = QLineEdit()
        self.input_schema2_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema2 = QCheckBox('Схема_2')
        self.checkbox_schema2.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.input_schema3_name = QLineEdit()
        self.input_schema3_pass = QLineEdit()
        self.input_schema3_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema3 = QCheckBox('Схема_3')
        self.checkbox_schema3.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.input_schema4_name = QLineEdit()
        self.input_schema4_pass = QLineEdit()
        self.input_schema4_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema4 = QCheckBox('Схема_4')
        self.checkbox_schema4.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.input_schema5_name = QLineEdit()
        self.input_schema5_pass = QLineEdit()
        self.input_schema5_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema5 = QCheckBox('Схема_5')
        self.checkbox_schema5.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.btn_create_schema = QPushButton('Создать схему')
        self.btn_create_schema.clicked.connect(self.creating_schemas)
        self.btn_delete_schema = QPushButton('Удалить схему')
        self.btn_delete_schema.clicked.connect(self.deleting_schemas)
        self.path_schema1 = QLineEdit()
        self.btn_path_schema1 = QPushButton()
        self.btn_path_schema1.setIcon(QIcon(self.btn_icon))
        self.path_schema1.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema1.clicked.connect(self.fn_set_path_for_dumps)
        self.path_schema2 = QLineEdit()
        self.btn_path_schema2 = QPushButton()
        self.btn_path_schema2.setIcon(QIcon(self.btn_icon))
        self.path_schema2.setPlaceholderText('ВВведите путь или нажмите на кнопку')
        self.btn_path_schema2.clicked.connect(self.fn_set_path_for_dumps)
        self.path_schema3 = QLineEdit()
        self.btn_path_schema3 = QPushButton()
        self.btn_path_schema3.setIcon(QIcon(self.btn_icon))
        self.path_schema3.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema3.clicked.connect(self.fn_set_path_for_dumps)
        self.path_schema4 = QLineEdit()
        self.btn_path_schema4 = QPushButton()
        self.btn_path_schema4.setIcon(QIcon(self.btn_icon))
        self.path_schema4.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema4.clicked.connect(self.fn_set_path_for_dumps)
        self.path_schema5 = QLineEdit()
        self.btn_path_schema5 = QPushButton()
        self.btn_path_schema5.setIcon(QIcon(self.btn_icon))
        self.path_schema5.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema5.clicked.connect(self.fn_set_path_for_dumps)
        self.input_schemas_area = QTextEdit()
        self.tab_schemas.layout.addWidget(self.checkbox_schema1, 0, 0)
        self.tab_schemas.layout.addWidget(self.input_schema1_name, 0, 1)
        self.tab_schemas.layout.addWidget(self.input_schema1_pass, 0, 2)
        self.tab_schemas.layout.addWidget(self.path_schema1, 0, 3)
        self.tab_schemas.layout.addWidget(self.btn_path_schema1, 0, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema2, 1, 0)
        self.tab_schemas.layout.addWidget(self.input_schema2_name, 1, 1)
        self.tab_schemas.layout.addWidget(self.input_schema2_pass, 1, 2)
        self.tab_schemas.layout.addWidget(self.path_schema2, 1, 3)
        self.tab_schemas.layout.addWidget(self.btn_path_schema2, 1, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema3, 2, 0)
        self.tab_schemas.layout.addWidget(self.input_schema3_name, 2, 1)
        self.tab_schemas.layout.addWidget(self.input_schema3_pass, 2, 2)
        self.tab_schemas.layout.addWidget(self.path_schema3, 2, 3)
        self.tab_schemas.layout.addWidget(self.btn_path_schema3, 2, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema4, 3, 0)
        self.tab_schemas.layout.addWidget(self.input_schema4_name, 3, 1)
        self.tab_schemas.layout.addWidget(self.input_schema4_pass, 3, 2)
        self.tab_schemas.layout.addWidget(self.path_schema4, 3, 3)
        self.tab_schemas.layout.addWidget(self.btn_path_schema4, 3, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema5, 4, 0)
        self.tab_schemas.layout.addWidget(self.input_schema5_name, 4, 1)
        self.tab_schemas.layout.addWidget(self.input_schema5_pass, 4, 2)
        self.tab_schemas.layout.addWidget(self.path_schema5, 4, 3)
        self.tab_schemas.layout.addWidget(self.btn_path_schema5, 4, 4)
        self.tab_schemas.layout.addWidget(self.btn_create_schema, 5, 1)
        self.tab_schemas.layout.addWidget(self.btn_delete_schema, 5, 2)
        self.tab_schemas.layout.addWidget(self.input_schemas_area, 6, 0, 1, 4)


if __name__ == '__main__':
    logger.info(f'Запущен файл {__file__}')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())

# добавить progressbar в выполнение функции
# сделать функцию (или 2) для определения формата дампа ->
# если архив, то предложение разархивировать, если дамп, то берем дамп
# падает программа если не проверены бд и не заполнен список?
# после клонирования (удаления?) почему-то выводится ошибка. посмотреть номер ошибки и текст
