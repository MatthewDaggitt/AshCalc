'''
Created on 15 Aug 2013

@author: Matthew Daggitt
'''
import math
from copy import deepcopy

import tkinter
from tkinter import Canvas, StringVar, IntVar, messagebox, PhotoImage
from tkinter.ttk import Separator, Notebook, LabelFrame, Frame, Button, Label, Entry, Radiobutton, Combobox, Checkbutton
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas, NavigationToolbar2TkAgg as NavigationToolbar
from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
np.seterr(all="ignore")

from core.isopach import Isopach
from core.models.exponential import calculateExponentialSegmentVolume
from core.models.power_law import calculatePowerLawVolume
from core.models.weibull import calculateWeibullVolume, calculateTheta
from core import regression_methods

from desktop import helper_functions
from desktop.thread_handlers import ThreadHandler
from desktop.timing_module import createWeibullTimingEstimationFunction
from desktop.tooltip import createToolTip
from desktop.custom_components import CustomEntry, ImprovedNotebook
from desktop.settings import Model

from desktop.frames.model_frame import ModelFrame
from desktop.frames.isopach_frame import IsopachFrame
from desktop.frames.calculation_frame import CalculationFrame

###########Config###########

MODEL_PLOTTING_PRECISION = 100

ERROR_SURFACE_MAX_RESOLUTION = 100
ERROR_SURFACE_MIN_RESOLUTION = 5
ERROR_SURFACE_DEFAULT_RESOLUTION = 50

NUMBER_OF_SF = 6

colours = ["blue","green","red","cyan","magenta"]

############################

#########Constants##########

SQRT_PI = np.sqrt(np.pi)

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
		self.calculationFrame.grid(row=0,column=0,sticky="NSWE",padx=(10,5),pady=10)
		self.calculationFrame.startCalculationB.bind("<Button-1>",self.startCalculation)
		self.calculationFrame.endCalculationB.configure(state=tkinter.DISABLED)

		self.isopachEntryFrame = IsopachFrame(self,self.estimateWeibullCalculationTime)
		self.isopachEntryFrame.grid(row=1,column=0,padx=10,sticky="NS",pady=10)
		
		self.modelEntryFrame = ModelFrame(self)
		self.modelEntryFrame.grid(row=0,column=1,sticky="NESW",padx=10,pady=10)
		self.modelEntryFrame.weiNumberOfRuns_E.bind("<KeyRelease>",self.estimateWeibullCalculationTime)
		self.modelEntryFrame.weiIterationsPerRun_E.bind("<KeyRelease>",self.estimateWeibullCalculationTime)
		self.estimateWeibullCalculationTime(None)

		self.resultsFrame = ResultsFrame(self)
		self.resultsFrame.grid(row=1,column=1,padx=10,sticky="NS",pady=10)

		self.isopachEntryFrame.loadData([Isopach(0.4,16.25),Isopach(0.2,30.63),Isopach(0.1,58.87),Isopach(0.05,95.75),Isopach(0.02,181.56),Isopach(0.01,275.1)])

		self.pack()
		self.mainloop()
		
	def startCalculation(self, event):
		try:
			isopachs = self.isopachEntryFrame.getData()
			modelDetails = self.modelEntryFrame.getModelDetails()
			self.threadHandler.startCalculation(modelDetails[0], [isopachs] + modelDetails[1:])

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
	
	def finishCalculation(self,_):
		self.threadHandler.cancelLastCalculation()
		self.calculating = False
		self.calculationFrame.startCalculationB.configure(state=tkinter.ACTIVE)
		self.calculationFrame.startCalculationB.bind("<Button-1>",self.startCalculation)
		self.calculationFrame.endCalculationB.configure(state=tkinter.DISABLED)
		self.calculationFrame.endCalculationB.unbind("<Button-1>")
		self.calculationFrame.calculationPB.stop()

	def estimateWeibullCalculationTime(self,event):
		try:
			numberOfIsopachs = self.isopachEntryFrame.getNumberOfIncludedIsopachs()
			numberOfRuns = int(self.modelEntryFrame.weiNumberOfRuns_E.get())
			iterationsPerRun = int(self.modelEntryFrame.weiIterationsPerRun_E.get())
			if numberOfRuns <= 0 or iterationsPerRun <= 0 or numberOfIsopachs <= 0:
				raise ValueError()
			est = self.weibullTimingEstimationFunction(numberOfIsopachs,iterationsPerRun,numberOfRuns)
			self.modelEntryFrame.weiEstimatedTime_E.insertNew(helper_functions.roundToSF(est,2))
		except ValueError:
			self.modelEntryFrame.weiEstimatedTime_E.insertNew("N/A")
				
