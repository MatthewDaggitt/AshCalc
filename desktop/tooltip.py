'''
@author: Michael Foord
http://www.voidspace.org.uk/python/weblog
'''
import tkinter

class ToolTip(object):

    def __init__(self, widget, text):
        self.widget = widget
        self.window = None
        self.id = None

        widget.bind('<Enter>', lambda e : self.show(text))
        widget.bind('<Leave>', lambda e : self.hide())

    def show(self, text):

        if self.window or not text:
            return

        "Display text in tooltip window"
        x = self.widget.winfo_width() + self.widget.winfo_rootx() + 5
        y = self.widget.winfo_height() + self.widget.winfo_rooty() + 5
        self.window = tkinter.Toplevel(self.widget)
        self.window.wm_overrideredirect(1)
        self.window.wm_geometry("+%d+%d" % (x, y))
        
        try:
            # For Mac OS
            self.window.tk.call("::tk::unsupported::MacWindowStyle", "style", self.window._w, "help", "noActivates")
        except tkinter.TclError:
            pass

        label = tkinter.ttk.Label(self.window, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("tahoma", "8", "normal"))
        label.grid(row=0, column=0, padx=3)

    def hide(self):
        if self.window:
            self.window.destroy()
            self.window = None

   