from flask import Flask, request, jsonify, g
from flask_cors import CORS
import json
import os
import pyodbc
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

server = os.getenv("SERVER")
database = os.getenv("DATABASE")
username = os.getenv("SQLUSERNAME")
password = os.getenv("PASSWORD")
username=username
app = Flask(__name__)

# Restrict CORS to trusted domains
CORS(app, resources={r"/transactions": {"origins": ["https://skyalcu.com"]}})

# Enable logging
logging.basicConfig(level=logging.DEBUG)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return {"error": "An internal error occurred"}, 500
    
# Database connection pooling
def get_db_connection():
    if 'db' not in g:
        g.db = pyodbc.connect(
            "DRIVER={/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.0.so.1.1};"
            "SERVER=" + server + ";"
            "DATABASE=" + database + ";"
            "UID=" + username + ";"
            "PWD=" + password + ";"
            "TrustServerCertificate=yes",
            autocommit=True
        )
    return g.db


@app.teardown_appcontext
def close_db_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        account_number = request.args.get("AccountNumber")
        if not account_number:
            return jsonify({"error": "Missing AccountNumber parameter"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC GetTransDetail ?", account_number)
        rows = cursor.fetchall()

        # Convert to JSON
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        if not data:
            return jsonify({"error": "No transactions found"}), 404

        return jsonify(data)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"error": "An internal error occurred"}), 500
        
if __name__ == "__main__":
    app.run(debug=True)

    


