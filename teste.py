
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
def passa_dados_para_eurodia():
    try:
        print(db.colecao_tem_dados("euroHora"))
        if db.colecao_tem_dados("euroHora"):
            df = db.criaRelatorio(1, "euroHora")
            # Converter apenas para exibição
            data_brasil = datetime.now(TZ_BRASIL)
            media = df["valor"].mean()
            db.insereDados(data_brasil, media, "euroDia")
            db.deletaDados()
    except Exception as e:
         return print(f"❌ Erro ao buscar cotação: {e}")

     
if __name__ == "__main__":
    
      passa_dados_para_eurodia()