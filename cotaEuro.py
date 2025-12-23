import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import threading
from datetime import datetime
from flask import Flask
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import conectaBanco as db
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

TOKEN = os.environ.get("COTA_EURO_TELEGRAM_TOKEN")
API_TOKEN  = os.environ.get("API_TOKEN")
TZ_BRASIL = ZoneInfo("America/Sao_Paulo")

def agora_brasil() -> datetime:
    return datetime.now(TZ_BRASIL)

async def esta_horario_comercial(chat_id, context) -> bool:
    agora = agora_brasil()
    dia_util = agora.weekday() < 6 # seg–sab
    horario = 8 <= agora.hour < 18
    if agora.hour == 18:
        passa_dados_para_eurodia()
    # Sexta-feira às 18h → gerar relatório semanal
    if agora.weekday() == 4 and agora.hour == 18:
        await gerar_relatorio(chat_id, context, 7)
    return dia_util and horario

# =========================
# Banco / Relatórios
# =========================


def passa_dados_para_eurodia():
    if db.colecao_tem_dados("euroHora"):
        df = db.criaRelatorio(1, "euroHora")
        # Converter apenas para exibição
        data_brasil = agora_brasil()
        media = df["valor"].mean()
        db.insereDados(data_brasil, media, "euroDia")
        db.deletaDados()


async def gerar_relatorio(chat_id, context, dias):
    if db.colecao_tem_dados("euroDia"):
        df = db.criaRelatorio(dias, "euroDia")
        db.gerar_grafico_euro(df)
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=buf,
            caption=f'Relatório referente aos ultimos {dias} dias'
        )
        
        return df

# =========================
# API de cotação
# =========================
async def cotacao_euro() -> str:
    url = f"https://api.fxratesapi.com/latest?api_key={API_TOKEN}&base=EUR&currencies=BRL&resolution=1m"

    headers = {"User-Agent": "Mozilla/5.0 (TelegramBot/1.0)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()


        data = response.json()
        valor = data["rates"]["BRL"]


        # Data UTC da API
        data_utc = datetime.strptime(
        data["date"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=timezone.utc)


        # Converter apenas para exibição
        data_brasil = data_utc.astimezone(TZ_BRASIL)


        # Persistência (salvar datetime, não string)
        db.insereDados(data_brasil, valor, "euroHora")


        data_exibicao = data_brasil.strftime("%d/%m/%Y - %H:%M")
        return f"{data_exibicao}\n💶 Euro: R$ {valor:.2f}"


    except Exception as e:
        return f"❌ Erro ao buscar cotação: {e}"
    
# =========================
# Jobs do Telegram
# =========================


async def callback_auto_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job


    if not esta_horario_comercial(job.data, context):
        return


    mensagem = await cotacao_euro()
    await context.bot.send_message(chat_id=job.data, text=mensagem)
    
# =========================
# Comandos do Bot
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id


    # Remove jobs existentes
    for job in context.job_queue.get_jobs_by_name(str(chat_id)):
        job.schedule_removal()

    context.job_queue.run_repeating(
        callback_auto_message,
        interval=900,
        first=0,
        data=chat_id,
        name=str(chat_id),
        )


    await update.message.reply_text(
    "✅ Bot iniciado! Enviarei a cotação a cada 15 minutos (horário comercial)."
    )
    
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))


    if not jobs:
        await update.message.reply_text("ℹ️ Não há tarefas ativas.")
        return

    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("🛑 Ok! Parei de enviar mensagens.")

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Validar argumento
    if not context.args:
        await update.message.reply_text(
            "❗ Use assim: /relatorio <número_de_dias>\nExemplo: /relatorio 7"
        )
        return

    try:
        dias = int(context.args[0])
        if dias <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Informe um número inteiro válido de dias.")
        return

    # Verificar se há dados
    if not db.colecao_tem_dados("euroHora"):
        await update.message.reply_text("⚠️ Ainda não há dados suficientes.")
        return

    # Criar relatório
    df = gerar_relatorio(chat_id, context, dias)

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
    
    await context.bot.send_message(chat_id=chat_id, text=mensagem)
# =========================
# Flask (healthcheck Render)
# =========================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot de cotação do Euro rodando 🚀", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# =========================
# Main
# =========================
def main():
# Flask em thread separada
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.bot.delete_webhook(drop_pending_updates=True)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("relatorio", relatorio))

    
    print("🤖 Bot rodando...")
    try:
        app.run_polling()
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("Loop encerrado pelo sistema. Ignorando…")
        else:
            raise

if __name__ == "__main__":
    main()
