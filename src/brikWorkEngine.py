import os
import re
from bwStore import BrikStore
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
        parentDim = frame.layout[dim]
        parentLoc = 0
    else:
        parentDim = frame.container[dim]
        parentLoc = frame.container[frame.prop[0]]
        # on x2 and y2 use the container's x and y

    if frame.value == 'center':
        elem[frame.prop] = (parentDim-elem[dim])//2 + parentLoc
        return True
    else:
        value = Unit.fromStr(frame.value, signs='-+^',units=('px', 'in', 'mm', '%'))
        if value is None:
            return False
        if value.unit == '%':
            value = value.toInt(whole=parentDim)
        elif value.sign == '^':
            #TODO consider making ^ a signal not a sign to allow ^-.3
            value = parentDim - elem[dim] - value.toInt(dpi=frame.layout.dpi)
        else:
            value = value.toInt(dpi=frame.layout.dpi)
        elem[frame.prop] = value + parentLoc
        return True

def validateHeightWidth(frame, elem):
    if frame.container == 'layout':
        parentDim = frame.layout[frame.prop]
    else:
        parentDim = frame.container[frame.prop]
    value = Unit.fromStr(frame.value, units=('px', 'in', 'mm', '%'))
    if value is None:
        return False
    if value.unit == '%':
        value = value.toInt(whole=parentDim)
    else:
        value = value.toInt(dpi=frame.layout.dpi)
    elem[frame.prop] = value
    return True

def validateAngle(frame, elem):
    value = Unit.fromStr(frame.value, signs='+', units=('deg'))
    if value is None:
        return False
    value = value.toInt()
    if frame.container == 'layout':
        elem[frame.prop] = value % 360
    else:
        elem[frame.prop] = (value+frame.containerValue) % 360
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
    '''A subclass of ChainMap that also has attributes for parent and child relationships'''
    def __init__(self, *maps: Mapping) -> None:
        super().__init__(*maps)
        self.children = []
        self.parent = None


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
        prop('fontSize', validateFontSize, '18pt'),
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
        prop('lineWidth', 'number', '1px'),
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
        #TODO rename parent everywhere to container
        
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

        if template.parent is None:
            frame.container = 'layout'
            frame.containerValue = None
        else:
            frame.container = self.elements[template.parent].copy()
         
        elem = AttrDict(name=template['name'], container=template.parent,
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
            if template.parent is not None and prop in frame.container:
                frame.containerValue = frame.container[prop]
            validator.store.add('propertyName', prop)
            frame.prop = prop
            frame.value = validator.store.parse(value)
            validator.validate(frame)
        return elem

@dataclass
class Layout():
    '''class for owning layouts'''
    
    width:int = '1in'
    height:int = '1in'
    name:str = 'asset.png'
    output:str = ''
    data:str = None
    elements:list = field(default_factory=dict)
    template:str = ''
    defaults:dict = field(default_factory=dict)
    filename:str = ''
    userBriks:dict = field(default_factory=dict)
    dpi:int = 300

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

    def paintElement(self, elem, painter:QPainter, generator):
        '''Paint a given element'''
        #elem = generator.generate(template, self.validator)
        #if not generator.elements[elem.parent].draw:
        #    return
        #if not elem.draw:
        #    return
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


    def save(self):
        '''save the generated images.'''
        try:
            for image, name in self.images:
                image.save(os.path.join(self.layout.output, name))
        except OSError:
            raise bWError('failed to save images to {ouput}',
            output=self.layout.output, layout=self.layout.filename)



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
    parsedLayout = layoutParser.parseLayoutFile()
    if 'layout' in parsedLayout:
        rawLayout = parsedLayout.pop('layout')
    else:
        #templates may not have a layout
        rawLayout = {}


    if 'template' in rawLayout:
        layout = buildLayout(rawLayout.pop('template'))
    else:
        layout = Layout()
    layout.filename = filename
    
    if 'data' in rawLayout:
        #prefer the data property over section
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
    
    #update layout with the rest of the props
    for prop, value in rawLayout.items():
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
            setattr(layout, prop, unit.toInt(dpi=layout.dpi))



    if 'defaults' in parsedLayout:
        deepUpdate(layout.defaults, parsedLayout.pop('defaults'))

    if 'briks' in parsedLayout:
        layout.userBriks.update(parsedLayout.pop('briks'))
    
    def makeElements(items, parent=None):
        for name, props in items:
            #props.pop('children')
            if name in layout.elements:
                #if the template includes this element usurp it
                layout.elements[name].maps.insert(0, props)
                children = props.pop('children')
                if len(children) > 0:
                    makeElements(children.items(), layout.elements[name]['name'])

            else:
                if parent is not None:
                    name = f'{parent}->{name}'
                if 'type' not in props:
                    props['type'] = 'none'
                elif props['type'] not in elemClasses:
                    raise InvalidValueError(name, 'type', prop['type'])
                elemType = elemClasses[props['type']]
                elem = elemType.defaults.new_child(props)
                elem.maps.insert(1, layout.defaults)
                elem.parent = parent
                elem['name'] = name
                
                layout.addElement(elem)
                children = props.pop('children')
                if len(children) > 0:
                    makeElements(children.items(), layout.elements[name]['name'])
        
    makeElements(parsedLayout.items())
    

    return layout
