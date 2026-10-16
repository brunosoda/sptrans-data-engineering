
import os

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("SPTRANS_TOKEN", "").strip()

if not token:
    raise ValueError(
        "SPTRANS_TOKEN não encontrado. Verifique o arquivo .env."
    )

url = "https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar"

with requests.Session() as session:
    try:
        response = session.post(
            url,
            params={"token": token},
            data="",
            timeout=30,
        )

        print("HTTP status:", response.status_code)
        print("Resposta:", response.text)
        print("Cookies recebidos:", bool(session.cookies))

        if response.status_code == 200 and response.text.strip() == "true":
            print("Autenticação bem-sucedida.")
        elif response.status_code == 200:
            print("Autenticação não confirmada. Verifique o token e o portal.")
        else:
            print("Erro HTTP. Verifique o endpoint e as credenciais.")

    except requests.RequestException as error:
        print("Erro de conexão:", error)
