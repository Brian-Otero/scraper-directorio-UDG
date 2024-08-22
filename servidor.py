from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json
import os
import logging
import ngrok
from dotenv import load_dotenv
from datetime import datetime, timedelta
import threading
import time

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Ruta del archivo JSON
json_path = 'contact_info.json'
# Intervalo de tiempo para ejecutar el scraper (1 semana)
scraping_interval = timedelta(weeks=1)

# Función para verificar si el scraper debe ejecutarse
def should_run_scraping():
    if not os.path.exists(json_path):
        return True

    last_modified = datetime.fromtimestamp(os.path.getmtime(json_path))
    return datetime.now() - last_modified > scraping_interval

# Función para ejecutar el scraper
def run_scraping():
    subprocess.run(['python', 'scrap.py'], check=True)

# Clase manejadora de solicitudes HTTP
class ScrapingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            if should_run_scraping():
                self.run_and_respond()
            else:
                self.serve_json()
        elif self.path.startswith("/get-image/"):
            self.get_image()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Endpoint not found")

    def run_and_respond(self):
        try:
            # Ejecutar el scraping
            run_scraping()
            self.serve_json()
        except subprocess.CalledProcessError as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error al ejecutar el script de scraping: {e}".encode('utf-8'))

    def serve_json(self):
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                contact_info = json.load(f)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(contact_info).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Archivo JSON no encontrado")

    def get_image(self):
        filename = self.path.split("/")[-1]
        filepath = os.path.join('contact_info', filename)
        
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.end_headers()
            with open(filepath, 'rb') as file:
                self.wfile.write(file.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(f"Imagen {filename} no encontrada.".encode('utf-8'))

# Función para programar la ejecución semanal del scraping
def schedule_weekly_scraping():
    while True:
        if should_run_scraping():
            run_scraping()
        time.sleep(scraping_interval.total_seconds())

if __name__ == "__main__":
    # Configura el logging
    logging.basicConfig(level=logging.INFO)

    # Iniciar la ejecución semanal del scraping en un hilo separado
    threading.Thread(target=schedule_weekly_scraping, daemon=True).start()
    
    # Configura el servidor HTTP
    server = HTTPServer(("localhost", 0), ScrapingHandler)
    
    # Obtiene el token de ngrok desde la variable de entorno
    ngrok_auth_token = os.getenv("NGROK_AUTHTOKEN")
    
    if not ngrok_auth_token:
        raise ValueError("NGROK_AUTHTOKEN variable de entorno no está configurada.")
    
    # Autentica ngrok usando el token de la variable de entorno
    ngrok.set_auth_token(ngrok_auth_token)
    
    # Expone el servidor HTTP en un túnel ngrok
    ngrok.listen(server)
    
    # Inicia el servidor
    logging.info(f"Server running on {server.server_address}")
    server.serve_forever()
