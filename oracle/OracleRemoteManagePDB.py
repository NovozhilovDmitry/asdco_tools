from tkinter import *
from tkinter import scrolledtext
from tkinter.ttk import Progressbar
import asyncio

from myLogging import logger
from .integrityOracle12 import (get_string_check_oracle_connection,
                                check_success_result_check_oracle_connection,
                                get_string_make_pdb_writable,
                                check_failure_result_make_pdb_writable,
                                # get_string_show_pdbs,
                                # check_failure_result_show_pdbs,
                                get_string_create_data_pump_dir,
                                check_failure_result_create_data_pump_dir,
                                get_string_clone_pdb,
                                check_failure_result_clone_pdb)
from additions import MAIN_WINDOW_TITLE
from .OracleCommon import SysdbaUserStringGUISuit, ConnectionStringGUISuit, ConnectionCDBStringGUISuit


WINDOW_TITLE = 'Oracle (remote). Управление PDB'
WINDOW_GEOMETRY = r'1350x920'
WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 40
PADX_LEFT_BORDER = 15
NUMBER_ROWS = 10
INTERVAL = .01
PROGRESSBAR_START_INTERVAL = 1


# Класс отображения элементов строки клонирования PDB
class PDBCloneGUISuit:
    def __init__(self,
                 window,
                 pdb_name='',
                 pdb_name_cloned='',
                 start_row_position=0):
        self.window = window
        self.pdb_name = StringVar(value=pdb_name)
        self.pdb_name_cloned = StringVar(value=pdb_name_cloned)

        self.label_pdb_name = Label(self.window, text='Исходная PDB*')
        self.label_pdb_name.grid(column=0, padx=PADX_LEFT_BORDER,  pady=15, row=start_row_position + 1, sticky='SE')
        self.field_pdb_name = Entry(self.window, textvariable=self.pdb_name)
        self.field_pdb_name.grid(column=1, columnspan=1, pady=15, row=start_row_position + 1, sticky='SWE')
        self.label_pdb_name_cloned = Label(self.window, text='Имя новой PDB ')
        self.label_pdb_name_cloned.grid(column=2, pady=15, row=start_row_position + 1, sticky='SE')
        self.field_pdb_name_cloned = Entry(self.window, textvariable=self.pdb_name_cloned)
        self.field_pdb_name_cloned.grid(column=3, pady=15, columnspan=1, row=start_row_position + 1, sticky='SWE')
        self.label_description = Label(self.window, text='*После клонирования исходная PDB становится read-only')
        self.label_description.grid(column=5, pady=15, row=start_row_position + 1, sticky='SWE')


