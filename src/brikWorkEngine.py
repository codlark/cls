import os
import re
from bwStore import BrikStore
from collections import ChainMap
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from bwUtils import *


def validateString(frame, elem):
    elem[frame.prop] = evalEscapes(frame.value)
    return True

def validateNumber(signs='+', units=('px', 'in', 'mm'), out=int): 
    def func(frame, elem):
        num = Unit.fromStr(frame.value, signs, units)
        if num is None:
            return False
        else:
            if out == int:
                value = num.toInt(dpi=frame.layout.dpi)
            elif out == float:
                value = num.toFloat(dpi=frame.layout.dpi)
            else:
                value = num
            elem[frame.prop] = value
            return True
    return func

def validateToggle(frame, elem):
    value = asBool(frame.value)
    if value is None:
        return False
    elem[frame.prop] = value
    return True

def validateXY(frame, elem):
    #also handles x2 and y2
    if frame.prop[0] == 'x':
        dim = 'width'
    else:
        dim = 'height'
    if frame.container == 'layout':
        containerDim = frame.layout[dim]
    else:
        containerDim = frame.container[dim]

    if frame.value == 'center':
        #x2 and y2 shouldn't center, 
        elem[frame.prop] = (containerDim-elem[dim])//2
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
        elem[frame.prop] = value
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

class ElementProtoype(ChainMap):
    '''This class acts as the prototype of an element, prototype:element::layout:asset  '''
    def __init__(self, container, name, props:dict, defaults:dict, type_:"Element") -> None:
        super().__init__(props, defaults, *type_.defaults.maps)

        self.container = container
        self.subelements = {}
        self.name = name
        self.type = type_
        if container is not None:
            self.qualName = f'{container}->{name}'
        else:
            self.qualName = name
    
    def validate(self, frame:AttrDict):
        if frame.prop not in self.type.validators:
            raise bWError("'{name}' is not a known property", name=frame.prop, elem=frame.name)
        func = self.type.validators[frame.prop]
        result = func(frame, frame.elem)
        if not result:
            raise InvalidValueError(frame.elem.name, frame.prop, frame.value)
        else:
            return

    def generate(self, container, store, layout):

        frame = AttrDict(name=self.qualName)
        frame.layout = layout.copy()
        if container is None:
            frame.container = 'layout'
            frame.containerValue = None
        else:
            frame.container = container.copy()
         
        elem = AttrDict(name=self.qualName, type=self.type)
        frame.elem = elem
        
        store.add('elementName', self.qualName)
        
        for prop, value in self.items():
            if prop in ['x', 'y']:
                continue
            if frame.container != 'layout' and prop in frame.container:
                frame.containerValue = frame.container[prop]
            else:
                frame.containerValue = None
            store.add('propertyName', prop)
            frame.prop = prop
            frame.value = store.parse(value)
            #the validate function puts the new value on element
            self.validate(frame)

        
        if hasattr(self.type, 'postGenerate'):
            self.type.postGenerate(elem)

        for prop in ['x', 'y']:
            #x and y need to be validated after width and height
            value = self[prop]
            if frame.container != 'layout' and prop in frame.container:
                frame.containerValue = frame.container[prop]
            store.add('propertyName', prop)
            frame.prop = prop
            frame.value = store.parse(value)
            self.validate(frame)

        return elem


class Element():
    defaults = ChainMap(dict(
        draw =  'true',
        x =  '0px',
        y =  '0px',
        width =  '1/4in',
        height =  '1/4in',
        rotation =  '0',
    ))

    validators = ChainMap(dict(
        draw = validateDraw,
        x = validateXY,
        y = validateXY,
        width = validateHeightWidth,
        height = validateHeightWidth,
        rotation = validateAngle
    ))

    @staticmethod
    def paint(elem, painter, upperLect, size):
        pass

