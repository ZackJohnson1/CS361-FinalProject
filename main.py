import json
import os
import requests
import zmq


inventory_file = 'inventory.json'
history_stack = []

if not os.path.exists(inventory_file):
    with open(inventory_file, 'w') as f:
        json.dump([], f)


def load_inventory():
    with open(inventory_file, 'r') as f:
        return json.load(f)


def save_inventory(inventory):
    with open(inventory_file, 'w') as f:
        json.dump(inventory, f, indent=4)


def generate_sku(prefix=""):
    """Generates a unique SKU"""
    url = "http://localhost:5004/generateSKU"
    try:
        response = requests.post(url, json={"prefix": prefix})
        response.raise_for_status()
        data = response.json()
        return data.get("sku")
    except requests.RequestException as e:
        print(f"Error generating SKU: {e}")
        return None


def send_to_sku_alert(sku, quantity):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    try:
        socket.connect("tcp://localhost:5555")  # Ensure the port matches your microservice
        socket.send_json((sku, quantity))  # Send SKU and quantity as a tuple
        message = socket.recv()  # Receive response from microservice
        print(f"Microservice alert: {message.decode()}")  # Print the alert
    except zmq.ZMQError as e:
        print(f"Error communicating with SKU alert microservice: {e}")
    finally:
        socket.close()
        context.term()


def add_item():
    inventory = load_inventory()
    history_stack.append(inventory.copy())
    print("\n** Adding an item will take approximately 1 to 2 minutes **")
    print("** Please make sure all data fields are correct, items can only be updated retroactively, not deleted **\n")
    print("ADD ITEM:")
    name = input("Enter item name: ")
    prefix = input("Enter optional SKU prefix (leave blank for no prefix): ")
    sku = generate_sku(prefix)
    if not sku:
        print("Error: Could not generate SKU. Please try again.")
        history_stack.pop()
        return
    print(f"Generated SKU: {sku}")
    quantity = int(input("Enter quantity: "))
    price = float(input("Enter price: "))
    low_stock_threshold = int(input("Enter low stock threshold: "))
    for item in inventory:
        if item['sku'] == sku:
            print("Error: SKU must be unique.")
            history_stack.pop()
            return
    inventory.append({
        'name': name,
        'sku': sku,
        'quantity': quantity,
        'price': price,
        'low_stock_threshold': low_stock_threshold
    })
    save_inventory(inventory)
    print("Item added successfully!")
    if quantity < low_stock_threshold:
        send_to_sku_alert(sku, quantity)


def update_item():
    inventory = load_inventory()
    history_stack.append(inventory.copy())
    sku = input("Enter the SKU of the item to update: ")
    for item in inventory:
        if item['sku'] == sku:
            print("Updating item:", item)
            item['name'] = input("Enter new name (leave blank to keep current): ") or item['name']
            quantity = input("Enter new quantity (leave blank to keep current): ")
            item['quantity'] = int(quantity) if quantity else item['quantity']
            price = input("Enter new price (leave blank to keep current): ")
            item['price'] = float(price) if price else item['price']
            low_stock_threshold = input("Enter new low stock threshold (leave blank to keep current): ")
            item['low_stock_threshold'] = int(low_stock_threshold) if low_stock_threshold else item['low_stock_threshold']
            save_inventory(inventory)
            print("Item updated successfully!")
            if item['quantity'] < item['low_stock_threshold']:
                send_to_sku_alert(item['sku'], item['quantity'])
            return
    print("Item not found.")
    history_stack.pop()


def view_all_inventory():
    inventory = load_inventory()
    if inventory:
        print("All Inventory Items:")
        for item in inventory:
            print(f"Name: {item['name']}, SKU: {item['sku']}, Quantity: {item['quantity']}, Price: ${item['price']}, Low Stock Threshold: {item['low_stock_threshold']}")
    else:
        print("No items in inventory.")


def view_low_stock():
    inventory = load_inventory()
    low_stock_items = [item for item in inventory if item['quantity'] < item['low_stock_threshold']]
    if low_stock_items:
        print("Low Stock Items:")
        for item in low_stock_items:
            print(f"Name: {item['name']}, SKU: {item['sku']}, Quantity: {item['quantity']}")
            send_to_sku_alert(item['sku'], item['quantity'])  # Notify microservice
    else:
        print("All items are sufficiently stocked.")


def view_inventory_report():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    try:
        socket.connect("tcp://localhost:5555")  # Connect to the ZeroMQ microservice
        socket.send_json(["generate_report"])  # Send a request to generate the report
        response = socket.recv_string()  # Receive the report
        print("\nInventory Report:\n")
        print(response)
    except zmq.ZMQError as e:
        print(f"Error connecting to the microservice: {e}")
    finally:
        socket.close()
        context.term()


def search_item():
    query = input("Enter the name or SKU of the item to search: ")
    url = "http://localhost:5005/searchItem"
    try:
        response = requests.post(url, json={"query": query})
        response.raise_for_status()
        results = response.json()
        if results:
            print("\nSearch Results:")
            for item in results:
                print(f"Name: {item['name']}, SKU: {item['sku']}, Quantity: {item['quantity']}, Price: ${item['price']:.2f}")
        else:
            print("\nNo items found matching your query.")
    except requests.RequestException as e:
        print(f"Error searching items: {e}")


def backup_inventory():
    url = "http://localhost:5006/backupInventory"
    try:
        response = requests.post(url)
        response.raise_for_status()
        data = response.json()
        print(f"\n{data['message']}")
        print(f"Backup file created: {data['backup_file']}")
    except requests.RequestException as e:
        print(f"Error during backup: {e}")


def main_menu():
    print("\nWelcome to the Inventory Management System!")
    while True:
        print("\nInventory Management System")
        print("1. Add Item")
        print("2. Update Item")
        print("3. View Inventory")
        print("4. View Low Stock Items")
        print("5. View Inventory Report")
        print("6. Search Item")
        print("7. Backup Inventory")  # New Option
        print("8. Exit")
        choice = input("Enter your choice: ")
        if choice == '1':
            add_item()
        elif choice == '2':
            update_item()
        elif choice == '3':
            view_all_inventory()
        elif choice == '4':
            view_low_stock()
        elif choice == '5':
            view_inventory_report()
        elif choice == '6':
            search_item()
        elif choice == '7':  # New Option
            backup_inventory()
        elif choice == '8':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main_menu()