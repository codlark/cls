import os
import csv

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from bwStore import BrikStore
from bwUtils import *
from bwElements import *

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
    
    @staticmethod
    def validateCSV(frame, sec):
        if frame.value.lower() not in ('brikwork', 'excel'):
            return False
        else:
            sec[frame.prop] = frame.value.lower()
            return True

class PDFSection(Section):

    defaults = ChainMap(dict(
        name = '',
        render ='yes',
        xMargin = '.25in',
        yMargin = '.25in',
        border = '0.01in',
        pageSize = 'letter',
        orientation = 'portrait',
        contentOnly = 'false',
    ))

    validators = ChainMap(dict(
        name = Section.validateString,
        render = validateToggle,
        xMargin = Section.validateNumber(units=('in', 'mm'), out=Unit),
        yMargin = Section.validateNumber(units=('in', 'mm'), out=Unit),
        border = Section.validateNumber(units=('in', 'mm'), out=Unit),
        pageSize = Section.validatePageSize,
        orientation = Section.validateOrientation,
        contentOnly = validateToggle,
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
        csv = 'brikWork',
    ))

    validators = ChainMap(dict(
        width = Section.validateNumber(units=('in', 'mm'), out=Unit),
        height = Section.validateNumber(units=('in', 'mm'), out=Unit),
        name = Section.validateName,
        output = Section.validateString,
        data = Section.validateString,
        dpi = Section.validateNumber(units=('px'), out=int),
        csv = Section.validateCSV,
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

    #data
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
        if layout.csv == 'brikwork':
            reader = CSVParser(userData)
            data = reader.parseCSV()
        else:
            reader = csv.DictReader(userData.splitlines(), restval='')
            data = list(reader)
        layout.data = parseData(data)
        
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
                name = evalEscapes(self.store.parse(self.layout.name))
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

        assetUnitWidth = self.layout.widthUnit
        assetUnitHeight = self.layout.heightUnit
        assetXOfs = 0
        assetYOfs = 0

        if pdf.contentOnly and 'content' in self.layout.elements:
            content = self.layout.elements['content']
            contentWidth = Unit.fromStr(content['width'])
            contentHeight = Unit.fromStr(content['height'])
            contentX = Unit.fromStr(content['x'])
            contentY = Unit.fromStr(content['y'])
            if contentWidth.unit == contentHeight.unit \
              and contentWidth.unit == contentX.unit\
              and contentWidth.unit == pdf.xMargin.unit:
                assetUnitWidth = contentWidth
                assetUnitHeight = contentHeight
                assetXOfs = contentX.toInt(dpi=self.layout.dpi)
                assetYOfs = contentY.toInt(dpi=self.layout.dpi)
        
        assetWidth = assetUnitWidth.toInt(dpi=self.layout.dpi)
        assetHeight = assetUnitHeight.toInt(dpi=self.layout.dpi)
        assetAcross = int(pageLayout.paintRect().width() // assetUnitWidth.num)
        assetDown = int(pageLayout.paintRect().height() // assetUnitHeight.num)

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
                    pdfPainter.drawImage(across*assetWidth, down*assetHeight, self.images[assetsSeen][0],
                        assetXOfs, assetYOfs, assetWidth, assetHeight
                    )
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

def parseData(data):

    ##data = parseCSV(rows)
    #parser = CSVParser(rows)
    #data = parser.parseCSV()
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