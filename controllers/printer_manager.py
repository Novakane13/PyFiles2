import sqlite3
from escpos.printer import Usb
#from views.utils.escpos_utils import format_receipt_header, format_receipt_items, format_receipt_totals
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
        SELECT q.id, c.first_name, c.last_name, c.phone_number, 
            q.due_date1, q.due_time1, q.due_date2, q.due_time2, q.due_date3, q.due_time3,
            q.date_created, e.display_name, 
            q.ticket_type_id1, q.pieces1, q.ticket_type_id2, q.pieces2, q.ticket_type_id3, q.pieces3
        FROM quick_tickets q
        JOIN customers c ON q.customer_id = c.id
        JOIN employees e ON q.employee_id = e.employee_id
        WHERE q.id = ?
        """

        cursor.execute(query, (ticket_id,))
        result = cursor.fetchone()
        
        print("Database result:", result)  # Debugging output

        if not result:
            print(f"No quick ticket found for ID {ticket_id}")
            conn.close()
            return None

        conn.close()

        # Correctly format the dictionary with the expected keys
        return {
            "ticket_number": result[0],
            "customer_name": f"{result[1]} {result[2]}",  # Concatenating first_name and last_name
            "phone": result[3],
            "due_date": result[4] or "N/A",   # Defaulting to the first due_date
            "due_time": result[5] or "N/A",   # Defaulting to the first due_time
            "due_date1": result[4] or "N/A",
            "due_time1": result[5] or "N/A",
            "due_date2": result[6] or "N/A",
            "due_time2": result[7] or "N/A",
            "due_date3": result[8] or "N/A",
            "due_time3": result[9] or "N/A",
            "drop_date": result[10] or "N/A",  # Renamed from `date_created`
            "employee": result[11] or "N/A",
            "ticket_type1": self.get_ticket_type_name(result[12]),
            "pieces1": result[13] if result[13] else 0,
            "ticket_type2": self.get_ticket_type_name(result[14]),
            "pieces2": result[15] if result[15] else 0,
            "ticket_type3": self.get_ticket_type_name(result[16]),
            "pieces3": result[17] if result[17] else 0,
        }



    def fetch_detailed_ticket_data(self, ticket_id):
        """Fetch detailed ticket information from the database, including garments, quantities, and prices."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
        SELECT 
            t.ticket_number, c.first_name || ' ' || c.last_name AS customer_name, c.phone_number, 
            t.date_due, t.date_created, e.display_name, 
            t.ticket_type_id, t.total_price, t.payment, t.paid
        FROM tickets t
        JOIN customers c ON t.customer_id = c.id
        JOIN employees e ON t.employee_id = e.employee_id
        WHERE t.id = ?
        """
        cursor.execute(query, (ticket_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            print(f"No detailed ticket found for ID {ticket_id}")
            return None

        # Fetch garment variants linked to this ticket
        cursor.execute("""
            SELECT gv.name, tg.quantity, tg.price
            FROM TicketGarments tg
            JOIN GarmentVariants gv ON tg.garment_variant_id = gv.id
            WHERE tg.ticket_id = ?
        """, (ticket_id,))
        garments = [{"name": row[0], "pcs": row[1], "total": row[2]} for row in cursor.fetchall()]

        conn.close()

        return {
            "ticket_number": result[0],
            "customer_name": result[1],
            "phone": result[2],
            "due_date": result[3] or "N/A",
            "drop_date": result[4] or "N/A",
            "employee": result[5] or "N/A",
            "ticket_prefix": self.get_ticket_type_letter(result[6]),  # First letter of ticket type
            "total": result[7],
            "discount": 0,  # Adjust if needed
            "env_fee": 0,    # Adjust if needed
            "tax": 0,        # Adjust if needed
            "grand_total": result[7],  # Assuming total is correct
            "paid": result[9],
            "garments": garments
        }

    def fetch_receipt_data(self, receipt_id):
        """Fetch receipt data from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
        SELECT 
            r.id, c.first_name || ' ' || c.last_name AS customer_name, c.phone_number, 
            r.date, e.display_name, r.total, r.tax, r.total, r.paid
        FROM billing_statements r
        JOIN customers c ON r.customer_id = c.id
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.id = ?
        """
        cursor.execute(query, (receipt_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        # Fetch items linked to this receipt
        cursor.execute("""
            SELECT g.name, ri.qty, ri.price
            FROM receipt_items ri
            JOIN Garments g ON ri.item_id = g.id
            WHERE ri.receipt_id = ?
        """, (receipt_id,))
        items = [{"name": row[0], "qty": row[1], "price": row[2]} for row in cursor.fetchall()]

        conn.close()

        return {
            "receipt_number": result[0],
            "customer_name": result[1],
            "phone": result[2],
            "date": result[3],
            "employee": result[4],
            "subtotal": result[5] - result[6],  # Assuming tax is separate
            "tax": result[6],
            "total": result[7],
            "paid": result[8],
            "items": items
        }

    def get_ticket_type_name(self, ticket_type_id):
        """Fetches the ticket type name from the database."""
        if ticket_type_id is None:
            return "N/A"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM TicketTypes WHERE id = ?", (ticket_type_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Unknown"

    def get_ticket_type_letter(self, ticket_type_id):
        """Fetch the ticket type's first letter from the database."""
        if ticket_type_id is None:
            return "D"  # Default for 'Detailed'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM TicketTypes WHERE id = ?", (ticket_type_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0][0] if result else "D"

    def print_quick_ticket(self, ticket_data):
        try:
            self.printer.set(align='center', bold=True)

            
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

            else:
                print(f"Could not print logo: File not found at {logo_path}")

            
            
            self.printer.text("3655 W Anthem Way\n")
            self.printer.text("Anthem, AZ 85086\n")
            self.printer.text("623-233-6658\n")
            self.printer.text("-" * 32 + "\n")

            
            self.printer._raw(b'\x1b!\x30') 
            self.printer.set(align='left')
            self.printer.text(f"{ticket_data['customer_name']}\n")
            self.printer.text(f"{ticket_data['phone']}\n")
            self.printer._raw(b'\x1b!\x00')  
            self.printer.text("-" * 32 + "\n")

            
            self.printer.set(align='left', bold=False)
            self.printer.text(f"Due  : {ticket_data['due_date']}\n")
            self.printer.text(f"Drop : {ticket_data['drop_date']}\n")
            self.printer.text(f"Emp  : {ticket_data['employee']}\n")
            self.printer.text("-" * 32 + "\n")

            self.printer.set(align='center', bold=True)
            ticket_number = f"Q{ticket_data['ticket_number']}"
            self.printer.barcode(ticket_number, "CODE39", width=2, height=100)

           
            self.printer._raw(b'\x1b!\x30')  
            self.printer.text(f"{ticket_number}\n")
            self.printer._raw(b'\x1b!\x00')  
            self.printer.text("-" * 32 + "\n")


            
            self.printer.text("-" * 32 + "\n")
            self.printer._raw(b'\x1b!\x30')  
            self.printer.set(align='right')  
            self.printer.text(f"{'Pcs.'.rjust(10)}\n")  

            for i in range(1, 4):
                ticket_type = ticket_data.get(f'ticket_type{i}', None)
                pieces = ticket_data.get(f'pieces{i}', 0)
                if ticket_type:
                    formatted_row = f"{ticket_type.ljust(20)}{str(pieces).rjust(10)}\n"  
                    self.printer.text(formatted_row)

            self.printer._raw(b'\x1b!\x00') 
            self.printer.text("-" * 32 + "\n")

            # **Footer**
            self.printer.set(align='center', bold=True)
            self.printer.text("Quick Tickets are payable upon pickup\n")
            self.printer.cut()

        except Exception as e:
            print(f"Error printing quick ticket: {e}")

    def print_detailed_ticket(self, ticket_id):
        try:
            self.printer.set(align='center', bold=True)

            
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

            else:
                print(f"Could not print logo: File not found at {logo_path}")
        
            ticket_data = self.fetch_detailed_ticket_data(ticket_id)
            if not ticket_data:
                print(f"No detailed ticket found for ID {ticket_id}")
                return

           

            
            self.printer.text("\n3655 W Anthem Way\n")
            self.printer.text("Anthem, AZ 85086\n")
            self.printer.text("623-233-6658\n")
            self.printer.text("-" * 32 + "\n")

            # Customer Info
            self.printer.set(align='left', bold=True, height=2, width=2)
            self.printer.text(f"{ticket_data['customer_name']}\n")
            self.printer.text(f"{ticket_data['phone']}\n")
            self.printer.text("-" * 32 + "\n")

                # Due & Drop Dates
            self.printer.set(align='left', bold=False)
            self.printer.text(f"Due  : {ticket_data['due_date']}\n")
            self.printer.text(f"Drop : {ticket_data['drop_date']}\n")
            self.printer.text(f"Emp  : {ticket_data['employee']}\n")
            self.printer.text("-" * 32 + "\n")

                # Corrected Ticket Number
            self.printer.set(align='center', bold=True, height=3, width=3)
            ticket_number = f"{ticket_data['ticket_prefix']}{ticket_data['ticket_number']}"
            self.printer.barcode(ticket_number, "CODE39", width=3, height=120)
            self.printer.text(f"{ticket_number}\n")
            self.printer.text("-" * 32 + "\n")

                # Garments (Now Corrected)
            self.printer.set(align='left', bold=True, height=2, width=2)
            self.printer.text("Garment                 Pcs.    Total\n")
            for garment in ticket_data["garments"]:
                self.printer.text(f"{garment['name'][:18]:<18} {garment['pcs']:>5}  ${garment['total']:>6.2f}\n")

            self.printer.text("-" * 32 + "\n")

                # Totals
            self.printer.text(f"Total: ${ticket_data['total']:.2f}\n")
            self.printer.text(f"Discount: ${ticket_data['discount']:.2f}\n")
            self.printer.text(f"Env. Fee: ${ticket_data['env_fee']:.2f}\n")
            self.printer.text(f"Tax: ${ticket_data['tax']:.2f}\n")
            self.printer.text(f"Grand Total: ${ticket_data['grand_total']:.2f}\n")
            self.printer.text(f"Paid: ${ticket_data['paid']:.2f}\n")
            self.printer.text("-" * 32 + "\n")

            self.printer.set(align='center', bold=True)
            self.printer.text("Thank you for your business!\n")
            self.printer.cut()

        except Exception as e:    
            print(f"Error printing detailed ticket: {e}")

    def print_receipt(self, receipt_data):
       
        try:
            self.printer.set(align='center', bold=True)
           
            self.printer.text("Ogdens Cleaners\n")
            self.printer.text("3655 W Anthem Way\n")
            self.printer.text("Anthem, AZ 85086\n")
            self.printer.text("623-233-6658\n")
            self.printer.text("-" * 32 + "\n")

            
            self.printer.set(align='left', bold=False)
            self.printer.text(f"Customer: {receipt_data['customer_name']}\n")
            self.printer.text(f"Phone: {receipt_data['phone']}\n")
            self.printer.text(f"Date: {receipt_data['date']}\n")
            self.printer.text(f"Emp: {receipt_data['employee']}\n")
            self.printer.text("-" * 32 + "\n")

            
            self.printer.text("Item                 Qty   Price\n")
            for item in receipt_data["items"]:
                self.printer.text(f"{item['name'][:18]:<18} {item['qty']:>3}  ${item['price']:<6.2f}\n")

            self.printer.text("-" * 32 + "\n")

           
            self.printer.text(f"Subtotal: ${receipt_data['subtotal']:.2f}\n")
            self.printer.text(f"Tax: ${receipt_data['tax']:.2f}\n")
            self.printer.text(f"Total: ${receipt_data['total']:.2f}\n")
            self.printer.text(f"Paid: ${receipt_data['paid']:.2f}\n")
            self.printer.text("-" * 32 + "\n")

            
            self.printer.text("Thank you for your business!\n")
            self.printer.cut()
        except Exception as e:
            print(f"Error printing receipt: {e}")

    def disconnect(self):
        
        if self.printer:
            self.printer.close()
            print("Printer disconnected.")

    def open_cash_drawer(self):
       
        if not self.printer:
            print("Printer is not connected.")
            return
        try:
            self.printer.cashdraw(2)  
            print("Cash drawer opened.")
        except Exception as e:
            print(f"Error opening cash drawer: {e}")

if __name__ == "__main__":
    db_path = r"C:\Users\novak\OneDrive\Desktop\QTDesigner\PyFiles2\models\pos_system.db"
    printer = ReceiptPrinter(vendor_id=0x0525, product_id=0xA700, db_path=db_path)
    printer.connect()

    detailed_ticket_id = 74  
    printer.print_detailed_ticket(detailed_ticket_id)

    printer.disconnect()