class LabelElement():
    defaults = Element.defaults.new_child(dict(
        text = '',
        fontFamily = 'Verdana',
        fontSize = '22pt',
        color = 'black',
        wordWrap = 'yes',
        alignment = 'center top',
        italic = 'no',
        bold = 'no',
        overline = 'no',
        underline = 'no',
        lineThrough = 'no',
    ))

    validators = Element.validators.new_child(dict(
        text = validateString,
        fontFamily = validateString,
        fontSize = validateFontSize,
        color = validateString,
        wordWrap = validateToggle,
        alignment = validateAlignment,
        italic = validateToggle,
        bold = validateToggle,
        overline = validateToggle,
        underline = validateToggle,
        lineThrough = validateToggle,

    ))

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
    defaults = Element.defaults.new_child(dict(
        width = '0px',
        height = '0px',
        source = '',
        keepAspectRatio = 'yes',
    ))

    validators = Element.validators.new_child(dict(
        source = validateImage,
        keepAspectRatio = validateToggle,
    ))

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

    @staticmethod
    def validateIBY(frame, elem):
        validateXY(frame, elem)
        
        imgWidth = elem.source.width()
        imgHeight = elem.source.height()

        if elem.alignment & Qt.AlignLeft:
            pass
        elif elem.alignment & Qt.AlignRight:
            elem.x += imgWidth
        else: #center or justify
            elem.x += imgWidth/2
        
        if elem.alignment & Qt.AlignTop:
            pass
        elif elem.alignment & Qt.AlignBottom:
            elem.y += imgHeight
        else:
            elem.y += imgHeight/2
        


    defaults = ImageElement.defaults.new_child(dict(
        alignment = 'center middle'
    ))

    validators = ImageElement.validators.new_child(dict(
        y = validateIBY, #post, post, generate
        alignment = validateAlignment
    ))
    
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        painter.drawPixmap(upperLeft, elem.source)
    
    def postGenerate(elem):
        pass


class ShapeElement():
    defaults = Element.defaults.new_child(dict(
        lineColor = 'black',
        lineWidth = '0.01in',
        lineJoin = 'miter',
        lineCap = 'flat',
        fillColor = 'white',
    ))

    validators = Element.validators.new_child(dict(
        lineColor = validateString,
        lineWidth = validateNumber(),
        lineJoin = validateLineJoin,
        lineCap = validateLineCap,
        fillColor = validateString,
    ))

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
    defaults = ShapeElement.defaults.new_child(dict(
        xRadius = '0px',
        yRadius = '0px',
    ))

    validators = ShapeElement.validators.new_child(dict(
        xRadius = validateNumber(),
        yRadius = validateNumber(),
    ))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        ShapeElement.readyPainter(elem, painter)
        painter.drawRoundedRect(QRect(upperLeft, size), elem.xRadius, elem.yRadius)

class EllipseElement():
    defaults = ShapeElement.defaults.new_child()
    validators = ShapeElement.validators.new_child()

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
    defaults = ShapeElement.defaults.new_child(dict(
        x2 = '1/4in',
        y2 = '1/4in',
    ))

    validators = ShapeElement.validators.new_child(dict(
        x2 = validateXY,
        y2 = validateXY,
    ))


    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.resetTransform()
        painter.drawLine(elem.x, elem.y, elem.x2, elem.y2)

elemClasses = dict(
    none = Element,
    label = LabelElement,
    image = ImageElement,
    #imageBox = ImageBoxElement,
    rect = RectangleElement,
    ellipse = EllipseElement,
    circle = EllipseElement,
    line = LineElement
)

class Section():
    @staticmethod
    def validateNumber(signs='+', units=('px', 'in', 'mm'), out=int): 
        def func(frame, elem):
            num = Unit.fromStr(frame.value, signs, units)
            if num is None:
                return False
            else:
                if out == int:
                    value = num.toInt()
                elif out == float:
                    value = num.toFloat()
                else:
                    value = num
                elem[frame.prop] = value
                return True
        return func
    
    @staticmethod
    def validateString(frame, sec):
        sec[frame.prop] = frame.value
        return True
    
    @staticmethod
    def validateName(frame, sec):
        if '[' not in frame.value:
            sec[frame.prop] = '[assetIndex]'+frame.value
        else:
            sec[frame.prop] = frame.value
        return True
    
    @staticmethod
    def validatePageSize(frame, sec):
        if frame.value.lower() == 'letter':
            sec[frame.prop] = QPageSize.Letter
            return True
        elif frame.value.lower() == 'a4':
            sec[frame.prop] = QPageSize.A4
            return True
        else:
            return False
        
    @staticmethod
    def validateOrientation(frame, sec):
        if frame.value.lower() == 'portrait':
            sec[frame.prop] = QPageLayout.Portrait
            return True
        elif frame.value.lower() == 'landscape':
            sec[frame.prop] = QPageLayout.Landscape
            return True
        else:
            return False

