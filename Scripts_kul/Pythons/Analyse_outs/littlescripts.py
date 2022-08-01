import numpy as np
import subprocess
import os
from itertools import chain


def mmpdir_construct(gmap):
    # Starts digging in the folder and stops at layer before kr/ --> saves only last layer in grmaps
    # and subtracts gmap from the mapnames
    maplist = [gmap + i for i in next(os.walk(gmap))[1]]
    m = 0
    while 'kr' not in list(chain(*[os.listdir(i) for i in maplist])):
        m = len(maplist)
        for innermap in maplist:
            dirs = next(os.walk(innermap))[1]
            if 'kr' in dirs or 'kic' in dirs:
                break
            for i in dirs:
                maplist.append(innermap + '/' + i)
    grmaps = [i.replace(gmap, '') for i in maplist[m:]]
    grmaps = [x+'/' for x in grmaps if 'kr' in os.listdir(gmap+x)]
    grmaps.sort()
    return grmaps


def smooth(y, box_pts):
    box = np.ones(box_pts) / box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth


def closest(lst, k):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - k))]


def tail(f, n):
    proc = subprocess.Popen(['tail', '-n', str(n), f], stdout=subprocess.PIPE)
    t = [i.decode('utf8').split() for i in proc.stdout.readlines()][0]
    return t


def is_int(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()