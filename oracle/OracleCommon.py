from tkinter import *

WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 40
PADX_LEFT_BORDER = 15
NUMBER_ROWS = 10


class SysdbaUserStringGUISuit:
    def __init__(self,
                 window,
                 sysdba_name_string='',
                 sysdba_password_string='',
                 start_row_position=0):
        self.window = window
        self.sysdba_name_string = StringVar(value=sysdba_name_string)
        self.sysdba_password_string = StringVar(value=sysdba_password_string)
        self.label_sysdba_name_string = Label(self.window, text='Пользователь sysdba')
        self.label_sysdba_name_string.grid(column=0, padx=PADX_LEFT_BORDER, pady=9, row=start_row_position + 1,
                                           sticky='SE')
        self.field_sysdba_name_string = Entry(self.window, width=WIDTH_SCHEMA_NAME_FIELD,
                                              textvariable=self.sysdba_name_string, bg="#EDFAFD")
        self.field_sysdba_name_string.grid(column=1, pady=9, row=start_row_position + 1, sticky='SWE')
        self.field_sysdba_password_string = Entry(self.window, show='*', width=WIDTH_SCHEMA_NAME_FIELD,
                                                  textvariable=self.sysdba_password_string, bg="#EDFAFD")
        self.field_sysdba_password_string.grid(column=2, pady=9, row=start_row_position + 1, sticky='SWE')


# Класс отображения элементов строки подключения
class ConnectionStringGUISuit:
    def __init__(self,
                 window,
                 connection_string='',
                 start_row_position=0):
        self.window = window
        self.connection_string = StringVar(value=connection_string)
        self.label_connection_string = Label(self.window, text='Строка подключения')
        self.label_connection_string.grid(column=0, padx=PADX_LEFT_BORDER, row=start_row_position + 1, sticky='NE')
        self.field_connection_string = Entry(self.window, width=WIDTH_SCHEMA_NAME_FIELD,
                                             textvariable=self.connection_string, bg="#EDFAFD")
        self.field_connection_string.grid(column=1, columnspan=5, row=start_row_position + 1, sticky='NWE')


# Класс отображения элементов строки подключения к CDB
class ConnectionCDBStringGUISuit:
    def __init__(self,
                 window,
                 connection_string='',
                 pdb_name='',
                 remote_system_data_pump_dir='',
                 local_system_data_pump_dir="",
                 start_row_position=0):
        self.window = window
        self.connection_string = StringVar(value=connection_string)
        self.pdb_name = StringVar(value=pdb_name)
        self.remote_system_data_pump_dir = StringVar(value=remote_system_data_pump_dir)
        self.local_system_data_pump_dir = StringVar(value=local_system_data_pump_dir)

        self.label_pdb_name = Label(self.window, text='Имя PDB')
        self.label_pdb_name.grid(column=0, pady=9, padx=PADX_LEFT_BORDER, row=start_row_position + 1, sticky='SE')
        self.field_pdb_name = Entry(self.window, textvariable=self.pdb_name, bg="#EDFAFD")
        self.field_pdb_name.grid(column=1, columnspan=1, pady=9, row=start_row_position + 1, sticky='SWE')

        self.label_connection_string = Label(self.window, text='Строка подключения к CDB')
        self.label_connection_string.grid(column=2,  pady=9, row=start_row_position + 1, sticky='SE')
        self.field_connection_string = Entry(self.window, width=WIDTH_SCHEMA_NAME_FIELD,
                                             textvariable=self.connection_string, bg="#EDFAFD")
        self.field_connection_string.grid(column=3, columnspan=3, pady=9, row=start_row_position + 1, sticky='SWE')

        self.label_data_pump_dir = Label(self.window, text='DATA_PUMP_DIR')
        self.label_data_pump_dir.grid(column=0, padx=PADX_LEFT_BORDER, row=start_row_position + 2, sticky='NE')
        self.label_data_pump_dir_content = Label(self.window, text=f'{self.remote_system_data_pump_dir.get()} -> {self.local_system_data_pump_dir.get()}')
        self.label_data_pump_dir_content.grid(column=1, columnspan=5, row=start_row_position + 2, sticky='NW')

        self.label_empty_string = Label(self.window, text='').grid(column=0, row=start_row_position + 3)


# Класс отображения элементов схем данных СУБД
class SchemeGUISuit:
    def __init__(self,
                 window,
                 scheme_id,
                 checked,
                 callback,
                 scheme_name=None,
                 scheme_password=None,
                 enabled=1,
                 dump_file='',
                 start_row_position=0):
        self.window = window
        self.scheme_id = scheme_id
        self.checked = checked
        self.callback = callback

        self.scheme_name = StringVar(value=scheme_name)
        self.scheme_password = StringVar(value=scheme_password)
        self.enabled = IntVar(value=enabled)
        self.scheme_name_dump_file = StringVar(value=dump_file)

        self.label_scheme_name = Label(self.window, text='Имя схемы', state=DISABLED)
        self.label_scheme_name.grid(column=0, row=start_row_position + 1, padx=PADX_LEFT_BORDER, sticky='E')
        self.field_scheme_name = Entry(self.window, width=WIDTH_SCHEMA_NAME_FIELD, textvariable=self.scheme_name,
                                       state=DISABLED)
        self.field_scheme_name.grid(column=1, row=start_row_position + 1, sticky='WE')
        self.field_scheme_password = Entry(self.window, show='*', width=WIDTH_SCHEMA_NAME_FIELD,
                                           textvariable=self.scheme_password, state=DISABLED)
        self.field_scheme_password.grid(column=2, row=start_row_position + 1, sticky='WE')

        self.checkbutton = Radiobutton(self.window, variable=self.checked, value=self.scheme_id, command=self.callback)
        self.checkbutton.grid(column=3, row=start_row_position + 1, padx=3, sticky='W')

        self.label_scheme_dump_file = Label(self.window, text='Файл для экспорта', state=DISABLED)
        self.label_scheme_dump_file.grid(column=4, row=start_row_position + 1, padx=3, sticky='E')
        self.field_scheme_dump_file = Entry(self.window, textvariable=self.scheme_name_dump_file,
                                                   width=WIDTH_SCHEMA_FILE_FIELD, state=DISABLED)
        self.field_scheme_dump_file.grid(column=5, row=start_row_position + 1, sticky='WE')

        self.label_1 = Label(self.window)
        self.label_1.grid(column=7, row=start_row_position + 1, sticky='W')
        self.label_2 = Label(self.window)
        self.label_2.grid(column=8, row=start_row_position + 1, sticky='W')
        self.label_3 = Label(self.window)
        self.label_3.grid(column=9, row=start_row_position + 1, sticky='W')

