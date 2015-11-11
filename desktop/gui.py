'''
Created on 15 Aug 2013

@author: Matthew Daggitt
'''
import math

import tkinter
from tkinter import messagebox

import numpy as np
np.seterr(all="ignore")

from core.isopach import Isopach

from desktop.settings import Model
from desktop import helper_functions
from desktop.thread_handlers import ThreadHandler
from desktop.timing_module import createWeibullTimingEstimationFunction
from desktop import tooltip

from desktop.frames.model_frame import ModelFrame
from desktop.frames.isopach_frame import IsopachFrame
from desktop.frames.calculation_frame import CalculationFrame
from desktop.frames.results_frame import ResultsFrame

######### Themes ###########

desiredOrder = ["aqua","vista","xpnative","clam"]

for theme in desiredOrder:
	if theme in tkinter.ttk.Style().theme_names():
		tkinter.ttk.Style().theme_use(theme)
		break

############################

class App(tkinter.ttk.Frame):
	
	def __init__(self):
		tkinter.ttk.Frame.__init__(self)
		self.master.title("AshCalc")
		
		self.threadHandler = ThreadHandler()
		self.calculating = False
		self.weibullTimingEstimationFunction = createWeibullTimingEstimationFunction()
		
		self.calculationFrame = CalculationFrame(self)
		self.calculationFrame.grid(row=0,column=0,sticky="NSWE",padx=(10,5),pady=10)
		self.calculationFrame.startCalculationB.bind("<Button-1>",self.startCalculation)
		self.calculationFrame.endCalculationB.configure(state=tkinter.DISABLED)

		self.isopachFrame = IsopachFrame(self,self.estimateWeibullCalculationTime)
		self.isopachFrame.grid(row=1,column=0,padx=10,sticky="NS",pady=10)
		
		self.modelFrame = ModelFrame(self)
		self.modelFrame.grid(row=0,column=1,sticky="NESW",padx=10,pady=10)
		self.modelFrame.weiNumberOfRuns_E.bind("<KeyRelease>",self.estimateWeibullCalculationTime)
		self.modelFrame.weiIterationsPerRun_E.bind("<KeyRelease>",self.estimateWeibullCalculationTime)
		self.estimateWeibullCalculationTime(None)

		self.resultsFrame = ResultsFrame(self)
		self.resultsFrame.grid(row=1,column=1,padx=10,sticky="NSEW",pady=10)

		self.isopachFrame.loadData([Isopach(16.25, 0.4),Isopach(30.63, 0.2),Isopach(58.87,0.1),Isopach(95.75,0.05),Isopach(181.56,0.02),Isopach(275.1,0.01)])

		self.createTooltips()

		self.pack()
		self.mainloop()
		
	def startCalculation(self, event):
		
		try:
			isopachs = self.isopachFrame.getData()
			modelDetails = self.modelFrame.getModelDetails()
			self.threadHandler.startCalculation(modelDetails[0], [isopachs] + modelDetails[1:])

		except ValueError as ve:
			messagebox.showerror("Calculation error", ve.args[0])
			return
		
		self.resultsFrame.clear()

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
			modelType, results = result
			if modelType == "Error":
				messagebox.showerror("Calculation error", results.args[0])
			else:
				self.resultsFrame.displayNewModel(modelType,results)
			self.finishCalculation(None)
		elif self.calculating:
			self.after(100, self.poll)
	
	def finishCalculation(self,_):
		self.threadHandler.cancelLastCalculation()
		self.calculating = False
		self.calculationFrame.startCalculationB.configure(state=tkinter.ACTIVE)
		self.calculationFrame.startCalculationB.bind("<Button-1>", self.startCalculation)
		self.calculationFrame.endCalculationB.configure(state=tkinter.DISABLED)
		self.calculationFrame.endCalculationB.unbind("<Button-1>")
		self.calculationFrame.calculationPB.stop()

	def estimateWeibullCalculationTime(self,event):
		try:
			numberOfIsopachs = self.isopachFrame.getNumberOfIncludedIsopachs()
			numberOfRuns = int(self.modelFrame.weiNumberOfRuns_E.get())
			iterationsPerRun = int(self.modelFrame.weiIterationsPerRun_E.get())
			if numberOfRuns <= 0 or iterationsPerRun <= 0 or numberOfIsopachs <= 0:
				raise ValueError()
			est = self.weibullTimingEstimationFunction(numberOfIsopachs,iterationsPerRun,numberOfRuns)
			self.modelFrame.weiEstimatedTime_E.insertNew(helper_functions.roundToSF(est,2))
		except ValueError:
			self.modelFrame.weiEstimatedTime_E.insertNew("N/A")

	def createTooltips(self):
		statsFrame = self.resultsFrame.statsFrame

		tooltip.createToolTip

		tips = [
			(statsFrame.totalEstimatedVolume_E, 		"The model's estimate for the total volume of the tephra deposit."),
			(statsFrame.relativeSquaredError_E, 		"A measure of the goodness of fit of the model. Comparisons are \nonly valid when comparing different models for identical\nisopach data."),
			
			(statsFrame.expSegVolume_E, 				"The model's estimate for the volume of this segment of the tephra deposit."),

			(statsFrame.powSuggestedProximalLimit_E,	"An estimate for the proximal limit of integration as described\nin Bonadonna and Houghton 2005. Requires 4 or more isopachs."),
		
			(self.isopachFrame.loadFromFileButton,		"Load isopach data from a comma seperated value file of the form: \n\n\tthickness1,\u221AArea1\n\tthickness2,\u221AArea2\n\t...\n\nwith thickness in metres and \u221AArea in kilometres"),
		]

		for target, tip in tips:
			tooltip.createToolTip(target, tip)