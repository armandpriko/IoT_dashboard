import sqlite3

def list_devices():
    conn = sqlite3.connect('climate_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, api_key FROM devices')
    devices = cursor.fetchall()
    
    print('Devices in database:')
    if devices:
        for device in devices:
            print(f"ID: {device[0]}, Name: {device[1]}, API Key: {device[2]}")
    else:
        print("No devices found.")
    
    conn.close()

if __name__ == "__main__":
    list_devices()
