import os
import sys
import time
import numpy as np
import traceback

import pyqtgraph

from PyQt5 import QtCore
from PyQt5 import QtGui
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

    # `NUM_AVG` has to be an even amount or otherwise
    # averaged two-finger tapping data can be
    # assymetrical.
    # 
    # Ex: 
    #   odd:  [1, 0.5, 1]      -> [0.5, 1, 0.5]
    #   even: [1, 0.5, 1, 0.5] -> [0.5, 1, 0.5, 1]
    #
    # Odds produce varying average as data gets shifted in
    # and out, evens produce consistent data
    NUM_AVG  = 10

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.pressed = set()

        self.is_recording = False
        self.is_ready_to_record = False
        
        self.start_time = None

        self.data_raw = []
        self.data_bpm = []

        self.setWindowTitle('BPM Recorder')

        self.bpm_display = QtWidgets.QLabel(f'Taps/s: -\nBPM:    -\n# Taps: -')
        self.bpm_display.setStyleSheet('QLabel { font-size: 10pt; font-family: Consolas; }')

        self.graph_display = pyqtgraph.PlotWidget(title='Time vs BPM')
        self.graph_display.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graph_display.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graph_display.setLabel('left', 'BPM avg 10 data points', units='BPM', unitPrefix='')
        self.graph_display.setLabel('bottom', 'Time', units='ms', unitPrefix='')

        self.plot = self.graph_display.plot()

        self.num_press_setting_label = QtWidgets.QLabel('Num presses to record:')
        self.num_press_setting = QtWidgets.QLineEdit()

        self.num_press_setting_label.setStyleSheet('QLabel { font-size: 10pt; }')
        self.num_press_setting.setStyleSheet('QLabel { font-size: 10pt; }')
        self.num_press_setting.setValidator(QtGui.QIntValidator(App.NUM_AVG, 10000, self))

        self.status_text = QtWidgets.QLabel('Click on the plot then any key  to prepare for a new recording')

        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)

        self.setting__layout = QtWidgets.QHBoxLayout()
        self.setting__layout.addWidget(self.num_press_setting_label)
        self.setting__layout.addWidget(self.num_press_setting)
        self.setting__layout.setContentsMargins(0, 0, 0, 10)

        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.addWidget(self.bpm_display)
        self.main_layout.addWidget(self.graph_display)
        self.main_layout.addLayout(self.setting__layout)
        self.main_layout.addWidget(self.status_text)

        self.show()


    def __start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.start_time = time.perf_counter()
        
        self.data_raw = []
        self.data_bpm = []

        self.status_text.setText('Recording (Press Esc to stop)')
        self.bpm_display.setText(f'Taps/s: -\nBPM:    -\n# Taps: 0')


    def __prepare_recording(self):
        self.is_ready_to_record = True
        self.status_text.setText('Start pressing keys to record')
        self.num_press_setting.setEnabled(False)
        

    def __stop_recording(self):
        self.is_recording = False
        self.is_ready_to_record = False

        self.status_text.setText('Click on the plot then any key to prepare for a new recording')
        self.num_press_setting.setEnabled(True)

        self.__export_data()


    def __export_data(self):
        if len(self.data_bpm) > 0:
            os.makedirs('data', exist_ok=True)
            np.savetxt(f'data/{time.time():.0f}.csv', np.asarray(self.data_bpm), delimiter=',', fmt='%i %i %.2f %i', header='tap, ms, bpm, key')


    def __record_data_point(self, key):
        curr_time = time.perf_counter()
        self.data_raw.append([ curr_time, key ])

        num_taps = len(self.data_raw)
        
        data = np.asarray(self.data_raw)
        data = np.diff(data[:, App.IDX_TIME])

        if num_taps < 3:
            self.bpm_display.setText(f'Taps/s: -\nBPM:    -\n# Taps: {num_taps}')
            return
            
        avg = np.mean(data[-App.NUM_AVG - 1:-1])

        self.data_bpm.append([ len(self.data_bpm), 1000*(curr_time - self.start_time), 15 / avg, key ])
        self.bpm_display.setText(f'Taps/s: {(1 / avg):.1f}\nBPM:    {(15 / avg):.0f}\n# Taps: {num_taps}')

        data = np.asarray(self.data_bpm)
        self.plot.setData(data[:, 1], data[:, 2], pen=(0, 255, 0, 150))

        try: num_presses_to_record = int(self.num_press_setting.text())
        except ValueError:
            num_presses_to_record = 0
            
        if num_presses_to_record != 0:
            if num_taps >= num_presses_to_record:
                self.__stop_recording()


    def keyReleaseEvent(self, event):
        QtWidgets.QMainWindow.keyReleaseEvent(self, event)

        if event.key() == QtCore.Qt.Key.Key_Escape:
            event.accept()
            return

        if self.is_recording:
            if not event.isAutoRepeat():
                self.pressed.remove(event.key())

        event.accept()


    def keyPressEvent(self, event):
        QtWidgets.QMainWindow.keyPressEvent(self, event)

        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.is_recording:
                self.__stop_recording()
        #     else:
        #         self.__prepare_recording()
        #         self.__start_recording()
            
            event.accept()
            return
    
        if self.is_recording:
            if event.key() not in self.pressed:
                self.__record_data_point(event.key())
        else:
            self.__prepare_recording()
            self.__start_recording()
    
        self.pressed.add(event.key())
        event.accept()


    def closeEvent(self, event):
        event.accept()
