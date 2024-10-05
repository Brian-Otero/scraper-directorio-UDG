import json
import os
import re

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_full_url(base_url, relative_url):
    return base_url + relative_url if relative_url.startswith('/') else relative_url


def decode_html_entities(html):
    return re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), html)


def clean_text(text):
    return re.sub(r'^(Puesto:|Dirección:|Conmutador:|Teléfono:)\s*', '', text.strip())


def extract_contact_info(page_soup, base_url):
    contacts = []
    department_containers = page_soup.select('.view-content .item-list')

    for department_container in department_containers:
        department_tag = department_container.select_one('h3 div')
        if department_tag:
            department = department_tag.get_text(strip=True)
        else:
            continue

        for item in department_container.select('ul li.views-row'):
            contact = {}
            contact['departamento'] = department

            img_tag = item.select_one('.views-field-field-fotograf-a img')
            if img_tag:
                img_url = get_full_url(base_url, img_tag['src'])
                img_filename = img_url.split('/')[-1]
                img_path = os.path.join('contact_info', img_filename)
                contact['imagen'] = './contact_info/' + img_filename

                try:
                    img_response = requests.get(img_url)
                    img_response.raise_for_status()
                    os.makedirs(os.path.dirname(img_path), exist_ok=True)
                    with open(img_path, 'wb') as img_file:
                        img_file.write(img_response.content)
                except requests.RequestException as e:
                    print(f"Error downloading image {img_url}: {e}")

            name_tag = item.select_one('.views-field-title a')
            if name_tag:
                contact['nombre'] = name_tag.get_text(strip=True)

            position_tag = item.select_one('.views-field-field-puesto-directorio')
            if position_tag:
                contact['puesto'] = clean_text(position_tag.get_text(strip=True))

            address_tag = item.select_one('.views-field-field-direcci-n')
            if address_tag:
                contact['direccion'] = clean_text(address_tag.get_text(strip=True))

            conmutador_tag = item.select_one('.views-field-field-conmutador')
            if conmutador_tag and conmutador_tag.get_text(strip=True):
                contact['conmutador'] = clean_text(conmutador_tag.get_text(strip=True))
            else:
                phone_tag = item.select_one('.views-field-field-tel-fono')
                if phone_tag:
                    contact['conmutador'] = clean_text(phone_tag.get_text(strip=True))

            email_tag = item.select_one('.views-field-field-correo-electronico a')
            if email_tag:
                contact['correo_electronico'] = decode_html_entities(email_tag.get_text(strip=True))
            else:
                contact['correo_electronico'] = 'N/A'

            if contact['correo_electronico'] != 'N/A':
                contacts.append(contact)

    return contacts


def cleanup_files():
    # Eliminar el archivo JSON si existe
    if os.path.exists('contact_info.json'):
        os.remove('contact_info.json')

    # Eliminar todas las imágenes en el directorio 'contact_info'
    if os.path.exists('contact_info'):
        for filename in os.listdir('contact_info'):
            file_path = os.path.join('contact_info', filename)
            if os.path.isfile(file_path):
                os.remove(file_path)


def get_driver_for_linux():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def get_driver_for_windows():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=Service("./chromedriver.exe"), options=options)
    return driver


def main():
    base_url = 'https://www.cucei.udg.mx'
    start_url = 'https://www.cucei.udg.mx/es/directorio'

    # Limpia los archivos antiguos antes de ejecutar el scraping
    cleanup_files()

    # Selecciona el driver adecuado según el sistema operativo
    driver = get_driver_for_windows() if os.name == 'nt' else get_driver_for_linux()
    driver.get(start_url)

    # Espera a que la pagina se cargue complatemente
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "views-row")))

    # Obtiene el HTML después de que el JavaScript haya sido ejecutado
    page_soup = BeautifulSoup(driver.page_source, 'html.parser')

    contact_info = extract_contact_info(page_soup, base_url)
    with open('contact_info.json', 'w', encoding='utf-8') as f:
        json.dump(contact_info, f, ensure_ascii=False, indent=4)

    print("Data extraction and saving complete.")

    driver.quit()


if __name__ == "__main__":
    main()
