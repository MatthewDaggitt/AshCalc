import tkinter
from tkinter.ttk import LabelFrame, Button, Frame, Scrollbar, Label, Entry, Checkbutton

from core.isopach import Isopach

from desktop import tooltip
from desktop import helper_functions
from desktop.custom_components import ScrollFrame

MINIMUM_NUMBER_OF_ISOPACHS = 2
DEFAULT_NUMBER_OF_ISOPACHS = 1

IMAGE_DIR = "images/"

class IsopachFrame(LabelFrame):
    
    entryWidth = 8
    buttonWidth = 13

    def __init__(self,parent,calculationTimeEstimationFunction):
        
        LabelFrame.__init__(self,parent,text="Isopachs",borderwidth=5)
        self.numberOfIsopachs = DEFAULT_NUMBER_OF_ISOPACHS
        self.calculationTimeEstimationFunction = calculationTimeEstimationFunction
        
        openButtonImage = tkinter.PhotoImage(file=IMAGE_DIR + "open_file-icon.gif")
        self.tickImage = tkinter.PhotoImage(file=IMAGE_DIR + "tick.gif")
        
        self.loadFromFileButton = Button(self,image=openButtonImage)
        self.loadFromFileButton.grid(row=0,column=0,padx=10,pady=10)
        self.loadFromFileButton.bind("<Button-1>",self.loadFromFile)
        self.loadFromFileButton.image = openButtonImage
        
        self.addButton = Button(self,text="Add isopach",width=self.buttonWidth)
        self.addButton.grid(row=0,column=1,padx=10,pady=10)
        self.addButton.bind("<Button-1>",self.addIsopach)

        self.removeButton = Button(self,text="Remove isopach",width=self.buttonWidth)
        self.removeButton.grid(row=0,column=2,padx=10,pady=10)
        self.removeButton.bind("<Button-1>",self.removeIsopach)
        
        self.scrollFrame = ScrollFrame(self)
        self.scrollFrame.grid(row=1,column=0,columnspan=3, sticky="NS")
        self.innerFrame = self.scrollFrame.innerFrame

        self.grid_rowconfigure(1,weight=0)
        self.grid_rowconfigure(1,weight=1)

        self.rows = [self.createRow(i) for i in range(self.numberOfIsopachs)]
        
        thicknessM_L = Label(self.innerFrame, text="Thickness (m)")
        thicknessM_L.grid(column=1, row=1, padx=5, pady=5)
        sqrtAreaKM_L = Label(self.innerFrame, text="\u221AArea (km)")
        sqrtAreaKM_L.grid(column=2, row=1, padx=5, pady=5)
        include_L = Label(self.innerFrame, text="Use?")
        include_L.grid(column=3, row=1, padx=5, pady=5)
        
    def createRow(self,rowNumber):
        isopach_L = Label(self.innerFrame, text=str(rowNumber+1), width=2)
        isopach_L.grid(column=0, row=rowNumber+2, padx=(0,5), pady=5)
        
        thicknessVar = tkinter.StringVar()
        thicknessM_E = Entry(self.innerFrame,width=self.entryWidth,textvariable=thicknessVar, justify="right")
        thicknessM_E.grid(column=1, row=rowNumber+2, pady=5)
        
        areaVar = tkinter.StringVar()
        sqrtAreaKM_E = Entry(self.innerFrame,width=self.entryWidth,textvariable=areaVar, justify="right")
        sqrtAreaKM_E.grid(column=2, row=rowNumber+2, pady=5)

        includeVar = tkinter.IntVar()
        includeCB = tkinter.Checkbutton(self.innerFrame,variable=includeVar, selectimage=self.tickImage)
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
        values = [(thicknessVar.get(), sqrtAreaVar.get(), includeVar.get()) for (_,_),(_,thicknessVar),(_,sqrtAreaVar),(_,includeVar) in self.rows]
        isopachs = []
        for index, (thicknessStr, sqrtAreaStr, includeInt) in enumerate(values):
            if includeInt == 1:
                thicknessM = helper_functions.validateValue(
                                thicknessStr,
                                "Isopach " + str(index+1) + "'s thickness must be a strictly positive number",
                                "float",
                                strictLowerBound=0)
                sqrtAreaKM = helper_functions.validateValue(
                                sqrtAreaStr,
                                "Isopach " + str(index+1) + "'s area must be a strictly positive number",
                                "float",
                                strictLowerBound=0)
                isopachs.append(Isopach(sqrtAreaKM, thicknessM))
        isopachs = sorted(isopachs, key=lambda i : i.thicknessM, reverse=True)
        
        if len({i.thicknessM for i in isopachs}) != len(isopachs):
            raise ValueError("Isopachs must all have unique thicknesses")
        
        return isopachs
    
    def loadData(self, isopachs):
        current = len(self.rows)
        difference = len(isopachs)-current

        if difference < 0:
            for _ in range(-difference):
                self.removeIsopach(None)
        elif difference > 0:
            for _ in range(difference):
                self.addIsopach(None)
                
        for row, isopach in zip(self.rows, isopachs):
            row[1][1].set(isopach.thicknessM)
            row[2][1].set(isopach.sqrtAreaKM)
            row[3][1].set(1)
            
    def getNumberOfIncludedIsopachs(self):
        return len([None for _,_,_,(_,includeVar) in self.rows if includeVar.get() == 1])
    
    def loadFromFile(self,event):
        print(self.scrollFrame.winfo_width(), self.scrollFrame.winfo_height())
        fileName = tkinter.filedialog.askopenfilename();
        
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