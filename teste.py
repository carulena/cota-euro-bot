
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
def cotacao_euro():
    url = f"https://api.fxratesapi.com/latest?api_key={API_TOKEN}&base=EUR&currencies=BRL&resolution=1m"
    payload = {}
    headers = {"User-Agent": "Mozilla/5.0 (TelegramBot/1.0)"}
    response = requests.request("GET", url, headers=headers, data=payload)
    
    try:
        responseJson = response.json()
        valor = responseJson['rates']['BRL']
        data_utc = datetime.strptime(
            responseJson['date'],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ).replace(tzinfo=timezone.utc)

        # (opcional) converter para Brasil, mas mantendo datetime
        data_brasil = data_utc.astimezone(ZoneInfo("America/Sao_Paulo"))
        cria_retorno = f"{data_brasil} \n O Euro está R${valor:.2f}"
        db.insereDados(data_brasil, valor, 'euroHora')
        
        brasil_tz = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(brasil_tz)
        resultadosSemana(agora)
        return cria_retorno
    except Exception as e:  
        return f"API de cotação retornou {response.status_code} - erro {e} \n por favor verifique"

def resultadosSemana(agora:datetime):
    if(db.colecao_tem_dados('euroHora')):
        df = db.criaRelatorio(7, 'euroHora')
        print(df.head())
        gerar_grafico_euro(df)
        
def gerar_grafico_euro(df, caminho="euro.png"):
    plt.figure(figsize=(25, 5))
    plt.plot(df["dataHora"].dt.strftime("%d/%m - %H:%M"), df["valor"])
    plt.xlabel("Data")
    plt.ylabel("Euro (R$)")
    plt.title("Cotação do Euro (últimos 7 dias)")
    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()
    
TZ_BRASIL = ZoneInfo("America/Sao_Paulo")

async def gerar_relatorio(chat_id, context, dias):
    if db.colecao_tem_dados("euroDia"):
        df = db.criaRelatorio(dias, "euroDia")
        db.gerar_grafico_euro(df)
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        
        # await context.bot.send_photo(
        #     chat_id=chat_id,
        #     photo=buf,
        #     caption=f'Relatório referente aos ultimos {dias} dias'
        # )
        
        return df
def agora_brasil() -> datetime:
    return datetime.now(TZ_BRASIL)
async def relatorio():
    
    try:
        dias = 7
        if dias <= 0:
            raise ValueError

        # Criar relatório
        df = await gerar_relatorio('', '', dias)

        # Exemplo de métricas
        media = df["valor"].mean()
        minimo = df["valor"].min()
        maximo = df["valor"].max()

        mensagem = (
            f"📊 *Relatório do Euro — últimos {dias} dias*\n\n"
            f"📈 Máximo: R$ {maximo:.2f}\n"
            f"📉 Mínimo: R$ {minimo:.2f}\n"
            f"📊 Média: R$ {media:.2f}"
        )
        print(mensagem)
    except Exception as e:
        return f"❌ Erro ao buscar cotação: {e}"
    # await context.bot.send_message(chat_id=chat_id, text=mensagem)
async def main():
    cotacao_euro()
    await relatorio()

if __name__ == "__main__":
    asyncio.run(main())