#!/usr/bin/env python
__author__ = 'Stefan+Omar'
import sys
import os
import numpy as np

import threading
import queue
import time
import collections

from matplotlib import cm
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
#import coloredGraph
import AFE4900EVM_driver
import AFEregisters
import analysis
import pandas as pd

class GuiViewer(QtGui.QWidget):

    def __init__(self):
        super(GuiViewer, self).__init__()

        self.initUI()

    def initUI(self):

        self.fs = 250
        self.low_cut = 0.5
        self.high_cut = 30
        self.order  = 4
        self.pt = 175
        self.st= -0.25

        # self.led1_chart = pg.GraphicsWindow(title="LED1 data")
        # self.led1_chart.resize(1200,80)
        # self.led1_line = self.led1_chart.addPlot()
        # self.led1_curve = self.led1_line.plot()
        # self.led1_data = []

        # self.led2_chart = pg.GraphicsWindow(title="LED2 data")
        # self.led2_chart.resize(1200,80)
        # self.led2_line = self.led2_chart.addPlot()
        # self.led2_curve = self.led2_line.plot()
        # self.led2_data = []

        self.led3_chart = pg.GraphicsWindow(title="LED3 data")
        self.led3_chart.resize(1200,80)
        self.led3_line = self.led3_chart.addPlot()
        self.led3_curve = self.led3_line.plot()
        self.led3_data = []

        # self.led4_chart = pg.GraphicsWindow(title="LED4 data")
        # self.led4_chart.resize(1200,80)
        # self.led4_line = self.led4_chart.addPlot()
        # self.led4_curve = self.led4_line.plot()
        # self.led4_data = []

        self.ppg_sr = 250
        self.ppg_duration = 3.0
        self.ppg_len = int(self.ppg_sr * self.ppg_duration)
        self.j_ppg = 0
        self.ppg_x = np.arange(0, self.ppg_duration, 1/self.ppg_sr)
        print("ppg_len : ",self.ppg_len)
        # self.led1_data = [0] * self.ppg_len
        # self.led2_data = [0] * self.ppg_len
        self.led3_data = [0] * self.ppg_len
        # self.led4_data = [0] * self.ppg_len

        self.skew_3_1 = QtGui.QLabel("Window Skewness")
        self.skew_3_1.setAlignment(QtCore.Qt.AlignCenter)
        self.skew_3_2 = QtGui.QLabel("--")
        self.skew_3_2.setAlignment(QtCore.Qt.AlignCenter)

        self.msq_3_1 = QtGui.QLabel("Window MSQ")
        self.msq_3_1.setAlignment(QtCore.Qt.AlignCenter)
        self.msq_3_2 = QtGui.QLabel("--")
        self.msq_3_2.setAlignment(QtCore.Qt.AlignCenter)



        self.btn1 = QtGui.QPushButton("Start data read")
        self.btn2 = QtGui.QPushButton("Stop data read")
        # self.txtbox = QtGui.QLineEdit(self)
        # self.txtbox.resize(280,40)
        # self.txtbox.setText("Default")
        self.btn3 = QtGui.QPushButton("Analyse")
        self.btn4 = QtGui.QPushButton("Clear all")

        self.dropdown = QtGui.QComboBox(self)
        self.dropdown.addItem("OFF")
        self.dropdown.addItem("SFH7072")
        self.dropdown.addItem("SFH7050")
        self.dropdown.addItem("Custom Board")
        self.dropdown.activated[str].connect(self.boardChoice)

        self.btn1.clicked.connect(self.btn1Pres)
        self.btn2.clicked.connect(self.btn2Pres)
        self.btn3.clicked.connect(self.btn3Pres)
        self.btn4.clicked.connect(self.btn4Pres)

        self.configlbl = QtGui.QLabel("Sensor Configuration")
        self.filelbl = QtGui.QLabel("File Name")

        # self.led1Lbl = QtGui.QLabel('LED1')
        # self.led2Lbl = QtGui.QLabel('LED2')
        self.led3Lbl = QtGui.QLabel('LED3')
        # self.led4Lbl = QtGui.QLabel('LED4')

        self.GUI_queue = queue.Queue()
        self.Analysis_queue = queue.Queue()
        self.Skewness_queue = queue.Queue()
        self.MSQ_queue = queue.Queue()
        self.boardHandle = AFE4900EVM_driver.AFEBoard("/dev/tty.usbmodem14101")
        self.boardHandle.set_LED_currents((1,0),(1,0),(1,0),(1,0),0)
        #self.boardHandle = AFE4900EVM_driver.AFEBoard("/dev/tty.usb0")
        self.dataThread = Board_Read_Thread(self.boardHandle, self.GUI_queue,self.Analysis_queue)
        print("Entering Thread")
        self.AnalyseThread = Data_Analyse_Thread(self.Analysis_queue,self.Skewness_queue,self.MSQ_queue,self.fs,self.low_cut,self.high_cut,self.order)
        print("exiting thread")

        self.coefficients=[[ 0.86748371, -1.27669843],[-0.26330752,  2.02026498],[-0.36095814, -1.97291746]]
        self.intercepts=[-0.12581411, -1.02240841,  0.86276226]

        #Initialise temporary array to store data before every read
        self.tmpData=[]
        self.first_start=True
        self.started=False
        self.stop=True

        #self.imv = pg.ImageView()

        grid = QtGui.QGridLayout()
        grid.setSpacing(5)

        # grid.addWidget(self.led1Lbl, 0, 0)
        # grid.addWidget(self.led1_chart, 1, 0, 4, 5)
        # grid.addWidget(self.led2Lbl, 5, 0)
        # grid.addWidget(self.led2_chart, 6, 0, 4, 5)
        grid.addWidget(self.led3Lbl, 10, 0)
        grid.addWidget(self.led3_chart, 11, 0, 4, 5)
        # grid.addWidget(self.led4Lbl, 15, 0)
        # grid.addWidget(self.led4_chart, 16, 0, 4, 5)

        grid.addWidget(self.skew_3_1,11,5,1,1)
        grid.addWidget(self.skew_3_2,12,5,1,1)
        grid.addWidget(self.msq_3_1,13,5,1,1)
        grid.addWidget(self.msq_3_2,14,5,1,1)


        grid.addWidget(self.configlbl,20,0,1,1)
        # grid.addWidget(self.filelbl,20,3,1,1)

        grid.addWidget(self.dropdown,21,0,1,1)
        grid.addWidget(self.btn1, 21, 1, 1, 1)
        grid.addWidget(self.btn2, 21, 2, 1, 1)
        # grid.addWidget(self.txtbox, 21, 3, 1, 1)
        grid.addWidget(self.btn3, 21, 3, 1, 1)
        grid.addWidget(self.btn4, 21, 4, 1, 1)

        self.setLayout(grid)

        self.setGeometry(200, 200, 1200, 800)
        self.setWindowTitle('AFE4900 data viewer')
        #
        # self.show()

    def boardChoice(self, text):
        if(text=="OFF"):
            self.boardHandle.set_LED_currents((1,0),(1,0),(1,0),(1,0),0)
        else:
            self.boardHandle.set_250Hz_timing("SFH7072")
            self.boardHandle.set_LED_currents((1,4.692), (1,4.692), (1,4.692), (0,0), 1)
            self.boardHandle.set_BW_early_DAC(0, 1)
            self.boardHandle.set_feedback_gains(1, [(3, 0)])
            self.boardHandle.set_dc_current_offset(2,[(1, 95, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)])
            # set current and offset settings here from driver :
            # self.boardHandle.setSensor(text)
            # self.boardHandle.set_250Hz_timing(text)

    def btn1Pres(self):
        print("Button1 press")
        if self.dropdown.currentText() != "OFF":
            if self.first_start:
                self.first_start=False
                self.dataThread.start()
                self.AnalyseThread.start()
            else:
                self.ppg_x = np.arange(0, self.ppg_duration, 1/self.ppg_sr)
                self.dataThread = Board_Read_Thread(self.boardHandle, self.GUI_queue,self.Analysis_queue)
                print("Entering Thread")
                self.AnalyseThread = Data_Analyse_Thread(self.Analysis_queue,self.Skewness_queue,self.MSQ_queue,self.fs,self.cutoff,self.order)
                self.dataThread.start()
                self.AnalyseThread.start()

            self.started=True
            self.stop=False
            #board.set_250Hz_timing('Default')
            self.pollGUI_queue()
            # time.sleep(1)
            print("Started Reading")
        else:
            print("Sensor off please select sensor configuration")

    def btn2Pres(self):
        print("Button2 press")
        if self.started:
            self.dataThread.stop()
            self.AnalyseThread.stop()
            print("Thread stop executed fully")
            # self.dataThread.join()
            qsize = self.GUI_queue.qsize()
            for i in range(qsize):
                ledsData = self.GUI_queue.get()
                self.tmpData.extend(ledsData)

            self.started=False
            print("Thread stopped")
            self.stop = True
            self.Data=np.array(self.tmpData)
            self.l = self.Data.shape[0]
            print("Shape of Data: ",self.Data.shape)
            print("ds length: ",self.l)
            print("self.fs: ",self.fs)
            print("changing view")
            self.ppg_x = np.arange(0, self.l/self.fs, 1/self.fs)
            self.led3_curve.setData(self.ppg_x,self.Data[:,1])
            # self.parent().parent().upload_screen.update_Graph(ds,self.fs,self.l)
            # self.parent().setCurrentWidget(self.parent().parent().upload_screen)

    # def stop_data_read(self):
    #     print("display data")
    #     print("bool: ",self.view.started)
    #     if self.view.started:
    #         self.view.dataThread.stop()
    #         self.view.AnalyseThread.stop()
    #         print("Thread stop executed fully")
    #         self.view.dataThread.join()
    #         self.view.started=False
    #         print("Thread stopped")
    #         self.view.stop = True
    #         ds = pd.DataSeries(self.view.tmpData)
    #         self.l = ds.shape[0]
    #         self.view = AnalyseViewer(ds , sr, l)
    #         self.setCentralWidget(self.view)
    #         print("Done")
    #

    def btn3Pres(self):
        print("Analyse pressed")
        if self.stop and len(self.tmpData) > 0:
            ds = pd.Series(self.Data[:,1])
            self.parent().parent().upload_screen.update_Graph(ds,self.fs,self.l)
            self.parent().setCurrentWidget(self.parent().parent().upload_screen)

            print("begin analysing")

    def btn4Pres(self):
        print("Button4 press")
        self.tmpData=[]
        self.ppg_x = np.arange(0, self.ppg_duration, 1/self.ppg_sr)
        # self.led1_curve.setData(self.ppg_x, [0] * self.ppg_len)
        # self.led2_curve.setData(self.ppg_x, [0] * self.ppg_len)
        self.led3_data=[0] * self.ppg_len
        self.led3_curve.setData(self.ppg_x, [0] * self.ppg_len)
        # self.led4_curve.setData(self.ppg_x, [0] * self.ppg_len)
        print("Cleared Sucessfully")

    def pollGUI_queue(self):
        if self.started==True:
            if not self.GUI_queue.empty():
                #print("queue not empty")
                len = 10 #set to nymber of samples but should be a variable
                ledsData = self.GUI_queue.get()
                # print(ledsData.size)
                self.tmpData.extend(ledsData)

                # self.led1_data[self.j_ppg: self.j_ppg + len] = ledsData[:,2]
                # self.led1_curve.setData(self.ppg_x, self.led1_data)
                # #self.led1_curve.plot(pen='#418934')
                #
                # self.led2_data[self.j_ppg: self.j_ppg + len] = ledsData[:,0]
                # self.led2_curve.setData(self.ppg_x, self.led2_data)
                # #self.led2_curve.plot(pen='#418934')

                self.led3_data[self.j_ppg: self.j_ppg + len] = ledsData[:,1]
                self.led3_curve.setData(self.ppg_x, self.led3_data)
                #self.led3_curve.plot(pen='#418934')

                # self.led4_data[self.j_ppg: self.j_ppg + len] = ledsData[:,3]
                # self.led4_curve.setData(self.ppg_x, self.led4_data)
                #self.led4_curve.plot(pen='#418934')
                self.j_ppg += len
                # print(self.j_ppg)
                if(self.j_ppg == self.ppg_len):
                    self.j_ppg=0

                # self.led1_data.extend(ledsData[:,2])
                # self.led1_curve.setData(self.led1_data)
                # self.led2_data.extend(ledsData[:,0])
                # self.led2_curve.setData(self.led2_data)
                # self.led3_data.extend(ledsData[:,1])
                # self.led3_curve.setData(self.led3_data)
                # self.led4_data.extend(ledsData[:,3])
                # self.led4_curve.setData(self.led4_data)

                #print(ledsData[:,0])
                #print(self.GUI_queue.qsize())
            if not self.Skewness_queue.empty():
                print("skew pulled")
                skew_3 = self.Skewness_queue.get()
                self.skew_3_2.setText(str(round(skew_3,3)))
            if not self.MSQ_queue.empty():
                print("msq pulled")
                msq_3 = self.MSQ_queue.get()
                self.msq_3_2.setText(str(round(msq_3,3)))
            QtCore.QTimer.singleShot(8, self.pollGUI_queue)

    # def pollGUI_queue(self):
    #     if not self.GUI_queue.empty():
    #         ledsData = self.GUI_queue.get()
    #         self.led1_data.extend(ledsData[:,2])
    #         self.led1_curve.setData(self.led1_data)
    #         self.led2_data.extend(ledsData[:,0])
    #         self.led2_curve.setData(self.led2_data)
    #         self.led3_data.extend(ledsData[:,1])
    #         self.led3_curve.setData(self.led3_data)
    #         self.led4_data.extend(ledsData[:,3])
    #         self.led4_curve.setData(self.led4_data)
    #
    #         #print(ledsData[:,0])
    #         #print(self.GUI_queue.qsize())
    #
    #
    #     QtCore.QTimer.singleShot(10, self.pollGUI_queue)


