import os
import re
import configparser
from bwStore import BrikStore
from dataclasses import dataclass, asdict, field
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from bwUtils import *


class Validation():
    '''This object holds all the property validators and runs them
    at a future date it may also store the mapping between user property
    and Element attrs'''
    
    validators = {}

    @classmethod
    def addValidator(cls, name, func):
        cls.validators[name] = func
        return name

    def __init__(self, layout:'Layout'):
        self.layout = layout
        self.store = BrikStore()
    
    def validate(self, name, value, element=''):
        if name not in self.validators:
            if type(value) == str:
                return evalEscapes(value)
            #not actually sure what to do here?
        func = self.validators[name]
        newValue = func(value)
        if newValue is None:
            raise InvalidValueError(element, name, value)
        elif type(newValue) == str:
            #do I want this here or generate?
            return evalEscapes(newValue)
        else:
            return newValue

def prop(name, validator, default):
    Validation.addValidator(name, validator)
    return name, default

def validateAlignment(string):
    horz = {'left':Qt.AlignLeft, 'right':Qt.AlignRight, 'center':Qt.AlignHCenter,
        'justify':Qt.AlignJustify}
    vert = {'top':Qt.AlignTop, 'bottom':Qt.AlignBottom, 'middle':Qt.AlignVCenter,}
    terms = string.lower().split()
    if terms[0] in horz:
        result = horz[terms[0]]
    else:
        return None
    if terms[1] in vert:
        return result|vert[terms[1]]
    else:
        return None

imageCache = {}
def validateImage(value):
    if value not in imageCache:
        imageCache[value] = QImage(value)
    return imageCache[value]

def validateLineJoin(value):
    joins = {'miter': Qt.MiterJoin, 'bevel': Qt.BevelJoin, 'round': Qt.RoundJoin}
    if value.lower() not in joins:
        return None
    return joins[value.lower()]

def validateLineCap(value):
    caps = {'flat': Qt.FlatCap, 'square': Qt.SquareCap, 'round': Qt.RoundCap}
    if value.lower() not in caps:
        return None
    return caps[value.lower()]


class Element():
    defaults = ChainMap(dict([
        prop('type', str, ''),
        prop('name', str, ''),
        prop('draw', asBool, 'true'),
        prop('x', asNum, '0'),
        prop('y', asNum, '0'),
        prop('width', asNum, '50'),
        prop('height', asNum, '50'),
        prop('rotation', asNum, '0'),
    ]))
    @staticmethod
    def paint(elem, painter, upperLect, size):
        pass

class LabelElement():
    defaults = Element.defaults.new_child(dict([
        prop('text', str, ''),
        prop('fontFamily', str, 'Verdana'),
        prop('fontSize', asNum, '18'),
        prop('color', str, 'black'),
        prop('wordWrap', asBool, 'yes'),
        prop('alignment', validateAlignment, 'center top'),
        prop('italic', asBool, 'no'),
        prop('bold', asBool, 'no'),
        prop('overline', asBool, 'no'),
        prop('underline', asBool, 'no'),
        prop('lineThrough', asBool, 'no'),
    ]))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        label = QLabel()
        label.setTextFormat(Qt.RichText)
        label.resize(size)
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        label.setAlignment(elem.alignment)
        label.setWordWrap(elem.wordWrap)
        style = 'QLabel {\n'
        style += f'font-family: {elem.fontFamily};\n'
        style += f'font-size: {elem.fontSize}pt;\n'
        style += f'color: {elem.color};\n'
        if elem.italic: style += 'font-style: italic;\n'
        if elem.bold: style += 'font-weight: bold;\n'
        if elem.overline: style += 'text-decoration: overline;\n'
        if elem.underline: style += 'text-decoration: underline;\n'
        if elem.lineThrough: style += 'text-decoration: line-through;\n'
        #style += "font-variant-numeric: lining-nums;\n" someday
        label.setStyleSheet(style+'}')
        label.setText(re.sub(r'\n', '<br>', elem.text))
        painter.drawPixmap(upperLeft, label.grab())

        # - should I allow pt and px? (extra validation)

class ImageElement():
    defaults = Element.defaults.new_child(dict([
        prop('width', asNum, '0'),
        prop('height', asNum, '0'),
        prop('source', validateImage, ''),
        prop('keepAspectRatio', asBool, 'yes'),
    ]))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        if elem.keepAspectRatio:
            aspect = Qt.KeepAspectRatio
        else:
            aspect = Qt.IgnoreAspectRatio
        painter.drawPixmap(upperLeft, QPixmap.fromImage(elem.source.scaled(size, aspectMode=aspect)))

    @staticmethod
    def postGenerate(elem):
        if elem.width == 0:
            elem.width = elem.source.width()
        if elem.height == 0:
            elem.height = elem.source.height()

