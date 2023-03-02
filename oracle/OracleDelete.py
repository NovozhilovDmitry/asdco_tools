from tkinter import *
from tkinter import scrolledtext
from tkinter.ttk import Progressbar
import asyncio

from myLogging import logger
from .integrityOracle12 import get_string_delete_oracle_scheme, \
    check_success_result_delete_oracle_scheme, \
    get_string_show_oracle_users, \
    check_failure_result_show_oracle_users
from additions import MAIN_WINDOW_TITLE

WINDOW_GEOMETRY = r'1100x930'
WINDOW_TITLE = 'Oracle Удаление схем'
WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 80
PADX_LEFT_BORDER = 15
NUMBER_ROWS = 7
INTERVAL = .01
PROGRESSBAR_START_INTERVAL = 1

# Класс строки с пустыми элементами
class EmptyStringGUISuit:
    def __init__(self, window, number_rows, start_row_position=0):
        self.window = window
        self.empty_string = []
        for i in range(number_rows):
            self.empty_string.append(Label(self.window, width=WIDTH_SCHEMA_NAME_FIELD))
            self.empty_string[i].grid(column=i, row=start_row_position + 1)


class SysdbaUserStringGUISuit:
    def __init__(self, window, sysdba_name_string='', sysdba_password_string='', start_row_position=0):
        self.window = window
        self.sysdba_name_string = StringVar(value=sysdba_name_string)
        self.sysdba_password_string = StringVar(value=sysdba_password_string)
        self.label_sysdba_name_string = Label(self.window, text='Пользователь sysdba')
        self.label_sysdba_name_string.grid(column=0, padx=PADX_LEFT_BORDER, pady=9, row=start_row_position + 1, sticky='SE')
        self.field_sysdba_name_string = Entry(self.window, width=WIDTH_SCHEMA_NAME_FIELD, textvariable=self.sysdba_name_string, bg="#EDFAFD")
        self.field_sysdba_name_string.grid(column=1, pady=9, row=start_row_position + 1, sticky='SWE')
        self.field_sysdba_password_string = Entry(self.window, show='*', width=WIDTH_SCHEMA_NAME_FIELD, textvariable=self.sysdba_password_string, bg="#EDFAFD")
        self.field_sysdba_password_string.grid(column=2, pady=9, row=start_row_position + 1, sticky='SWE')


# Класс отображения элементов строки подключения
class ConnectionStringGUISuit:
    def __init__(self, window, connection_string='', start_row_position=0):
        self.window = window
        self.connection_string = StringVar(value=connection_string)
        self.label_connection_string = Label(self.window, text='Строка подключения')
        self.label_connection_string.grid(column=0, padx=PADX_LEFT_BORDER, row=start_row_position + 1, sticky='NE')
        self.field_connection_string = Entry(self.window, width=WIDTH_SCHEMA_NAME_FIELD, textvariable=self.connection_string, bg="#EDFAFD")
        self.field_connection_string.grid(column=1, columnspan=4, row=start_row_position + 1, sticky='NWE')


# Класс отображения элементов схем данных для удаления схем из СУБД
class SchemeGUISuit:
    def __init__(self,
                 window,
                 scheme_id,
                 checked,
                 callback,
                 scheme_name=None,
                 scheme_password=None,
                 enabled=1,
                 start_row_position=0):
        self.window = window
        self.scheme_id = scheme_id
        self.checked = checked
        self.callback = callback
        self.scheme_name = StringVar(value=scheme_name)
        self.scheme_password = StringVar(value=scheme_password)
        self.enabled = IntVar(value=enabled)

        self.label_scheme_name = Label(self.window, text='Имя схемы', state=DISABLED)
        self.label_scheme_name.grid(column=0, row=start_row_position + 1, padx=PADX_LEFT_BORDER, sticky='E')
        self.field_scheme_name = Entry(self.window, width=WIDTH_SCHEMA_NAME_FIELD, textvariable=self.scheme_name, state=DISABLED)
        self.field_scheme_name.grid(column=1, row=start_row_position + 1, sticky='WE')
        self.field_scheme_password = Entry(self.window, show='*', width=WIDTH_SCHEMA_NAME_FIELD, textvariable=self.scheme_password, state=DISABLED)
        self.field_scheme_password.grid(column=2, row=start_row_position + 1, sticky='WE')

        self.checkbutton = Radiobutton(self.window, variable=self.checked, value=self.scheme_id, command=self.callback)
        self.checkbutton.grid(column=3, row=start_row_position + 1, padx=3, sticky='W')

        self.label_1 = Label(self.window)
        self.label_1.grid(column=4, row=start_row_position + 1, sticky='W')


