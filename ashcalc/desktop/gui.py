'''
Created on 15 Aug 2013

@author: Matthew Daggitt
'''

from copy import deepcopy
import math

import tkinter
from tkinter import Canvas, StringVar, IntVar, messagebox, PhotoImage
from tkinter.ttk import Separator, Notebook, LabelFrame, Frame, Button, Label, Entry, Radiobutton, Combobox, Progressbar, Checkbutton, Scrollbar
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas, NavigationToolbar2TkAgg as NavigationToolbar
from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
np.seterr(all="ignore")

from core.isopach import Isopach
from core.model_exp import exponentialModelAnalysis, calculateExponentialSegmentVolume
from core.model_pow import powerLawModelAnalysis, calculatePowerLawVolume
from core.model_wei import weibullModelAnalysis, calculateWeibullVolume, calculateTheta
from core import regression_methods
from desktop.thread_handlers import ThreadHandler
from desktop.timingModule import createWeibullTimingEstimationFunction
from desktop.tooltip import createToolTip

###########Config###########

EXP_DEFAULT_NUMBER_OF_SEGMENTS = 2
EXP_MAX_NUMBER_OF_SEGMENTS = 5

POW_DEFAULT_PROXIMAL_LIMIT = 1.0
POW_DEFAULT_DISTAL_LIMIT = 300

WEI_DEFAULT_NUMBER_OF_RUNS = 20
WEI_DEFAULT_ITERATIONS_PER_RUN = 1000
WEI_DEFAULT_LAMBDA_LOWER_BOUND = 0.0
WEI_DEFAULT_LAMBDA_UPPER_BOUND = 1000
WEI_DEFAULT_K_LOWER_BOUND = 0.0
WEI_DEFAULT_K_UPPER_BOUND = 2.0

MINIMUM_NUMBER_OF_ISOPACHS = 2
DEFAULT_NUMBER_OF_ISOPACHS = 6

MODEL_PLOTTING_PRECISION = 100

ERROR_SURFACE_MAX_RESOLUTION = 100
ERROR_SURFACE_MIN_RESOLUTION = 5
ERROR_SURFACE_DEFAULT_RESOLUTION = 50

NUMBER_OF_SF = 6

colours = ["blue","green","red","cyan","magenta"]

############################

#########Constants##########

EXP = 0
POW = 1
WEI = 2

SQRT_PI = math.sqrt(math.pi)

############################

######### Current ##########

sqrtAreaUsed = True

############################

######### Themes ###########

desiredOrder = ["aqua","vista","xpnative","clam"]

for theme in desiredOrder:
    if theme in tkinter.ttk.Style().theme_names():
        tkinter.ttk.Style().theme_use(theme)
        break

############################

class App(Frame):
    
    def __init__(self):
        Frame.__init__(self)
        self.master.title("AshCalc")
        
        self.threadHandler = ThreadHandler()
        self.calculating = False
        self.weibullTimingEstimationFunction = createWeibullTimingEstimationFunction()
        
        self.calculationFrame = CalculationFrame(self)
        self.calculationFrame.grid(row=0,column=0,sticky="NSW",padx=(10,5),pady=10)
        self.calculationFrame.startCalculationB.bind("<Button-1>",self.startCalculation)
        self.calculationFrame.endCalculationB.configure(state=tkinter.DISABLED)
                
        self.optionsFrame = OptionsFrame(self)
        self.optionsFrame.grid(row=0,column=1,sticky="NESW",padx=(5,10),pady=10)
        self.optionsSelection = IntVar()
        self.optionsFrame.ventDistance_Rb.configure(command=self.changeOptionsSelection,variable=self.optionsSelection)
        self.optionsFrame.sqrtArea_Rb.configure(command=self.changeOptionsSelection,variable=self.optionsSelection)
        
        self.isopachEntryFrame = IsopachEntryFrame(self,self.estimateWeibullCalculationTime)
        self.isopachEntryFrame.grid(row=1,column=0,columnspan=2,padx=10,sticky="NS",pady=10)
        
        self.modelEntryFrame = ModelEntryFrame(self)
        self.modelEntryFrame.grid(row=0,column=2,sticky="NESW",padx=10,pady=10)
        self.modelEntryFrame.weiNumberOfRuns_E.bind("<KeyRelease>",self.estimateWeibullCalculationTime)
        self.modelEntryFrame.weiIterationsPerRun_E.bind("<KeyRelease>",self.estimateWeibullCalculationTime)
        self.estimateWeibullCalculationTime(None)
        
        self.resultsFrame = ResultsFrame(self)
        self.resultsFrame.grid(row=1,column=2,padx=10,sticky="N",pady=10)
        
        #self.isopachEntryFrame.loadData([Isopach(0.4,16.25),Isopach(0.2,30.63),Isopach(0.1,58.87),Isopach(0.05,95.75),Isopach(0.02,181.56),Isopach(0.01,275.1)])

        self.pack()
        self.mainloop()
        
    def startCalculation(self, event):
        try:
            isopachs = self.isopachEntryFrame.getData()
            modelDetails = self.modelEntryFrame.getModelDetails()
            
            if modelDetails[0] == EXP:
                _, numberOfSegments = modelDetails
                self.threadHandler.startCalculation(exponentialModelAnalysis,[isopachs,numberOfSegments],EXP)
            elif modelDetails[0] == POW:
                _, proximalLimitKM, distalLimitKM = modelDetails
                self.threadHandler.startCalculation(powerLawModelAnalysis,[isopachs,proximalLimitKM,distalLimitKM],POW)
            elif modelDetails[0] == WEI:
                _, numberOfRuns, iterationsPerRun, limits = modelDetails
                self.threadHandler.startCalculation(weibullModelAnalysis,[isopachs,numberOfRuns,iterationsPerRun,limits],WEI)
        except ValueError as ve:
            messagebox.showerror("Calculation error", ve.args[0])
            return
        
        self.calculationFrame.calculationPB.start(interval=3)
        self.calculationFrame.startCalculationB.configure(state=tkinter.DISABLED)
        self.calculationFrame.startCalculationB.unbind("<Button-1>")
        self.calculationFrame.endCalculationB.configure(state=tkinter.ACTIVE)
        self.calculationFrame.endCalculationB.bind("<Button-1>",self.finishCalculation)
        
        self.calculating = True
        self.poll()
            
    def finishCalculation(self,_):
        self.threadHandler.cancelLastCalculation()
        self.calculating = False
        self.calculationFrame.startCalculationB.configure(state=tkinter.ACTIVE)
        self.calculationFrame.startCalculationB.bind("<Button-1>",self.startCalculation)
        self.calculationFrame.endCalculationB.configure(state=tkinter.DISABLED)
        self.calculationFrame.endCalculationB.unbind("<Button-1>")
        self.calculationFrame.calculationPB.stop()
        
    def poll(self):
        result = self.threadHandler.getCurrentCalculationResult()
        if result is not None:
            modelType, resultsDict = result
            if modelType == "Error":
                messagebox.showerror("Calculation error", resultsDict.args[0])
            else:
                self.resultsFrame.displayResults(modelType,resultsDict)
            self.finishCalculation(None)
        elif self.calculating:
            self.after(100, self.poll)
    
    def estimateWeibullCalculationTime(self,event):
        try:
            numberOfIsopachs = self.isopachEntryFrame.getNumberOfIncludedIsopachs()
            numberOfRuns = int(self.modelEntryFrame.weiNumberOfRuns_E.get())
            iterationsPerRun = int(self.modelEntryFrame.weiIterationsPerRun_E.get())
            if numberOfRuns <= 0 or iterationsPerRun <= 0 or numberOfIsopachs <= 0:
                raise ValueError()
            est = self.weibullTimingEstimationFunction(numberOfIsopachs,iterationsPerRun,numberOfRuns)
            self.modelEntryFrame.weiEstimatedTime_E.insertNew(roundToSF(est,2))
        except ValueError:
            self.modelEntryFrame.weiEstimatedTime_E.insertNew("N/A")

    def changeOptionsSelection(self):
        global sqrtAreaUsed
        
        value = self.optionsSelection.get()
        if (value == 1 and sqrtAreaUsed) or (value == 0 and not sqrtAreaUsed):
            if self.resultsFrame.modelType is not None:
                message = "Are you sure you want to change the unit of measurement?\nWarning: The current calculation will be lost."
                result = messagebox.askquestion("Change x variable", message , icon='warning')
            else:
                result = "yes"
                
            if result == "yes":
                sqrtAreaUsed = not sqrtAreaUsed
                self.resultsFrame.clear()
            else:
                self.optionsSelection.set(1-value)
                
class CalculationFrame(LabelFrame):
    
    def __init__(self,parent):
        LabelFrame.__init__(self,parent,text="Calculate",borderwidth=5)       
         
        self.startCalculationB = Button(self,text="Start calculation",width=20)
        self.startCalculationB.grid(row=0,column=0,padx=10,pady=5)
        self.endCalculationB = Button(self,text="Cancel calculation",width=20)
        self.endCalculationB.grid(row=1,column=0,padx=10,pady=5)
        self.calculationPB = Progressbar(self, mode="indeterminate",length=128)
        self.calculationPB.grid(row=2,column=0,padx=10,pady=5)

