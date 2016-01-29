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


def read_file(filename):
    """
    Read a list of isopachs from comma separated text file, with columns of
    thickness in metres, square root area in kilometres.  Additional comments,
    beginning with #, are also returned.

    :return list of Isopach objects:
    """
    isopachs = []
    comments = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#'):
                comments.append(line[1:].strip())
            else:
                thicknessM, sqrtAreaKM = line.split(',')
                isopachs.append(Isopach(float(thicknessM), float(sqrtAreaKM)))
    return isopachs, comments
