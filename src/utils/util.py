### util.py ###

from collections.abc import Mapping
from types import SimpleNamespace
from PySide6.QtGui import QImage
from PySide6.QtSvg import QSvgRenderer
from typing import *


__all__ = ['AttrDict', 'Collection', 'ImageGetter', 'build', 'commaSplit', 'deepUpdate', 'SvgGetter']


class Collection(SimpleNamespace):
    '''Used to hold generated elements'''
    def _set(self, name:str, value:Any):
        self.__dict__[name] = value
    def _get(self, name:str) -> Any:
        return self.__dict__[name]

class AttrDict():
    """AttrDict maps item access to its attributes"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        return repr(self.__dict__)
    def __getitem__(self, key):
        return self.__dict__[key]
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    def __contains__(self, key):
        return key in self.__dict__
    def items(self):
        return self.__dict__.items()
    def copy(self):
        "return a shallow copy of this AttrDict"
        copy = AttrDict()
        copy.__dict__.update(self.__dict__)
        return copy

class ImageGetter():
    """A static class that holds a cache of images"""
    cache = {}
    
    @staticmethod
    def getImage(name) -> QImage:
        if name not in ImageGetter.cache:
            ImageGetter.cache[name] = QImage(name)
        return ImageGetter.cache[name]
    
    @staticmethod
    def clearCache():
        ImageGetter.cache = {}

class SvgGetter():
    '''a static class that holds a cache of svg files'''
    cache = {}

    @staticmethod
    def getSvg(name) -> QSvgRenderer:
        if name not in SvgGetter.cache:
            SvgGetter.cache[name] = QSvgRenderer(name)
        return SvgGetter.cache[name]
    
    @staticmethod
    def clearChache():
        SvgGetter.cache = {}

def deepUpdate(self:Mapping, other:Mapping):
    '''like update, but if a given index is a mapping in both self and other we recurse'''
    for k, v in other.items():
        if isinstance(v, Mapping):
            if k in self and isinstance(self[k], Mapping):
                deepUpdate(self[k], other[k])
            else:
                self[k] = {}
                deepUpdate(self[k], other[k])
        else:
            self[k] = other[k]

def build(accum:list) -> str:
    '''collapse a string builder'''
    return ''.join(accum).strip()

def commaSplit(string) -> str:
    accum = []
    values = []
    pos = 0
    stack = []
    char = ''
    while pos < len(string):
        char = string[pos]
        if char == '\\':
            accum.append(string[pos:pos+2])
            pos += 1

        elif char in "[(":
            stack.append(char)
            accum.append(char)
        
        elif char in ")]":
            stack.pop()
            accum.append(char)

        elif char == ',':
            if len(stack) == 0:
                values.append(build(accum))
                accum = []
            else:
                accum.append(char)
        
        else:
            accum.append(char)

        pos += 1
    values.append(build(accum))
    return values

