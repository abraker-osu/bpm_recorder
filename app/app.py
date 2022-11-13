import json
import os
import sys
import time
import numpy as np
import traceback

from PyQt5 import QtCore
from PyQt5 import QtWidgets


"""
Set numpy settings
"""
np.set_printoptions(suppress=True)


"""
Override default exception hook
"""
sys._excepthook = sys.excepthook
def exception_hook(exctype, value, tb):
    sys.__excepthook = (exctype, value, tb)
    print(''.join(traceback.format_exception(exctype, value, tb)))

    # Log assertion errors, but don't exit because of them
    if exctype == AssertionError:
        return

    #score_data_obj.save_data_and_close()
    #diff_data_obj.save_data_and_close()
    sys.exit(1)

sys.excepthook = exception_hook


"""
Main app class
"""
class App(QtWidgets.QMainWindow):

    IDX_TIME = 0
    IDX_KEY  = 1

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.pressed = set()
        self.is_recording = False
        self.start_time = None

        self.data_raw = []
        self.data_bpm = []

        self.setWindowTitle('BPM Recorder')

        self.bpm_display = QtWidgets.QLabel('')

        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.clicked.connect(self.__start_recording)
        self.start_button.setToolTip('Starts BPM recording')

        self.stop_button = QtWidgets.QPushButton('Stop')
        self.stop_button.clicked.connect(self.__stop_recording)
        self.stop_button.setToolTip('Stops BPM recording')

        self.status_text = QtWidgets.QLabel()

        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)

        self.btn__layout = QtWidgets.QHBoxLayout()
        self.btn__layout.addWidget(self.start_button)
        self.btn__layout.addWidget(self.stop_button)

        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.addWidget(self.bpm_display)
        self.main_layout.addLayout(self.btn__layout)
        self.main_layout.addWidget(self.status_text)

        self.show()


    def __start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.start_time = time.perf_counter()
        
        self.data_raw = []
        self.data_bpm = []

        self.status_text.setText('Recording')
        self.bpm_display.setText(f'0 Taps/s\n0 BPM')


    def __stop_recording(self):
        self.is_recording = False

        self.status_text.setText('')
        self.__export_data()


    def __export_data(self):
        os.makedirs('data', exist_ok=True)
        np.savetxt(f'data/{time.time():.0f}.csv', np.asarray(self.data_bpm), delimiter=',', fmt='%i %i %.2f %i')


    def __record_data_point(self, key):
        curr_time = time.perf_counter()
        self.data_raw.append([ curr_time, key ])
        
        data = np.asarray(self.data_raw)
        data = np.diff(data[:, App.IDX_TIME])

        n = 10
        avg = np.mean(data[-n:-1])

        self.data_bpm.append([ len(self.data_bpm), 1000*(curr_time - self.start_time), 15 / avg, key ])
        self.bpm_display.setText(f'{(1 / avg):.1f} Taps/s\n{(15 / avg):.0f} BPM')


    def keyReleaseEvent(self, event):
        QtWidgets.QMainWindow.keyReleaseEvent(self, event)

        if event.key() == QtCore.Qt.Key.Key_Escape:
            event.accept()
            return

        if not event.isAutoRepeat():
            self.pressed.remove(event.key())

        event.accept()


    def keyPressEvent(self, event):
        QtWidgets.QMainWindow.keyPressEvent(self, event)

        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.__stop_recording()
            self.pressed.clear()
            
            event.accept()
            return

        self.__start_recording()

        if event.key() not in self.pressed:
            self.pressed.add(event.key())
            self.__record_data_point(event.key())
        
        event.accept()


    def closeEvent(self, event):
        event.accept()
