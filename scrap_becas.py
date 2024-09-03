from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time

def extract_table_data(page_soup):
    table_data = []

    rows = page_soup.select('div.view-content ul li.views-row')

    for row in rows:
        convocatoria = row.select_one('div.views-field-title span.field-content a')
        beneficiados = row.select_one('div.views-field-field-convocatoria-carreras .field-content')
        fecha = row.select_one('div.views-field-field-convocatoria-fecha .date-display-range')
        resumen = row.select_one('div.views-field-field-convocatoria-resumen .field-content')
        hipervinculo = "https://www.cucei.udg.mx" + convocatoria['href'] if convocatoria else None

        data = {
            'convocatoria': convocatoria.get_text(strip=True) if convocatoria else 'N/A',
            'beneficiados': beneficiados.get_text(strip=True) if beneficiados else 'N/A',
            'fecha': fecha.get_text(strip=True) if fecha else 'N/A',
            'resumen': resumen.get_text(strip=True) if resumen else 'N/A',
            'hipervinculo': hipervinculo if hipervinculo else 'N/A'
        }
        
        table_data.append(data)

    return table_data


def main():
    start_url = 'https://www.cucei.udg.mx/es/servicios/becas-y-convocatorias'

    options = Options()
    options.add_argument('--headless')  # Ejecuta el navegador en modo headless
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    service = Service('./chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(start_url)
    
    all_data = []
    
    while True:
        try:
            # Esperar a que la vista de contenido esté presente en la página
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.view-content')))
            
            # Parsear la página con BeautifulSoup
            page_soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extraer la información de la tabla
            table_data = extract_table_data(page_soup)
            all_data.extend(table_data)
            
            try:
                # Intentar encontrar el botón "siguiente"
                next_button = driver.find_element(By.CSS_SELECTOR, 'li.pager-next a')
                if next_button:
                    # Hacer clic en "siguiente"
                    next_button.click()
                    # Esperar un poco para que cargue la nueva página
                    time.sleep(2)
                else:
                    break  # Si no hay más botón "siguiente", sal del bucle
            except:
                break  # Salir del bucle si no se encuentra el botón "siguiente"
        
        except Exception as e:
            print(f"Error during scraping: {e}")
            break
    
    # Guardar los datos en un archivo JSON
    with open('becas_convocatorias.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print("Data extraction and saving complete.")
    
    driver.quit()

if __name__ == "__main__":
    main()
