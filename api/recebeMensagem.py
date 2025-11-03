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


def callback_auto_message(context):
    print(context)
    context.bot.send_message(chat_id=context.chat_id, text='Automatic message!')
    
    
def start_auto_messaging(update, context):
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(callback_auto_message, 30, context=chat_id, name=str(chat_id))
  


TOKEN = os.environ.get("COTA_EURO_TELEGRAM_TOKEN")
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("auto", start_auto_messaging))
app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
async def webhook():
    return "ok"

# ====================
# ROTA PÚBLICA (opcional) para teste
# ====================
@app.route("/")
def index():
    return "Bot rodando!"