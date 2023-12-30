from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt, QProcess, QObject, pyqtSignal, pyqtSlot, QRunnable, QAbstractListModel
from PyQt6.QtWidgets import QStyledItemDelegate, QMessageBox, QWidget, QPushButton, QGridLayout, QLineEdit, QLabel
import traceback
import uuid
import re
import sys


DEFAULT_STATE = {
    "progress": 0,
    "status": QProcess.ProcessState.Starting,
}


class JobManager(QAbstractListModel):
    _jobs = {}
    _state = {}
    _parsers = {}
    status = pyqtSignal(str)
    result = pyqtSignal(str, object)
    progress = pyqtSignal(str, int)
    finish = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.p = None
        self.progress.connect(self.handle_progress)

    def execute(self, command, parsers=None):
        job_id = uuid.uuid4().hex

        def fwd_signal(target):
            return lambda *args: target(job_id, *args)

        self._parsers[job_id] = parsers or []
        self._state[job_id] = DEFAULT_STATE.copy()
        self.p = QProcess()
        self.p.readyReadStandardOutput.connect(fwd_signal(self.handle_output))
        self.p.readyReadStandardError.connect(fwd_signal(self.handle_output))
        self.p.stateChanged.connect(fwd_signal(self.handle_state))
        self.p.finished.connect(fwd_signal(self.done))
        self._jobs[job_id] = self.p
        self.p.startCommand(command)
        self.layoutChanged.emit()

    def handle_output(self, job_id):
        p = self._jobs[job_id]
        try:
            stderr = bytes(p.readAllStandardError()).decode("utf8")
            stdout = bytes(p.readAllStandardOutput()).decode("utf8")
        except:
            stderr = bytes(p.readAllStandardError()).decode("cp1251")
            stdout = bytes(p.readAllStandardOutput()).decode("cp1251")
        output = stderr + stdout
        parsers = self._parsers.get(job_id)
        for parser, signal_name in parsers:
            result = parser(output)
            data = result.strip()
            find_ora_error = re.compile("ORA-\d{1,5}:")
            searching_in_stdout = find_ora_error.search(data)
            try:
                start = data.find(searching_in_stdout.group(0))
                self.message_error = data.strip()[start:]
                self.p.kill()
            except:
                signal = getattr(self, signal_name)
                signal.emit(job_id, result)

    def handle_progress(self, job_id, progress):
        self._state[job_id]["progress"] = progress
        self.layoutChanged.emit()

    def handle_state(self, job_id, state):
        self._state[job_id]["status"] = state
        self.layoutChanged.emit()

    def done(self, job_id, exit_code, exit_status):
        del self._jobs[job_id]
        del self._state[job_id]
        if exit_code == 0:
            self.finish.emit(exit_code, str(exit_status))
        else:
            self.finish.emit(exit_code, self.message_error)
        self.layoutChanged.emit()

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            job_ids = list(self._state.keys())
            job_id = job_ids[index.row()]
            return job_id, self._state[job_id]

    def rowCount(self, index):
        return len(self._state)


class WorkerSignals(QObject):
    finish = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:  # выполняем переданный из window метод
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:  # если ошибок не было, то формируем сигнал .result и передаем результат
            self.signals.result.emit(result)  # Вернуть результат обработки
        finally:
            self.signals.finish.emit()  # Готово


class InitialDelegate(QStyledItemDelegate):
    def __init__(self, decimals, parent=None):
        super().__init__(parent)
        self.nDecimals = decimals

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        try:
            text = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            number = int(text)
            option.text = "{:,d}".format(number, self.nDecimals).replace(',', ' ')
        except:
            pass

    def paint(self, painter, option, index):
        if index.data() == 'READONLY' or index.data() == 'MOUNTED':
            option.palette.setColor(QPalette.ColorRole.Text, QColor('red'))
        QStyledItemDelegate.paint(self, painter, option, index)


class MessageWindows(QMessageBox):
    def __init__(self):
        super().__init__()
        self.dlg = QMessageBox()

    def msg_window(self, text):
        """
        :return: вызов диалогового окна с ошибками
        """
        dialog_window = self.dlg
        dialog_window.setWindowTitle('ОШИБКА')
        dialog_window.setText(text)
        dialog_window.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog_window.setIcon(QMessageBox.Icon.Warning)
        dialog_window.exec()

    def msg_accept_delete_pdb(self, pdb_name):
        """
        :param pdb_name: имя PDB
        :return: вызов диалогового окна с выбором да/нет для удаления PDB
        """
        dialog_window = self.dlg
        dialog_window.setWindowTitle('Удаление PDB')
        dialog_window.setText(f'Вы действительно хотите удалить "{pdb_name}?"')
        dialog_window.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog_window.setIcon(QMessageBox.Icon.Question)
        result = dialog_window.exec()
        if result == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False


class SecondWindow(QWidget):
    def __init__(self):
        super(SecondWindow, self).__init__()
        self.setWindowTitle('Клонирование PDB')
        self.setMinimumSize(550, 150)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        current_pdb_name = QLabel('Имя исходной PDB')
        new_pdb_name = QLabel('Новое имя PDB')
        self.input_pdb_name = QLineEdit()
        self.input_new_pdb_name = QLineEdit()
        self.input_new_pdb_name.setMaxLength(21)
        self.btn_clone_pdb = QPushButton('Клонирование PDB')
        self.btn_clone_pdb.clicked.connect(self.clone_pdb)
        self.btn_clone_pdb.setStyleSheet('width: 250')
        self.btn_snapshot_pdb = QPushButton('Сделать snapshot')
        self.btn_snapshot_pdb.clicked.connect(self.clone_pdb)
        self.btn_snapshot_pdb.setStyleSheet('width: 250')
        self.layout.addWidget(current_pdb_name, 0, 0)
        self.layout.addWidget(self.input_pdb_name, 0, 1)
        self.layout.addWidget(new_pdb_name, 1, 0)
        self.layout.addWidget(self.input_new_pdb_name, 1, 1)
        self.layout.addWidget(self.btn_clone_pdb, 2, 0)
        self.layout.addWidget(self.btn_snapshot_pdb, 2, 1)

    def set_name(self, pdb_name):
        """
        :param pdb_name: имя PDB, которое передается из главного окна
        :return: в поле "Исходное имя PDB" устанавливается значение исходного имени из основного окна
        """
        self.input_pdb_name.setText(pdb_name)

    def clone_pdb(self):
        """
        :return: передаем из второстепенного окна значение полей исходного имени и нового имени PDB
        """
        pdb_name = self.input_pdb_name.text()
        new_pdb_name = self.input_new_pdb_name.text()
        return [pdb_name, new_pdb_name]


if __name__ == '__main__':
    pass
