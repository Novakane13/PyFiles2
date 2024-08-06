import re
import sys
import sqlite3
import os
from datetime import datetime
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QTreeWidgetItem, QVBoxLayout, QComboBox, QPushButton, QApplication, QMessageBox, QTableWidgetItem, QAbstractItemView 
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, Signal, QDate
from views.Test import Ui_DetailedTicketCreation

# Assuming Ui_DetailedTicketCreation is imported from the appropriate file
# from ui_detailedticketcreation import Ui_DetailedTicketCreation

class DetailedTicketWindow(QMainWindow):
    ticket_completed = Signal(int)  # Signal to indicate ticket completion with customer_id as an argument

    def __init__(self, customer_id=None, ticket_type_id=None, employee_id=None, ticket_number=None, pieces=None, due_date=None, notes=None, all_notes=None, quick_ticket_data=None):
        super().__init__()
        self.ui = Ui_DetailedTicketCreation()
        self.ui.setupUi(self)

        self.customer_id = customer_id
        self.quick_ticket_data = quick_ticket_data  # Store the quick ticket data
        self.employee_id = employee_id  # Store the logged-in employee ID
        self.ticket_type_id = ticket_type_id
        self.pieces = pieces
        self.due_date = due_date
        self.notes = notes
        self.all_notes = all_notes
        self.ticket_numbers = [None] * 3  # Store ticket numbers for each tab
        self.items_per_tab = [[] for _ in range(3)]  # Store items for each tab

        self.ui.canceltbutton.clicked.connect(self.close)  # Close functionality
        self.ui.ctbutton.clicked.connect(self.create_ticket)  # Create ticket functionality

        self.ui.tctabs.currentChanged.connect(self.on_tab_change)  # Handle tab changes

        self.populate_widgets()
        self.setup_table_headers()

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
        self.ui.piecesdisplay.display(0)  # Initialize the display to 0

        self.combobox_selection_in_progress = False  # Add this flag to track combobox selection

        # Connect item click events for all tab lists
        self.ui.sglist.itemClicked.connect(self.select_garment_variant)
        self.ui.sglist_2.itemClicked.connect(self.select_garment_variant)
        self.ui.sglist_3.itemClicked.connect(self.select_garment_variant)

        self.selected_variant_row = None

        self.delivery_fee = 0  # Example fixed delivery fee, you can make this dynamic

        self.update_totals()

        # If quick ticket data is provided, load it into the detailed ticket window
        if self.quick_ticket_data:
            self.load_quick_ticket_data()

    def setup_table_headers(self):
        headers = ["Counted Pieces", "Garment Variant", "Colors", "Patterns", "Textures", "Upcharges", "Price"]
        for table in [self.ui.sglist, self.ui.sglist_2, self.ui.sglist_3]:
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setDragDropMode(QAbstractItemView.InternalMove)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.SingleSelection)

    def increment_pieces(self):
        current_value = self.ui.piecesdisplay.intValue()
        self.ui.piecesdisplay.display(current_value + 1)

    def decrement_pieces(self):
        current_value = self.ui.piecesdisplay.intValue()
        if current_value > 0:
            self.ui.piecesdisplay.display(current_value - 1)

    def on_tab_change(self, index):
        # When the tab changes, load the data for the current ticket tab
        self.load_ticket_data(index)
        # Refresh garment list whenever tab changes to reflect the latest data
        self.refresh_garment_list()

    def refresh_garment_list(self):
        # Establish a connection to the database
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Clear the existing items in the list widget
        self.ui.glist.clear()

        # Execute the query and fetch results, filtering by ticket_type_id
        cursor.execute("""
            SELECT g.id, g.name, g.image_path, v.id, v.name, COALESCE(v.price, 0) as price
            FROM Garments g
            LEFT JOIN GarmentVariants v ON g.id = v.garment_id
            JOIN ticket_type_garments ttg ON ttg.garments_id = g.id
            WHERE v.garment_id IS NOT NULL AND ttg.ticket_type_id = ?
        """, (self.ticket_type_id,))

        garments = {}
        for row in cursor.fetchall():
            garment_id, garment_name, garment_image, variant_id, variant_name, price = row
            print(f"Fetched Garment: {garment_name}, Variant: {variant_name}, Price: {price}")

            # Check for garment presence and construct the dictionary
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
                garment_item = QListWidgetItem(QIcon(garment_info['image']), f"{garment_info['name']}")
                garment_item.setData(Qt.UserRole, garment_id)
                self.ui.glist.addItem(garment_item)
            except Exception as e:
                print(f"Error loading garment {garment_info['name']}: {e}")

        # Close the database connection
        conn.close()

    def populate_widgets(self):
        # Call refresh_garment_list to populate garments
        self.refresh_garment_list()

        # Establish a connection to the database for other widgets
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Populate colors associated with the ticket type
        cursor.execute("""
            SELECT c.id, c.name
            FROM Colors c
            JOIN ticket_type_colors ttc ON ttc.colors_id = c.id
            WHERE ttc.ticket_type_id = ?
        """, (self.ticket_type_id,))
        colors = cursor.fetchall()
        for color in colors:
            item = QListWidgetItem(color[1])
            item.setData(Qt.UserRole, color[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.clist.addItem(item)

        # Populate patterns associated with the ticket type
        cursor.execute("""
            SELECT p.id, p.name
            FROM Patterns p
            JOIN ticket_type_patterns ttp ON ttp.patterns_id = p.id
            WHERE ttp.ticket_type_id = ?
        """, (self.ticket_type_id,))
        patterns = cursor.fetchall()
        for pattern in patterns:
            item = QListWidgetItem(pattern[1])
            item.setData(Qt.UserRole, pattern[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.plist.addItem(item)

        # Populate textures associated with the ticket type
        cursor.execute("""
            SELECT t.id, t.name
            FROM Textures t
            JOIN ticket_type_textures ttt ON ttt.textures_id = t.id
            WHERE ttt.ticket_type_id = ?
        """, (self.ticket_type_id,))
        textures = cursor.fetchall()
        for texture in textures:
            item = QListWidgetItem(texture[1])
            item.setData(Qt.UserRole, texture[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.tlist.addItem(item)

        # Populate upcharges associated with the ticket type
        cursor.execute("""
            SELECT u.id, u.description, u.price
            FROM Upcharges u
            JOIN ticket_type_upcharges ttu ON ttu.upcharges_id = u.id
            WHERE ttu.ticket_type_id = ?
        """, (self.ticket_type_id,))
        upcharges = cursor.fetchall()
        for upcharge in upcharges:
            item = QListWidgetItem(f"{upcharge[1]} - ${upcharge[2]:.2f}")
            item.setData(Qt.UserRole, upcharge[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.ulist.addItem(item)

        # Close the database connection
        conn.close()

    def load_ticket_data(self, index):
        # Load the ticket data for the given tab index
        if not self.ticket_numbers[index]:
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
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

        conn.close()

    def create_ticket(self):
        """
        Create a new ticket with all garments and details.
        """
        # Check if there are items to save
        current_index = self.ui.tctabs.currentIndex()
        if not self.items_per_tab[current_index]:
            QMessageBox.warning(self, "Error", "No garments have been added to this ticket.")
            return

        # Initialize the ticket in the database if not already done
        ticket_number = self.ticket_numbers[current_index]
        if not ticket_number:
            ticket_number = self.create_new_ticket()

        # Save all items for the current tab
        self.save_garments_to_ticket(self.ticket_numbers[current_index], current_index)

        # Update totals
        self.update_totals()

        # Refresh garment list after creating a ticket
        self.refresh_garment_list()

        # Signal completion
        self.ticket_completed.emit(self.customer_id)  # Emit the customer ID
        QMessageBox.information(self, "Success", "Ticket created successfully.")
        self.close()

    def create_new_ticket(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(ticket_number) FROM Tickets")
        max_ticket_number = cursor.fetchone()[0]
        next_ticket_number = max_ticket_number + 1 if max_ticket_number else 1

        # Calculate initial total price
        total_price = sum(quantity * price for _, _, quantity, price in self.items_per_tab[self.ui.tctabs.currentIndex()])

        # Debugging: Check the types and values of parameters
        print(f"Customer ID: {self.customer_id} ({type(self.customer_id)})")
        print(f"Ticket Number: {next_ticket_number} ({type(next_ticket_number)})")
        print(f"Ticket Type ID: {self.ticket_type_id} ({type(self.ticket_type_id)})")
        print(f"Employee ID: {self.employee_id} ({type(self.employee_id)})")
        print(f"Total Price: {total_price} ({type(total_price)})")

        try:
            # Insert ticket for the single customer
            cursor.execute("""
                INSERT INTO Tickets (customer_id, ticket_number, ticket_type_id, employee_id, date_created, total_price, pieces, date_due)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.customer_id,
                next_ticket_number,
                self.ticket_type_id,
                self.employee_id,  # Save the logged-in employee ID
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                total_price,  # Save calculated total price
                self.pieces,  # Save the number of pieces
                self.due_date,  # Save due date
            ))

            conn.commit()

            cursor.execute("SELECT last_insert_rowid()")
            new_ticket_id = cursor.fetchone()[0]

            self.ticket_numbers[self.ui.tctabs.currentIndex()] = new_ticket_id

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create ticket: {e}")
        finally:
            conn.close()

        return next_ticket_number

    def save_garments_to_ticket(self, ticket_id, current_index):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Save garment details to the ticket
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
        conn.close()

    def select_garment(self, item):
        garment_id = item.data(Qt.UserRole)

        # Only update the combobox, do not add to the ticket list
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, COALESCE(price, 0) as price
            FROM GarmentVariants
            WHERE garment_id = ?
        """, (garment_id,))
        variants = cursor.fetchall()
        conn.close()

        self.combobox_selection_in_progress = True  # Set the flag before updating the combobox
        self.ui.garmentvariantsbox.clear()
        self.ui.garmentvariantsbox.addItem("Select Garment Variant", -1)
        for variant_id, variant_name, price in variants:
            self.ui.garmentvariantsbox.addItem(f"{variant_name} - ${price:.2f}", variant_id)

        # Enable and show the combobox when a garment is selected
        self.ui.garmentvariantsbox.setCurrentIndex(0)
        self.ui.garmentvariantsbox.setVisible(True)
        self.ui.garmentvariantsbox.setEnabled(True)
        self.combobox_selection_in_progress = False  # Reset the flag after updating the combobox

        self.selected_garment_item = item

    def add_variant_to_ticket(self, index):
        if self.combobox_selection_in_progress:
            return  # Ignore the signal if it was triggered by updating the combobox

        if index == 0:
            return  # "Select Garment Variant" selected, do nothing

        try:
            garment_variant_id = self.ui.garmentvariantsbox.currentData()
            quantity = self.ui.piecesdisplay.intValue()  # Use the value from the LCD display
            price = self.calculate_garment_variant_price(garment_variant_id)

            current_index = self.ui.tctabs.currentIndex()
            ticket_number = self.ticket_numbers[current_index]

            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Insert into TicketGarments if not exists, otherwise update
            cursor.execute("""
                INSERT INTO TicketGarments (ticket_id, garment_variant_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (ticket_number, garment_variant_id, quantity, price))
            ticket_garment_id = cursor.lastrowid

            conn.commit()
            conn.close()

            # Add to current garment list display
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

            # Store the added item details
            self.items_per_tab[current_index].append((ticket_garment_id, garment_variant_id, quantity, price))

            # Select the newly added row
            self.get_current_garment_list().selectRow(row_position)
            self.selected_variant_row = row_position

            self.update_totals()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {e}")
            self.update_totals()

    def calculate_garment_variant_price(self, garment_variant_id):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COALESCE(price, 0) FROM GarmentVariants WHERE id = ?", (garment_variant_id,))
        result = cursor.fetchone()
        conn.close()

        if result is not None:
            return result[0]
        else:
            return 0  # Return a default price if no variant is found

    def complete_ticket(self):
        # Calculate and save the total price
        self.update_totals()
        self.save_garments_to_ticket(self.ticket_numbers[self.ui.tctabs.currentIndex()], self.ui.tctabs.currentIndex())

        # Refresh garment list after completing a ticket
        self.refresh_garment_list()

        # Signal completion
        self.ticket_completed.emit(self.customer_id)  # Emit the customer ID
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
        conn = sqlite3.connect(db_path)
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
        conn.close()

        # Update the details in the current garment list
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
                    item.setSelected(False)  # Deselect after adding

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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get colors
        cursor.execute("""
            SELECT c.name
            FROM garment_colors gc
            JOIN Colors c ON gc.color_id = c.id
            WHERE gc.ticket_garment_id = ?
        """, (ticket_garment_id,))
        colors = ", ".join(row[0] for row in cursor.fetchall())

        # Get patterns
        cursor.execute("""
            SELECT p.name
            FROM garment_patterns gp
            JOIN Patterns p ON gp.pattern_id = p.id
            WHERE gp.ticket_garment_id = ?
        """, (ticket_garment_id,))
        patterns = ", ".join(row[0] for row in cursor.fetchall())

        # Get textures
        cursor.execute("""
            SELECT t.name
            FROM garment_textures gt
            JOIN Textures t ON gt.texture_id = t.id
            WHERE gt.ticket_garment_id = ?
        """, (ticket_garment_id,))
        textures = ", ".join(row[0] for row in cursor.fetchall())

        # Get upcharges
        cursor.execute("""
            SELECT u.description
            FROM garment_upcharges gu
            JOIN Upcharges u ON gu.upcharge_id = u.id
            WHERE gu.ticket_garment_id = ?
        """, (ticket_garment_id,))
        upcharges = ", ".join(row[0] for row in cursor.fetchall())

        conn.close()
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

    def update_totals(self):
        current_index = self.ui.tctabs.currentIndex()

        initial_price = sum(quantity * price for _, _, quantity, price in self.items_per_tab[current_index])
        deductions = 0
        taxes: float = initial_price * 0.1
        delivery_fee = self.delivery_fee
        total_price = initial_price - deductions + taxes + delivery_fee

        self.ui.initial_price_label.setText(f"Initial Price: ${initial_price:.2f}")
        self.ui.total_price_label.setText(f"Total Price: ${total_price:.2f}")
        self.ui.deductions_label.setText(f"Deductions: ${deductions:.2f}")
        self.ui.taxes_label.setText(f"Taxes: ${taxes:.2f}")
        self.ui.delivery_fee_label.setText(f"Delivery Fee: ${delivery_fee:.2f}")

    def load_quick_ticket_data(self):
        """
        Load quick ticket data into the detailed ticket window.
        """
        for index, ticket in enumerate(self.quick_ticket_data.get('tickets', [])):
            self.ui.tctabs.setCurrentIndex(index)
            self.ticket_numbers[index] = ticket['ticket_number']
            self.ticket_type_id = self.get_ticket_type_id(ticket['ticket_type'])

            # Populate counted pieces
            self.ui.piecesdisplay.display(ticket['pieces'])

            # Populate due dates
            due_date_widget = getattr(self.ui, f'qtdselection_{index + 1}')
            due_date_widget.setDate(QDate.fromString(ticket['due_date'], 'yyyy-MM-dd'))

            # Set ticket type in the UI (this assumes you have a way to select ticket types in the detailed ticket UI)
            self.set_ticket_type_in_ui(index, ticket['ticket_type'])

            # Add notes
            notes_widget = getattr(self.ui, f'qtninput_{index + 1}')
            notes_widget.setPlainText(ticket['notes'])

            all_notes_widget = self.ui.atninput
            all_notes_widget.setPlainText(ticket['all_notes'])

        self.ui.tctabs.setCurrentIndex(0)

    def get_ticket_type_id(self, ticket_type_name):
        # Helper function to fetch the ticket type ID based on its name
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM TicketTypes WHERE name = ?", (ticket_type_name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        return None

    def set_ticket_type_in_ui(self, index, ticket_type_name):
        # This function should set the appropriate ticket type in the detailed UI
        # You might need to adjust this based on how your UI manages ticket types
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Assume you have customer_id and employee_id after login
    customer_id = 1
    employee_id = 1

    # Example quick ticket data for testing
    quick_ticket_data = {
        'customer_id': customer_id,
        'tickets': [
            {'ticket_number': 101, 'ticket_type': 'Wash & Fold', 'pieces': 5, 'due_date': '2024-08-15', 'notes': 'Note 1', 'all_notes': 'All notes'},
            {'ticket_number': 102, 'ticket_type': 'Dry Clean', 'pieces': 3, 'due_date': '2024-08-16', 'notes': 'Note 2', 'all_notes': 'All notes'},
            {'ticket_number': 103, 'ticket_type': 'Iron', 'pieces': 2, 'due_date': '2024-08-17', 'notes': 'Note 3', 'all_notes': 'All notes'}
        ]
    }

    window = DetailedTicketWindow(customer_id=customer_id, quick_ticket_data=quick_ticket_data, employee_id=employee_id)
    window.show()
    sys.exit(app.exec())