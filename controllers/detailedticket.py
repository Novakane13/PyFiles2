import re
import sys
import sqlite3
import os
from datetime import datetime
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QTreeWidgetItem, QVBoxLayout, QComboBox, QPushButton, QApplication, QMessageBox, QTableWidgetItem, QAbstractItemView 
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, Signal, QDate, QDateTime
from views.Test import Ui_DetailedTicketCreation
from views.Test import get_next_ticket_number



class DetailedTicketWindow(QMainWindow):
    ticket_completed = Signal(int)

    def __init__(self, customer_id=None, employee_id=None, tt_name=None, ticket_type_id1=None, tt_name2=None, ticket_type_id2=None, tt_name3=None, ticket_type_id3=None,
                 pieces1=1, pieces2=None, pieces3=None, due_date1=None, due_date2=None, due_date3=None,
                 notes1=None, notes2=None, notes3=None, all_notes=None, parent=None):
        super(DetailedTicketWindow, self).__init__(parent)
        self.ui = Ui_DetailedTicketCreation()
        self.ui.setupUi(self)
        

        # Store customer and employee IDs
        self.customer_id = customer_id
        self.employee_id = employee_id

        # Ticket details for three tabs
        self.tt_name = tt_name
        self.ticket_type_id1 = ticket_type_id1
        self.tt_name2 = tt_name2
        self.ticket_type_id2 = ticket_type_id2
        self.tt_name3 = tt_name3
        self.ticket_type_id3 = ticket_type_id3

        self.pieces1 = pieces1
        self.pieces2 = pieces2
        self.pieces3 = pieces3

        self.due_date1 = due_date1
        self.due_date2 = due_date2
        self.due_date3 = due_date3

        self.notes1 = notes1
        self.notes2 = notes2
        self.notes3 = notes3

        self.all_notes = all_notes

        self.ticket_numbers = [None, None, None]
        
        self.garments_per_tab = {0: [], 1: [], 2: []}

        # Connect UI elements
        self.ui.canceltbutton.clicked.connect(self.close)  # Close functionality
        self.ui.ctbutton.clicked.connect(self.create_ticket)  # Create ticket functionality
        self.ui.tctabs.currentChanged.connect(self.on_tab_change)  # Handle tab changes

        
        self.populate_tabs()
        

        # Connect single click events to select a garment
        self.ui.glist.itemClicked.connect(self.select_garment)

        # Connect the "Add to Garment" button
        self.ui.addtogarmentbutton.clicked.connect(self.add_selected_options_to_garment)

        self.selected_garment_item = None

        # Initially hide the combobox
        self.ui.garmentvariantsbox.setVisible(False)
        self.ui.garmentvariantsbox.currentIndexChanged.connect(self.add_variant_to_ticket)

        # Connect plus and minus buttons to increment and decrement the number of pieces
        self.ui.plusbutton.clicked.connect(self.increment_pieces)
        self.ui.minusbutton.clicked.connect(self.decrement_pieces)
        self.ui.piecesdisplay.display(1)

        self.combobox_selection_in_progress = False

        # Connect item click events for all tab lists
        self.ui.sglist.itemClicked.connect(self.select_garment_variant)
        self.ui.sglist_2.itemClicked.connect(self.select_garment_variant)
        self.ui.sglist_3.itemClicked.connect(self.select_garment_variant)

        self.selected_variant_row = None

        self.delivery_fee = 0
        self.items_per_tab = {0: [], 1: [], 2: []}  # Initialize for storing garments by tab

       
        self.update_totals()
        
        self.populate_widgets_for_current_tab()
        
        self.setup_table_headers()
        
    def populate_widgets_for_current_tab(self):
        # Get the current tab index
        current_index = self.ui.tctabs.currentIndex()
        
        # Restore saved garment list and notes for the current tab
        self.restore_saved_garment_list(current_index)
        self.load_tab_notes(current_index)

        # Get the correct ticket_type_id based on the current tab
        ticket_type_id = None
        if current_index == 0:
            ticket_type_id = self.ticket_type_id1
        elif current_index == 1:
            ticket_type_id = self.ticket_type_id2
        elif current_index == 2:
            ticket_type_id = self.ticket_type_id3

        # If we have a valid ticket_type_id, populate the widgets for this ticket type
        if ticket_type_id:
            self.populate_widgets_for_ticket_type(ticket_type_id)
            
        self.setup_table_headers()

    def restore_saved_garment_list(self, tab_index):
        """Restore garments for the given tab from saved data."""
        current_garment_list = self.get_current_garment_list()
        current_garment_list.setRowCount(0)
        
        if tab_index in self.garments_per_tab:
            for garment in self.garments_per_tab[tab_index]:
                row_position = current_garment_list.rowCount()
                current_garment_list.insertRow(row_position)

                quantity_item = QTableWidgetItem(str(garment['quantity']))
                variant_item = QTableWidgetItem(f"Variant {garment['garment_variant_id']}")
                colors_item = QTableWidgetItem(garment['colors'])
                patterns_item = QTableWidgetItem(garment['patterns'])
                textures_item = QTableWidgetItem(garment['textures'])
                upcharges_item = QTableWidgetItem(garment['upcharges'])
                price_item = QTableWidgetItem(f"${garment['price']:.2f}")

                current_garment_list.setItem(row_position, 0, quantity_item)
                current_garment_list.setItem(row_position, 1, variant_item)
                current_garment_list.setItem(row_position, 2, colors_item)
                current_garment_list.setItem(row_position, 3, patterns_item)
                current_garment_list.setItem(row_position, 4, textures_item)
                current_garment_list.setItem(row_position, 5, upcharges_item)
                current_garment_list.setItem(row_position, 6, price_item)
    
    def load_tab_notes(self, tab_index):
        """Load notes for the active tab."""
        if tab_index == 0:
            self.ui.ticketnotes.setPlainText(self.notes1)
        elif tab_index == 1:
            self.ui.ticketnotes_2.setPlainText(self.notes2)
        elif tab_index == 2:
            self.ui.ticketnotes_3.setPlainText(self.notes3)
            self.setup_table_headers()
    
    def populate_widgets_for_ticket_type(self, ticket_type_id):
        print(f"Populating widgets for ticket_type_id: {ticket_type_id}")
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            self.clear_widgets()  # Clear all widgets before populating

            # Populate colors, patterns, textures, upcharges, and garments
            self.populate_ticket_details(cursor, ticket_type_id)
            self.populate_garments(cursor, ticket_type_id)
            self.setup_table_headers()


    def populate_ticket_details(self, cursor, ticket_type_id):
        # Query maps for colors, patterns, textures, and upcharges
        query_map = {
            "colors": """
                SELECT c.id, c.name 
                FROM Colors c 
                JOIN ticket_type_colors ttc ON ttc.colors_id = c.id 
                WHERE ttc.ticket_type_id = ?
            """,
            "patterns": """
                SELECT p.id, p.name 
                FROM Patterns p 
                JOIN ticket_type_patterns ttp ON ttp.patterns_id = p.id 
                WHERE ttp.ticket_type_id = ?
            """,
            "textures": """
                SELECT t.id, t.name 
                FROM Textures t 
                JOIN ticket_type_textures ttt ON ttt.textures_id = t.id 
                WHERE ttt.ticket_type_id = ?
            """,
            "upcharges": """
                SELECT u.id, u.name, u.price 
                FROM Upcharges u 
                JOIN ticket_type_upcharges ttu ON ttu.upcharges_id = u.id 
                WHERE ttu.ticket_type_id = ?
            """
        }

        # Iterate over the query map to populate each corresponding widget
        for key, query in query_map.items():
            cursor.execute(query, (ticket_type_id,))
            results = cursor.fetchall()
            list_widget = getattr(self.ui, f"{key[0]}list")  # Get the widget for the key (e.g., clist for colors)

            list_widget.clear()  # Clear the list widget

            # Populate the list widget
            for result in results:
                if key == "upcharges":
                    item_id, item_name, item_price = result
                    item_name = f"{item_name} (${item_price:.2f})"
                else:
                    item_id, item_name = result

                item = QListWidgetItem(item_name)
                item.setData(Qt.UserRole, item_id)
                list_widget.addItem(item)


    def populate_garments(self, cursor, ticket_type_id):
        # Retrieve garments associated with the ticket_type_id
        cursor.execute("""
            SELECT g.id, g.name, g.image_path, v.id, v.name, COALESCE(v.price, 0) as price
            FROM Garments g
            LEFT JOIN GarmentVariants v ON g.id = v.garment_id
            JOIN ticket_type_garments ttg ON ttg.garments_id = g.id
            WHERE ttg.ticket_type_id = ?
        """, (ticket_type_id,))

        garments = {}
        for row in cursor.fetchall():
            garment_id, garment_name, garment_image, variant_id, variant_name, price = row
            if garment_id not in garments:
                garments[garment_id] = {
                    'name': garment_name,
                    'image': garment_image,
                    'variants': []
                }
            garments[garment_id]['variants'].append((variant_id, variant_name, price))

        # Add garments to the list widget
        for garment_id, garment_info in garments.items():
            try:
                garment_item = QListWidgetItem(QIcon(garment_info['image']), garment_info['name'])
                garment_item.setData(Qt.UserRole, garment_id)
                self.ui.glist.addItem(garment_item)
            except Exception as e:
                print(f"Error loading garment {garment_info['name']}: {e}")


    def setup_table_headers(self):
        headers = ["Counted Pieces", "Garment Variant", "Colors", "Patterns", "Textures", "Upcharges", "Price"]
        
        self.ui.sglist.setColumnCount(len(headers))
        self.ui.sglist.setHorizontalHeaderLabels(headers)
        self.ui.sglist.setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.sglist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.sglist.setSelectionMode(QAbstractItemView.SingleSelection)

        self.ui.sglist_2.setColumnCount(len(headers))
        self.ui.sglist_2.setHorizontalHeaderLabels(headers)
        self.ui.sglist_2.setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.sglist_2.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.sglist_2.setSelectionMode(QAbstractItemView.SingleSelection)

        self.ui.sglist_3.setColumnCount(len(headers))
        self.ui.sglist_3.setHorizontalHeaderLabels(headers)
        self.ui.sglist_3.setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.sglist_3.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.sglist_3.setSelectionMode(QAbstractItemView.SingleSelection)

    def increment_pieces(self):
        current_value = self.ui.piecesdisplay.intValue()
        self.ui.piecesdisplay.display(current_value + 1)

    def decrement_pieces(self):
        current_value = self.ui.piecesdisplay.intValue()
        if current_value > 1:
            self.ui.piecesdisplay.display(current_value - 1)
            
    def save_current_tab_data(self):
        current_index = self.ui.tctabs.currentIndex()
        self.garments_per_tab[current_index] = self.get_current_garment_list_data()
        
        if current_index == 0:
            self.notes1 = self.ui.ticketnotes.toPlainText()
            
        elif current_index == 1:
            self.notes2 = self.ui.ticketnotes_2.toPlainText()
            
        elif current_index == 2:
            self.notes3 = self.ui.ticketnotes_3.toPlainText()
            

    def get_current_garment_list_data(self):
        """Retrieve the garments, variants, and their details from the current tab."""
        current_garment_list = self.get_current_garment_list()
        tab_garments = []
        if current_garment_list:
            for row in range(current_garment_list.rowCount()):
                garment_variant_id = current_garment_list.item(row, 1).data(Qt.UserRole)
                garment_variant_name = current_garment_list.item(row, 1).text()
                quantity = int(current_garment_list.item(row, 0).text())
                price = float(current_garment_list.item(row, 6).text().replace("$", ""))
                colors = current_garment_list.item(row, 2).text()
                patterns = current_garment_list.item(row, 3).text()
                textures = current_garment_list.item(row, 4).text()
                upcharges = current_garment_list.item(row, 5).text()

                tab_garments.append({
                    "garment_variant_id": garment_variant_id,
                    "garment_variant_name": garment_variant_name,
                    "quantity": quantity,
                    "price": price,
                    "colors": colors,
                    "patterns": patterns,
                    "textures": textures,
                    "upcharges": upcharges,
                })
        return tab_garments

    def on_tab_change(self, index):
        """Save data from the current tab and load the data for the selected tab."""
        self.save_current_tab_data()  # Save the current tab's data
        self.clear_widgets()  # Clear the current widgets

        if index == 0:
            ticket_type_id = self.ticket_type_id1
        elif index == 1:
            ticket_type_id = self.ticket_type_id2
        elif index == 2:
            ticket_type_id = self.ticket_type_id3

        if ticket_type_id:
            self.populate_widgets_for_ticket_type(ticket_type_id)

        self.load_garment_variants_for_tab(index)
        
        


    def load_garment_variants_for_tab(self, tab_index):
        """Load the saved garments and their details for the specified tab."""
        current_garment_list = self.get_current_garment_list()
        current_garment_list.setRowCount(0)

        if tab_index in self.garments_per_tab:
            for garment in self.garments_per_tab[tab_index]:
                row_position = current_garment_list.rowCount()
                current_garment_list.insertRow(row_position)

                quantity_item = QTableWidgetItem(str(garment['quantity']))
                variant_item = QTableWidgetItem(garment.get('garment_variant_name', 'Variant None'))  
                variant_item.setData(Qt.UserRole, garment['garment_variant_id'])
                colors_item = QTableWidgetItem(garment['colors'])
                patterns_item = QTableWidgetItem(garment['patterns'])
                textures_item = QTableWidgetItem(garment['textures'])
                upcharges_item = QTableWidgetItem(garment['upcharges'])
                price_item = QTableWidgetItem(f"${garment['price']:.2f}")

                current_garment_list.setItem(row_position, 0, quantity_item)
                current_garment_list.setItem(row_position, 1, variant_item)
                current_garment_list.setItem(row_position, 2, colors_item)
                current_garment_list.setItem(row_position, 3, patterns_item)
                current_garment_list.setItem(row_position, 4, textures_item)
                current_garment_list.setItem(row_position, 5, upcharges_item)
                current_garment_list.setItem(row_position, 6, price_item)
        self.setup_table_headers()
    def populate_tabs(self):
        
        if self.ticket_type_id1:
            self.populate_tab(1, self.ticket_type_id1, self.pieces1, self.due_date1, self.notes1)
        self.setup_table_headers()

        
        if self.ticket_type_id2:
            self.populate_tab(2, self.ticket_type_id2, self.pieces2, self.due_date2, self.notes2)
        self.setup_table_headers()

        
        if self.ticket_type_id3:
            self.populate_tab(3, self.ticket_type_id3, self.pieces3, self.due_date3, self.notes3)
        self.setup_table_headers()

        
        self.apply_all_notes()

    def populate_tab(self, tab_index, ticket_type_id, pieces, due_date, notes):
        if tab_index == 1:
            self.ui.ticketnotes.setPlainText(notes)
        elif tab_index == 2:
            self.ui.ticketnotes_2.setPlainText(notes)
        elif tab_index == 3:
            self.ui.ticketnotes_3.setPlainText(notes)

    def apply_all_notes(self):
        if self.all_notes:
            if self.ticket_type_id1:
                self.ui.ticketnotes.setPlainText(self.ui.ticketnotes.toPlainText() + "\n" + self.all_notes)
            if self.ticket_type_id2:
                self.ui.ticketnotes_2.setPlainText(self.ui.ticketnotes_2.toPlainText() + "\n" + self.all_notes)
            if self.ticket_type_id3:
                self.ui.ticketnotes_3.setPlainText(self.ui.ticketnotes_3.toPlainText() + "\n" + self.all_notes)
                

    def update_totals(self):
        current_index = self.ui.tctabs.currentIndex()

        initial_price = sum(quantity * price for _, _, quantity, price in self.items_per_tab[current_index])
        deductions = 0
        taxes = initial_price * 0.1
        delivery_fee = self.delivery_fee
        total_price = initial_price - deductions + taxes + delivery_fee

        self.ui.initial_price_label.setText(f"Initial Price: ${initial_price:.2f}")
        self.ui.total_price_label.setText(f"Total Price: ${total_price:.2f}")
        self.ui.deductions_label.setText(f"Deductions: ${deductions:.2f}")
        self.ui.taxes_label.setText(f"Taxes: ${taxes:.2f}")
        self.ui.delivery_fee_label.setText(f"Delivery Fee: ${delivery_fee:.2f}")
        self.setup_table_headers()

    def load_ticket_data(self, index):
        if not self.ticket_numbers[index]:
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT tg.id, gv.name, tg.quantity, tg.price
                FROM TicketGarments tg
                JOIN GarmentVariants gv ON tg.garment_variant_id = gv.id
                WHERE tg.ticket_id = ?
            """, (self.ticket_numbers[index],))

            self.get_current_garment_list().clear()
            for row in cursor.fetchall():
                ticket_garment_id, garment_name, quantity, price = row
                row_position = self.get_current_garment_list().rowCount()
                self.get_current_garment_list().insertRow(row_position)

                colors, patterns, textures, upcharges = self.get_garment_details(ticket_garment_id)
                quantity_item = QTableWidgetItem(str(quantity))
                variant_item = QTableWidgetItem(garment_name)
                colors_item = QTableWidgetItem(colors)
                patterns_item = QTableWidgetItem(patterns)
                textures_item = QTableWidgetItem(textures)
                upcharges_item = QTableWidgetItem(upcharges)
                price_item = QTableWidgetItem(f"${price:.2f}")

                self.get_current_garment_list().setItem(row_position, 0, quantity_item)
                self.get_current_garment_list().setItem(row_position, 1, variant_item)
                self.get_current_garment_list().setItem(row_position, 2, colors_item)
                self.get_current_garment_list().setItem(row_position, 3, patterns_item)
                self.get_current_garment_list().setItem(row_position, 4, textures_item)
                self.get_current_garment_list().setItem(row_position, 5, upcharges_item)
                self.get_current_garment_list().setItem(row_position, 6, price_item)

    def create_ticket(self):
        current_index = self.ui.tctabs.currentIndex()
        if not self.items_per_tab[current_index]:
            QMessageBox.warning(self, "Error", "No garments have been added to this ticket.")
            return

        ticket_number = self.ticket_numbers[current_index]
        if not ticket_number:
            ticket_number = self.create_new_ticket()

        self.save_garments_to_ticket(self.ticket_numbers[current_index], current_index)
        self.update_totals()
        

        self.ticket_completed.emit(self.customer_id)
        QMessageBox.information(self, "Success", "Ticket created successfully.")
        self.close()

    def create_new_ticket(self):
        next_ticket_number = get_next_ticket_number()

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            total_price = sum(quantity * price for _, _, quantity, price in self.items_per_tab[self.ui.tctabs.currentIndex()])

            try:
                cursor.execute("""
                    INSERT INTO Tickets (customer_id, ticket_number, ticket_type_id, employee_id, date_created, total_price, pieces, date_due)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.customer_id,
                    next_ticket_number,
                    self.ticket_type_id1,
                    self.employee_id,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    total_price,
                    self.pieces1,
                    self.due_date1,
                ))

                conn.commit()

                cursor.execute("SELECT last_insert_rowid()")
                new_ticket_id = cursor.fetchone()[0]

                self.ticket_numbers[self.ui.tctabs.currentIndex()] = new_ticket_id

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create ticket: {e}")

        return next_ticket_number

    def save_garments_to_ticket(self, ticket_id, current_index):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            for ticket_garment_id, garment_variant_id, quantity, price in self.items_per_tab[current_index]:
                cursor.execute("""
                    UPDATE TicketGarments
                    SET quantity = ?, price = ?
                    WHERE id = ?
                """, (quantity, price, ticket_garment_id))

            total_price = sum(item[3] for item in self.items_per_tab[current_index])
            cursor.execute("""
                UPDATE Tickets
                SET total_price = ?
                WHERE id = ?
            """, (total_price, ticket_id))

            conn.commit()

    def select_garment(self, item):
        garment_id = item.data(Qt.UserRole)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, COALESCE(price, 0) as price
                FROM GarmentVariants
                WHERE garment_id = ?
            """, (garment_id,))
            variants = cursor.fetchall()

        self.combobox_selection_in_progress = True
        self.ui.garmentvariantsbox.clear()
        self.ui.garmentvariantsbox.addItem("Select Garment Variant", -1)
        for variant_id, variant_name, price in variants:
            self.ui.garmentvariantsbox.addItem(f"{variant_name} - ${price:.2f}", variant_id)

        self.ui.garmentvariantsbox.setCurrentIndex(0)
        self.ui.garmentvariantsbox.setVisible(True)
        self.ui.garmentvariantsbox.setEnabled(True)
        self.combobox_selection_in_progress = False

        self.selected_garment_item = item

    def add_variant_to_ticket(self, index):
        if self.combobox_selection_in_progress or index == 0:
            return

        quantity = self.ui.piecesdisplay.intValue()

        if quantity < 1:
            QMessageBox.warning(self, "Invalid Quantity", "Please select at least 1 piece before adding a garment variant.")
            return

        try:
            garment_variant_id = self.ui.garmentvariantsbox.currentData()
            quantity = self.ui.piecesdisplay.intValue()
            price = self.calculate_garment_variant_price(garment_variant_id)

            current_index = self.ui.tctabs.currentIndex()
            ticket_number = self.ticket_numbers[current_index]

            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO TicketGarments (ticket_id, garment_variant_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                """, (ticket_number, garment_variant_id, quantity, price))
                ticket_garment_id = cursor.lastrowid

                conn.commit()

            row_position = self.get_current_garment_list().rowCount()
            self.get_current_garment_list().insertRow(row_position)

            quantity_item = QTableWidgetItem(str(quantity))
            variant_item = QTableWidgetItem(self.ui.garmentvariantsbox.currentText())
            colors_item = QTableWidgetItem("")
            patterns_item = QTableWidgetItem("")
            textures_item = QTableWidgetItem("")
            upcharges_item = QTableWidgetItem("")
            price_item = QTableWidgetItem(f"${price:.2f}")

            self.get_current_garment_list().setItem(row_position, 0, quantity_item)
            self.get_current_garment_list().setItem(row_position, 1, variant_item)
            self.get_current_garment_list().setItem(row_position, 2, colors_item)
            self.get_current_garment_list().setItem(row_position, 3, patterns_item)
            self.get_current_garment_list().setItem(row_position, 4, textures_item)
            self.get_current_garment_list().setItem(row_position, 5, upcharges_item)
            self.get_current_garment_list().setItem(row_position, 6, price_item)

            self.items_per_tab[current_index].append((ticket_garment_id, garment_variant_id, quantity, price))
            self.get_current_garment_list().selectRow(row_position)
            self.selected_variant_row = row_position

            self.update_totals()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {e}")
            self.update_totals()

    def calculate_garment_variant_price(self, garment_variant_id):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COALESCE(price, 0) FROM GarmentVariants WHERE id = ?", (garment_variant_id,))
            result = cursor.fetchone()

        return result[0] if result else 0

    def complete_ticket(self):
        self.update_totals()
        self.save_garments_to_ticket(self.ticket_numbers[self.ui.tctabs.currentIndex()], self.ui.tctabs.currentIndex())

        self.refresh_garment_list()

        self.ticket_completed.emit(self.customer_id)
        QMessageBox.information(self, "Success", "Ticket saved successfully.")
        self.close()

    def select_garment_variant(self, item):
        self.selected_variant_row = item.row()

    def add_option_to_garment(self, item, option_type):
        if self.selected_variant_row is None:
            QMessageBox.warning(self, "Error", "Please select a garment variant first.")
            return

        option_id = item.data(Qt.UserRole)
        current_index = self.ui.tctabs.currentIndex()
        ticket_garment_id = self.items_per_tab[current_index][self.selected_variant_row][0]

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            if option_type == 'colors':
                cursor.execute("""
                    INSERT INTO garment_colors (ticket_garment_id, color_id)
                    VALUES (?, ?)
                """, (ticket_garment_id, option_id))
            elif option_type == 'patterns':
                cursor.execute("""
                    INSERT INTO garment_patterns (ticket_garment_id, pattern_id)
                    VALUES (?, ?)
                """, (ticket_garment_id, option_id))
            elif option_type == 'textures':
                cursor.execute("""
                    INSERT INTO garment_textures (ticket_garment_id, texture_id)
                    VALUES (?, ?)
                """, (ticket_garment_id, option_id))
            elif option_type == 'upcharges':
                cursor.execute("""
                    INSERT INTO garment_upcharges (ticket_garment_id, upcharge_id)
                    VALUES (?, ?)
                """, (ticket_garment_id, option_id))

            conn.commit()

        colors, patterns, textures, upcharges = self.get_garment_details(ticket_garment_id)
        self.get_current_garment_list().item(self.selected_variant_row, 2).setText(colors)
        self.get_current_garment_list().item(self.selected_variant_row, 3).setText(patterns)
        self.get_current_garment_list().item(self.selected_variant_row, 4).setText(textures)
        self.get_current_garment_list().item(self.selected_variant_row, 5).setText(upcharges)

        self.update_totals()

    def add_selected_options_to_garment(self):
        if self.selected_variant_row is None:
            QMessageBox.warning(self, "Error", "Please select a garment variant first.")
            return

        for option_list in [self.ui.clist, self.ui.plist, self.ui.tlist, self.ui.ulist]:
            for i in range(option_list.count()):
                item = option_list.item(i)
                if item.isSelected():
                    option_type = self.get_option_type(option_list)
                    self.add_option_to_garment(item, option_type)
                    item.setSelected(False)

        self.update_totals()
        

    def get_option_type(self, option_list):
        if option_list == self.ui.clist:
            return 'colors'
        elif option_list == self.ui.plist:
            return 'patterns'
        elif option_list == self.ui.tlist:
            return 'textures'
        elif option_list == self.ui.ulist:
            return 'upcharges'
        return None

    def get_garment_details(self, ticket_garment_id):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT c.name
                FROM garment_colors gc
                JOIN Colors c ON gc.color_id = c.id
                WHERE gc.ticket_garment_id = ?
            """, (ticket_garment_id,))
            colors = ", ".join(row[0] for row in cursor.fetchall())

            cursor.execute("""
                SELECT p.name
                FROM garment_patterns gp
                JOIN Patterns p ON gp.pattern_id = p.id
                WHERE gp.ticket_garment_id = ?
            """, (ticket_garment_id,))
            patterns = ", ".join(row[0] for row in cursor.fetchall())

            cursor.execute("""
                SELECT t.name
                FROM garment_textures gt
                JOIN Textures t ON gt.texture_id = t.id
                WHERE gt.ticket_garment_id = ?
            """, (ticket_garment_id,))
            textures = ", ".join(row[0] for row in cursor.fetchall())

            cursor.execute("""
                SELECT u.name
                FROM garment_upcharges gu
                JOIN Upcharges u ON gu.upcharge_id = u.id
                WHERE gu.ticket_garment_id = ?
            """, (ticket_garment_id,))
            upcharges = ", ".join(row[0] for row in cursor.fetchall())

        return colors, patterns, textures, upcharges

    def get_current_garment_list(self):
        current_index = self.ui.tctabs.currentIndex()
        if current_index == 0:
            return self.ui.sglist
        elif current_index == 1:
            return self.ui.sglist_2
        elif current_index == 2:
            return self.ui.sglist_3
        return None

    def clear_widgets(self):
        
        current_index = self.ui.tctabs.currentIndex()
        if current_index == 0:
            self.ui.glist.clear()
            self.ui.clist.clear()
            self.ui.plist.clear()
            self.ui.tlist.clear()
            self.ui.ulist.clear()
            self.ui.sglist.clear()
        elif current_index == 1:
            self.ui.glist.clear()
            self.ui.clist.clear()
            self.ui.plist.clear()
            self.ui.tlist.clear()
            self.ui.ulist.clear()
            self.ui.sglist_2.clear()
        elif current_index == 2:
            self.ui.glist.clear()
            self.ui.clist.clear()
            self.ui.plist.clear()
            self.ui.tlist.clear()
            self.ui.ulist.clear()
            self.ui.sglist_3.clear()

