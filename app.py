from flask import Flask, request, jsonify, g,  render_template
from flask_cors import CORS
import os
import pyodbc
import logging
from dotenv import load_dotenv
from flask import send_from_directory

# Load environment variables (not needed in Azure App Service, but useful for local development)
load_dotenv(".env")

# Retrieve environment variables
server = os.getenv("SERVER")
database = os.getenv("DATABASE")
username = os.getenv("SQLUSERNAME")
password = os.getenv("PASSWORD")

# Validate environment variables
if not all([server, database, username, password]):
    logging.error("One or more required environment variables are missing!")

app = Flask(__name__)

# Restrict CORS to the trusted domain
CORS(app)

# Enable logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return render_template("index.html")  # This loads templates/index.html

@app.route('/favicon.ico')
def favicon():
    return send_from_directory("static", "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.errorhandler(Exception)
def handle_exception(e):
    """ Global error handler to log unexpected exceptions """
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return {"error": "An internal error occurred"}, 500

# Database connection pooling
def get_db_connection():
    """ Returns a database connection from the pool, or creates one if needed """
    if 'db' not in g:
        try:
            g.db = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=240;",
            autocommit=True
        )
        except pyodbc.Error as e:
            app.logger.error(f"Database connection error: {e}")
            raise
    return g.db

@app.teardown_appcontext
def close_db_connection(exception):
    """ Closes the database connection when the request context ends """
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """ Fetches transactions for a given account number from the database """
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

    except pyodbc.Error as e:
        logging.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database connection error"}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
