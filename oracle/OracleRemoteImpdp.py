from tkinter import *

from .OracleImpdp import OracleImpdp
from additions import MAIN_WINDOW_TITLE

WINDOW_TITLE = 'Oracle (remote). Импорт схем (data pump)'
WINDOW_GEOMETRY = r'1350x920'
WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 40
PADX_LEFT_BORDER = 15
NUMBER_ROWS = 10
INTERVAL = .01
PROGRESSBAR_START_INTERVAL = 1


# Основной класс отображения всех элементов окна для выполнения импорта в remote СУБД
class OracleRemoteImpdp(OracleImpdp):
    def __init__(self, parent, loop, config_file):
        super().__init__(parent, loop, config_file)
        self.window.title(f"{MAIN_WINDOW_TITLE}: {WINDOW_TITLE}")
        self.window.geometry(WINDOW_GEOMETRY)
        self.asdco_menu = Menu(self.main_menu, tearoff=0)
        self.pdb_menu = Menu(self.main_menu, tearoff=0)

    def create_menu(self):
        self.window.config(menu=self.main_menu)
        self.config_menu.add_command(label='Показать существующие схемы', command=self.show_shemes)
        self.config_menu.add_separator()
        self.config_menu.add_command(label='Сохранить текущие настройки', command=self._save_current_config)
        self.main_menu.add_cascade(label='Конфигурация', menu=self.config_menu)
        self.asdco_menu.add_command(label='Предоставление привилегий и компиляция объектов схем(ы)',
                                    command=self.enabled_schemes_options)
        self.main_menu.insert_cascade(0, label='АС ДКО', menu=self.asdco_menu)
        self.pdb_menu.add_command(label='Показать существующие PDB', command=self.show_pdbs)
        self.main_menu.insert_cascade(0, label='PDB', menu=self.pdb_menu)


if __name__ == '__main__':
    pass