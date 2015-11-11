import tkinter
from tkinter.ttk import LabelFrame, Radiobutton, Separator, Label, Entry
import numpy as np

from desktop import settings
from desktop import helper_functions
from desktop import tooltip

from desktop.settings import Model
from desktop.custom_components import CustomEntry


SQRT_PI = np.sqrt(np.pi)

class ModelFrame(LabelFrame):
	
	topPadding = 12

	def __init__(self,parent):        
		LabelFrame.__init__(self,parent,text="Model",borderwidth=5)
		
		self.selection = tkinter.IntVar()
		
		self.exponential = Radiobutton(self,text="Exponential model",variable=self.selection,value=Model.EXP.value,command=self.changeSelection)
		self.powerlaw = Radiobutton(self,text="Power law model",variable=self.selection,value=Model.POW.value,command=self.changeSelection)
		self.weibull = Radiobutton(self,text="Weibull model",variable=self.selection,value=Model.WEI.value,command=self.changeSelection)

		self.exponential.grid(row=0,column=0,sticky="W",padx=10,pady=(self.topPadding,5))
		self.powerlaw.grid(row=1,column=0,sticky="W",padx=10,pady=5)
		self.weibull.grid(row=2,column=0,sticky="W",padx=10,pady=(5,0))
		
		seperator = Separator(self, orient=tkinter.VERTICAL)
		seperator.grid(row=0, column=1, rowspan=3, sticky="NS", padx=(20,10), pady=(self.topPadding,0))
		
		## Exponential setup

		self.expNumberOfSegments_L = Label(self,text="Number of segments: ")
		self.expNumberOfSegments_E = Entry(self,width=5, justify="right")

		self.expNumberOfSegments_E.insert(0, settings.EXP_DEFAULT_NUMBER_OF_SEGMENTS)

		self.expWidgets = [self.expNumberOfSegments_L,self.expNumberOfSegments_E]
		
		## Power law setup

		self.powProximalLimit_L = Label(self,text="Proximal limit of integration: ")
		self.powProximalLimit_E = Entry(self,width=5, justify="right")
		self.powDistalLimit_L = Label(self,text="Distal limit of integration: ")
		self.powDistalLimit_E = Entry(self,width=5, justify="right")

		self.powProximalLimit_E.insert(0, settings.POW_DEFAULT_PROXIMAL_LIMIT)
		self.powDistalLimit_E.insert(0, settings.POW_DEFAULT_DISTAL_LIMIT)

		self.powWidgets = [self.powProximalLimit_L,self.powProximalLimit_E,
						   self.powDistalLimit_L,self.powDistalLimit_E]
		
		## Weibull setup

		self.weiNumberOfRuns_L = Label(self,text="Number of runs: ")
		self.weiNumberOfRuns_E = Entry(self,width=5, justify="right")
		self.weiIterationsPerRun_L = Label(self,text="Iterations per run: ")
		self.weiIterationsPerRun_E = Entry(self,width=5, justify="right")

		self.weiEstimatedTime_L = Label(self,text="Estimated time (s): ")
		self.weiEstimatedTime_E = CustomEntry(self,width=5, justify="right")
		self.weiEstimatedTime_E.setUserEditable(False)

		self.weiLambdaLowerBoundL = Label(self,text="\u03BB lower bound:")
		self.weiLambdaUpperBoundL = Label(self,text="\u03BB upper bound:")
		self.weiLambdaLowerBoundE = Entry(self,width=5, justify="right")
		self.weiLambdaUpperBoundE = Entry(self,width=5, justify="right")

		self.weiKLowerBoundL = Label(self,text="k lower bound:")
		self.weiKUpperBoundL = Label(self,text="k upper bound:")
		self.weiKLowerBoundE = Entry(self,width=5, justify="right")
		self.weiKUpperBoundE = Entry(self,width=5, justify="right")

		self.weiNumberOfRuns_E.insert(0, settings.WEI_DEFAULT_NUMBER_OF_RUNS)
		self.weiIterationsPerRun_E.insert(0, settings.WEI_DEFAULT_ITERATIONS_PER_RUN)
		self.weiLambdaLowerBoundE.insert(0, settings.WEI_DEFAULT_LAMBDA_LOWER_BOUND)
		self.weiLambdaUpperBoundE.insert(0, settings.WEI_DEFAULT_LAMBDA_UPPER_BOUND)
		self.weiKLowerBoundE.insert(0, settings.WEI_DEFAULT_K_LOWER_BOUND)
		self.weiKUpperBoundE.insert(0, settings.WEI_DEFAULT_K_UPPER_BOUND)

		tooltip.createToolTip(self.weiNumberOfRuns_E,"The number of possible sets of parameters that are generated.\nThe final parameters returned are the set which best fit the data.\n\nSee the instruction manual for further details.");
		tooltip.createToolTip(self.weiIterationsPerRun_E,"The number of times the current parameters are adjusted\nwithin each run.\n\nSee the instruction manual for further details.");
		tooltip.createToolTip(self.weiEstimatedTime_E,"A rough estimate of the time required to execute this computation.");
		
		self.weiWidgets = [self.weiNumberOfRuns_L,self.weiNumberOfRuns_E,
						   self.weiIterationsPerRun_L,self.weiIterationsPerRun_E,
						   self.weiEstimatedTime_L,self.weiEstimatedTime_E,
						   self.weiLambdaLowerBoundL,self.weiLambdaUpperBoundL,self.weiLambdaLowerBoundE,self.weiLambdaUpperBoundE,
						   self.weiKLowerBoundL,self.weiKUpperBoundL,self.weiKLowerBoundE,self.weiKUpperBoundE]
		
		## General

		self.currentWidgets = []
		self.selection.set(Model.EXP.value)
		self.changeSelection()
		
	def changeSelection(self):
		
		for widget in self.currentWidgets:
			widget.grid_remove()

		modelType = Model(self.selection.get())
		
		sX = 10
		bX = 20
		
		if modelType == Model.EXP:
			self.expNumberOfSegments_L.grid(row=0,column=2,padx=(bX,sX),pady=(self.topPadding,5),sticky="W")
			self.expNumberOfSegments_E.grid(row=0,column=3,padx=(sX,bX),pady=(self.topPadding,5),sticky="W")
			self.currentWidgets = self.expWidgets
		elif modelType == Model.POW:
			self.powProximalLimit_L.grid(row=0,column=2,padx=(bX,sX),pady=(self.topPadding,5),sticky="W")
			self.powProximalLimit_E.grid(row=0,column=3,padx=(sX,bX),pady=(self.topPadding,5),sticky="W")
			self.powDistalLimit_L.grid(row=1,column=2,padx=(bX,sX),pady=5,sticky="W")
			self.powDistalLimit_E.grid(row=1,column=3,padx=(sX,bX),pady=5,sticky="W")
			self.currentWidgets = self.powWidgets
		elif modelType == Model.WEI:
			self.weiNumberOfRuns_L.grid(row=0,column=2,padx=(bX,sX),pady=(self.topPadding,5),sticky="W")
			self.weiNumberOfRuns_E.grid(row=0,column=3,padx=(sX,bX),pady=(self.topPadding,5),sticky="W")
			self.weiIterationsPerRun_L.grid(row=1,column=2,padx=(bX,sX),pady=5,sticky="W")
			self.weiIterationsPerRun_E.grid(row=1,column=3,padx=(sX,bX),pady=5,sticky="W")
			self.weiEstimatedTime_L.grid(row=2,column=2,padx=(bX,sX),pady=5,sticky="W")
			self.weiEstimatedTime_E.grid(row=2,column=3,padx=(sX,bX),pady=5,sticky="W")
			
			self.weiLambdaLowerBoundL.grid(row=0,column=4,padx=(bX,sX),pady=(self.topPadding,5),sticky="W")
			self.weiLambdaLowerBoundE.grid(row=0,column=5,padx=(sX,bX),pady=(self.topPadding,5))
			self.weiLambdaUpperBoundL.grid(row=1,column=4,padx=(bX,sX),pady=5,sticky="W")
			self.weiLambdaUpperBoundE.grid(row=1,column=5,padx=(sX,bX),pady=5)
			
			self.weiKLowerBoundL.grid(row=0,column=6,padx=(bX,sX),pady=(self.topPadding,5),sticky="W")
			self.weiKLowerBoundE.grid(row=0,column=7,padx=(sX,bX),pady=(self.topPadding,5))
			self.weiKUpperBoundL.grid(row=1,column=6,padx=(bX,sX),pady=5,sticky="W")
			self.weiKUpperBoundE.grid(row=1,column=7,padx=(sX,bX),pady=5)
			
			self.currentWidgets = self.weiWidgets
	
	def getModelDetails(self):
		modelType = Model(self.selection.get())
		values = [modelType]

		if modelType == Model.EXP:
			numberOfSegments = helper_functions.validateValue(
									self.expNumberOfSegments_E.get(),
									"The number of exponential segments must be 1 \u2264 n \u2264 " + str(settings.EXP_MAX_NUMBER_OF_SEGMENTS),
									"int",
									lowerBound=1,
									upperBound=settings.EXP_MAX_NUMBER_OF_SEGMENTS)
			values.append(numberOfSegments)
			
		elif modelType == Model.POW:
			proximalLimitKM = helper_functions.validateValue(
									self.powProximalLimit_E.get(),
									"The proximal limit of integration must be 0 \u2264 x \u2264 \u221E",
									"float",
									strictLowerBound=0,
									strictUpperBound=float('inf'))
			proximalLimitKM /= SQRT_PI
			
			distalLimitKM = helper_functions.validateValue(
									self.powDistalLimit_E.get(),
									"The distal limit of integration must be prox \u2264 x \u2264 \u221E",
									"float",
									strictLowerBound=proximalLimitKM,
									strictUpperBound=float('inf'))
			distalLimitKM /= SQRT_PI
			
			values.extend([proximalLimitKM,distalLimitKM])
			
		elif modelType == Model.WEI:
			numberOfRuns = helper_functions.validateValue(
									self.weiNumberOfRuns_E.get(),
									"The number of runs must be greater than 0",
									"int",
									strictLowerBound=0)
			
			iterationsPerRun = helper_functions.validateValue(
									self.weiIterationsPerRun_E.get(),
									"The number of iterations must be greater than 0",
									"int",
									strictLowerBound=0)
			
			lambdaLowerBound = helper_functions.validateValue(
									self.weiLambdaLowerBoundE.get(),
									"The lower bound for \u03BB must be a decimal",
									"float")
			  
			lambdaUpperBound = helper_functions.validateValue(
									self.weiLambdaUpperBoundE.get(),
									"The upper bound for \u03BB must be greater than the lower bound",
									"float",
									strictLowerBound=lambdaLowerBound)
			
			kLowerBound = helper_functions.validateValue(
									self.weiKLowerBoundE.get(),
									"The lower bound for k must be numeric and less than 2",
									"float",
									strictUpperBound=2)
												
			kUpperBound = helper_functions.validateValue(
									self.weiKUpperBoundE.get(),
									"The upper bound for k must be greater than the lower bound and less than or equal to 2",
									"float",
									strictLowerBound=kLowerBound,
									upperBound=2)
			
			values.extend([numberOfRuns,iterationsPerRun,[[lambdaLowerBound,lambdaUpperBound],[kLowerBound,kUpperBound]]])
		
		return values