class PDFSection(Section):

    defaults = ChainMap(dict(
        name = '',
        render ='yes',
        xMargin = '.25in',
        yMargin = '.25in',
        border = '0.1in',
        pageSize = 'letter',
        orientation = 'portrait',
    ))

    validators = ChainMap(dict(
        name = Section.validateString,
        render = validateToggle,
        xMargin = Section.validateNumber(units=('in', 'mm'), out=Unit),
        yMargin = Section.validateNumber(units=('in', 'mm'), out=Unit),
        border = Section.validateNumber(units=('in', 'mm'), out=Unit),
        pageSize = Section.validatePageSize,
        orientation = Section.validateOrientation,
    ))

    @staticmethod
    def postGenerate(layout, sec):
        if sec.xMargin.unit != sec.yMargin.unit:
            raise bWError("pdf margins must use the same unit", file=layout.filename)
        if layout.widthUnit.unit != sec.xMargin.unit:
            raise bWError("magins and layout size must be defined in the same units", file=layout.filename)
        
        if sec.name == '':
            sec.name = os.path.splitext(os.path.basename(layout.filename))[0] + '.pdf'

class LayoutSection(Section):

    defaults = ChainMap(dict(
        width = '1in',
        height = '1in',
        name = 'asset.png',
        output = '',
        data = '',
        dpi = '300',
    ))

    validators = ChainMap(dict(
        width = Section.validateNumber(units=('in', 'mm'), out=Unit),
        height = Section.validateNumber(units=('in', 'mm'), out=Unit),
        name = Section.validateName,
        output = Section.validateString,
        data = Section.validateString,
        dpi = Section.validateNumber(units=('px'), out=int),
    ))

def parseLayout(filename):
    '''Parses the layout out of the file and turns it into a dict
    also handles templates'''
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

    layout = LayoutParser(layoutText, filename).parseLayoutFile()
    if 'template' in layout['props']:
        template = parseLayout(layout['props']['template'])
        deepUpdate(template, layout)
        template['props'].pop('template', None)
        return template
    else:
        return layout

