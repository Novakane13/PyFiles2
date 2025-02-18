import sys

class BarcodeScanner:
    def __init__(self, callback):
        """
        Initializes the scanner with a callback function to process scanned data.
        :param callback: Function to process barcode data.
        """
        self.callback = callback

    def start_scanning(self):
        """
        Starts scanning for barcodes (simulate keyboard input for now).
        Replace this with serial communication if needed.
        """
        print("Scanning started. Type barcode data and press Enter...")
        try:
            while True:
                barcode = input("Scanned: ")  # Simulate scanner input
                if barcode:
                    self.callback(barcode)
        except KeyboardInterrupt:
            print("Scanning stopped.")

# Example usage
if __name__ == "__main__":
    def process_barcode(data):
        print(f"Barcode processed: {data}")
        # Add logic to query database or update UI

    scanner = BarcodeScanner(callback=process_barcode)
    scanner.start_scanning()
