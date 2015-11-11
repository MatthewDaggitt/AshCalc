import math
from copy import deepcopy

import numpy as np

import tkinter
from tkinter.ttk import Frame, LabelFrame, Label, Button, Combobox, Separator, Notebook

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas, NavigationToolbar2TkAgg as NavigationToolbar
from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D

from core.isopach import Isopach
from core.models.exponential import calculateExponentialSegmentVolume
from core.models.power_law import calculatePowerLawVolume
from core.models.weibull import calculateWeibullVolume, calculateTheta
from core import regression_methods

from desktop import helper_functions
from desktop.custom_components import CustomEntry, ImprovedNotebook, CutDownNavigationToolbar
from desktop.settings import Model

###########Config###########

colours = ["blue","green","red","cyan","magenta"]

############################

SQRT_PI = np.sqrt(np.pi)

MODEL_PLOTTING_PRECISION = 100

ERROR_SURFACE_MAX_RESOLUTION = 100
ERROR_SURFACE_MIN_RESOLUTION = 5
ERROR_SURFACE_DEFAULT_RESOLUTION = 50

NUMBER_OF_SF = 4

class ResultsFrame(LabelFrame):
	
	padY = 5
	padX = 30

	def __init__(self,parent):

		LabelFrame.__init__(self, parent,text="Results", width=825, height=485)

		# Terrible kludgy hack to force the app to stay the right size
		# Need to work out how to remove
		self.grid_propagate(False)
		 

		self.resultsDict = None
		self.modelType = None
		self.currentSegment = 0

		# Stats frame
		
		self.statsFrame = StatsFrame(self, self.padX, self.padY)
		self.statsFrame.calculate_B.bind("<Button-1>", self._parametersChanged)
		self.statsFrame.reset_B.bind("<Button-1>", self._parametersReset)
		
		def onComboBoxSelect(e):
			self.currentSegment = e.widget.current()
			self._updateDisplay()
		self.statsFrame.expSeg_CB.bind("<<ComboboxSelected>>", onComboBoxSelect)
		
		# Error frame
		
		self.errorSurfaceFrame = ErrorSurfaceFrame(self)
		self.errorSurfaceFrame.errorSurfaceB.bind("<Button-1>", self._displayErrorSurface)

		# Graph notebook
		
		self.errorSurfaceSeperator = Separator(self,orient=tkinter.HORIZONTAL)

		self.graphNotebook = ImprovedNotebook(self)

		self.modelGraphFrame = GraphFrame(self.graphNotebook, dim=2)
		self.modelGraphFrame.axes.set_ylabel(r'$thickness(m)$')

		self.regressionGraphFrame = GraphFrame(self.graphNotebook, dim=2)
		self.regressionGraphFrame.axes.set_ylabel(r'$\ln{(thickness(m))}$')
		
		self.errorSurfaceGraphFrame = GraphFrame(self.graphNotebook, dim=3)
		self.errorSurfaceGraphFrame.axes.set_zlabel(r'$error$')
		
		self.graphNotebook.addFrame(self.modelGraphFrame, text="Model")
		
	def displayNewModel(self, modelType, resultsDict):

		self.modelType = modelType
		self.isopachs = resultsDict["isopachs"]
		self.sqrtAreaKM = [isopach.sqrtAreaKM for isopach in self.isopachs]
		self.thicknessM = [isopach.thicknessM for isopach in self.isopachs]
		self.currentParameters = resultsDict
		self.defaultParameters = deepcopy(self.currentParameters)

		self.statsFrame.grid(row=0,column=0,padx=10,pady=5,sticky="NESW")
		self.graphNotebook.grid(row=0,column=1,padx=10, pady=5,sticky="NESW")

		if self.modelType == Model.EXP:
			self._displayExp()
			self.config(text="Results (Exponential)")
		else:
			self.errorSurfaceSeperator.grid(row=1, column=0, columnspan=2, padx=20, pady=(20,0), sticky="EW")
			self.errorSurfaceFrame.grid(row=2, column=0, columnspan=2, padx=10, pady=0, sticky="EW")

			if self.modelType == Model.POW:
				self._displayPow()
				self.config(text="Results (Power law)")
			elif self.modelType == Model.WEI:
				self._displayWei()
				self.config(text="Results (Weibull)")


		self._updateDisplay()
		
	def _updateDisplay(self):
		
		self.modelGraphFrame.clear()
		self.regressionGraphFrame.clear()

		thicknessM = [isopach.thicknessM for isopach in self.isopachs]
		sqrtArea = [isopach.sqrtAreaKM for isopach in self.isopachs]

		self.modelGraphFrame.plotScatter(sqrtArea,thicknessM,True)
		self.modelGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
		
		if self.modelType == Model.EXP:
			self._updateExp()
		elif self.modelType == Model.POW:
			self._updatePow()
		elif self.modelType == Model.WEI:
			self._updateWei()
		
	def _displayExp(self):
		fr = self.statsFrame
		padX = self.padX
		padY = self.padY

		fr.expSeg_CB.grid(row=3,column=0,sticky="W",padx=10,pady=padY)
		vals = ["Segment " + str(i) for i in range(1,self.currentParameters["numberOfSegments"]+1)]
		fr.expSeg_CB.configure(values=vals)
		fr.expSeg_CB.current(0)

		fr.expSegVolume_L.grid(row=4,column=0,padx=10,sticky="W",pady=padY)
		fr.expSegVolume_E.grid(row=4,column=1,padx=10,sticky="E")

		fr.parameters_L.grid(row=5,column=0,padx=10,pady=padY,sticky="W")

		fr.expSegStartLimit_L.grid(row=6,column=0,sticky="W",padx=padX,pady=padY)
		fr.expSegStartLimit_E.grid(row=6,column=1,padx=10,sticky="E")

		fr.expSegEndLimit_L.grid(row=7,column=0,sticky="W",padx=padX,pady=padY)
		fr.expSegEndLimit_E.grid(row=7,column=1,padx=10,sticky="E")

		fr.expSegCoefficent_L.grid(row=8,column=0,sticky="W",padx=padX,pady=padY)
		fr.expSegCoefficent_E.grid(row=8,column=1,padx=10,sticky="E")

		fr.expSegExponent_L.grid(row=9,column=0,sticky="W",padx=padX,pady=padY)
		fr.expSegExponent_E.grid(row=9,column=1,padx=10,sticky="E")

		
		# Recalculate buttons
		fr.calculate_B.grid(row=10,column=0,padx=padX,pady=padY,sticky="W")
		fr.reset_B.grid(row=10,column=1,padx=10,sticky="E")
		
		self.graphNotebook.addFrame(self.regressionGraphFrame, text="Regression")

	def _displayPow(self):
		fr = self.statsFrame
		padX = self.padX
		padY = self.padY

		fr.parameters_L.grid(row=2,column=0,padx=10,pady=padY,sticky="W")

		fr.powCoefficient_L.grid(row=3,column=0,sticky="W",padx=padX,pady=padY)
		fr.powCoefficient_E.grid(row=3,column=1,padx=10,sticky="E")

		fr.powExponent_L.grid(row=4,column=0,sticky="W",padx=padX,pady=padY)
		fr.powExponent_E.grid(row=4,column=1,padx=10,sticky="E")

		fr.powProximalLimit_L.grid(row=5,column=0,sticky="W",padx=padX,pady=padY)
		fr.powProximalLimit_E.grid(row=5,column=1,padx=10,sticky="E")

		fr.powDistalLimit_L.grid(row=6,column=0,sticky="W",padx=padX,pady=padY)
		fr.powDistalLimit_E.grid(row=6,column=1,padx=10,sticky="E")

		fr.powSuggestedProximalLimit_L.grid(row=10,column=0,sticky="W",padx=10,pady=padY+20)
		fr.powSuggestedProximalLimit_E.grid(row=10,column=1,padx=10,sticky="E")

		# Recalculate buttons
		fr.calculate_B.grid(row=9,column=0,padx=padX,pady=padY,sticky="W")
		fr.reset_B.grid(row=9,column=1,padx=10,sticky="E")

		self.graphNotebook.addFrame(self.regressionGraphFrame, text="Regression")
		self.errorSurfaceFrame.update("c", "m", 0.0, 5.0, 0.0, 5.0)

	def _displayWei(self):
		fr = self.statsFrame
		padX = self.padX
		padY = self.padY

		fr.parameters_L.grid(row=2,column=0,padx=10,pady=padY,sticky="W")

		fr.weiLambdaL.grid(row=3,column=0,padx=padX,pady=padY,sticky="W")
		fr.weiLambdaE.grid(row=3,column=1,padx=10,sticky="E")

		fr.weiKL.grid(row=4,column=0,padx=padX,pady=padY,sticky="W")
		fr.weiKE.grid(row=4,column=1,padx=10,sticky="E")

		fr.weiThetaL.grid(row=5,column=0,padx=padX,pady=padY,sticky="W")
		fr.weiThetaE.grid(row=5,column=1,padx=10,sticky="E")

		# Recalculate buttons
		fr.calculate_B.grid(row=6,column=0,padx=padX,pady=padY,sticky="W")
		fr.reset_B.grid(row=6,column=1,padx=10,sticky="E")

		parameterLimits = self.currentParameters["limits"]
		lambdaLower, lambdaUpper = parameterLimits[0]
		kLower, kUpper = parameterLimits[1]
		self.errorSurfaceFrame.update("\u03BB", "k", lambdaLower, lambdaUpper, kLower, kUpper)

	def _updateExp(self):
		
		n = self.currentParameters["numberOfSegments"]
		coefficients = self.currentParameters["segmentCoefficients"]
		exponents = self.currentParameters["segmentExponents"]
		limits = self.currentParameters["segmentLimits"]

		###########
		## Stats ##
		###########

		fr = self.statsFrame

		# Segment start
		start = limits[self.currentSegment]
		startStr = helper_functions.roundToSF(start, NUMBER_OF_SF)
		fr.expSegStartLimit_E.insertNew(startStr)
		fr.expSegStartLimit_E.setUserEditable(self.currentSegment != 0)

		# Segment end
		end = limits[self.currentSegment+1]
		endStr = helper_functions.roundToSF(end, NUMBER_OF_SF)
		fr.expSegEndLimit_E.insertNew(endStr)
		fr.expSegEndLimit_E.setUserEditable(self.currentSegment != n-1)

		# Segment coefficient
		coefficient = coefficients [self.currentSegment]
		coefficientStr = helper_functions.roundToSF(coefficient, NUMBER_OF_SF)
		fr.expSegCoefficent_E.insertNew(coefficientStr)
		
		# Segment exponent
		exponent = exponents[self.currentSegment]
		exponentStr = helper_functions.roundToSF(exponent, NUMBER_OF_SF)
		fr.expSegExponent_E.insertNew(exponentStr)
		
		# Segment volume
		segmentVolumes = [calculateExponentialSegmentVolume(coefficients[i], exponents[i], limits[i], limits[i+1]) for i in range(n)]
		segmentVolumeStr = helper_functions.roundToSF(segmentVolumes[self.currentSegment], NUMBER_OF_SF)
		fr.expSegVolume_E.insertNew(segmentVolumeStr)

		# Total volume
		totalVolume = sum(segmentVolumes)
		estimatedTotalVolumeStr = helper_functions.roundToSF(totalVolume, NUMBER_OF_SF)
		fr.totalEstimatedVolume_E.insertNew(estimatedTotalVolumeStr)

		# Error 
		def thicknessFunction(x):
			for i in range(n):
				if limits[i] <= x < limits[i+1]:
					return coefficients[i]*math.exp(-exponents[i]*x)
		error = regression_methods.meanRelativeSquaredError(self.sqrtAreaKM, self.thicknessM, thicknessFunction)
		errorStr = helper_functions.roundToSF(error, NUMBER_OF_SF)
		fr.relativeSquaredError_E.insertNew(errorStr)

		# Equation
		equationStr = "T = " + coefficientStr
		if exponent > 0:
			equationStr += "exp(-" + exponentStr + "x)"
		elif exponent < 0:
			equationStr += "exp(" + exponentStr[1:] + "x)"
		fr.equation_E.insertNew(equationStr)



		############
		## Graphs ##
		############
		
		# Model

		endXs = limits[1:-1] + [1.5*max(self.sqrtAreaKM)-0.5*min(self.sqrtAreaKM)]

		for i in range(n):
			xs = helper_functions.getStaggeredPoints(limits[i], endXs[i], MODEL_PLOTTING_PRECISION)
			ys = [thicknessFunction(x) for x in xs]
			self.modelGraphFrame.plotFilledLine(xs, ys, color=colours[i])

		# Regression
		logThicknessM = [np.log(t) for t in self.thicknessM]
		self.regressionGraphFrame.plotScatter(self.sqrtAreaKM, logThicknessM, False)
		self.regressionGraphFrame.axes.set_xlabel(r"$\sqrt{Area}$")
		
		for i in range(n):
			xs = [limits[i], endXs[i]]
			ys = [np.log(thicknessFunction(x)) for x in xs]
			self.regressionGraphFrame.plotLine(xs,ys, color=colours[i])
		
	def _updatePow(self):
		
		###########
		## Stats ##
		###########

		fr = self.statsFrame

		# Coefficient
		c = self.currentParameters["coefficient"]
		coefficientStr = helper_functions.roundToSF(c, NUMBER_OF_SF)
		fr.powCoefficient_E.insertNew(coefficientStr)

		# Exponent
		m = self.currentParameters["exponent"] 
		exponentStr = helper_functions.roundToSF(m, NUMBER_OF_SF)
		fr.powExponent_E.insertNew(exponentStr)

		# Proximal limit
		proximalLimitKM = self.currentParameters["proximalLimitKM"]
		proximalLimitStr = helper_functions.roundToSF(proximalLimitKM, NUMBER_OF_SF)
		fr.powProximalLimit_E.insertNew(proximalLimitStr)
		
		# Distal limit
		distalLimitKM = self.currentParameters["distalLimitKM"]
		distalLimitStr = helper_functions.roundToSF(distalLimitKM, NUMBER_OF_SF)
		fr.powDistalLimit_E.insertNew(distalLimitStr)
		
		# Volume
		volume = calculatePowerLawVolume(c, m, proximalLimitKM, distalLimitKM)
		volumeStr = helper_functions.roundToSF(volume, NUMBER_OF_SF)
		fr.totalEstimatedVolume_E.insertNew(volumeStr)

		# Error
		thicknessFunction = lambda x : c*(x**(-m))
		error = regression_methods.meanRelativeSquaredError(self.sqrtAreaKM, self.thicknessM, thicknessFunction)
		errorStr = helper_functions.roundToSF(error, NUMBER_OF_SF)
		fr.relativeSquaredError_E.insertNew(errorStr)

		# Equation
		equationStr = "T = " + coefficientStr
		if m > 0:
			equationStr += "x^-" + exponentStr
		elif m < 0:
			equationStr += "x^" + exponentStr[1:]
		fr.equation_E.insertNew(equationStr)

		# Suggested proximal limit
		suggestedProximalLimit = self.currentParameters["suggestedProximalLimit"]
		suggestedProximalLimitStr = helper_functions.roundToSF(suggestedProximalLimit, NUMBER_OF_SF)
		fr.powSuggestedProximalLimit_E.insertNew(suggestedProximalLimitStr)


		############
		## Graphs ##
		############

		startX = proximalLimitKM*SQRT_PI
		endX = distalLimitKM*SQRT_PI

		# Model
		xs = helper_functions.getStaggeredPoints(startX, endX, MODEL_PLOTTING_PRECISION)
		ys = [thicknessFunction(x) for x in xs]
		self.modelGraphFrame.plotFilledLine(xs, ys, color=colours[0])

		# Regression
		logXs = [np.log(a) for a in self.sqrtAreaKM]
		logYs = [np.log(t) for t in self.thicknessM]
		self.regressionGraphFrame.plotScatter(logXs, logYs, False)

		self.regressionGraphFrame.axes.set_xlabel(r"$\log{\sqrt{Area}}$")
		lineXs = [np.sqrt(startX), np.sqrt(endX)]
		lineYs = [np.log(c) - m*x for x in lineXs]
		self.regressionGraphFrame.plotLine(lineXs, lineYs, colours[0])

	def _updateWei(self):
		
		###########
		## Stats ##
		###########

		fr = self.statsFrame

		# lambda
		lamb = self.currentParameters["lambda"]
		lambdaStr = helper_functions.roundToSF(lamb, NUMBER_OF_SF)
		fr.weiLambdaE.insertNew(lambdaStr)

		# k
		k = self.currentParameters["k"]
		kStr = helper_functions.roundToSF(k, NUMBER_OF_SF)
		fr.weiKE.insertNew(kStr)

		# theta
		theta = self.currentParameters["theta"]
		thetaStr = helper_functions.roundToSF(theta, NUMBER_OF_SF)
		fr.weiThetaE.insertNew(thetaStr)

		# Volume
		volume = calculateWeibullVolume(lamb, k, theta)
		volumeStr = helper_functions.roundToSF(volume, NUMBER_OF_SF)
		fr.totalEstimatedVolume_E.insertNew(volumeStr)

		# Error
		thicknessFunction = lambda x : theta*((x/lamb)**(k-2))*math.exp(-((x/lamb)**k))
		error = regression_methods.meanRelativeSquaredError(self.sqrtAreaKM, self.thicknessM, thicknessFunction)
		errorStr = helper_functions.roundToSF(error, NUMBER_OF_SF)
		fr.relativeSquaredError_E.insertNew(errorStr)

		# Equation
		invLambdaStr = helper_functions.roundToSF(1/lamb, NUMBER_OF_SF)
		kminus2Str = helper_functions.roundToSF(k-2, NUMBER_OF_SF)
		equationStr = "T = " + thetaStr + "((" + invLambdaStr + "x)^" +kminus2Str + ")exp(-(" + invLambdaStr + "x)^" + kStr + ")"
		fr.equation_E.insertNew(equationStr)




		############
		## Graphs ##
		############

		# Model
		startX = 0
		endX = (self.isopachs[-1].distanceFromVentKM()+50)*SQRT_PI
		xs = helper_functions.getStaggeredPoints(startX,endX,MODEL_PLOTTING_PRECISION)[1:]
		ys = [theta*((x/lamb)**(k-2))*math.exp(-((x/lamb)**k)) for x in xs]
		self.modelGraphFrame.plotFilledLine(xs, ys, colours[0])
												   
	def _displayErrorSurface(self,event):
		
		try:
			xLL, xUL, yLL, yUL, resolution = self.errorSurfaceFrame.getSurfaceParameters()
		except ValueError as ve:
			messagebox.showerror("Calculation error", ve.args[0])
			return
		
		self.graphNotebook.addFrame(self.errorSurfaceGraphFrame, text="Error surface")
		if self.errorSurfaceFrame.xSymbol == "\u03BB":
			self.errorSurfaceGraphFrame.axes.set_xlabel("$\lambda$")
		else:
			self.errorSurfaceGraphFrame.axes.set_xlabel(self.errorSurfaceFrame.xSymbol)
		
		xs = [isopach.sqrtAreaKM for isopach in self.isopachs]
		ys = [isopach.thicknessM for isopach in self.isopachs]

		if self.modelType == Model.POW:
			def errorFunction(c,m):
				thicknessFunction = lambda x : c*(x**(-m))
				return math.log(regression_methods.meanRelativeSquaredError(xs, ys, thicknessFunction))

		elif self.modelType == Model.WEI:
			def errorFunction(lamb,k):
				theta = calculateTheta(xs,ys,lamb,k)
				def thicknessFunction(x):
					try:
						return np.exp(np.log(theta)+(k-2)*np.log(x/lamb)-(x/lamb)**k)
					except FloatingPointError:
						return 0
				mrse = regression_methods.meanRelativeSquaredError(xs, ys, thicknessFunction)
				return math.log(mrse)

		self.errorSurfaceGraphFrame.axes.set_ylabel(self.errorSurfaceFrame.ySymbol)
		self.errorSurfaceGraphFrame.clear()
		self.errorSurfaceGraphFrame.plotSurface(errorFunction, xLL, xUL, yLL, yUL, resolution)

		self.graphNotebook.select(self.errorSurfaceGraphFrame)
	

	def _parametersReset(self,event):
		self.currentParameters = deepcopy(self.defaultParameters)
		self._updateDisplay()
	
	def _parametersChanged(self,event):
		
		try:
			newValues = self.statsFrame.getParameters(self.modelType)
		except ValueError as ve:
			messagebox.showerror("Calculation error", ve.args[0])
			return

		if self.modelType == Model.EXP:
			self.currentParameters["segmentCoefficients"][self.currentSegment] = newValues["c"]
			self.currentParameters["segmentExponents"][self.currentSegment] = newValues["m"]
			self.currentParameters["segmentLimits"][self.currentSegment] = newValues["segStart"]
			self.currentParameters["segmentLimits"][self.currentSegment+1] = newValues["segEnd"]
		elif self.modelType == Model.POW:
			self.currentParameters["coefficient"] = newValues["c"]
			self.currentParameters["exponent"] = newValues["m"]
		elif self.modelType == Model.WEI:
			self.currentParameters["lambda"] = newValues["lambda"]
			self.currentParameters["k"] = newValues["k"]
			self.currentParameters["theta"] = newValues["theta"]

		self._updateDisplay()
	
	def clear(self):

		if self.modelType is not None:
			for component in self.statsFrame.components[self.modelType]:
				component.grid_remove()

			self.statsFrame.grid_remove()
			self.graphNotebook.grid_remove()
			self.errorSurfaceFrame.grid_remove()
			self.errorSurfaceSeperator.grid_remove()

			self.config(text="Results")

			self.modelGraphFrame.clear()
			self.regressionGraphFrame.clear()
			self.errorSurfaceGraphFrame.clear()

			self.graphNotebook.removeFrame(self.regressionGraphFrame)
			self.graphNotebook.removeFrame(self.errorSurfaceGraphFrame)

		self.modelType = None

