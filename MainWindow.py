import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot 
from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction, QBoxLayout, QFormLayout, QGroupBox, QLabel, QListWidget, QMessageBox, QWidget,QLineEdit,QCheckBox,QRadioButton,QMainWindow,QVBoxLayout,QHBoxLayout,QGridLayout,QPushButton,QApplication,QFileDialog,QGroupBox,QButtonGroup,QToolBar
from PyQt5.QtCore import QFile, QLine, QRunnable, Qt,QSize,QThread,QThreadPool,QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon,QPixmap
import sys
import datetime
import json
import os
import pandas as pd
import numpy as np
import itertools



class WorkerSignal(QObject):
    """
    Defines the signals available from a running worker thread. 
    
    """
    finished = pyqtSignal()
    unsupported_type = pyqtSignal(str)



class Worker(QRunnable):
    def __init__(self,file_list,mode,command_dict):
        super().__init__()
        self.signals = WorkerSignal()
        self.file_list = file_list
        self.mode = mode
        self.command_dict = command_dict
        #self.window = window

    @pyqtSlot()
    def run(self):
        """
        Initialize runner with passed self.args and self.kwargs
        """
        print('worker running!')

        if len(self.file_list):

            if self.mode == "Dimensional to Dimensionless":
                for file_name in self.file_list:
                    if os.path.splitext(file_name)[1] == '.csv':
                        df = pd.read_csv(file_name)
                        df.iloc[:,0] = 96485/(8.134*298)*(df.iloc[:,0]-self.command_dict['E0f'])
                        df.iloc[:,1] = df.iloc[:,1] / (96485*2*np.pi*self.command_dict['dElectrode']*self.command_dict['concT']*self.command_dict['DX'])
                        df.to_csv(f'{os.path.splitext(file_name)[0]}-Dimensionless{os.path.splitext(file_name)[1]}',index=False)

                    elif os.path.splitext(file_name)[1] == '.xlsx' or os.path.splitext(file_name)[1] == '.xls' :
                        xl = pd.ExcelFile(file_name)
                        processed_df_dict = {}
                        for sheet_name in xl.sheet_names:
                            df = pd.read_excel(file_name,sheet_name=sheet_name)
                            df.iloc[:,0] = 96485/(8.134*298)*(df.iloc[:,0]-self.command_dict['E0f'])
                            df.iloc[:,1] = df.iloc[:,1] / (96485*2*np.pi*self.command_dict['dElectrode']*self.command_dict['concT']*self.command_dict['DX'])
                            processed_df_dict[sheet_name] = df

                        with pd.ExcelWriter(f'{os.path.splitext(file_name)[0]}-Dimensionless{os.path.splitext(file_name)[1]}') as writer:
                            for sheet_name,df in processed_df_dict.items():
                                df.to_excel(writer,sheet_name=sheet_name,index=False)
                            

                    else:
                        self.signals.unsupported_type.emit(file_name)
                        print(f'{os.path.splitext(file_name)[1]} is not supported for conversion.')

            elif self.mode == "Dimensionless to Dimensional":
                for file_name in self.file_list:
                    if os.path.splitext(file_name)[1] == '.csv':
                        df = pd.read_csv(file_name)
                        df.iloc[:,0] = (8.134*298/96485)*df.iloc[:,0] + self.command_dict['E0f']
                        df.iloc[:,1] = df.iloc[:,1] * (96485*2*np.pi*self.command_dict['dElectrode']*self.command_dict['concT']*self.command_dict['DX'])
                        df.to_csv(f'{os.path.splitext(file_name)[0]}-Dimensional{os.path.splitext(file_name)[1]}',index=False)

                    elif os.path.splitext(file_name)[1] == '.xlsx' or os.path.splitext(file_name)[1] == '.xls' :
                        xl = pd.ExcelFile(file_name)
                        processed_df_dict = {}
                        for sheet_name in xl.sheet_names:
                            df = pd.read_excel(file_name,sheet_name=sheet_name)
                            df.iloc[:,0] = (8.134*298/96485)*df.iloc[:,0] + self.command_dict['E0f']
                            df.iloc[:,1] = df.iloc[:,1] * (96485*2*np.pi*self.command_dict['dElectrode']*self.command_dict['concT']*self.command_dict['DX'])
                            processed_df_dict[sheet_name] = df

                        with pd.ExcelWriter(f'{os.path.splitext(file_name)[0]}-Dimensional{os.path.splitext(file_name)[1]}') as writer:
                            for sheet_name,df in processed_df_dict.items():
                                df.to_excel(writer,sheet_name=sheet_name,index=False)

                    else:
                        self.signals.unsupported_type.emit(file_name)
                        print(f'{os.path.splitext(file_name)[1]} is not supported for conversion.')

        # Emit signal when work completed
        self.signals.finished.emit()




