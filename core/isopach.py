'''
Created on 2 Jul 2013

@author: Matthew Daggitt
'''
import numpy as np

class Isopach(object):

    def __init__(self, thicknessM, sqrtAreaKM):
        self.thicknessM = thicknessM
        self.sqrtAreaKM = sqrtAreaKM

    def __repr__(self):
        return "<Isopach t:%s sqrtA:%s>" % (str(self.sqrtAreaKM), str(self.thicknessM))

    def distanceFromVentKM(self):
    	return self.sqrtAreaKM/np.sqrt(np.pi)