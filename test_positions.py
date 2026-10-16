
import os

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("SPTRANS_ACCESS_TOKEN", "").strip()

if not token:
    raise ValueError("SPTRANS_ACCESS_TOKEN não encontrado no .env")

url = (
    "https://gateway.apilib.prefeitura.sp.gov.br/"
    "sptrans/olhovivo/v2.1/Posicao"
)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "Content-Length": "0",
}

# Códigos internos encontrados na busca pela linha 516N-10
target_codes = {266, 33034}

response = requests.get(
    url,
    headers=headers,
    timeout=60,
)

print("HTTP status:", response.status_code)

response.raise_for_status()
data = response.json()

print("Horário da consulta na API:", data.get("hr"))

lines = data.get("l", [])

matches = [
    line for line in lines
    if line.get("cl") in target_codes
]

if not matches:
    print("Nenhuma das duas linhas foi encontrada na resposta.")
else:
    for line in matches:
        vehicles = line.get("vs", [])

        print("\nLinha:", line.get("c"))
        print("Código interno:", line.get("cl"))
        print("Sentido:", line.get("sl"))
        print("Terminal inicial:", line.get("lt0"))
        print("Terminal final:", line.get("lt1"))
        print("Quantidade veículos informada pela API:", line.get("qv"))
        print("Veículos detalhados:", len(vehicles))

        for vehicle in vehicles:
            print({
                "prefixo": vehicle.get("p"),
                "ativo": vehicle.get("a"),
                "ultima_atualizacao": vehicle.get("ta"),
                "latitude": vehicle.get("py"),
                "longitude": vehicle.get("px"),
            })
