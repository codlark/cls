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


prop = Validation.addValidator


@dataclass
class Element():
    name:str = ''
    draw:prop('draw', asBool) = 'true'
    x:prop('x', asNum) = '0'
    y:prop('y', asNum) = '0'
    width:prop('width', asNum) = '50'
    height:prop('height', asNum) = '50'
    rotation:prop('rotation', asNum) = '0'

    #the below are the result of implementation
    type:str = ''


    @staticmethod
    def generate(template:'Element', validator:Validation):
        elem =  Collection()
        new_val = None
        centerRe = r'center'
        validator.store.add('elementName', template.name)
        for prop, value in asdict(template).items():
            if prop in ['x', 'y']:
                if re.match(centerRe, value.lower()):
                    continue
            validator.store.add('propertyName', prop)
            parsed = validator.store.parse(value)
            new_val = validator.validate(prop, parsed, template.name)
            elem._set(prop, new_val)
        if hasattr(template, 'postGenerate'):
            template.postGenerate(elem)
        
        #center is a special case here because it needs the width and height 
        #to be fully validated.
        if re.match(centerRe, template.x):
            elem.x = (validator.layout.width-elem.width)//2
        if re.match(centerRe, template.y):
            elem.y = (validator.layout.height-elem.height)//2

        return elem

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

@dataclass
class TextElement(Element):
    '''future properties
    font stuff (bold etc)
    color'''
    text:str = ''
    fontFamily:str = 'Verdana'
    fontSize:prop('fontSize', asNum) = '18'
    color:str = 'black'
    wordWrap:prop('wordWrap', asBool) = 'yes'
    alignment:prop('alignment', validateAlignment) = 'center top'
    italic:prop('italic', asBool) = 'no'
    bold:prop('bold', asBool) = 'no'
    overline:prop('overline', asBool) = 'no'
    underline:prop('underline', asBool) = 'no'
    lineThrough:prop('lineThrough', asBool) = 'no'

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
        

imageCache = {}
def validateImage(value):
    if value not in imageCache:
        imageCache[value] = QImage(value)
    return imageCache[value]
        

@dataclass
class ImageElement(Element):
    '''future properties
    aspect ratio
    resize
    sub image?
    '''
    width:prop('width', asNum) = '0'
    height:prop('height', asNum) = '0'
    source:prop('source', validateImage) = ''
    keepAspectRatio:prop('keepAspectRatio', asBool) = 'yes'
   
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

@dataclass
class ShapeElement(Element):
    '''not used directly, this class exists to handle features common to shape
    elements such as line color'''
    lineColor:str = 'black'
    lineWidth:prop('lineWidth', asNum) = '1'
    lineJoin:prop('lineJoin', validateLineJoin) = 'miter'
    lineCap:prop('lineCap', validateLineCap) = 'flat'
    fillColor:str = 'white'
    
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


@dataclass
class RectangleElement(ShapeElement):
    ''' rectangles, with and without rounded corners
    '''
    xRadius:prop('xRadius', asNum) = '0'
    yRadius:prop('yRadius', asNum) = '0'

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        ShapeElement.readyPainter(elem, painter)
        painter.drawRoundedRect(QRect(upperLeft, size), elem.xRadius, elem.yRadius)

@dataclass
class EllipseElement(ShapeElement):
    ''''''
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

@dataclass
class LineElement(ShapeElement):
    x2:prop('x2', asNum) = '50'
    y2:prop('y2', asNum) = '50'
    
    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.resetTransform()
        painter.drawLine(elem.x, elem.y, elem.x2, elem.y2)

    @staticmethod
    def postGenerate(elem):
        elem.rotation = 0
 

@dataclass
class Layout():
    '''class for owning layouts'''
    
    width:int = 300
    height:int = 300
    name:str = 'asset.png'
    output:str = ''
    data:str = None
    elements:list = field(default_factory=list)
    template:str = ''

    def addElement(self, element:Element):
        self.elements.append(element)

