import os
import pathlib
import sys
import re
import getpass
from datetime import datetime, date
from myLogging import logger
from PyQt6.QtGui import QPixmap, QIcon, QAction, QShortcut, QKeySequence
from PyQt6.QtCore import QSettings, QProcess, QThreadPool, Qt, QDate, QProcessEnvironment
from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel, QGridLayout, QApplication, QPushButton, QLineEdit, QTextEdit,
                             QCheckBox, QComboBox, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QProgressBar, QFileDialog, QStatusBar, QMenu)
from functions import (get_string_show_pdbs, delete_temp_directory, formating_sqlplus_results_and_return_pdb_names,
                       get_string_clone_pdb, get_string_make_pdb_writable, get_string_delete_pdb, format_list_result,
                       get_string_create_oracle_schema, get_string_show_oracle_users,
                       get_string_enabled_oracle_asdco_options, get_string_import_oracle_schema,
                       get_string_delete_oracle_scheme, create_file_for_pdb, get_last_login_to_common_schemas,
                       get_total_space_and_used_space_from_zabbix, get_string_export_oracle_scheme, make_shortname,
                       get_date_exe_file, check_empty_fields, get_string_snapshot_clone_pdb, get_string_for_sql_scripts,
                       get_string_oracle_users_name, get_string_for_cyrillic_sql_scripts)
