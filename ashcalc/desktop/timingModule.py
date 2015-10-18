'''
Created on 20 Aug 2013

@author: Matthew Daggitt
'''

from timeit import Timer
from core.model_wei import weibullModelAnalysis
from core.isopach import Isopach

def timeFunction(func,args,number):
    return Timer(lambda : func(*args)).timeit(number=number)/number

def createWeibullTimingEstimationFunction():
    limits = [[0,1000],[0,10]]
    n = 100
    isopachs = [Isopach(i+1, i+1) for i in range(n)]
    isopachSets = [[isopachs[:2],5,100,limits],[isopachs,5,100,limits]]
    results = [timeFunction(weibullModelAnalysis,iset,3) for iset in isopachSets]
    timeTakenPerIsopach = (results[1]-results[0])/((n-2))
    timeTakenPerIsopach /= 10
    return createPredictionFunction(timeTakenPerIsopach)

def createPredictionFunction(timeTakenPerIsopach):
    
    def predictionFunction(numberOfIsopachs,numberOfRuns,iterationsPerRun):
        return timeTakenPerIsopach*numberOfIsopachs*iterationsPerRun*numberOfRuns
    return predictionFunction