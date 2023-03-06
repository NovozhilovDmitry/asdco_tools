from tkinter import *
from tkinter import scrolledtext
from tkinter.ttk import Progressbar
import asyncio

from myLogging import logger
from .integrityOracle12 import get_string_check_oracle_connection, \
    check_success_result_check_oracle_connection, \
    get_string_expdp_oracle_scheme, \
    check_failure_result_expdp_oracle_scheme, \
    get_string_show_oracle_users, \
    check_failure_result_show_oracle_users, \
    get_string_show_pdbs, \
    check_failure_result_show_pdbs
from additions import MAIN_WINDOW_TITLE
from .OracleCommon import SysdbaUserStringGUISuit, ConnectionStringGUISuit, ConnectionCDBStringGUISuit, SchemeGUISuit


WINDOW_TITLE = 'Oracle (local). Экспорт схем (data pump)'
WINDOW_GEOMETRY = r'1350x920'
WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 40
PADX_LEFT_BORDER = 15
NUMBER_ROWS = 10
INTERVAL = .01
PROGRESSBAR_START_INTERVAL = 1


# Основной класс отображения всех элементов окна для выполнения экспорта из СУБД
class OracleExpdp(Frame):
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
        self.button_export_scheme = Button(self.window,
                                           text='Экспортировать (data pump)',
                                           command=self.export_schemes,
                                           state=DISABLED)
        self.button_export_scheme.grid(column=3, columnspan=3, pady=18, row=self.shift_row_position + 1, sticky='WE')
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
        print("check_schemes_connection")
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

    def export_schemes(self):
        connection_string = self.connection_string_gui_suit.field_connection_string.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
        for item in self.scheme_gui_suits:
            if item.checked.get() == int(item.scheme_id):
                scheme_name = item.field_scheme_name.get()
                scheme_import_dump_file = item.field_scheme_dump_file.get()
                oracle_string, oracle_string_mask_password = get_string_expdp_oracle_scheme(connection_string,
                                                                                            sysdba_name,
                                                                                            sysdba_password,
                                                                                            scheme_name,
                                                                                            scheme_import_dump_file)
                self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                           oracle_string_mask_password,
                                                                                           check_failure_result_expdp_oracle_scheme,
                                                                                           label_item=item.label_2,
                                                                                           label_text="exported",
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

    # Запуск асинхронной команды в отдельном процессе:
    # - Во время работы основной команды в асинхронном режиме запускается проверка stdout
    #   для поиска ключевых выражений для определения успешености выполнения;
    # - Если задан параметр run_next_function, то после успешного выполнения запускается
    #   функция переданная в этом параметре.
    async def run_async_cmd_with_check_and_run_next_functions(self,
                                                              cmd,
                                                              cmd_mask_password,
                                                              check_function,
                                                              run_next_function=None,
                                                              label_item=None,
                                                              label_text="",
                                                              check_failure=False):
        if cmd_mask_password:
            self.result_scrolledtext.insert(END, f'{cmd_mask_password}\n')
        else:
            self.result_scrolledtext.insert(END, f'{cmd}\n')
        self.result_scrolledtext.see(END)
        self._start_main_progressbar()
        process = await asyncio.create_subprocess_shell(cmd,
                                                        stdin=asyncio.subprocess.PIPE,
                                                        stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.PIPE)
        self.oracle_execute_state = check_failure

        async def check_stdout():
            while True:
                data = await process.stdout.readline()
                line = data.decode('cp1251')
                if line:
                    if check_failure:
                        self.oracle_execute_state = self.oracle_execute_state and (not check_function(line))
                    else:
                        self.oracle_execute_state = self.oracle_execute_state or check_function(line)
                    self.result_scrolledtext.insert(END, f'{line}')
                    self.result_scrolledtext.see(END)
                else:
                    if process.returncode is None:
                        await asyncio.sleep(INTERVAL)
                    else:
                        break

        async def check_stderr():
            while True:
                data = await process.stderr.readline()
                line = data.decode('cp1251')
                if line:
                    self.result_scrolledtext.insert(END, f'{line}')
                    self.result_scrolledtext.see(END)
                else:
                    if process.returncode is None:
                        await asyncio.sleep(INTERVAL)
                    else:
                        break

        await asyncio.gather(check_stdout(), check_stderr())

        logger.info(f"process.returncode={process.returncode}")
        if process.returncode == 0 and self.oracle_execute_state:
            self.result_scrolledtext.insert(END, 'Команда выполнена успешно\n')
            self._save_current_config()
            if label_item:
                label_item.configure(text=f"{label_text}")
            if run_next_function:
                run_next_function()
        # Данный случай для команды expdp.exe
        elif process.returncode == 5 and self.oracle_execute_state:
            self.result_scrolledtext.insert(END, 'Команда выполнена с предупреждениями\n')
            self._save_current_config()
            if label_item:
                label_item.configure(text=f"{label_text}")
            if run_next_function:
                run_next_function()
        else:
            self.result_scrolledtext.insert(END, 'Команда завершена с ошибкой.\n')
            if label_item:
                label_item.configure(text=f"not {label_text}")
        self.result_scrolledtext.see(END)
        self._stop_main_progressbar()
        return process.returncode == 0

    def _start_main_progressbar(self):
        self.main_progressbar.start(PROGRESSBAR_START_INTERVAL)
        self.main_progressbar.grid(column=0, columnspan=2, padx=PADX_LEFT_BORDER, pady=18, sticky='WE')
        self.button_check_connection.configure(state=DISABLED)
        self.button_export_scheme.configure(state=DISABLED)

    def _stop_main_progressbar(self):
        self.main_progressbar.stop()
        self.main_progressbar.grid_forget()
        self.button_check_connection.configure(state=NORMAL)
        if self.oracle_execute_state:
            self.button_export_scheme.configure(state=NORMAL)
        else:
            self.button_export_scheme.configure(state=DISABLED)

    def _load_connection_string_gui_suit(self, start_row_position):
        return ConnectionStringGUISuit(self.window,
                                       self.config['connection_string'],
                                       start_row_position)

    def _load_connection_cdb_string_gui_suit(self, start_row_position):
        return ConnectionCDBStringGUISuit(self.window,
                                          self.config['connection_cdb_string'],
                                          self.config['pdb_name'],
                                          self.config['remote_system_data_pump_dir'],
                                          self.config['local_system_data_pump_dir'],
                                          start_row_position)

    def _load_sysdba_user_string_gui_suit(self, start_row_position):
        return SysdbaUserStringGUISuit(self.window,
                                       self.config['sysdba_name_string'],
                                       self.config['sysdba_password_string'],
                                       start_row_position)

    def _load_scheme_gui_suits(self, start_row_position):
        gui_suits = []
        try:
            for scheme_id in sorted(self.config['scheme'].keys()):
                scheme = self.config['scheme'][scheme_id]
                dump_file = scheme['dump_file']
                gui_suits.append(SchemeGUISuit(self.window,
                                               scheme_id,
                                               self.checked,
                                               self.set_visibility_scheme_gui_suits,
                                               scheme['name'],
                                               scheme['password'],
                                               scheme['enabled'],
                                               dump_file,
                                               start_row_position))
                start_row_position += 1
        except KeyError as error:
            logger.error(f'KeyError in _load_scheme_gui_suits() {error}!')
        return gui_suits

    def _save_current_config(self):
        if self.oracle_execute_state:
            self.config['connection_string'] = self.connection_string_gui_suit.field_connection_string.get()
            self.config['connection_cdb_string'] = self.connection_cdb_string_gui_suit.field_connection_string.get()
            self.config['pdb_name'] = self.connection_cdb_string_gui_suit.field_pdb_name.get()
            self.config['sysdba_name_string'] = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
            self.config['sysdba_password_string'] = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
        for item in self.scheme_gui_suits:
            scheme_id = item.scheme_id
            enabled = item.enabled.get()
            self.config['scheme'][scheme_id]['enabled'] = enabled
            if enabled:
                self.config['scheme'][scheme_id]['name'] = item.field_scheme_name.get()
                self.config['scheme'][scheme_id]['password'] = item.field_scheme_password.get()
                self.config['scheme'][scheme_id]['dump_file'] = item.scheme_name_dump_file.get()
        # dump_config(self.config, self.config_file)

    def _refresh(self):
        # self.config = load_config(self.config_file)
        self.scheme_gui_suits = self._load_scheme_gui_suits(self.scheme_gui_suits_start_row_position)


if __name__ == '__main__':
    pass
