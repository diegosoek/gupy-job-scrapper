# importando as bibliotecas necessarias
import requests
import csv
import os
from datetime import datetime
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# para realizar uma solicitacao http precisamos informar um header, neste caso usaremos o user-agent
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 OPR/100.0.0.0 (Edition std-1)'}
# Outras constantes utilizadas
START_DATE = os.getenv("DATE_START")
WORD_KEYS_REQUIRED = [word.strip() for word in os.getenv("DESCRIPTION_REQUIRED_KEYWORDS").split(',')]
START_DATE_DATETIME = datetime.strptime(START_DATE, "%d/%m/%Y")

# criando uma lista para aumentar o alcance de retornos no scrap
LABEL_SEARCH = [label.strip() for label in os.getenv("TITLE_KEYWORDS").split(',')]

# criando uma lista para definir o nome das colunas no arquivo csv
COLUMN_NAMES = ['id', 'companyId', 'name', 'description', 'careerPageName', 'type', 'publishedDate',  'isRemoteWork', 'city', 'state', 'country', 'JobLink', 'searchDate']

# lista vazia para salvar os dados
data = []

# conjunto para guardar os ids das vagas para impedir de gravar vagas repetidas
ids = set()


def find_word_keys(array, string_alvo):
    for s in array:
        if s.lower() not in string_alvo.lower():
            return False
    return True

#aqui esta nosso scrap, faremos um HTTP GET no endpoint onde esta localizada as vagas, fazendo um busca por cada valor passado no rotulo anterior e salvando em um arquivo jobs.csv. 
with open('jobs.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    
    #aplicando nome nas colunas do csv
    writer.writerow(COLUMN_NAMES)
    
    for label in LABEL_SEARCH:

        labelFormated = label.replace(" ", "%20")
        offset = 0
        limit = 10
        total = None
        jobCount = 0

        while True:
            url = f"https://portal.api.gupy.io/api/job?name={labelFormated}&offset={offset}"
            try:
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()  
                json_response = response.json()

                if total is None:
                    pagination = json_response.get("pagination", {})
                    total = pagination["total"]

                data = json_response.get("data", [])
                
                if not data:
                    break

                print(f"Buscando vagas para {label} ({offset}/{total})")

                for job in data:
                    job_id = job.get('id', '')
                    
                    # Verificar se o id da vaga ja foi salvo
                    if job_id not in ids:
                        ids.add(job_id)


                        # Converter a string publishedDate para um objeto datetime
                        data1_str = job.get('publishedDate', '')
                        data1 = datetime.strptime(data1_str, "%Y-%m-%dT%H:%M:%S.%fZ")

                        description = job.get('description', '')

                        #dados que utilizaremos na nossa analise
                        row = [
                            job_id,
                            job.get('companyId', ''),
                            job.get('name', ''),
                            description,
                            job.get('careerPageName', ''),
                            job.get('type', ''),
                            job.get('publishedDate', ''),
                            job.get('isRemoteWork', ''),
                            job.get('city', ''),
                            job.get('state', ''),
                            job.get('country', ''),
                            job.get('jobUrl', ''),
                            date.today().strftime('%d/%m/%Y'),
                        ]

                        # só adiciona se a data for maior que a data minima especificada
                        # só adiciona se a string contiver TODAS as palavras chaves
                        if data1 > START_DATE_DATETIME and find_word_keys(WORD_KEYS_REQUIRED, description):
                            writer.writerow(row)
                            jobCount += 1
                
                offset += limit
                if offset >= total:
                    break
            
            #printando erro caso ocorra
            except requests.exceptions.RequestException as e:
                print(f"Erro ao buscar dados para {label}: {e}")
            
        print(f"Numero de vagas encontradas: {jobCount}")


