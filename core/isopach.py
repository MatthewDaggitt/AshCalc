'''
Created on 2 Jul 2013

@author: Matthew Daggitt
'''
import numpy as np

class Isopach(object):

    def __init__(self, sqrtAreaKM, thicknessM):
        self.sqrtAreaKM = sqrtAreaKM
        self.thicknessM = thicknessM

    def distanceFromVentKM(self):
    	return self.sqrtAreaKM/np.sqrt(np.pi)