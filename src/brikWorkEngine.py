import os
import re
from bwStore import BrikStore
from collections import ChainMap
from dataclasses import dataclass, asdict, field
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from bwUtils import *


class Validation():
    '''This object holds all the property validators and runs them'''
    
    validators = {}

    @classmethod
    def addValidator(cls, name, func):
        cls.validators[name] = func
        return name

    def __init__(self, layout:'Layout'):
        self.layout = layout
        self.store = BrikStore()

    def validate(self, frame:AttrDict):
        if frame.prop not in self.validators:
            raise bWError("'{name}' is not a known property", name=frame.prop, elem=frame.elem.name)
        func = self.validators[frame.prop]
        result = func(frame, frame.elem)
        if not result:
            raise InvalidValueError(frame.elem.name, frame.prop, frame.value)
        else:
            return

def validateString(frame, elem):
    elem[frame.prop] = evalEscapes(frame.value)
    return True

def validateNumber(frame, elem):
    value = Unit.fromStr(frame.value, signs='+')
    if value is None:
        return False
    elem[frame.prop] = value.toInt(dpi=frame.layout.dpi)
    return True

def validateToggle(frame, elem):
    value = asBool(frame.value)
    if value is None:
        return False
    elem[frame.prop] = value
    return True

def prop(name, validator, default):
    if validator == 'number': 
        validator = validateNumber
    elif validator == 'string':
        validator = validateString
    elif validator == 'toggle':
        validator = validateToggle
    Validation.addValidator(name, validator)
    return name, default

def validateXY(frame, elem):
    #also handles x2 and y2
    if frame.prop[0] == 'x':
        dim = 'width'
    else:
        dim = 'height'
    if frame.container == 'layout':
        containerDim = frame.layout[dim]
        containerLoc = 0
    else:
        containerDim = frame.container[dim]
        containerLoc = frame.container[frame.prop[0]]
        # on x2 and y2 use the container's x and y

    if frame.value == 'center':
        elem[frame.prop] = (containerDim-elem[dim])//2 + containerLoc
        return True
    else:
        value = Unit.fromStr(frame.value, signs='-+^',units=('px', 'in', 'mm', '%'))
        if value is None:
            return False
        if value.unit == '%':
            value = value.toInt(whole=containerDim)
        elif value.sign == '^':
            #TODO consider making ^ a signal not a sign to allow ^-.3
            value = containerDim - elem[dim] - value.toInt(dpi=frame.layout.dpi)
        else:
            value = value.toInt(dpi=frame.layout.dpi)
        elem[frame.prop] = value + containerLoc
        return True

def validateHeightWidth(frame, elem):
    if frame.container == 'layout':
        containerDim = frame.layout[frame.prop]
    else:
        containerDim = frame.container[frame.prop]
    value = Unit.fromStr(frame.value, units=('px', 'in', 'mm', '%'))
    if value is None:
        return False
    if value.unit == '%':
        value = value.toInt(whole=containerDim)
    else:
        value = value.toInt(dpi=frame.layout.dpi)
    elem[frame.prop] = value
    return True

def validateAngle(frame, elem):
    value = Unit.fromStr(frame.value, signs='+', units=('deg'))
    if value is None:
        return False
    elem[frame.prop] = value.toInt() % 360
    return True


def validateDraw(frame, elem):
    value = asBool(frame.value)
    if value is None:
        return False
    elif frame.container == 'layout':
        elem[frame.prop] = value
    elif frame.containerValue == True:
        elem.draw = value
    else:
        elem.draw = frame.containerValue
    return True

def validateFontSize(frame, elem):
    value = Unit.fromStr(frame.value, signs='+', units=('pt', 'px', 'in', 'mm'))
    if value is None:
        return False
    elem[frame.prop] = value, frame.layout.dpi
    return True

def validateAlignment(frame, elem):
    horz = {'left':Qt.AlignLeft, 'right':Qt.AlignRight, 'center':Qt.AlignHCenter,
        'justify':Qt.AlignJustify}
    vert = {'top':Qt.AlignTop, 'bottom':Qt.AlignBottom, 'middle':Qt.AlignVCenter,}
    terms = frame.value.lower().split()
    if terms[0] in horz:
        result = horz[terms[0]]
    else:
        return False
    if terms[1] in vert:
         result |= vert[terms[1]]
    else:
        return False
    elem[frame.prop] = result
    return True