class OptionsFrame(LabelFrame):
    
    def __init__(self,parent):
        LabelFrame.__init__(self,parent,text="Options")
        
        self.textLabel = Label(self,text="For x in \u222BxT(x)dx:")
        self.textLabel.grid(row=0,column=0,padx=10,pady=(8,5),sticky="W")
        self.sqrtArea_Rb = Radiobutton(self,text="use \u221AArea",value=0)
        self.sqrtArea_Rb.grid(row=1,column=0,sticky="W",padx=10,pady=5)
        self.ventDistance_Rb = Radiobutton(self,text="use Vent Distance",value=1)
        self.ventDistance_Rb.grid(row=2,column=0,sticky="W",padx=10,pady=5)
        createToolTip(self.sqrtArea_Rb,"The standard unit for x in the literature for the integral above.")
        createToolTip(self.ventDistance_Rb,"An alternative unit for x for the integral above. It has the\nadvantage of the x-axes of graphs being measured in km\nfrom the vent and hence allows you to immediately read off\nwhere changes in thickness occur. The volume estimates are\nindependent of the unit used.\n\nSee the instruction manual for further details.")
        
class IsopachEntryFrame(LabelFrame):
    
    def __init__(self,parent,calculationTimeEstimationFunction):
        
        LabelFrame.__init__(self,parent,text="Isopachs",borderwidth=5)
        self.numberOfIsopachs = DEFAULT_NUMBER_OF_ISOPACHS
        self.calculationTimeEstimationFunction = calculationTimeEstimationFunction
        
        self.buttonWidth = 14
        
        photo = PhotoImage(file="open_file-icon.gif")
        self.loadFromFileButton = Button(self,image=photo)
        self.loadFromFileButton.grid(row=0,column=0,padx=10,pady=10)
        self.loadFromFileButton.bind("<Button-1>",self.loadFromFile)
        self.loadFromFileButton.image = photo
        
        self.addButton = Button(self,text="Add isopach",width=self.buttonWidth)
        self.addButton.grid(row=0,column=1,padx=10,pady=10)
        self.addButton.bind("<Button-1>",self.addIsopach)
        self.removeButton = Button(self,text="Remove isopach",width=self.buttonWidth)
        self.removeButton.grid(row=0,column=2,padx=10,pady=10)
        self.removeButton.bind("<Button-1>",self.removeIsopach)
        
        createToolTip(self.loadFromFileButton,"Load isopach data from a comma seperated value file of the form: \n\n\tthickness1,\u221AArea1\n\tthickness2,\u221AArea2\n\t...\n\nwith thickness in metres and \u221AArea in kilometres")
        
        scrollFrame = ScrollFrame(self,width=300,height=400)
        scrollFrame.grid(row=1,column=0,columnspan=3)
        self.innerFrame = scrollFrame.innerFrame
        
        self.rows = [self.createRow(i) for i in range(self.numberOfIsopachs)]
        
        thicknessM_L = Label(self.innerFrame, text="Thickness (m)")
        thicknessM_L.grid(column=1, row=1, padx=5, pady=5)
        sqrtAreaKM_L = Label(self.innerFrame, text="\u221AArea (km)")
        sqrtAreaKM_L.grid(column=2, row=1, padx=5, pady=5)
        include_L = Label(self.innerFrame, text="Include?")
        include_L.grid(column=3, row=1, padx=5, pady=5)
        
    def createRow(self,rowNumber):
        isopach_L = Label(self.innerFrame, text="Isopach " + str(rowNumber+1))
        isopach_L.grid(column=0, row=rowNumber+2, padx=10, pady=5)
        
        thicknessVar = StringVar()
        thicknessM_E = Entry(self.innerFrame,width=10,textvariable=thicknessVar)
        thicknessM_E.grid(column=1, row=rowNumber+2, pady=5)
        #thicknessM_E.insert(0,rowNumber+1)
        
        areaVar = StringVar()
        sqrtAreaKM_E = Entry(self.innerFrame,width=10,textvariable=areaVar)
        sqrtAreaKM_E.grid(column=2, row=rowNumber+2, pady=5)
        #sqrtAreaKM_E.insert(0,2*math.log(math.sqrt(rowNumber+2)))
        
        includeVar = IntVar()
        includeCB = Checkbutton(self.innerFrame,variable=includeVar)
        includeCB.grid(column=3,row=rowNumber+2,pady=5)
        includeCB.invoke()
        includeCB.bind("<Leave>",self.calculationTimeEstimationFunction)
        
        return (isopach_L,None),(thicknessM_E,thicknessVar),(sqrtAreaKM_E,areaVar),(includeCB,includeVar)
    
    def addIsopach(self,event):
        row = self.createRow(self.numberOfIsopachs)
        self.rows.append(row)
        self.numberOfIsopachs += 1
        self.calculationTimeEstimationFunction(None)
        
    def removeIsopach(self,event):
        if self.numberOfIsopachs > MINIMUM_NUMBER_OF_ISOPACHS:
            row = self.rows[-1]
            for wg,_ in row:
                wg.grid_remove()
            self.numberOfIsopachs -= 1
            self.rows = self.rows[:self.numberOfIsopachs]
            self.calculationTimeEstimationFunction(None)
    
    def getData(self):
        values = [(thicknessVar.get(),sqrtAreaVar.get(),includeVar.get()) for (_,_),(_,thicknessVar),(_,sqrtAreaVar),(_,includeVar) in self.rows]
        isopachs = []
        for index, (thicknessStr, sqrtAreaStr, includeInt) in enumerate(values):
            if includeInt == 1:
                thicknessM = validateValue(thicknessStr,
                                           "Isopach " + str(index+1) + "'s thickness must be a strictly positive number",
                                           "float",
                                           strictLowerBound=0)
                sqrtAreaKM = validateValue(sqrtAreaStr,
                                        "Isopach " + str(index+1) + "'s area must be a strictly positive number",
                                        "float",
                                        strictLowerBound=0)
                isopachs.append(Isopach(thicknessM,sqrtAreaKM))
        isopachs = sorted(isopachs, key=lambda i : i.thicknessM, reverse=True)
        
        for i in range(len(isopachs)-1):
            if isopachs[i].thicknessM == isopachs[i+1].thicknessM:
                raise ValueError("Isopachs must all have unique thicknesses")
        
        return isopachs
    
    def loadData(self,isopachs):
        n = len(isopachs)
        current = len(self.rows)
        difference = n-current
        if difference < 0:
            for _ in range(-difference):
                self.removeIsopach(None)
        elif difference > 0:
            for _ in range(difference):
                self.addIsopach(None)
                
        for row, isopach in zip(self.rows,isopachs):
            row[1][1].set(isopach.thicknessM)
            row[2][1].set(isopach.sqrtAreaKM)
            row[3][1].set(1)
            
    def getNumberOfIncludedIsopachs(self):
        return len([None for _,_,_,(_,includeVar) in self.rows if includeVar.get() == 1])
    
    def loadFromFile(self,event):
        fileName = filedialog.askopenfilename();
        
        if fileName is None or fileName == "":
            return;
        
        try:
            file = open(fileName, "r")
        except FileNotFoundError:
            messagebox.showerror("Could not find file:\n\n\\t\"" + fileName.replace("\n","") + "\"")
            return
        
        isopachs = []
        success = True
        
        try:
            for index, line in enumerate(file):
                try:
                    thicknessM, sqrtAreaKM = line.split(',')
                    line = line.replace(" ","")
                    isopachs.append(Isopach(float(thicknessM), float(sqrtAreaKM)))
                except (ValueError, UnicodeDecodeError):
                    messagebox.showerror("File format error", "Line " + str(index+1) + " of the file \n\n\t\"" + 
                                         line.replace("\n","") + "\"\n\nis not in the format of 'thickness (M),\u221Aarea (KM)'")
                    success = False
                    break
        except:
            messagebox.showerror("File format error", "The file\n\n" + fileName + "\n\nis not in the format of 'thickness (M),\u221Aarea (KM)'")
            success = False
            
        if success:
            self.loadData(isopachs)
            
