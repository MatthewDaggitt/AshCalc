import tkinter
from tkinter.ttk import Entry, Notebook, Frame, Scrollbar
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar


class CutDownNavigationToolbar(NavigationToolbar):
	# only display the buttons needed
	toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ("Home", "Back", "Forward", "Pan", "Save")]
	
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

class ScrollFrame(Frame):
	
	def __init__(self,parent,width,height):
		
		Frame.__init__(self, master=parent)

		canvas = tkinter.Canvas(self, highlightthickness=0)
		self.innerFrame = Frame(canvas)

		myscrollbar = Scrollbar(self, orient="vertical")
		def setY(command, t1, t2=None):
			top, bottom = myscrollbar.get()
			if top > 0 or bottom < 1:
				if t2:
					canvas.yview(command, t1, t2)
				else:
					canvas.yview(command, t1)
		myscrollbar.configure(command=setY)


		canvas.configure(yscrollcommand = myscrollbar.set)

		configureFunc = lambda _ :  canvas.configure(scrollregion=canvas.bbox("all"), width=width, height=height)
		canvas.create_window((0,0), window=self.innerFrame, anchor='nw')
		self.innerFrame.bind("<Configure>",configureFunc)

		myscrollbar.grid(row=0, column=1, sticky="NS")
		canvas.grid(row=0, column=0)