def validateLineJoin(frame, elem):
    joins = {'miter': Qt.MiterJoin, 'bevel': Qt.BevelJoin, 'round': Qt.RoundJoin}
    if frame.value.lower() not in joins:
        return False
    elem[frame.prop] = joins[frame.value.lower()]
    return True

def validateLineCap(frame, elem):
    caps = {'flat': Qt.FlatCap, 'square': Qt.SquareCap, 'round': Qt.RoundCap}
    if frame.value.lower() not in caps:
        return False
    elem[frame.prop] = caps[frame.value.lower()]
    return True

class ElementScope(ChainMap):
    '''A subclass of ChainMap that also has an attribute to hold an element's container'''
    def __init__(self, *maps: Mapping) -> None:
        super().__init__(*maps)
        self.container = None


class Element():
    defaults = ElementScope(dict([
        prop('type', 'string', ''),
        prop('name', 'string', ''),
        prop('draw', validateDraw, 'true'),
        prop('x', validateXY, '0px'),
        prop('y', validateXY, '0px'),
        prop('width', validateHeightWidth, '1/4in'),
        prop('height', validateHeightWidth, '1/4in'),
        prop('rotation', validateAngle, '0'),
    ]))
    @staticmethod
    def paint(elem, painter, upperLect, size):
        pass

