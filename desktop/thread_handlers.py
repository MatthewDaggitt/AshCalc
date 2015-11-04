'''
Created on 19 Aug 2013

@author: Matthew Daggitt
'''

from threading import Thread
from queue import Queue

from core.models.exponential import exponentialModelAnalysis
from core.models.power_law import powerLawModelAnalysis
from core.models.weibull import weibullModelAnalysis

from desktop.settings import Model


class ThreadHandler():
    """
    Class for running calculations in a seperate thread
    """
    def __init__(self):
        self._resultsQueue = Queue()
        self._currentThreadID = 0
        self._currentCalculationType = None
        self._currentResult = None
        
    def startCalculation(self, calculationType, args):
        """
        Creates a WorkerThread to carry out func(*args). Will cause any
        previous still running calculations to be cancelled
        """

        if calculationType == Model.EXP:
            function = exponentialModelAnalysis
        elif calculationType == Model.POW:
            function = powerLawModelAnalysis
        elif calculationType == Model.WEI:
            function = weibullModelAnalysis

        self._currentThreadID += 1
        self._currentCalculationType = calculationType
        newThread = WorkerThread(function, args, self._calculationFinished, self._resultsQueue, self._currentThreadID)
        newThread.setDaemon(True)
        newThread.start()
        
    def _calculationFinished(self):
        """
        Called internally by the WorkerThreads. If the calculation was cancelled
        the result is ignored, otherwise if it ended in an error the result type is changed to error,
        and the result of the calculation is stored in _currentResult ready for retrieval
        """
        threadID, results = self._resultsQueue.get_nowait()
        if threadID == None:
            self._currentResult = ("Error",results)
        elif threadID == self._currentThreadID:
            self._currentResult = (self._currentCalculationType,results)
            
    def cancelLastCalculation(self):
        """
        Tells the ThreadHandler to cancel the last calculation
        At the moment this involves leaving the calculation to run and
        ignoring the result when it is returned
        """
        self._currentThreadID += 1
    
    def getCurrentCalculationResult(self):
        """
        Returns the result of the last calculation if finished
        otherwise returns None
        """
        if self._currentResult is not None:
            result = self._currentResult
            self._currentResult = None
            return result
        else:
            return None
        
class WorkerThread(Thread):
    """Subclass of Thread that performs the calculation"""
    
    def __init__(self, function, args, callbackFunction, resultsQueue, threadID):
        Thread.__init__(self)
        self.callbackFunction = callbackFunction
        self._resultsQueue = resultsQueue
        self.function = function
        self.args = args
        self.threadID = threadID
        
    def run(self):
        """
        Performs the provided calculation and puts the result and the calculation type
        back into the results queue when finished.
        
        If an error occurs it puts the result type "None" and the error instance into
        the results queue.
        
        It then calls it's callback function to signify it's finished (usually the
        ThreadHandler.calculationFinished() method)
        """
        try:
            result = self.function(*self.args)
            self._resultsQueue.put((self.threadID,result))
        except Exception as e:
            self._resultsQueue.put((None,e))
        self.callbackFunction()