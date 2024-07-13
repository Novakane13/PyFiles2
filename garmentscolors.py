import sqlite3
from PySide6.QtWidgets import QMainWindow, QColorDialog, QFileDialog, QListWidgetItem, QMessageBox
from Test import Ui_GarmentandColorCreation
from PySide6.QtGui import QPixmap, QIcon

class GarmentsColorsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_GarmentandColorCreation()
        self.ui.setupUi(self)
        
        # Connecting buttons to functions
        self.ui.dcbutton.clicked.connect(self.close)
        self.ui.ccbutton.clicked.connect(self.choose_color)
        self.ui.scbutton.clicked.connect(self.save_color)
        self.ui.sibutton.clicked.connect(self.select_image)
        self.ui.avbutton.clicked.connect(self.add_variation)
        self.ui.sgbutton.clicked.connect(self.save_garment)
        
        # Attributes to store selected color and image
        self.selected_color = None
        self.selected_image = None

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color
            self.ui.ccbutton.setStyleSheet(f"background-color: {color.name()}")
            self.ui.ccbutton.setText("Color Selected")

    def save_color(self):
        color_name = self.ui.cninput.text().strip()
        if not color_name:
            QMessageBox.warning(self, "Input Error", "Please enter a color name.")
            return
        if self.selected_color is None:
            QMessageBox.warning(self, "Input Error", "Please choose a color.")
            return
        
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO colors (name, color) VALUES (?, ?)", (color_name, self.selected_color.name()))
        conn.commit()
        conn.close()

        item = QListWidgetItem(color_name)
        item.setBackground(self.selected_color)
        self.ui.sclist.addItem(item)
        self.ui.cninput.clear()
        self.selected_color = None
        self.ui.ccbutton.setStyleSheet("")
        self.ui.ccbutton.setText("Choose Color")

    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            self.selected_image = file_name
            self.ui.sibutton.setText("Image Selected")

    def add_variation(self):
        variation_name = self.ui.gninput.text().strip()
        if not variation_name:
            QMessageBox.warning(self, "Input Error", "Please enter a variation name.")
            return
        
        self.ui.avlist.addItem(variation_name)
        self.ui.gninput.clear()

    def save_garment(self):
        garment_name = self.ui.gninput.text().strip()
        if not garment_name:
            QMessageBox.warning(self, "Input Error", "Please enter a garment name.")
            return
        if self.selected_image is None:
            QMessageBox.warning(self, "Input Error", "Please select an image.")
            return
        
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO garments (name, image) VALUES (?, ?)", (garment_name, self.selected_image))
        conn.commit()
        conn.close()

        garment_item = QListWidgetItem(garment_name)
        garment_item.setIcon(QIcon(QPixmap(self.selected_image)))
        self.ui.sglist.addItem(garment_item)
        
        self.ui.gninput.clear()
        self.ui.avlist.clear()
        self.selected_image = None
        self.ui.sibutton.setText("Select Image")

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = GarmentsColorsWindow()
    window.show()
    sys.exit(app.exec())
