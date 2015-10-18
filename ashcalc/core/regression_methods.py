'''
Created on 2 Jul 2013

@author: Matthew Daggitt
'''

from scipy import stats

from core.geom import Line
    
def calculateSingleLineRegression(xs,ys):
    """ Returns the least squares regression line through the provided coordinates """
    slope, intercept = stats.linregress(xs, ys)[0:2]
    return Line(slope,intercept)

def residualSumOfSquares(xs,ys,func):
    """Return the residual sum of squares."""
    return sum([(func(xs[i])-ys[i])**2 for i in range(len(xs))])

def meanRelativeSquaredError(xs,ys,func):
    """Return the mean relative squared error."""
    return sum([((func(x)-y)/y)**2 for x, y in zip(xs,ys)])/len(xs)

def calculateMultiLineRegression(xs, ys, numberOfSegments):
    """
    Fits a specified number of linear segments to the provided data
    
    Arguments
    xs -- the x coordinates of the data
    ys -- the y coordinates of the data
    numberOfSegments -- the number of linear segments to fit to the data
    
    Returns
    segmentLines:list   --  list of Line objects each representing a linear segment
    segmentLimits:list  --  list of n+1 integers, segmentLines[i] is valid between 
                            segmentLimits[i] and segmentLimits[i+1]
    
    """
    
    xs, ys = zip(*sorted(zip(xs,ys), key=lambda x: x[0]))
    
    uniqueXValues = set(xs)
    m = len(uniqueXValues)
    if len(uniqueXValues) < numberOfSegments*2:
        raise ValueError("Cannot perform linear regression for " + str(numberOfSegments) + " segment" +
                         (" " if numberOfSegments == 1 else "s ") +
                         "with only " + str(m) + " unique x-value" + (" " if m == 1 else "s "))
    
    n = len(xs)
    allLines = {}
    allErrors = {}
    
    for j in range(1,n):
        for i in range(0,j):
            segXs, segYs = xs[i:j+1], ys[i:j+1]
            allLines[(i,j)] = calculateSingleLineRegression(segXs,segYs)
            allErrors[(i,j)] = residualSumOfSquares(segXs,segYs,allLines[(i,j)].calcY) if allLines[(i,j)] is not None else float("inf")
    
    minTraversal = _findMinTraversal(allErrors,n,numberOfSegments)
    segmentLines = [allLines[(x,y)] for (x,y) in minTraversal]
    segmentLimits = _calculateSegments(xs,ys,segmentLines,minTraversal)
    
    return (segmentLines,segmentLimits)

def _calculateSegments(xs,ys,lines,minTraversal):
    bounds = [xs[0]]
    for i in range(0,len(lines)-1):
        intersectionPoint = lines[i].intersection(lines[i+1])
        if intersectionPoint is None or lines[i].m > lines[i+1].m:
            bounds.append((xs[minTraversal[i][1]]+xs[minTraversal[i+1][0]])/2)
        else:
            bounds.append(intersectionPoint.x)
    bounds.append(xs[-1])
      
    return bounds
            
def _findMinTraversal(scores,numberOfPoints,numberOfSteps):
    
    traversals = _compilePossibleTraversals(0,numberOfPoints,numberOfSteps)
    
    minScore = float("inf")
    minTraversal = []
    for t in traversals:
        currentScore = 0
        for (x,y) in t:
            currentScore += scores[(x,y)]
        if currentScore < minScore:
            minScore = currentScore
            minTraversal = t
            
    return minTraversal
        
def _compilePossibleTraversals(start,end,n):
    if start == end and n == 0:
        return [[]]
    elif start == end or n == 0:
        return None
    else:
        possiblities = []
        for i in range(start+1,end):
            results = _compilePossibleTraversals(i+1,end,n-1)
            if results != None:
                for r in results:
                    r = r.insert(0,(start,i))
                possiblities += results
        return possiblities