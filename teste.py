
import asyncio
from io import BytesIO
import os
import requests
from datetime import datetime, timezone
from datetime import date, timedelta
from zoneinfo import ZoneInfo
import pytz 
import conectaBanco as db
import pandas as pd
import matplotlib.pyplot as plt
API_TOKEN  = os.environ.get("API_TOKEN")

TZ_BRASIL = ZoneInfo("America/Sao_Paulo")

if __name__ == "__main__":
    df =  db.criaRelatorio(1, "euroHora")
   
    db.gerar_grafico_euro(df)
    
    url = f"https://api.fxratesapi.com/latest?api_key={API_TOKEN}&base=EUR&currencies=BRL&resolution=1m"

    headers = {"User-Agent": "Mozilla/5.0 (TelegramBot/1.0)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()
    valor = data["rates"]["BRL"]
    print(data['date'])

    dataUTC = datetime.strptime(data['date'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    print(dataUTC)
    
    data_brasil = dataUTC.astimezone(TZ_BRASIL)
    print(data_brasil)
    db.insereDados(data_brasil, valor, "euroHora")


