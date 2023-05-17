import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import datetime

# Pega html da pagina
url = "https://servicos.tce.pr.gov.br/servicos/srv_sim_agendaobrigacoes.aspx"
option = Options()
option.headless = True
driver = webdriver.Firefox()

driver.get(url)

time.sleep(1)

data_atual = datetime.datetime.now().strftime('%Y-%m-%d')

# Estrutura dicionário vazio para armazenar os dados
atrasos = {}

# Loop pelos municípios de 2 a 401
for i in range(2, 401):

    # Seleciona opção do município
    municipio = driver.find_element("xpath", f'//*[@id="ctl00_ContentPlaceHolder1_ddlcdMunicipio"]/option[{i}]')
    municipio_text = municipio.get_attribute('textContent')
    idmunicipio_text = municipio.get_attribute('value')
    municipio.click()

   # Espera até que a mensagem de carregamento desapareça
    WebDriverWait(driver, 240).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_UpdateProgress1"]/div')))

    pane_num = 0

    while True:
        # Construa o XPath para o cabeçalho do painel
        header_xpath = f'//*[@id="ctl00_ContentPlaceHolder1_acPrincipal_Pane_{pane_num}_header"]/table/tbody/tr/td[1]/span'

        # Verifique se o painel existe
        try:
            NomePane = driver.find_element("xpath", header_xpath)
        except:
            # O painel não existe, saia do loop
            break

        # O painel existe, tente obter o conteúdo
        try:
            element = driver.find_element("xpath", f'//*[@id="ctl00_ContentPlaceHolder1_acPrincipal_Pane_{pane_num}_content"]/table')
            html_content = element.get_attribute('outerHTML')
        except:
            element = driver.find_element("xpath", f'//*[@id="ctl00_ContentPlaceHolder1_acPrincipal_Pane_{pane_num}_content"]/span')
            html_content = element.get_attribute('textContent').strip()

        #parsea o conteudo
        soup = BeautifulSoup(html_content, 'html.parser')

        if html_content.startswith('<table'):
            table = soup.find(name='table')

            #Estrutura dataframe
            df_full = pd.read_html(str(table), skiprows=1)[0]

            # Adiciona os dados ao dicionário
            df_full['3'] = municipio_text # Adiciona a informação de município ao dataframe
            df_full['4'] = idmunicipio_text
            df_full['5'] = NomePane.text
            df_full['6'] = data_atual
            df_dict = df_full.to_dict('records')
            atrasos[NomePane.text] = ([{'3': municipio_text,'4': idmunicipio_text, '5' : NomePane.text,'6' : data_atual, **row} for row in df_dict])
            # Adiciona o dicionário atualizado ao dicionário principal
        else:
            # Adiciona os dados ao dicionário
            atrasos[NomePane.text] = [{'0': '', '1': html_content, '2': '', '3' : municipio_text,'4' : idmunicipio_text, '5' :NomePane.text, '6' : data_atual}]

        # Procura o próximo painel
        pane_num += 1

atrasados = atrasos.values()

# Salva os dados em um arquivo JSON
data = list(atrasados)

# Converte o objeto JSON para string e remove todos os colchetes
json_str = json.dumps(data).replace('[', '').replace(']', '')

# Adiciona um colchete aberto no início e um fechado no final da string
json_str = '[' + json_str + ']'

# Converte a string resultante de volta para objeto JSON e escreve no arquivo
data = json.loads(json_str)
with open('Atrasados.json', 'w', encoding= "utf-8") as f:
    json.dump(data, f, ensure_ascii=False,indent = 4)

driver.quit()