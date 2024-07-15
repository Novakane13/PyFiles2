from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class ColorWidget(QWidget):
    def __init__(self, name, color):
        super().__init__()
        self.name = name
        self.color = color
        self.initUI()
    
    def initUI(self):
        self.setStyleSheet(f"background-color: {self.color}; border: 1px solid black;")
        layout = QVBoxLayout()
        
        label = QLabel(self.name)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        self.setLayout(layout)
