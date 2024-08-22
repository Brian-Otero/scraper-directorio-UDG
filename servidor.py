from flask import Flask, send_file, jsonify
import subprocess
import os
import json

app = Flask(__name__)

@app.route('/run-scraping', methods=['GET'])
def run_scraping():
    try:
        # Ejecuta el script de scraping
        subprocess.run(['python', 'scrap.py'], check=True)
        
        # Carga los datos JSON generados por el script
        with open('contact_info.json', 'r', encoding='utf-8') as f:
            contact_info = json.load(f)
        
        # Devuelve el JSON con la información de contacto
        return jsonify(contact_info)
    
    except subprocess.CalledProcessError as e:
        return f"Error al ejecutar el script de scraping: {e}", 500

@app.route('/get-image/<filename>', methods=['GET'])
def get_image(filename):
    # Construye la ruta completa de la imagen solicitada
    filepath = os.path.join('contact_info', filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/jpeg')
    else:
        return f"Imagen {filename} no encontrada.", 404

if __name__ == "__main__":
    app.run(debug=True)