class Board_Read_Thread(threading.Thread):
    def __init__(self, board_handle, GUI_queue,Analysis_queue):
        threading.Thread.__init__(self)
        self.board = board_handle
        self.GUI_queue = GUI_queue
        self.Analysis_queue = Analysis_queue
        self._stop_event = threading.Event()
        if not self.board.is_port_open():
            self.board.open_port()
        self.board.start_adc_read()
    def stop(self):
        #print "Stopping file read"
        self._stop_event.set()
        print("Stopped task")

    def restart(self):
        #print "Stopping file read"
        self._stop_event.clear()
        print("restarted task")

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            tmp_sig=self.board.adc_unlimited_read(10)
            self.GUI_queue.put(tmp_sig)
            self.Analysis_queue.put(tmp_sig)
            # time.sleep(0.25)
        self.board.stop_adc_read()
        print("ADC reading stopped")
        self.board.close_port()

class Data_Analyse_Thread(threading.Thread):
    def __init__(self, Analysis_queue,skewness_queue,MSQ_queue,fs,low_cut,high_cut,order):
        threading.Thread.__init__(self)
        self.Analysis_queue = Analysis_queue
        self.Skewness_queue = skewness_queue
        self.MSQ_queue = MSQ_queue
        self._stop_event = threading.Event()
        self.window_1 = []
        self.window_2 = []
        self.window_3 = []
        self.window_4 = []
        self.index=0
        self.fs=fs
        self.b , self.a = analysis.butter_bandpass(fs,low_cut,high_cut,order)
        self.coefficients=[[ 0.86748371, -1.27669843],[-0.26330752,  2.02026498],[-0.36095814, -1.97291746]]
        self.intercepts=[-0.12581411, -1.02240841,  0.86276226]
        #TO DO: CHANGE WINDOW SIZE TO BE VARIABLE
    def stop(self):
        #print "Stopping file read"
        self._stop_event.set()
        print("Stopped task")

    def stopped(self):
        return self._stop_event.is_set()
        #TO DO: CHANGE WINDOW SIZE TO BE VARIABLE

    def restart(self):
        #print "Stopping file read"
        self._stop_event.clear()
        print("restarted task")

    def run(self):
        while not self.stopped():
            # print("hello")
            qsize=self.Analysis_queue.qsize()
            # print("length of window: ",len(self.window))
            for i in range(qsize):
                # print("reading")
                signal = self.Analysis_queue.get()
                # self.window_1.extend(signal[:,2])
                # self.window_2.extend(signal[:,0])
                self.window_3.extend(signal[:,1])
                # self.window_4.extend(signal[:,3])
            print("window size: ",len(self.window_3))

            if(len(self.window_3)>=750):
                print("IN")
                input=self.window_3[:750]
                self.window_3=self.window_3[750:]
                print("input size: ",len(input))
                detrended_window = analysis.detrend(analysis.filt_pipeline(input,self.b,self.a,self.fs))
                # filtered_window = analysis.notch_filt(self.window_3,50.0)
                skew_3=analysis.skew1(detrended_window)
                msq_3=analysis.get_msq(detrended_window,d=0.4,h=50)
                if msq_3>0.7 and msq_3<3.0 and skew_3>0:
                    if skew_3>0.6:
                        predicted_class=0
                    else:
                        predicted_class=1
                else:
                    predicted_class=2


                predicted_class=analysis.predict_sample([skew_3,msq_3],self.coefficients,self.intercepts)
                print("Predicted Class: ",predicted_class)
                self.Skewness_queue.put(skew_3)
                self.MSQ_queue.put(msq_3)
            time.sleep(0.1)

                # self.Skewness_queue.put(skew_3)
                # self.MSQ_queue.put(msq_3)

                # print("skewness of window: ",skew_3)
                # print("msqusion of window:",msq_3)
                # self.window_1=[]
                # self.window_2=[]
                # self.window_3=[]
                # self.window_4=[]







def main():
    print("started")
    app = QtGui.QApplication(sys.argv)
    ex = GuiViewer()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
