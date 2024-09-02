from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import json
import os
from datetime import datetime, timedelta
import uvicorn

# Ruta del archivo JSON
json_path = 'contact_info.json'

# Intervalo de tiempo para ejecutar el scraper (1 semana)
scraping_interval = timedelta(weeks=1)

app = FastAPI()

# Funcion para verificar si el scraper debe ejecutarse o no
def should_run_scraping():
    if not os.path.exists(json_path):
        return True

    last_modified = datetime.fromtimestamp(os.path.getmtime(json_path))
    return datetime.now() - last_modified > scraping_interval

# Funcin de la api para activar el scraper
def run_scraping():
    subprocess.run(['python', 'scrap.py'], check=True)

# Funcion de la api para servir el json
@app.get("/")
async def serve_json():
    if should_run_scraping():
        run_scraping()
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            contact_info = json.load(f)
        return JSONResponse(content=contact_info)
    else:
        raise HTTPException(status_code=404, detail="Archivo JSON no encontrado")

# Funcion de la api para servir imagenes
@app.get("/get-image/{filename}")
async def get_image(filename: str):
    filepath = os.path.join('contact_info', filename)
    
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type='image/jpeg')
    else:
        raise HTTPException(status_code=404, detail=f"Imagen {filename} no encontrada")

# Configuracion del programador de tareas
def schedule_weekly_scraping():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scraping, 'interval', weeks=1)
    scheduler.start()

if __name__ == "__main__":
   
    # Iniciar la tarea programada
    schedule_weekly_scraping()
    
    # Ejecutar el servidor de FastAPI por medio de uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
