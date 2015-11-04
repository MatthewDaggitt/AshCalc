import tkinter
from tkinter.ttk import LabelFrame, Button, Frame, Scrollbar, Label, Entry, Checkbutton

from core.isopach import Isopach

from desktop import tooltip
from desktop import helper_functions
from desktop.custom_components import ScrollFrame

MINIMUM_NUMBER_OF_ISOPACHS = 2
DEFAULT_NUMBER_OF_ISOPACHS = 6

IMAGE_DIR = "images/"

class IsopachFrame(LabelFrame):
    
    def __init__(self,parent,calculationTimeEstimationFunction):
        
        LabelFrame.__init__(self,parent,text="Isopachs",borderwidth=5)
        self.numberOfIsopachs = DEFAULT_NUMBER_OF_ISOPACHS
        self.calculationTimeEstimationFunction = calculationTimeEstimationFunction
        
        self.buttonWidth = 14
        
        photo = tkinter.PhotoImage(file=IMAGE_DIR + "open_file-icon.gif")
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
        
        tooltip.createToolTip(self.loadFromFileButton,"Load isopach data from a comma seperated value file of the form: \n\n\tthickness1,\u221AArea1\n\tthickness2,\u221AArea2\n\t...\n\nwith thickness in metres and \u221AArea in kilometres")
        
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
        isopach_L.grid(column=0, row=rowNumber+2, padx=(0,10), pady=5)
        
        thicknessVar = tkinter.StringVar()
        thicknessM_E = Entry(self.innerFrame,width=10,textvariable=thicknessVar)
        thicknessM_E.grid(column=1, row=rowNumber+2, pady=5)
        #thicknessM_E.insert(0,rowNumber+1)
        
        areaVar = tkinter.StringVar()
        sqrtAreaKM_E = Entry(self.innerFrame,width=10,textvariable=areaVar)
        sqrtAreaKM_E.grid(column=2, row=rowNumber+2, pady=5)
        #sqrtAreaKM_E.insert(0,2*math.log(math.sqrt(rowNumber+2)))
        
        includeVar = tkinter.IntVar()
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
                thicknessM = helper_functions.validateValue(
                                thicknessStr,
                                    "Isopach " + str(index+1) + "'s thickness must be a strictly positive number",
                                         "float",
                                           strictLowerBound=0)
                sqrtAreaKM = helper_functions.validateValue(sqrtAreaStr,
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