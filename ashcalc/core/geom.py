'''
Created on 5 Jul 2013

@author: Matthew Daggitt
'''

from collections import namedtuple

class Line(namedtuple("Line", "m c")):
                
    def calcY(self,x):
        """
        Calculates the y coordinate of the line for a given x coordinate
        """
        return self.m*x+self.c

    def intersection(self,other):
        """
        Calculates the intersection between self and
        another line.
        
        If other is parallel with self returns None.
        """
        
        if self.m == other.m:
            return None
        else:
            xintersect = (other.c-self.c)/(self.m-other.m)
            yintersect = self.m*xintersect+self.c
            return Point(xintersect,yintersect)

class Point(namedtuple("Point", "x y")):
    """    
    def distanceTo(self,other):
        return np.sqrt((self.x-other.x)**2 + (self.y-other.y)**2)
    """
    
    def __str__(self):
        return "".join(["(",str(self.x),",",str(self.y),")"])
    
    def __eq__(self, other):
        return type(other) is type(self) and self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return (self.x,self.y).__hash__()