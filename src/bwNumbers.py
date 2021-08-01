import bwUtils
import re

class Unit():
    '''Unit represents a unitized number'''
    def __init__(self, frame, sign, wholeNum, frac):
        '''frame is a collection holding the dpi and stuff on the parent
        sign is a 1 or -1
        wholeNum and frac store the actual number'''
        self.frame = frame
        self.sign = sign
        self.int = wholeNum
        self.frac = frac
    
class Inch(Unit):
    '''an inch'''
    def __init__(self, frame, sign, wholeNum, frac):
        super().__init__(frame, sign, wholeNum, frac)
    
    def __int__(self):
        pix = self.frame.dpi * (self.int+self.frac)
        if self.sign == '^':
            pass
        return pix*self.sign