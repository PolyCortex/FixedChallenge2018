from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot
import sys
import gui
import numpy as np
import pyqtgraph as pg
import time
import threading
import multiprocessing as mp
import Adafruit_ADS1x15

adc = Adafruit_ADS1x15.ADS1115()
GAIN=1
freq=860/4 #hz


class App(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    # This function is performed everytime the application is launched. It initializes the GUI and all of its parameters
    def __init__(self, parent=None):
        # Initialize
        global freq
        super(App, self).__init__(parent)
        self.setupUi(self)
        self.x_f=np.linspace(0,freq/5,int(np.round(freq/2)))
        self.x_t=np.linspace(0,2.5,int(freq))

        # Initialize variable
        self.savepath = ""
        self.has_savepath = False
        self.xdata = [[], [], [], []]
        self.ydata = [[], [], [], []]
        self.fxdata = [[], [], [], []]
        self.fydata = [[], [], [], []]
        self.threads = []
        self.threadpool = QtCore.QThreadPool()

        # Associate callbacks
        self.btn_startstop.clicked.connect(self.startstop)
        self.btn_browse.clicked.connect(self.browse)

        # Initialize graphs
        self.timers = []
        self.plotlist = [self.tsgraph_el1, self.tsgraph_el2, self.tsgraph_el3, self.tsgraph_el4,
                         self.fsgraph_el1, self.fsgraph_el2, self.fsgraph_el3, self.fsgraph_el4]
        plottitles = ['Time Series - Electrode 1', 'Time Series - Electrode 2', 'Time Series - Electrode 3',
                      'Time Series - Electrode 4', 'Frequency Spectrum - Electrode 1',
                      'Frequency Spectrum - Electrode 2', 'Frequency Spectrum - Electrode 3',
                      'Frequency Spectrum - Electrode 4']
        plotlinecolors = ['r','g','c','y','r','g','c','y']
        self.curve = []
        for itr in range(len(self.plotlist)):
            g = self.plotlist[itr]
            g.plotItem.setTitle(plottitles[itr])
            if itr < 4:
                g.plotItem.setLabel('left','Amplitude','V')
                g.plotItem.setLabel('bottom','Time','s')
#                g.plotItem.getViewBox().setXRange(0, 1)
            else:
                g.plotItem.setLabel('left','Amplitude','dB')
                g.plotItem.setLabel('bottom','Frequency','Hz')
#                g.plotItem.getViewBox().setXRange(0, 60)
            g.plotItem.getViewBox().setMouseEnabled(False)
            g.plotItem.getViewBox().setMenuEnabled(False)
            self.curve.append(g.plotItem.plot())
            self.curve[itr].setPen(plotlinecolors[itr])

        self.getADC_=getADC()
        self.getADC_.sendData.connect(self.update_plot)


    def startstop(self):
        if self.btn_startstop.text() == "START":
            self.btn_startstop.setText("STOP")
            self.getADC_.startButton()
#            # Start acquisition
#            self.threads = []
#            if self.group_el1.isChecked():
#                self.threads.append(AcquisitionThread(0))
#                self.threads[-1].signals.data.connect(self.update_data)
#                # self.threads.append(PlottingThread(self.update_plot, 0))
#            if self.group_el2.isChecked():
#                self.threads.append(AcquisitionThread(1))
#                self.threads[-1].signals.data.connect(self.update_data)
#                # self.threads.append(PlottingThread(self.update_plot, 1))
#            if self.group_el3.isChecked():
#                self.threads.append(AcquisitionThread(2))
#                self.threads[-1].signals.data.connect(self.update_data)
#                # self.threads.append(PlottingThread(self.update_plot, 2))
#            if self.group_el4.isChecked():
#                self.threads.append(AcquisitionThread(3))
#                self.threads[-1].signals.data.connect(self.update_data)
#                # self.threads.append(PlottingThread(self.update_plot, 3))
#            for t in self.threads:
#                self.threadpool.start(t)
#                t.start_button()

        elif self.btn_startstop.text() == "STOP":
            self.btn_startstop.setText("START")
            # Stop acquisition
            self.getADC_.stopButton()
#            for t in self.threads:
#                t.stop_button()

    # Callback function of the "Browse" button, which is used to ask the user where to save data after acquisition.
    def browse(self):
        self.savepath = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.has_savepath = True
        self.ed_saveloc.setText(self.savepath)

    # Emit functions (launched when emitting from the QThread objects
    def update_data(self, data):
        plot_id = data[0]
        self.xdata[plot_id] = data[1]
        self.ydata[plot_id] = data[2]
        self.fxdata[plot_id] = data[3]
        self.fydata[plot_id] = data[4]
        self.update_plot(plot_id)

    def update_plot(self, data_t,data_f,plot_t,plot_f):
        # TODO : Adjust range from parameters in GUI
        self.curve[plot_t].setData(self.x_t, data_t)
        self.curve[plot_f].setData(self.x_f, data_f.real)

    # Validation functions
    def data_valid(self, plot_id):
        if len(self.xdata[plot_id]) != len(self.ydata[plot_id]):
            return False
        if len(self.fxdata[plot_id]) != len(self.fydata[plot_id]):
            return False
        # TODO : Add other validation? (data type, etc.)
        return True




### JONNNY TAKES OVER

class getADC(QThread):
    sendData=pyqtSignal(object,object,object,object)
    # emit signal once you want to plot something, that should pass arguments to a function that will just do plot when triggered
        
    def __init__(self):
        QThread.__init__(self)
        
        self.startButton_=False
        self.dataTreatment_E1=dataTreatment(0,4)
        self.dataTreatment_E1.sendTreatedData.connect(self.update_plot)
        self.dataTreatment_E2=dataTreatment(1,5)
        self.dataTreatment_E2.sendTreatedData.connect(self.update_plot)
        self.dataTreatment_E3=dataTreatment(2,6)
        self.dataTreatment_E3.sendTreatedData.connect(self.update_plot)
        self.dataTreatment_E4=dataTreatment(3,7)
        self.dataTreatment_E4.sendTreatedData.connect(self.update_plot)
        
    def __del__(self):
        self.wait()
    def startButton(self):
        self.startButton_=True
        self.start()
        
    def update_plot(self,data_t, data_f,plot_t,plot_f):
        self.sendData.emit(data_t,data_f,plot_t, plot_f)    
    def stopButton(self):
        self.startButton_=False

    def run(self): #### when you wanna start this thread do nameOfThread.start()
        ## faire des update ici, et emettre tes signaux icu
        global adc, GAIN, freq
        data=np.zeros((int(freq),4))
        count=0
        while self.startButton_:
            for i in range(4):
        # Read the specified ADC channel using the previously set gain value.
                data[count,i] = adc.read_adc(i, gain=GAIN, data_rate=int(freq*4))
#                data[count,i]=np.random.random()
            count=count+1
            if count==int(freq):
                self.dataTreatment_E1.treatData(data[:,0])
                self.dataTreatment_E2.treatData(data[:,1])
                self.dataTreatment_E3.treatData(data[:,2])
                self.dataTreatment_E4.treatData(data[:,3])
                data=np.zeros((int(freq),4))
                count=0

        # Note you can also pass in an optional data_rate parameter that controls
        # the ADC conversion time (in samples/second). Each chip has a different
        # set of allowed data rate values, see datasheet Table 9 config register
        # DR bit values.
        #values[i] = adc.read_adc(i, gain=GAIN, data_rate=128)
        # Each value will be a 12 or 16 bit signed integer value depending on the
        # ADC (ADS1015 = 12-bit, ADS1115 = 16-bit).
#         Print the ADC values.
#            print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*values))
    # Pause for half a second.
#            time.sleep(1/freq)

                
class dataTreatment(QThread):
    sendTreatedData=pyqtSignal(object,object,object,object)
    # emit signal once you want to plot something, that should pass arguments to a function that will just do plot when triggered
        
    def __init__(self,plot_t,plot_f):
        QThread.__init__(self)
        self.plot_t=plot_t
        self.plot_f=plot_f
        
    def __del__(self):
        self.wait()
        
    def treatData(self,data):
        self.data=(1000/18139)*(4.096/32767)*data
        self.start()

    def run(self): #### when you wanna start this thread do nameOfThread.start()
        # data treatment
        y_f=20*np.log10(np.abs(np.fft.rfft(self.data)))
        #send data
        self.sendTreatedData.emit(self.data,y_f,self.plot_t,self.plot_f)
        


def main():
    app = QtWidgets.QApplication(sys.argv)
    wndw = App()
    wndw.show()
    app.exec()


if __name__ == '__main__':
    main()
