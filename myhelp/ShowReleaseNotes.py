from tkinter import *
from tkinter import scrolledtext

from myLogging import logger
from additions import MAIN_WINDOW_TITLE, load_release_notes

WINDOW_TITLE = 'Show Release notes'
WINDOW_GEOMETRY = r'1200x900'
WIDTH_SCHEMA_NAME_FIELD = 18
WIDTH_SCHEMA_FILE_FIELD = 40
PADX_LEFT_BORDER = 15
NUMBER_ROWS = 10
INTERVAL = .01


# Основной класс отображения Release notes
class ShowReleaseNotes(Frame):
    def __init__(self, parent, loop):
        Frame.__init__(self, parent)
        self.window = parent
        self.loop = loop

        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        self.window.grab_set()
        self.window.focus()
        self.window.title(f"{MAIN_WINDOW_TITLE}: {WINDOW_TITLE}")
        self.window.geometry(WINDOW_GEOMETRY)
        self.text = load_release_notes()

        self.result_scrolledtext = scrolledtext.ScrolledText(self.window, width=140, height=54, wrap=WORD)
        self.result_scrolledtext.grid(column=0, columnspan=10, padx=PADX_LEFT_BORDER, pady=9, row=2, sticky='WE')
        self.result_scrolledtext.insert(END, self.text)
        self.result_scrolledtext.see()

    def close_window(self):
        logger.info('Close the ShowReleaseNotes window.')
        self.window.destroy()


if __name__ == '__main__':
    pass
