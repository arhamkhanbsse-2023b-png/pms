import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('park_o_matic.db')
    cursor = conn.cursor()
    
    # Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       username TEXT UNIQUE, 
                       password TEXT, 
                       parking_count INTEGER DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS slots 
                      (slot_id TEXT PRIMARY KEY, 
                       status TEXT DEFAULT 'AVAILABLE',
                       area TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS car_logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       plate TEXT, model TEXT, 
                       arrival TEXT, exit TEXT, 
                       slot_id TEXT, 
                       user_id INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       user_id INTEGER, 
                       rating INTEGER, 
                       message TEXT)''')

    # Data Seed
    areas = ['Hayatabad', 'University Road', 'Saddar', 'Cantt']
    existing = cursor.execute("SELECT count(*) FROM slots").fetchone()[0]
    if existing == 0:
        for i in range(1, 13):
            area = areas[(i-1) // 3] 
            cursor.execute("INSERT INTO slots (slot_id, area) VALUES (?,?)", (f"SLOT-{i:02d}", area))

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('park_o_matic.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- API ROUTES ---

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                        (data['username'], data['password'])).fetchone()
    conn.close()
    if user:
        return jsonify({'success': True, 'user_id': user['id'], 'username': user['username'], 'count': user['parking_count']})
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (data['username'], data['password']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Username exists'})

@app.route('/status')
def status():
    area = request.args.get('area', 'All')
    conn = get_db()
    query = """
    SELECT s.slot_id, s.status, s.area, c.plate, c.model 
    FROM slots s
    LEFT JOIN car_logs c ON s.slot_id = c.slot_id AND c.exit IS NULL
    """
    params = []
    if area != 'All':
        query += " WHERE s.area = ?"
        params.append(area)
    
    query += " GROUP BY s.slot_id"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/park', methods=['POST'])
def park():
    data = request.json
    conn = get_db()
    
    # Park
    conn.execute("UPDATE slots SET status = 'OCCUPIED' WHERE slot_id = ?", (data['slot'],))
    conn.execute("INSERT INTO car_logs (plate, model, arrival, slot_id, user_id) VALUES (?,?,?,?,?)",
                 (data['plate'], data['model'], datetime.now().strftime("%H:%M:%S"), data['slot'], data['user_id']))
    
    # Loyalty
    conn.execute("UPDATE users SET parking_count = parking_count + 1 WHERE id = ?", (data['user_id'],))
    
    # Get new count
    new_count = conn.execute("SELECT parking_count FROM users WHERE id = ?", (data['user_id'],)).fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'new_count': new_count})

@app.route('/update_status', methods=['POST'])
def update():
    data = request.json
    conn = get_db()
    conn.execute("UPDATE slots SET status = ? WHERE slot_id = ?", (data['status'], data['slot_id']))
    if data['status'] in ['AVAILABLE', 'UNAVAILABLE', 'RESERVED']:
        conn.execute("UPDATE car_logs SET exit = ? WHERE slot_id = ? AND exit IS NULL", 
                     (datetime.now().strftime("%H:%M:%S"), data['slot_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/get_user_info')
def user_info():
    uid = request.args.get('user_id')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    if user:
         return jsonify({'parking_count': user['parking_count']})
    return jsonify({'parking_count': 0})

if __name__ == '__main__':
    init_db()
    app.run(port=5000)
