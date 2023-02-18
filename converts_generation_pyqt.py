import sys
from PyQt6.QtWidgets import (QMainWindow,
                             QWidget,
                             QLabel,
                             QGridLayout,
                             QApplication,
                             QPushButton,
                             QLineEdit,
                             QProgressBar)
from PyQt6.QtCore import QRunnable, QThreadPool


class Worker(QRunnable):
    def run(self):
        print('Начинается выполнение потока')
        print('Выполнение потока завершено')


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Генератор конвертов")  # заголовок главного окна
        self.setFixedSize(400, 150)  # начальные размеры главного окна
        self.get_directory_path = QPushButton('Выбор каталога', self)
        self.get_converts = QPushButton('Создать конверты', self)
        self.iteration_label = QLabel()
        self.date_label = QLabel()
        self.directory_path = QLineEdit()
        self.converts = QLineEdit()
        self.input_date = QLineEdit()
        self.progressbar = QProgressBar()
        # self.get_directory_path.clicked.connect('какая-то функция')
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.get_directory_path, 0, 0)
        grid_layout.addWidget(self.directory_path, 0, 1)
        grid_layout.addWidget(self.iteration_label, 1, 0)
        grid_layout.addWidget(self.converts, 1, 1)
        grid_layout.addWidget(self.date_label, 2, 0)
        grid_layout.addWidget(self.input_date, 2, 1)
        grid_layout.addWidget(self.get_converts, 3, 0, 1, 2)
        grid_layout.addWidget(self.progressbar, 4, 0, 1, 2)
        widget = QWidget()
        widget.setLayout(grid_layout)
        self.setCentralWidget(widget)
        self.iteration_label.setText('Количество конвертов')
        self.date_label.setText('Введите дату')
        self.get_converts.setEnabled(False)
        self.get_directory_path.setToolTip('Кнопка вызова диалогового окна для выбора каталога')
        self.directory_path.setToolTip('Можно вставить путь или выбрать с помощью кнопки')
        self.converts.setToolTip('Количество необходимых конвертов')
        self.get_converts.setToolTip('Введите количество необходимых конвертов')
        self.input_date.setToolTip('Дата должна быть не ранее текущего ОД')
        self.threadpool = QThreadPool()
        self.iteration_label = ''
        self.iteration_count = ''
        self.start_path = 'C:/install'
        self.envelope_path = self.start_path + '/sample/envelope.xml'
        self.routeinfo_path = self.start_path + '/sample/RouteInfo.xml'
        self.ed421_path = self.start_path + '/sample/ED421.xml'
        self.directory_path.setText(self.start_path)


app = QApplication(sys.argv)
style = """QMainWindow {background-color: #fff;}"""
app.setStyleSheet(style)
win = Window()
win.show()
sys.exit(app.exec())
