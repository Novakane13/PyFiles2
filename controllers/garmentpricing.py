import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QTreeWidgetItem, QApplication, QMessageBox
from views.garmentpricingui import Ui_garmentpricing  
from PySide6.QtCore import Qt

class GarmentPricingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_garmentpricing()
        self.ui.setupUi(self)
        
        self.ui.setprice.clicked.connect(self.set_price)
        self.ui.garmentvariationlist.itemClicked.connect(self.on_item_clicked)
        
        self.selected_item = None
        self.load_garments_and_variations()

    def load_garments_and_variations(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT g.id, g.name, g.image_path
            FROM Garments g
        """)
        
        garments = cursor.fetchall()
        for garment in garments:
            garment_id, garment_name, garment_image_path = garment
            garment_item = QTreeWidgetItem([f"{garment_name}"])
            garment_item.setData(0, Qt.UserRole, (garment_id, None))
            self.ui.garmentvariationlist.addTopLevelItem(garment_item)

            cursor.execute("""
                SELECT v.id, v.name, v.price
                FROM GarmentVariants v
                WHERE v.garment_id = ?
            """, (garment_id,))
            
            variations = cursor.fetchall()
            for variation in variations:
                variation_id, variation_name, variation_price = variation
                variation_item = QTreeWidgetItem([f"{variation_name} - ${variation_price:.2f}"])
                variation_item.setData(0, Qt.UserRole, (garment_id, variation_id))
                garment_item.addChild(variation_item)

        conn.close()

    def on_item_clicked(self, item):
        self.selected_item = item
        garment_id, variant_id = item.data(0, Qt.UserRole)
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if variant_id is None:
            self.ui.price.setText("0.00")
        else:
            cursor.execute("SELECT price FROM GarmentVariants WHERE id = ?", (variant_id,))
            result = cursor.fetchone()
            if result:
                self.ui.price.setText(f"{result[0]:.2f}")
            else:
                self.ui.price.setText("0.00")
        
        conn.close()

    def set_price(self):
        if self.selected_item is None:
            QMessageBox.warning(self, "No Item Selected", "Please select a garment or variation to set the price.")
            return
        
        garment_id, variant_id = self.selected_item.data(0, Qt.UserRole)
        try:
            new_price = float(self.ui.price.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Price", "Please enter a valid price.")
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if variant_id is None:
            QMessageBox.warning(self, "Invalid Selection", "Please select a variation to set the price.")
            return
        else:
            cursor.execute("UPDATE GarmentVariants SET price = ? WHERE id = ?", (new_price, variant_id))
        
        conn.commit()
        conn.close()

        self.selected_item.setText(0, f"{self.selected_item.text(0).split(' - ')[0]} - ${new_price:.2f}")

if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    window = GarmentPricingWindow()
    window.show()
    sys.exit(app.exec())
