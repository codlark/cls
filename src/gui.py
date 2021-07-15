from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from brikWorkEngine import *

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        center = QWidget(self)
        self.setCentralWidget(center)

        layout = QVBoxLayout(center)
        
        self.assetHolder = QLabel(center)
        layout.addWidget(self.assetHolder)
        self.assetHolder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.textLog = QTextEdit(center)
        layout.addWidget(self.textLog)
        self.textLog.setReadOnly(True)
        self.textLog.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

app = QApplication()
window = MainWindow()
window.resize(800, 600)

with open('src/test/test.bwl') as file:
    layoutText = file.read()

layout = buildLayout(layoutText, 'test')
painter = AssetPainter(layout)
painter.paint()
window.textLog.append(f'\ngenerated images')
image = QPixmap.fromImage(painter.images[0][0]).scaledToHeight(600)
window.assetHolder.setPixmap(image)

window.show()
app.exec()