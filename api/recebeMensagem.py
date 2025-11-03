import os
from http.server import BaseHTTPRequestHandler
 
# Configura o matplotlib para rodar em /tmp (Vercel serverless)
os.environ['MPLCONFIGDIR'] = '/tmp'
from io import BytesIO
from telegram import Update, Bot
from flask import Flask, request
import zipfile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
import datetime


TOKEN = os.environ.get("COTA_EURO_TELEGRAM_TOKEN")
telegram_app = ApplicationBuilder().token(TOKEN).build()
app = Flask(__name__)


async def callback_auto_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.context, text="Mensagem automática 🔁")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Se já existir um job pra esse chat, remove primeiro
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # Cria o job que roda a cada 30 segundos
    context.job_queue.run_repeating(
        callback_auto_message,
        interval=30,      # segundos
        first=0,          # envia imediatamente
        context=chat_id,
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

    await update.message.reply_text("Mensagens automáticas paradas. 🚫")
def callback_auto_message(context):
    print(context)
    context.bot.send_message(chat_id=context.chat_id, text='Automatic message!')
    

@app.route("/webhook", methods=["POST"])
async def webhook():
    return "ok"

# ====================
# ROTA PÚBLICA
# ====================
@app.route("/")
def index():
    
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("stop", stop))
    
    print("Bot rodando...")
    app.run_polling()

    return "Bot rodando!"