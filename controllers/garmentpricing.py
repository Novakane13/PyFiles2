import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QTreeWidgetItem, QApplication, QMessageBox
from views.Test import Ui_garmentpricing  # Import the UI from Test.py
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
            SELECT g.id, g.name, g.image, COALESCE(p.price, 0) as price
            FROM cgarments g
            LEFT JOIN prices p ON g.id = p.cgarment_id AND p.variation_id IS NULL
        """)
        
        garments = cursor.fetchall()
        for garment in garments:
            garment_id, garment_name, garment_image, garment_price = garment
            garment_item = QTreeWidgetItem([f"{garment_name} - ${garment_price:.2f}"])
            garment_item.setData(0, Qt.UserRole, (garment_id, None))
            self.ui.garmentvariationlist.addTopLevelItem(garment_item)

            cursor.execute("""
                SELECT v.id, v.variation, COALESCE(p.price, 0) as price
                FROM cgarment_variations v
                LEFT JOIN prices p ON v.id = p.variation_id
                WHERE v.cgarment_id = ?
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
        garment_id, variation_id = item.data(0, Qt.UserRole)
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if variation_id is None:
            cursor.execute("SELECT price FROM prices WHERE cgarment_id = ? AND variation_id IS NULL", (garment_id,))
        else:
            cursor.execute("SELECT price FROM prices WHERE cgarment_id = ? AND variation_id = ?", (garment_id, variation_id))
        
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
        
        garment_id, variation_id = self.selected_item.data(0, Qt.UserRole)
        try:
            new_price = float(self.ui.price.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Price", "Please enter a valid price.")
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if variation_id is None:
            cursor.execute("REPLACE INTO prices (cgarment_id, variation_id, price) VALUES (?, NULL, ?)", (garment_id, new_price))
        else:
            cursor.execute("REPLACE INTO prices (cgarment_id, variation_id, price) VALUES (?, ?, ?)", (garment_id, variation_id, new_price))
        
        conn.commit()
        conn.close()

        self.selected_item.setText(0, f"{self.selected_item.text(0).split(' - ')[0]} - ${new_price:.2f}")

if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    window = GarmentPricingWindow()
    window.show()
    sys.exit(app.exec())
