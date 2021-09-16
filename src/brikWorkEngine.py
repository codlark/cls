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
    def validateRangeNumber(range, signs='+', units=('px', 'in', 'mm'), out=int):
        def validate(frame, sec):
            num = Unit.fromStr(frame.value, signs, units)
            if num is None:
                return False
            else:
                if out == int:
                    value = num.toInt()
                    if value < range[0] or value > range[1]:
                        return False
                elif out == float:
                    value = num.toFloat()
                    if value < range[0] or value > range[1]:
                        return False
                else:
                    if num.num < range[0] or num.num > range[1]:
                        return False
                    value = num
                sec[frame.prop] = value
                return True
        return validate

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

class ExportSection():
    defaults = ChainMap(dict(
        contentOnly = 'yes',
        name='',
    ))
    validators = ChainMap(dict(
        name = Section.validateString,
        contentOnly = validateToggle,
    ))
    names = ChainMap({
        'content-only': 'contentOnly'
    })

class BulkExport(ExportSection):
    defaults = ExportSection.defaults.new_child(dict(
        name = 'asset.png',
    ))
    validators = ExportSection.validators.new_child(dict())
    names = ExportSection.names.new_child({})

    @staticmethod
    def postGenerate(layout, sec):
        if sec.name == '':
            sec.name = os.path.splitext(os.path.basename(layout.filename))[0] + '.png'
        

class PDFSection(ExportSection):

    defaults = ExportSection.defaults.new_child(dict(
        xMargin = '.25in',
        yMargin = '.25in',
        border = '0.01in',
        pageSize = 'letter',
        orientation = 'portrait',
    ))

    validators = ExportSection.validators.new_child(dict(
        xMargin = Section.validateNumber(units=('in', 'mm'), out=Unit),
        yMargin = Section.validateNumber(units=('in', 'mm'), out=Unit),
        margin = validateManyStretch(xMargin=Section.validateNumber(units=('in', 'mm'), out=Unit),
           yMargin=Section.validateNumber(units=('in', 'mm'), out=Unit)),
        border = Section.validateNumber(units=('in', 'mm'), out=Unit),
        pageSize = Section.validatePageSize,
        orientation = Section.validateOrientation,
    ))

    names = ExportSection.names.new_child({
        'x-margin': 'xMargin',
        'y-margin': 'yMargin',
        'page-size': 'pageSize',
    })

    @staticmethod
    def postGenerate(layout, sec):
        if sec.xMargin.unit != sec.yMargin.unit:
            raise bWError("pdf margins must use the same unit", file=layout.filename)
        
        if sec.name == '':
            sec.name = os.path.splitext(os.path.basename(layout.filename))[0] + '.pdf'

class TTSExport(ExportSection):
    defaults = ExportSection.defaults.new_child(dict(
        across = '10',
        down = '7',
    ))
    validators = ExportSection.validators.new_child(dict(
        across = Section.validateRangeNumber((2, 10), units=('',)),
        down = Section.validateRangeNumber((2, 7), units=('',)),
        size = validateMany(2,
            across=Section.validateRangeNumber((2, 10), units=('',)), 
            down=Section.validateRangeNumber((2, 7), units=('',))
        )
    ))
    names = ExportSection.names.new_child({})


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
        size = validateMany(2, width=Section.validateNumber(units=('in', 'mm'), out=Unit), height=Section.validateNumber(units=('in', 'mm'), out=Unit)),
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
            if prop in PDFSection.names:
                trueProp = PDFSection.names[prop]
            else:
                trueProp = prop
            if trueProp not in PDFSection.validators:
                raise bWError("'{prop}' is not a known property",
                prop=prop, elem='pdf')
            func = PDFSection.validators[trueProp]
            frame.prop = trueProp
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
            self.store.add('asset-total', str(len(layout.data)))
            self.store.add('row-total', str(layout.data[-1]['row-index']))
       
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
        # TODO put in PDFSection
        pdf = self.layout.pdf
        dpi = self.layout.dpi
        border = pdf.border.toInt(dpi=dpi)
        #print(pdf)
        
        if pdf.xMargin.unit == 'in':
            unit = QPageLayout.Inch
        elif pdf.xMargin.unit == 'mm':
            unit = QPageLayout.Millimeter

        xMargin = pdf.xMargin.num
        yMargin = pdf.yMargin.num
        
        pageLayout = QPageLayout()
        pageLayout.setPageSize(QPageSize(pdf.pageSize))
        pageLayout.setOrientation(pdf.orientation)
        pageLayout.setUnits(unit)
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
            if None in (contentWidth, contentHeight, contentX, contentY):
                raise bWError("content position and size can't use briks", layout=layout.filename)
            if contentWidth.unit == contentHeight.unit:
                assetUnitWidth = contentWidth
                assetUnitHeight = contentHeight
                assetXOfs = contentX.toInt(dpi=dpi)
                assetYOfs = contentY.toInt(dpi=dpi)
        
        assetWidth = assetUnitWidth.toInt(dpi=dpi)
        assetHeight = assetUnitHeight.toInt(dpi=dpi)
        assetAcross = int(pageLayout.paintRectPixels(dpi).width() // assetWidth)
        assetDown = int(pageLayout.paintRectPixels(dpi).height() // assetHeight)

        if assetAcross == 0 or assetDown == 0:
            raise bWError("failed to render PDF, asset too large for printable area", file=self.layout.filename)

        assetPages, mod = divmod(len(self.images), assetAcross*assetDown)
        if mod > 0:
            assetPages += 1
        
        pdfWriter = QPdfWriter(pdf.name)
        self._pdf = pdfWriter
        pdfWriter.setPageLayout(pageLayout)
        pdfWriter.setResolution(dpi)
        pdfWriter.setCreator('brikWork')

        pdfPainter = QPainter()
        result = pdfPainter.begin(pdfWriter)
        if not result:
            raise bWError("failed to render pdf, is the file open elsewhere?", file=self.layout.filename)

        assetsSeen = 0
        #print(assetDown, assetAcross, assetPages)
        limit = len(self.images)
        for page in range(assetPages):
            for down in range(assetDown):
                
                for across in range(assetAcross):
                    pdfPainter.drawImage(across*assetWidth, down*assetHeight, self.images[assetsSeen][0],
                        assetXOfs, assetYOfs, assetWidth, assetHeight
                    )
                    if border > 0:
                        pen = QPen()
                        pen.setWidth(border)
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

assetI = 'asset-index'
assetT = 'asset-total'
rowI = 'row-index'
rowT = 'row-total'
repeatI = 'repeat-index'
repeatT = 'repeat-total'

def parseData(data):

    if data is None:
        return None

    newData = []

    if 'repeat' in data[0]:
        assetIndex = 1
        rowIndex = 1
        for row in data: #change to enumerate?
            
            repeatTotal = row.pop('repeat')
            if repeatTotal == '1':
                counts = {assetI:str(assetIndex), rowI:str(rowIndex), repeatI:'1', repeatT:repeatTotal}
                newData.append(row | counts)
                assetIndex += 1
                rowIndex += 1
            else:
                for repeat in range(int(repeatTotal)):
                    counts = {assetI:str(assetIndex), rowI:str(rowIndex), repeatI:str(repeat+1), repeatT:repeatTotal}
                    newData.append(row | counts)
                    assetIndex += 1
                rowIndex += 1

    else:
        for index, row in enumerate(data):
            counts = {assetI:str(index+1), rowI:str(index+1), repeatI:'1', repeatT:'1'}
            newData.append(row | counts)

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