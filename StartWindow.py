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
                             QFileDialog,
                             QMessageBox)
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
                       get_string_import_oracle_schema,
                       get_string_delete_oracle_scheme)


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
TITLE = 'ASDCO TOOLS'
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
        else:  # если ошибок не было, то формируем сигнал .result и передаем результат
            self.signals.result.emit(result)  # Вернуть результат обработки
        finally:
            self.signals.finish.emit()  # Готово


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle(TITLE)  # заголовок главного окна
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # минимальный размер окна
        self.btn_icon = QPixmap("others/folder.png")  # иконка для приложения
        self.layout = QWidget()
        self.main_layout = QVBoxLayout()
        self.top_grid_layout = QGridLayout()
        self.tabs = QTabWidget()
        self.tab_control = QWidget()  # вкладка для pdb
        self.tab_schemas = QWidget()  # вкладка для схем
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
        self.btn_clone_pdb.setEnabled(True)
        self.btn_delete_pdb.setEnabled(True)
        self.btn_make_pdb_for_write.setEnabled(True)
        logger.debug(s)

    def thread_print_complete(self):
        """
        :return: слот для сигнала о завершении потока
        """
        logger.debug('Выделенный поток завершен. Прогресс бар установлен на 100%')
        self.pdb_progressbar.setRange(0, 1)

    def msg_window(self):
        """
        :return: вызов диалогового окна
        """
        text = self.message_text
        dlg = QMessageBox()
        dlg.setWindowTitle('ОШИБКА')
        dlg.setText(text)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.exec()

    def thread_check_pdb(self):
        """
        :return: передача функции по проверки pdb в отдельном потоке
        """
        logger.info('Запрошен список существующих PDB')
        worker = Worker(self.fn_check_pdb)  # функция, которая выполняется в потоке
        # worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        worker.signals.error.connect(self.msg_window)  # сообщение, если была вызвана ошибка
        self.threadpool.start(worker)

    def fn_check_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()  # строка подключения из интерфейса
        sysdba_name = self.input_main_login.text()  # имя пользователя из интерфейса
        sysdba_password = self.input_main_password.text()  # пароль
        if connection_string and sysdba_name and sysdba_password:
            self.pdb_progressbar.setRange(0, 0)  # запускается бесконечный прогресс бар
            oracle_string = get_string_show_pdbs(sysdba_name, sysdba_password, connection_string)
            result, list_result = runnings_sqlplus_scripts_with_subprocess(oracle_string, return_split_result=True)
            self.pdb_name_list = formating_sqlplus_results_and_return_pdb_names(list_result)
            self.table.setSortingEnabled(False)  # отключаем возможность сортировки по столбцам
            self.table.setRowCount(len(self.pdb_name_list))  # количество строк по длине списка
            self.table.setColumnCount(4)  # количество столбцов
            self.table.setHorizontalHeaderLabels(['Имя', 'Дата создания', 'Статус', 'Размер'])  # названия столбцов
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
            self.table.setSortingEnabled(True)
            self.table.sortItems(0)
            return f'Функция {traceback.extract_stack()[-1][2]} завершена'
        else:
            logger.warning('Не заполнены все обязательные поля. Список PDB не получен')
            self.message_text = ('Не заполнены все обязательные поля:\n\t- пользователь/пароль SYSDBA пользователя\n'
                                 '\t- строка подключения к CDB')
            raise Exception('Не заполнены все обязательные поля. Список PDB не получен')

    def thread_check_connection(self):
        """
        :return: передача функции по проверке подключения к cdb в отдельном потоке
        """
        logger.info('Проверка подключения к PDB')
        self.btn_clone_pdb.setEnabled(False)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write.setEnabled(False)
        worker = Worker(self.fn_check_connect)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        worker.signals.error.connect(self.msg_window)  # сообщение, если была вызвана ошибка
        self.threadpool.start(worker)

    def fn_check_connect(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        pdb_name = self.list_pdb.currentText().upper()
        connection_string = self.line_main_connect.text()[:self.line_main_connect.text().rfind('/')+1] + pdb_name
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        if pdb_name and connection_string and sysdba_name and sysdba_password:
            self.pdb_progressbar.setRange(0, 0)
            oracle_string = get_string_check_oracle_connection(connection_string, sysdba_name, sysdba_password)
            result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
            ora_not_error = re.search(r'CONNECTION SUCCESS', result)
            if ora_not_error.group(0):
                logger.info(result.strip())
                return f'Функция {traceback.extract_stack()[-1][2]} завершена'
            else:
                logger.warning(result.strip(), exc_info=True)
                return f'Не удалось подключиться к PDB. Возможны ошибки на сервере'
        else:
            logger.warning('Не заполнены все обязательные поля. Проверка подключения прервана')
            self.message_text = ('Не заполнены все обязательные поля:\n\t- пользователь/пароль SYSDBA пользователя\n'
                                 '\t- строка подключения к CDB\n\t- имя PDB')
            raise Exception('Не заполнены все обязательные поля. Проверка подключения прервана')

    def thread_cloning_pdb(self):
        """
        :return: передача функции клонирования pdb в отдельном потоке
        """
        logger.info('Клонирование PDB')
        self.btn_clone_pdb.setEnabled(False)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write.setEnabled(False)
        worker = Worker(self.fn_cloning_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        worker.signals.error.connect(self.msg_window)  # сообщение, если была вызвана ошибка
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
        if connection_string and schema_name and schema_password and pdb_name and pdb_name_clone:
            self.pdb_progressbar.setRange(0, 0)
            if pdb_name_clone == 'ASDCOEMPTY_ETALON' or pdb_name_clone == 'PDB$SEED':
                logger.error('Заблокирована попытка клонирования на базу ASDCOEMPTY_ETALON или PDB$SEED')
                self.message_text = 'Клонирование на БД ASDCOEMPTY_ETALON или PDB$SEED запрещено'
                raise Exception('Клонирование на БД ASDCOEMPTY_ETALON или PDB$SEED запрещено')
            elif pdb_name_clone == pdb_name:
                logger.error('Имя новой PDB и имеющейся PDB не должны совпадать')
                self.message_text = 'Имя новой PDB и имеющейся PDB не должны совпадать'
                raise Exception('Имя новой PDB и имеющейся PDB не должны совпадать')
            else:
                oracle_string = get_string_clone_pdb(connection_string, schema_name, schema_password, pdb_name, pdb_name_clone)
                result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
                logger.info(f'Проверьте в списке созданную PDB [{pdb_name_clone}]')
                logger.info(result.strip())
                logger.info('Перезаполнение списка PDB и таблицы')
                self.thread_check_pdb()
                return f'Функция {traceback.extract_stack()[-1][2]} завершена. Имя новой PDB {pdb_name_clone}'
        else:
            logger.warning('Не заполнены все обязательные поля. Клонирование PDB прервано')
            self.message_text = ('Не заполнены все обязательные поля:\n\t- пользователь/пароль SYSDBA пользователя\n'
                                 '\t- строка подключения к CDB\n\t- имя PDB\n\t- новое имя PDB')
            raise Exception('Не заполнены все обязательные поля. Клонирование PDB прервано')

    def thread_deleting_pdb(self):
        """
        :return: передача функции удаления pdb в отдельном потоке
        """
        self.btn_clone_pdb.setEnabled(False)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write.setEnabled(False)
        logger.info('Удаление PDB')
        worker = Worker(self.fn_deleting_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        worker.signals.error.connect(self.msg_window)  # сообщение, если была вызвана ошибка
        self.threadpool.start(worker)

    def fn_deleting_pdb(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        schema_name = self.input_main_login.text()
        schema_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        if connection_string and schema_name and schema_password and pdb_name:
            self.pdb_progressbar.setRange(0, 0)
            if pdb_name == 'ASDCOEMPTY_ETALON' or pdb_name == 'PDB$SEED':
                logger.error('Заблокирована попытка удаления на базу ASDCOEMPTY_ETALON или PDB$SEED')
                self.message_text = 'Обнаружена попытка удаления ASDCOEMPTY_ETALON или PDB$SEED'
                raise Exception('Удаление ASDCOEMPTY_ETALON или PDB$SEED запрещено')
            else:
                oracle_string = get_string_delete_pdb(connection_string,
                                                      schema_name,
                                                      schema_password,
                                                      pdb_name)
                result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
                logger.info(f'PDB {pdb_name} удалена')
                logger.info(result.strip())
                logger.info('Перезаполнение списка PDB и таблицы')
                self.thread_check_pdb()
                self.list_pdb.setCurrentIndex(0)
                return f'Функция {traceback.extract_stack()[-1][2]} завершена. {pdb_name} удалена'
        else:
            logger.warning('Не заполнены все обязательные поля. Удаление PDB прервано')
            self.message_text = ('Не заполнены все обязательные поля:\n\t- пользователь/пароль SYSDBA пользователя\n'
                                 '\t- строка подключения к CDB\n\t- имя PDB')
            raise Exception('Не заполнены все обязательные поля. Удаление PDB прервано')

    def thread_make_pdb_writable(self):
        """
        :return: передача функции по переводу pdb из режима только для чтения в отдельном потоке
        """
        self.btn_clone_pdb.setEnabled(False)
        self.btn_delete_pdb.setEnabled(False)
        self.btn_make_pdb_for_write.setEnabled(False)
        logger.info('Перевести PDB в режим writable')
        worker = Worker(self.fn_writable_pdb)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        worker.signals.error.connect(self.msg_window)  # сообщение, если была вызвана ошибка
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
        if connection_string and schema_name and schema_password and pdb_name:
            self.pdb_progressbar.setRange(0, 0)
            oracle_string = get_string_make_pdb_writable(connection_string,
                                                         schema_name,
                                                         schema_password,
                                                         pdb_name)
            result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
            logger.info('PDB переведена в режим доступной для записи')
            logger.info(result.strip())
            return f'Функция {traceback.extract_stack()[-1][2]} завершена. ' \
                   f'PDB {pdb_name} переведена в режим доступной для записи'
        else:
            logger.warning('Не заполнены все обязательные поля. Перевод PDB в режим записи прерван')
            self.message_text = ('Не заполнены все обязательные поля:\n\t- пользователь/пароль SYSDBA пользователя\n'
                                 '\t- строка подключения к CDB\n\t- имя PDB')
            raise Exception('Не заполнены все обязательные поля. Перевод PDB в режим записи прерван')

    def thread_schemas_complete(self):
        """
        :return: слот для сигнала о завершении потока
        """
        logger.info('Выделенный поток завершен. Прогресс бар установлен на 100%')
        self.schemas_progressbar.setRange(0, 1)

    def thread_showing_schemas(self):
        """
        :return: передача функции по созданию схем в отдельном потоке
        """
        logger.info(f'Запрошен список существующих схем в PDB {self.list_pdb.currentText()}')
        worker = Worker(self.fn_show_shemas)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_schemas_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_show_shemas(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        bd_name = self.list_pdb.currentText().upper()
        if connection_string and sysdba_name and sysdba_password and bd_name:
            self.schemas_progressbar.setRange(0, 0)
            oracle_string = get_string_show_oracle_users(sysdba_name, sysdba_password, connection_string, bd_name)
            result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
            logger.info(result.strip())
            self.input_schemas_area.append(result.strip())
            return f'Функция {traceback.extract_stack()[-1][2]} завершена'
        else:
            logger.warning('Не заполнены все обязательные поля. Невозможно отобразить существующие схемы')
            self.msg_window('Не заполнены все обязательные поля:\n'
                            '\t- пользователь/пароль SYSDBA пользователя\n'
                            '\t- строка подключения к CDB\n'
                            '\t- имя PDB')

    def thread_creating_schemas(self):
        """
        :return: передача функции по созданию схем в отдельном потоке
        """
        logger.info('Начато создание схем')
        worker = Worker(self.fn_creating_schemas)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_schemas_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_creating_schemas(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        bd_name = self.list_pdb.currentText().upper()
        checked_schemas = [key for key in self.schemas.keys() if self.schemas[key] == 1]
        if connection_string and sysdba_name and sysdba_password and bd_name:
            self.schemas_progressbar.setRange(0, 0)
            for schema_name in checked_schemas:
                name = eval('self.input_' + schema_name + '_name.text()')
                identified = eval('self.input_' + schema_name + '_pass.text()')
                result_creating_schemas = self.creating_schemas(connection_string, sysdba_name, sysdba_password,
                                                                name, identified, bd_name)
                self.input_schemas_area.append(result_creating_schemas.strip())
                logger.info(f'Схема {name} создана')
                result_for_privileges = self.grant_privilege_schemas(connection_string, sysdba_name, sysdba_password,
                                                                     name, bd_name)
                self.input_schemas_area.append(result_for_privileges.strip())
                logger.info(f'Схеме {name} выданы привилегии')
                return f'Функция {traceback.extract_stack()[-1][2]} завершена'
        else:
            logger.warning('Не заполнены все обязательные поля. Невозможно cоздать новые схемы')
            self.msg_window('Не заполнены все обязательные поля:\n'
                            '\t- пользователь/пароль SYSDBA пользователя\n'
                            '\t- строка подключения к CDB\n'
                            '\t- имя PDB')

    def creating_schemas(self, connection_string, sysdba_name, sysdba_password, name, identified, bd_name):
        """
        :param connection_string: строка подключения к pdb
        :param sysdba_name: логин пользователя SYSDBA
        :param sysdba_password: пароль пользователя SYSDBA
        :param name: имя новой схемы
        :param identified: пароль от схемы
        :param bd_name: имя pdb, в которой будет создана схема
        :return: созданные схемы
        """
        oracle_string = get_string_create_oracle_schema(connection_string, sysdba_name, sysdba_password, name,
                                                        identified, bd_name)
        return runnings_sqlplus_scripts_with_subprocess(oracle_string)

    def grant_privilege_schemas(self, connection_string, sysdba_name, sysdba_password, schema_name, bd_name):
        """
        :param connection_string: строка подключения к pdb
        :param sysdba_name: логин пользователя SYSDBA
        :param sysdba_password: пароль пользователя SYSDBA
        :param schema_name: имя новой схемы
        :param bd_name: имя pdb, в которой будет создана схема
        :return: выданы привилегии для схем
        """
        oracle_string = get_string_grant_oracle_privilege(connection_string,
                                                          sysdba_name,
                                                          sysdba_password,
                                                          schema_name,
                                                          bd_name)
        return runnings_sqlplus_scripts_with_subprocess(oracle_string)

    def thread_import_from_dumps(self):
        """
        :return: передача функции по созданию схем в отдельном потоке
        """
        logger.info('Начат импорт из дампа')
        worker = Worker(self.fn_import_schemas)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_schemas_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_import_schemas(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        bd_name = self.list_pdb.currentText().upper()
        checked_schemas = [key for key in self.schemas.keys() if self.schemas[key] == 1]
        if connection_string and sysdba_name and sysdba_password and bd_name:
            self.schemas_progressbar.setRange(0, 0)
            if len(checked_schemas) == 7:
                name = eval('self.input_' + checked_schemas[0] + '_name.text()')
                identified = eval('self.input_' + checked_schemas[0] + '_pass.text()')
                dump_for_schema_path = eval('self.path_' + checked_schemas[0] + '.text()')
                dump_name = eval('self.pdb_' + checked_schemas[0] + '_name.text()')
                connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                oracle_string = get_string_import_oracle_schema(connection_string_without_orcl, bd_name, name,
                                                                identified, dump_name, dump_for_schema_path)
                result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
                self.input_schemas_area.append(result.strip())
            elif len(checked_schemas) > 7:
                for schema_name in checked_schemas:
                    name = eval('self.input_' + schema_name + '_name.text()')
                    identified = eval('self.input_' + schema_name + '_pass.text()')
                    dump_for_schema_path = eval('self.path_' + schema_name + '.text()')
                    dump_name = eval('self.pdb_' + schema_name + '_name.text()')
                    self.input_schemas_area.append(f'Начато выполнение импорта из дампа для схемы {name}')
                    logger.info(f'Начато выполнение импорта из дампа для схемы {name}')
                    connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                    oracle_string = get_string_import_oracle_schema(connection_string_without_orcl, bd_name, name,
                                                                    identified, dump_name, dump_for_schema_path)
                    result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
                    self.input_schemas_area.append(f'Импорт из дампа для схемы {name} завершен. Результаты выполнения:\n')
                    self.input_schemas_area.append(result.strip())
                    logger.info(f'Импорт из дампа для схемы {name} завершен')
                    logger.info(f'Включение опций и перекомпиляция view и функций для схемы {name}')
                    self.enabled_schemes_options(connection_string, bd_name, name, identified)
                    logger.info(f'Выполнение перекомпиляции view и функций для схемы {name} зевершено')
                    return f'Функция {traceback.extract_stack()[-1][2]} завершена'
            else:
                logger.warning('Не найдены отмеченные чекбоксами схемы')
                self.msg_window('Проверьте отмечены ли схемы')
        else:
            logger.warning('Не заполнены все обязательные поля. Невозможно импортировать из дампа')
            self.msg_window('Не заполнены все обязательные поля:\n'
                            '\t- пользователь/пароль SYSDBA пользователя\n'
                            '\t- строка подключения к CDB\n'
                            '\t- имя PDB')

    def enabled_schemes_options(self, connection_string, pdb_name, schema_name, schema_password):
        connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
        oracle_string = get_string_enabled_oracle_asdco_options(connection_string_without_orcl, pdb_name,
                                                                schema_name, schema_password)
        return runnings_sqlplus_scripts_with_subprocess(oracle_string)

    def thread_deleting_schemas(self):
        """
        :return: передача функции по созданию схем в отдельном потоке
        """
        logger.info('Начато удаление схем')
        worker = Worker(self.fn_deleting_schemas)  # функция, которая выполняется в потоке
        worker.signals.result.connect(self.thread_print_output)  # сообщение после завершения выполнения задачи
        worker.signals.finish.connect(self.thread_schemas_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def fn_deleting_schemas(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: удаление выделенных схем
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        bd_name = self.list_pdb.currentText().upper()
        checked_schemas = ', '.join([key for key in self.schemas.keys() if self.schemas[key] == 1])
        self.input_schemas_area.append(f'Удаление схем: {checked_schemas}')
        logger.info(f'Начато удаление схем {checked_schemas}')
        if connection_string and sysdba_name and sysdba_password:
            self.schemas_progressbar.setRange(0, 0)
            if len(checked_schemas) == 7:
                connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                oracle_string = get_string_delete_oracle_scheme(connection_string_without_orcl, sysdba_name,
                                                                sysdba_password, bd_name, checked_schemas)
                result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
                self.input_schemas_area.append(result.strip())
            elif len(checked_schemas) > 7:
                for schema_name in checked_schemas:
                    connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                    oracle_string = get_string_delete_oracle_scheme(connection_string_without_orcl, sysdba_name,
                                                                    sysdba_password, bd_name, schema_name)
                    result = runnings_sqlplus_scripts_with_subprocess(oracle_string)
                    self.input_schemas_area.append(result.strip())
            else:
                logger.warning('Не найдены отмеченные чекбоксами схемы')
                self.msg_window('Проверьте отмечены ли схемы')
        else:
            logger.warning('Не заполнены все обязательные поля. Невозможно удалить схемы')
            self.msg_window('Не заполнены все обязательные поля:\n'
                            '\t- пользователь/пароль SYSDBA пользователя\n'
                            '\t- строка подключения к CDB\n'
                            '\t- имя PDB')

    def fn_checkbox_clicked_for_schemas(self, checked):
        """
        :param checked: принимаем статус чекбокса
        :return: устанавливаем для словаря 1/0
        """
        checkbox = self.sender()
        if checked:
            self.schemas[checkbox.name] = 1
        else:
            self.schemas[checkbox.name] = 0

    def fn_set_path_for_dumps(self):
        """
        :return: устанавливаем путь для каждого дампа схемы
        """
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
        self.settings.setValue('credit_pdb_schemaname', self.pdb_schema1_name.text())
        self.settings.setValue('deposit_pdb_schemaname', self.pdb_schema2_name.text())
        self.settings.setValue('credit_ar_pdb_schemaname', self.pdb_schema3_name.text())
        self.settings.setValue('deposit_ar_pdb_schemaname', self.pdb_schema4_name.text())
        self.settings.setValue('reserve_pdb_schemaname', self.pdb_schema5_name.text())
        self.settings.setValue('credit_dump_path', self.path_schema1.text())
        self.settings.setValue('deposit_dump_path', self.path_schema2.text())
        self.settings.setValue('credit_ar_dump_path', self.path_schema3.text())
        self.settings.setValue('deposit_ar_dump_path', self.path_schema4.text())
        self.settings.setValue('reserve_dump_path', self.path_schema5.text())
        self.settings.endGroup()
        delete_temp_directory()
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
        self.pdb_schema1_name.setText(self.settings.value('SCHEMAS/credit_pdb_schemaname'))
        self.pdb_schema2_name.setText(self.settings.value('SCHEMAS/deposit_pdb_schemaname'))
        self.pdb_schema3_name.setText(self.settings.value('SCHEMAS/credit_ar_pdb_schemaname'))
        self.pdb_schema4_name.setText(self.settings.value('SCHEMAS/deposit_ar_pdb_schemaname'))
        self.pdb_schema5_name.setText(self.settings.value('SCHEMAS/reserve_pdb_schemaname'))
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
            logger.info('Установлены размеры окна по умолчанию')
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
        self.line_main_connect.setToolTip('Указывается ip:порт/SID(service name)')
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
        self.input_newpdb.setPlaceholderText('Новое имя PDB')
        self.input_newpdb.setToolTip('Введите в данное поле новое имя PDB')
        self.btn_connect = QPushButton('Проверить подключение к PDB')
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
        self.pdb_progressbar.setStyleSheet('text-align: center; min-height: 20px; max-height: 20px;')
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tab_control.layout.addWidget(self.input_newpdb, 0, 1)
        self.tab_control.layout.addWidget(self.btn_connect, 0, 0)
        self.tab_control.layout.addWidget(self.btn_clone_pdb, 0, 2)
        self.tab_control.layout.addWidget(self.table, 2, 0, 1, 3)
        self.tab_control.layout.addWidget(self.btn_make_pdb_for_write, 1, 0)
        self.tab_control.layout.addWidget(self.pdb_progressbar, 1, 1)
        self.tab_control.layout.addWidget(self.btn_delete_pdb, 1, 2)
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
        self.pdb_schema1_name = QLineEdit()
        self.pdb_schema1_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema2_name = QLineEdit()
        self.input_schema2_name.setPlaceholderText('Имя новой схемы')
        self.input_schema2_pass = QLineEdit()
        self.input_schema2_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema2_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema2 = QCheckBox()
        self.checkbox_schema2.name = 'schema2'
        self.checkbox_schema2.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema2_name = QLineEdit()
        self.pdb_schema2_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema3_name = QLineEdit()
        self.input_schema3_name.setPlaceholderText('Имя новой схемы')
        self.input_schema3_pass = QLineEdit()
        self.input_schema3_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema3_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema3 = QCheckBox()
        self.checkbox_schema3.name = 'schema3'
        self.checkbox_schema3.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema3_name = QLineEdit()
        self.pdb_schema3_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema4_name = QLineEdit()
        self.input_schema4_name.setPlaceholderText('Имя новой схемы')
        self.input_schema4_pass = QLineEdit()
        self.input_schema4_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema4_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema4 = QCheckBox()
        self.checkbox_schema4.name = 'schema4'
        self.checkbox_schema4.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema4_name = QLineEdit()
        self.pdb_schema4_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema5_name = QLineEdit()
        self.input_schema5_name.setPlaceholderText('Имя новой схемы')
        self.input_schema5_pass = QLineEdit()
        self.input_schema5_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema5_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema5 = QCheckBox()
        self.checkbox_schema5.name = 'schema5'
        self.checkbox_schema5.stateChanged.connect(self.fn_checkbox_clicked_for_schemas)
        self.pdb_schema5_name = QLineEdit()
        self.pdb_schema5_name.setPlaceholderText('Имя схемы в дампе')
        self.btn_create_schema = QPushButton('Создать схему')
        self.btn_create_schema.clicked.connect(self.thread_creating_schemas)
        self.btn_delete_schema = QPushButton('Удалить схему')
        self.btn_delete_schema.clicked.connect(self.thread_deleting_schemas)
        self.btn_show_schemas = QPushButton('Показать существующие схемы')
        self.btn_show_schemas.clicked.connect(self.thread_showing_schemas)
        self.btn_import_from_dumps = QPushButton('Импорт из дампа')
        self.btn_import_from_dumps.clicked.connect(self.thread_import_from_dumps)
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
        self.schemas_progressbar.setStyleSheet('text-align: center; min-height: 20px; max-height: 20px;')
        self.tab_schemas.layout.addWidget(self.checkbox_schema1, 0, 0)
        self.tab_schemas.layout.addWidget(self.input_schema1_name, 0, 1)
        self.tab_schemas.layout.addWidget(self.input_schema1_pass, 0, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema1_name, 0, 3)
        self.tab_schemas.layout.addWidget(self.path_schema1, 0, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema2, 1, 0)
        self.tab_schemas.layout.addWidget(self.input_schema2_name, 1, 1)
        self.tab_schemas.layout.addWidget(self.input_schema2_pass, 1, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema2_name, 1, 3)
        self.tab_schemas.layout.addWidget(self.path_schema2, 1, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema3, 2, 0)
        self.tab_schemas.layout.addWidget(self.input_schema3_name, 2, 1)
        self.tab_schemas.layout.addWidget(self.input_schema3_pass, 2, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema3_name, 2, 3)
        self.tab_schemas.layout.addWidget(self.path_schema3, 2, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema4, 3, 0)
        self.tab_schemas.layout.addWidget(self.input_schema4_name, 3, 1)
        self.tab_schemas.layout.addWidget(self.input_schema4_pass, 3, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema4_name, 3, 3)
        self.tab_schemas.layout.addWidget(self.path_schema4, 3, 4)
        self.tab_schemas.layout.addWidget(self.checkbox_schema5, 4, 0)
        self.tab_schemas.layout.addWidget(self.input_schema5_name, 4, 1)
        self.tab_schemas.layout.addWidget(self.input_schema5_pass, 4, 2)
        self.tab_schemas.layout.addWidget(self.pdb_schema5_name, 4, 3)
        self.tab_schemas.layout.addWidget(self.path_schema5, 4, 4)
        self.tab_schemas.layout.addWidget(self.btn_show_schemas, 5, 1)
        self.tab_schemas.layout.addWidget(self.btn_create_schema, 5, 2)
        self.tab_schemas.layout.addWidget(self.btn_import_from_dumps, 5, 3)
        self.tab_schemas.layout.addWidget(self.btn_delete_schema, 5, 4)
        self.tab_schemas.layout.addWidget(self.schemas_progressbar, 6, 2, 1, 2)
        self.tab_schemas.layout.addWidget(self.input_schemas_area, 7, 0, 1, 5)


if __name__ == '__main__':
    logger.info(f'Запущен файл {__file__}')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
