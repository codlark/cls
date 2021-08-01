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
    value = asNum(frame.value)
    if value is None:
        return False
    elem[frame.prop] = value
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
    if frame.value == 'center':
        if frame.prop == 'x':
            dim = 'width'
        else:
            dim = 'height'
        
        if frame.container == 'layout':
            parentDim = frame.layout[dim]
            parentLoc = 0
        else:
            parentDim = frame.container[dim]
            parentLoc = frame.containerValue

        elem[frame.prop] = (parentDim-elem[dim])//2 + parentLoc
        return True
    else:
        value = asNum(frame.value)
        if value is None:
            return False
        if frame.container == 'layout':
            elem[frame.prop] = value
        else:
            elem[frame.prop] = value + frame.containerValue
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
        prop('x', validateXY, '0'),
        prop('y', validateXY, '0'),
        prop('width', 'number', '50'),
        prop('height', 'number', '50'),
        prop('rotation', 'number', '0'),
    ]))
    @staticmethod
    def paint(elem, painter, upperLect, size):
        pass

class LabelElement():
    defaults = Element.defaults.new_child(dict([
        prop('text', 'string', ''),
        prop('fontFamily', 'string', 'Verdana'),
        prop('fontSize', 'number', '18'),
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
def validateImage(frame, elem):
    if frame.value not in imageCache:
        imageCache[frame.value] = QImage(frame.value)
    elem[frame.prop] = imageCache[frame.value]
    return True

class ImageElement():
    defaults = Element.defaults.new_child(dict([
        prop('width', 'number', '0'),
        prop('height', 'number', '0'),
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
            

class ShapeElement():
    defaults = Element.defaults.new_child(dict([
        prop('lineColor', 'string', 'black'),
        prop('lineWidth', 'number', '1'),
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
        prop('xRadius', 'number', '0'),
        prop('yRadius', 'number', '0'),
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
        prop('x2', 'number', '50'),
        prop('y2', 'number', '50'),
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
    
    def getDraw(self, elem):
        #this will become the drawValidator func
        while elem.parent is not None:
            if not elem.draw:
                return False
            elem = self.elements[elem.parent]
        return elem.draw

    def generate(self, template:Element, validator:Validation):
        #TODO rename parent everywhere to container
        frame = AttrDict(name=template['name'])
        validator.store.add('elementName', frame.name)
        
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
            print(frame.name, prop, value)
            if frame.container != 'layout' and prop in frame.container:
                frame.containerValue = frame.container[prop]
            validator.store.add('propertyName', prop)
            frame.prop = prop
            frame.value = validator.store.parse(value)
            validator.validate(frame)
            print(elem[prop])
        
        elemClass = elemClasses[template['type']]
        if hasattr(elemClass, 'postGenerate'):
            elemClass.postGenerate(elem)
        
        prop = 'gloop'
        for prop in ['x', 'y']:
            value = template[prop]
            print(frame.name, prop, value)
            if template.parent is not None and prop in frame.container:
                frame.containerValue = frame.container[prop]
            validator.store.add('propertyName', prop)
            frame.prop = prop
            frame.value = validator.store.parse(value)
            validator.validate(frame)
            print(elem[prop])
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
    
    #update layout with the rest of the 
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
