def format_receipt_header(store_name, store_address, store_phone):
    return f"{store_name}\n{store_address}\nPhone: {store_phone}\n{'-' * 32}\n"

def format_receipt_items(items):
    item_lines = ""
    for item in items:
        item_lines += f"{item['name'][:20]:<20} {item['qty']:>3} x {item['price']:<6.2f}\n"
    return item_lines

def format_receipt_totals(subtotal, tax, total):
    return (
        f"{'-' * 32}\n"
        f"Subtotal: {' ' * 20}${subtotal:.2f}\n"
        f"Tax: {' ' * 25}${tax:.2f}\n"
        f"Total: {' ' * 23}${total:.2f}\n{'-' * 32}\n"
    )
