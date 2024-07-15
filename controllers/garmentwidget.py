from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class GarmentWidget(QWidget):
    def __init__(self, name, image_path):
        super().__init__()
        self.name = name
        self.image_path = image_path
        self.initUI()
    
    def initUI(self):
        self.setStyleSheet("background-color: black; border: 1px solid black;")
        layout = QVBoxLayout()
        
        label = QLabel(self.name)
        label.setStyleSheet("color: white;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        if self.image_path:
            pixmap = QPixmap(self.image_path)
            image_label = QLabel()
            image_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            layout.addWidget(image_label)
        
        self.setLayout(layout)
