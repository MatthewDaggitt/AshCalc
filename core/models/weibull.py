'''
Created on 2 Jul 2013

@author: Matthew Daggitt
'''

import random
import numpy as np

def weibullModelAnalysis(isopachs,numberOfRuns,iterationsPerRun,limits):
	"""
	Analyses the isopach data under the assumption it follows a Weibull model
	
	Model: T(x) = theta*((x/lambda)^(k-2))*exp(-((x/lambda)^k))
	IMPORTANT: Works under the assumption x = sqrt(A/pi) rather than x = sqrt(A).
	
	Not guaranteed to provide a good fit (although with a suitable number of runs and iterations
	per run the probability is high). If a poor fit is returned, try rerunning the calculation.
	
	Arguments
	isopachs:list of Isopachs  --  list of isopachs to analyse.
	numberOfRuns:int		   --  the number of runs that the hill-climbing algorithm performs
	iterationsPerRun:int	   --  the number of iterations per run that the hill-climbing
								   algorithm performs
	limits:list of 2-tuples	--  A list of 2 2-tuples, the first 2 tuple representing
								   lower and upper bounds for parameter lambda and the 
								   second 2-tuple the bounds for parameter k.
								   
	
	Returns
	A dictionary with the following key-value mapping:
	
		dict["estimatedTotalVolume"]:float   --  the estimated total volume of the deposit (in km3).
		dict["thicknessFunction"]:func x->t  --  the thickness function, calculates T(x) (in metres).
		dict["lambda"]:float				 --  estimated value of parameter lambda
		dict["k"]:float					  --  estimated value of parameter k
		dict["theta"]:float				  --  estimated value of parameter theta
		dict["bestScore"]:float			  --  the score of the parameters returned, the closer
												 to zero it is the better the fit of the curve
		dict["isopachs"]:list of Isopachs	--  list of Isopachs analysed
		dict["limits"]:list of 2-tuples	  --  the limits for lambda and k used in calculations
		
	"""

	sqrtAreaKM = np.array([isopach.sqrtAreaKM for isopach in isopachs])
	thicknessM = np.array([isopach.thicknessM for isopach in isopachs])

	lamb, k, bestScore = _solveWeibullParameters(_logErrorFunction,
												 sqrtAreaKM,
												 thicknessM,
												 numberOfRuns,
												 iterationsPerRun,
												 *limits)
	theta = calculateTheta(sqrtAreaKM,thicknessM,lamb,k)
	
	thicknessFunction = _createThicknessFunction(lamb,k,theta)
	estimatedTotalVolumeKM3 = calculateWeibullVolume(lamb,k,theta)

	return {"estimatedTotalVolume" : estimatedTotalVolumeKM3,
			"thicknessFunction" : thicknessFunction,
			"lambda" : lamb,
			"k" : k,
			"theta" : theta,
			"bestScore" : bestScore,
			"isopachs" : isopachs,
			"limits" : limits}
	
def calculateWeibullVolume(lamb,k,theta):
	""" 
	Returns the total volume for the deposit in km3.
	"""
	return 0.001*2*theta*lamb*lamb/k

def calculateTheta(xs,ts,lamb,k):
	"""
	Calculates the optimal value of theta given a lists of x and t values,
	the value of k and the value of lambda
	"""
	xs = np.asarray(xs)
	ts = np.asarray(ts)
	
	if lamb == 0:
		return 0
	else:
		qs = np.exp(-np.log(ts)+(k-2)*np.log(xs/lamb)-np.power(xs/lamb,k))
		top, bottom = np.sum(qs), np.sum(qs*qs)
		return top/bottom if top != 0 and bottom != 0 else 1

def _createThicknessFunction(lamb,k,theta):
	
	def thicknessFunction(x):
		try:
			return np.exp(np.log(theta)+(k-2)*np.log(x/lamb)-(x/lamb)**k)
		except FloatingPointError:
			return 0
	return thicknessFunction

def _logErrorFunction(xs,ts,lamb,k):   
	theta = calculateTheta(xs,ts,lamb,k)
	relativeSquaredError = np.sum(np.power(((np.exp(np.log(theta*((xs/lamb)**(k-2)))-(xs/lamb)**k)-ts)/ts),2))
	return np.log(relativeSquaredError) + relativeSquaredError
	
def _solveWeibullParameters(errorFunction,xs,ts,numberOfRuns,iterationsPerRun,lambdaLimits,kLimits):
	
	bestScore = float('inf')
	bestParameters = []

	for _ in range(numberOfRuns):
		startLamb = random.uniform(lambdaLimits[0],lambdaLimits[1])
		startK = random.uniform(kLimits[0],kLimits[1])
		
		startingParameters = [startLamb,startK]
		currentParameters, currentScore = _performRun(errorFunction,xs,ts,startingParameters,iterationsPerRun,lambdaLimits,kLimits)
		if(bestScore > currentScore):
			bestParameters = currentParameters
			bestScore = currentScore
	
	bestParameters.append(bestScore)
	return bestParameters

def _performRun(errorFunction, xs, ts, initialParameters, maxIterations, lambdaLimits, kLimits):
	iteration = 0
	
	lamb, k = initialParameters
	currentScore = errorFunction(xs,ts,lamb,k)

	bestScore = currentScore
	bestParameters = initialParameters
	
	while iteration < maxIterations:
		
		newLambda = _updateParameter(lamb,lambdaLimits,iteration,maxIterations)
		newK = _updateParameter(k,kLimits,iteration,maxIterations)

		newScore = errorFunction(xs,ts,newLambda,newK)

		newParameters = [newLambda,newK]
		
		if newScore < bestScore:
			bestParameters = newParameters
			bestScore = newScore

		if newScore < currentScore or random.uniform(0,1) > np.exp(currentScore-newScore):
			lamb, k = newParameters
			currentScore = newScore
			
		iteration += 1
	return bestParameters, bestScore

def _updateParameter(value,limits,iteration,maxIterations):
	
	while True:
		delta = (1-iteration/maxIterations)*0.1*(limits[1]-limits[0])
		newValue = value + random.uniform(-delta,delta)
		if limits[0] <= newValue <= limits[1] and newValue != 0:
			return newValue