class AssetPainter():
    def __init__(self, layout:Layout):
        self.layout = layout
        self.validator = Validation(layout)
        if layout.data is not None:
            self.validator.store.add('assetTotal', str(len(layout.data)))
            self.validator.store.add('rowTotal', str(layout.data[-1]['rowIndex']))
        if hasattr(self.layout, '_names'):
            self.validator.store.briks.update(self.layout._names)

        self.images = []

        if  self.layout.output != '' and not os.path.isdir(self.layout.output):
            if not os.path.isfile(self.layout.output):
                os.mkdir(self.layout.output)
            else:
                raise bWError("'{dir}' exists and is not a directory",
                origin="output in section layout", dir=self.layout.output
                )


    def paintElement(self, template:Element, painter:QPainter):
        '''Paint a given element'''
        elem = Element.generate(template, self.validator)
        if not elem.draw:
            return
        mid = QPoint(elem.width/2, elem.height/2)
        painter.translate(QPoint(elem.x, elem.y)+mid)
        painter.rotate(elem.rotation)
        template.paint(elem, painter, -mid, QSize(elem.width, elem.height))

    def paintAsset(self):
        '''paint the layout and the contained elements'''
        image = QImage(self.layout.width, self.layout.height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setClipRect(0, 0, self.layout.width, self.layout.height)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for element in self.layout.elements:

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
        for image, name in self.images:
            image.save(os.path.join(self.layout.output, name))


elemConstuctors = dict(label=TextElement, image=ImageElement, rect=RectangleElement,
    circle=EllipseElement, ellipse=EllipseElement, line=LineElement)

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



def parseLayout(string:str, filename):

    halves = re.split(r'\n\s*data\s*:\s*\n', string, maxsplit=1)
    script = halves[0]
    if len(halves) == 1:
        rows = None
    else:
        rows = halves[1]

    parser = configparser.ConfigParser(allow_no_value=False, delimiters=':', 
        comment_prefixes='#', empty_lines_in_values=False, default_section="~~don't use~~",
        interpolation=None)
    #this prevents case folding on options
    parser.optionxform = lambda option: option
    #below re was copied from the docs
    parser.SECTCRE = re.compile(r"^ *(?P<header>[^:]+?) *: *$")
    #parser.SECTCRE = re.compile(r"\[ *(?P<header>[^]]+?) *\]")
    layout = Layout()
    try:
        parser.read_string(script)
    
    except configparser.MissingSectionHeaderError as e:
        raise bWError('layout is missing a section header', layout=filename)
    except configparser.DuplicateSectionError as e:
        raise bWError("element name '{name}' is used twice",
        name=e.section, layout=filename
        )
    except configparser.DuplicateOptionError as e:
        raise bWError("property '{prop}' is given twice",
        prop=e.option, elem=e.section
        )
    except configparser.ParsingError as e:
        err = e.errors[0]
        #raise brikWorkError(f'Syntax error on line {err[0]}: {err[1]}')
        #raise brikWorkError(f"'{err[1]}' contains a syntax error")
        raise bWError("'{line}' contains a syntax error",
        layout=filename, line=err[1][1:-1]
        )
    except configparser.Error as e:
        raise bWError('An arbitrary error as occured while parsing your layout file, please alert the devs.')

    #if 'template' in parser['layout']:
    if parser.has_option('layout', 'template'):
        try:
            with open(parser['layout']['template'], encoding='utf-8') as file:
                templateString = file.read()
        except OSError:
            raise bWError("could not open template file '{filename}'",
            file=filename, filename=parser['layout']['template'])
        newParser, newRows = parseLayout(templateString, parser['layout']['template'])
        
        newParser.read_dict(parser)
        parser = newParser
        if rows is None:
            print(rows)
            rows = newRows
    
    if parser.has_option('layout', 'data'):
        dataFile = parser['layout']['data']
        #we have to delete it to ensure proper precedence wrt templates
        del parser['layout']['data']
        if os.path.isfile(dataFile):
            try:
                with open(dataFile, encoding='utf-8') as file:
                    rows = file.read()
            except OSError:
                raise bWError("could not open data file '{filename}'",
                file=filename, filename=dataFile
                )
            dataFile = parseData(rows)
        else:
            raise bWError("'{file}' is not a usable data file",
            layout=filename, file=dataFile)

    return parser, rows

def buildLayout(string:str, filename):

    parser, rows = parseLayout(string, filename)

    try:
        layout = Layout(**parser['layout'])
    except TypeError as e:
        prop = e.args[0].split()[-1][1:-1]
        raise bWError("{prop} is not a valid layout property", 
        layout=filename, prop=prop
        )

    width = asNum(layout.width, err=bWError("'{value}' is not a valid width",
        layout=filename, value=layout.width))
    layout.width = width
    
    height = asNum(layout.height, err=bWError("'{value}' is not a valid height",
        layout=filename, value=layout.height))
    layout.height = height

    for name, section in parser.items():
        
        if name == 'layout':
            pass
            #we already parsed layout earlier
        
        elif name == 'names':
            names = {}
            for n,v in section.items():
                names[n] = v
                #section proxies don't have a copy method so we do it the long way
            layout._names = names

        elif name == "~~don't use~~":
            pass #literally ignore this section lol

        else:
            type = section.pop('type', None)
            if type is None:
                #I think after the rework this won't be an error
                raise bWError("this element lacks a type", elem=name)

            copy = {}
            for prop,value in section.items():
                copy[re.sub(' ', '_', prop)] = value

            try:
                element = elemConstuctors[type](**copy)
            except KeyError as e:
                raise bWError("'{type}' is not a valid type",
                type=type, elem=name
                )
            except TypeError as e:
                prop = e.args[0].split()[-1][1:-1]
                raise InvalidPropError(name, prop)
            element.name = name
            layout.addElement(element)
    
    
    if rows is not None:
        layout.data = parseData(rows)
    
    if '[' not in layout.name and layout.data is not None:
        layout.name = '[assetIndex]'+layout.name


    return layout
