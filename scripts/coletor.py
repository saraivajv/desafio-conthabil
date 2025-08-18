import os
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# --- Configurações ---
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "downloads")
DOM_URL = "https://www.natal.rn.gov.br/dom"
UPLOAD_URL = "https://0x0.st"
WINDOWS_TEMP_DIR_PATH = "/mnt/c/temp_selenium_profiles"

# Garante que o diretório de downloads exista
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_target_competence():
    """Calcula a competência alvo (mês anterior)."""
    today = datetime.now()
    target_date = today - relativedelta(months=1)
    return target_date.strftime("%m"), target_date.strftime("%Y")


def setup_driver():
    """Configura o driver do Selenium para baixar arquivos no diretório correto."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        },
    )

    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def collect_pdfs(driver, target_month, target_year):
    """Navega no site, encontra e baixa os PDFs da competência alvo."""
    print(f"Buscando publicações de {target_month}/{target_year}...")
    driver.get(DOM_URL)

    try:
        # --- MUDANÇA IMPORTANTE: ESPERA INTELIGENTE ---
        # Espera até 15 segundos para que os containers das publicações apareçam na página.
        # ATENÇÃO: a classe 'dom-edicao-container' pode precisar de ajuste.
        print("Aguardando os elementos da página carregarem...")
        wait = WebDriverWait(driver, 15)
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "dom-edicao-container")
            )
        )
        print("Elementos carregados. Analisando o HTML...")

    except Exception as e:
        print(f"Erro ao esperar pelos elementos da página: {e}")
        print(
            "A página pode ter mudado ou não há publicações. Verifique o seletor 'dom-edicao-container'."
        )
        return  # Sai da função se não encontrar nada

    # Usa o page_source APÓS a espera, garantindo que o conteúdo está lá
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    publications = soup.find_all("div", class_="dom-edicao-container")
    print(
        f"Análise inicial do HTML encontrou {len(publications)} publicações na página.\n"
    )

    downloaded_files_count = 0
    for i, pub in enumerate(publications):
        print(f"--- Processando Publicação #{i+1} ---")
        try:
            # --- DEBUG: Vamos ver o texto da data que está sendo extraído ---
            date_element = pub.find("div", class_="dom-edicao-data")
            date_str = (
                date_element.text.strip()
                if date_element
                else "DATA NÃO ENCONTRADA"
            )
            print(f"Texto da data extraído: '{date_str}'")

            # Tenta converter a data para o formato esperado
            pub_date = datetime.strptime(date_str, "%d/%m/%Y")
            print(
                f"Data convertida com sucesso: {pub_date.strftime('%Y-%m-%d')}"
            )

            # Verifica se a publicação é do mês e ano alvo
            if (
                pub_date.strftime("%m") == target_month
                and pub_date.strftime("%Y") == target_year
            ):
                link_element = pub.find("a", href=True)
                if link_element:
                    pdf_url = link_element["href"]
                    print(f"  ==> DATA CORRETA! Baixando PDF de {date_str}...")

                    element_to_click = driver.find_element(
                        By.CSS_SELECTOR, f'a[href="{pdf_url}"]'
                    )
                    element_to_click.click()

                    downloaded_files_count += 1
                    time.sleep(3)
                else:
                    print(
                        "  Aviso: Data correta, mas nenhum link de PDF encontrado."
                    )
            else:
                print(
                    f"  Data fora do período alvo ({target_month}/{target_year}). Ignorando."
                )

        except (AttributeError, ValueError) as e:
            print(f"  ERRO ao processar esta publicação: {e}")
            print(
                "  Verifique se o seletor 'dom-edicao-data' e o formato da data ('%d/%m/%Y') estão corretos."
            )

        print("-" * (len("--- Processando Publicação #1 ---")))

    if downloaded_files_count == 0:
        print("\nNenhum arquivo baixado para o período alvo.")
    else:
        print(
            f"\nTotal de {downloaded_files_count} arquivos baixados. Aguardando conclusão..."
        )
        time.sleep(15)


def upload_files():
    """Faz o upload dos arquivos da pasta downloads para o 0x0.st."""
    uploaded_urls = []
    print("\nIniciando upload dos arquivos...")

    pdf_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("Nenhum PDF para fazer upload.")
        return []

    for filename in pdf_files:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f)}
                response = requests.post(UPLOAD_URL, files=files)
                response.raise_for_status()

                file_url = response.text.strip()
                uploaded_urls.append(file_url)
                print(f"  - Upload de {filename} bem-sucedido: {file_url}")

        except requests.exceptions.RequestException as e:
            print(f"  Erro ao fazer upload de {filename}: {e}")
        except IOError as e:
            print(f"  Erro ao ler o arquivo {filename}: {e}")

    return uploaded_urls


def save_urls_to_api(urls, competence):
    """Envia as URLs coletadas para a API Django."""
    API_ENDPOINT = "http://127.0.0.1:8000/api/publications/"
    print(
        f"\nEnviando {len(urls)} URLs para a API na competência {competence}..."
    )

    success_count = 0
    for url in urls:
        payload = {"file_url": url, "competence": competence}
        try:
            response = requests.post(API_ENDPOINT, json=payload)
            if response.status_code == 201:
                print(f"  - URL salva: {url}")
                success_count += 1
            else:
                print(
                    f"  - Falha ao salvar URL {url}: {response.status_code} - {response.text}"
                )
        except requests.exceptions.RequestException as e:
            print(f"  - Erro de conexão com a API: {e}")

    print(f"{success_count}/{len(urls)} URLs salvas com sucesso.")


def main():
    """Orquestra a execução do script."""
    target_month, target_year = get_target_competence()
    competence_str = f"{target_year}-{target_month}"

    driver = setup_driver()

    try:
        collect_pdfs(driver, target_month, target_year)
        uploaded_urls = upload_files()

        if uploaded_urls:
            # Com a API rodando, chame a nova função
            save_urls_to_api(uploaded_urls, competence_str)
        else:
            print("\nNenhuma URL foi gerada para salvar na API.")

    finally:
        driver.quit()
        print("\nScript finalizado.")


if __name__ == "__main__":
    main()