def buildLayout(filename):

    parsedLayout = parseLayout(filename)

    layoutProto = LayoutSection.defaults.new_child(parsedLayout['props'])

    frame = AttrDict()
    layout = AttrDict(filename=filename)

    for prop, value in layoutProto.items():
        if prop not in LayoutSection.validators:
            raise bWError("'{prop}' is not a valid layout property",
            prop=prop, file=filename)
        func = LayoutSection.validators[prop]
        frame.prop = prop
        frame.value = value
        result = func(frame, layout)
        if not result:
            raise InvalidValueError('layout', prop, value)
    
    layout.widthUnit = layout.width
    layout.width = layout.widthUnit.toInt(dpi=layout.dpi)
    layout.heightUnit = layout.height
    layout.height = layout.heightUnit.toInt(dpi=layout.dpi)
    if layout.heightUnit.unit != layout.widthUnit.unit:
        raise bWError("layout width and height must use the same unit",
        file=filename)

    sections = parsedLayout['sections']

    if layout.data != '':
        #prefer the data property over section
        dataFilename = layout.data
        if 'data' in sections:
            sections.pop('data')
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
    elif 'data' in sections:
        userData = sections['data']
    else:
        userData = None
    if userData != None:
        layout.data = parseData(userData)
    else:
        layout.data = None
        
    #pdf
    if 'pdf' in sections:
        pdfProto = PDFSection.defaults.new_child(sections['pdf'])
        frame = AttrDict()
        layout.pdf = AttrDict()

        for prop, value in pdfProto.items():
            if prop not in PDFSection.validators:
                raise bWError("'{prop}' is not a known property",
                prop=prop, elem='pdf')
            func = PDFSection.validators[prop]
            frame.prop = prop
            frame.value = value
            result = func(frame, layout.pdf)
            if not result:
                raise InvalidValueError('pdf', prop, value)

        PDFSection.postGenerate(layout, layout.pdf)

    else:
        layout.pdf = None

    #defaults
    if 'defaults' in sections:
        layout.defaults = sections['defaults']
    else:
        layout.defaults = {}

    #briks
    if 'briks' in sections:
        layout.userBriks = sections['briks']
    else:
        layout.userBriks = {}

    #elemnts
    def makeElements(source, dest, container=None):
        for name, props in source.items():

            if name in dest:
                #if the template includes this element usurp it
                proto = dest[name]
                proto.maps.insert(0, props)
                children = props.pop('children')
                if len(children) > 0:
                    makeElements(children, proto.subelements, proto.qualName)
                    
            else:
                type_ = props.pop('type', 'none')
                if type_ not in elemClasses:
                    raise InvalidValueError(name, 'type', type_)
                proto = ElementProtoype(container, name, props, layout.defaults, elemClasses[type_])
                dest[name] = proto
                children = props.pop('children')
                if len(children) > 0:
                    makeElements(children, proto.subelements, proto.qualName)
    layout.elements = {}
    makeElements(parsedLayout['elements'], layout.elements)

    return layout

class AssetPainter():
    def __init__(self, layout):
        self.layout = layout
        self.store = BrikStore()
        if layout.data is not None:
            self.store.add('assetTotal', str(len(layout.data)))
            self.store.add('rowTotal', str(layout.data[-1]['rowIndex']))
       
        self.store.briks.update(self.layout.userBriks)

        self.images = []

    def generate(self, source:dict[str, ElementProtoype], dest, container=None):
        
        for name, proto in source.items():
            elem = proto.generate(container, self.store, self.layout)
            if elem.draw:
                dest[name] = elem
                elem.subelements = {}
                if len(proto.subelements) > 0:
                    self.generate(proto.subelements, elem.subelements, elem)

    def paintElement(self, elem, painter:QPainter):
        '''Paint a given element'''
        painter.save()
        mid = QPoint(elem.width/2, elem.height/2)
        painter.translate(QPoint(elem.x, elem.y)+mid)
        painter.rotate(elem.rotation)
        elem.type.paint(elem, painter, -mid, QSize(elem.width, elem.height))
        if len(elem.subelements) > 0:
            painter.translate(-mid)
            for subelem in elem.subelements.values():
                self.paintElement(subelem, painter)

        painter.restore()

    def paintAsset(self):
        '''paint the layout and the contained elements'''
        elements = {}
        self.generate(self.layout.elements, elements)

        image = QImage(self.layout.width, self.layout.height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setClipRect(0, 0, self.layout.width, self.layout.height)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for element in elements.values():
            #painter.resetTransform()
            painter.setPen(Qt.black)
            painter.setBrush(Qt.white)
            self.paintElement(element, painter)

        return image

    

    def paint(self):
        '''paint a set of assets based on the current layout and data file.'''

        if self.layout.data is None:
                image = self.paintAsset()
                name = self.store.parse(self.layout.name)
                self.images.append((image, name))

        else:
            for row in  self.layout.data:
                #TODO figure out a better way to do this
                self.store.briks.update(row)
                image = self.paintAsset()
                name = self.store.parse(self.layout.name)
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


if __name__ == '__main__':
    import pprint
    try:
        layout = buildLayout(os.path.join(os.getcwd(), 'test.bwl'))
    except bWError as e:
        print(e.message)
        import sys
        sys.exit()
    print(pprint.pformat(layout.elements['icon'].subelements))