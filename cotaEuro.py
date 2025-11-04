import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import pytz 
import threading
from datetime import datetime
from flask import Flask
from datetime import date, timedelta
from zoneinfo import ZoneInfo

TOKEN = os.environ.get("COTA_EURO_TELEGRAM_TOKEN")

API_TOKEN  = os.environ.get("API_TOKEN")

def esta_horario_comercial():
    brasil_tz = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(brasil_tz)
    dia_util = agora.weekday() < 5
    horario_comercial = 8 <= agora.hour < 18
    return dia_util and horario_comercial

async def cotacao_euro():
    url = f"https://api.fxratesapi.com/latest?api_key={API_TOKEN}&base=EUR&currencies=BRL&resolution=1m"
    payload = {}
    headers = {"User-Agent": "Mozilla/5.0 (TelegramBot/1.0)"}
    response = requests.request("GET", url, headers=headers, data=payload)
    
    try:
        responseJson = response.json()
        valor = responseJson['rates']['BRL']
        data = datetime.strptime(responseJson['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        data_brasil = data.astimezone(ZoneInfo("America/Sao_Paulo")).strftime('%d/%m/%y - %H:%M')
        # cria_retorno = ''
        
        # if euro_atual != 0 and euro_atual < float(valor):
        #     cria_retorno = f'O EURO SUBIU 😓 \n anterior estava R${euro_atual}\n'
        # elif euro_atual != 0 and euro_atual > float(valor):
        #     cria_retorno = f'O EURO CAIU 😁 \n anterior estava R${euro_atual}\n'
            
        # euro_atual = float(valor)
        cria_retorno = f"{data_brasil} \n O Euro está R${valor:.2f}"
        return cria_retorno
    except Exception as e:  
        return f"API de cotação retornou {response.status_code} - erro {e} \n por favor verifique"
    
async def callback_auto_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    horario_comercial = esta_horario_comercial()
    if(horario_comercial):
        mensagem = await cotacao_euro()
        await context.bot.send_message(chat_id=job.data, text=mensagem)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        callback_auto_message,
        interval=900,
        first=0,
        data=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text("Bot iniciado! Enviarei mensagens a cada 15 minutos (em dias e horários comerciais),")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not jobs:
        await update.message.reply_text("Não há tarefas ativas.")
        return

    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("Ta bom, mas não se irrite 😓")

app_flask = Flask(__name__)


@app_flask.route('/')
def home():
    return "Bot de cotação do Euro está rodando no Render!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.bot.delete_webhook(drop_pending_updates=True)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    
    print("Bot rodando no Render...")
    try:
        app.run_polling()
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("Loop encerrado pelo sistema (Render reiniciou o container). Ignorando...")
        else:
            raise

if __name__ == "__main__":
    main()