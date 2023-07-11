from tkinter import *
from tkinter import scrolledtext
from tkinter.ttk import Progressbar
import asyncio

from myLogging import logger
from .integrityOracle12 import get_string_check_oracle_connection, \
    check_success_result_check_oracle_connection, \
    get_string_impdp_oracle_scheme, \
    check_failure_result_impdp_oracle_scheme, \
    get_string_show_oracle_users, \
    check_failure_result_show_oracle_users, \
    get_string_enabled_oracle_asdco_options, \
    check_failure_enabled_oracle_asdco_options

WINDOW_TITLE = 'Oracle (local). Импорт схем (data pump)'
WINDOW_GEOMETRY = r'1350x920'
WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 40
PADX_LEFT_BORDER = 15
NUMBER_ROWS = 10
INTERVAL = .01
PROGRESSBAR_START_INTERVAL = 1


# Основной класс отображения всех элементов окна для выполнения экспорта из СУБД
class OracleImpdp(Frame):
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
        self.asdco_menu = Menu(self.main_menu, tearoff=0)
        self.pdb_menu = Menu(self.main_menu, tearoff=0)
        self.create_menu()

        self.config_file = config_file
        # self.config = load_config(self.config_file)
        self.oracle_execute_state = False
        self.auto_confirmation = IntVar(value=1)
        self.main_progressbar = Progressbar(self.window, length=200, mode='indeterminate', orient=HORIZONTAL)
        self.shift_row_position = 1
        self.sysdba_user_string_gui_suit = self._load_sysdba_user_string_gui_suit(self.shift_row_position)
        self.shift_row_position += 1
        self.connection_string_gui_suit = self._load_connection_string_gui_suit(self.shift_row_position)
        self.label_1 = Label(self.window)
        self.label_1.grid(column=7, row=self.shift_row_position + 1, sticky='WE')
        self.shift_row_position += 1
        self.connection_cdb_string_gui_suit = self._load_connection_cdb_string_gui_suit(self.shift_row_position)
        self.shift_row_position += 3
        self.scheme_gui_suits_start_row_position = self.shift_row_position
        self.scheme_gui_suits = self._load_scheme_gui_suits(self.scheme_gui_suits_start_row_position)
        self.scheme_quantity = len(self.scheme_gui_suits)
        self.shift_row_position += self.scheme_quantity
        self.button_check_connection = Button(self.window,
                                              text='Проверка соединения',
                                              # запускается цепочка функций
                                              # check_connection()->check_schemes_connection()
                                              command=self.check_connection)
        self.button_check_connection.grid(column=0, columnspan=3, padx=PADX_LEFT_BORDER, pady=18,
                                          row=self.shift_row_position + 1, sticky='WE')
        self.button_import_scheme = Button(self.window,
                                           text='Импортировать (data pump)',
                                           command=self.import_schemes,
                                           state=DISABLED)
        self.button_import_scheme.grid(column=3, columnspan=3, pady=18, row=self.shift_row_position + 1, sticky='WE')
        self.result_scrolledtext = scrolledtext.ScrolledText(self.window, width=140, height=30, wrap=WORD)
        self.result_scrolledtext.grid(column=0, columnspan=10, padx=PADX_LEFT_BORDER, pady=9,
                                      row=self.shift_row_position + 2, sticky='WE')

    def set_visibility_scheme_gui_suits(self):
        for item in self.scheme_gui_suits:
            current_state = NORMAL if self.checked.get() == int(item.scheme_id) else DISABLED
            item.label_scheme_name.config(state=current_state)
            item.field_scheme_name.config(state=current_state)
            item.field_scheme_password.config(state=current_state)
            item.label_scheme_dump_file.config(state=current_state)
            item.field_scheme_dump_file.config(state=current_state)

    def create_menu(self):
        self.window.config(menu=self.main_menu)
        self.config_menu.add_command(label='Показать существующие схемы', command=self.show_shemes)
        self.config_menu.add_separator()
        self.config_menu.add_command(label='Сохранить текущие настройки', command=self._save_current_config)
        self.main_menu.add_cascade(label='Конфигурация', menu=self.config_menu)
        self.asdco_menu.add_command(label='Предоставление привилегий и компиляция объектов схем(ы)',
                                    command=self.enabled_schemes_options)
        self.main_menu.insert_cascade(0, label='АС ДКО', menu=self.asdco_menu)
        # self.pdb_menu.add_command(label='Показать существующие PDB', command=self.show_pdbs)
        # self.main_menu.insert_cascade(0, label='PDB', menu=self.pdb_menu)

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
                                                                                   run_next_function=self.check_schemes_connection))

    def check_schemes_connection(self):
        connection_string = self.connection_string_gui_suit.field_connection_string.get()
        for item in self.scheme_gui_suits:
            if item.checked.get() == int(item.scheme_id):
                scheme_name = item.field_scheme_name.get()
                scheme_password = item.field_scheme_password.get()
                oracle_string, oracle_string_mask_password = get_string_check_oracle_connection(connection_string,
                                                                                                scheme_name,
                                                                                                scheme_password)
                self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                           oracle_string_mask_password,
                                                                                           check_success_result_check_oracle_connection,
                                                                                           label_item=item.label_1,
                                                                                           label_text="connected"))

    def import_schemes(self):
        connection_string = self.connection_string_gui_suit.field_connection_string.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
        for item in self.scheme_gui_suits:
            if item.checked.get() == int(item.scheme_id):
                scheme_name = item.field_scheme_name.get()
                scheme_import_dump_file = item.field_scheme_dump_file.get()
                oracle_string, oracle_string_mask_password = get_string_impdp_oracle_scheme(connection_string,
                                                                                            sysdba_name,
                                                                                            sysdba_password,
                                                                                            scheme_name,
                                                                                            scheme_import_dump_file)
                self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                           oracle_string_mask_password,
                                                                                           check_failure_result_impdp_oracle_scheme,
                                                                                           run_next_function=self.enabled_schemes_options,
                                                                                           label_item=item.label_2,
                                                                                           label_text="imported",
                                                                                           check_failure=True))
    def enabled_schemes_options(self):
        connection_string = self.connection_string_gui_suit.field_connection_string.get()
        for item in self.scheme_gui_suits:
            if item.checked.get() == int(item.scheme_id):
                scheme_name = item.field_scheme_name.get()
                scheme_password = item.field_scheme_password.get()

                oracle_string, oracle_string_mask_password = get_string_enabled_oracle_asdco_options(connection_string,
                                                                                                     scheme_name,
                                                                                                     scheme_password)
                self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                           oracle_string_mask_password,
                                                                                           check_failure_enabled_oracle_asdco_options,
                                                                                           label_item=item.label_3,
                                                                                           label_text="compiled",
                                                                                           check_failure=True))

    def show_shemes(self):
        connection_string = self.connection_string_gui_suit.field_connection_string.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()

        oracle_string, oracle_string_mask_password = get_string_show_oracle_users(sysdba_name,
                                                                                  sysdba_password,
                                                                                  connection_string)
        self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                   oracle_string_mask_password,
                                                                                   check_failure_result_show_oracle_users,
                                                                                   check_failure=True))

    def show_pdbs(self):
        connection_string = self.connection_cdb_string_gui_suit.field_connection_string.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()

        oracle_string, oracle_string_mask_password = get_string_show_pdbs(sysdba_name,
                                                                          sysdba_password,
                                                                          connection_string)
        self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                   oracle_string_mask_password,
                                                                                   check_failure_result_show_pdbs,
                                                                                   check_failure=True))

if __name__ == '__main__':
    pass