from classes import JobManager, Worker, InitialDelegate, MessageWindows, SecondWindow
from sql_scripts import get_sql_dict

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
TITLE = 'ASDCO TOOLS'


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle(TITLE)  # заголовок главного окна
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # минимальный размер окна
        self.btn_icon = QPixmap("others/folder.png")  # иконка для приложения
        self.layout = QWidget()  # наследуемся для макета
        self.threadpool = QThreadPool()
        self.main_layout = QVBoxLayout()  # вертикальный макет
        self.top_grid_layout = QGridLayout()  # макет с сеткой
        self.tabs = QTabWidget()  # наследуемся для вкладок
        self.tab_control = QWidget()  # вкладка для pdb
        self.tab_schemas = QWidget()  # вкладка для схем
        self.tab_scripts = QWidget()  # вкладка для скриптов
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)  # наследуемся для сохранения настроек
        self.schemas = {'schema1': 0, 'schema2': 0, 'schema3': 0, 'schema4': 0,
                        'schema5': 0}  # это словарь для чекбоксов
        self.header_layout()  # функция с добавленными элементами интерфейса для верхней части
        self.pdb_tab()  # функция с добавленными элементами вкладки pdb
        self.schemas_tab()  # функция с добавленными элементами вкладки со схемами
        self.scripts_tab()  # функция с добавленными элементами вкладки со скриптами
        self.footer_status_bar()
        self.tab_schemas.setLayout(self.tab_schemas.layout)
        self.tab_scripts.setLayout(self.tab_scripts.layout)
        self.main_layout.addLayout(self.top_grid_layout)
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.stbar)
        self.layout.setLayout(self.main_layout)
        self.setCentralWidget(self.layout)
        self.initialization_settings()  # вызов функции с инициализацией сохраненных значений
        # self.thread_get_info_from_server()  # запустить получение инфы о размере по api
        self.process = None  # это для QProcess
        self.finish_message = ''  # передается сообщение в лог после клонирования, удаления и функции writeble
        self.job = JobManager()  # наследуемся от нашего класса JobManager
        self.space_warning = ''  # заполняется, если на сервере будет меньше 50 гб свободного места
        self.current_user = getpass.getuser().upper()  # получение имени текущего пользователя
        self.short_name = make_shortname(self.current_user)  # сократить имя пользователя для клонирования и удаления
        self.thread_check_update()  # запуск проверки обновления
        self.message_windows = MessageWindows()  # наследуемся от собственного класса QMessageBox
        self.set_style_for_fields()  # функция с установкой стилей для разных полей при включенном параметре
        self.new_window = SecondWindow()

    def set_style_for_fields(self):
        """
        :return: если параметр show_msg_window установлен на 0, то устанавливаем другой стиль для полей
        """
        if self.show_msg_window == '0':
            self.btn_current_pdb.setStyleSheet('background-color: #00bb00; color: #fff; border: 3px solid #00bb00;')

    def thread_print_complete(self):
        """
        :return: слот для сигнала о завершении потока
        """
        logger.info('Информация о пространстве на сервере oracle получена и записана в статусную строку')
        self.footer_label.setText(self.status_string)
        if self.space_warning != '':
            self.message_windows.msg_window(self.space_warning)

    def thread_get_info_from_server(self):
        """
        :return: передача функции по проверки pdb в отдельном потоке
        """
        logger.info('Запрошена информация по api о состоянии сервера oracle')
        self.footer_label.setText('Идет получение данных с сервера...')
        worker = Worker(self.get_space)  # функция, которая выполняется в потоке
        worker.signals.finish.connect(self.thread_print_complete)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def get_space(self, progress_callback):
        """
        :param progress_callback: передача результатов из класса потока
        :return: передает сообщение в функцию thread_print_output
        """
        data = get_total_space_and_used_space_from_zabbix()
        total_space = round(data["total_space"] / 1024 / 1024 / 1024)
        empty_space = round((data["total_space"] - data["used_space"]) / 1024 / 1024 / 1024)
        if empty_space < 50:
            self.space_warning = 'На сервере осталось свободного места меньше 50 Гб. ' \
                                 'Проверьте свои базы и удалите не актуальные'
        self.status_string = f"""На 136 сервере свободно {empty_space} Гб. Всего выделено {total_space} Гб"""

    def thread_print_update(self):
        """
        :re
        turn: слот для сигнала о завершении потока
        """
        logger.info('Получена информация об обновлении')
        if self.repository_file_date is not None or self.file_date is not None:
            if self.repository_file_date > self.file_date:
                self.stbar.showMessage('в каталоге "10.1.18.19\\Share\\Novozhilov\\asdco_tools" найдена новая версия')

    def thread_check_update(self):
        """
        :return: передача функции по проверки pdb в отдельном потоке
        """
        logger.info('Проверка обновления')
        worker = Worker(self.get_update)  # функция, которая выполняется в потоке
        worker.signals.finish.connect(self.thread_print_update)  # сообщение после завершения потока
        self.threadpool.start(worker)

    def get_update(self, progress_callback):
        """
        :return: запись в статусную строку при наличии обновления
        """
        try:
            if pathlib.Path.cwd().joinpath('asdcotools.exe'):
                file_date = datetime.fromtimestamp(os.path.getmtime(pathlib.Path.cwd().joinpath('asdcotools.exe')))
            elif pathlib.Path.cwd().joinpath('asdco_tools.exe'):
                file_date = datetime.fromtimestamp(os.path.getmtime(pathlib.Path.cwd().joinpath('asdco_tools.exe')))
            elif pathlib.Path.cwd().joinpath('asdco-tools.exe'):
                file_date = datetime.fromtimestamp(os.path.getmtime(pathlib.Path.cwd().joinpath('asdco-tools.exe')))
            self.file_date = file_date
            self.repository_file_date = get_date_exe_file('\\\\10.1.18.19\\Share\\Novozhilov\\asdco_tools')
        except:
            self.file_date = None
            self.repository_file_date = None

    def handle_stdout_pdb_list(self):
        """
        :return: отлавливаем поток данных из запущенной через QProcess программы
        """
        try:
            stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
            stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        except:
            stdout = bytes(self.process.readAllStandardOutput()).decode("cp1251")
            stderr = bytes(self.process.readAllStandardError()).decode("cp1251")
        output = (stdout + stderr).strip()
        find_ora_error = re.compile("ORA-\d{1,5}:")
        searching_in_stdout = find_ora_error.search(output)
        try:
            start = output.find(searching_in_stdout.group(0))
            self.error_message = output[start:]
            self.process.kill()
        except:
            with open(self.full_path_to_file, 'a') as file:
                file.write(output + '\n')
            return self.process.exitCode()

    def process_pdb_list_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса и выводим список баз данных
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.pdb_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            current_pdb = self.list_pdb.currentText()
            with open(self.full_path_to_file, 'r') as file:
                data = file.read()
            result_list = data.split('\n')
            self.pdb_name_list = formating_sqlplus_results_and_return_pdb_names(result_list)
            new_list = format_list_result(result_list)
            self.table.setSortingEnabled(False)  # отключаем возможность сортировки по столбцам
            self.table.setRowCount(len(new_list))  # количество строк по длине списка
            self.table.setColumnCount(4)  # количество столбцов
            self.table.setHorizontalHeaderLabels(['Имя', 'Дата создания', 'Статус', 'Размер'])  # названия столбцов
            row = 0
            for i in new_list:
                item_string_c1 = QTableWidgetItem()
                item_date = QTableWidgetItem()
                item_string_c2 = QTableWidgetItem()
                item_number = QTableWidgetItem()
                item_string_c1.setData(Qt.ItemDataRole.DisplayRole, i[0])
                try:
                    item_date.setData(Qt.ItemDataRole.DisplayRole, QDate.fromString(i[1], 'dd.MM.yyyy'))
                except ValueError:
                    logger.error(f'Ошибка преобразования формата из строки в дату для значения "{i}"')
                    item_date.setData(Qt.ItemDataRole.DisplayRole, i[1])
                item_string_c2.setData(Qt.ItemDataRole.DisplayRole, i[2])
                try:
                    item_number.setData(Qt.ItemDataRole.DisplayRole, int(i[3]))
                except ValueError:
                    logger.error(f'Ошибка преобразования формата из строки в число для значения "{i}"')
                    item_number.setData(Qt.ItemDataRole.DisplayRole, i[3])
                self.table.setItem(row, 0, item_string_c1)
                self.table.setItem(row, 1, item_date)
                self.table.setItem(row, 2, item_string_c2)
                self.table.setItem(row, 3, item_number)
                row += 1
            self.list_pdb.clear()
            for i in self.pdb_name_list:
                self.list_pdb.addItem(i)
            current_index = self.list_pdb.findText(current_pdb)
            self.list_pdb.setCurrentIndex(current_index)
            self.table.setSortingEnabled(True)
            self.table.sortItems(0)
            self.process = None
            self.pdb_progressbar.setRange(0, 1)
            logger.info('Успешное завершение получения списка PDB')

    def get_pdb_name_from_bd(self):
        """
        :return: создаем строку подключения для запуска и отправляем на выполнение в QProcess
        """
        connection_string = self.line_main_connect.text()  # строка подключения из интерфейса
        sysdba_name = self.input_main_login.text()  # имя пользователя из интерфейса
        sysdba_password = self.input_main_password.text()  # пароль
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password:
                self.pdb_progressbar.setRange(0, 0)  # запускается бесконечный прогресс бар
                oracle_string = get_string_show_pdbs(connection_string, sysdba_name, sysdba_password)
                self.full_path_to_file = create_file_for_pdb('pdb_name.txt')
                self.process = QProcess()
                self.process.readyReadStandardError.connect(self.handle_stdout_pdb_list)  # сигнал об ошибках
                self.process.readyReadStandardOutput.connect(self.handle_stdout_pdb_list)  # сигнал во время работы
                self.process.finished.connect(self.process_pdb_list_finished)  # сигнал после завершения всех задач
                self.process.startCommand(oracle_string)
                logger.info('Запущена процедура получения списка PDB')
            else:
                logger.warning('Не заполнены все обязательные поля. Проверка подключения прервана')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password})
                self.message_windows.msg_window(message_text)

        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def handle_stdout_connect(self):
        """
        :return: отлавливаем поток данных из запущенной через QProcess программы
        """
        try:
            stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
            stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        except:
            stdout = bytes(self.process.readAllStandardOutput()).decode("cp1251")
            stderr = bytes(self.process.readAllStandardError()).decode("cp1251")
        output = (stdout + stderr).strip()
        find_ora_error = re.compile("ORA-\d{1,5}:")
        searching_in_stdout = find_ora_error.search(output)
        try:
            start = output.find(searching_in_stdout.group(0))
            self.error_message = output[start:]
            self.process.kill()
        except:
            ora_not_error = re.search(r'CONNECTION SUCCESS', output)
            if ora_not_error.group(0):
                logger.info('Успешное подключение к PDB')
                self.stdout_data = output
            else:
                logger.warning(output)
                self.error_message = output
            return self.process.exitCode()

    def handle_stdout(self):
        """
        :return: отлавливаем поток данных из запущенной через QProcess программы
        """
        try:
            stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
            stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        except:
            stdout = bytes(self.process.readAllStandardOutput()).decode("cp1251")
            stderr = bytes(self.process.readAllStandardError()).decode("cp1251")
        output = (stdout + stderr).strip()
        find_ora_error = re.compile("ORA-\d{1,5}:")
        searching_in_stdout = find_ora_error.search(output)
        try:
            start = output.find(searching_in_stdout.group(0))
            self.error_message = output[start:]
            self.process.kill()
        except:
            return self.process.exitCode()

    def process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.pdb_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.pdb_progressbar.setRange(0, 1)
            logger.info('Перезаполнение списка PDB и таблицы')
            self.get_pdb_name_from_bd()
            self.stbar.showMessage(f'Функция "{self.finish_message}" выполнена')
            logger.info(f'Функция "{self.finish_message}" выполнена')

    def execute_command(self, cmd):
        """
        :param cmd: строка для запуска ПО вместе  аргументами
        :return: запускается программа и подключаются сигналы к слотам
        """
        self.process = QProcess()
        self.process.readyReadStandardError.connect(self.handle_stdout)  # сигнал об ошибках
        self.process.readyReadStandardOutput.connect(self.handle_stdout)  # сигнал во время работы
        self.process.finished.connect(self.process_finished)  # сигнал после завершения всех задач
        self.process.startCommand(cmd)

    def get_cloning_names(self):
        """
        :return: получение имен из полей и запуск клонирования pdb
        """
        pdb_name = self.list_pdb.currentText().upper()
        pdb_name_clone = self.input_newpdb.text().upper()
        self.cloning_pdb([pdb_name, pdb_name_clone])

    def get_snapshots_name(self):
        """
        :return: получение имен из полей и запуск процедуры снапшота pdb
        """
        pdb_name = self.list_pdb.currentText().upper()
        pdb_name_clone = self.input_newpdb.text().upper()
        self.get_snapshot_pdb([pdb_name, pdb_name_clone])

    def cloning_pdb(self, pdb_list_names):
        """
        :param pdb_list_names: получаем лист с исходным именем pdb и новым именем pdb
        :return: создаем строку подключения для запуска клонирования pdb и отправляем на выполнение в QProcess
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = pdb_list_names[0]
        pdb_name_clone = pdb_list_names[1]
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name and pdb_name_clone:
                if pdb_name_clone == 'ASDCOEMPTY_ETALON' or pdb_name_clone == 'PDB$SEED':
                    logger.error('Заблокирована попытка клонирования на базу ASDCOEMPTY_ETALON или PDB$SEED')
                    message_text = 'Клонирование на БД ASDCOEMPTY_ETALON или PDB$SEED запрещено'
                    self.message_windows.msg_window(message_text)
                elif pdb_name_clone == pdb_name:
                    error_message = 'Имя новой PDB и имеющейся PDB не должны совпадать'
                    logger.error(error_message)
                    self.message_windows.msg_window(error_message)
                elif pdb_name_clone == '':
                    error_message = 'Имя новой PDB не заполнено'
                    logger.error(error_message)
                    self.message_windows.msg_window(error_message)
                else:
                    if self.current_user != '65NDA':
                        if pdb_name_clone.startswith(self.short_name):
                            if len(pdb_name_clone) < 25:
                                self.pdb_progressbar.setRange(0, 0)
                                oracle_string = get_string_clone_pdb(connection_string, sysdba_name, sysdba_password,
                                                                     pdb_name, pdb_name_clone)
                                self.execute_command(oracle_string)
                                logger.info(f'Запущена процедура клонирования PDB. '
                                            f'Имя исходной PDB: "{pdb_name}". Имя новой PDB: "{pdb_name_clone}"')
                                self.finish_message = 'Клонирование PDB'
                                self.stbar.showMessage('Идет клонирование PDB...')
                            else:
                                error_message = f'Имя новой PDB не должно превышать 25 символов. ' \
                                                f'Текущее имя содержит {len(pdb_name_clone)} символов'
                                logger.error(error_message)
                                self.message_windows.msg_window(error_message)
                        else:
                            error_message = f'Имя новой PDB должно начинаться с "{self.short_name}"'
                            logger.error(error_message)
                            self.message_windows.msg_window(error_message)
                    else:
                        if len(pdb_name_clone) < 25:
                            self.pdb_progressbar.setRange(0, 0)
                            oracle_string = get_string_clone_pdb(connection_string, sysdba_name, sysdba_password, pdb_name,
                                                                 pdb_name_clone)
                            self.execute_command(oracle_string)
                            logger.info(f'Запущена процедура клонирования PDB. '
                                        f'Имя исходной PDB: "{pdb_name}". Имя новой PDB: "{pdb_name_clone}"')
                            self.finish_message = 'Клонирование PDB'
                            self.stbar.showMessage('Идет клонирование PDB...')
                        else:
                            error_message = f'Имя новой PDB не должно превышать 25 символов. ' \
                                            f'Текущее имя содержит {len(pdb_name_clone)} символов'
                            logger.error(error_message)
                            self.message_windows.msg_window(error_message)
            else:
                logger.warning(f'Не заполнены все обязательные поля. Клонирование PDB {pdb_name_clone} прервано')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name,
                                                     'pdb_name_clone': pdb_name_clone})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def get_snapshot_pdb(self, pdb_list_names):
        """
        :param pdb_list_names: получаем лист с исходным именем pdb и новым именем pdb
        :return: создаем строку подключения для запуска снапшотов pdb и отправляем на выполнение в QProcess
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = pdb_list_names[0]
        pdb_name_clone = pdb_list_names[1]
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name and pdb_name_clone:
                if pdb_name_clone == 'ASDCOEMPTY_ETALON' or pdb_name_clone == 'PDB$SEED':
                    logger.error('Заблокирована попытка клонирования на базу ASDCOEMPTY_ETALON или PDB$SEED')
                    message_text = 'Клонирование на БД ASDCOEMPTY_ETALON или PDB$SEED запрещено'
                    self.message_windows.msg_window(message_text)
                elif pdb_name_clone == pdb_name:
                    error_message = 'Имя новой PDB и имеющейся PDB не должны совпадать'
                    logger.error(error_message)
                    self.message_windows.msg_window(error_message)
                elif pdb_name_clone == '':
                    error_message = 'Имя новой PDB не заполнено'
                    logger.error(error_message)
                    self.message_windows.msg_window(error_message)
                else:
                    if self.current_user != '65NDA':
                        if pdb_name_clone.startswith(self.short_name):
                            if pdb_name.endswith('SNP'):
                                error_message = f'Создавать snapshot для существующего snapshot запрещено. ' \
                                                f'Выберите оригинальную PDB'
                                logger.error(error_message)
                                self.message_windows.msg_window(error_message)
                            else:
                                if len(pdb_name_clone) < 25:
                                    if pdb_name_clone.endswith('SNP'):
                                        new_pdb_clone = pdb_name_clone
                                    else:
                                        new_pdb_clone = pdb_name_clone + '_SNP'
                                    self.pdb_progressbar.setRange(0, 0)
                                    oracle_string = get_string_snapshot_clone_pdb(connection_string, sysdba_name,
                                                                                  sysdba_password, pdb_name, new_pdb_clone)
                                    self.execute_command(oracle_string)
                                    logger.info(f'Запущена процедура клонирования (snapshot) PDB. '
                                                f'Имя исходной PDB: "{pdb_name}". Имя новой PDB: "{new_pdb_clone}"')
                                    self.finish_message = 'Клонирование (snapshot) PDB'
                                    self.stbar.showMessage('Идет клонирование (snapshot) PDB...')
                                else:
                                    error_message = f'Имя новой PDB не должно превышать 25 символов. ' \
                                                    f'Текущее имя содержит {len(pdb_name_clone)} символов'
                                    logger.error(error_message)
                                    self.message_windows.msg_window(error_message)
                        else:
                            error_message = f'Имя новой PDB должно начинаться с "{self.short_name}"'
                            logger.error(error_message)
                            self.message_windows.msg_window(error_message)
                    else:
                        if pdb_name.endswith('SNP'):
                            error_message = f'Создавать snapshot для существующего snapshot запрещено. ' \
                                            f'Выберите оригинальную PDB'
                            logger.error(error_message)
                            self.message_windows.msg_window(error_message)
                        else:
                            if len(pdb_name_clone) < 25:
                                if pdb_name_clone.endswith('SNP'):
                                    new_pdb_clone = pdb_name_clone
                                else:
                                    new_pdb_clone = pdb_name_clone + '_SNP'
                                self.pdb_progressbar.setRange(0, 0)
                                oracle_string = get_string_snapshot_clone_pdb(connection_string, sysdba_name,
                                                                              sysdba_password, pdb_name, new_pdb_clone)
                                self.execute_command(oracle_string)
                                logger.info(f'Запущена процедура клонирования (snapshot) PDB. '
                                            f'Имя исходной PDB: "{pdb_name}". Имя новой PDB: "{new_pdb_clone}"')
                                self.finish_message = 'Клонирование (snapshot) PDB'
                                self.stbar.showMessage('Идет клонирование (snapshot) PDB...')
                            else:
                                error_message = f'Имя новой PDB не должно превышать 25 символов. ' \
                                                f'Текущее имя содержит {len(pdb_name_clone)} символов'
                                logger.error(error_message)
                                self.message_windows.msg_window(error_message)
            else:
                logger.warning(f'Не заполнены все обязательные поля. '
                               f'Клонирование (snapshot) PDB {pdb_name_clone} прервано')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name,
                                                     'pdb_name_clone': pdb_name_clone})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def show_clone_window_for_context_menu(self):
        """
        :return: запуск нового окна с клонированием PDB, в котором присутствуют кнопки клона PDB и snapshot PDB
        """
        self.new_window.show()
        pdb_name = self.pdb_name
        self.new_window.set_name(pdb_name)
        self.new_window.btn_clone_pdb.clicked.connect(lambda: self.cloning_pdb(self.new_window.clone_pdb()))
        self.new_window.btn_snapshot_pdb.clicked.connect(lambda: self.get_snapshot_pdb(self.new_window.clone_pdb()))

    def deleting_pdb(self):
        """
        :return: создаем строку подключения для запуска и отправляем на выполнение в QProcess
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = self.pdb_name
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name:
                if self.current_user != '65NDA':
                    if pdb_name == 'ASDCOEMPTY_ETALON' or pdb_name == 'PDB$SEED':
                        error_message = 'Заблокирована попытка удаления ASDCOEMPTY_ETALON или PDB$SEED'
                        logger.error(error_message)
                        self.message_windows.msg_window(error_message)
                    elif pdb_name.startswith('ETALON'):
                        message_text = f'Пользователю {self.current_user} запрещено удалять эталонные базы'
                        logger.error(message_text)
                        self.message_windows.msg_window(message_text)
                    elif not pdb_name.startswith(self.short_name):
                        error_message = f'Удалять разрешено только PDB, которые начинаются с "{self.short_name}"'
                        logger.error(error_message)
                        self.message_windows.msg_window(error_message)
                    else:
                        if self.show_msg_window == '1':
                            check_output = self.message_windows.msg_accept_delete_pdb(pdb_name)
                            if check_output is True:
                                self.pdb_progressbar.setRange(0, 0)
                                oracle_string = get_string_delete_pdb(connection_string, sysdba_name, sysdba_password, pdb_name)
                                self.execute_command(oracle_string)
                                logger.info(f'Запущена процедура удаления PDB {pdb_name}')
                                self.finish_message = 'Удаление PDB'
                                self.stbar.showMessage('Идет удаление PDB...')
                            else:
                                logger.info(f'Пользователь отменил удаление PDB {pdb_name}')
                        elif self.show_msg_window == '0':
                            logger.info(f'Пользователь {self.current_user} отключил отображение окна с подтверждением удаления PDB')
                            self.pdb_progressbar.setRange(0, 0)
                            oracle_string = get_string_delete_pdb(connection_string, sysdba_name, sysdba_password,
                                                                  pdb_name)
                            self.execute_command(oracle_string)
                            logger.info(f'Запущена процедура удаления PDB {pdb_name}')
                            self.finish_message = 'Удаление PDB'
                            self.stbar.showMessage('Идет удаление PDB...')
                else:
                    if self.show_msg_window == '1':
                        check_output = self.message_windows.msg_accept_delete_pdb(pdb_name)
                        if check_output is True:
                            self.pdb_progressbar.setRange(0, 0)
                            oracle_string = get_string_delete_pdb(connection_string, sysdba_name, sysdba_password, pdb_name)
                            self.execute_command(oracle_string)
                            logger.info(f'Запущена процедура удаления PDB {pdb_name}')
                            self.finish_message = 'Удаление PDB'
                            self.stbar.showMessage('Идет удаление PDB...')
                        else:
                            logger.info(f'Пользователь отменил удаление PDB {pdb_name}')
                    elif self.show_msg_window == '0':
                        logger.info(f'Пользователь {self.current_user} отключил отображение окна с подтверждением удаления PDB')
                        self.pdb_progressbar.setRange(0, 0)
                        oracle_string = get_string_delete_pdb(connection_string, sysdba_name, sysdba_password,
                                                              pdb_name)
                        self.execute_command(oracle_string)
                        logger.info(f'Запущена процедура удаления PDB {pdb_name}')
                        self.finish_message = 'Удаление PDB'
                        self.stbar.showMessage('Идет удаление PDB...')
            else:
                logger.warning(f'Не заполнены все обязательные поля. Удаление PDB {pdb_name} прервано')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завршения старого')

    def make_pdb_writable(self):
        """
        :return: создаем строку подключения для запуска и отправляем на выполнение в QProcess
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = self.pdb_name
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name:
                self.pdb_progressbar.setRange(0, 0)
                oracle_string = get_string_make_pdb_writable(connection_string, sysdba_name, sysdba_password, pdb_name)
                self.execute_command(oracle_string)
                logger.info(f'Запущена процедура перевода PDB "{pdb_name}" в режим доступной для записи')
                self.finish_message = 'Перевести PDB в режим доступной для записи'
                self.stbar.showMessage('Идет перевод PDB в режим доступной для записи...')
            else:
                logger.warning(f'Не заполнены все обязательные поля. Перевод PDB "{pdb_name}" режим записи прерван')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завршения старого')

    def handle_stdout_schemas(self):
        """
        :return: отлавливаем поток данных из запущенной через QProcess программы
        """
        try:
            stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
            stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        except:
            stdout = bytes(self.process.readAllStandardOutput()).decode("cp1251")
            stderr = bytes(self.process.readAllStandardError()).decode("cp1251")
        output = (stdout + stderr).strip()
        find_ora_error = re.compile("ORA-\d{1,5}:|IMP-\d{1,5}:|EXP-\d{1,5}:")
        searching_in_stdout = find_ora_error.search(output)
        try:
            start = output.find(searching_in_stdout.group(0))
            self.error_message = output[start:]
            self.process.kill()
        except:
            self.input_schemas_area.append(output)
            return self.process.exitCode()

    def show_schemas_process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.info('Процесс завершен без ошибок')

    def get_pdbs_schemas(self):
        """
        :return: показать схемы, которые есть в PDB
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name:
                self.schemas_progressbar.setRange(0, 0)
                self.process = QProcess()
                self.process.readyReadStandardError.connect(self.handle_stdout_schemas)
                self.process.readyReadStandardOutput.connect(self.handle_stdout_schemas)
                self.process.finished.connect(self.show_schemas_process_finished)
                connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                oracle_string = get_string_show_oracle_users(connection_string_without_orcl, sysdba_name,
                                                             sysdba_password, pdb_name)
                self.process.startCommand(oracle_string)
            else:
                logger.warning('Не заполнены все обязательные поля. Невозможно отобразить существующие схемы')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def creating_schemas_process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.info('Процесс завершен без ошибок')

    def schemas_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.info('Процесс завершен без ошибок')

    def display_result(self, job_id, data):
        """
        :param job_id: уникальный номер для запущенного процесса
        :param data: данные из потоков stdout, stderr
        :return: записывает потоком данные в input_schemas_area
        """
        self.input_schemas_area.append(data)

    def done_message(self, code, text):
        """
        :param code: код завершения процесса
        :param text: текст завершения процесса
        :return: обработка сигнала о завершении процесса
        """
        if code == 0:
            self.schemas_progressbar.setRange(0, 1)
            self.input_schemas_area.append(f'Схема {self.operation_name} успешно')
        elif code != 0:
            self.schemas_progressbar.setRange(0, 1)
            self.input_schemas_area.append(f'Ошибка. Схема не {self.operation_name}')
            self.message_windows.msg_window(text)

    def extract_vars(self, output_data):
        """
        :param output_data: данные из потока stdout, stderr
        :return: обработанные данные
        """
        data = output_data.strip()
        return data

    def creating_schemas(self):
        """
        :return: создать схемы
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        checked_schemas = [key for key in self.schemas.keys() if self.schemas[key] == 1]
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name:
                if len(checked_schemas) == 1:
                    self.schemas_progressbar.setRange(0, 0)
                    self.process = QProcess()
                    self.process.readyReadStandardError.connect(self.handle_stdout_schemas)
                    self.process.readyReadStandardOutput.connect(self.handle_stdout_schemas)
                    self.process.finished.connect(self.schemas_finished)
                    name = eval('self.input_' + checked_schemas[0] + '_name.text()')
                    identified = eval('self.input_' + checked_schemas[0] + '_pass.text()')
                    connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                    oracle_string = get_string_create_oracle_schema(connection_string_without_orcl, sysdba_name,
                                                                    sysdba_password, name, identified, pdb_name)
                    self.input_schemas_area.append(f'Начато создание схемы {name}')
                    self.process.startCommand(oracle_string)
                elif len(checked_schemas) > 1:
                    self.schemas_progressbar.setRange(0, 0)
                    for schema_name in checked_schemas:
                        self.job.result.connect(self.display_result)
                        self.job.finish.connect(self.done_message)
                        name = eval('self.input_' + schema_name + '_name.text()')
                        identified = eval('self.input_' + schema_name + '_pass.text()')
                        connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                        oracle_string = get_string_create_oracle_schema(connection_string_without_orcl, sysdba_name,
                                                                        sysdba_password, name, identified, pdb_name)
                        self.input_schemas_area.append(f'Начато создание схемы {name}')
                        self.job.execute(oracle_string, parsers=[(self.extract_vars, "result")])
                        self.operation_name = 'создана'
                else:
                    error_message = 'Не найдены отмеченные чекбоксами схемы'
                    logger.warning(error_message)
                    self.message_windows.msg_window(error_message)
            else:
                logger.warning('Не заполнены все обязательные поля. Невозможно cоздать новые схемы')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def import_dumps_process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.info('Процесс завершен без ошибок')
            self.compile_view_and_options(self.name, self.password)

    def import_from_dumps_to_schemas(self):
        """
        :return: импорт из дампа выбранных схем
        """
        connection_string = self.line_main_connect.text()
        pdb_name = self.list_pdb.currentText().upper()
        checked_schemas = [key for key in self.schemas.keys() if self.schemas[key] == 1]
        if self.process is None:
            if connection_string and pdb_name:
                if len(checked_schemas) == 1:
                    name = eval('self.input_' + checked_schemas[0] + '_name.text()')
                    identified = eval('self.input_' + checked_schemas[0] + '_pass.text()')
                    dump_for_schema_path = eval('self.path_' + checked_schemas[0] + '.text()')
                    dump_name = eval('self.pdb_' + checked_schemas[0] + '_name.text()')
                    if name and identified and dump_for_schema_path and dump_name:
                        self.schemas_progressbar.setRange(0, 0)
                        self.process = QProcess()
                        self.process.readyReadStandardError.connect(self.handle_stdout_schemas)
                        self.process.readyReadStandardOutput.connect(self.handle_stdout_schemas)
                        self.process.finished.connect(self.import_dumps_process_finished)
                        connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                        oracle_string = get_string_import_oracle_schema(connection_string_without_orcl, pdb_name, name,
                                                                        identified, dump_name, dump_for_schema_path)
                        self.process.startCommand(oracle_string)
                        self.name = name
                        self.password = identified
                        logger.info(f'Начат процесс импорта из дампа для схемы {name}')
                    else:
                        logger.warning('Не заполнены все обязательные поля. Невозможно импортировать из дампа')
                        message_text = check_empty_fields(**{'name': name,
                                                             'identified': identified,
                                                             'dump_for_schema_path': dump_for_schema_path,
                                                             'dump_name': dump_name})
                        self.message_windows.msg_window(message_text)
                elif len(checked_schemas) > 1:
                    logger.warning(f'Запрещен множественный импорт из дампа')
                    message_text = 'Невозможно импортировать более одной схемы одновременно'
                    self.message_windows.msg_window(message_text)
                else:
                    error_message = 'Не найдены отмеченные чекбоксами схемы'
                    logger.warning(error_message)
                    self.message_windows.msg_window(error_message)
            else:
                logger.warning('Не заполнены все обязательные поля. Невозможно импортировать из дампа')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def compile_view_and_options(self, name, identified):
        """
        :param name: имя схемы, на которой будет проведена компиляция
        :param identified: пароль от схемы
        :return: перекомпиляция view и функций
        """
        connection_string = self.line_main_connect.text()
        bd_name = self.list_pdb.currentText().upper()
        connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
        if name == '' or identified == '':
            logger.error('Компиляция схем невозможна из-за ошибки - не переданы имя и пароль схемы')
        else:
            self.process = QProcess()
            self.process.readyReadStandardError.connect(self.handle_stdout_schemas)
            self.process.readyReadStandardOutput.connect(self.handle_stdout_schemas)
            self.process.finished.connect(self.schemas_finished)
            enabled_schemes_options_string = get_string_enabled_oracle_asdco_options(connection_string_without_orcl,
                                                                                     bd_name, name, identified)
            self.process.startCommand(enabled_schemes_options_string)
            logger.info(f'Начато включение опций и перекомпиляция view и функций для схемы {name}')

    def export_schema_process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.info('Процесс завершен без ошибок')

    def export_from_schema_to_dump(self):
        """
        :return: экспорта дампа из выбранной схемы
        """
        connection_string = self.line_main_connect.text()
        pdb_name = self.list_pdb.currentText().upper()
        checked_schemas = [key for key in self.schemas.keys() if self.schemas[key] == 1]
        if self.process is None:
            if connection_string and pdb_name:
                if len(checked_schemas) == 1:
                    name = eval('self.input_' + checked_schemas[0] + '_name.text()')
                    identified = eval('self.input_' + checked_schemas[0] + '_pass.text()')
                    if name and identified:
                        self.schemas_progressbar.setRange(0, 0)
                        self.process = QProcess()
                        self.process.readyReadStandardError.connect(self.handle_stdout_schemas)
                        self.process.readyReadStandardOutput.connect(self.handle_stdout_schemas)
                        self.process.finished.connect(self.export_schema_process_finished)
                        dump_for_schema_path = pathlib.Path.cwd().joinpath(f'{name}.dmp')
                        connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                        oracle_string = get_string_export_oracle_scheme(connection_string_without_orcl, pdb_name, name,
                                                                        identified, dump_for_schema_path)
                        self.process.startCommand(oracle_string)
                        logger.info(f'Начат процесс экспорта схемы {name} в дамп')
                    else:
                        logger.warning('Не заполнены все обязательные поля. Невозможно экспортировать в файл дампа')
                        message_text = check_empty_fields(**{'name': name,
                                                             'identified': identified})
                        self.message_windows.msg_window(message_text)
                elif len(checked_schemas) > 1:
                    logger.warning(f'Запрещен множественный экспорт схем')
                    message_text = 'Невозможно экспортировать более одной схемы одновременно'
                    self.message_windows.msg_window(message_text)
                else:
                    error_message = 'Не найдены отмеченные чекбоксами схемы'
                    logger.warning(error_message)
                    self.message_windows.msg_window(error_message)
            else:
                logger.warning('Не заполнены все обязательные поля. Невозможно экспортировать в файл дампа')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def deleting_schemas(self):
        """
        :return: удаление выбранных схем
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        checked_schemas = [key for key in self.schemas.keys() if self.schemas[key] == 1]
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name:
                if len(checked_schemas) == 1:
                    self.schemas_progressbar.setRange(0, 0)
                    self.process = QProcess()
                    self.process.readyReadStandardError.connect(self.handle_stdout_schemas)
                    self.process.readyReadStandardOutput.connect(self.handle_stdout_schemas)
                    self.process.finished.connect(self.schemas_finished)
                    name = eval('self.input_' + checked_schemas[0] + '_name.text()')
                    self.input_schemas_area.append(f'Начато удаление схемы {name}')
                    connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                    oracle_string = get_string_delete_oracle_scheme(connection_string_without_orcl, sysdba_name,
                                                                    sysdba_password, pdb_name, name)
                    self.process.startCommand(oracle_string)
                elif len(checked_schemas) > 1:
                    self.schemas_progressbar.setRange(0, 0)
                    for schema_name in checked_schemas:
                        self.job.result.connect(self.display_result)
                        self.job.finish.connect(self.done_message)
                        name = eval('self.input_' + schema_name + '_name.text()')
                        connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                        oracle_string = get_string_delete_oracle_scheme(connection_string_without_orcl, sysdba_name,
                                                                        sysdba_password, pdb_name, name)
                        self.input_schemas_area.append(f'Начато удаление схемы {name}')
                        self.job.execute(oracle_string, parsers=[(self.extract_vars, "result")])
                        self.operation_name = 'удалена'
                else:
                    error_message = 'Не найдены отмеченные чекбоксами схемы'
                    logger.warning(error_message)
                    self.message_windows.msg_window(error_message)
            else:
                logger.warning('Не заполнены все обязательные поля. Невозможно удалить схемы')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def handle_stdout_check_last_login(self):
        """
        :return: отлавливаем поток данных из запущенной через QProcess программы
        """
        try:
            stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
            stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        except:
            stdout = bytes(self.process.readAllStandardOutput()).decode("cp1251")
            stderr = bytes(self.process.readAllStandardError()).decode("cp1251")
        output = (stdout + stderr).strip()
        find_ora_error = re.compile("ORA-\d{1,5}:")
        searching_in_stdout = find_ora_error.search(output)
        try:
            start = output.find(searching_in_stdout.group(0))
            self.error_message = output[start:]
            self.process.kill()
        except:
            with open(self.full_path_to_file_username, 'a') as file:
                file.write(output)
            return self.process.exitCode()

    def check_last_login_process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.schemas_progressbar.setRange(0, 1)
            with open(self.full_path_to_file_username, 'r') as file:
                data = file.read()
            temp_dict = dict()
            temp_list = [[i for i in elements.split('; ')] for elements in data.split('\n\n') if
                         elements != '' and elements != 'Session altered.']
            for i in temp_list:
                temp_dict[i[0]] = i[1].split(' ')[0]
            current_date = str(datetime.now().date())
            for key, value in temp_dict.items():
                value_date = str(datetime.strptime(value, '%d.%m.%Y')).split(' ')[0]
                delta_days = str(date.fromisoformat(current_date) - date.fromisoformat(value_date)).split(' ')[0]
                try:
                    if int(delta_days) > 20:
                        logger.warning(f'В схему {key} не заходили более 20 дней')
                        self.input_schemas_area.insertHtml(f"Последний вход в схему {key} <span style= color:#ff0000;>был выполнен {delta_days} дней назад</span> (последний вход был выполнен {value})<br>")
                    elif int(delta_days) < 20:
                        self.input_schemas_area.insertHtml(f"Последний вход в схему {key} <span style= color:#008000;>был выполнен {delta_days} дней назад</span> (последний вход был выполнен {value})<br>")
                except ValueError:
                    self.input_schemas_area.insertHtml(f"В схему {key} был выполнен вход {value}<br>")
            logger.info('Процесс завершен без ошибок')

    def check_last_login(self):
        """
        :return: проверить последний вход пользователей, отмеченных чекбоксом
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name:
                self.schemas_progressbar.setRange(0, 0)
                connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                oracle_string = get_last_login_to_common_schemas(connection_string_without_orcl, sysdba_name,
                                                                 sysdba_password, pdb_name)
                self.full_path_to_file_username = create_file_for_pdb('username_and_date.txt')
                self.input_schemas_area.clear()
                self.input_schemas_area.append(f'Проверяем последний вход в схемы для PDB: {self.list_pdb.currentText().upper()}\n')
                self.process = QProcess()
                self.process.readyReadStandardError.connect(self.handle_stdout_check_last_login)
                self.process.readyReadStandardOutput.connect(self.handle_stdout_check_last_login)
                self.process.finished.connect(self.check_last_login_process_finished)
                self.process.startCommand(oracle_string)
                logger.info('Запущена проверка последнего входа для созданных пользователей')
            else:
                logger.warning('Не заполнены все обязательные поля. Невозможно отобразить последний вход пользователей')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def sqlscripts_handle_stdout(self):
        """
        :return: отлавливаем поток данных из запущенной через QProcess программы
        """
        try:
            stdout = bytes(self.process.readAllStandardOutput()).decode("cp1251")
            stderr = bytes(self.process.readAllStandardError()).decode("cp1251")
        except:
            stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
            stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        output = (stdout + stderr).strip()
        find_ora_error = re.compile("ORA-\d{1,5}:")
        searching_in_stdout = find_ora_error.search(output)
        try:
            start = output.find(searching_in_stdout.group(0))
            self.error_message = output[start:]
            self.process.kill()
        except:
            self.input_scripts_area.append(output)
            return self.process.exitCode()

    def sqlscripts_process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.scripts_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            self.process = None
            self.scripts_progressbar.setRange(0, 1)
            logger.info('Процесс завершен без ошибок')

    def execute_sql_sqcript(self, cmd):
        """
        :param cmd: строка для запуска ПО вместе аргументами
        :return: запускается программа и подключаются сигналы к слотам
        """
        self.process = QProcess()
        self.process.readyReadStandardError.connect(self.sqlscripts_handle_stdout)  # сигнал об ошибках
        self.process.readyReadStandardOutput.connect(self.sqlscripts_handle_stdout)  # сигнал во время работы
        self.process.finished.connect(self.sqlscripts_process_finished)  # сигнал после завершения всех задач
        self.process.startCommand(cmd)

    def execute_cyrillic_sql_script(self, cmd):
        """
        :param cmd: строка для запуска ПО вместе аргументами
        :return: запускается программа и подключаются сигналы к слотам
        """
        self.process = QProcess()
        self.process.readyReadStandardError.connect(self.sqlscripts_handle_stdout)  # сигнал об ошибках
        self.process.readyReadStandardOutput.connect(self.sqlscripts_handle_stdout)  # сигнал во время работы
        self.process.finished.connect(self.sqlscripts_process_finished)  # сигнал после завершения всех задач
        env = QProcessEnvironment.systemEnvironment()
        env.insert('NLS_LANG', '.CL8MSWIN1251')
        self.process.setProcessEnvironment(env)
        self.process.start('cmd.exe')
        self.process.waitForReadyRead()
        self.process.write('echo off \n'.encode())
        self.process.waitForBytesWritten()
        self.process.write('chcp 1251 \n'.encode())
        self.process.waitForBytesWritten()
        self.process.write(cmd)
        self.process.waitForBytesWritten()
        self.process.write('exit \n'.encode())

    def sqlscripts_runner(self):
        """
        :return: запустить выбранный скрипт на PDB
        """
        sql_script_name = self.list_scripts.currentText()
        connection_string = self.line_main_connect.text()
        schema_name = self.list_schemas_name.currentText().lower()
        pdb_name = self.list_pdb.currentText().upper()
        connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
        self.scripts_progressbar.setRange(0, 0)
        if sql_script_name == 'Установить подключение в настройках':
            sql_script = self.sql_dict.get(sql_script_name).replace('{CONNECTION_WITH_PDB}', f'{connection_string_without_orcl}/{pdb_name}')
            oracle_string = get_string_for_cyrillic_sql_scripts(connection_string_without_orcl, pdb_name, schema_name,
                                                                schema_name, sql_script)
            self.execute_sql_sqcript(oracle_string)
        else:
            sql_script = self.sql_dict.get(sql_script_name)
            if sql_script_name == 'Убрать график смен':
                oracle_string = get_string_for_cyrillic_sql_scripts(connection_string_without_orcl, pdb_name, schema_name,
                                                                    schema_name, sql_script)
                self.execute_sql_sqcript(oracle_string)
            else:
                oracle_string = get_string_for_sql_scripts(connection_string_without_orcl, pdb_name, schema_name,
                                                           schema_name, sql_script)
                self.execute_sql_sqcript(oracle_string)

    def handle_stdout_schemas_name_process_schemas(self):
        """
        :return: отлавливаем поток данных из запущенной через QProcess программы
        """
        try:
            stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
            stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        except:
            stdout = bytes(self.process.readAllStandardOutput()).decode("cp1251")
            stderr = bytes(self.process.readAllStandardError()).decode("cp1251")
        output = (stdout + stderr).strip()
        find_ora_error = re.compile("ORA-\d{1,5}:")
        searching_in_stdout = find_ora_error.search(output)
        try:
            start = output.find(searching_in_stdout.group(0))
            self.error_message = output[start:]
            self.process.kill()
        except:
            with open(self.schemas_name, 'a') as file:
                file.write(output)
            return self.process.exitCode()

    def fill_schemas_name_process_finished(self):
        """
        :return: отлавливаем сигнал о завершении процесса
        """
        if self.process.exitCode() != 0:
            self.process = None
            self.scripts_progressbar.setRange(0, 1)
            logger.warning('Процесс завершен с ошибками')
            self.message_windows.msg_window(self.error_message)
        elif self.process.exitCode() == 0:
            with open(self.schemas_name, 'r') as file:
                data = file.read()
            result_list = [i for i in data.split('\n') if i != '']
            for i in result_list:
                self.list_schemas_name.addItem(i)
            self.list_schemas_name.setCurrentIndex(0)
            self.process = None
            self.scripts_progressbar.setRange(0, 1)
            logger.info('Процесс завершен без ошибок')

    def fill_schemas_list(self):
        """
        :return: заполнить найденными именами схем в PDB
        """
        connection_string = self.line_main_connect.text()
        sysdba_name = self.input_main_login.text()
        sysdba_password = self.input_main_password.text()
        pdb_name = self.list_pdb.currentText().upper()
        if self.process is None:
            if connection_string and sysdba_name and sysdba_password and pdb_name:
                self.scripts_progressbar.setRange(0, 0)
                self.schemas_name = create_file_for_pdb('schemas_name.txt')
                self.process = QProcess()
                self.process.readyReadStandardError.connect(self.handle_stdout_schemas_name_process_schemas)
                self.process.readyReadStandardOutput.connect(self.handle_stdout_schemas_name_process_schemas)
                self.process.finished.connect(self.fill_schemas_name_process_finished)
                connection_string_without_orcl = connection_string[:connection_string.rfind('/')]
                oracle_string = get_string_oracle_users_name(connection_string_without_orcl, sysdba_name,
                                                             sysdba_password, pdb_name)
                self.process.startCommand(oracle_string)
            else:
                logger.warning('Не заполнены все обязательные поля. Невозможно отобразить существующие схемы')
                message_text = check_empty_fields(**{'connection_string': connection_string,
                                                     'sysdba_name': sysdba_name,
                                                     'sysdba_password': sysdba_password,
                                                     'pdb_name': pdb_name})
                self.message_windows.msg_window(message_text)
        else:
            logger.warning('Вызван новый процесс до завершения старого')

    def find_name(self):
        """
        :return: фильтрация данных в таблице
        """
        name = self.input_regexp.text().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            self.table.setRowHidden(row, name not in item.text().lower())

    def checkbox_clicked_for_schemas(self, checked):
        """
        :param checked: принимаем статус чекбокса
        :return: устанавливаем для словаря 1/0
        """
        checkbox = self.sender()
        if checked:
            self.schemas[checkbox.name] = 1
        else:
            self.schemas[checkbox.name] = 0

    def set_path_for_dumps(self):
        """
        :return: устанавливаем путь для каждого дампа схемы
        """
        button = self.sender()
        get_dir = QFileDialog.getOpenFileName(self, caption='Выбрать файл', filter='*.dmp')
        for i in range(1, 6):
            if button is eval('self.btn_path_schema' + str(i)):
                eval('self.path_schema' + str(i) + '.setText(get_dir[0])')

    def clicked_row_column(self, row, column):
        """
        :param row: номер строки
        :param column: номер колонки
        :return: передает в переменную текст, расположенный в строке row и 1 стролбце
        """
        self.pdb_name = self.table.item(row, 0).text()

    def context(self, point, table):
        """
        :param point: координаты вызова меню
        :param table: таблица, в которой вызывается меню
        :return: вызов контексного меню
        """
        menu = QMenu()
        if table.itemAt(point):
            list_pdb = QAction(f'Сделать базу "{self.pdb_name}" доступной для записи', menu)
            list_pdb.triggered.connect(self.make_pdb_writable)
            delete = QAction(f'Удалить выбранную базу "{self.pdb_name}"', menu)
            delete.triggered.connect(self.deleting_pdb)
            clone_pdb = QAction(f'Клонироваться с "{self.pdb_name}"', menu)
            clone_pdb.triggered.connect(self.show_clone_window_for_context_menu)
            menu.addAction(clone_pdb)
            menu.addAction(list_pdb)
            menu.addAction(delete)
        else:
            logger.error('Ошибка вызова контексного меню')
        menu.exec(table.mapToGlobal(point))

    def closeEvent(self, event):
        """
        :param event: событие, которое можно принять или переопределить при закрытии
        :return: охранение настроек при закрытии приложения
        """
        self.settings.setValue('login', self.input_main_login.text())
        self.settings.setValue('connectline', self.line_main_connect.text())
        self.settings.setValue('password', self.input_main_password.text())
        self.settings.setValue('PDB_name', self.list_pdb.currentText())
        self.settings.setValue('exit_date', str(datetime.now()))
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
        self.show_msg_window = self.settings.value('show_window') or '1'
        self.input_main_login.setText(self.settings.value('login'))
        self.line_main_connect.setText(self.settings.value('connectline'))
        self.list_pdb.setCurrentText(self.settings.value('PDB_name'))
        self.input_main_password.setText(self.settings.value('password'))
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
        logger.info('Файл с пользовательскими настройками проинициализирован')

    def header_layout(self):
        """
        :return: добавление виджетов в верхнюю часть интерфейса на главном окне
        """
        self.label_main_login = QLabel('Пользователь sysdba')
        self.input_main_login = QLineEdit()
        self.input_main_login.setPlaceholderText('Имя пользователя DBA')
        self.input_main_password = QLineEdit()
        self.input_main_password.setPlaceholderText('Пароль пользователя DBA')
        self.input_main_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.label_main_connect = QLabel('Строка подключения')
        self.line_main_connect = QLineEdit()
        self.line_main_connect.setToolTip('Пример для .136 сервера: 192.168.65.136:1521/ORCL')
        self.line_main_connect.setPlaceholderText('Указывается ip:порт/Service name')
        self.label_pdb = QLabel('Имя исходной PDB')
        self.list_pdb = QComboBox()
        self.line_for_combobox = QLineEdit()
        self.list_pdb.setLineEdit(self.line_for_combobox)
        self.btn_current_pdb = QPushButton('Показать существующие pdb')
        self.btn_current_pdb.clicked.connect(self.get_pdb_name_from_bd)
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
        self.input_newpdb.setPlaceholderText('Имя новой PDB')
        self.input_newpdb.setToolTip('Введите в данное поле новое имя PDB')
        self.input_newpdb.setMaxLength(21)
        self.btn_clone_pdb = QPushButton('Клонировать PDB')
        self.btn_clone_pdb.clicked.connect(self.get_cloning_names)
        self.btn_clone_pdb.setStyleSheet('width: 450')
        self.btn_clone_pdb.setToolTip('Сделать полную копию PDB')
        self.btn_snapshot_clone = QPushButton('Snapshot PDB')
        self.btn_snapshot_clone.clicked.connect(self.get_snapshots_name)
        self.btn_snapshot_clone.setToolTip('Сделать быструю копию PDB с некоторыми ограничениями')
        self.input_regexp = QLineEdit()
        self.input_regexp.setPlaceholderText('Введите имя для фильтрации списка')
        self.input_regexp.setToolTip('Пример: "NDA" или оставьте поле пустым для получения полного списка')
        self.input_regexp.textChanged.connect(self.find_name)
        self.pdb_progressbar = QProgressBar()
        self.pdb_progressbar.setStyleSheet('text-align: center; min-height: 10px; max-height: 10px;')
        self.table = QTableWidget()
        self.table.cellPressed[int, int].connect(self.clicked_row_column)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.customContextMenuRequested.connect(lambda pos, table=self.table: self.context(pos, table))
        self.table.setItemDelegate(InitialDelegate(2, self.table))
        self.tab_control.layout.addWidget(self.input_newpdb, 0, 0)
        self.tab_control.layout.addWidget(self.btn_clone_pdb, 0, 1)
        self.tab_control.layout.addWidget(self.input_regexp, 1, 0)
        self.tab_control.layout.addWidget(self.btn_snapshot_clone, 1, 1)
        self.tab_control.layout.addWidget(self.table, 2, 0, 1, 2)
        self.tab_control.layout.addWidget(self.pdb_progressbar, 3, 0, 1, 2)
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
        self.checkbox_schema1.stateChanged.connect(self.checkbox_clicked_for_schemas)
        self.pdb_schema1_name = QLineEdit()
        self.pdb_schema1_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema2_name = QLineEdit()
        self.input_schema2_name.setPlaceholderText('Имя новой схемы')
        self.input_schema2_pass = QLineEdit()
        self.input_schema2_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema2_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema2 = QCheckBox()
        self.checkbox_schema2.name = 'schema2'
        self.checkbox_schema2.stateChanged.connect(self.checkbox_clicked_for_schemas)
        self.pdb_schema2_name = QLineEdit()
        self.pdb_schema2_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema3_name = QLineEdit()
        self.input_schema3_name.setPlaceholderText('Имя новой схемы')
        self.input_schema3_pass = QLineEdit()
        self.input_schema3_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema3_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema3 = QCheckBox()
        self.checkbox_schema3.name = 'schema3'
        self.checkbox_schema3.stateChanged.connect(self.checkbox_clicked_for_schemas)
        self.pdb_schema3_name = QLineEdit()
        self.pdb_schema3_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema4_name = QLineEdit()
        self.input_schema4_name.setPlaceholderText('Имя новой схемы')
        self.input_schema4_pass = QLineEdit()
        self.input_schema4_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema4_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema4 = QCheckBox()
        self.checkbox_schema4.name = 'schema4'
        self.checkbox_schema4.stateChanged.connect(self.checkbox_clicked_for_schemas)
        self.pdb_schema4_name = QLineEdit()
        self.pdb_schema4_name.setPlaceholderText('Имя схемы в дампе')
        self.input_schema5_name = QLineEdit()
        self.input_schema5_name.setPlaceholderText('Имя новой схемы')
        self.input_schema5_pass = QLineEdit()
        self.input_schema5_pass.setPlaceholderText('Пароль для новой схемы')
        self.input_schema5_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.checkbox_schema5 = QCheckBox()
        self.checkbox_schema5.name = 'schema5'
        self.checkbox_schema5.stateChanged.connect(self.checkbox_clicked_for_schemas)
        self.pdb_schema5_name = QLineEdit()
        self.pdb_schema5_name.setPlaceholderText('Имя схемы в дампе')
        self.btn_create_schema = QPushButton('Создать схему')
        self.btn_create_schema.clicked.connect(self.creating_schemas)
        self.btn_delete_schema = QPushButton('Удалить схему')
        self.btn_delete_schema.clicked.connect(self.deleting_schemas)
        self.btn_show_schemas = QPushButton('Показать существующие схемы')
        self.btn_show_schemas.clicked.connect(self.get_pdbs_schemas)
        self.btn_import_from_dumps = QPushButton('Импорт из дампа')
        self.btn_import_from_dumps.clicked.connect(self.import_from_dumps_to_schemas)
        self.btn_export_to_dump = QPushButton('Экспорт схемы')
        self.btn_export_to_dump.setToolTip('Дамп создается в директории с исполняемым файлом')
        self.btn_export_to_dump.clicked.connect(self.export_from_schema_to_dump)
        self.btn_check_users_last_login = QPushButton('Проверить последний вход пользователя')
        self.btn_check_users_last_login.clicked.connect(self.check_last_login)
        self.path_schema1 = QLineEdit()
        self.path_schema1.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema1 = self.path_schema1.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema1.triggered.connect(self.set_path_for_dumps)
        self.path_schema2 = QLineEdit()
        self.path_schema2.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema2 = self.path_schema2.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema2.triggered.connect(self.set_path_for_dumps)
        self.path_schema3 = QLineEdit()
        self.path_schema3.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema3 = self.path_schema3.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema3.triggered.connect(self.set_path_for_dumps)
        self.path_schema4 = QLineEdit()
        self.path_schema4.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema4 = self.path_schema4.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema4.triggered.connect(self.set_path_for_dumps)
        self.path_schema5 = QLineEdit()
        self.path_schema5.setPlaceholderText('Введите путь или нажмите на кнопку')
        self.btn_path_schema5 = self.path_schema5.addAction(QIcon(self.btn_icon),
                                                            QLineEdit.ActionPosition.TrailingPosition)
        self.btn_path_schema5.triggered.connect(self.set_path_for_dumps)
        self.input_schemas_area = QTextEdit()
        self.input_schemas_area.setReadOnly(True)
        self.schemas_progressbar = QProgressBar()
        self.schemas_progressbar.setStyleSheet('text-align: center; min-height: 10px; max-height: 10px;')
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
        self.tab_schemas.layout.addWidget(self.btn_show_schemas, 5, 0, 1, 2)
        self.tab_schemas.layout.addWidget(self.btn_create_schema, 5, 2)
        self.tab_schemas.layout.addWidget(self.btn_import_from_dumps, 5, 3)
        self.tab_schemas.layout.addWidget(self.btn_export_to_dump, 5, 4)
        self.tab_schemas.layout.addWidget(self.schemas_progressbar, 6, 0, 1, 5)
        self.tab_schemas.layout.addWidget(self.btn_check_users_last_login, 7, 0, 1, 2)
        self.tab_schemas.layout.addWidget(self.btn_delete_schema, 7, 4)
        self.tab_schemas.layout.addWidget(self.input_schemas_area, 8, 0, 1, 5)

    def scripts_tab(self):
        """
        :return: добавление виджетов на вкладку с pdb
        """
        self.tab_scripts.layout = QGridLayout()
        self.tabs.addTab(self.tab_scripts, "SQL скрипты")
        self.name_schemas = QLabel('Схемы в PDB: ')
        self.sql_scripts = QLabel('Основные SQL скрипты: ')
        self.list_scripts = QComboBox()
        self.list_schemas_name = QComboBox()
        self.btn_fill_schemas_list = QPushButton('Заполнить поле именами схем')
        self.btn_fill_schemas_list.clicked.connect(self.fill_schemas_list)
        self.btn_fill_schemas_list.setStyleSheet('width: 400')
        self.btn_script_runner = QPushButton(f'Запустить скрипт на выбранной PDB')
        self.btn_script_runner.clicked.connect(self.sqlscripts_runner)
        self.btn_script_runner.setStyleSheet('width: 400')
        self.scripts_progressbar = QProgressBar()
        self.scripts_progressbar.setStyleSheet('text-align: center; min-height: 10px; max-height: 10px;')
        self.input_scripts_area = QTextEdit()
        self.input_scripts_area.setReadOnly(True)
        self.tab_scripts.layout.addWidget(self.name_schemas, 0, 0)
        self.tab_scripts.layout.addWidget(self.list_schemas_name, 0, 1)
        self.tab_scripts.layout.addWidget(self.btn_fill_schemas_list, 0, 2)
        self.tab_scripts.layout.addWidget(self.sql_scripts, 1, 0)
        self.tab_scripts.layout.addWidget(self.list_scripts, 1, 1)
        self.tab_scripts.layout.addWidget(self.btn_script_runner, 1, 2)
        self.tab_scripts.layout.addWidget(self.scripts_progressbar, 3, 0, 1, 3)
        self.tab_scripts.layout.addWidget(self.input_scripts_area, 4, 0, 1, 3)
        self.sql_dict = get_sql_dict()
        for i in self.sql_dict:
            self.list_scripts.addItem(i)

    def footer_status_bar(self):
        """
        :return: добавление статусной строки и добавление на него дополнительного элемента
        """
        shortcut = QShortcut(QKeySequence('Ctrl+R'), self)
        shortcut.activated.connect(self.thread_get_info_from_server)
        self.stbar = QStatusBar()
        self.footer_label = QLabel()
        self.stbar.addPermanentWidget(self.footer_label)


if __name__ == '__main__':
    logger.info(f'Запущен файл {__file__}')
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
