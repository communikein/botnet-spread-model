## "pycxsimulator.py"
## Realtime Simulation GUI for PyCX
##
## Developed by:
## Chun Wong
## email@chunwong.net
##
## Revised by:
## Hiroki Sayama
## sayama@binghamton.edu
##
## Copyright 2012 Chun Wong & Hiroki Sayama
##
## Simulation control & GUI extensions for Python 2.7 and 3.0 
## Copyright 2013 Przemyslaw Szufel & Bogumil Kaminski
## {pszufe, bkamins}@sgh.waw.pl
##
##
## The following two lines should be placed at the beginning of your simulator code:
##
## import matplotlib
## matplotlib.use('qt4agg')

import matplotlib
matplotlib.use("qt4agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure 
import matplotlib.backends.backend_qt4agg as backend

from tkinter import *
from tkinter.ttk import Notebook
 


class GUI:

    ## GUI variables
    titleText = 'PyCX Simulator'  # window title
    timeInterval = 0              # refresh time in milliseconds
    running = False
    modelFigure = None
    stepSize = 1
    currentStep = 0
    def __init__(self,title='PyCX Simulator',interval=0,stepSize=1,parameterSetters=[]):
        self.titleText = title
        self.timeInterval = interval
        self.stepSize = stepSize
        self.parameterSetters = parameterSetters
        self.varEntries = {}
        self.statusStr = ""        
        self.initGUI()
    def initGUI(self):
        plt.close('all') 
        self.rootWindow = Tk()
        self.statusText = StringVar() 
        
        self.rootWindow.wm_title(self.titleText)
        self.rootWindow.protocol('WM_DELETE_WINDOW',self.quitGUI)
        self.rootWindow.geometry('550x400')
        self.rootWindow.columnconfigure(0, weight=1)
        self.rootWindow.rowconfigure(0, weight=1)
        
        self.notebook = Notebook(self.rootWindow)
        self.notebook.grid(row=0,column=0,padx=2,pady=2,sticky='nswe')
        
        self.frameRun = Frame(self.rootWindow)
        self.frameSettings = Frame(self.rootWindow)
        self.frameParameters = Frame(self.rootWindow)
        self.frameInformation = Frame(self.rootWindow)          
        
        self.notebook.add(self.frameRun,text="Run")
        self.notebook.add(self.frameSettings,text="Settings")
        self.notebook.add(self.frameParameters,text="Parameters")
        self.notebook.add(self.frameInformation,text="Info")
        self.status = Label(self.rootWindow, relief=SUNKEN,textvariable=self.statusText)
        self.status.grid(row=1,column=0,padx=2,pady=2,sticky='we')
        
        self.setStatusStr("Simulation not yet started")
        
        self.runPauseString = StringVar()
        self.runPauseString.set("Run")
        self.buttonRun = Button(self.frameRun,width=30,height=2,textvariable=self.runPauseString,command=self.runEvent)
        self.buttonRun.pack(side=TOP, padx=5, pady=5)
        self.showHelp(self.buttonRun,"Runs the simulation (or pauses the running simulation)")
        
        self.buttonStep = Button(self.frameRun,width=30,height=2,text='Step Once',command=self.stepOnce)
        self.buttonStep.pack(side=TOP, padx=5, pady=5)
        self.showHelp(self.buttonStep,"Steps the simulation only once")
        self.buttonReset = Button(self.frameRun,width=30,height=2,text='Reset',command=self.resetModel)
        self.buttonReset.pack(side=TOP, padx=5, pady=5) 
        self.showHelp(self.buttonReset,"Resets the simulation")
        
        
        self.can = Canvas(self.frameSettings)
        self.lab = Label(self.can, width=25,height=1,text="Step size ", justify=LEFT, anchor=W,takefocus=0)
        self.lab.pack(side='left')
        self.stepScale = Scale(self.can,from_=1, to=50, resolution=1,command=self.changeStepSize,orient=HORIZONTAL, width=25,length=150)
        self.stepScale.set(self.stepSize)
        self.showHelp(self.stepScale,"Skips model redraw during every [n] simulation steps\nResults in a faster model run.")
        self.stepScale.pack(side='left')    
        self.can.pack(side='top')
        
        self.can2 = Canvas(self.frameSettings)
        self.lab2 = Label(self.can2, width=25,height=1,text="Step visualization delay in ms ", justify=LEFT, anchor=W,takefocus=0)
        self.lab2.pack(side='left')
        self.stepDelay = Scale(self.can2,from_=0, to=max(2000,self.timeInterval), resolution=10,command=self.changeStepDelay,orient=HORIZONTAL, width=25,length=150)
        self.stepDelay.set(self.timeInterval)
        self.showHelp(self.stepDelay,"The visualization of each step is delays by the given number of milliseconds.")
        self.stepDelay.pack(side='left')    
        self.can2.pack(side='top')
        
        
        self.scrollInfo = Scrollbar(self.frameInformation)
        self.textInformation = Text(self.frameInformation, width=45,height=13,bg='lightgray',wrap=WORD,font=("Courier",10))
        self.scrollInfo.pack(side=RIGHT, fill=Y)
        self.textInformation.pack(side=LEFT,fill=BOTH,expand=YES)
        self.scrollInfo.config(command=self.textInformation.yview)
        self.textInformation.config(yscrollcommand=self.scrollInfo.set)
        for variableSetter in self.parameterSetters:
            can = Canvas(self.frameParameters)
            lab = Label(can, width=25,height=1,text=variableSetter.__name__+" ",anchor=W,takefocus=0)
            lab.pack(side='left')
            ent = Entry(can, width=11)
            ent.insert(0, str(variableSetter()))
            if variableSetter.__doc__ != None and len(variableSetter.__doc__) > 0:
                self.showHelp(ent,variableSetter.__doc__.strip())
            ent.pack(side='left')            
            can.pack(side='top')
            self.varEntries[variableSetter]=ent
        if len(self.parameterSetters) > 0:
            self.buttonSaveParameters = Button(self.frameParameters,width=50,height=1,command=self.saveParametersCmd,text="Save parameters to the running model",state=DISABLED)
            self.showHelp(self.buttonSaveParameters,"Saves the parameter values.\nNot all values may take effect on a running model\nA model reset might be required.")
            self.buttonSaveParameters.pack(side='top',padx=5,pady=5)
            self.buttonSaveParametersAndReset = Button(self.frameParameters,width=50,height=1,command=self.saveParametersAndResetCmd,text="Save parameters to the model and reset the model")
            self.showHelp(self.buttonSaveParametersAndReset,"Saves the given parameter values and resets the model")
            self.buttonSaveParametersAndReset.pack(side='top',padx=5,pady=5)
        

    
    def setStatusStr(self,newStatus):
        self.statusStr = newStatus
        self.statusText.set(self.statusStr)  
    #model control functions
    def changeStepSize(self,val):        
        self.stepSize = int(val)
    def changeStepDelay(self,val):        
        self.timeInterval= int(val)    
    def saveParametersCmd(self):
        for variableSetter in self.parameterSetters:
            variableSetter(float(self.varEntries[variableSetter].get()))
        self.setStatusStr("New parameter values have been set")
    def saveParametersAndResetCmd(self):
        self.saveParametersCmd()
        self.resetModel()

    def runEvent(self):
        self.running = not self.running
        if self.running:
            self.rootWindow.after(self.timeInterval,self.stepModel)
            self.runPauseString.set("Pause")
            self.buttonStep.configure(state=DISABLED)
            self.buttonReset.configure(state=DISABLED)
            if len(self.parameterSetters) > 0:
                self.buttonSaveParameters.configure(state=NORMAL)
                self.buttonSaveParametersAndReset.configure(state=DISABLED)     
        else:
            self.runPauseString.set("Continue Run")
            self.buttonStep.configure(state=NORMAL)
            self.buttonReset.configure(state=NORMAL)
            if len(self.parameterSetters) > 0:
                self.buttonSaveParameters.configure(state=NORMAL)
                self.buttonSaveParametersAndReset.configure(state=NORMAL)

    def stepModel(self):
        if self.running:
            self.modelStepFunc()
            self.currentStep += 1
            self.setStatusStr("Step "+str(self.currentStep))
            self.status.configure(foreground='black')
            if (self.currentStep) % self.stepSize == 0:
                self.drawModel()
            self.rootWindow.after(int(self.timeInterval*1.0/self.stepSize),self.stepModel)

    def stepOnce(self):
        self.running = False
        self.runPauseString.set("Continue Run")
        self.modelStepFunc()
        self.currentStep += 1
        self.setStatusStr("Step "+str(self.currentStep))
        self.drawModel()
        if len(self.parameterSetters) > 0:
            self.buttonSaveParameters.configure(state=NORMAL)

    def resetModel(self):
        self.running = False        
        self.runPauseString.set("Run")
        self.modelInitFunc()
        self.currentStep = 0;
        self.setStatusStr("Model has been reset")
        self.drawModel()

    def drawModel(self):
        
        if self.modelFigure == None or self.modelFigure.canvas.manager.window == None:
            self.modelFigure = plt.figure()
            plt.ion()
        self.modelDrawFunc()
        self.modelFigure.canvas.manager.window.update()

    def start(self,func=[]):
        if len(func)==3:
            self.modelInitFunc = func[0]
            self.modelDrawFunc = func[1]
            self.modelStepFunc = func[2]            
            if (self.modelStepFunc.__doc__ != None and len(self.modelStepFunc.__doc__)>0):
                self.showHelp(self.buttonStep,self.modelStepFunc.__doc__.strip())                
            if (False and self.modelInitFunc.__doc__ != None and len(self.modelInitFunc.__doc__)>0):
                                
                self.textInformation.config(state=NORMAL)
                self.textInformation.delete(1.0, END)
                self.textInformation.insert(END, self.modelInitFunc.__doc__.strip())
                self.textInformation.config(state=DISABLED)
                
            self.modelInitFunc()
            self.drawModel()
        self.rootWindow.mainloop()

    def quitGUI(self):
        plt.close('all')
        self.rootWindow.quit()
        self.rootWindow.destroy()
    
    
    
    def showHelp(self, widget,text):
        def setText(self):
            self.statusText.set(text)
            self.status.configure(foreground='blue')
            
        def showHelpLeave(self):
            self.statusText.set(self.statusStr)
            self.status.configure(foreground='black')
        widget.bind("<Enter>", lambda e : setText(self))
        widget.bind("<Leave>", lambda e : showHelpLeave(self))