class ShapeElement():
    defaults = Element.defaults.new_child(dict([
        prop('lineColor', str, 'black'),
        prop('lineWidth', asNum, '1'),
        prop('lineJoin', validateLineJoin, 'miter'),
        prop('lineCap', validateLineCap, 'flat'),
        prop('fillColor', str, 'white'),
    ]))

    @staticmethod
    def readyPainter(elem, painter:QPainter):
        pen = QPen(QColor(elem.lineColor))
        if elem.lineWidth == 0:
            pen.setStyle(Qt.NoPen)
        else:
            pen.setWidth(elem.lineWidth)
        pen.setCapStyle(elem.lineCap)
        pen.setJoinStyle(elem.lineJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(elem.fillColor)))

class RectangleElement():
    defaults = ShapeElement.defaults.new_child(dict([
        prop('xRadius', asNum, '0'),
        prop('yRadius', asNum, '0'),
    ]))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        ShapeElement.readyPainter(elem, painter)
        painter.drawRoundedRect(QRect(upperLeft, size), elem.xRadius, elem.yRadius)

class EllipseElement():
    defaults = ShapeElement.defaults.new_child()

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.drawEllipse(QRect(upperLeft, size))

    @staticmethod
    def postGenerate(elem):
        if elem.width == 0 and elem.height != 0:
            elem.width = elem.height
        elif elem.width != 0 and elem.height == 0:
            elem.height = elem.width

class LineElement():
    defaults = ShapeElement.defaults.new_child(dict([
        prop('x2', asNum, '50'),
        prop('y2', asNum, '50'),
    ]))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.resetTransform()
        painter.drawLine(elem.x, elem.y, elem.x2, elem.y2)

elemClasses = dict(
    none = Element,
    label = LabelElement,
    image = ImageElement,
    rect = RectangleElement,
    ellipse = EllipseElement,
    circle = EllipseElement,
    line = LineElement
)

def generateElement(template, validator:Validation):
    elem =  Collection()
    new_val = None
    centerRe = r'center'
    validator.store.add('elementName', template['name'])
    for prop, value in template.items():
        if prop in ['x', 'y']:
            if re.match(centerRe, value.lower()):
                continue
        validator.store.add('propertyName', prop)
        parsed = validator.store.parse(value)
        new_val = validator.validate(prop, parsed, template['name'])
        elem._set(prop, new_val)
    elemClass = elemClasses[template['type']]
    if hasattr(elemClass, 'postGenerate'):
        elemClass.postGenerate(elem)
    
    #center is a special case here because it needs the width and height 
    #to be fully validated.
    if re.match(centerRe, template['x']):
        elem.x = (validator.layout.width-elem.width)//2
    if re.match(centerRe, template['y']):
        elem.y = (validator.layout.height-elem.height)//2

    return elem
        

@dataclass
class Layout():
    '''class for owning layouts'''
    
    width:int = 300
    height:int = 300
    name:str = 'asset.png'
    output:str = ''
    data:str = None
    elements:list = field(default_factory=dict)
    template:str = ''
    defaults:dict = field(default_factory=dict)
    filename:str = ''
    userBriks:dict = field(default_factory=dict)

    def addElement(self, element):
        self.elements[element['name']] = element