class LabelElement():
    defaults = Element.defaults.new_child(dict([
        prop('text', 'string', ''),
        prop('fontFamily', 'string', 'Verdana'),
        prop('fontSize', validateFontSize, '22pt'),
        prop('color', 'string', 'black'),
        prop('wordWrap', 'toggle', 'yes'),
        prop('alignment', validateAlignment, 'center top'),
        prop('italic', 'toggle', 'no'),
        prop('bold', 'toggle', 'no'),
        prop('overline', 'toggle', 'no'),
        prop('underline', 'toggle', 'no'),
        prop('lineThrough', 'toggle', 'no'),
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
        fontSize, dpi = elem.fontSize
        if fontSize.unit == 'pt':
            fontUnit = fontSize.unit
            fontSize = fontSize.num
        else:
            fontUnit = fontSize.unit
            fontSize = fontSize.toInt(dpi=dpi)
        style += f'font-size: {fontSize}{fontUnit};\n'
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
def validateImage(frame, elem):
    if frame.value not in imageCache:
        imageCache[frame.value] = QImage(frame.value)
    elem[frame.prop] = imageCache[frame.value]
    return True

class ImageElement():
    defaults = Element.defaults.new_child(dict([
        prop('width', validateHeightWidth, '0px'),
        prop('height', validateHeightWidth, '0px'),
        prop('source', validateImage, ''),
        prop('keepAspectRatio', 'toggle', 'yes'),
    ]))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        painter.drawPixmap(upperLeft, elem.source)

    @staticmethod
    def postGenerate(elem):
        scaleMode = Qt.SmoothTransformation
        if elem.keepAspectRatio:
            aspect = Qt.KeepAspectRatio
        else:
            aspect = Qt.IgnoreAspectRatio

        if elem.width == 0 and elem.height == 0:
            elem.width = elem.source.width()
            elem.height = elem.source.height()
        elif elem.keepAspectRatio:
            if elem.width == 0:
                elem.source = elem.source.scaledToHeight(elem.height, scaleMode)
                elem.width = elem.source.width()
            elif elem.height == 0:
                elem.source = elem.source.scaledToWidth(elem.width, scaleMode)
                elem.height = elem.source.height()
            else:
                elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)
                elem.width = elem.source.width()
                elem.height = elem.source.height()
        else:
            elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)
        
        elem.source = QPixmap.fromImage(elem.source)
            
class ImageBoxElement():
    defaults = ImageElement.defaults.new_child(dict([
        prop('alignment', validateAlignment, 'center middle'),
    ]))
    
class ShapeElement():
    defaults = Element.defaults.new_child(dict([
        prop('lineColor', 'string', 'black'),
        prop('lineWidth', 'number', '0.01in'),
        prop('lineJoin', validateLineJoin, 'miter'),
        prop('lineCap', validateLineCap, 'flat'),
        prop('fillColor', 'string', 'white'),
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
        prop('xRadius', 'number', '0px'),
        prop('yRadius', 'number', '0px'),
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
    #AAAAAAAAAAAAAHHHHHHHHHHHHHHHHHHHHHHHH
    defaults = ShapeElement.defaults.new_child(dict([
        prop('x2', validateXY, '1/4in'),
        prop('y2', validateXY, '1/4in'),
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
class ElementGenerator ():

    def __init__(self):
        self.elements = {}

    def generate(self, template:Element, validator:Validation):
        
        frame = AttrDict(name=template['name'])
        validator.store.add('elementName', frame.name)
        
        @validator.store.add('$', 1)
        def stripBrik(context, value):
            #parse vlaue and flatten to int    
            value = context.parse(value)
            valueUnit = Unit.fromStr(value, units='all')
            if valueUnit is None:
                raise InvalidArgError(context.elem, context.prop, '$', 'NUM', value)
            if frame.containerValue is not None:
                if type(frame.containerValue) not in (int, float):
                    return str(valueUnit.toInt(dpi=frame.layout.dpi))
                return str(valueUnit.toInt(dpi=frame.layout.dpi, whole=frame.containerValue))
            else:
                return str(valueUnit.toInt(dpi=frame.layout.dpi))

        frame.layout = AttrDict(**asdict(validator.layout))

        if template.container is None:
            frame.container = 'layout'
            frame.containerValue = None
        else:
            frame.container = self.elements[template.container].copy()
         
        elem = AttrDict(name=template['name'], container=template.container,
        type=template['type'])
        self.elements[elem.name] = elem
        frame.elem = elem
        
        for prop, value in template.items():
            if prop in ['name', 'x', 'y', 'type']:
                continue
            if frame.container != 'layout' and prop in frame.container:
                frame.containerValue = frame.container[prop]
            else:
                frame.containerValue = None
            validator.store.add('propertyName', prop)
            frame.prop = prop
            frame.value = validator.store.parse(value)
            validator.validate(frame)
        
        elemClass = elemClasses[template['type']]
        if hasattr(elemClass, 'postGenerate'):
            elemClass.postGenerate(elem)

        for prop in ['x', 'y']:
            value = template[prop]
            if template.container is not None and prop in frame.container:
                frame.containerValue = frame.container[prop]
            validator.store.add('propertyName', prop)
            frame.prop = prop
            frame.value = validator.store.parse(value)
            validator.validate(frame)
        return elem

@dataclass
class PDF():
    
    name:str = None
    render:bool = 'yes'
    xMargin:Unit = '.25in'
    yMargin:Unit = '.25in'
    border:Unit = '.01in'
    pageSize:QPageSize = 'letter'
    orientation:QPageLayout.Orientation = 'portrait'
    
    @staticmethod
    def fromDict(options, current, name):
        options = AttrDict(**options)
        if current is None:
            current = PDF()
        
        if 'name' in options:
            current.name = options.name
        else:
            current.name = os.path.splitext(os.path.basename(name))[0] + '.pdf'
        
        if 'render' in options:
            current.render = options.render
        if type(current.render) == str:
            render = asBool(current.render)
            if render is None:
                raise InvalidValueError('pdf', 'render', 'render')
            current.render = render
            

        for prop in ('xMargin', 'yMargin'):
            if prop in options:
                setattr(current, prop, options[prop])
            value = getattr(current, prop)
            if type(value) == str:
                num = Unit.fromStr(value, signs='+', units=('in', 'mm'))
                if num is None:
                    raise InvalidValueError('pdf', prop, value)
                setattr(current, prop, num)
        if current.xMargin.unit != current.yMargin.unit:
            raise bWError("pdf margins must use the same unit", file=name)
        
        if 'border' in options:
            current.border = options.border
        if type(current.border) == str:
            border = Unit.fromStr(current.border, signs='+', units=('in', 'mm'))
            if border is None:
                raise InvalidValueError('pdf', 'borders', current.border)
            current.border = border
        
        #these two need to be based on the Qt enum values
        if 'pageSize' in options:
            current.pageSize = options.pageSize
        if type(current.pageSize) == str:
            if current.pageSize.lower() == 'letter':
                current.pageSize = QPageSize.Letter
            elif current.pageSize.lower() == 'a4':
                current.pageSize = QPageSize.A4
            else:
                raise InvalidValueError('pdf', 'pageSize', current.pageSize)
        
        if 'orientation' in options:
            current.orientation = options.orientation
        if type(current.orientation) == str:
            if current.orientation.lower() == 'portrait':
                current.orientation = QPageLayout.Portrait
            elif current.orientation.lower() == 'landscape':
                current.orientation = QPageLayout.Landscape
            else:
                raise InvalidValueError('pdf', 'orientation', current.orientation)

        return current
    

@dataclass
class Layout():
    '''class for owning layouts'''
    
    width:int = '1in'
    widthUnit:Unit = None
    height:int = '1in'
    heightUnit:Unit = None
    name:str = 'asset.png'
    output:str = ''
    data:str = None
    elements:list = field(default_factory=dict)
    template:str = ''
    defaults:dict = field(default_factory=dict)
    filename:str = ''
    userBriks:dict = field(default_factory=dict)
    dpi:int = 300
    pdf:PDF = None

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

        self.images = []


    def paintElement(self, elem, painter:QPainter, generator):
        '''Paint a given element'''
        mid = QPoint(elem.width/2, elem.height/2)
        painter.translate(QPoint(elem.x, elem.y)+mid)
        painter.rotate(elem.rotation)
        elemClasses[elem.type].paint(elem, painter, -mid, QSize(elem.width, elem.height))
        #elemClasses[template['type']].paint(elem, painter, -mid, QSize(elem.width, elem.height))

    def paintAsset(self):
        '''paint the layout and the contained elements'''
        generator = ElementGenerator()
        elements = []
        for template in self.layout.elements.values():
            elem = generator.generate(template, self.validator)
            if elem.draw:
                elements.append(elem)

        image = QImage(self.layout.width, self.layout.height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)
        generator = ElementGenerator()
        painter = QPainter(image)
        painter.setClipRect(0, 0, self.layout.width, self.layout.height)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for element in elements:

            painter.resetTransform()
            painter.setPen(Qt.black)
            painter.setBrush(Qt.white)
            self.paintElement(element, painter, generator)

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


    def makePdf(self):
        pdf = self.layout.pdf
        #print(pdf)
        
        if pdf.xMargin.unit == 'in':
            unit = QPageLayout.Inch
        elif pdf.xMargin.unit == 'mm':
            unit = QPageLayout.Millimeter

        xMargin = pdf.xMargin.num
        yMargin = pdf.yMargin.num
        
        pageLayout = QPageLayout()
        pageLayout.setUnits(unit)
        pageLayout.setPageSize(QPageSize(pdf.pageSize))
        pageLayout.setOrientation(pdf.orientation)
        pageLayout.setMargins(QMarginsF(xMargin, yMargin, xMargin, yMargin))
        
        assetWidth = self.layout.widthUnit.toInt(dpi=self.layout.dpi)
        assetHeight = self.layout.heightUnit.toInt(dpi=self.layout.dpi)
        assetAcross = int(pageLayout.paintRect().width() // self.layout.widthUnit.num)
        assetDown = int(pageLayout.paintRect().height() // self.layout.heightUnit.num)

        if assetAcross == 0 or assetDown == 0:
            raise bWError("failed to render PDF, asset too large for printable area", file=self.layout.filename)

        assetPages = len(self.images)/(assetAcross*assetDown)
        if assetPages - int(assetPages) > 0:
            assetPages = int(assetPages) + 1
        
        pdfWriter = QPdfWriter(pdf.name)
        self._pdf = pdfWriter
        pdfWriter.setPageLayout(pageLayout)
        pdfWriter.setResolution(self.layout.dpi)
        pdfWriter.setCreator('brikWork')

        pdfPainter = QPainter()
        result = pdfPainter.begin(pdfWriter)
        if not result:
            raise bWError("failed to render pdf, no reason could be found. Maybe jsut try again?", file=self.layout.filename)

        assetsSeen = 0
        #print(assetDown, assetAcross, assetPages)
        limit = len(self.images)
        for page in range(assetPages):
            for down in range(assetDown):
                
                for across in range(assetAcross):
                    pdfPainter.drawImage(across*assetWidth, down*assetHeight, self.images[assetsSeen][0])
                    if pdf.border.num > 0:
                        pen = QPen()
                        pen.setWidth(pdf.border.toInt(dpi=self.layout.dpi))
                        pdfPainter.setPen(pen)
                        pdfPainter.drawRect(across*assetWidth, down*assetHeight, assetWidth, assetHeight)
                    assetsSeen += 1
                    if assetsSeen == limit:
                        break #down
                
                if assetsSeen == limit:
                    break #across
            
            if assetsSeen == limit:
                break #page
            
            pdfWriter.newPage()


    def save(self):
        '''save the generated images.'''
        path = os.getcwd()
        if  self.layout.output != '' and not os.path.isdir(self.layout.output):
            try:
                os.mkdir(self.layout.output)
            except IOError:
                os.chdir(path)
                raise bWError("failed to make output directory", file=self.layout.filename)
        os.chdir(os.path.realpath(self.layout.output))
        if self.layout.pdf != None and self.layout.pdf.render:
            self.makePdf()
        else:
            try:
                for image, name in self.images:
                    image.save(name)
            except OSError:
                os.chdir(path)
                raise bWError('failed to save images to {ouput}',
                output=self.layout.output, layout=self.layout.filename)
        os.chdir(path)



def parseData(rows:str):

    #data = parseCSV(rows)
    parser = CSVParser(rows)
    data = parser.parseCSV()
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
    
    layoutParser = LayoutParser(layoutText, filename)
    layoutFile = layoutParser.parseLayoutFile()
    if 'layout' in layoutFile:
        rawLayoutDict = layoutFile.pop('layout')
    else:
        #templates may not have a layout
        rawLayoutDict = {}

    if 'template' in rawLayoutDict:
        layout = buildLayout(rawLayoutDict.pop('template'))
    else:
        layout = Layout()
    layout.filename = filename
    
    if 'data' in rawLayoutDict:
        #prefer the data property over section
        dataFilename = rawLayoutDict.pop('data')
        if 'data' in layoutFile:
            layoutFile.pop('data')
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
    elif 'data' in layoutFile:
        userData = layoutFile.pop('data')
    else:
        userData = None
    if userData != None:
        layout.data = parseData(userData)
    
    #update layout with the rest of the props
    for prop, value in rawLayoutDict.items():
        #NOTE width and height get passed on as strings
        if prop == 'dpi':
            unit = Unit.fromStr(value, signs='+', units=('px',))
            if unit is None:
                raise InvalidValueError('layout', prop, value)
            value = unit.toInt()
        setattr(layout, prop, value)

    for prop in ('width', 'height'):
        #NOTE the width and height strings are parsed here, regardless of where they comefrom
        value = getattr(layout, prop)
        if type(value) == str:
            unit = Unit.fromStr(value, signs='+')
            if unit is None:
                raise InvalidValueError('layout', prop, value)
            setattr(layout, prop+'Unit', unit)
            setattr(layout, prop, unit.toInt(dpi=layout.dpi))
    
    if layout.heightUnit.unit != layout.widthUnit.unit:
        raise bWError("layout width and height must use the same unit",
        file=filename)

    if 'pdf' in layoutFile:
        pdfDict = layoutFile.pop('pdf')
        layout.pdf = PDF.fromDict(pdfDict, layout.pdf, filename)
        if layout.pdf.xMargin.unit != layout.widthUnit.unit:
            raise bWError("Layout size and pdf margins must use the same units",
            file=filename)

    if 'defaults' in layoutFile:
        deepUpdate(layout.defaults, layoutFile.pop('defaults'))

    if 'briks' in layoutFile:
        layout.userBriks.update(layoutFile.pop('briks'))
    
    def makeElements(items, container=None):
        for name, props in items:
            #props.pop('children')
            if name in layout.elements:
                #if the template includes this element usurp it
                layout.elements[name].maps.insert(0, props)
                children = props.pop('children')
                if len(children) > 0:
                    makeElements(children.items(), layout.elements[name]['name'])

            else:
                if container is not None:
                    name = f'{container}->{name}'
                if 'type' not in props:
                    props['type'] = 'none'
                elif props['type'] not in elemClasses:
                    raise InvalidValueError(name, 'type', prop['type'])
                elemType = elemClasses[props['type']]
                elem = elemType.defaults.new_child(props)
                elem.maps.insert(1, layout.defaults)
                elem.container = container
                elem['name'] = name
                
                layout.addElement(elem)
                children = props.pop('children')
                if len(children) > 0:
                    makeElements(children.items(), layout.elements[name]['name'])
        
    makeElements(layoutFile.items())
    

    return layout


if __name__ == '__main__':
    pageSize = QPageSize(QPageSize.A4)
    pageLayout = QPageLayout(pageSize, QPageLayout.Portrait, QMarginsF(.25, .25, .25, .25), units=QPageLayout.Inch)
    print(pageLayout.minimumMargins())
    print(pageLayout.margins())
    print(pageLayout.maximumMargins())