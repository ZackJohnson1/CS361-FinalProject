from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
inventory_file = 'inventory.json'


def load_inventory():
    """Load inventory from the inventory.json file."""
    if not os.path.exists(inventory_file):
        with open(inventory_file, 'w') as f:
            json.dump([], f)  # Create an empty inventory if the file doesn't exist
    with open(inventory_file, 'r') as f:
        return json.load(f)


@app.route('/searchItem', methods=['POST'])
def search_item():
    """Search for items by name or SKU."""
    inventory = load_inventory()
    data = request.get_json()
    query = data.get('query', '').lower()
    results = [
        item for item in inventory
        if query in item['name'].lower() or query in item['sku']
    ]
    return jsonify(results), 200


if __name__ == '__main__':
    app.run(port=5005)