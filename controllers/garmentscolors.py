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
        self.ui.dcbutton.clicked.connect(self.delete_color)
        self.ui.ccbutton.clicked.connect(self.choose_color)
        self.ui.scbutton.clicked.connect(self.save_color)
        self.ui.sibutton.clicked.connect(self.select_image)
        self.ui.avbutton.clicked.connect(self.add_variation)
        self.ui.sgbutton.clicked.connect(self.save_garment)
        self.ui.dgbutton.clicked.connect(self.delete_garment)
        
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
            self.apply_outline_color(color)
            
    def apply_outline_color(self, color):
        outline_style = f"border: 2px solid {color.name()};"
        widgets = [
            self.ui.centralwidget,
            self.ui.sgbutton,
            self.ui.sglist,
            self.ui.gninput,
            self.ui.gnlabel,
            self.ui.sglabel,
            self.ui.avbutton,
            self.ui.sibutton,
            self.ui.avlist,
            self.ui.avlabel,
            self.ui.egbutton,
            self.ui.dgbutton,
            self.ui.cninput,
            self.ui.cnlabel,
            self.ui.ccbutton,
            self.ui.sclist,
            self.ui.dcbutton,
            self.ui.scbutton,
            self.ui.sclabel,
            self.ui.ecbutton,
            self.ui.lineEdit,
            self.ui.label,
            self.ui.ImageLabel
        ]
        
        for widget in widgets:
            widget.setStyleSheet(outline_style)

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
        item.setData(Qt.UserRole, cursor.lastrowid)
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
        garment_item.setData(Qt.UserRole, cgarment_id)
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
        cursor.execute("SELECT id, name, color FROM colors")
        saved_colors = cursor.fetchall()
        conn.close()

        for color_id, color_name, color_value in saved_colors:
            item = QListWidgetItem(color_name)
            item.setBackground(QBrush(QColor(color_value)))
            item.setData(Qt.UserRole, color_id)
            self.ui.sclist.addItem(item)

    def load_saved_garments(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, image FROM cgarments")
        saved_garments = cursor.fetchall()
        conn.close()

        for garment_id, garment_name, image_path in saved_garments:
            garment_item = QListWidgetItem(garment_name)
            if image_path:
                garment_item.setIcon(QIcon(QPixmap(image_path)))
            garment_item.setData(Qt.UserRole, garment_id)
            self.ui.sglist.addItem(garment_item)

    def delete_garment(self):
        selected_item = self.ui.sglist.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a garment to delete.")
            return
        
        garment_id = selected_item.data(Qt.UserRole)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cgarments WHERE id = ?", (garment_id,))
        cursor.execute("DELETE FROM cgarment_variations WHERE cgarment_id = ?", (garment_id,))
        
        conn.commit()
        conn.close()
        
        self.ui.sglist.takeItem(self.ui.sglist.row(selected_item))

    def delete_color(self):
        selected_item = self.ui.sclist.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a color to delete.")
            return
        
        color_id = selected_item.data(Qt.UserRole)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM colors WHERE id = ?", (color_id,))
        
        conn.commit()
        conn.close()
        
        self.ui.sclist.takeItem(self.ui.sclist.row(selected_item))

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = GarmentsColorsWindow()
    window.show()
    sys.exit(app.exec())
