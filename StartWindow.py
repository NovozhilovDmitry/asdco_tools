import sys
import traceback
import re
import hashlib
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
                       format_list_result,
                       get_string_create_oracle_schema,
                       get_string_grant_oracle_privilege,
                       get_string_show_oracle_users,
                       get_string_enabled_oracle_asdco_options,
                       get_string_import_oracle_schema)


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
MD5_HEX = 'cdb17afa0d724dbdcc7449c602228c30'


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
            traceback.print_exc()
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
        self.btn_icon = QPixmap("others/folder.png")
        self.layout = QWidget()
        self.main_layout = QVBoxLayout()
        self.top_grid_layout = QGridLayout()
        self.tabs = QTabWidget()
        self.tab_control = QWidget()
        self.tab_schemas = QWidget()
        self.threadpool = QThreadPool()
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        self.schemas = {'schema1': 0, 'schema2': 0, 'schema3': 0, 'schema4': 0, 'schema5': 0}
        self.header_layout()  # функция с добавленными элементами интерфейса для верхней части
        self.pdb_tab()  # функция с добавленными элементами вкладки pdb
        self.schemas_tab()  # функция с добавленными элементами вкладки со схемами
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
        self.pdb_progressbar.setRange(0, 1)

    def thread_check_pdb(self):
        """
        :return: передача функции по проверки pdb в отдельном потоке
        """
        logger.info('Функция просмотра существующих PDB запущена')
        worker = Worker(self.fn_check_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_check_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        self.pdb_progressbar.setRange(0, 0)
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        oracle_string = get_string_show_pdbs(sysdba_name, sysdba_password, connection_string)
        result, list_result = runnings_sqlplus_scripts_with_subprocess(oracle_string, return_split_result=True)
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
        return f'Функция {traceback.extract_stack()[-1][2]} выполнена успешно'

    def thread_check_connection(self):
        """
        :return: передача функции по ппроверке подключения к cdb в отдельном потоке
        """
        logger.info('Функция проверки подключения к PDB запущена')
        worker = Worker(self.fn_check_connect)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_check_connect(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        self.pdb_progressbar.setRange(0, 0)
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        oracle_string = get_string_check_oracle_connection(connection_string, sysdba_name, sysdba_password)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        logger.info(result)
        ora_not_error = re.search(r'CONNECTION SUCCESS', result)
        if ora_not_error.group(0):
            self.btn_clone_pdb.setEnabled(True)
            self.btn_delete_pdb.setEnabled(True)
            self.btn_make_pdb_for_write.setEnabled(True)
            return f'Функция {traceback.extract_stack()[-1][2]} выполнена успешно'
        else:
            logger.warning(result, exc_info=True)
            return f'Не удалось подключиться к PDB. Возможны ошибки на сервере (посмотрите логи)'

    def thread_cloning_pdb(self):
        """
        :return: передача функции клонирования pdb в отдельном потоке
        """
        logger.info('Функция клонирования PDB запущена')
        worker = Worker(self.fn_cloning_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_cloning_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        self.pdb_progressbar.setRange(0, 0)
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        schema_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        pdb_name_clone = self.input_newpdb.text().upper()
        if pdb_name_clone == 'ASDCOEMPTY_ETALON' or pdb_name_clone == 'PDB$SEED':
            logger.error('Заблокирована попытка клонирования на базу ASDCOEMPTY_ETALON или PDB$SEED')
            return f'Функция {traceback.extract_stack()[-1][2]} выполнена, ' \
                   f'но нельзя использовать в новом имени PDB имена ASDCOEMPTY_ETALON/PDB$SEED'

        else:
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
            logger.info(result)
            return f'Функция {traceback.extract_stack()[-1][2]} выполнена успешно. Имя новой PDB {pdb_name_clone}'

    def thread_deleting_pdb(self):
        """
        :return: передача функции удаления pdb в отдельном потоке
        """
        logger.info('Функция удаления PDB запущена')
        worker = Worker(self.fn_deleting_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_deleting_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        self.pdb_progressbar.setRange(0, 0)
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        schema_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        if pdb_name == 'ASDCOEMPTY_ETALON' or pdb_name == 'PDB$SEED':
            logger.error('Заблокирована попытка удаления на базу ASDCOEMPTY_ETALON или PDB$SEED')
            # всплывающее окно, в котором указано, что удалить ASDCOEMPTY_ETALON/PDB$SEED нельзя
            return f'Функция {traceback.extract_stack()[-1][2]} выполнена, но нельзя удалять ASDCOEMPTY_ETALON/PDB$SEED'
        else:
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
            logger.info(result)
            return f'Функция {traceback.extract_stack()[-1][2]} выполнена успешно. {pdb_name} удалена'

    def thread_make_pdb_writable(self):
        """
        :return: передача функции по переводу pdb из режима только для чтения в отдельном потоке
        """
        logger.info("Функция для перевода PDB в режим записи запущена")
        worker = Worker(self.fn_writable_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_writable_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        self.pdb_progressbar.setRange(0, 0)
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        schema_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        oracle_string = get_string_make_pdb_writable(connection_string,
                                                     schema_name,
                                                     schema_password,
                                                     pdb_name)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        logger.info('PDB переведена в режим доступной для записи')
        logger.info(result)
        return f'Функция {traceback.extract_stack()[-1][2]} выполнена успешно. ' \
               f'PDB {pdb_name} переведена в режим доступной для записи'

    def thread_creating_schemas(self):
        worker = Worker(self.fn_creating_schemas)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_creating_schemas(self, progress_callback):
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        bd_name = self.list_pdb.currentText().upper()
        checked_schemas = [key for key in self.schemas.keys() if self.schemas[key] == 1]
        format_checked_schemas = ', '.join(checked_schemas)
        self.input_schemas_area.append(f'Создание схем: {format_checked_schemas}')
        for schema_name in checked_schemas:
            name = eval('self.input_' + schema_name + '_name.text()')
            identified = eval('self.input_' + schema_name + '_pass.text()')
            oracle_string = get_string_create_oracle_schema(connection_string,
                                                            sysdba_name,
                                                            sysdba_password,
                                                            name,
                                                            identified,
                                                            bd_name)
            result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
            self.input_schemas_area.append(result)
            check_result_for_privileges = self.grant_privilege_schemas(connection_string,
                                                                       sysdba_name,
                                                                       sysdba_password,
                                                                       name,
                                                                       bd_name)
            self.input_schemas_area.append(check_result_for_privileges)
            show_schemas_from_pdb = self.show_shemas(connection_string, sysdba_name, sysdba_password, bd_name)
            self.input_schemas_area.append(show_schemas_from_pdb)
            # __import_schemas()  не забыть добавить имя pdb, добавить графическое поле с именем схемы в дампе
            # __enabled_schemes_options()

    def grant_privilege_schemas(self, connection_string, sysdba_name, sysdba_password, schema_name, bd_name):
        oracle_string = get_string_grant_oracle_privilege(connection_string,
                                                          sysdba_name,
                                                          sysdba_password,
                                                          schema_name,
                                                          bd_name)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        return result

    def show_shemas(self, connection_string, sysdba_name, sysdba_password, bd_name):
        oracle_string = get_string_show_oracle_users(sysdba_name, sysdba_password, connection_string, bd_name)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        return result

    def __import_schemas(self, connection_string, pdb_name, schema_name,
                         schema_password, schema_name_in_dump, schema_dump_file):
        oracle_string = get_string_import_oracle_schema(connection_string, pdb_name, schema_name,
                                                        schema_password, schema_name_in_dump, schema_dump_file)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        return result

    def __enabled_schemes_options(self, connection_string, pdb_name, schema_name, schema_password):
        oracle_string = get_string_enabled_oracle_asdco_options(connection_string, pdb_name,
                                                                schema_name, schema_password)
        result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
        return result

    def thread_deleting_schemas(self):
        worker = Worker(self.fn_deleting_schemas)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_deleting_schemas(self):
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.append(f'Удаление схем: {checked_schemas}')

    def fn_checkbox_clicked_for_schemas(self, checked):
        checkbox = self.sender()
        if checked:
            self.schemas[checkbox.name] = 1
        else:
            self.schemas[checkbox.name] = 0

    def fn_set_path_for_dumps(self):
        button = self.sender()
        get_dir = QFileDialog.getOpenFileName(self, caption='Выбрать файл')
        for i in range(1, 6):
            if button is eval('self.btn_path_schema' + str(i)):
                eval('self.path_schema' + str(i) + '.setText(get_dir[0])')

    def closeEvent(self, event):
        """
        :param event: событие, которое можно принять или переопределить при закрытии
        :return: охранение настроек при закрытии приложения
        """
        self.settings.setValue('login', self.input_main_login.text())
        self.settings.setValue('connectline', self.line_main_connect.text())
        self.settings.setValue('password', hashlib.md5(self.input_main_password.text().encode()).hexdigest())
        self.settings.setValue('PDB_name', self.list_pdb.currentText())
        self.settings.beginGroup('GUI')
        self.settings.setValue('width', self.geometry().width())
        self.settings.setValue('height', self.geometry().height())
        self.settings.setValue('x', self.geometry().x())
        self.settings.setValue('y', self.geometry().y())
        self.settings.endGroup()
        self.settings.beginGroup('SCHEMAS')
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
        self.settings.setValue('credit_pdb_schemaname', self.pdb_schema_name1.text())
        self.settings.setValue('deposit_pdb_schemaname', self.pdb_schema_name2.text())
        self.settings.setValue('credit_ar_pdb_schemaname', self.pdb_schema_name3.text())
        self.settings.setValue('deposit_ar_pdb_schemaname', self.pdb_schema_name4.text())
        self.settings.setValue('reserve_pdb_schemaname', self.pdb_schema_name5.text())
        self.settings.setValue('credit_dump_path', self.path_schema1.text())
        self.settings.setValue('deposit_dump_path', self.path_schema2.text())
        self.settings.setValue('credit_ar_dump_path', self.path_schema3.text())
        self.settings.setValue('deposit_ar_dump_path', self.path_schema4.text())
        self.settings.setValue('reserve_dump_path', self.path_schema5.text())
        self.settings.endGroup()
        delete_temp_directory()  # удалить каталог temp
        logger.info('Пользовательские настройки сохранены')
        logger.info(f'Файл {__file__} закрыт')

    def initialization_settings(self):
        """
        :return: заполнение полей из настроек
        """
        self.input_main_login.setText(self.settings.value('login'))
        self.line_main_connect.setText(self.settings.value('connectline'))
        self.list_pdb.setCurrentText(self.settings.value('PDB_name'))
        self.input_schema1_name.setText(self.settings.value('SCHEMAS/credit1_schemaname'))
        self.input_schema2_name.setText(self.settings.value('SCHEMAS/deposit1_schemaname'))
        self.input_schema3_name.setText(self.settings.value('SCHEMAS/credit1_ar_schemaname'))
        self.input_schema4_name.setText(self.settings.value('SCHEMAS/deposit1_ar_schemaname'))
        self.input_schema5_name.setText(self.settings.value('SCHEMAS/reserve_schemaname'))
        self.input_schema1_pass.setText(self.settings.value('SCHEMAS/credit1_schemapass'))
        self.input_schema2_pass.setText(self.settings.value('SCHEMAS/deposit1_schemapass'))
        self.input_schema3_pass.setText(self.settings.value('SCHEMAS/credit1_ar_schemapass'))
        self.input_schema4_pass.setText(self.settings.value('SCHEMAS/deposit1_ar_schemapass'))
        self.input_schema5_pass.setText(self.settings.value('SCHEMAS/reserve_schemapass'))
        self.pdb_schema_name1.setText(self.settings.value('SCHEMAS/credit_pdb_schemaname'))
        self.pdb_schema_name2.setText(self.settings.value('SCHEMAS/deposit_pdb_schemaname'))
        self.pdb_schema_name3.setText(self.settings.value('SCHEMAS/credit_ar_pdb_schemaname'))
        self.pdb_schema_name4.setText(self.settings.value('SCHEMAS/deposit_ar_pdb_schemaname'))
        self.pdb_schema_name5.setText(self.settings.value('SCHEMAS/reserve_pdb_schemaname'))
        self.path_schema1.setText(self.settings.value('SCHEMAS/credit_dump_path'))
        self.path_schema2.setText(self.settings.value('SCHEMAS/deposit_dump_path'))
        self.path_schema3.setText(self.settings.value('SCHEMAS/credit_ar_dump_path'))
        self.path_schema4.setText(self.settings.value('SCHEMAS/deposit_ar_dump_path'))
        self.path_schema5.setText(self.settings.value('SCHEMAS/reserve_dump_path'))
        try:
            width = int(self.settings.value('GUI/width'))
            height = int(self.settings.value('GUI/height'))
            x = int(self.settings.value('GUI/x'))
            y = int(self.settings.value('GUI/y'))
            self.setGeometry(x, y, width, height)
            logger.info('Настройки размеров окна загружены.')
        except TypeError:
            pass
            logger.info('Настройки размеров окна НЕ загружены. Установлены размеры по умолчанию')
        if self.settings.value('password') == MD5_HEX:
            self.input_main_password.setText('123devop')
        else:
            self.input_main_password.setText('')
        logger.info('Файл с пользовательскими настройками проинициализирован')

    def header_layout(self):
        """
        :return: добавление виджетов в верхнюю часть интерфейса на главном окне
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
        self.input_newpdb.setToolTip('Используется только как имя новой PDB')
        self.btn_connect = QPushButton('Проверить подключение')
        self.btn_connect.clicked.connect(self.thread_check_connection)
        self.btn_connect.setStyleSheet('width: 300')
        self.btn_clone_pdb = QPushButton('Клонировать PDB')
        self.btn_clone_pdb.setEnabled(False)
        self.btn_clone_pdb.clicked.connect(self.thread_cloning_pdb)
        self.btn_clone_pdb.setStyleSheet('width: 300')
        self.btn_delete_pdb = QPushButton('Удалить PDB')
        self.btn_delete_pdb.clicked.connect(self.thread_deleting_pdb)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write = QPushButton('Сделать PDB доступной для записи')
        self.btn_make_pdb_for_write.clicked.connect(self.thread_make_pdb_writable)
        self.btn_make_pdb_for_write.setEnabled(False)
        self.pdb_progressbar = QProgressBar()
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tab_control.layout.addWidget(self.input_newpdb, 1, 0)
        self.tab_control.layout.addWidget(self.btn_connect, 1, 1)
        self.tab_control.layout.addWidget(self.btn_clone_pdb, 1, 2)
        self.tab_control.layout.addWidget(self.table, 2, 0, 1, 3)
        self.tab_control.layout.addWidget(self.btn_make_pdb_for_write, 3, 0)
        self.tab_control.layout.addWidget(self.pdb_progressbar, 3, 1)
        self.tab_control.layout.addWidget(self.btn_delete_pdb, 3, 2)
        self.tab_control.setLayout(self.tab_control.layout)

    def schemas_tab(self):
        """
        :return: добавление виджетов на вкладку с схемами
        """
        self.tab_schemas.layout = QGridLayout()
        self.tabs.addTab(self.tab_schemas, "Управление схемами")
        self.input_schema1_name = QLineEdit()
        self.input_schema1_name.setPlaceholderText('Имя новой схемы')
        self.input_schema1_pass = QLineEdit()
        self.input_schema1_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema1_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema1 = QCheckBox()
        self.checkbox_schema1.name = 'schema1'
        self.checkbox_schema1.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema_name1 = QLineEdit()
        self.pdb_schema_name1.setPlaceholderText('Имя схемы в дампе')
        self.input_schema2_name = QLineEdit()
        self.input_schema2_name.setPlaceholderText('Имя новой схемы')
        self.input_schema2_pass = QLineEdit()
        self.input_schema2_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema2_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema2 = QCheckBox()
        self.checkbox_schema2.name = 'schema2'
        self.checkbox_schema2.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema_name2 = QLineEdit()
        self.pdb_schema_name2.setPlaceholderText('Имя схемы в дампе')
        self.input_schema3_name = QLineEdit()
        self.input_schema3_name.setPlaceholderText('Имя новой схемы')
        self.input_schema3_pass = QLineEdit()
        self.input_schema3_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema3_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema3 = QCheckBox()
        self.checkbox_schema3.name = 'schema3'
        self.checkbox_schema3.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema_name3 = QLineEdit()
        self.pdb_schema_name3.setPlaceholderText('Имя схемы в дампе')
        self.input_schema4_name = QLineEdit()
        self.input_schema4_name.setPlaceholderText('Имя новой схемы')
        self.input_schema4_pass = QLineEdit()
        self.input_schema4_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema4_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema4 = QCheckBox()
        self.checkbox_schema4.name = 'schema4'
        self.checkbox_schema4.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema_name4 = QLineEdit()
        self.pdb_schema_name4.setPlaceholderText('Имя схемы в дампе')
        self.input_schema5_name = QLineEdit()
        self.input_schema5_name.setPlaceholderText('Имя новой схемы')
        self.input_schema5_pass = QLineEdit()
        self.input_schema5_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema5_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema5 = QCheckBox()
        self.checkbox_schema5.name = 'schema5'
        self.checkbox_schema5.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema_name5 = QLineEdit()
        self.pdb_schema_name5.setPlaceholderText('Имя схемы в дампе')
        self.btn_create_schema = QPushButton('Создать схему')
        self.btn_create_schema.clicked.connect(self.thread_creating_schemas)
        self.btn_delete_schema = QPushButton('Удалить схему')
        self.btn_delete_schema.clicked.connect(self.thread_deleting_schemas)
        self.path_schema1 = QLineEdit()
        self.path_schema1.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema1 = self.path_schema1.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema1.triggered.connect(self.fn_set_path_for_dumps)
        self.path_schema2 = QLineEdit()
        self.path_schema2.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema2 = self.path_schema2.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema2.triggered.connect(self.fn_set_path_for_dumps)
        self.path_schema3 = QLineEdit()
        self.path_schema3.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema3 = self.path_schema3.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema3.triggered.connect(self.fn_set_path_for_dumps)
        self.path_schema4 = QLineEdit()
        self.path_schema4.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema4 = self.path_schema4.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema4.triggered.connect(self.fn_set_path_for_dumps)
        self.path_schema5 = QLineEdit()
        self.path_schema5.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema5 = self.path_schema5.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema5.triggered.connect(self.fn_set_path_for_dumps)
        self.input_schemas_area = QTextEdit()
        self.schemas_progressbar = QProgressBar()
        self.tab_schemas.layout.addWidget(self.checkbox_schema1, 0, 0)
        self.tab_schemas.layout.addWidget(self.input_schema1_name, 0, 1)
        self.tab_schemas.layout.addWidget(self.input_schema1_pass, 0, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema_name1, 0, 3)
        self.tab_schemas.layout.addWidget(self.path_schema1, 0, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema2, 1, 0)
        self.tab_schemas.layout.addWidget(self.input_schema2_name, 1, 1)
        self.tab_schemas.layout.addWidget(self.input_schema2_pass, 1, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema_name2, 1, 3)
        self.tab_schemas.layout.addWidget(self.path_schema2, 1, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema3, 2, 0)
        self.tab_schemas.layout.addWidget(self.input_schema3_name, 2, 1)
        self.tab_schemas.layout.addWidget(self.input_schema3_pass, 2, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema_name3, 2, 3)
        self.tab_schemas.layout.addWidget(self.path_schema3, 2, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema4, 3, 0)
        self.tab_schemas.layout.addWidget(self.input_schema4_name, 3, 1)
        self.tab_schemas.layout.addWidget(self.input_schema4_pass, 3, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema_name4, 3, 3)
        self.tab_schemas.layout.addWidget(self.path_schema4, 3, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema5, 4, 0)
        self.tab_schemas.layout.addWidget(self.input_schema5_name, 4, 1)
        self.tab_schemas.layout.addWidget(self.input_schema5_pass, 4, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema_name5, 4, 3)
        self.tab_schemas.layout.addWidget(self.path_schema5, 4, 4)
        self.tab_schemas.layout.addWidget(self.btn_create_schema, 5, 1)
        self.tab_schemas.layout.addWidget(self.schemas_progressbar, 5, 2, 1, 2)
        self.tab_schemas.layout.addWidget(self.btn_delete_schema, 5, 4)
        self.tab_schemas.layout.addWidget(self.input_schemas_area, 6, 0, 1, 5)


if __name__ == '__main__':
    logger.info(f'Запущен файл {__file__}')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