class ResultsFrame(LabelFrame):
	
	def __init__(self,parent):
		
		LabelFrame.__init__(self,parent,text="Results")
		
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
		
		if modelType == Model.EXP:
			self.currentParameters = {"isopachs":resultsDict["isopachs"],
									  "numberOfSegments":resultsDict["numberOfSegments"],
									  "cs":resultsDict["segmentCoefficients"],
									  "ms":resultsDict["segmentExponents"],
									  "limits":resultsDict["segmentLimits"]}
			self.resultsStatsFrame.loadExpDisplay(resultsDict["numberOfSegments"])
			
		elif modelType == Model.POW:
			xs = [isopach.sqrtAreaKM for isopach in resultsDict["isopachs"]]
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
			
		elif modelType == Model.WEI:
			xs = np.array([isopach.sqrtAreaKM for isopach in resultsDict["isopachs"]])
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
		sqrtArea = [isopach.sqrtAreaKM for isopach in self.currentParameters["isopachs"]]
		self.modelGraphFrame.plotScatter(sqrtArea,thicknessM,True)
		self.modelGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
		
		if self.modelType == Model.EXP:
			self._updateExp()
		elif self.modelType == Model.POW:
			self._updatePow()
		elif self.modelType == Model.WEI:
			self._updateWei()
		
	def _updateExp(self):
		
		self.resultsStatsFrame.expParametersUpdated(self.currentParameters)
		
		n = self.currentParameters["numberOfSegments"]
		
		self.errorSurfaceFrame.grid_remove()
		
		startOfIsopachs = min(self.currentParameters["isopachs"],key=lambda i:i.distanceFromVentKM()).distanceFromVentKM()
		endOfIsopachs = max(self.currentParameters["isopachs"],key=lambda i:i.distanceFromVentKM()).distanceFromVentKM()
		
		logThickness = [math.log(isopach.thicknessM) for isopach in self.currentParameters["isopachs"]]
		sqrtArea = [isopach.sqrtAreaKM for isopach in self.currentParameters["isopachs"]]
		self.regressionGraphFrame.plotScatter(sqrtArea,logThickness,False)
		self.regressionGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
		startOfIsopachs *= SQRT_PI
		endOfIsopachs *= SQRT_PI
		
		for i in range(n):
			c, m = self.currentParameters["cs"][i], self.currentParameters["ms"][i]/SQRT_PI
			
			startX = self.currentParameters["limits"][i]*SQRT_PI
			endX = (self.currentParameters["limits"][i+1]*SQRT_PI if i != n-1 else 1.5*(endOfIsopachs-startOfIsopachs)+startOfIsopachs)
			startY = math.log(c)-m*startX
			endY = math.log(c)-m*endX
			color = colours[i]
			xs = helper_functions.getStaggeredPoints(startX,endX,MODEL_PLOTTING_PRECISION)
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
		c *= SQRT_PI**m


		logThickness = [math.log(isopach.thicknessM) for isopach in self.currentParameters["isopachs"]]
		sqrtArea = [isopach.sqrtAreaKM for isopach in self.currentParameters["isopachs"]]
		self.regressionGraphFrame.plotScatter(sqrtArea,logThickness,False)
		self.regressionGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
		
		proxLimit = self.currentParameters["proximalLimitKM"]*SQRT_PI
		distLimit = self.currentParameters["distalLimitKM"]*SQRT_PI
		xs = helper_functions.getStaggeredPoints(proxLimit,distLimit,MODEL_PLOTTING_PRECISION)
		ys = [np.log(c)-m*np.log(x) for x in xs]
		self.regressionGraphFrame.plotLine(xs,ys,colours[0])
		
		xs = helper_functions.getStaggeredPoints(proxLimit,distLimit,MODEL_PLOTTING_PRECISION)
		ys = [c*(x**(-m)) for x in xs]
		self.modelGraphFrame.plotFilledLine(xs, ys, color=colours[0])
		
		self.graphNotebook.addFrame(self.regressionGraphFrame,text="Regression")
		self.currentTabs = [self.regressionGraphFrame]
			
	def _updateWei(self):
		
		self.resultsStatsFrame.weiParametersUpdated(self.currentParameters)
		
		lamb = self.currentParameters["lambda"]*SQRT_PI
		k = self.currentParameters["k"]
		theta = self.currentParameters["theta"]
		limits = self.currentParameters["limits"]
		
		self.errorSurfaceFrame.grid(row=1,column=0,columnspan=2,padx=10,pady=5,sticky="EW")
		self.errorSurfaceFrame.update("\u03BB", "k", limits[0][0]*SQRT_PI, limits[0][1]*SQRT_PI, limits[1][0], limits[1][1])
		
		startX = 0
		endX = (self.currentParameters["isopachs"][-1].distanceFromVentKM()+50)*SQRT_PI

		xs = helper_functions.getStaggeredPoints(startX,endX,MODEL_PLOTTING_PRECISION)[1:]
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

		if self.modelType == Model.EXP:
			i = changedParameters["segmentNumber"]
			self.currentParameters["cs"][i] = changedParameters["c"]
			self.currentParameters["ms"][i] = changedParameters["m"]
			self.currentParameters["limits"][i] = changedParameters["segStart"]
			self.currentParameters["limits"][i+1] = changedParameters["segEnd"]
		elif self.modelType == Model.POW:
			self.currentParameters["c"] = changedParameters["c"]
			self.currentParameters["m"] = changedParameters["m"]
		elif self.modelType == Model.WEI:
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
		
		LabelFrame.__init__(self,parent,borderwidth=0)
		
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
		
		self.currentType = Model.EXP
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
		
		self.currentType = Model.POW
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
		
		self.currentType = Model.WEI
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
		if self.currentType == Model.EXP:
			values["c"] = helper_functions.validateValue(self.expSegCoefficent_E.get(),
										"Coefficient, c, must be a number",
										"float")
			values["m"] = helper_functions.validateValue(self.expSegExponent_E.get(),
										"Exponent, m, must be a number",
										"float")
			values["segStart"] = helper_functions.validateValue(self.expSegStartLimit_E.get(),
										"'Start of segment' must be a number > 0",
										"float",
										lowerBound=0)
			values["segEnd"] = helper_functions.validateValue(self.expSegEndLimit_E.get(),
										"'End of segment' must be a number greater than the 'Start of segment'",
										"float",
										strictLowerBound=values["segStart"])
			values["segmentNumber"] = self.currentSegment

			values["m"] *= SQRT_PI
			values["segStart"] /= SQRT_PI
			values["segEnd"] /= SQRT_PI
				
		elif self.currentType == Model.POW:
			values["c"] = helper_functions.validateValue(self.powCoefficient_E.get(),
										"coefficient, c, must be a number",
										"float")
			values["m"] = helper_functions.validateValue(self.powExponent_E.get(),
										"exponent, m, must be a number",
										"float")

			values["c"] *= SQRT_PI**-values["m"]
				
		elif self.currentType == Model.WEI:
			values["lambda"] = helper_functions.validateValue(self.weiLambdaE.get(),
											 "\u03BB must be a positive number",
											 "float",
											 strictLowerBound=0)
			values["k"] = helper_functions.validateValue(self.weiKE.get(),
										"k must be a positive number",
										"float",
										strictLowerBound=0)
			
			values["theta"] = helper_functions.validateValue(self.weiThetaE.get(),
										"\u03B8 must be a positive number",
										"float",
										strictLowerBound=0)
			
			values["lambda"] /= SQRT_PI
				
		return values
	
	def expParametersUpdated(self,currentParameters):
		
		numberOfSegments = currentParameters["numberOfSegments"]
		
		start, end = currentParameters["limits"][self.currentSegment], currentParameters["limits"][self.currentSegment+1]
		c, m = currentParameters["cs"][self.currentSegment], currentParameters["ms"][self.currentSegment]
		
		start *= SQRT_PI
		end *= SQRT_PI
		m /= SQRT_PI
			
		startStr, endStr = helper_functions.roundToSF(start,NUMBER_OF_SF), helper_functions.roundToSF(end,NUMBER_OF_SF)
		cStr, mStr = helper_functions.roundToSF(c,NUMBER_OF_SF), helper_functions.roundToSF(m,NUMBER_OF_SF)
		
		segmentVolumes = []
		for i in range(numberOfSegments):
			segmentVolumes.append(calculateExponentialSegmentVolume(currentParameters["cs"][i],
																	currentParameters["ms"][i],
																	currentParameters["limits"][i],
																	currentParameters["limits"][i+1]))                                                             
		
		estimatedTotalVolumeStr = helper_functions.roundToSF(sum(segmentVolumes),NUMBER_OF_SF)
		segmentVolumeStr = helper_functions.roundToSF(segmentVolumes[self.currentSegment],NUMBER_OF_SF)
		
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
				
		distanceFromVentKM = [isopach.distanceFromVentKM() for isopach in currentParameters["isopachs"]]
		thicknessM = [isopach.thicknessM for isopach in currentParameters["isopachs"]]
		errorStr = helper_functions.roundToSF(regression_methods.meanRelativeSquaredError(distanceFromVentKM, thicknessM, thicknessFunction),NUMBER_OF_SF)
		self.relativeSquaredError_E.insertNew(errorStr)
		
		self.expSegStartLimit_E.setUserEditable(self.currentSegment != 0)
		self.expSegEndLimit_E.setUserEditable(self.currentSegment != numberOfSegments-1)
			   
	def powParametersUpdated(self,currentParameters):
		
		c, m = currentParameters["c"], currentParameters["m"] 
		
		thicknessFunction = lambda x : c*(x**(-m))
		distanceFromVentKM = [isopach.distanceFromVentKM() for isopach in currentParameters["isopachs"]]
		thicknessM = [isopach.thicknessM for isopach in currentParameters["isopachs"]]
		proximalLimitKM = currentParameters["proximalLimitKM"]
		distalLimitKM = currentParameters["distalLimitKM"]
		suggestedProximalLimit = currentParameters["suggestedProximalLimit"]
		
		errorStr = helper_functions.roundToSF(regression_methods.meanRelativeSquaredError(distanceFromVentKM, thicknessM, thicknessFunction),NUMBER_OF_SF)
		self.relativeSquaredError_E.insertNew(errorStr)
		
		volumeStr = helper_functions.roundToSF(calculatePowerLawVolume(c,m,proximalLimitKM,distalLimitKM),NUMBER_OF_SF)
		
		c *= SQRT_PI**m
		proximalLimitKM *= SQRT_PI
		distalLimitKM *= SQRT_PI
			
		coefficientStr = helper_functions.roundToSF(c,NUMBER_OF_SF)
		exponentStr = helper_functions.roundToSF(m,NUMBER_OF_SF)
		proximalLimitStr = helper_functions.roundToSF(proximalLimitKM,NUMBER_OF_SF)
		distalLimitStr = helper_functions.roundToSF(distalLimitKM,NUMBER_OF_SF)
		suggestedProximalLimitStr = helper_functions.roundToSF(suggestedProximalLimit,NUMBER_OF_SF)
		
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
		distanceFromVentKM = [isopach.distanceFromVentKM() for isopach in currentParameters["isopachs"]]
		thicknessM = [isopach.thicknessM for isopach in currentParameters["isopachs"]]
		errorStr = helper_functions.roundToSF(regression_methods.meanRelativeSquaredError(distanceFromVentKM, thicknessM, thicknessFunction),NUMBER_OF_SF)
		volumeStr = helper_functions.roundToSF(calculateWeibullVolume(lamb, k, theta),NUMBER_OF_SF)
		
		lamb *= SQRT_PI
			
		lambdaStr = helper_functions.roundToSF(lamb,NUMBER_OF_SF)
		invLambdaStr = helper_functions.roundToSF(1/lamb,NUMBER_OF_SF)
		kStr = helper_functions.roundToSF(k,NUMBER_OF_SF)
		kminus2Str = helper_functions.roundToSF(k-2,NUMBER_OF_SF)
		thetaStr = helper_functions.roundToSF(theta,NUMBER_OF_SF)
		
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
		
		xLowerLimit = helper_functions.validateValue(self.errorXLowerLimitE.get(),
									self.xSymbol + " lower limit must be a positive number",
									"float",
									lowerBound=0)
		xUpperLimit = helper_functions.validateValue(self.errorXUpperLimitE.get(),
									self.xSymbol + " upper limit must be greater than the lower limit",
									"float",
									strictLowerBound=xLowerLimit)
		yLowerLimit = helper_functions.validateValue(self.errorYLowerLimitE.get(),
									self.ySymbol + " lower limit must be a positive number",
									"float",
									lowerBound=0)
		yUpperLimit = helper_functions.validateValue(self.errorYUpperLimitE.get(),
									self.ySymbol + " upper limit must be greater than the lower limit",
									"float",
									strictLowerBound=yLowerLimit)
		resolution = helper_functions.validateValue(self.errorResolutionE.get(),
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
		#toolbar = CutDownNavigationToolbar(self.canvas,self)
		#toolbar.grid(row=1,column=2,sticky="W")
		
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