class StatsFrame(LabelFrame):
	
	def __init__(self,parent, padX, padY):
		
		LabelFrame.__init__(self,parent,borderwidth=0)
		
		# Total volume
		self.totalEstimatedVolume_L = Label(self,text="Estimated total volume (km\u00B3): ")
		self.totalEstimatedVolume_E = CustomEntry(self,width=10, justify="right")
		self.totalEstimatedVolume_E.setUserEditable(False)
		self.totalEstimatedVolume_E.grid(row=0,column=1,padx=10,sticky="E")
		self.totalEstimatedVolume_L.grid(row=0,column=0,sticky="W",padx=10,pady=0)
		
		# Relative squared error
		self.relativeSquaredError_L = Label(self,text="Mean relative squared error: ")
		self.relativeSquaredError_L.grid(row=1,column=0,sticky="W",padx=10,pady=padY)
		self.relativeSquaredError_E = CustomEntry(self,width=10, justify="right")
		self.relativeSquaredError_E.grid(row=1,column=1,padx=10,sticky="E")
		self.relativeSquaredError_E.setUserEditable(False)
		
		# Equation
		self.equation_L = Label(self,text="Equation: ")
		self.equation_E = CustomEntry(self,width=10, justify="right")
		self.equation_E.setUserEditable(False)

		# General
		self.parameters_L = Label(self,text="Parameters:")
		self.calculate_B = Button(self,text="Recalculate",width=10)
		self.reset_B = Button(self,text="Reset",width=10)



		#########
		## Exp ##
		#########

		# Segment combobox
		self.expSeg_CB = Combobox(self,state="readonly",width=10)

		# Segment volume
		self.expSegVolume_L = Label(self,text="Segment volume (km\u00B3): ")
		self.expSegVolume_E = CustomEntry(self,width=10, justify="right")
		self.expSegVolume_E.setUserEditable(False)
		
		# Segment start
		self.expSegStartLimit_L = Label(self,text="Start of segment: ")
		self.expSegStartLimit_E = CustomEntry(self,width=10, justify="right")
		
		# Segment end
		self.expSegEndLimit_L = Label(self,text="End of segment: ")
		self.expSegEndLimit_E = CustomEntry(self,width=10, justify="right")
		
		# Segment coefficient
		self.expSegCoefficent_L = Label(self,text="Segment coefficient, c: ")
		self.expSegCoefficent_E = CustomEntry(self,width=10, justify="right")
		
		# Segment exponent
		self.expSegExponent_L = Label(self,text="Segment exponent, m: ")
		self.expSegExponent_E = CustomEntry(self,width=10, justify="right")
		
		

		#########
		## Pow ##
		#########

		# Coefficient
		self.powCoefficient_L = Label(self,text="Coefficient, c: ")
		self.powCoefficient_E = CustomEntry(self,width=10, justify="right")
		
		# Exponent
		self.powExponent_L = Label(self,text="Exponent, m: ")
		self.powExponent_E = CustomEntry(self,width=10, justify="right")
		
		# Proximal limit
		self.powProximalLimit_L = Label(self,text="Proximal limit: ")
		self.powProximalLimit_E = CustomEntry(self,width=10, justify="right")
		
		# Distal limit
		self.powDistalLimit_L = Label(self,text="Distal limit: ")
		self.powDistalLimit_E = CustomEntry(self,width=10, justify="right")
		
		# Suggested proximal limit
		self.powSuggestedProximalLimit_L = Label(self,text="Suggested proximal limit: ")
		self.powSuggestedProximalLimit_E = CustomEntry(self,width=10, justify="right")
		self.powSuggestedProximalLimit_E.setUserEditable(False)

		

		#########
		## Wei ##
		#########

		# lambda
		self.weiLambdaL = Label(self,text="Estimated \u03BB: ")
		self.weiLambdaE = CustomEntry(self,width=10, justify="right")
		
		# k
		self.weiKL = Label(self,text="Estimated k: ")
		self.weiKE = CustomEntry(self,width=10, justify="right")
		
		# theta
		self.weiThetaL = Label(self,text="Estimated \u03B8: ")
		self.weiThetaE = CustomEntry(self,width=10, justify="right")
		


		self.components = {
			Model.EXP : [
				self.expSeg_CB,
				self.expSegVolume_L, self.expSegVolume_E, 
				self.expSegStartLimit_L, self.expSegStartLimit_E,
				self.expSegEndLimit_L, self.expSegEndLimit_E,
				self.expSegCoefficent_L, self.expSegCoefficent_E,
				self.expSegExponent_L, self.expSegExponent_E
			],

			Model.POW : [
				self.powCoefficient_L, self.powCoefficient_E,
				self.powExponent_L, self.powExponent_E,
				self.powProximalLimit_L, self.powProximalLimit_E,
				self.powDistalLimit_L, self.powDistalLimit_E,
				self.powSuggestedProximalLimit_L, self.powSuggestedProximalLimit_E
			],

			Model.WEI : [
				self.weiLambdaL, self.weiLambdaE,
				self.weiKL, self.weiKE,
				self.weiThetaL, self.weiThetaE,
			],

		}

	def getParameters(self, model):
		if model == Model.EXP:
			return {
				"c" : 			helper_functions.validateValue(self.expSegCoefficent_E.get(), 	"Coefficient, c, must be a number", 									"float"),
				"m" : 			helper_functions.validateValue(self.expSegExponent_E.get(), 	"Exponent, m, must be a number", 										"float"),
				"segStart" : 	helper_functions.validateValue(self.expSegStartLimit_E.get(), 	"'Start of segment' must be a number > 0", 								"float", lowerBound=0),
				"segEnd" : 		helper_functions.validateValue(self.expSegEndLimit_E.get(), 	"'End of segment' must be a number greater than the 'Start of segment'","float", strictLowerBound=float(self.expSegStartLimit_E.get())),
			}
		elif model == Model.POW:
			return {
				"c" : 			helper_functions.validateValue(self.powCoefficient_E.get(), "coefficient, c, must be a number", "float"),
				"m" : 			helper_functions.validateValue(self.powExponent_E.get(), 	"exponent, m, must be a number", 	"float")
			}
		elif model == Model.WEI:
			return {
				"lambda" : 		helper_functions.validateValue(self.weiLambdaE.get(), 	"\u03BB must be a positive number", "float", strictLowerBound=0),
				"k" : 			helper_functions.validateValue(self.weiKE.get(), 		"k must be a positive number", 		"float", strictLowerBound=0),
				"theta" : 		helper_functions.validateValue(self.weiThetaE.get(), 	"\u03B8 must be a positive number", "float", strictLowerBound=0)
			}

