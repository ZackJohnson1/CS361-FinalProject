# Danny Caspary
# CS361: Microservice A -- SKU alert
# Fall 2024
# Using ZeroMQ API, code adapted from example in "Introduction to ZeroMQ"
#     by Luis Flores

import zmq
import json
import os

inventory_file = 'inventory.json'

def load_inventory():
    if os.path.exists(inventory_file):
        with open(inventory_file, 'r') as f:
            return json.load(f)
    return []

def generate_report():
    inventory = load_inventory()
    if not inventory:
        return "Inventory is empty. No data to report."
    report_lines = ["Inventory Report:"]
    for item in inventory:
        name = item.get('name', 'Unknown')
        sku = item.get('sku', 'Unknown')
        quantity = item.get('quantity', 0)
        low_stock_threshold = item.get('low_stock_threshold', 0)
        status = "Low Stock" if quantity < low_stock_threshold else "Sufficient Stock"
        report_lines.append(f"- {name} (SKU: {sku}): {quantity} in stock ({status})")
    return "\n".join(report_lines)

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

while True:
    data = socket.recv_json()
    if isinstance(data, list) and data[0] == "generate_report":
        report = generate_report()  # Generate the report dynamically
        socket.send_string(report)
    elif len(data) >= 2:  # SKU alert
        sku, quantity = data
        alert = f"Item {sku} low in stock! Only {quantity} remaining."
        socket.send_string(alert)
    elif data == "Q":  # Quit signal
        socket.send_string("evaluation complete")
        print("message received")
        break

context.destroy()