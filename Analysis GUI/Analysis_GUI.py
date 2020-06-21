from matplotlib import cm
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph import examples
import numpy as np
import pandas as pd
import sys
import analysis
from natsort import natsorted
import glob
import GUI_omar
import csv
from os.path import expanduser
from PyQt5.QtWidgets import *



# class CustomViewBox(pg.ViewBox):
#     def __init__(self, *args, **kwds):
#         pg.ViewBox.__init__(self, *args, **kwds)
#         self.setMouseMode(self.RectMode)
#     #
#     # ## reimplement right-click to zoom out
#     # def mouseClickEvent(self, ev):
#     #     if ev.button() == QtCore.Qt.RightButton:
#     #         self.autoRange()
#
#     def mouseDragEvent(self, ev):
#         if ev.button() == QtCore.Qt.RightButton:
#             ev.ignore()
#         else:
#             pg.ViewBox.mouseDragEvent(self, ev)

class GUI(QtGui.QMainWindow):
    def __init__(self):
        super(GUI, self).__init__()

        openFile = QtGui.QAction("&Open File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open File')
        openFile.triggered.connect(self.file_open)

        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu('&File')
        # fileMenu.addAction(extractAction)
        fileMenu.addAction(openFile)
        self.initUI()

    def initUI(self):
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.start_screen = Initial_Screen()
        self.setup_screen = GUI_omar.SetupScreen()
        self.record_screen = GUI_omar.RecordViewer()
        self.upload_screen = AnalyseViewer()
        self.central_widget.addWidget(self.start_screen)
        self.central_widget.addWidget(self.setup_screen)
        self.central_widget.addWidget(self.record_screen)
        self.central_widget.addWidget(self.upload_screen)
        self.central_widget.setCurrentWidget(self.start_screen)

        self.setGeometry(20, 20, 120, 80)
        self.setWindowTitle('Dataset Analyser')

        self.show()

    def file_open(self):
        self.name = QtGui.QFileDialog.getOpenFileName(self, 'Open File')
        if self.name[0]!="":
            self.get_sr_column()
        else:
            pass

    def import_file(self,column_name,sampling_rate):
        # sampling_rate = int(input("Enter Sampling Rate of Data: "))
        # length = int(input("Enter Length of Data (s) : "))
        tmp=pd.read_csv(self.name[0])
        DataSeries=tmp[column_name]
        self.length=len(DataSeries)
        self.ds=DataSeries
        self.sr=sampling_rate

    def get_sr_column(self):
        self.msg=data_info(self)
        if self.msg.exec_():
            self.upload_screen.update_Graph(self.ds,self.sr,self.length)
            self.central_widget.setCurrentWidget(self.upload_screen)
        else:
            pass


class Initial_Screen(QtGui.QWidget):
    def __init__(self):
        super(Initial_Screen, self).__init__()
        self.initUI()
    def initUI(self):

        self.Title = QtGui.QLabel("Choose What Data to Analyse:")
        self.Title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        self.Recordbtn = QtGui.QPushButton("Record Data")
        self.Uploadbtn = QtGui.QPushButton("Upload Data")


        grid = QtGui.QGridLayout()
        grid.setSpacing(1)

        grid.addWidget(self.Title, 0, 0, 1, 3)
        grid.addWidget(self.Recordbtn,1,1,1,1)
        grid.addWidget(self.Uploadbtn,2,1,1,1)

        self.Recordbtn.clicked.connect(self.RecordbtnPress)
        self.Uploadbtn.clicked.connect(self.UploadbtnPress)

        self.setLayout(grid)
        # self.setGeometry(100, 100, 120, 80)

        # self.setLayout(grid)
        # self.setGeometry(200, 200, 1200, 800)
        # self.setWindowTitle('Dataset Annotator')

    def RecordbtnPress(self):
        print("Clicked record")
        self.parent().setCurrentWidget(self.parent().parent().setup_screen)
        self.setGeometry(200, 200, 1200, 800)

    def UploadbtnPress(self):
        print("Clicked upload")
        self.name = QtGui.QFileDialog.getOpenFileName(self, 'Open File')
        print(self.name)
        if self.name[0] !="":
            self.get_sr_column()
        else:
            pass
        # print("ds: ",ds)
        # print("sr: ",sr)
        # print("l: ",l)
        # print("Parent Once: ",type(self.parent()))
        # print("Parent Twice: ",type(self.parent().parent()))
        # self.parent().parent().upload_screen.update_Graph(ds,sr,l*sr)
        # self.parent().setCurrentWidget(self.parent().parent().upload_screen)
    def import_file(self,column_name,sampling_rate):
        # sampling_rate = int(input("Enter Sampling Rate of Data: "))
        # length = int(input("Enter Length of Data (s) : "))
        try:
            tmp=pd.read_csv(self.name[0])
            DataSeries=tmp[column_name]
            self.length=len(DataSeries)
            self.ds=DataSeries
            self.sr=sampling_rate
            return True
        except:
            return False


    def get_sr_column(self):
        self.msg=data_info(self)
        if self.msg.exec_():
            self.parent().parent().upload_screen.update_Graph(self.ds,self.sr,self.length)
            self.parent().setCurrentWidget(self.parent().parent().upload_screen)
        else:
            pass













class AnalyseViewer(QtGui.QWidget):

    def __init__(self,ds=None,sample_rate=125,sample_time=60000):
        super(AnalyseViewer, self).__init__()
        self.initUI(ds,sample_rate,sample_time)

    def initUI(self,ds=None,sample_rate=125,sample_time=60000):

        self.chart = pg.GraphicsWindow(title="Data viewer")
        self.chart.resize(1200,80)
        # view = CustomViewBox()
        # view.setMouseMode(view.PanMode)
        self.line = self.chart.addPlot()
        # pen =QtGui.QPen(QtGui.QColor(200, 200, 200, 100),0.1)
        self.curve = self.line.plot()
        self.filterbttn = QtGui.QCheckBox("Filter")
        self.analysebttn = QtGui.QPushButton("Analyse")
        # self.filelbl = QtGui.QLabel("Export File Name: ")

        # self.filelbl.resize(280,40)
        self.txtbox = QtGui.QLineEdit(self)
        self.txtbox.resize(280,40)
        self.txtbox.setText("File_Name")
        self.exportbttn= QtGui.QPushButton("Export")
        self.classifiers=analysis.Classifiers()


        self.filterbttn.clicked.connect(self.filter_display)
        self.analysebttn.clicked.connect(self.analyse_display)
        self.exportbttn.clicked.connect(self.export)

        self.analysebttn.setEnabled(False)

        self.dropdown = QtGui.QComboBox(self)
        self.dropdown.addItem("Choose Classifier")
        for c in self.classifiers.three_class_classifiers.keys():
            self.dropdown.addItem(c)
        for c in self.classifiers.two_class_classifiers.keys():
            self.dropdown.addItem(c)

        self.dropdown.addItem("New Classifier 3")
        self.dropdown.addItem("New Classifier 2")
        self.dropdown.activated[str].connect(self.boardChoice)


        self.filtered_signal=[]
        self.a_segments=[]
        self.b_segments=[]
        self.c_segments=[]
        self.ppg_sr = sample_rate
        self.ppg_duration = sample_time
        print("sample rate: ",sample_rate)
        print("PPG Duration: ",self.ppg_duration)
        if ds==None:
            self.data = [0] * self.ppg_duration
            ds=pd.Series(self.data)
        self.ppg_x = np.arange(0, self.ppg_duration/self.ppg_sr, 1/self.ppg_sr)
        self.b=[]
        self.a=[]
        # self.ppg_x = range(0, 60000)
        # print("PPG x shape: ",self.ppg_x.shape)

        self.update_Graph(ds , self.ppg_sr , self.ppg_duration)

        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(1)


        self.setLayout(self.grid)
        self.grid.addWidget(self.chart, 0, 0, 5, 15)
        # self.grid.addWidget(self.filelbl, 4, 2, 1, 1)
        self.grid.addWidget(self.filterbttn, 5, 0, 1, 3)
        self.grid.addWidget(self.dropdown, 5, 3, 1, 3)
        self.grid.addWidget(self.analysebttn, 5, 6, 1, 3)
        self.grid.addWidget(self.txtbox, 5, 9, 1, 3)
        self.grid.addWidget(self.exportbttn , 5 , 12, 1, 3)

        # self.setGeometry(200, 200, 1200, 800)
        self.setWindowTitle('Dataset Annotator')
        # self.show()

    def update_Graph(self,ds,sample_rate, period):
        self.ds=ds
        self.fs=float(sample_rate)
        self.line.clear()
        self.curve = self.line.plot()
        self.length=period
        # print("PPG x shape: ",self.ppg_x.shape)
        self.data = ds.values
        # self.period = 3*125
        self.ppg_x = np.arange(0, period/sample_rate, 1/sample_rate)
        print("setting curve")
        self.curve.setData(self.ppg_x, self.data)
        print("finishing curve")

    def filter_display(self):
        print("Filter pressed")
        if self.filterbttn.isChecked():
            if self.b==[]:
                self.b , self.a = analysis.butter_bandpass(int(self.fs))
                print("new period= ",self.length/self.fs*125)
                self.filtered_signal= analysis.detrend(analysis.filt_pipeline(self.ds.values,self.b,self.a,int(self.length/self.fs*125)))
            self.ppg_x_2=np.arange(0, (self.length-1)/self.fs, 1/125)
            print(len(self.ppg_x_2))
            self.curve.setData(self.ppg_x_2, self.filtered_signal[:len(self.ppg_x_2)])
        else:
            self.curve.setData(self.ppg_x, self.ds.values)

    def analyse_display(self,classified=False,a_segments=[],b_segments=[],c_segments=[]):
        self.analysebttn.setEnabled(False)
        self.line.clear()
        self.curve = self.line.plot()
        if self.filtered_signal != []:
            self.curve.setData(self.ppg_x_2, self.filtered_signal[:len(self.ppg_x_2)])
        else:
            self.curve.setData(self.ppg_x, self.data)

        if not classified:
            self.a_segments , self.b_segments , self.c_segments = self.classify()
        else:
            self.a_segments=a_segments
            self.b_segments=b_segments
            self.c_segments=c_segments

        self.period=int(self.fs)*3
        print("a segments: ",self.a_segments)
        print("b segments: ",self.b_segments)
        print("c segments: ",self.c_segments)
        for a in self.a_segments:
            a_lr= pg.LinearRegionItem(values=[a,(a+3)],movable=False, brush=QtGui.QBrush(QtGui.QColor(0, 255, 0, 50)))
            # a_lr= pg.LinearRegionItem(values=[a,(a+3)],movable=False, brush=QtGui.QBrush(QtGui.QColor(255, 0, 0, 50)))
            self.line.addItem(a_lr)
        for b in self.b_segments:
            b_lr= pg.LinearRegionItem(values=[b,(b+3)],movable=False, brush=QtGui.QBrush(QtGui.QColor(0, 0, 255, 50)))
            self.line.addItem(b_lr)
        for c in self.c_segments:
            c_lr= pg.LinearRegionItem(values=[c,(c+3)],movable=False, brush=QtGui.QBrush(QtGui.QColor(255, 0, 0, 50)))
            self.line.addItem(c_lr)

    def export(self):
        tmp=[self.data,self.filtered_signal,self.a_segments,self.b_segments,self.c_segments]
        csv_file = "{}.csv".format(self.txtbox.text())
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(tmp)
        print("Exported")
        msg = QtGui.QMessageBox()
        msg.setWindowTitle("Exported")
        msg.setText("Exported with name: {}.csv".format(self.txtbox.text()))
        msg.exec_()

    def boardChoice(self,text):
        print("boardchoice")
        if text=="Choose Classifier":
            self.analysebttn.setEnabled(False)
            self.classifiers.set_current(text)
        elif text=="New Classifier 3":
            self.msg=analysis.input3class(self)
            # msg = QtGui.QMessageBox()
            # msg.setWindowTitle("New Classifier")
            # msg.setText("Input thresholds and classifiers!")
            if self.msg.exec_():  # this will show our messagebox
                self.analysebttn.setEnabled(True)
            else:
                self.dropdown.setCurrentIndex(0)
                self.analysebttn.setEnabled(False)
        elif text=="New Classifier 2":
            self.msg=analysis.input2class(self)
            # msg = QtGui.QMessageBox()
            # msg.setWindowTitle("New Classifier")
            # msg.setText("Input thresholds and classifiers!")
            if self.msg.exec_(): # this will show our messagebox
                self.analysebttn.setEnabled(True)
            else:
                self.dropdown.setCurrentIndex(0)
                self.analysebttn.setEnabled(False)

        else:
            self.analysebttn.setEnabled(True)
            self.classifiers.set_current(text)

    def addClassifier(self,type,name,coefficients,intercepts):
        if type==2:
            self.classifiers.new_classifier2(name,coefficients,intercepts)
        else:
            self.classifiers.new_classifier3(name,coefficients,intercepts)
        self.dropdown.addItem(name)
        count=self.dropdown.count()
        self.dropdown.setCurrentIndex(count-1)
        self.classifiers.set_current(name)

    def classify(self):
        a_segments = []
        b_segments = []
        c_segments = []
        period=int(3*self.fs)
        print(self.fs)
        b,a=analysis.butter_bandpass(self.fs,lowcut=0.5, highcut=30, order=4)

        if self.classifiers.current[-1]=="3":
            for i in range(int(self.ds.shape[0]/period)):
                signal = self.ds[(i*period):(i+1)*period]
                filt_signal=analysis.filt_pipeline(signal,b,a,int(self.fs))
                detrend_signal=analysis.detrend(filt_signal)

                tmp_sk = analysis.skew1(detrend_signal)
                tmp_msq = analysis.get_msq(detrend_signal,d=0.4,h=50)
                if tmp_msq>0.7 and tmp_msq<3.0 and tmp_sk>0:
                    if tmp_sk>0.6:
                        tmp_class=0
                    else:
                        tmp_class=1
                else:
                    tmp_class=2
                tmp_sample = [tmp_sk,tmp_msq]
                tmp_class=self.classifiers.classify_sample3(tmp_sample)
                # if tmp_sk>3.0:
                #     tmp_class=2
                # print("Predicted Class: ",tmp_class)
                if tmp_class==0:
                    a_segments.append(i*3)
                elif tmp_class==1:
                    b_segments.append(i*3)
                elif tmp_class==2:
                    c_segments.append(i*3)
                else:
                    print("ERROR")
            return a_segments,b_segments,c_segments
        if self.classifiers.current[-1]=="2":
            for i in range(int(self.ds.shape[0]/period)):
                signal = self.ds[(i*period):(i+1)*period]
                filt_signal=analysis.filt_pipeline(signal,b,a,int(self.fs))
                detrend_signal=analysis.detrend(filt_signal)

                tmp_sk = analysis.skew1(detrend_signal)
                tmp_msq = analysis.get_msq(detrend_signal,d=0.4,h=50)
                if tmp_msq>0.7 and tmp_msq<3.0 and tmp_sk>0:
                    if tmp_sk>0.6:
                        tmp_class=0
                    else:
                        tmp_class=1
                else:
                    tmp_class=2
                tmp_sample = [tmp_sk,tmp_msq]
                tmp_class=self.classifiers.classify_sample2(tmp_sample)
                # if tmp_sk>3.0:
                #     tmp_class=2
                # print("Predicted Class: ",tmp_class)
                if tmp_class==0:
                    a_segments.append(i*3)
                elif tmp_class==1:
                    b_segments.append(i*3)
                elif tmp_class==2:
                    c_segments.append(i*3)
                else:
                    print("ERROR")
            return a_segments,b_segments,c_segments


def import_folder(location):
    # sampling_rate = int(input("Enter Sampling Rate of Data: "))
    # length = int(input("Enter Length of Data (s) : "))
    sampling_rate=125.0
    length=480
    print("Sampling Rate : ",sampling_rate)
    print("Length : ",length)
    filenames = natsorted(glob.glob(location+"/bidmc_*_Signals.csv"))
#     print(filenames)
    dataframes = []
    columns=[str(i) for i in range(len(filenames))]
    for f in filenames:
        tmp = pd.read_csv(f)
        tmp = tmp[" PLETH"]
        dataframes.append(tmp[:sampling_rate*length])
    DataFrame = pd.concat(dataframes,axis=1)
    DataFrame.columns=columns
    return DataFrame, sampling_rate, length



class data_info(QtGui.QDialog):
    def __init__(self,parent):
        super(data_info, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        print("opening pop up")
        layout = QtGui.QGridLayout()
        layout.setSpacing(1)

        self.label_sr=QtGui.QLabel("Sample Rate: ")
        self.sr = QtGui.QLineEdit()

        self.label_column=QtGui.QLabel("Column Name: ")
        self.column = QtGui.QLineEdit()

        layout.addWidget(self.label_sr, 0, 0 , 1, 2)
        layout.addWidget(self.sr, 0, 2 , 1, 2)

        layout.addWidget(self.label_column, 1, 0 , 1, 2)
        layout.addWidget(self.column, 1, 2 , 1, 2)


        self.btn1 = QtGui.QPushButton("Cancel")
        self.btn1.clicked.connect(self.cancel)

        self.btn2 = QtGui.QPushButton("Open")
        self.btn2.clicked.connect(self.add)

        layout.addWidget(self.btn1, 2, 0 , 1, 2)
        layout.addWidget(self.btn2, 2, 2 , 1, 2)
        self.setLayout(layout)
        self.setWindowTitle('File Information')

    def isint(self,value):
      try:
        int(value)
        return True
      except ValueError:
        return False

    def cancel(self):
        self.reject()

    def add(self):
        if self.isint(self.sr.text()):
            if self.column.text() != "":
                success=self.parent().import_file(self.column.text(),int(self.sr.text()))
                if success:
                    self.accept()
                else:
                    msg = QtGui.QMessageBox()
                    msg.setWindowTitle("ERROR")
                    msg.setText("IMPORT DATA ERROR CHECK DATA FORMAT AND TRY AGAIN")
                    msg.exec_()
                    self.reject()
            else:
                msg = QtGui.QMessageBox()
                msg.setWindowTitle("ERROR")
                msg.setText("EMPTY COLUMN NAME!")
                msg.exec_()
        else:
            msg = QtGui.QMessageBox()
            msg.setWindowTitle("ERROR")
            msg.setText("INVALID SAMPLE RATE!")
            msg.exec_()

def main():
    # print("started")
    # choice = input("Import 'Folder' or Import 'File': ")
    # if choice == "Folder":
    #     print("Folder")
    #     location = input("Input Folder Path: ")
    #     df , sr , l = import_folder(location)
    #     index=input("Folder has {} valid data series please input which sample to view ({}-{})".format(df.shape[1],df.columns[0],df.columns[-1]))
    #     ds=df[index]
    # elif choice == "File":
    #     print("File")
    #     location = input("Input File Path: ")
    #     ds , sr, l = import_file(location)
    # else:
    #     print("Incorrect Selection")
    # # examples.run()
    # app = QtGui.QApplication(sys.argv)
    app = QtGui.QApplication(sys.argv)
    ex = GUI()

    # ex = Filefind()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
