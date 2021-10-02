import sys
import os
import argparse

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from brikWorkEngine import *

def getResource(filename):
    if getattr(sys, "frozen", False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)
    return os.path.join(datadir, 'res', filename)


state = Collection()
state.filename = ''
state.layout = None
state.painter = None
state.asset = 0

def openFile(filename):
    startingDir = os.getcwd()
    directory, filename = os.path.split(os.path.realpath(filename))
    os.chdir(directory)
    app.setOverrideCursor(waitCursor)
    try:
        #layoutText = _openFile(filename)
        layout = buildLayout(filename)
        painter = AssetPainter(layout)
        painter.paint()
        #state.asset = 0        

    except bWError as e:
        os.chdir(startingDir)
        #state.layout = None
        #state.painter = None
        #state.assetSpin.setValue(1)
        #state.assetSpin.setRange(1, 1)
        return False, e.message
    
    else:
        state.layout = layout
        state.painter = painter
        if len(state.painter.images) != state.assetSpin.value():
            state.assetSpin.setValue(1)
            state.assetSpin.setRange(1, len(state.painter.images))
        return True, f'generated {len(state.painter.images)} assets'
    
    finally:
        app.setOverrideCursor(arrowCursor)

def setImage():
    if state.painter is None:
        return
    if len(state.painter.images) == 0:
        return
    pix = QPixmap.fromImage(state.painter.images[state.assetSpin.value()-1][0])
    window.assetHolder.setPixmap(pix.scaledToHeight(window.assetHolder.size().height()-10, mode=Qt.SmoothTransformation))

@Slot()
def openFunc(earlyOpen):
    if earlyOpen:
        filename = state.filename
    else:
        filename, filter = QFileDialog.getOpenFileName(window, 'Open Layout File', '.', 'Layout Files (*.bwl)')

    if not os.path.isfile(filename):
        return
    
    state.filename = filename
    window.textLog.append('\n-----------')
    window.textLog.append(filename)
    window.textLog.append('-----------')
    
    shortFilename = os.path.split(state.filename)[1]
    window.setWindowTitle(f'{shortFilename} - brikWork')
    
    result, message = openFile(filename)
    if result:
        setImage()
    window.textLog.append(message)

@Slot()
def reloadFunc():
    result, message = openFile(state.filename)
    if result:
        setImage()
    window.textLog.append(message)

@Slot()
def spinChangeFunc(val):
    if state.painter is None:
        return
    state.asset = val
    setImage()

@Slot()
def exportFunc():
    if state.painter is not None:
        app.setOverrideCursor(waitCursor)
        try:
            state.painter.export(state.exportChoice.currentText())
        except bWError as e:
            window.textLog.append(e.message)
        else:
            window.textLog.append(f"saved cards to {state.layout.output}")
        finally:
            app.setOverrideCursor(arrowCursor)
    else:
        window.textLog.append('unable to save, no layout is present')
    

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle('brikWork')
        iconPath = getResource('logo.ico')
        icon = QIcon(iconPath)
        self.setWindowIcon(icon)

        center = QWidget(self)
        self.setCentralWidget(center)

        layout = QHBoxLayout(center)

        self.assetHolder = QLabel(center)
        layout.addWidget(self.assetHolder)
        self.assetHolder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.textLog = QTextEdit(center)
        layout.addWidget(self.textLog)
        self.textLog.setTabStopDistance(40.0)
        self.textLog.setWordWrapMode(QTextOption.NoWrap)
        self.textLog.setReadOnly(True)
        #self.textLog.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.toolbar = QToolBar(self)
        self.addToolBar(self.toolbar)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)

        openAct = QAction('Open Layout', parent=self)
        self.toolbar.addAction(openAct)
        openAct.triggered.connect(openFunc)

        reloadAct = QAction('Reload Layout', parent=self)
        self.toolbar.addAction(reloadAct)
        reloadAct.triggered.connect(reloadFunc)

        self.toolbar.addWidget(QLabel("Current Card ", parent=self))

        state.assetSpin = QSpinBox(parent=self)
        self.toolbar.addWidget(state.assetSpin)
        state.assetSpin.valueChanged.connect(spinChangeFunc)
        state.assetSpin.setRange(1,1)

        self.toolbar.addWidget(QLabel('Export Target '))

        state.exportChoice = QComboBox(self)
        self.toolbar.addWidget(state.exportChoice)
        state.exportChoice.addItems(['bulk', 'pdf', 'tts'])
        state.exportChoice.setEditable(False)

        exportAct = QAction('Export', parent=self)
        self.toolbar.addAction(exportAct)
        exportAct.triggered.connect(exportFunc)

        #exportBulkAct = QAction('bulk', parent=self)
        #self.toolbar.addAction(exportBulkAct)
        #exportBulkAct.triggered.connect(exportFunc, 'bulk')



    def resizeEvent(self, e):
        super().resizeEvent(e)
        setImage()


commandParser = argparse.ArgumentParser(
    description='brikwork command line app',
    add_help=True,
)
commandParser.add_argument('file', 
    metavar='FILE', 
    nargs='?',
    default=None,
    type=os.path.realpath,
    help='optional, a layout file to open and generate at startup'
)

commandParser.add_argument('-w', '--windowless',
    action='store_true',
    dest='windowless',
    help='generate and save cards without displaying a window, FILE must be provided'
)

app = QApplication()
window = MainWindow()
args = commandParser.parse_args()

waitCursor = QCursor(Qt.WaitCursor)
arrowCursor = QCursor()


if args.file is not None and args.windowless:
    result, message = openFile(args.file)
    print(message)
    if result:
        try:
            state.painter.save()
        except bWError as e:
            print(e.message)
        else:
            print(f"saved cards to {state.layout.output}")

elif not args.windowless:
    if args.file is not None:
        state.filename = args.file
        openFunc(True)
    window.show()
    window.resize(800, 600)
    app.exec()

elif args.windowless and args.file is None:
    commandParser.print_help()

