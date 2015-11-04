from tkinter.ttk import LabelFrame, Button, Progressbar

class CalculationFrame(LabelFrame):
	
	def __init__(self,parent):
		LabelFrame.__init__(self,parent,text="Calculate",borderwidth=5)       
		 
		self.startCalculationB = Button(self,text="Start calculation",width=20)
		self.startCalculationB.grid(row=0,column=0,padx=10,pady=5)
		self.endCalculationB = Button(self,text="Cancel calculation",width=20)
		self.endCalculationB.grid(row=1,column=0,padx=10,pady=5)
		self.calculationPB = Progressbar(self, mode="indeterminate",length=128)
		self.calculationPB.grid(row=2,column=0,padx=10,pady=5)