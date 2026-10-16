
import os

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("SPTRANS_ACCESS_TOKEN", "").strip()

if not token:
    raise ValueError("SPTRANS_ACCESS_TOKEN não encontrado no .env")

url = (
    "https://gateway.apilib.prefeitura.sp.gov.br/"
    "sptrans/olhovivo/v2.1/Linha/Buscar"
)

try:
    response = requests.get(
        url,
        params={"termosBusca": "516N-10"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    print("HTTP status:", response.status_code)

    if response.ok:
        print("Resposta:", response.text[:2000])
    else:
        print("Resposta:", response.text[:500])

except requests.RequestException as error:
    print("Erro de conexão:", error)