# Основной класс отображения всех элементов окна для удаления схем из СУБД
class OracleDelete(Frame):
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
        self.create_menu()

        self.config_file = config_file
        # self.config = load_config(self.config_file)
        self.oracle_execute_state = False
        self.force_delete = IntVar(value=0)
        self.shift_row_position = 1
        self.empty_string_gui_suit = self._load_empty_string_gui_suit(NUMBER_ROWS, self.shift_row_position)
        self.main_progressbar = Progressbar(self.window, length=200, mode='indeterminate', orient=HORIZONTAL)
        self.shift_row_position += 1
        self.sysdba_user_string_gui_suit = self._load_sysdba_user_string_gui_suit(self.shift_row_position)
        self.shift_row_position += 1
        self.connection_string_gui_suit = self._load_connection_string_gui_suit(self.shift_row_position)
        self.shift_row_position += 1
        self.scheme_gui_suits = self._load_scheme_gui_suits(self.shift_row_position)
        self.scheme_quantity = len(self.scheme_gui_suits)
        self.shift_row_position += self.scheme_quantity
        self.button_delete_scheme = Button(self.window,
                                           text='Удалить схему',
                                           command=self.delete_schemes)
        self.button_delete_scheme.grid(column=0, columnspan=3, padx=PADX_LEFT_BORDER, pady=18, row=self.shift_row_position + 1, sticky='WE')
        self.result_scrolledtext = scrolledtext.ScrolledText(self.window, width=120, height=30, wrap=WORD)
        self.result_scrolledtext.grid(column=0, columnspan=NUMBER_ROWS, padx=PADX_LEFT_BORDER, pady=9, row=self.shift_row_position + 2, sticky='WE')

    def set_visibility_scheme_gui_suits(self):
        for item in self.scheme_gui_suits:
            current_state = NORMAL if self.checked.get() == int(item.scheme_id) else DISABLED
            item.label_scheme_name.config(state=current_state)
            item.field_scheme_name.config(state=current_state)
            item.field_scheme_password.config(state=current_state)

    def create_menu(self):
        self.window.config(menu=self.main_menu)
        self.config_menu.add_command(label='Показать существующие схемы', command=self.show_shemes)
        self.config_menu.add_separator()
        self.config_menu.add_command(label='Сохранить текущие настройки', command=self._save_current_config)
        self.main_menu.add_cascade(label='Конфигурация', menu=self.config_menu)

    def delete_schemes(self):
        connection_string = self.connection_string_gui_suit.field_connection_string.get()
        sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
        sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
        for item in self.scheme_gui_suits:
            if item.checked.get() == int(item.scheme_id):
                scheme_name = item.field_scheme_name.get()
                oracle_string, oracle_string_mask_password = get_string_delete_oracle_scheme(sysdba_name,
                                                                                             sysdba_password,
                                                                                             connection_string,
                                                                                             scheme_name)
                self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
                                                                                           oracle_string_mask_password,
                                                                                           check_success_result_delete_oracle_scheme,
                                                                                           label_item=item.label_1,
                                                                                           label_text="deleted schema"))

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
        self.button_delete_scheme.configure(state=DISABLED)

    def _stop_main_progressbar(self):
        self.main_progressbar.stop()
        self.main_progressbar.grid_forget()
        self.button_delete_scheme.configure(state=NORMAL)

    def _load_empty_string_gui_suit(self, number_rows, start_row_position):
        return EmptyStringGUISuit(self.window,
                                  number_rows,
                                  start_row_position)

    def _load_connection_string_gui_suit(self, start_row_position):
        return ConnectionStringGUISuit(self.window,
                                       self.config['connection_string'],
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
                gui_suits.append(SchemeGUISuit(self.window,
                                               scheme_id,
                                               self.checked,
                                               self.set_visibility_scheme_gui_suits,
                                               scheme['name'],
                                               scheme['password'],
                                               scheme['enabled'],
                                               start_row_position))
                start_row_position += 1
        except KeyError as error:
            logger.error(f'KeyError in _load_volume_gui_suits() {error}!')
        return gui_suits

    def _save_current_config(self):
        if self.oracle_execute_state:
            self.config['connection_string'] = self.connection_string_gui_suit.field_connection_string.get()
            self.config['sysdba_name_string'] = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
            self.config['sysdba_password_string'] = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
        for item in self.scheme_gui_suits:
            scheme_id = item.scheme_id
            enabled = item.enabled.get()
            self.config['scheme'][scheme_id]['enabled'] = enabled
            if enabled:
                self.config['scheme'][scheme_id]['name'] = item.field_scheme_name.get()
                self.config['scheme'][scheme_id]['password'] = item.field_scheme_password.get()
        # dump_config(self.config, self.config_file)


if __name__ == '__main__':
    pass
