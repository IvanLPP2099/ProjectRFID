from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuración MySQL usando variables de entorno
app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
app.config['MYSQL_USER'] = os.getenv('DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('DB_NAME')
app.config['MYSQL_CURSORCLASS'] = os.getenv('DICTCURSOR')

mysql = MySQL(app)

@app.route('/api/bolsas', methods=['POST'])
def recordRFIDReading():
    """
    Recibe el rfid_tag desde el lector RC522.
    - Si es la primera vez: crea registro en bolsas con estado "Almacenado"
    - Si ya existe: actualiza el estado a "Despachado"
    """
    data = request.get_json()
    rfid_tag = data.get("rfid_tag")

    if not rfid_tag:
        return jsonify({"error": "rfid_tag es obligatorio"}), 400

    cur = mysql.connection.cursor()

    # Buscar si el tag ya está registrado
    cur.execute("SELECT * FROM bolsas WHERE rfid_tag = %s", (rfid_tag,))
    existente = cur.fetchone()

    if existente:
        # Si ya estaba registrado → cambiar estado a Despachado
        cur.execute("""
            UPDATE bolsas
            SET estado = 'Despachado'
            WHERE rfid_tag = %s
        """, (rfid_tag,))
        mysql.connection.commit()

        cur.close()
        return jsonify({
            "mensaje": "Bolsa actualizada a estado 'Despachado'",
            "rfid_tag": rfid_tag,
            "estado": "Despachado"
        }), 200

    else:
        # Si no existe → registrar como almacenado
        fecha_ingreso = datetime.now()
        cur.execute("""
            INSERT INTO bolsas (rfid_tag, fecha_ingreso, estado)
            VALUES (%s, %s, 'Almacenado')
        """, (rfid_tag, fecha_ingreso))
        mysql.connection.commit()

        cur.close()
        return jsonify({
            "mensaje": "Bolsa registrada como 'Almacenado'",
            "rfid_tag": rfid_tag,
            "estado": "Almacenado"
        }), 201


@app.route('/api/bolsas/<rfid_tag>', methods=['GET'])
def getBags(rfid_tag):
    """Obtener información de una bolsa a partir del RFID tag"""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id_bolsa, rfid_tag, fecha_ingreso, estado
        FROM bolsas
        WHERE rfid_tag = %s
    """, (rfid_tag,))
    bolsa = cur.fetchone()
    cur.close()

    if bolsa:
        return jsonify(bolsa)
    else:
        return jsonify({"error": "Bolsa no encontrada"}), 404


if __name__ == '__main__':
    app.run(debug=True)