class ModelEntryFrame(LabelFrame):
    
    def __init__(self,parent):
        
        LabelFrame.__init__(self,parent,text="Model",borderwidth=5)
        
        self.selection = tkinter.IntVar()
        
        self.exponential = Radiobutton(self,text="Exponential model",variable=self.selection,value=EXP,command=self.changeSelection)
        self.exponential.grid(row=0,column=0,sticky="W",padx=10,pady=5)
        self.powerlaw = Radiobutton(self,text="Power law model",variable=self.selection,value=POW,command=self.changeSelection)
        self.powerlaw.grid(row=1,column=0,sticky="W",padx=10,pady=5)
        self.weibull = Radiobutton(self,text="Weibull model",variable=self.selection,value=WEI,command=self.changeSelection)
        self.weibull.grid(row=2,column=0,sticky="W",padx=10,pady=5)
        
        seperator = Separator(self,orient=tkinter.VERTICAL)
        seperator.grid(row=0, column=1, rowspan=3, sticky="NS", padx=(20,10))
        
        self.expNumberOfSegments_L = Label(self,text="Number of segments: ")
        self.expNumberOfSegments_E = Entry(self,width=5)
        self.expNumberOfSegments_E.insert(0, EXP_DEFAULT_NUMBER_OF_SEGMENTS)
        self.expWidgets = [self.expNumberOfSegments_L,self.expNumberOfSegments_E]
        
        self.powProximalLimit_L = Label(self,text="Proximal limit of integration: ")
        self.powProximalLimit_E = Entry(self,width=5)
        self.powProximalLimit_E.insert(0, POW_DEFAULT_PROXIMAL_LIMIT)
        self.powDistalLimit_L = Label(self,text="Distal limit of integration: ")
        self.powDistalLimit_E = Entry(self,width=5)
        self.powDistalLimit_E.insert(0, POW_DEFAULT_DISTAL_LIMIT)
        self.powWidgets = [self.powProximalLimit_L,self.powProximalLimit_E,
                           self.powDistalLimit_L,self.powDistalLimit_E]
        
        self.weiNumberOfRuns_L = Label(self,text="Number of runs: ")
        self.weiNumberOfRuns_E = Entry(self,width=5)
        self.weiNumberOfRuns_E.insert(0, WEI_DEFAULT_NUMBER_OF_RUNS)
        self.weiIterationsPerRun_L = Label(self,text="Iterations per run: ")
        self.weiIterationsPerRun_E = Entry(self,width=5)
        self.weiIterationsPerRun_E.insert(0, WEI_DEFAULT_ITERATIONS_PER_RUN)
        self.weiEstimatedTime_L = Label(self,text="Estimated time (s): ")
        self.weiEstimatedTime_E = CustomEntry(self,width=5)
        self.weiEstimatedTime_E.setUserEditable(False)
        self.weiLambdaLowerBoundL = Label(self,text="\u03BB lower bound:")
        self.weiLambdaUpperBoundL = Label(self,text="\u03BB upper bound:")
        self.weiLambdaLowerBoundE = Entry(self,width=5)
        self.weiLambdaLowerBoundE.insert(0, WEI_DEFAULT_LAMBDA_LOWER_BOUND)
        self.weiLambdaUpperBoundE = Entry(self,width=5)
        self.weiLambdaUpperBoundE.insert(0, WEI_DEFAULT_LAMBDA_UPPER_BOUND)
        
        createToolTip(self.weiNumberOfRuns_E,"The number of possible sets of parameters that are generated.\nThe final parameters returned are the set which best fit the data.\n\nSee the instruction manual for further details.");
        createToolTip(self.weiIterationsPerRun_E,"The number of times the current parameters are adjusted\nwithin each run.\n\nSee the instruction manual for further details.");
        createToolTip(self.weiEstimatedTime_E,"A rough estimate of the time required to execute this computation.");
        
        self.weiKLowerBoundL = Label(self,text="k lower bound:")
        self.weiKUpperBoundL = Label(self,text="k upper bound:")
        self.weiKLowerBoundE = Entry(self,width=5)
        self.weiKLowerBoundE.insert(0, WEI_DEFAULT_K_LOWER_BOUND)
        self.weiKUpperBoundE = Entry(self,width=5)
        self.weiKUpperBoundE.insert(0, WEI_DEFAULT_K_UPPER_BOUND)
        
        self.weiWidgets = [self.weiNumberOfRuns_L,self.weiNumberOfRuns_E,
                           self.weiIterationsPerRun_L,self.weiIterationsPerRun_E,
                           self.weiEstimatedTime_L,self.weiEstimatedTime_E,
                           self.weiLambdaLowerBoundL,self.weiLambdaUpperBoundL,self.weiLambdaLowerBoundE,self.weiLambdaUpperBoundE,
                           self.weiKLowerBoundL,self.weiKUpperBoundL,self.weiKLowerBoundE,self.weiKUpperBoundE]
        
        self.currentWidgets = []
        self.changeSelection()
        
    def changeSelection(self):
        
        for widget in self.currentWidgets:
            widget.grid_remove()
            
        value = self.selection.get()
        
        sX = 10
        bX = 20
        
        if value == EXP:
            self.expNumberOfSegments_L.grid(row=0,column=2,padx=(bX,sX),pady=5,sticky="W")
            self.expNumberOfSegments_E.grid(row=0,column=3,padx=(sX,bX),pady=5,sticky="W")
            self.currentWidgets = self.expWidgets
        elif value == POW:
            self.powProximalLimit_L.grid(row=0,column=2,padx=(bX,sX),pady=5,sticky="W")
            self.powProximalLimit_E.grid(row=0,column=3,padx=(sX,bX),pady=5,sticky="W")
            self.powDistalLimit_L.grid(row=1,column=2,padx=(bX,sX),pady=5,sticky="W")
            self.powDistalLimit_E.grid(row=1,column=3,padx=(sX,bX),pady=5,sticky="W")
            self.currentWidgets = self.powWidgets
        elif value == WEI:
            self.weiNumberOfRuns_L.grid(row=0,column=2,padx=(bX,sX),pady=5,sticky="W")
            self.weiNumberOfRuns_E.grid(row=0,column=3,padx=(sX,bX),pady=5,sticky="W")
            self.weiIterationsPerRun_L.grid(row=1,column=2,padx=(bX,sX),pady=5,sticky="W")
            self.weiIterationsPerRun_E.grid(row=1,column=3,padx=(sX,bX),pady=5,sticky="W")
            self.weiEstimatedTime_L.grid(row=2,column=2,padx=(bX,sX),pady=5,sticky="W")
            self.weiEstimatedTime_E.grid(row=2,column=3,padx=(sX,bX),pady=5,sticky="W")
            
            self.weiLambdaLowerBoundL.grid(row=0,column=4,padx=(bX,sX),sticky="W")
            self.weiLambdaLowerBoundE.grid(row=0,column=5,padx=(sX,bX))
            self.weiLambdaUpperBoundL.grid(row=1,column=4,padx=(bX,sX),sticky="W")
            self.weiLambdaUpperBoundE.grid(row=1,column=5,padx=(sX,bX))
            
            self.weiKLowerBoundL.grid(row=0,column=6,padx=(bX,sX),sticky="W")
            self.weiKLowerBoundE.grid(row=0,column=7,padx=(sX,bX))
            self.weiKUpperBoundL.grid(row=1,column=6,padx=(bX,sX),sticky="W")
            self.weiKUpperBoundE.grid(row=1,column=7,padx=(sX,bX))
            
            self.currentWidgets = self.weiWidgets
    
    def getModelDetails(self):
        modelType = self.selection.get()
        values = [modelType]
              
        if modelType == EXP: 
            numberOfSegments = validateValue(self.expNumberOfSegments_E.get(),
                                             "The number of exponential segments must be 1 \u2264 n \u2264 " + str(EXP_MAX_NUMBER_OF_SEGMENTS),
                                             "int",
                                             lowerBound=1,
                                             upperBound=EXP_MAX_NUMBER_OF_SEGMENTS)
            values.append(numberOfSegments)
            
        elif modelType == POW:
            proximalLimitKM = validateValue(self.powProximalLimit_E.get(),
                                            "The proximal limit of integration must be 0 \u2264 x \u2264 \u221E",
                                            "float",
                                            strictLowerBound=0,
                                            strictUpperBound=float('inf'))
            proximalLimitKM /= (SQRT_PI if sqrtAreaUsed else 1)
            
            distalLimitKM = validateValue(self.powDistalLimit_E.get(),
                                          "The distal limit of integration must be prox \u2264 x \u2264 \u221E",
                                          "float",
                                          strictLowerBound=proximalLimitKM,
                                          strictUpperBound=float('inf'))
            distalLimitKM /= (SQRT_PI if sqrtAreaUsed else 1)
            
            values.extend([proximalLimitKM,distalLimitKM])
            
        elif modelType == WEI:
            numberOfRuns = validateValue(self.weiNumberOfRuns_E.get(),
                                         "The number of runs must be greater than 0",
                                         "int",
                                         strictLowerBound=0)
            
            iterationsPerRun = validateValue(self.weiIterationsPerRun_E.get(),
                                             "The number of iterations must be greater than 0",
                                             "int",
                                             strictLowerBound=0)
            
            lambdaLowerBound = validateValue(self.weiLambdaLowerBoundE.get(),
                                             "The lower bound for \u03BB must be a decimal",
                                             "float")
            lambdaLowerBound /= (SQRT_PI if sqrtAreaUsed else 1)
              
            lambdaUpperBound = validateValue(self.weiLambdaUpperBoundE.get(),
                                             "The upper bound for \u03BB must be greater than the lower bound",
                                             "float",
                                             strictLowerBound=lambdaLowerBound)
            lambdaUpperBound /= (SQRT_PI if sqrtAreaUsed else 1)
            
            kLowerBound = validateValue(self.weiKLowerBoundE.get(),
                                        "The lower bound for k must be numeric and less than 2",
                                        "float",
                                        strictUpperBound=2)
                                                
            kUpperBound = validateValue(self.weiKUpperBoundE.get(),
                                        "The upper bound for k must be greater than the lower bound and less than or equal to 2",
                                        "float",
                                        strictLowerBound=kLowerBound,
                                        upperBound=2)
            
            values.extend([numberOfRuns,iterationsPerRun,[[lambdaLowerBound,lambdaUpperBound],[kLowerBound,kUpperBound]]])
        
        return values
    
