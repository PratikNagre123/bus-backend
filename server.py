from flask import Flask, request, jsonify, render_template
import json
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# File paths
DRIVERS_FILE = 'drivers.json'
BUS_LOCATIONS_FILE = 'bus_locations.json'

# Initialize JSON files if they don't exist
def init_json_files():
    for file_path in [DRIVERS_FILE, BUS_LOCATIONS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)
        else:
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        with open(file_path, 'w') as f:
                            json.dump([], f)
                    else:
                        json.loads(content)
            except (json.JSONDecodeError, FileNotFoundError):
                with open(file_path, 'w') as f:
                    json.dump([], f)

# Read JSON file
def read_json(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

# Write to JSON file
def write_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/register_driver', methods=['POST'])
def register_driver():
    data = request.json
    drivers = read_json(DRIVERS_FILE)
    
    if any(d['driver_id'] == data['driver_id'] for d in drivers):
        return jsonify({'error': 'Driver ID already exists'}), 400
    if any(d['email'] == data['email'] for d in drivers):
        return jsonify({'error': 'Email already exists'}), 400
    
    drivers.append({
        'driver_id': data['driver_id'],
        'full_name': data['full_name'],
        'email': data['email'],
        'password': data['password']
    })
    
    write_json(DRIVERS_FILE, drivers)
    return jsonify({'message': 'Registration successful'})

@app.route('/login_driver', methods=['POST'])
def login_driver():
    data = request.json
    drivers = read_json(DRIVERS_FILE)
    
    driver = next((d for d in drivers if d['driver_id'] == data['driver_id'] and d['password'] == data['password']), None)
    if driver:
        return jsonify({'message': 'Login successful'})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/submit_bus_info', methods=['POST'])
def submit_bus_info():
    data = request.json
    bus_locations = read_json(BUS_LOCATIONS_FILE)
    
    bus_info = {
        'driver_id': data['driver_id'],
        'start': data['start'],
        'end': data['end'],
        'major_cities': [city.strip() for city in data['major_cities'].split(',')],
        'plate': data['plate'],
        'latitude': data['latitude'],
        'longitude': data['longitude'],
        'timestamp': datetime.now().isoformat()
    }
    
    bus_locations = [b for b in bus_locations if b['driver_id'] != data['driver_id']]
    bus_locations.append(bus_info)
    
    write_json(BUS_LOCATIONS_FILE, bus_locations)
    return jsonify({'message': 'Bus location updated'})

@app.route('/find_buses', methods=['POST'])
def find_buses():
    data = request.json
    current_location = data['current_location'].lower()
    destination = data['destination'].lower()
    
    bus_locations = read_json(BUS_LOCATIONS_FILE)
    matching_buses = []
    
    for bus in bus_locations:
        if (current_location in bus['start'].lower() or
            current_location in bus['end'].lower() or
            any(current_location in city.lower() for city in bus['major_cities']) or
            destination in bus['start'].lower() or
            destination in bus['end'].lower() or
            any(destination in city.lower() for city in bus['major_cities'])):
            matching_buses.append(bus)
    
    matching_buses.sort(key=lambda x: x['driver_id'])
    return jsonify(matching_buses)

@app.route('/get_bus_location', methods=['GET'])
def get_bus_location():
    driver_id = request.args.get('driver_id')
    bus_locations = read_json(BUS_LOCATIONS_FILE)
    
    bus = next((b for b in bus_locations if b['driver_id'] == driver_id), None)
    if bus:
        return jsonify({
            'latitude': bus['latitude'],
            'longitude': bus['longitude']
        })
    return jsonify({'error': 'Bus not found'}), 404

@app.route('/track')
def track_location():
    driver_id = request.args.get('driver_id')
    bus_locations = read_json(BUS_LOCATIONS_FILE)
    bus = next((b for b in bus_locations if b['driver_id'] == driver_id), None)
    
    if bus:
        return render_template('track.html',
                               lat=bus['latitude'],
                               lon=bus['longitude'],
                               driver_id=bus['driver_id'],
                               start=bus['start'],
                               end=bus['end'])
    else:
        return "No location data found for this driver.", 404

if __name__ == '__main__':
    init_json_files()
    app.run(debug=True, port=5000)
