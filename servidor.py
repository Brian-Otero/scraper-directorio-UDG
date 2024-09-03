from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import json
import os
from datetime import datetime, timedelta
import uvicorn

# Rutas de los archivos JSON
contact_info_json_path = 'contact_info.json'
becas_json_path = 'becas_convocatorias.json'

# Intervalo de tiempo para ejecutar los scrapers (1 semana)
scraping_interval = timedelta(weeks=1)

app = FastAPI()

# Función para verificar si el scraper debe ejecutarse o no
def should_run_scraping(json_path):
    if not os.path.exists(json_path):
        return True

    last_modified = datetime.fromtimestamp(os.path.getmtime(json_path))
    return datetime.now() - last_modified > scraping_interval

# Función de la API para activar el scraper
def run_scraping(script_name):
    subprocess.run(['python3', script_name], check=True)

# Función de la API para servir el JSON de contact_info
@app.get("/")
async def serve_contact_info_json():
    if should_run_scraping(contact_info_json_path):
        run_scraping('scrap.py')
    
    if os.path.exists(contact_info_json_path):
        with open(contact_info_json_path, 'r', encoding='utf-8') as f:
            contact_info = json.load(f)
        return JSONResponse(content=contact_info)
    else:
        raise HTTPException(status_code=404, detail="Archivo JSON no encontrado")

# Función de la API para servir el JSON de becas
@app.get("/becas")
async def serve_becas_json():
    if should_run_scraping(becas_json_path):
        run_scraping('scrap_becas.py')
    
    if os.path.exists(becas_json_path):
        with open(becas_json_path, 'r', encoding='utf-8') as f:
            becas_info = json.load(f)
        return JSONResponse(content=becas_info)
    else:
        raise HTTPException(status_code=404, detail="Archivo JSON de becas no encontrado")

# Función de la API para servir imágenes
@app.get("/get-image/{filename}")
async def get_image(filename: str):
    filepath = os.path.join('contact_info', filename)
    
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type='image/jpeg')
    else:
        raise HTTPException(status_code=404, detail=f"Imagen {filename} no encontrada")

# Configuración del programador de tareas
def schedule_weekly_scraping():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: run_scraping('scrap.py'), 'interval', weeks=1)
    scheduler.add_job(lambda: run_scraping('scrap_becas.py'), 'interval', weeks=1)
    scheduler.start()

if __name__ == "__main__":
    # Iniciar la tarea programada
    schedule_weekly_scraping()
    
    # Ejecutar el servidor de FastAPI por medio de uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
