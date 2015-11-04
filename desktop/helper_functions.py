import numpy as np

def validateValue(string,errorString,numericType,lowerBound=None,strictLowerBound=None,upperBound=None,strictUpperBound=None):
	try:
		if numericType == "float":
			if string == "\u221E":
				value = float('inf')
			else:
				value = float(string)
		elif numericType == "int":
			value = int(string)
			
		if lowerBound is not None and value < lowerBound:
			raise ValueError()
		if strictLowerBound is not None and value <= strictLowerBound:
			raise ValueError()
		if upperBound is not None and value > upperBound:
			raise ValueError()
		if strictUpperBound is not None and value >= strictUpperBound:
			raise ValueError()
	except ValueError:
		raise ValueError(errorString)
	return value

def roundToSF(number,sf):
	if number == 0:
		return "0."+"0"*sf
	elif number == float("inf"):
		return "\u221E"
	elif isinstance(number,str):
		return number
	else:
		places = int(np.floor(np.log10(abs(number))))
		value = round(number, -places + (sf - 1))
		return str(int(value) if places >= sf - 1 else value)
	
def getStaggeredPoints(start,end,number):
	c = start+1
	lamb = np.log((end+1)/c)/number 
	return [c*np.exp(lamb*i)-1 for i in range(0,number+1)]