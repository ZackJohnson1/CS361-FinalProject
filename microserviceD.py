from flask import Flask, request, jsonify
import json
import os
from datetime import datetime


app = Flask(__name__)


inventory_file = 'inventory.json'
backup_folder = 'backups'


if not os.path.exists(backup_folder):
    os.makedirs(backup_folder)


def load_inventory():
    """Loads inventory.json"""
    if not os.path.exists(inventory_file):
        with open(inventory_file, 'w') as f:
            json.dump([], f)  
    with open(inventory_file, 'r') as f:
        return json.load(f)


@app.route('/backupInventory', methods=['POST'])
def backup_inventory():
    """Backups inventory to a timestamped json"""
    inventory = load_inventory()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = os.path.join(backup_folder, f'backup_{timestamp}.json')
    try:
        with open(backup_filename, 'w') as f:
            json.dump(inventory, f, indent=4)
        return jsonify({
            "message": "Backup successful",
            "backup_file": backup_filename
        }), 200
    except Exception as e:
        return jsonify({"message": f"Backup failed: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(port=5006)