class ResultsFrame(LabelFrame):
    
    def __init__(self,parent):
        
        LabelFrame.__init__(self,parent)
        
        ##################################### Stats frame #############################################
        
        self.resultsStatsFrame = ResultsStatsFrame(self)
        self.resultsStatsFrame.grid(row=0,column=0,padx=10,pady=5,sticky="NESW")
        self.resultsStatsFrame.calculate_B.bind("<Button-1>",self._parameterChanged)
        self.resultsStatsFrame.reset_B.bind("<Button-1>",self._parameterReset)
        
        def onComboBoxSelect(e):
            self.resultsStatsFrame.currentSegment = e.widget.current()
            self.resultsStatsFrame.expParametersUpdated(self.currentParameters)
            
        self.resultsStatsFrame.expSeg_CB.bind("<<ComboboxSelected>>",onComboBoxSelect)
        
        ###############################################################################################
        
        ##################################### Error frame #############################################
        
        self.errorSurfaceFrame = ErrorSurfaceFrame(self)
        self.errorSurfaceFrame.errorSurfaceB.bind("<Button-1>",self.displayErrorSurface)
        
        ###############################################################################################
        
        ################################## Graph notebook #############################################
        
        self.graphNotebook = ImprovedNotebook(self)
        
        self.modelGraphFrame = GraphFrame(self,dim=2)
        self.modelGraphFrame.axes.set_ylabel(r'$thickness(m)$')
        
        self.regressionGraphFrame = GraphFrame(self,dim=2)
        self.regressionGraphFrame.axes.set_ylabel(r'$\ln{(thickness(m))}$')
        
        self.errorSurfaceGraphFrame = GraphFrame(self,dim=3)
        self.errorSurfaceGraphFrame.axes.set_zlabel(r'$error$')
        
        self.graphNotebook.addFrame(self.modelGraphFrame,text="Model")
        self.graphNotebook.grid(row=0,column=1,padx=10,pady=5)
        
        ##############################################################################################
        
        self.resultsDict = None
        self.modelType = None
    
    def displayResults(self,modelType,resultsDict):
        
        self.modelType = modelType
        
        if modelType == EXP:
            self.currentParameters = {"isopachs":resultsDict["isopachs"],
                                      "numberOfSegments":resultsDict["numberOfSegments"],
                                      "cs":resultsDict["segmentCoefficients"],
                                      "ms":resultsDict["segmentExponents"],
                                      "limits":resultsDict["segmentLimits"]}
            self.resultsStatsFrame.loadExpDisplay(resultsDict["numberOfSegments"])
            
        elif modelType == POW:
            xs = [isopach.sqrtAreaKM/(1 if sqrtAreaUsed else SQRT_PI) for isopach in resultsDict["isopachs"]]
            ys = [isopach.thicknessM for isopach in resultsDict["isopachs"]]
            def errorFunction(c,m):
                thicknessFunction = lambda x : c*(x**(-m))
                return math.log(regression_methods.meanRelativeSquaredError(xs, ys, thicknessFunction))
            self.currentParameters = {"isopachs":resultsDict["isopachs"],
                                      "c":resultsDict["coefficient"],
                                      "m":resultsDict["exponent"],
                                      "distalLimitKM":resultsDict["distalLimitKM"],
                                      "proximalLimitKM":resultsDict["proximalLimitKM"],
                                      "errorFunction":errorFunction,
                                      "suggestedProximalLimit":resultsDict["suggestedProximalLimit"]}
            self.resultsStatsFrame.loadPowDisplay()
            
        elif modelType == WEI:
            xs = np.array([isopach.sqrtAreaKM/(1 if sqrtAreaUsed else SQRT_PI) for isopach in resultsDict["isopachs"]])
            ys = np.array([isopach.thicknessM for isopach in resultsDict["isopachs"]])
            
            def errorFunction(lamb,k):
                theta = calculateTheta(xs,ys,lamb,k)
                def thicknessFunction(x):
                    try:
                        return math.exp(math.log(theta)+(k-2)*math.log(x/lamb)-(x/lamb)**k)
                    except FloatingPointError:
                        return 0
                mrse = regression_methods.meanRelativeSquaredError(xs, ys, thicknessFunction)
                return math.log(mrse)
            
            self.currentParameters = {"isopachs":resultsDict["isopachs"],
                                      "lambda":resultsDict["lambda"],
                                      "k":resultsDict["k"],
                                      "theta":resultsDict["theta"],
                                      "limits":resultsDict["limits"],
                                      "errorFunction":errorFunction}
            self.resultsStatsFrame.loadWeiDisplay()
        
        self.defaultParameters = deepcopy(self.currentParameters)
        self.recalculateAndDisplay()
        
    def recalculateAndDisplay(self):
        
        self.modelGraphFrame.clear()
        self.regressionGraphFrame.clear()
        self.graphNotebook.removeFrame(self.regressionGraphFrame)
        self.graphNotebook.removeFrame(self.errorSurfaceGraphFrame)
        
        thicknessM = [isopach.thicknessM for isopach in self.currentParameters["isopachs"]]
        if sqrtAreaUsed:
            sqrtArea = [isopach.distanceFromVentKM*SQRT_PI for isopach in self.currentParameters["isopachs"]]
            self.modelGraphFrame.plotScatter(sqrtArea,thicknessM,True)
            self.modelGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
        else:
            distanceFromVentKM = [isopach.distanceFromVentKM for isopach in self.currentParameters["isopachs"]]
            self.modelGraphFrame.plotScatter(distanceFromVentKM,thicknessM,True)
            self.modelGraphFrame.axes.set_xlabel(r"$distance$ $from$ $vent$ $(km)$")
        
        if self.modelType == EXP:
            self._updateExp()
        elif self.modelType == POW:
            self._updatePow()
        elif self.modelType == WEI:
            self._updateWei()
        
    def _updateExp(self):
        
        self.resultsStatsFrame.expParametersUpdated(self.currentParameters)
        
        n = self.currentParameters["numberOfSegments"]
        
        self.errorSurfaceFrame.grid_remove()
        
        startOfIsopachs = min(self.currentParameters["isopachs"],key=lambda i:i.distanceFromVentKM).distanceFromVentKM
        endOfIsopachs = max(self.currentParameters["isopachs"],key=lambda i:i.distanceFromVentKM).distanceFromVentKM
        
        logThickness = [math.log(isopach.thicknessM) for isopach in self.currentParameters["isopachs"]]
        if sqrtAreaUsed:
            sqrtArea = [isopach.distanceFromVentKM*SQRT_PI for isopach in self.currentParameters["isopachs"]]
            self.regressionGraphFrame.plotScatter(sqrtArea,logThickness,False)
            self.regressionGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
            startOfIsopachs *= SQRT_PI
            endOfIsopachs *= SQRT_PI
        else:
            distanceFromVentKM = [isopach.distanceFromVentKM for isopach in self.currentParameters["isopachs"]]
            self.regressionGraphFrame.plotScatter(distanceFromVentKM,logThickness,False)
            self.regressionGraphFrame.axes.set_xlabel(r"$distance$ $from$ $vent$ $(km)$")
        
        for i in range(n):
            c, m = self.currentParameters["cs"][i], self.currentParameters["ms"][i]/(SQRT_PI if sqrtAreaUsed else 1)
            
            startX = self.currentParameters["limits"][i]*(SQRT_PI if sqrtAreaUsed else 1)
            endX = (self.currentParameters["limits"][i+1]*(SQRT_PI if sqrtAreaUsed else 1) if i != n-1 else 1.5*(endOfIsopachs-startOfIsopachs)+startOfIsopachs)
            startY = math.log(c)-m*startX
            endY = math.log(c)-m*endX
            color = colours[i]
            xs = getStaggeredPoints(startX,endX,MODEL_PLOTTING_PRECISION)
            ys = [c*math.exp(-x*m) for x in xs]
            self.modelGraphFrame.plotFilledLine(xs, ys, color=color)
            
            self.regressionGraphFrame.plotLine([startX,endX],[startY,endY],color=color)
        
        self.graphNotebook.addFrame(self.regressionGraphFrame,text="Regression")
        self.currentTabs = [self.regressionGraphFrame]
        
    def _updatePow(self):
        
        self.resultsStatsFrame.powParametersUpdated(self.currentParameters)
        
        self.errorSurfaceFrame.grid(row=1,column=0,columnspan=2,padx=10,pady=5,sticky="EW")
        self.errorSurfaceFrame.update("c","m",0.0,5.0,0.0,5.0)
        
        c, m = self.currentParameters["c"], self.currentParameters["m"]
        logThickness = [math.log(isopach.thicknessM) for isopach in self.currentParameters["isopachs"]]
        if sqrtAreaUsed:
            c *= SQRT_PI**m
            sqrtArea = [isopach.distanceFromVentKM*SQRT_PI for isopach in self.currentParameters["isopachs"]]
            self.regressionGraphFrame.plotScatter(sqrtArea,logThickness,False)
            self.regressionGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
        else:
            logDistanceFromVentKM = [math.log(isopach.distanceFromVentKM) for isopach in self.currentParameters["isopachs"]]
            self.regressionGraphFrame.plotScatter(logDistanceFromVentKM,logThickness,False)
            self.regressionGraphFrame.axes.set_xlabel(r" $distance$ $from$  $vent(km)$")
            
        proxLimit = self.currentParameters["proximalLimitKM"]*(SQRT_PI if sqrtAreaUsed else 1)
        distLimit = self.currentParameters["distalLimitKM"]*(SQRT_PI if sqrtAreaUsed else 1)
        xs = getStaggeredPoints(proxLimit,distLimit,MODEL_PLOTTING_PRECISION)
        ys = [np.log(c)-m*np.log(x) for x in xs]
        self.regressionGraphFrame.plotLine(xs,ys,colours[0])
        
        xs = getStaggeredPoints(proxLimit,distLimit,MODEL_PLOTTING_PRECISION)
        ys = [c*(x**(-m)) for x in xs]
        self.modelGraphFrame.plotFilledLine(xs, ys, color=colours[0])
        
        self.graphNotebook.addFrame(self.regressionGraphFrame,text="Regression")
        self.currentTabs = [self.regressionGraphFrame]
            
    def _updateWei(self):
        
        self.resultsStatsFrame.weiParametersUpdated(self.currentParameters)
        
        lamb = self.currentParameters["lambda"]*(SQRT_PI if sqrtAreaUsed else 1)
        k = self.currentParameters["k"]
        theta = self.currentParameters["theta"]
        limits = self.currentParameters["limits"]
        
        self.errorSurfaceFrame.grid(row=1,column=0,columnspan=2,padx=10,pady=5,sticky="EW")
        if sqrtAreaUsed:
            self.errorSurfaceFrame.update("\u03BB", "k", limits[0][0]*SQRT_PI, limits[0][1]*SQRT_PI, limits[1][0], limits[1][1])
        else:
            self.errorSurfaceFrame.update("\u03BB", "k", limits[0][0], limits[0][1], limits[1][0], limits[1][1])
        
        startX = 0
        endX = (self.currentParameters["isopachs"][-1].distanceFromVentKM+50)*(SQRT_PI if sqrtAreaUsed else 1)
        xs = getStaggeredPoints(startX,endX,MODEL_PLOTTING_PRECISION)[1:]
        ys = [theta*((x/lamb)**(k-2))*math.exp(-((x/lamb)**k)) for x in xs]
        self.modelGraphFrame.plotFilledLine(xs, ys, colours[0])
        
    def displayErrorSurface(self,event):
        
        try:
            xLL, xUL, yLL, yUL, resolution = self.errorSurfaceFrame.getSurfaceParameters()
        except ValueError as ve:
            messagebox.showerror("Calculation error", ve.args[0])
            return
        
        self.graphNotebook.addFrame(self.errorSurfaceGraphFrame,text="Error surface")
        if self.errorSurfaceFrame.xSymbol == "\u03BB":
            self.errorSurfaceGraphFrame.axes.set_xlabel("$\lambda$")
        else:
            self.errorSurfaceGraphFrame.axes.set_xlabel(self.errorSurfaceFrame.xSymbol)
        
        self.errorSurfaceGraphFrame.axes.set_ylabel(self.errorSurfaceFrame.ySymbol)
        self.errorSurfaceGraphFrame.clear()
        self.errorSurfaceGraphFrame.plotSurface(self.currentParameters["errorFunction"], xLL, xUL, yLL, yUL, resolution)
        self.graphNotebook.selectFrame(self.errorSurfaceGraphFrame)
    
    def _parameterReset(self,event):
        self.currentParameters = deepcopy(self.defaultParameters)
        self.recalculateAndDisplay()
    
    def _parameterChanged(self,event):
        
        try:
            changedParameters = self.resultsStatsFrame.getParameterValues()
        except ValueError as ve:
            messagebox.showerror("Calculation error", ve.args[0])
            return

        if self.modelType == EXP:
            i = changedParameters["segmentNumber"]
            self.currentParameters["cs"][i] = changedParameters["c"]
            self.currentParameters["ms"][i] = changedParameters["m"]
            self.currentParameters["limits"][i] = changedParameters["segStart"]
            self.currentParameters["limits"][i+1] = changedParameters["segEnd"]
        elif self.modelType == POW:
            self.currentParameters["c"] = changedParameters["c"]
            self.currentParameters["m"] = changedParameters["m"]
        elif self.modelType == WEI:
            self.currentParameters["lambda"] = changedParameters["lambda"]
            self.currentParameters["k"] = changedParameters["k"]
            self.currentParameters["theta"] = changedParameters["theta"]

        self.recalculateAndDisplay()
    
    def clear(self):
        self.modelGraphFrame.clear()
        self.regressionGraphFrame.clear()
        self.errorSurfaceGraphFrame.clear()
        self.graphNotebook.removeFrame(self.regressionGraphFrame)
        self.graphNotebook.removeFrame(self.errorSurfaceGraphFrame)
        
        self.resultsStatsFrame.clear()
        self.modelType = None
        
