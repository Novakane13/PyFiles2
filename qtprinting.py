import sqlite3
from escpos.printer import Usb
import os
from PIL import Image

class ReceiptPrinter:
    def __init__(self, vendor_id, product_id, db_path):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.db_path = db_path
        self.printer = None

    def connect(self):
        try:
            self.printer = Usb(self.vendor_id, self.product_id)
            self.printer.profile.profile_data['media']['width']['pixel'] = 576  
            print("Printer connected successfully.")
        except Exception as e:
            print(f"Failed to connect to printer: {e}")

    def fetch_quick_ticket_data(self, ticket_id):
        """Fetches quick ticket details from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
        SELECT q.id, c.name, c.phone, q.due_date, q.drop_date, e.name, 
               q.ticket_type_id1, q.pieces1, q.ticket_type_id2, q.pieces2, q.ticket_type_id3, q.pieces3
        FROM quick_tickets q
        JOIN customers c ON q.customer_id = c.id
        JOIN employees e ON q.employee_id = e.id
        WHERE q.id = ?
        """
        cursor.execute(query, (ticket_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "ticket_number": result[0],
                "customer_name": result[1],
                "phone": result[2],
                "due_date": result[3],
                "drop_date": result[4],
                "employee": result[5],
                "ticket_type1": self.get_ticket_type_name(result[6]),
                "pieces1": result[7] or 0,
                "ticket_type2": self.get_ticket_type_name(result[8]),
                "pieces2": result[9] or 0,
                "ticket_type3": self.get_ticket_type_name(result[10]),
                "pieces3": result[11] or 0,
            }
        return None

    def get_ticket_type_name(self, ticket_type_id):
        """Fetches the ticket type name from the database."""
        if ticket_type_id is None:
            return None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM TicketTypes WHERE id = ?", (ticket_type_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def print_quick_ticket(self, ticket_id):
        """Fetch and print quick ticket details."""
        ticket_data = self.fetch_quick_ticket_data(ticket_id)
        if not ticket_data:
            print(f"No ticket found for ID {ticket_id}")
            return

        try:
            self.printer.set(align='center', bold=True)

            # Print Logo
            logo_path = r"C:\Users\novak\OneDrive\Desktop\QTDesigner\PyFiles2\controllers\logo.png"
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.convert("L")
                new_width = 400  
                aspect_ratio = img.height / img.width
                new_height = int(new_width * aspect_ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                resized_logo_path = r"C:\Users\novak\OneDrive\Desktop\QTDesigner\PyFiles2\controllers\resized_logo.png"
                img.save(resized_logo_path)
                self.printer.image(resized_logo_path)

            # Print Header
            self.printer.text("\nOgdens Cleaners\n")
            self.printer.text("3655 W Anthem Way\n")
            self.printer.text("Anthem, AZ 85086\n")
            self.printer.text("623-233-6658\n")
            self.printer.text("-" * 32 + "\n")

            # Customer Info
            self.printer._raw(b'\x1b!\x30')  
            self.printer.set(align='left')
            self.printer.text(f"{ticket_data['customer_name']}\n")
            self.printer.text(f"{ticket_data['phone']}\n")
            self.printer._raw(b'\x1b!\x00')  
            self.printer.text("-" * 32 + "\n")

            # Due & Drop Dates
            self.printer.set(align='left', bold=False)
            self.printer.text(f"Due  : {ticket_data['due_date']}\n")
            self.printer.text(f"Drop : {ticket_data['drop_date']}\n")
            self.printer.text(f"Emp  : {ticket_data['employee']}\n")
            self.printer.text("-" * 32 + "\n")

            # Barcode
            self.printer.set(align='center', bold=True)
            ticket_number = f"Q{ticket_data['ticket_number']}"
            self.printer.barcode(ticket_number, "CODE39", width=2, height=100)
            self.printer.text("-" * 32 + "\n")

            # Ticket Type & Pieces
            self.printer._raw(b'\x1b!\x30')  
            self.printer.text(f"{'Ticket Type'.center(20)} {'Pcs.'.rjust(10)}\n")  

            for i in range(1, 4):
                ticket_type = ticket_data.get(f'ticket_type{i}', None)
                pieces = ticket_data.get(f'pieces{i}', 0)
                if ticket_type:
                    formatted_row = f"{ticket_type.center(20)} {str(pieces).rjust(10)}\n"
                    self.printer.text(formatted_row)

            self.printer._raw(b'\x1b!\x00')  
            self.printer.text("-" * 32 + "\n")

            # Footer
            self.printer.set(align='center', bold=True)
            self.printer.text("Quick Tickets are payable upon pickup\n")
            self.printer.cut()

        except Exception as e:
            print(f"Error printing quick ticket: {e}")

    def disconnect(self):
        """Disconnect the printer."""
        if self.printer:
            self.printer.close()
            print("Printer disconnected.")

# Usage Example:
if __name__ == "__main__":
    db_path = r"C:\Users\novak\OneDrive\Desktop\QTDesigner\PyFiles2\models\pos_system.db"
    printer = ReceiptPrinter(vendor_id=0x0525, product_id=0xA700, db_path=db_path)
    printer.connect()

    quick_ticket_id = 1  # Change this to a valid ticket ID from your DB
    printer.print_quick_ticket(quick_ticket_id)
    printer.disconnect()