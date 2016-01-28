# -- coding: utf-8 --
from core.isopach import Isopach


def read(filename):
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
