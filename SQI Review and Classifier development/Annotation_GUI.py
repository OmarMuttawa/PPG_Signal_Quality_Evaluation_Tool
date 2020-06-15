from matplotlib import cm
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
import pandas as pd
import sys
import analysis

class GuiViewer(QtGui.QWidget):

    def __init__(self,file_path,sample_rate,sample_time):
        super(GuiViewer, self).__init__()
        self.initUI(sample_rate,sample_time)
        self.initVariables(file_path)

    def initUI(self,sample_rate,sample_time):

        self.smpllabel = QtGui.QLabel("Current Sample: ")
        self.smpllabel.setMaximumHeight(15)
        self.smpllabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.indexlabel = QtGui.QLabel("Current Index /: ")
        self.indexlabel.setMaximumHeight(15)
        self.indexlabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.complabel = QtGui.QLabel("Completed -/{}: ")
        self.complabel.setMaximumHeight(15)
        self.complabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        self.chart = pg.GraphicsWindow(title="LED1 data")
        self.chart.resize(1200,80)
        self.line = self.chart.addPlot()
        self.curve = self.line.plot()

        self.ppg_sr = sample_rate
        self.ppg_duration = sample_time
        self.ppg_len = int(self.ppg_sr * self.ppg_duration)
        self.data = [0] * self.ppg_len
        self.ppg_x = np.arange(0, self.ppg_duration, 1/self.ppg_sr)
        self.b , self.a = analysis.butter_bandpass(sample_rate,lowcut=0.5, highcut=30, order=4)

        self.Abtn = QtGui.QPushButton("A")
        self.Bbtn = QtGui.QPushButton("B")
        self.Cbtn = QtGui.QPushButton("C")

        self.Abtn.clicked.connect(self.AbtnPress)
        self.Bbtn.clicked.connect(self.BbtnPress)
        self.Cbtn.clicked.connect(self.CbtnPress)

        self.Filterbtn = QtGui.QCheckBox("Filter")
        self.Scalebtn = QtGui.QCheckBox("Scale")
        self.Detrendbtn = QtGui.QCheckBox("Detrend")
        # self.Filterbtn.setStyleSheet("#Filterbtn:checked {background-color: green}")
        self.Savebtn = QtGui.QPushButton("Save")
        self.Restbtn = QtGui.QPushButton("Restart")
        self.Nextbtn = QtGui.QPushButton("Next")
        self.Previousbtn = QtGui.QPushButton("Previous")
        self.filter_state=False

        self.Filterbtn.clicked.connect(self.ProcessbtnPress)
        self.Scalebtn.clicked.connect(self.ProcessbtnPress)
        self.Detrendbtn.clicked.connect(self.ProcessbtnPress)

        self.Savebtn.clicked.connect(self.SavebtnPress)
        self.Restbtn.clicked.connect(self.RestbtnPress)
        self.Nextbtn.clicked.connect(self.NextbtnPress)
        self.Previousbtn.clicked.connect(self.PreviousbtnPress)

        grid = QtGui.QGridLayout()
        grid.setSpacing(1)

        grid.addWidget(self.chart, 0, 0, 4, 15)
        grid.addWidget(self.Abtn,  5, 0, 1, 5)
        grid.addWidget(self.Bbtn,  5, 5, 1, 5)
        grid.addWidget(self.Cbtn,  5, 10, 1, 5)

        grid.addWidget(self.Filterbtn, 6,0,1,1)
        grid.addWidget(self.Scalebtn, 6,1,1,1)
        grid.addWidget(self.Detrendbtn, 6,2,1,1)

        grid.addWidget(self.Savebtn, 6,3,1,3)
        grid.addWidget(self.Restbtn, 6,6,1,3)
        grid.addWidget(self.Nextbtn, 6,9,1,3)
        grid.addWidget(self.Previousbtn, 6,12,1,3)

        grid.addWidget(self.smpllabel, 7,0,1,4)
        grid.addWidget(self.indexlabel, 7,4,1,4)
        grid.addWidget(self.complabel,7,8,1,4)

        self.setLayout(grid)
        self.setGeometry(200, 200, 1200, 800)
        self.setWindowTitle('Dataset Annotator')
        self.show()

    def initVariables(self,file_path):
        try:
            self.DataFrame = pd.read_pickle(file_path)
            self.DataFrame = self.DataFrame.dropna()
        except:
            print("Invalid file path DataFrame not found")
            sys.exit(app.exec_())
        try:
            self.config = pd.read_csv("config.csv")
            self.index  =self.config["index"][0]
            print("Current index: ",self.index)
        except:
            print("No configuration file found starting from first index")
            self.index = 0
        try:
            self.annotations = pd.read_csv("annotations.txt", sep = " ",index_col=0)
            print("Imported Annotations: ")
            print(self.annotations)
        except:
            print("No saved annotation file found starting from begining")
            self.columns=["Label"]
            self.annotations=pd.DataFrame(index=self.DataFrame.columns,columns=self.columns)
            self.index = 0

        completed = 0
        self.updateView()

    def updateView(self):
        self.Filterbtn.setChecked(False)
        self.Scalebtn.setChecked(False)
        self.Detrendbtn.setChecked(False)
        print("Close Annotations: \n {}".format(self.annotations.iloc[self.index-5:self.index+5]))
        self.smpllabel.setText("Current Sample: {}".format(self.DataFrame.columns[self.index]))
        self.indexlabel.setText("Current Index: {} of {}".format(self.index,self.DataFrame.shape[1]-1))
        self.completed = self.check_complete()
        self.complabel.setText("Completed {}/{} ".format(self.completed,self.DataFrame.shape[1]-1))
        self.data = self.DataFrame.iloc[:,self.index]
        self.curve.setData(self.ppg_x, self.data)



    def AbtnPress(self):
        print("A press")
        self.class_selected("A")

    def BbtnPress(self):
        print("B press")
        self.class_selected("B")

    def CbtnPress(self):
        print("C press")
        self.class_selected("C")

    def ProcessbtnPress(self):
        print("Process Pressed")

        # print(self.Filterbtn.isChecked())
        if self.Filterbtn.isChecked():
            self.data = self.DataFrame.iloc[:,self.index]
            self.filt= analysis.filt(self.data,self.b,self.a)
            if self.Scalebtn.isChecked():
                self.scaled = analysis.scale_data(self.filt)
                if self.Detrendbtn.isChecked():
                    self.detrended = analysis.detrend(self.scaled)
                    self.curve.setData(self.ppg_x, self.detrended)
                else:
                    self.curve.setData(self.ppg_x, self.scaled)
            else:
                if self.Detrendbtn.isChecked():
                    self.detrended = analysis.detrend(self.filt)
                    self.curve.setData(self.ppg_x, self.detrended)
                else:
                    self.curve.setData(self.ppg_x, self.filt)

        else:
            if self.Scalebtn.isChecked():
                self.scaled = analysis.scale_data(self.data)
                if self.Detrendbtn.isChecked():
                    self.detrended = analysis.detrend(self.scaled)
                    self.curve.setData(self.ppg_x, self.detrended)
                else:
                    self.curve.setData(self.ppg_x, self.scaled)
            else:
                if self.Detrendbtn.isChecked():
                    self.detrended = analysis.detrend(self.data)
                    self.curve.setData(self.ppg_x, self.detrended)
                else:
                    self.curve.setData(self.ppg_x, self.data)


    #
    #
    #     # # self.Filterbtn.toggle()
    #     # if not self.filter_state:
    #     #     self.filter_state=True
    #     #     self.Filterbtn.setChecked(True)
    #     #     # self.Filterbtn.setStyleSheet("background-color: blue")
    #     #     print(self.filter_state)
    #     # else:
    #     #     self.filter_state=False
    #     #     self.Filterbtn.setChecked(False)
    #     #     # self.Filterbtn.setStyleSheet("background-color: grey")
    #     #     print(self.filter_state)
    # def ScalebtnPress(self):
    #     pass
    # def DetrendbtnPress(self):
    #     pass

    def SavebtnPress(self):
        print("Save")
        print("Annotations so far: {}".format(self.annotations))
        self.annotations.to_csv("Annotations.txt",sep=" ")
        self.config=pd.Series([self.index])
        self.config.to_csv("config.csv",header=["index"],index=False)

    def RestbtnPress(self):
        print("Restart")
        self.index = 0
        self.updateView()

    def NextbtnPress(self):
        print("Next")
        self.index +=1
        if self.index>=self.DataFrame.shape[1]:
            self.index = 0
        self.updateView()

    def PreviousbtnPress(self):
        print("Previous")
        self.index -= 1
        if self.index < 0:
            self.index = self.DataFrame.shape[1]-1
        self.updateView()


    def class_selected(self,c):
        print(self.annotations.index[self.index])
        self.annotations.loc[self.DataFrame.columns[self.index]]["Label"]=c
        print("Annotations so far: \n {}".format(self.annotations))
        self.index +=1
        if self.index>=self.DataFrame.shape[1]:
            self.index = 0
        self.updateView()

    def check_complete(self):
        completed=sum(self.annotations.notna()["Label"].values)
        return completed






def main():
    print("started")
    file_path= input("Please Enter File path: ")
    sample_rate = float(input("Please Enter sample_rate: "))
    sample_time = float(input("Please Enter sample time: "))
    app = QtGui.QApplication(sys.argv)
    ex = GuiViewer(file_path,sample_rate,sample_time)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
