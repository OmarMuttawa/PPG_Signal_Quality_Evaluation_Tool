from scipy.stats import skew
import numpy as np
from scipy import signal as s
import numpy as np
from numpy import NaN, Inf, arange, isscalar, asarray, array
from pyqtgraph.Qt import QtCore, QtGui
def billauer_peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.

    """
    maxtab = []
    mintab = []

    if x is None:
        x = np.arange(len(v))

    v = np.asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        sys.exit('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in np.arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx-delta:
                maxtab.append(mxpos)
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append(mnpos)
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab) , array(mintab)

def scipy_find_peaks(sig,height=None,threshold=None,distance=None):
    return s.find_peaks(sig,height=height,threshold=threshold,distance=distance)


def skew1(signal):
    return skew(signal)

def perfusion(signal):
    return (((np.max(signal)-np.min(signal))/np.mean(signal))*100.0)


def get_msq(detrended_signal,d=0.4,h=21):
    peaks_1,_=scipy_find_peaks(detrended_signal,distance=h)
    peaks_2,_=billauer_peakdet(detrended_signal,d)
    # print("Peaks 1: ",peaks_1)
    # print("Peaks 2: ",peaks_2)
    if len(peaks_1)==0:
        return 0.0
    return len(np.intersect1d(peaks_1,peaks_2))/len(peaks_1)

def notch_filt(signal,f0,fs=250.0,Q=60.0):
    # Design notch filter
    b, a = s.iirnotch(f0, Q, fs)
    # Filter signal
    filtered= s.filtfilt(b, a, signal)
    return filtered


def filter_down_scale(sig,b,a,fs):
    filtered = s.filtfilt(b, a,sig)
    if fs == 250:
        return scale_data(s.decimate(filtered,2,ftype="iir"))
    else:
        return scale_data(filtered)

def scale_data(sig):
    s_min = np.min(sig)
    s_max = np.max(sig)
    s_mean= np.mean(sig)
    std = (sig - s_min) / (s_max - s_min)
#     scaled = std * (s_max - s_min) + s_min
    return std


def predict_set(X,coefficients,intercepts):
    predictions=[]
    for index in X.index:
        predictions.append(predict_sample(X.loc[index].values,coefficients,intercepts))
    return predictions

def filt(sig,b,a):
    # print("sig len: ",len(sig))
    # print("b: ",b)
    # print("a: ",a)
    return s.filtfilt(b,a,sig)

def filt_pipeline(sig,b,a,period=375):
    sig=s.resample(sig,period)
    sig=filt(sig,b,a)
    return scale_data(sig)

def detrend(sig):
    return s.detrend(sig)


def butter_bandpass(fs,lowcut=0.5, highcut=30, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = s.butter(order, [low, high], btype='band')
    return b, a


class Classifiers():
    def __init__(self):
        self.current="Universal"
        self.three_class_classifiers={
        "Universal 3" : {
            "coefficients" : [[ 0.86748371, -1.27669843],[-0.26330752,  2.02026498],[-0.36095814, -1.97291746]],
            "intercepts" : [-0.12581411, -1.02240841,  0.86276226]
            },
        "Vietnam Custom 3" : {
            "coefficients" : [[ 1.61915915,  5.15405977],[-0.40336029,  2.14019879],[-0.00989865, -3.34801026]],
            "intercepts" : [-3.79423438, -1.03319031,  1.50239078]
            }
        }
        self.two_class_classifiers={
        "Universal 2" : {
            "coefficients" : [-0.23720892 , -1.10489991],
            "intercepts" : 0.68119408
            },
        "AFE Custom 2" : {
            "coefficients" : [-0.10423464 , -1.52750249],
            "intercepts" : 0.71851766
            }
        }
    def new_classifier3(self,name,coefficients,intercepts):
        self.three_class_classifiers[name]={}
        self.three_class_classifiers[name]["coefficients"]=coefficients
        self.three_class_classifiers[name]["intercepts"]=intercepts
    def new_classifier2(self,name,coefficients,intercepts):
        self.two_class_classifiers[name]={}
        self.two_class_classifiers[name]["coefficients"]=coefficients
        self.two_class_classifiers[name]["intercepts"]=intercepts

    def classify_sample3(self,sample):
        Class_0_Score=self.three_class_classifiers[self.current]["coefficients"][0][0]*sample[0]+self.three_class_classifiers[self.current]["coefficients"][0][1]*sample[1]+self.three_class_classifiers[self.current]["intercepts"][0]
        Class_1_Score=self.three_class_classifiers[self.current]["coefficients"][1][0]*sample[0]+self.three_class_classifiers[self.current]["coefficients"][1][1]*sample[1]+self.three_class_classifiers[self.current]["intercepts"][1]
        Class_2_Score=self.three_class_classifiers[self.current]["coefficients"][2][0]*sample[0]+self.three_class_classifiers[self.current]["coefficients"][2][1]*sample[1]+self.three_class_classifiers[self.current]["intercepts"][2]
        Scores=[Class_0_Score,Class_1_Score,Class_2_Score]
        predicted_class=Scores.index(np.max(Scores))
        return predicted_class
    def classify_sample2(self,sample):
        Class_1_Score=self.two_class_classifiers[self.current]["coefficients"][0]*sample[0]+self.two_class_classifiers[self.current]["coefficients"][1]*sample[1]+self.two_class_classifiers[self.current]["intercepts"]
        Scores=[0,Class_1_Score]
        predicted_class=Scores.index(np.max(Scores))+1
        print(predicted_class)
        return predicted_class

    def set_current(self,classifier):
        self.current=classifier

class input3class(QtGui.QDialog):
    def __init__(self,parent):
        super(input3class, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        print("opening pop up")
        layout = QtGui.QGridLayout()
        layout.setSpacing(1)

        self.label_0=QtGui.QLabel("Name: ")
        self.name = QtGui.QLineEdit()

        layout.addWidget(self.label_0, 0, 0 , 1, 2)
        layout.addWidget(self.name, 0, 2 , 1, 2)

        self.label_1=QtGui.QLabel("")
        self.label_2=QtGui.QLabel("Skew")
        self.label_3=QtGui.QLabel("MSQ")
        self.label_4=QtGui.QLabel("Intercepts")
        layout.addWidget(self.label_1, 2, 0 , 1, 1)
        layout.addWidget(self.label_2, 2, 1 , 1, 1)
        layout.addWidget(self.label_3, 2, 2 , 1, 1)
        layout.addWidget(self.label_4, 2, 3 , 1, 1)

        self.class_1=QtGui.QLabel("Class 1")
        self.le_1_skew = QtGui.QLineEdit()
        self.le_1_msq = QtGui.QLineEdit()
        self.le_1_intercept = QtGui.QLineEdit()
        layout.addWidget(self.class_1, 3, 0 , 1, 1)
        layout.addWidget(self.le_1_skew , 3, 1 , 1, 1)
        layout.addWidget(self.le_1_msq, 3, 2 , 1, 1)
        layout.addWidget(self.le_1_intercept, 3, 3 , 1, 1)

        self.class_2=QtGui.QLabel("Class 2")
        self.le_2_skew = QtGui.QLineEdit()
        self.le_2_msq = QtGui.QLineEdit()
        self.le_2_intercept = QtGui.QLineEdit()
        layout.addWidget(self.class_2, 4, 0 , 1, 1)
        layout.addWidget(self.le_2_skew , 4, 1 , 1, 1)
        layout.addWidget(self.le_2_msq, 4, 2 , 1, 1)
        layout.addWidget(self.le_2_intercept, 4, 3 , 1, 1)


        self.class_3=QtGui.QLabel("Class 3")
        self.le_3_skew = QtGui.QLineEdit()
        self.le_3_msq = QtGui.QLineEdit()
        self.le_3_intercept = QtGui.QLineEdit()
        layout.addWidget(self.class_3, 5, 0 , 1, 1)
        layout.addWidget(self.le_3_skew , 5, 1 , 1, 1)
        layout.addWidget(self.le_3_msq, 5, 2 , 1, 1)
        layout.addWidget(self.le_3_intercept, 5, 3 , 1, 1)

        self.btn1 = QtGui.QPushButton("Cancel")
        self.btn1.clicked.connect(self.cancel)

        self.btn2 = QtGui.QPushButton("Add")
        self.btn2.clicked.connect(self.add)

        layout.addWidget(self.btn1, 6, 0 , 1, 2)
        layout.addWidget(self.btn2, 6, 2 , 1, 2)
        self.setLayout(layout)
        self.setWindowTitle('Adding New Classifier')

    def isfloat(self,value):
      try:
        float(value)
        return True
      except ValueError:
        return False

    def cancel(self):
        self.parent().dropdown.setCurrentIndex(0)
        self.reject()
    def add(self):
        if self.name.text() != "":
            if self.isfloat(self.le_1_skew.text()) and self.isfloat(self.le_1_msq.text()) and self.isfloat(self.le_2_skew.text()) and self.isfloat(self.le_2_msq.text()) and self.isfloat(self.le_3_skew.text()) and self.isfloat(self.le_3_msq.text()):
                if self.isfloat(self.le_1_intercept.text()) and self.isfloat(self.le_2_intercept.text()) and self.isfloat(self.le_3_intercept.text()):
                    name=self.name.text()+" 3"
                    coefficients=[[float(self.le_1_skew.text()),float(self.le_1_msq.text())],[float(self.le_2_skew.text()),float(self.le_2_msq.text())],[float(self.le_3_skew.text()),float(self.le_3_msq.text())]]
                    intercepts=[float(self.le_1_intercept.text()),float(self.le_2_intercept.text()),float(self.le_3_intercept.text())]
                    self.parent().addClassifier(3,name,coefficients,intercepts)
                    self.accept()
                else:
                    msg = QtGui.QMessageBox()
                    msg.setWindowTitle("ERROR")
                    msg.setText("INCORRECT INTERCEPT INPUT!")
                    msg.exec_()
            else:
                msg = QtGui.QMessageBox()
                msg.setWindowTitle("ERROR")
                msg.setText("INCORRECT THRESHOLD INPUT!")
                msg.exec_()
        else:
            msg = QtGui.QMessageBox()
            msg.setWindowTitle("ERROR")
            msg.setText("EMPTY CLASSIFIER NAME!")
            msg.exec_()


class input2class(QtGui.QDialog):
    def __init__(self,parent):
        super(input2class, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        print("opening pop up")
        layout = QtGui.QGridLayout()
        layout.setSpacing(1)

        self.label_0=QtGui.QLabel("Name: ")
        self.name = QtGui.QLineEdit()

        layout.addWidget(self.label_0, 0, 0 , 1, 2)
        layout.addWidget(self.name, 0, 2 , 1, 2)

        self.label_1=QtGui.QLabel("")
        self.label_2=QtGui.QLabel("Skew")
        self.label_3=QtGui.QLabel("MSQ")
        self.label_4=QtGui.QLabel("Intercepts")
        layout.addWidget(self.label_1, 2, 0 , 1, 1)
        layout.addWidget(self.label_2, 2, 1 , 1, 1)
        layout.addWidget(self.label_3, 2, 2 , 1, 1)
        layout.addWidget(self.label_4, 2, 3 , 1, 1)

        self.class_1=QtGui.QLabel("Class 2")
        self.le_1_skew = QtGui.QLineEdit()
        self.le_1_msq = QtGui.QLineEdit()
        self.le_1_intercept = QtGui.QLineEdit()
        layout.addWidget(self.class_1, 3, 0 , 1, 1)
        layout.addWidget(self.le_1_skew , 3, 1 , 1, 1)
        layout.addWidget(self.le_1_msq, 3, 2 , 1, 1)
        layout.addWidget(self.le_1_intercept, 3, 3 , 1, 1)



        self.btn1 = QtGui.QPushButton("Cancel")
        self.btn1.clicked.connect(self.cancel)

        self.btn2 = QtGui.QPushButton("Add")
        self.btn2.clicked.connect(self.add)

        layout.addWidget(self.btn1, 6, 0 , 1, 2)
        layout.addWidget(self.btn2, 6, 2 , 1, 2)
        self.setLayout(layout)
        self.setWindowTitle('Adding New Classifier')

    def isfloat(self,value):
      try:
        float(value)
        return True
      except ValueError:
        return False

    def cancel(self):
        self.parent().dropdown.setCurrentIndex(0)
        self.reject()
    def add(self):
        if self.name.text() != "":
            if self.isfloat(self.le_1_skew.text()) and self.isfloat(self.le_1_msq.text()):
                if self.isfloat(self.le_1_intercept.text()):
                    name=self.name.text()+" 2"
                    coefficients=[float(self.le_1_skew.text()),float(self.le_1_msq.text())]
                    intercepts=float(self.le_1_intercept.text())
                    self.parent().addClassifier(2,name,coefficients,intercepts)
                    self.accept()
                else:
                    msg = QtGui.QMessageBox()
                    msg.setWindowTitle("ERROR")
                    msg.setText("INCORRECT INTERCEPT INPUT!")
                    msg.exec_()
            else:
                msg = QtGui.QMessageBox()
                msg.setWindowTitle("ERROR")
                msg.setText("INCORRECT THRESHOLD INPUT!")
                msg.exec_()
        else:
            msg = QtGui.QMessageBox()
            msg.setWindowTitle("ERROR")
            msg.setText("EMPTY CLASSIFIER NAME!")
            msg.exec_()
