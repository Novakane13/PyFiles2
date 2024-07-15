import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QColorDialog, QFileDialog, QListWidgetItem, QMessageBox
from PySide6.QtGui import QPixmap, QIcon, QColor, QBrush
from PySide6.QtCore import Qt
from views.Test import Ui_GarmentandColorCreation

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
        
        # Attributes to store selected color, image, and variations
        self.selected_color = None
        self.selected_image = None
        self.variations = []

        self.load_saved_colors()
        self.load_saved_garments()

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
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
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
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(self.ui.ImageLabel.size(), Qt.KeepAspectRatio)
            self.ui.ImageLabel.setPixmap(scaled_pixmap)

    def add_variation(self):
        variation_name = self.ui.lineEdit.text().strip()
        if not variation_name:
            QMessageBox.warning(self, "Input Error", "Please enter a variation name.")
            return
        
        self.variations.append(variation_name)
        self.ui.avlist.addItem(variation_name)
        self.ui.lineEdit.clear()

    def save_garment(self):
        garment_name = self.ui.gninput.text().strip()
        if not garment_name:
            QMessageBox.warning(self, "Input Error", "Please enter a garment name.")
            return
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cgarments (name, image) VALUES (?, ?)", (garment_name, self.selected_image))
        cgarment_id = cursor.lastrowid
        
        for variation in self.variations:
            cursor.execute("INSERT INTO cgarment_variations (cgarment_id, variation) VALUES (?, ?)", (cgarment_id, variation))
        
        conn.commit()
        conn.close()

        garment_item = QListWidgetItem(garment_name)
        if self.selected_image:
            garment_item.setIcon(QIcon(QPixmap(self.selected_image)))
        self.ui.sglist.addItem(garment_item)
        
        # Clear input fields and reset attributes
        self.ui.gninput.clear()
        self.ui.avlist.clear()
        self.ui.ImageLabel.clear()
        self.selected_image = None
        self.variations = []
        self.ui.sibutton.setText("Select Image")

    def load_saved_colors(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, color FROM colors")
        saved_colors = cursor.fetchall()
        conn.close()

        for color_name, color_value in saved_colors:
            item = QListWidgetItem(color_name)
            item.setBackground(QBrush(QColor(color_value)))
            self.ui.sclist.addItem(item)

    def load_saved_garments(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, image FROM cgarments")
        saved_garments = cursor.fetchall()
        conn.close()

        for garment_name, image_path in saved_garments:
            garment_item = QListWidgetItem(garment_name)
            if image_path:
                garment_item.setIcon(QIcon(QPixmap(image_path)))
            self.ui.sglist.addItem(garment_item)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = GarmentsColorsWindow()
    window.show()
    sys.exit(app.exec())
