import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
TOKEN = os.environ.get("COTA_EURO_TELEGRAM_TOKEN")

API_TOKEN  = os.environ.get("API_TOKEN")

async def cotacao_euro():
    url = f"http://economia.awesomeapi.com.br/json/last/EUR-BRL?token={API_TOKEN}"
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)    
    resposta = response.json()['EURBRL']
    cria_retorno = f"Agora {resposta['create_date']} \n  O Euro está R${resposta['ask']} \n"
    cria_retorno += f"Hoje, o Euro esteve entre R${resposta['low']} e R${resposta['high']}"

    return cria_retorno

async def callback_auto_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.data, text=cotacao_euro)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        callback_auto_message,
        interval=120,
        first=0,
        data=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text("Bot iniciado! Enviarei mensagens a cada 2 minutos.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not jobs:
        await update.message.reply_text("Não há tarefas ativas.")
        return

    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("Mensagens automáticas paradas.")

def main():
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