class ResultsStatsFrame(LabelFrame):
    
    ySpread = 5
    paramX = 30
    
    def __init__(self,parent):
        
        LabelFrame.__init__(self,parent,text="Model")
        
        self.totalEstimatedVolume_L = Label(self,text="Estimated total volume (km\u00B3): ")
        self.totalEstimatedVolume_L.grid(row=0,column=0,sticky="W",padx=10,pady=self.ySpread)
        self.totalEstimatedVolume_E = CustomEntry(self,width=10)
        self.totalEstimatedVolume_E.grid(row=0,column=1,padx=10,sticky="E")
        self.totalEstimatedVolume_E.setUserEditable(False)
        createToolTip(self.totalEstimatedVolume_E,"The model's estimate for the total volume of the tephra deposit.");
        
        self.relativeSquaredError_L = Label(self,text="Mean relative squared error: ")
        self.relativeSquaredError_L.grid(row=1,column=0,sticky="W",padx=10,pady=self.ySpread)
        self.relativeSquaredError_E = CustomEntry(self,width=10)
        self.relativeSquaredError_E.grid(row=1,column=1,padx=10,sticky="E")
        self.relativeSquaredError_E.setUserEditable(False)
        createToolTip(self.relativeSquaredError_E,"A measure of the goodness of fit of the model. Comparisons are \nonly valid when comparing different models for identical\nisopach data.");
        
        self.parameters_L = Label(self,text="Parameters:")
        self.calculate_B = Button(self,text="Recalculate",width=10)
        self.reset_B = Button(self,text="Reset",width=10)
        
        self.expSeg_CB = Combobox(self,state="readonly",width=10)
        
        self.expSegVolume_L = Label(self,text="Segment volume (km\u00B3): ")
        self.expSegVolume_E = CustomEntry(self,width=10)
        self.expSegVolume_E.setUserEditable(False)
        createToolTip(self.expSegVolume_E,"The model's estimate for the volume of this segment of the tephra deposit.");
        
        self.expSegStartLimit_L = Label(self,text="Start of segment: ")
        self.expSegStartLimit_E = CustomEntry(self,width=10)
        self.expSegEndLimit_L = Label(self,text="End of segment: ")
        self.expSegEndLimit_E = CustomEntry(self,width=10)
        self.expSegCoefficent_L = Label(self,text="Segment coefficient, c: ")
        self.expSegCoefficent_E = CustomEntry(self,width=10)
        self.expSegExponent_L = Label(self,text="Segment exponent, m: ")
        self.expSegExponent_E = CustomEntry(self,width=10)
        
        self.expSegEquation_L = Label(self,text="Segment equation: ")
        self.expSegEquation_E = CustomEntry(self,width=10)
        self.expSegEquation_E.setUserEditable(False)
        
        self.expWidgets = [self.expSeg_CB,
                           self.parameters_L, self.calculate_B, self.reset_B,
                           self.expSegCoefficent_L, self.expSegCoefficent_E,
                           self.expSegExponent_L, self.expSegExponent_E,
                           self.expSegVolume_L, self.expSegVolume_E,
                           self.expSegEquation_L, self.expSegEquation_E,
                           self.expSegStartLimit_L, self.expSegStartLimit_E,
                           self.expSegEndLimit_L, self.expSegEndLimit_E]
        
        self.powCoefficient_L = Label(self,text="Coefficient, c: ")
        self.powCoefficient_E = CustomEntry(self,width=10)
        self.powExponent_L = Label(self,text="Exponent, m: ")
        self.powExponent_E = CustomEntry(self,width=10)
        self.powProximalLimit_L = Label(self,text="Proximal limit: ")
        self.powProximalLimit_E = CustomEntry(self,width=10)
        self.powDistalLimit_L = Label(self,text="Distal limit: ")
        self.powDistalLimit_E = CustomEntry(self,width=10)
        self.powEquation_L = Label(self,text="Equation: ")
        self.powEquation_E = CustomEntry(self,width=10)
        self.powEquation_E.setUserEditable(False)
        self.powSuggestedProximalLimit_L = Label(self,text="Suggested proximal limit: ")
        self.powSuggestedProximalLimit_E = CustomEntry(self,width=10)
        self.powSuggestedProximalLimit_E.setUserEditable(False)
        createToolTip(self.powSuggestedProximalLimit_E,"An estimate for the proximal limit of integration as described\nin Bonadonna and Houghton 2005")
        
        self.powWidgets = [self.parameters_L, self.calculate_B, self.reset_B,
                           self.powCoefficient_L, self.powCoefficient_E,
                           self.powExponent_L, self.powExponent_E,
                           self.powProximalLimit_L, self.powProximalLimit_E,
                           self.powDistalLimit_L, self.powDistalLimit_E,
                           self.powEquation_L, self.powEquation_E,
                           self.powSuggestedProximalLimit_L, self.powSuggestedProximalLimit_E]
        
        self.weiLambdaL = Label(self,text="Estimated \u03BB: ")
        self.weiLambdaE = CustomEntry(self,width=10)
        self.weiKL = Label(self,text="Estimated k: ")
        self.weiKE = CustomEntry(self,width=10)
        self.weiThetaL = Label(self,text="Estimated \u03B8: ")
        self.weiThetaE = CustomEntry(self,width=10)
        self.weiEquation_L = Label(self,text="Equation: ")
        self.weiEquation_E = CustomEntry(self,width=10)
        self.weiEquation_E.setUserEditable(False)
        self.weiWidgets = [self.parameters_L, self.calculate_B, self.reset_B,
                           self.weiLambdaL, self.weiLambdaE,
                           self.weiKL, self.weiKE,
                           self.weiThetaL, self.weiThetaE,
                           self.weiEquation_L, self.weiEquation_E]
        
        self.currentWidgets = []
        self.currentSegment = 0
        
    def loadExpDisplay(self,numberOfSegments):
        
        self.currentType = EXP
        self.clear()
            
        self.expSeg_CB.grid(row=2,column=0,sticky="W",padx=10,pady=self.ySpread)
        vals = ["Segment " + str(i) for i in range(1,numberOfSegments+1)]
        self.expSeg_CB.configure(values=vals)
        self.expSeg_CB.current(0)
        
        self.expSegVolume_L.grid(row=3,column=0,sticky="W",padx=10,pady=self.ySpread)
        self.expSegVolume_E.grid(row=3,column=1,padx=10,sticky="E")
        
        self.parameters_L.grid(row=4,column=0,padx=10,pady=self.ySpread,sticky="W")
        
        self.expSegStartLimit_L.grid(row=5,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.expSegStartLimit_E.grid(row=5,column=1,padx=10,sticky="E")
        self.expSegEndLimit_L.grid(row=6,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.expSegEndLimit_E.grid(row=6,column=1,padx=10,sticky="E")
        self.expSegCoefficent_L.grid(row=7,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.expSegCoefficent_E.grid(row=7,column=1,padx=10,sticky="E")
        self.expSegExponent_L.grid(row=8,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.expSegExponent_E.grid(row=8,column=1,padx=10,sticky="E")
        
        self.calculate_B.grid(row=9,column=0,padx=self.paramX,pady=self.ySpread,sticky="W")
        self.reset_B.grid(row=9,column=1,padx=10,sticky="E")
        
        self.expSegEquation_L.grid(row=10,column=0,sticky="W",padx=10,pady=self.ySpread)
        self.expSegEquation_E.grid(row=10,column=1,padx=10,sticky="E")
        
        self.currentWidgets = self.expWidgets
        
    def loadPowDisplay(self):
        
        self.currentType = POW
        self.clear()
        
        self.parameters_L.grid(row=2,column=0,padx=10,pady=self.ySpread,sticky="W")
        
        self.powCoefficient_L.grid(row=3,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.powCoefficient_E.grid(row=3,column=1,padx=10,sticky="E")
        self.powExponent_L.grid(row=4,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.powExponent_E.grid(row=4,column=1,padx=10,sticky="E")
        self.powProximalLimit_L.grid(row=5,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.powProximalLimit_E.grid(row=5,column=1,padx=10,sticky="E")
        self.powDistalLimit_L.grid(row=6,column=0,sticky="W",padx=self.paramX,pady=self.ySpread)
        self.powDistalLimit_E.grid(row=6,column=1,padx=10,sticky="E")
        
        self.calculate_B.grid(row=7,column=0,padx=self.paramX,pady=self.ySpread,sticky="W")
        self.reset_B.grid(row=7,column=1,padx=10,sticky="E")
        
        self.powEquation_L.grid(row=8,column=0,sticky="W",padx=10,pady=self.ySpread)
        self.powEquation_E.grid(row=8,column=1,padx=10,sticky="E")
        
        self.powSuggestedProximalLimit_L.grid(row=10,column=0,sticky="W",padx=10,pady=self.ySpread+20)
        self.powSuggestedProximalLimit_E.grid(row=10,column=1,padx=10,sticky="E")
        
        self.currentWidgets = self.powWidgets
            
    def loadWeiDisplay(self):
        
        self.currentType = WEI
        self.clear()
            
        self.parameters_L.grid(row=2,column=0,padx=10,pady=self.ySpread,sticky="W")
        self.calculate_B.grid(row=6,column=0,padx=self.paramX,pady=self.ySpread,sticky="W")
        self.reset_B.grid(row=6,column=1,padx=10,sticky="E")
        
        self.weiLambdaL.grid(row=3,column=0,padx=self.paramX,pady=self.ySpread,sticky="W")
        self.weiLambdaE.grid(row=3,column=1,padx=10,sticky="E")
        self.weiKL.grid(row=4,column=0,padx=self.paramX,pady=self.ySpread,sticky="W")
        self.weiKE.grid(row=4,column=1,padx=10,sticky="E")
        self.weiThetaL.grid(row=5,column=0,padx=self.paramX,pady=self.ySpread,sticky="W")
        self.weiThetaE.grid(row=5,column=1,padx=10,sticky="E")
        
        self.weiEquation_L.grid(row=7,column=0,padx=10,pady=self.ySpread,sticky="W")
        self.weiEquation_E.grid(row=7,column=1,padx=10,sticky="E")
        
        self.currentWidgets = self.weiWidgets
        
    def getParameterValues(self):
        
        values = {}
        if self.currentType == EXP:
            values["c"] = validateValue(self.expSegCoefficent_E.get(),
                                        "Coefficient, c, must be a number",
                                        "float")
            values["m"] = validateValue(self.expSegExponent_E.get(),
                                        "Exponent, m, must be a number",
                                        "float")
            values["segStart"] = validateValue(self.expSegStartLimit_E.get(),
                                        "'Start of segment' must be a number > 0",
                                        "float",
                                        lowerBound=0)
            values["segEnd"] = validateValue(self.expSegEndLimit_E.get(),
                                        "'End of segment' must be a number greater than the 'Start of segment'",
                                        "float",
                                        strictLowerBound=values["segStart"])
            values["segmentNumber"] = self.currentSegment
            if sqrtAreaUsed:
                values["m"] *= SQRT_PI
                values["segStart"] /= SQRT_PI
                values["segEnd"] /= SQRT_PI
                
        elif self.currentType == POW:
            values["c"] = validateValue(self.powCoefficient_E.get(),
                                        "coefficient, c, must be a number",
                                        "float")
            values["m"] = validateValue(self.powExponent_E.get(),
                                        "exponent, m, must be a number",
                                        "float")
            if sqrtAreaUsed:
                values["c"] *= SQRT_PI**-values["m"]
                
        elif self.currentType == WEI:
            values["lambda"] = validateValue(self.weiLambdaE.get(),
                                             "\u03BB must be a positive number",
                                             "float",
                                             strictLowerBound=0)
            values["k"] = validateValue(self.weiKE.get(),
                                        "k must be a positive number",
                                        "float",
                                        strictLowerBound=0)
            
            values["theta"] = validateValue(self.weiThetaE.get(),
                                        "\u03B8 must be a positive number",
                                        "float",
                                        strictLowerBound=0)
            if sqrtAreaUsed:
                values["lambda"] /= SQRT_PI
                
        return values
    
    def expParametersUpdated(self,currentParameters):
        
        numberOfSegments = currentParameters["numberOfSegments"]
        
        start, end = currentParameters["limits"][self.currentSegment], currentParameters["limits"][self.currentSegment+1]
        c, m = currentParameters["cs"][self.currentSegment], currentParameters["ms"][self.currentSegment]
        
        if sqrtAreaUsed:
            start *= SQRT_PI
            end *= SQRT_PI
            m /= SQRT_PI
            
        startStr, endStr = roundToSF(start,NUMBER_OF_SF), roundToSF(end,NUMBER_OF_SF)
        cStr, mStr = roundToSF(c,NUMBER_OF_SF), roundToSF(m,NUMBER_OF_SF)
        
        segmentVolumes = []
        for i in range(numberOfSegments):
            segmentVolumes.append(calculateExponentialSegmentVolume(currentParameters["cs"][i],
                                                                    currentParameters["ms"][i],
                                                                    currentParameters["limits"][i],
                                                                    currentParameters["limits"][i+1]))                                                             
        
        estimatedTotalVolumeStr = roundToSF(sum(segmentVolumes),NUMBER_OF_SF)
        segmentVolumeStr = roundToSF(segmentVolumes[self.currentSegment],NUMBER_OF_SF)
        
        equation = "T = " + cStr
        if m > 0:
            equation += "exp(-" + mStr + "x)"
        elif m < 0:
            equation += "exp(" + mStr[1:] + "x)"
        
        self.totalEstimatedVolume_E.insertNew(estimatedTotalVolumeStr)
        self.expSegStartLimit_E.insertNew(startStr)
        self.expSegEndLimit_E.insertNew(endStr)
        self.expSegEquation_E.insertNew(equation)
        self.expSegVolume_E.insertNew(segmentVolumeStr)
        self.expSegCoefficent_E.insertNew(cStr)
        self.expSegExponent_E.insertNew(mStr)
        
        def thicknessFunction(x):
            for i in range(numberOfSegments):
                if currentParameters["limits"][i] <= x < currentParameters["limits"][i+1]:
                    return currentParameters["cs"][i]*math.exp(-currentParameters["ms"][i]*x)
                
        distanceFromVentKM = [isopach.distanceFromVentKM for isopach in currentParameters["isopachs"]]
        thicknessM = [isopach.thicknessM for isopach in currentParameters["isopachs"]]
        errorStr = roundToSF(regression_methods.meanRelativeSquaredError(distanceFromVentKM, thicknessM, thicknessFunction),NUMBER_OF_SF)
        self.relativeSquaredError_E.insertNew(errorStr)
        
        self.expSegStartLimit_E.setUserEditable(self.currentSegment != 0)
        self.expSegEndLimit_E.setUserEditable(self.currentSegment != numberOfSegments-1)
               
    def powParametersUpdated(self,currentParameters):
        
        c, m = currentParameters["c"], currentParameters["m"] 
        
        thicknessFunction = lambda x : c*(x**(-m))
        distanceFromVentKM = [isopach.distanceFromVentKM for isopach in currentParameters["isopachs"]]
        thicknessM = [isopach.thicknessM for isopach in currentParameters["isopachs"]]
        proximalLimitKM = currentParameters["proximalLimitKM"]
        distalLimitKM = currentParameters["distalLimitKM"]
        suggestedProximalLimit = currentParameters["suggestedProximalLimit"]
        
        errorStr = roundToSF(regression_methods.meanRelativeSquaredError(distanceFromVentKM, thicknessM, thicknessFunction),NUMBER_OF_SF)
        self.relativeSquaredError_E.insertNew(errorStr)
        
        volumeStr = roundToSF(calculatePowerLawVolume(c,m,proximalLimitKM,distalLimitKM),NUMBER_OF_SF)
        
        if sqrtAreaUsed:
            c *= SQRT_PI**m
            proximalLimitKM *= SQRT_PI
            distalLimitKM *= SQRT_PI
            
        coefficientStr = roundToSF(c,NUMBER_OF_SF)
        exponentStr = roundToSF(m,NUMBER_OF_SF)
        proximalLimitStr = roundToSF(proximalLimitKM,NUMBER_OF_SF)
        distalLimitStr = roundToSF(distalLimitKM,NUMBER_OF_SF)
        suggestedProximalLimitStr = roundToSF(suggestedProximalLimit,NUMBER_OF_SF)
        
        equationStr = "T = " + coefficientStr
        if m > 0:
            equationStr += "x^-" + exponentStr
        elif m < 0:
            equationStr += "x^" + exponentStr[1:]
        
        self.totalEstimatedVolume_E.insertNew(volumeStr)
        self.powCoefficient_E.insertNew(coefficientStr)
        self.powExponent_E.insertNew(exponentStr)
        self.powProximalLimit_E.insertNew(proximalLimitStr)
        self.powDistalLimit_E.insertNew(distalLimitStr)
        self.powEquation_E.insertNew(equationStr)
        self.powSuggestedProximalLimit_E.insertNew(suggestedProximalLimitStr)
                                               
    def weiParametersUpdated(self,currentParameters):
        
        lamb, k, theta = currentParameters["lambda"], currentParameters["k"], currentParameters["theta"]
        
        thicknessFunction = lambda x : theta*((x/lamb)**(k-2))*math.exp(-((x/lamb)**k))
        distanceFromVentKM = [isopach.distanceFromVentKM for isopach in currentParameters["isopachs"]]
        thicknessM = [isopach.thicknessM for isopach in currentParameters["isopachs"]]
        errorStr = roundToSF(regression_methods.meanRelativeSquaredError(distanceFromVentKM, thicknessM, thicknessFunction),NUMBER_OF_SF)
        volumeStr = roundToSF(calculateWeibullVolume(lamb, k, theta),NUMBER_OF_SF)
        
        if sqrtAreaUsed:
            lamb *= SQRT_PI
            
        lambdaStr = roundToSF(lamb,NUMBER_OF_SF)
        invLambdaStr = roundToSF(1/lamb,NUMBER_OF_SF)
        kStr = roundToSF(k,NUMBER_OF_SF)
        kminus2Str = roundToSF(k-2,NUMBER_OF_SF)
        thetaStr = roundToSF(theta,NUMBER_OF_SF)
        
        equation = "T = " + thetaStr + "((" + invLambdaStr + "x)^" +kminus2Str + ")exp(-(" + invLambdaStr + "x)^" + kStr + ")"
        
        self.totalEstimatedVolume_E.insertNew(volumeStr)
        self.weiLambdaE.insertNew(lambdaStr)
        self.weiKE.insertNew(kStr)
        self.weiThetaE.insertNew(thetaStr)
        self.weiEquation_E.insertNew(equation)
        self.relativeSquaredError_E.insertNew(errorStr)
        
    def clear(self):
        for wg in self.currentWidgets:
            wg.grid_remove()
        self.currentWidgets = []
        
        self.totalEstimatedVolume_E.insertNew("")
        self.relativeSquaredError_E.insertNew("")
            
class ErrorSurfaceFrame(LabelFrame):
    
    def __init__(self,parent):
        LabelFrame.__init__(self,parent,text="Error surface")
        
        xPad1 = 30
        xPad2 = 15
        
        self.errorXLowerLimitL = Label(self)
        self.errorXLowerLimitE = CustomEntry(self,width=5)
        self.errorXLowerLimitL.grid(row=0,column=0,padx=(10,xPad2),pady=5,sticky="W")
        self.errorXLowerLimitE.grid(row=0,column=1,padx=(xPad2,xPad1),pady=5)
        
        self.errorXUpperLimitL = Label(self)
        self.errorXUpperLimitE = CustomEntry(self,width=5)
        self.errorXUpperLimitL.grid(row=0,column=2,padx=(xPad1,xPad2),pady=5,sticky="W")
        self.errorXUpperLimitE.grid(row=0,column=3,padx=(xPad2,xPad1),pady=5)
        
        self.errorYLowerLimitL = Label(self)
        self.errorYLowerLimitE = CustomEntry(self,width=5)
        self.errorYLowerLimitL.grid(row=1,column=0,padx=(10,xPad2),pady=5,sticky="W")
        self.errorYLowerLimitE.grid(row=1,column=1,padx=(xPad2,xPad1),pady=5)
        
        self.errorYUpperLimitL = Label(self)
        self.errorYUpperLimitE = CustomEntry(self,width=5)
        self.errorYUpperLimitL.grid(row=1,column=2,padx=(xPad1,xPad2),pady=5,sticky="W")
        self.errorYUpperLimitE.grid(row=1,column=3,padx=(xPad2,xPad1),pady=5)
        
        self.errorResolutionL = Label(self,text="Resolution: ")
        self.errorResolutionE = CustomEntry(self,width=5)
        self.errorResolutionE.insert(0,ERROR_SURFACE_DEFAULT_RESOLUTION)
        self.errorResolutionL.grid(row=0,column=4,padx=(xPad1,xPad2),pady=5,sticky="W")
        self.errorResolutionE.grid(row=0,column=5,padx=(xPad2,xPad1),pady=5,sticky="E")
        createToolTip(self.errorResolutionE,"The resolution of the error surface, which is modelled by\na grid of 'resolution' x 'resolution' points.");
        
        self.errorSurfaceB = Button(self,text=" Calculate error surface ")
        self.errorSurfaceB.grid(row=1,column=4,columnspan=2,padx=(xPad1,xPad1),sticky="EW")
        self.errorSurfaceB.configure(state=tkinter.ACTIVE)
        self.update("x","y","","","","")
        
    def update(self,xSymbol,ySymbol,xLL,xUL,yLL,yUL):
        
        self.xSymbol = xSymbol
        self.ySymbol = ySymbol
        
        self.errorXLowerLimitL.configure(text="Lower limit ("+self.xSymbol+"): ")
        self.errorXLowerLimitE.insertNew(xLL)
        
        self.errorXUpperLimitL.configure(text="Upper limit ("+self.xSymbol+"): ")
        self.errorXUpperLimitE.insertNew(xUL)
        
        self.errorYLowerLimitL.configure(text="Lower limit ("+self.ySymbol+"): ")
        self.errorYLowerLimitE.insertNew(yLL)
        
        self.errorYUpperLimitL.configure(text="Upper limit ("+self.ySymbol+"): ")
        self.errorYUpperLimitE.insertNew(yUL)
        
    def getSurfaceParameters(self):
        
        xLowerLimit = validateValue(self.errorXLowerLimitE.get(),
                                    self.xSymbol + " lower limit must be a positive number",
                                    "float",
                                    lowerBound=0)
        xUpperLimit = validateValue(self.errorXUpperLimitE.get(),
                                    self.xSymbol + " upper limit must be greater than the lower limit",
                                    "float",
                                    strictLowerBound=xLowerLimit)
        yLowerLimit = validateValue(self.errorYLowerLimitE.get(),
                                    self.ySymbol + " lower limit must be a positive number",
                                    "float",
                                    lowerBound=0)
        yUpperLimit = validateValue(self.errorYUpperLimitE.get(),
                                    self.ySymbol + " upper limit must be greater than the lower limit",
                                    "float",
                                    strictLowerBound=yLowerLimit)
        resolution = validateValue(self.errorResolutionE.get(),
                                   "Resolution must be " + str(ERROR_SURFACE_MIN_RESOLUTION) + " \u2264 x \u2264 " + str(ERROR_SURFACE_MAX_RESOLUTION),
                                   "int",
                                   lowerBound=ERROR_SURFACE_MIN_RESOLUTION,
                                   upperBound=ERROR_SURFACE_MAX_RESOLUTION)
        
        return [xLowerLimit,xUpperLimit,yLowerLimit,yUpperLimit,resolution]
        
    def clear(self):
        self.errorXLowerLimitE.insertNew("")
        self.errorXUpperLimitE.insertNew("")
        self.errorYLowerLimitE.insertNew("")
        self.errorYUpperLimitE.insertNew("")
        
class GraphFrame(Frame):
    
    def __init__(self,parent,dim):
        Frame.__init__(self,parent)    
        self.dim = dim
        
        self.figure = pyplot.Figure(figsize=(5.8,3.5), facecolor=(240/255,240/255,237/255))
        self.figure.subplots_adjust(left=0.15, bottom=0.2)
        self.canvas = FigureCanvas(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=0,column=2,sticky="W")
        self.canvas.get_tk_widget().configure(highlightthickness=0)
        toolbar = CutDownNavigationToolbar(self.canvas,self)
        toolbar.grid(row=1,column=2,sticky="W")
        
        if dim == 2:
            self.axes = self.figure.add_subplot(1,1,1)
        elif dim == 3:
            self.axes = Axes3D(self.figure)
        else:
            raise ValueError("Dimension must be either 2 or 3")
        
        self.currentLines = []
    
    def plotScatter(self,xs,ys,zeroed):
        self.currentLines.append(self.axes.scatter(xs,ys))
        minX, maxX = min(xs), max(xs)
        minY, maxY = min(ys), max(ys)
        dx, dy = 0.25*(maxX-minX), 0.25*(maxY-minY)
        startX, startY = (0,0) if zeroed else (minX-dx, minY-dy)
        endX, endY = maxX+dx, maxY+dy
        self.axes.set_xlim((startX,endX))
        self.axes.set_ylim((startY,endY))
        self.canvas.draw()
    
    def plotLine(self,xs,ys,color):
        self.currentLines.extend(self.axes.plot(xs,ys,color=color))
        self.canvas.draw()
        
    def plotFilledLine(self,xs,ys,color):
        self.currentLines.append(self.axes.fill_between(xs,ys,y2=0,alpha=0.5,color=color))
        self.canvas.draw()
        
    def plotSurface(self,zfunc,startX,endX,startY,endY,resolution):
        xInc, yInc = (endX-startX)/resolution, (endY-startY)/resolution
        xs = np.arange(startX,endX,xInc)
        ys = np.arange(startY,endY,yInc)
        X, Y = np.meshgrid(np.array(xs),np.array(ys))
        
        Z = []
        for row in range(resolution):
            rowL = []
            for col in range(resolution):
                try:
                    v = zfunc(X[row][col],Y[row][col])
                    if v > 10**10:
                        rowL.append(np.nan)
                    else:
                        rowL.append(v)
                except FloatingPointError:
                    rowL.append(np.nan)
            Z.append(rowL)
        
        maxZ = max([max([r for r in row if not np.isnan(r)]) for row in Z])
        minZ = min([min([r for r in row if not np.isnan(r)]) for row in Z])
        
        self.currentLines.append(self.axes.plot_wireframe(X, Y, Z))
        self.axes.set_xlim((startX,endX))
        self.axes.set_ylim((startY,endY))
        self.axes.set_zlim((minZ,maxZ))
        self.canvas.draw()
        
    def clear(self):
        for l in self.currentLines:
            l.remove()
            self.currentLines = []
        self.canvas.draw()

class CutDownNavigationToolbar(NavigationToolbar):
    # only display the buttons needed
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ("Home", "Back", "Forward", "Pan", "Save")]
    
class ScrollFrame(Frame):
    
    def __init__(self,parent,width,height):
        
        Frame.__init__(self,master=parent)
        
        canvas=Canvas(self, highlightthickness=0)
        myscrollbar=Scrollbar(self,orient="vertical",command=canvas.yview)
        
        self.innerFrame=Frame(canvas)
        canvas.configure(yscrollcommand=myscrollbar.set)
        
        myscrollbar.grid(row=0,column=1,sticky="NS")
        canvas.grid(row=0,column=0)
        canvas.create_window((0,0),window=self.innerFrame,anchor='nw')
        self.innerFrame.bind("<Configure>",lambda _ : canvas.configure(scrollregion=canvas.bbox("all"),width=width,height=height))

class CustomEntry(Entry):
    
    def __init__(self,*args,**kwargs):
        Entry.__init__(self,*args,**kwargs)
        self.userEditable = True

    def setUserEditable(self,userEditable):
        self.userEditable = userEditable
        self.config(state=(tkinter.ACTIVE if userEditable else tkinter.DISABLED))
        
    def insertNew(self,text):
        if not self.userEditable:
            self.config(state="normal")
        self.delete(0,tkinter.END)
        self.insert(0,text)
        if not self.userEditable:
            self.config(state="readonly")
    
class ImprovedNotebook(Notebook):
    
    def __init__(self,*args,**kwargs):
        Notebook.__init__(self,*args,**kwargs)
        self.currentFrames = {}
        
    def addFrame(self,frame,text):
        if frame not in self.currentFrames:
            tabID = self.add(frame,text=text)
            self.currentFrames[frame] = tabID
            
    def removeFrame(self,frame):
        if frame in self.currentFrames:
            self.forget(frame)
            del self.currentFrames[frame]
    
    def selectFrame(self,frame):
        if frame in self.currentFrames:
            self.select(self.currentFrames[frame])
               
def validateValue(string,errorString,numericType,lowerBound=None,strictLowerBound=None,upperBound=None,strictUpperBound=None):
    try:
        if numericType == "float":
            if string == "\u221E":
                value = float('inf')
            else:
                value = float(string)
        elif numericType == "int":
            value = int(string)
            
        if lowerBound is not None and value < lowerBound:
            raise ValueError()
        if strictLowerBound is not None and value <= strictLowerBound:
            raise ValueError()
        if upperBound is not None and value > upperBound:
            raise ValueError()
        if strictUpperBound is not None and value >= strictUpperBound:
            raise ValueError()
    except ValueError:
        raise ValueError(errorString)
    return value

def roundToSF(number,sf):
    if number == 0:
        return "0."+"0"*sf
    elif number == float("inf"):
        return "\u221E"
    elif isinstance(number,str):
        return number
    else:
        places = int(np.floor(np.log10(abs(number))))
        value = round(number, -places + (sf - 1))
        return str(int(value) if places >= sf - 1 else value)
    
def getStaggeredPoints(start,end,number):
    c = start+1
    lamb = np.log((end+1)/c)/number 
    return [c*math.exp(lamb*i)-1 for i in range(0,number+1)]