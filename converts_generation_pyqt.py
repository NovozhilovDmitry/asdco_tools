import sys
import time
import xml.etree.ElementTree as Et
from zipfile import ZipFile
import random
import os
import shutil
from PyQt6.QtWidgets import (QMainWindow,
                             QWidget,
                             QLabel,
                             QGridLayout,
                             QApplication,
                             QPushButton,
                             QLineEdit,
                             QFileDialog,
                             QProgressBar)
from PyQt6.QtCore import QRunnable, QThreadPool


class Worker(QRunnable):
    def run(self):
        print('Начинается выполнение потока')
        # self.iteration_count = value (количество конвертов)
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
        self.get_directory_path.clicked.connect(self.get_directory)
        self.get_converts.clicked.connect(self.create_converts)
        self.converts.textChanged.connect(self.line_edit_signal)
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


    def name_for_ik(self):
        """
        :return: выдает имена формата ###-###-###-###-### в шестнадцатиричной системе для интеграционных конвертов
        """
        first_part = str(hex(random.randint(1000000000, 9999999999)))
        second_part = str(hex(random.randint(10000, 99999)))
        third_part = str(hex(random.randint(10000, 99999)))
        fourth_part = str(hex(random.randint(10000, 99999)))
        fifth_part = str(hex(random.randint(100000000000000, 999999999999999)))
        return f'{first_part[2:10]}-{second_part[2:6]}-{third_part[2:6]}-{fourth_part[2:6]}-{fifth_part[2:14]}'

    def atribute_generator(self, char_value):  # 17 символов для имени файла ED, 9 символов для номера договора
        """
        :param char_value: количество знаков в срезе
        :return: случайное число, которое зависит от системной даты и времени
        """
        a = str(int(time.time() * 10000000))
        return a[len(a) - char_value::]

    def envelope_change_attrib(self,
                               namespaceprefix,
                               namespaceuri,
                               xml_source_file_path,
                               tags,
                               paramreplace,
                               path_to_save_xml):
        """
        Изменение аттрибутов в файле Envelope
        :param namespaceprefix: префикс пространства имен в файле envelope (igr)
        :param namespaceuri: ссылка пространства имен в envelope
        :param xml_source_file_path: путь к файлу envelope
        :param tags: теги, по которым идет поиск
        :param paramreplace: словарь из параметров тегов и их новых значений
        :param path_to_save_xml: путь и имя для готового файла
        :return: запись в файл в том же каталоге
        """
        Et.register_namespace(namespaceprefix, namespaceuri)  # для записи в файле необходимо передать prefix и uri
        tree = Et.parse(xml_source_file_path)  # открываем xml файл и парсим
        root = tree.getroot()
        for tag in tags:
            for element in root.findall('.//*[@{' + namespaceuri + '}' + tag + ']'):  #
                for key, value in paramreplace.items():
                    if element.attrib['{' + namespaceuri + '}' + tag] in key:
                        if len(str(element.text).strip()) > 0:  # как сделать проверку на None
                            if element.text is None:
                                element.attrib['{' + namespaceuri + '}fileIdentity'] = value
                            else:
                                element.text = value
                        else:
                            element.attrib['{' + namespaceuri + '}fileIdentity'] = value
        tree.write(path_to_save_xml)

    def ed421_change_attrib(self,
                            namespaceprefix,
                            namespaceuri,
                            xml_source_file_path,
                            path_to_save_xml,
                            **kwargs):
        """
        Изменение аттрибутов в файле ED421
        :param namespaceprefix: префикс пространства имен в файле ED421 (пусто)
        :param namespaceuri: ссылка пространства имен в файле ED421
        :param xml_source_file_path: путь к файлу ED421
        :param path_to_save_xml: путь и имя для готового файла
        :param kwargs: аттрибуты тега и их новые значения
        :return:
        """
        Et.register_namespace(namespaceprefix, namespaceuri)
        tree = Et.parse(xml_source_file_path)
        root = tree.getroot()
        for key, value in kwargs.items():
            if root.findall(f'.[@{key}]'):  # поиск атрибута в корневом элементе
                root.attrib[key] = value
            elif root.findall(f'.//*[@{key}]'):  # поиск атрибута в дочерних элементах
                root.find(f'.//*[@{key}]').set(key, value)
        tree.write(path_to_save_xml)  # сохранение xml файла

    def routeinfo_change_attrib(self,
                                namespaceprefix,
                                namespaceuri,
                                xml_source_file_path,
                                path_to_save_xml,
                                new_text):
        """
        Редактирование RouteInfo
        :param namespaceprefix: префикс пространства имен в файле ED421 (igr)
        :param namespaceuri: ссылка пространства имен в файле ED421
        :param xml_source_file_path: путь к файлу
        :param path_to_save_xml: путь и имя для готового файла
        :param new_text: текст, который будет записан между тегами
        :return: запись в xml-файл
        """
        Et.register_namespace(namespaceprefix, namespaceuri)

        tree = Et.parse(xml_source_file_path)
        root = tree.getroot()
        root.find('{' + namespaceuri + '}DocumentPackID').text = new_text
        tree.write(path_to_save_xml)  # сохранение xml файла

    def create_new_directory(self, path_to_new_directory, directory_name):
        """
        :param path_to_new_directory: путь, где будет создан каталог path
        :param directory_name: имя для нового каталога
        :return: создает каталог temp по указанному пути, если его не существует
        """
        if os.path.exists(path_to_new_directory + '/' + directory_name):
            pass
        else:
            os.mkdir(path_to_new_directory + '/' + directory_name)
        return path_to_new_directory + '/' + directory_name + '/'

    def get_arhive(self, path, *files):
        """
        :param path: путь, где будет создать архив
        :param files: файлы, которые будут помещаться в архив
        :return:
        """
        with ZipFile(path, 'w') as new_zip:  # добавить после path функцию вызова нового имени
            for arg in files:
                filename = arg[str(arg).rfind('/') + 1:]
                new_zip.write(arg, arcname=str(filename))
                os.remove(arg)

    def move_files(self, copy_from, copy_to):
        """
        :param copy_from: полный путь к файлу, который будет перемещен
        :param copy_to: каталог, в который будет перемещен файл
        :return: перемещает файл, переданный из copy_from в каталог copy_to
        """
        shutil.move(copy_from, copy_to)

    def get_directory(self):
        self.start_path = QFileDialog.getExistingDirectory(self, caption='Выбрать файл', directory='C:/')
        self.directory_path.setText(self.start_path)

    def line_edit_signal(self, value):
        if self.converts.text() == '':
            self.get_converts.setEnabled(False)
        else:
            self.get_converts.setEnabled(True)
            self.iteration_count = value

    def create_converts(self):
        print(Window.name_for_ik(self))
        # temp_path = Window.create_new_directory(self.start_path, 'temp')
        # convert_path = Window.create_new_directory(self.start_path, 'converts')
        prefix_for_routeinfo_envelope = 'igr'
        prefix_ed421 = ''
        uri_for_routeinfo_envelope = 'http://www.cbr.ru/igr/'
        uri_for_ed421 = 'urn:cbr-ru:elk:v2021.1.0'
        text_for_sign_file = 'test signature file'
        tags_attrib = ['name', 'fileType']
        print('передаем в потом')
        worker = Worker()
        self.threadpool.start(worker)


app = QApplication(sys.argv)
style = """
        QMainWindow {
            background-color: #fff;
        }
        QProgressBar {
            border: 1px solid grey;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #05B8CC;
            width: 20px;
        }
        """
app.setStyleSheet(style)
win = Window()
win.show()
sys.exit(app.exec())
