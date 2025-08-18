import os
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# --- Configurações ---
load_dotenv()

PROJECT_DOWNLOADS_FOLDER_NAME = os.getenv(
    "PROJECT_DOWNLOADS_FOLDER_NAME", "downloads"
)
DOM_URL = os.getenv("DOM_URL")
UPLOAD_URL = os.getenv("UPLOAD_URL")
API_ENDPOINT = os.getenv("API_ENDPOINT")
DOWNLOAD_DIR = os.path.join(
    os.path.dirname(__file__), "..", PROJECT_DOWNLOADS_FOLDER_NAME
)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_target_competence():
    """Calcula a competência alvo (mês anterior)."""
    today = datetime.now()
    target_date = today - relativedelta(months=1)
    return target_date.strftime("%m"), target_date.strftime("%Y")


def setup_driver():
    """Configura o driver do Selenium (sem a necessidade de gerenciar downloads)."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def collect_pdfs(driver, target_month, target_year):
    """Navega no site, filtra pela data e baixa os PDFs usando requests."""
    print(f"Buscando publicações de {target_month}/{target_year}...")
    driver.get(DOM_URL)

    try:
        print("Iniciando filtragem...")
        time.sleep(2)

        Select(
            driver.find_element(By.CSS_SELECTOR, "select[name='mes']")
        ).select_by_value(target_month)
        print(f"Mês '{target_month}' selecionado.")
        time.sleep(0.5)

        Select(
            driver.find_element(By.CSS_SELECTOR, "select[name='ano']")
        ).select_by_value(target_year)
        print(f"Ano '{target_year}' selecionado.")
        time.sleep(0.5)

        search_button = driver.find_element(
            By.CSS_SELECTOR, "button[type='submit'][data-attach-loading]"
        )
        driver.execute_script("arguments[0].click();", search_button)
        print("Botão 'Pesquisar' clicado. Aguardando resultados...")

        wait = WebDriverWait(driver, 20)
        texto_esperado = f"/{target_month}/{target_year}"
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//tbody/tr//a[contains(., '{texto_esperado}')]")
            )
        )
        print("Tabela com resultados carregada.")

    except Exception as e:
        print(
            f"ERRO: Não foi possível carregar os resultados para {target_month}/{target_year}: {e}"
        )
        driver.save_screenshot("debug_screenshot.png")
        print("Screenshot 'debug_screenshot.png' salvo para análise.")
        return 0

    soup = BeautifulSoup(driver.page_source, "html.parser")
    publications = soup.select("tbody tr")
    print(
        f"Análise do HTML encontrou {len(publications)} linhas na tabela filtrada.\n"
    )

    downloaded_files_count = 0
    for i, pub_row in enumerate(publications):
        print(f"--- Processando Linha #{i+1} ---")
        try:
            link_element = pub_row.select_one("td.sorting_1 a")
            if not link_element:
                print("   Link não encontrado nesta linha. Ignorando.")
                continue

            date_str = link_element.text.strip().split(" ")[-1]
            pub_date = datetime.strptime(date_str, "%d/%m/%Y")

            if pub_date.strftime("%m") == target_month:
                pdf_url = link_element["href"]
                print(f"   ==> DATA CORRETA! Baixando PDF de {date_str}...")

                filename = pdf_url.split("/")[-1]
                destination_path = os.path.join(DOWNLOAD_DIR, filename)

                response = requests.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()

                with open(destination_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"   Arquivo '{filename}' salvo com sucesso.")
                downloaded_files_count += 1
            else:
                print(f"   Data fora do período alvo. Ignorando.")

        except Exception as e:
            print(f"   ERRO ao processar esta linha: {e}")
        finally:
            print("-" * 25)

    if downloaded_files_count == 0:
        print("\nNenhum arquivo baixado para o período alvo.")
    else:
        print(
            f"\nTotal de {downloaded_files_count} arquivos baixados diretamente."
        )

    return downloaded_files_count


def upload_files():
    """Faz o upload dos arquivos da pasta downloads para o 0x0.st."""
    print("\nIniciando upload dos arquivos...")
    pdf_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("Nenhum PDF para fazer upload.")
        return []

    uploaded_urls = []
    for filename in pdf_files:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f)}
                response = requests.post(UPLOAD_URL, files=files, timeout=60)
                response.raise_for_status()

                file_url = response.text.strip()
                uploaded_urls.append(file_url)
                print(f"   - Upload de {filename} bem-sucedido: {file_url}")

        except requests.exceptions.RequestException as e:
            print(f"   Erro ao fazer upload de {filename}: {e}")
        except IOError as e:
            print(f"   Erro ao ler o arquivo {filename}: {e}")

    return uploaded_urls


def save_urls_to_api(urls, competence):
    """Envia as URLs coletadas para a API Django."""
    print(
        f"\nEnviando {len(urls)} URLs para a API na competência {competence}..."
    )
    success_count = 0
    for url in urls:
        payload = {"file_url": url, "competence": competence}
        try:
            response = requests.post(API_ENDPOINT, json=payload, timeout=15)
            if response.status_code == 201:
                print(f"   - URL salva: {url}")
                success_count += 1
            else:
                print(
                    f"   - Falha ao salvar URL {url}: {response.status_code} - {response.text}"
                )

        except requests.exceptions.RequestException as e:
            print(f"   - Erro de conexão com a API: {e}")

    print(f"{success_count}/{len(urls)} URLs salvas com sucesso.")


def main():
    """Orquestra a execução do script."""
    target_month, target_year = get_target_competence()
    competence_str = f"{target_year}-{target_month}"

    driver = setup_driver()
    try:
        downloads_count = collect_pdfs(driver, target_month, target_year)
        if downloads_count > 0:
            uploaded_urls = upload_files()
            if uploaded_urls:
                save_urls_to_api(uploaded_urls, competence_str)
    finally:
        driver.quit()
        print("\nScript finalizado.")


if __name__ == "__main__":
    main()