class LabelInput(QHBoxLayout):
    def __init__(self,label='',input_class = QLineEdit,input_var = None,input_args = None,label_args = None,**kwargs):
        super().__init__(**kwargs)
        input_args = input_args or {}
        label_args = label_args or {}
        self.variable = input_var
        self.input_class = input_class

        if input_class in (QCheckBox,QPushButton,QRadioButton):
            raise TypeError

        if input_class in (QLineEdit,):
            self.label = QLabel()
            self.input = QLineEdit()
            self.addWidget(self.label)
            self.addWidget(self.input)
            self.label.setText(label)

        if input_class in (QFileDialog,):
            self.label = QPushButton(label)
            self.addWidget(self.label)
            self.label.clicked.connect(self.openFileNamesDialog)

        def get():
            if self.input_class == QFileDialog:
                return self.variable

    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self.parent().parent(),"QFileDialog.getOpenFileNames()", "","All Files (*);;Excel File (*.xls | *xlsx);;CSV File (*.csv)", options=options)
        if files:
            print(files)
            self.variable = files
            self.parent().parent().parent().updateList()


class GraphWindow(QWidget):
    """
    This "window" is a Qwidget. It it has no parent, it will be a free floating window. 
    
    """


    def __init__(self):
        super().__init__()
        
        self.graphWidget = PlotWidget(self)
        self.layout = QVBoxLayout() 
        self.resize(500,400)
        self.graphWidget.resize(400,300)
        self.layout.addWidget(self.graphWidget)



        self.setLayout(self.layout)

        self.styles = {'color':'k','font-size':'20pt'}

        self.colorCycle =  itertools.cycle([u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf'])
        self.setWindowTitle('Voltammogram Graph')
        self.setWindowIcon(QIcon('./Icons/CV-icon.png'))

        
        




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()


        # The commands and parameters to passed to the conversion tool to convert from dimensional to dimensionless and vice versa
        self.commands = {}


        self.createFormGroupBox()
        self.fileLabelInput = LabelInput(label='Select File(s)',input_class=QFileDialog)
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.onFileListDoubleClicked)
        self.model_group_layout = QHBoxLayout()
        self.model_group = QButtonGroup()
        dim_to_dimless = QRadioButton('Dimensional to Dimensionless')
        dimless_to_dim = QRadioButton('Dimensionless to Dimensional')
        self.model_group.addButton(dim_to_dimless,id=1)
        self.model_group.addButton(dimless_to_dim,id=2)
        self.model_group.buttonClicked[int].connect(self.onMmodelButtonClicked)
        self.model_group_layout.addWidget(dim_to_dimless)
        self.model_group_layout.addWidget(dimless_to_dim)

        self.mainlayout = QVBoxLayout()
        self.mainlayout.addLayout(self.model_group_layout)

        self.mainlayout.addWidget(self.formGroupBox)


        self.mainlayout.addLayout(self.fileLabelInput)
        self.mainlayout.addWidget(self.file_list)
        button_start_conversion = QPushButton('Start Conversion')
        button_start_conversion.clicked.connect(self.getCommands)
        button_start_conversion.clicked.connect(self.saveCommands)
        button_start_conversion.clicked.connect(self.onStartConversion)

        self.mainlayout.addWidget(button_start_conversion)



        self.widget = QWidget()
        self.widget.setLayout(self.mainlayout)
        self.setCentralWidget(self.widget)
        self.setWindowIcon(QIcon('./Icons/CV-icon.png'))
        self.setWindowTitle('Voltammogram Dimension Conversion Tool')

        button_action = QAction(QIcon('./Icons/ScreenShotIcon.png'),'&ScreenShot',self)
        button_action.triggered.connect(self.onScreenShot)
        button_action2 = QAction(QIcon('./Icons/ChemistIcon.png'),'&Authors',self)
        button_action2.triggered.connect(self.onAuthors)
        button_action3 = QAction(QIcon('./Icons/ClearIcon.png'),'&Clear Inputs',self)
        button_action3.triggered.connect(self.clearCommands)

        menu = self.menuBar()
        file_menu = menu.addMenu('&File')
        file_menu.addAction(button_action)
        file_menu.addAction(button_action3)
        edit_menu = menu.addMenu('&Edit')
        about_menu = menu.addMenu('&About')
        about_menu.addAction(button_action2)


        self.graphWindow = None


        self.loadCommands()



    def onFileListDoubleClicked(self,item):
        selectedFile = item.text()

        if self.graphWindow is None or isinstance(self.graphWindow,GraphWindow):
            self.graphWindow = GraphWindow()
            self.graphWindow.graphWidget.setBackground('w')
            
            if os.path.splitext(selectedFile)[1] == '.csv':
                df = pd.read_csv(selectedFile)


                pen = pg.mkPen(width=5,color=(0,0,0))
                self.graphWindow.graphWidget.plot(df.iloc[:,0],df.iloc[:,1],pen=pen)
                self.graphWindow.graphWidget.setLabel('left','Flux',**self.graphWindow.styles)
                self.graphWindow.graphWidget.setLabel('bottom','Potential',**self.graphWindow.styles)
                self.graphWindow.graphWidget.setTitle('Preview of Voltammogram',**self.graphWindow.styles)
                self.graphWindow.graphWidget.showGrid(x=True,y=True)
            elif os.path.splitext(selectedFile)[1] =='.xls' or os.path.splitext(selectedFile)[1] =='.xlsx': 
                df_dict = pd.read_excel(selectedFile,sheet_name=None)
                # add legend
                self.graphWindow.graphWidget.addLegend()
                for key,df in df_dict.items():
                    pen = pg.mkPen(width=5,color=next(self.graphWindow.colorCycle))
                    self.graphWindow.graphWidget.plot(df.iloc[:,0],df.iloc[:,1],pen=pen,name=key)
                
                self.graphWindow.graphWidget.setLabel('left','Flux',**self.graphWindow.styles)
                self.graphWindow.graphWidget.setLabel('bottom','Potential',**self.graphWindow.styles)
                self.graphWindow.graphWidget.setTitle('Preview of Voltammogram',**self.graphWindow.styles)
                self.graphWindow.graphWidget.showGrid(x=True,y=True)




        self.graphWindow.show()

        

    def onMmodelButtonClicked(self,id):
        for button in self.model_group.buttons():
            if button is self.model_group.button(id):
                print(id,button.text() + " Was Clicked ")




    def onScreenShot(self):
        screen = QApplication.primaryScreen()
        screen = screen.grabWindow(self.winId())
        screen.save(f"screenshot-{datetime.datetime.now().strftime(r'%Y-%m-%d %H%M%S')}.jpg",'jpg')
        print('Save screenshot success!')


    def onAuthors(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle('About Authors')
        dlg.setText('GUI and Simulation: Haotian Chen, haotian.chen@lmh.ox.ac.uk\n\nGeneral Enquiry: Professor Richard Compton, richard.compton@chem.ox.ac.uk\n\nWe would like to hear your experience!')
        button = dlg.exec_()


    def createFormGroupBox(self):
        self.formGroupBox = QGroupBox('Input Parameters')
        layout = QFormLayout()
        self.input_widgets_dict  = {}
        for i in range(7):
            self.input_widgets_dict[i] = QLineEdit()

        layout.addRow(QLabel('Formal Potential of A/B couple, V'),self.input_widgets_dict[0])
        layout.addRow(QLabel('Bulk concentration of X,\nbefore chemical equilibrium, M'),self.input_widgets_dict[1])
        layout.addRow(QLabel('Radius of Electrode, m'),self.input_widgets_dict[2])
        layout.addRow(QLabel(r'Diffusion coefficient of X, m<sup>2</sup>s<sup>-1</sup>'),self.input_widgets_dict[3])
        layout.addRow(QLabel(r'Diffusion coefficient of A, m<sup>2</sup>s<sup>-1</sup>'),self.input_widgets_dict[4])
        layout.addRow(QLabel(r'Diffusion coefficient of B, m<sup>2</sup>s<sup>-1</sup>'),self.input_widgets_dict[5])
        layout.addRow(QLabel(r'Diffusion coefficient of C, m<sup>2</sup>s<sup>-1</sup>'),self.input_widgets_dict[6])
        self.formGroupBox.setLayout(layout)



    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            print(fileName)
    
    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","All Files (*);;Python Files (*.py)", options=options)
        if files:
            print(files)
    
    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            print(fileName)

    def updateList(self):
        self.file_list.addItems(self.fileLabelInput.variable)


    def onStartConversion(self):
        file_list = [str(self.file_list.item(i).text()) for i in range(self.file_list.count())]
        file_list = list(set(file_list))
        mode = self.model_group.checkedButton().text()
        worker = Worker(file_list = file_list,mode=mode,command_dict=self.commands)
        worker.signals.finished.connect(self.workerFinished)
        worker.signals.unsupported_type.connect(self.unsupportedFileType)
        print(file_list,self.model_group.checkedButton().text())

        self.threadpool = QThreadPool()
        self.threadpool.start(worker)

    def workerFinished(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle('Conversion Complete')
        dlg.setText('Congratulations!\nConversion successfully completed!')
        dlg.setIcon(QMessageBox.Information)
        button = dlg.exec_()

    def unsupportedFileType(self,s):
        dlg = QMessageBox(self)
        dlg.setWindowTitle('Unsupported File Type')
        dlg.setText(f'{s} has an unsupported data type {os.path.splitext(s)[1]} ')
        dlg.setIcon(QMessageBox.Warning)
        button = dlg.exec_()



    def getCommands(self):
        self.commands['E0f'] = float(self.input_widgets_dict[0].text())
        self.commands['concT'] = float(self.input_widgets_dict[1].text())
        self.commands['dElectrode'] = float(self.input_widgets_dict[2].text())
        self.commands['DX'] = float(self.input_widgets_dict[3].text())
        self.commands['DA'] = float(self.input_widgets_dict[4].text())
        self.commands['DB'] = float(self.input_widgets_dict[5].text())
        self.commands['DC'] = float(self.input_widgets_dict[5].text())


    def clearCommands(self):
        for index, item in self.input_widgets_dict.items():
            item.setText('')


    def HELLO(self):
        print('Hello World')


    def saveCommands(self):
        with open('Commands.json','w') as json_writer:
            json.dump(self.commands,json_writer)

    def loadCommands(self):
        if os.path.exists('Commands.json'):
            with open('Commands.json','r') as json_reader:
                self.commands = json.load(json_reader)

        self.input_widgets_dict[0].setText(f"{self.commands['E0f']:.5f}")
        self.input_widgets_dict[1].setText(f"{self.commands['concT']:.5E}")
        self.input_widgets_dict[2].setText(f"{self.commands['dElectrode']:.5E}")
        self.input_widgets_dict[3].setText(f"{self.commands['DX']:.5E}")
        self.input_widgets_dict[4].setText(f"{self.commands['DA']:.5E}")
        self.input_widgets_dict[5].setText(f"{self.commands['DB']:.5E}")
        self.input_widgets_dict[6].setText(f"{self.commands['DC']:.5E}")

if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec_()