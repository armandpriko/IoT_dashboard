import sqlite3

def update_database():
    conn = sqlite3.connect('climate_data.db')
    cursor = conn.cursor()
    
    # Check if columns exist before adding them
    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN device_type TEXT DEFAULT 'ESP8266'")
        print("Added device_type column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("device_type column already exists")
        else:
            print(f"Error adding device_type column: {e}")
    
    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN last_connection TEXT")
        print("Added last_connection column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("last_connection column already exists")
        else:
            print(f"Error adding last_connection column: {e}")
    
    conn.commit()
    conn.close()
    print("Database update completed")

if __name__ == "__main__":
    update_database()