class ErrorSurfaceFrame(LabelFrame):
	
	def __init__(self,parent):
		LabelFrame.__init__(self, parent, borderwidth=0)
		
		entryWidth = 7
		xPad1 = 30
		xPad2 = 5
		
		self.errorXLowerLimitL = Label(self)
		self.errorXLowerLimitE = CustomEntry(self,width=entryWidth,justify="right")
		self.errorXLowerLimitL.grid(row=0,column=0,padx=(10,xPad2),pady=5,sticky="W")
		self.errorXLowerLimitE.grid(row=0,column=1,padx=(xPad2,xPad1),pady=5)
		
		self.errorXUpperLimitL = Label(self)
		self.errorXUpperLimitE = CustomEntry(self,width=entryWidth,justify="right")
		self.errorXUpperLimitL.grid(row=1,column=0,padx=(10,xPad2),pady=5,sticky="W")
		self.errorXUpperLimitE.grid(row=1,column=1,padx=(xPad2,xPad1),pady=5)
		
		self.errorYLowerLimitL = Label(self)
		self.errorYLowerLimitE = CustomEntry(self,width=entryWidth,justify="right")
		self.errorYLowerLimitL.grid(row=0,column=2,padx=(xPad1,xPad2),pady=5,sticky="W")
		self.errorYLowerLimitE.grid(row=0,column=3,padx=(xPad2,xPad1),pady=5)
		
		self.errorYUpperLimitL = Label(self)
		self.errorYUpperLimitE = CustomEntry(self,width=entryWidth,justify="right")
		self.errorYUpperLimitL.grid(row=1,column=2,padx=(xPad1,xPad2),pady=5,sticky="W")
		self.errorYUpperLimitE.grid(row=1,column=3,padx=(xPad2,xPad1),pady=5)
		
		self.errorResolutionL = Label(self,text="Resolution: ")
		self.errorResolutionE = CustomEntry(self,width=entryWidth,justify="right")
		self.errorResolutionE.insert(0,ERROR_SURFACE_DEFAULT_RESOLUTION)
		self.errorResolutionL.grid(row=0,column=4,padx=(xPad1,xPad2),pady=5,sticky="W")
		self.errorResolutionE.grid(row=0,column=5,padx=(xPad2,xPad1),pady=5,sticky="E")
		
		self.errorSurfaceB = Button(self,text=" Calculate error surface ")
		self.errorSurfaceB.grid(row=1,column=4,columnspan=2,padx=(xPad1,xPad1),sticky="EW")
		self.errorSurfaceB.configure(state=tkinter.ACTIVE)
		
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

		self.figure = pyplot.Figure(figsize=(5.5,3.2), facecolor=(240/255,240/255,237/255))
		self.figure.subplots_adjust(left=0.15, bottom=0.2)

		self.canvas = FigureCanvas(self.figure, master=self)
		self.canvas.get_tk_widget().pack()
		self.canvas.get_tk_widget().configure(highlightthickness=0)

		toolbar = CutDownNavigationToolbar(self.canvas,self)
		toolbar.pack()
		
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