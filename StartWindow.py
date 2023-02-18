from tkinter import *

from additions import MAIN_WINDOW_TITLE, VERSION, load_config, dump_config

WINDOW_GEOMETRY = r'1000x600'
WINDOW_TITLE = VERSION
WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 80


class WindowMain(Frame):
    def __init__(self, parent, loop, main_menu):
        Frame.__init__(self, parent)
        self.window = parent
        self.loop = loop
        self.window.title(f"{MAIN_WINDOW_TITLE}: {WINDOW_TITLE}")
        self.window.geometry(WINDOW_GEOMETRY)
        self.config_menu = Menu(main_menu, tearoff=0)


if __name__ == '__main__':
    pass
