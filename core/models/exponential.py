'''
Created on 15 Jul 2013

@author: Matthew Daggitt
'''

import numpy as np

from core import regression_methods

def exponentialModelAnalysis(isopachs,n):
	"""
	Analyses the isopach data under the assumption it follows a n-segment exponential model 
	
	Model: T(x) = c*exp(-m*x)
	IMPORTANT: Works under the assumption x = sqrt(A/pi) rather than x = sqrt(A).
	
	Arguments
	isopachs:list of Isopachs -- list of isopachs to analyse
	n:int -- the number of exponential segments
	
	Returns
	A dictionary with the following key-value mapping:
	
		dict["estimatedTotalVolume"]:float		  --  the estimated total volume of the deposit.
		dict["thicknessFunction"]:func x->t		 --  the thickness function, calculates T(x) (in metres).
		dict["segmentLimits"]:list of floats		--  list of bounds for the segments. Segment i
														is valid between segmentLimits[i] and
														segmentLimits[i+1].
		dict["segmentVolumes"]:list of floats	   --  estimated tephra volumes for each segment.
		dict["segmentCoefficients"]:list of floats  --  estimated coefficients for each segment.
		dict["segmentExponents"]:list of floats	 --  estimated exponents for each segment.
		dict["segmentBts"]:list of floats		   --  estimated half-thicknesses for each segment
														(i.e. distance across which tephra thickness
														halves).
		dict["regressionLines"]:list of Lines	   --  Line objects representing each segment's
														least squares regression line used to estimate
														it's parameters.
		dict["isopachs"]:list of Isopachs		   --  list of Isopachs analysed.
		dict["numberOfSegments"]:int				--  number of exponential segments.
	"""

	logThickness = [np.log(isopach.thicknessM) for isopach in isopachs]
	sqrtAreaKM = [isopach.sqrtAreaKM for isopach in isopachs]

	regressionLines, segmentLimits = regression_methods.calculateMultiLineRegression(sqrtAreaKM,logThickness,n)

	segmentT0s = [np.exp(line.c) for line in regressionLines]
	segmentKs = [-line.m for line in regressionLines]
	segmentBts = [np.log(2)/(k*np.sqrt(np.pi)) for k in segmentKs]
	segmentVolumes = []
	
	segmentLimits[0], segmentLimits[-1] = 0, float("inf")

	for i in range(n):
		segmentVolumes.append(calculateExponentialSegmentVolume(segmentT0s[i],segmentKs[i],segmentLimits[i],segmentLimits[i+1]))
	estimatedTotalVolume = sum(segmentVolumes)

	def thicknessFunction(x):
		for i in range(n):
			if segmentLimits[i] <= x < segmentLimits[i+1]:
				return segmentT0s[i]*np.exp(-segmentKs[i]*x)
		raise ValueError("x (" + str(x) + ") is not in the domain of the function (0 to infinity)")

	return {"estimatedTotalVolume" : estimatedTotalVolume,
			"thicknessFunction" : thicknessFunction,
			"segmentLimits" : segmentLimits,
			"segmentVolumes" : segmentVolumes,
			"segmentCoefficients" : segmentT0s,
			"segmentExponents" : segmentKs,
			"segmentBts" : segmentBts,
			"regressionLines" : regressionLines,
			"isopachs" : isopachs,
			"numberOfSegments" : n}

def calculateExponentialSegmentVolume(coefficient,exponent,startLimitKM,endLimitKM):
	"""
	Returns the volume for the segment of the deposit in km3.
	"""

	t1 = (2*coefficient)/(1000*exponent*exponent)
	t2 = (startLimitKM*exponent+1)*np.exp(-exponent*startLimitKM)
	t3 = (endLimitKM*exponent+1)*np.exp(-exponent*endLimitKM) if endLimitKM != float("inf") else 0
	return t1*(t2-t3)
	