class AssetPainter():
    def __init__(self, layout:Layout):
        self.layout = layout
        self.validator = Validation(layout)
        if layout.data is not None:
            self.validator.store.add('assetTotal', str(len(layout.data)))
            self.validator.store.add('rowTotal', str(layout.data[-1]['rowIndex']))
       
        self.validator.store.briks.update(self.layout.userBriks)
        #if hasattr(self.layout, '_names'):
        #    self.validator.store.briks.update(self.layout._names)

        self.images = []

        if  self.layout.output != '' and not os.path.isdir(self.layout.output):
            if not os.path.isfile(self.layout.output):
                os.mkdir(self.layout.output)
            else:
                raise bWError("'{dir}' exists and is not a directory",
                origin="output in section layout", dir=self.layout.output
                )


    def paintElement(self, template, painter:QPainter):
        '''Paint a given element'''
        elem = generateElement(template, self.validator)
        if not elem.draw:
            return
        mid = QPoint(elem.width/2, elem.height/2)
        painter.translate(QPoint(elem.x, elem.y)+mid)
        painter.rotate(elem.rotation)
        elemClasses[template['type']].paint(elem, painter, -mid, QSize(elem.width, elem.height))

    def paintAsset(self):
        '''paint the layout and the contained elements'''
        image = QImage(self.layout.width, self.layout.height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setClipRect(0, 0, self.layout.width, self.layout.height)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for element in self.layout.elements.values():

            painter.resetTransform()
            painter.setPen(Qt.black)
            painter.setBrush(Qt.white)
            self.paintElement(element, painter)
        
        return image

    def paint(self):
        '''paint a set of assets based on the current layout and data file.'''

        if self.layout.data is None:
                image = self.paintAsset()
                name = self.validator.store.parse(self.layout.name)
                self.images.append((image, name))

        else:
            for row in  self.layout.data:
                #TODO figure out a better way to do this
                self.validator.store.briks.update(row)
                image = self.paintAsset()
                name = self.validator.store.parse(self.layout.name)
                self.images.append((image, name))
                #self.image.save(os.path.join(self.layout.output, name))


    def save(self):
        '''save the generated images.'''
        try:
            for image, name in self.images:
                image.save(os.path.join(self.layout.output, name))
        except OSError:
            raise bWError('failed to save images to {ouput}',
            output=self.layout.output, layout=self.layout.filename)



def parseData(rows:str):

    data = parseCSV(rows)
    if data is None:
        return None
        
    newData = []

    if 'repeat' in data[0]:
        assetIndex = 1
        rowIndex = 1
        for row in data:
            #I'm hard coding the names of the count and index
            #briks here, not a fan of that really
            
            repeatTotal = row.pop('repeat')
            if repeatTotal == '1':
                newData.append(dict(
                    assetIndex=str(assetIndex),
                    rowIndex=str(rowIndex),
                    repeatIndex='1',
                    repeatTotal=repeatTotal) | row
                )
            
            else:
                for repeat in range(int(repeatTotal)):
                    newData.append(dict(
                        assetIndex=str(assetIndex),
                        rowIndex=str(rowIndex),
                        repeatIndex=str(repeat+1),
                        repeatTotal=repeatTotal) | row
                    )
                    assetIndex += 1
                rowIndex += 1
                continue
                #this continue is to avoid weird inc placement
            
            assetIndex += 1
            rowIndex += 1

    else:
        for index, row in enumerate(data):
            newData.append(dict(
                assetIndex=str(index+1),
                rowIndex=str(index+1),
                repeatIndex='1',
                repeatTotal='1') | row
            )

    return newData



def buildLayout(filename):
    if not os.path.isfile(filename):
        raise bWError("'{file}' is not a valid file",
        file=filename
        )
    try:
        with open(filename, encoding='utf-8') as file:
            layoutText = file.read()
    except OSError:
        raise bWError("'{file}' could not be opened",
        file=filename
        )
    
    #layout may become a nonclass object
    parsedLayout = parseLayoutFile(layoutText, filename)
    if 'layout' in parsedLayout:
        rawLayout = parsedLayout.pop('layout')
    else:
        rawLayout = {}


    if 'template' in rawLayout:
        layout = buildLayout(rawLayout.pop('template'))
    else:
        layout = Layout()
    layout.filename = filename
    
    if 'data' in rawLayout:
        dataFilename = rawLayout.pop('data')
        if 'data' in parsedLayout:
            parsedLayout.pop('data')
        if not os.path.isfile(dataFilename):
            raise bWError("'{filename}' is not a valid file",
            file=filename, filename=dataFilename
            )
        try:
            with open(dataFilename, encoding='utf-8') as file:
                userData = file.read()
        except OSError:
            raise bWError("'{filename}' could not be opened",
            file=filename, filename=dataFilename
            )
    elif 'data' in parsedLayout:
        userData = parsedLayout.pop('data')
    else:
        userData = None
    if userData != None:
        layout.data = parseData(userData)
    
    for prop, value in rawLayout.items():
        setattr(layout, prop, value)

    if type(layout.width) == str:
        layout.width = asNum(layout.width, 
        err=bWError("'{value}' is not a valid asset width",
        layout=filename, value=layout.width))
    if type(layout.height) == str:
        layout.height = asNum(layout.height, 
        err=bWError("'{value}' is not a valid asset height",
        layout=filename, value=layout.height))


    if 'defaults' in parsedLayout:
        deepUpdate(layout.defaults, parsedLayout.pop('defaults'))

    if 'briks' in parsedLayout:
        layout.userBriks.update(parsedLayout.pop('briks'))
    
    for name, props in parsedLayout.items():
        if name in layout.elements:
            layout.elements[name].maps.insert(0, props)
        else:
            if 'type' not in props:
                props['type'] = 'none'
            elif props['type'] not in elemClasses:
                raise InvalidValueError(name, 'type', prop['type'])
            elemType = elemClasses[props['type']]
            elem = elemType.defaults.new_child(props)
            elem.maps.insert(1, layout.defaults)
            #its easier to just insert
            elem['name'] = name
            layout.addElement(elem)
    

    return layout
