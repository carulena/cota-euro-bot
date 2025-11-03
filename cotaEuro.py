import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
TOKEN = os.environ.get("COTA_EURO_TELEGRAM_TOKEN")

async def cotacao_euro():
    url = "http://economia.awesomeapi.com.br/json/last/EUR-BRL"
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json['ask']
async def callback_auto_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.data, text=cotacao_euro())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        callback_auto_message,
        interval=30,
        first=0,
        data=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text("Bot iniciado! Enviarei mensagens a cada 30 segundos.")

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
    asyncio.run(app.bot.delete_webhook(drop_pending_updates=True))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    print("Bot rodando no Render...")
    app.run_polling()

if __name__ == "__main__":
    main()