# Основной класс отображения всех элементов окна для управления PDB remote СУБД
class OracleRemoteManagePDB(Frame):
    def __init__(self, parent, loop, config_file):
        Frame.__init__(self, parent)
        self.window = parent
        self.loop = loop
        self.window.grab_set()
        self.window.focus()
        self.window.title(f"{MAIN_WINDOW_TITLE}: {WINDOW_TITLE}")
        self.window.geometry(WINDOW_GEOMETRY)
        self.checked = IntVar()

        self.main_menu = Menu(self.window)
        self.config_menu = Menu(self.main_menu, tearoff=0)
        self.pdb_menu = Menu(self.main_menu, tearoff=0)
        # self.create_menu()

        self.config_file = config_file
        # self.config = load_config(self.config_file)
        self.oracle_execute_state = False
        self.auto_confirmation = IntVar(value=1)
        self.main_progressbar = Progressbar(self.window, length=200, mode='indeterminate', orient=HORIZONTAL)

        self.shift_row_position = 1
        # self.sysdba_user_string_gui_suit = self._load_sysdba_user_string_gui_suit(self.shift_row_position)
        self.shift_row_position += 1
        # self.connection_string_gui_suit = self._load_connection_string_gui_suit(self.shift_row_position)
        self.label_1 = Label(self.window)
        self.label_1.grid(column=7, row=self.shift_row_position + 1, sticky='WE')
        self.shift_row_position += 1
        # self.connection_cdb_string_gui_suit = self._load_connection_cdb_string_gui_suit(self.shift_row_position)
        self.shift_row_position += 3
        # self.pdbd_clone_gui_suit = self._load_pdbd_clone_gui_suit(self.shift_row_position)
        self.shift_row_position += 1
        self.button_check_connection = Button(self.window,
                                              text='Проверка соединения',
                                              # запускается цепочка функций
                                              # check_connection()->check_cdb_connection()
                                              command=self.check_connection)
        self.button_check_connection.grid(column=0, columnspan=2, padx=PADX_LEFT_BORDER, pady=18, row=self.shift_row_position + 1, sticky='WE')
        self.button_clone_pdb = Button(self.window,
                                       text='Клонировать PDB',
                                       command=self.clone_pdb,
                                       state=DISABLED)
        self.button_clone_pdb.grid(column=2, columnspan=3, padx=40, pady=18, row=self.shift_row_position + 1, sticky='WE')
        self.button_make_writable = Button(self.window,
                                       text='Сделать исходную PDB writable',
                                       command=self.make_pdb_writable,
                                       state=DISABLED)
        self.button_make_writable.grid(column=4, columnspan=4, padx=40, pady=18, row=self.shift_row_position + 1, sticky='WE')
        self.result_scrolledtext = scrolledtext.ScrolledText(self.window, width=140, height=30, wrap=WORD)
        self.result_scrolledtext.grid(column=0, columnspan=10, padx=PADX_LEFT_BORDER, pady=9,
                                      row=self.shift_row_position + 2, sticky='WE')


    def check_connection(self):
        connection_string = self.connection_string_gui_suit.field_connection_string.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
        oracle_string, oracle_string_mask_password = get_string_check_oracle_connection(connection_string,
                                                                                        sysdba_name,
                                                                                        sysdba_password,
                                                                                        connection_as_sysdba=True)
        self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                   oracle_string_mask_password,
                                                                                   check_success_result_check_oracle_connection,
                                                                                   run_next_function=self.check_cdb_connection))

    def check_cdb_connection(self):
        # Включает внутреннюю проверку на валидность написания имени PDB
        # Реализовано в виде  проверка на полное вхождение имени PDB в строку подключеия к PDB
        connection_string = self.connection_string_gui_suit.connection_string.get()
        pdb_string = self.pdbd_clone_gui_suit.pdb_name.get()
        if pdb_string not in connection_string:
            self.oracle_execute_state = False
            self.result_scrolledtext.insert(END, '\nОшибка в имени PDB!\nКоманда завершена с ошибкой.\n')
            # self._stop_main_progressbar()
            return
        else:
            self.result_scrolledtext.insert(END, '\nPDB указана верно.\n')
        self.result_scrolledtext.see(END)

        connection_string = self.connection_cdb_string_gui_suit.field_connection_string.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
        oracle_string, oracle_string_mask_password = get_string_check_oracle_connection(connection_string,
                                                                                        sysdba_name,
                                                                                        sysdba_password,
                                                                                        connection_as_sysdba=True)
        self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                   oracle_string_mask_password,
                                                                                   check_success_result_check_oracle_connection))

    def make_pdb_writable(self):
        connection_string = self.connection_cdb_string_gui_suit.field_connection_string.get()
        pdb_name = self.pdbd_clone_gui_suit.field_pdb_name.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()

        oracle_string, oracle_string_mask_password = get_string_make_pdb_writable(sysdba_name,
                                                                                  sysdba_password,
                                                                                  connection_string,
                                                                                  pdb_name)
        self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                   oracle_string_mask_password,
                                                                                   check_failure_result_make_pdb_writable,
                                                                                   check_failure=True,
                                                                                   label_item=self.label_1,
                                                                                   label_text="is writable now"))

# зачем?
    def create_pdb_directory(self):
        connection_string = self.connection_cdb_string_gui_suit.field_connection_string.get()
        remote_system_data_pump_dir = self.connection_cdb_string_gui_suit.remote_system_data_pump_dir.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()

        oracle_string, oracle_string_mask_password = get_string_create_data_pump_dir(sysdba_name,
                                                                                     sysdba_password,
                                                                                     connection_string,
                                                                                     remote_system_data_pump_dir)
        self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                   oracle_string_mask_password,
                                                                                   check_failure_result_create_data_pump_dir,
                                                                                   check_failure=True))

    def clone_pdb(self):
        connection_string = self.connection_cdb_string_gui_suit.field_connection_string.get()
        pdb_name = self.pdbd_clone_gui_suit.field_pdb_name.get()
        pdb_name_cloned = self.pdbd_clone_gui_suit.field_pdb_name_cloned.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()

        oracle_string, oracle_string_mask_password = get_string_clone_pdb(sysdba_name,
                                                                          sysdba_password,
                                                                          connection_string,
                                                                          pdb_name,
                                                                          pdb_name_cloned)
        self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                   oracle_string_mask_password,
                                                                                   check_failure_result_clone_pdb,
                                                                                   check_failure=True,
                                                                                   label_item=self.label_1,
                                                                                   label_text="is writable now"))



if __name__ == '__main__':
    pass
