'''
Created on 15 Jul 2013

@author: Matthew Daggitt
'''

import numpy as np

from volume_calculations import regression_methods
from volume_calculations.model_exp import exponentialModelAnalysis

def powerLawModelAnalysis(isopachs, proximalLimitKM, distalLimitKM):
    """
    Analyses the isopach data under the assumption it follows a power law model
    
    Model: T(x) = c*x^(-m)
    IMPORTANT: Works under the assumption x = sqrt(A/pi) rather than x = sqrt(A).
    
    Arguments
    isopachs:list of Isopachs -- list of isopachs to analyse
    proximalLimitKM:float -- the proximal limit of integration (in km)
    distalLimitKM:float -- the distal limit of integration (in km)
    
    Returns
    A dictionary with the following key-value mapping:
    
        dict["estimatedTotalVolume"]:float          --  the estimated total volume of the deposit.
        dict["thicknessFunction"]:func x->t         --  the thickness function, calculates T(x) (in metres).
        dict["regressionLine"]:Line                 --  Line object representing the least squares
                                                        regression line used to estimate the parameters
        dict["coefficient"]:float                   --  estimated coefficient for the power curve
        dict["exponent"]:float                      --  estimated exponent for the power curve
        dict["isopachs"]:list of Isopachs           --  list of Isopachs analysed
        dict["proximalLimitKM"]:list of Isopachs    --  the proximal limit of integration used in calculations
        dict["distalLimitKM"]:list of Isopachs      --  the distal limit of integration used in calculations
        
    """
    
    logThicknessesM = [np.log(isopach.thicknessM) for isopach in isopachs]
    logSqrtAreaKM = [np.log(isopach.sqrtAreaKM) for isopach in isopachs]
        
    regressionLine = regression_methods.calculateSingleLineRegression(logSqrtAreaKM, logThicknessesM)
    m = -regressionLine.m
    c = np.exp(regressionLine.c)
    estimatedTotalVolume = calculatePowerLawVolume(c,m,proximalLimitKM,distalLimitKM)
    
    def thicknessFunction(x):
        if proximalLimitKM <= x <= distalLimitKM:
            return c*(x**-m)
        else:
            raise ValueError("x is out of range of proximal and distal limits of integration")
    
    suggestedProximalLimit = calculateProximalLimitEstimate(isopachs,c,m)
    
    return {"estimatedTotalVolume" : estimatedTotalVolume,
            "thicknessFunction" : thicknessFunction,
            "regressionLine" : regressionLine,
            "coefficient" : c,
            "exponent" : m,
            "isopachs" : isopachs,
            "proximalLimitKM" : proximalLimitKM,
            "distalLimitKM" : distalLimitKM,
            "suggestedProximalLimit" : suggestedProximalLimit}
  
def calculatePowerLawVolume(coefficient,exponent,proximalLimitKM,distalLimitKM):
    """ 
    Returns the total volume for the deposit in km3.
    """
    return 0.001*2*coefficient*(distalLimitKM**(2-exponent)-proximalLimitKM**(2-exponent))/(2-exponent)

def calculateProximalLimitEstimate(isopachs,coefficient,exponent):
    """
    Returns the estimate for the proximal limit of integration
    suggested by Bonadonna and Houghton 2005
    """
    expResults = exponentialModelAnalysis(isopachs,2)
    return (expResults["segmentCoefficients"][0]/coefficient)**(-(1/exponent))
