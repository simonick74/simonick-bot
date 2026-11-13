import logging
import io
import base64
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI

# --- INSERISCI QUI LE TUE CREDENZIALI ---
TELEGRAM_BOT_TOKEN = "9001457493:AAHb0oVPzHrxQonvTC5V9QqU3-oUA2cKrkI"
OPENROUTER_API_KEY = ""
# ----------------------------------------

# Inizializzazione del client OpenAI puntato su OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    timeout=30.0
)

SYSTEM_PROMPT = (
    "Sei Simonick (chiamato anche Giada), un'assistente esperta in nutrizione e benessere. "
    "Analizza i pasti e le richieste degli utenti con empatia, competenza e precisione scientifica in italiano."
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono Simonick, la tua assistente per la nutrizione. "
        "Puoi scrivermi o mandarmi la foto di un pasto per un'analisi dettagliata!"
    )

# Gestione dei messaggi di TESTO
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.effective_user.first_name
    
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash:free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Utente ({user_name}) ti scrive: {user_text}"}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Errore AI Testo: {e}")
        await update.message.reply_text("Scusami, ho avuto un piccolo problema a elaborare il messaggio.")

# Gestione delle FOTO (viste da Gemini via OpenRouter)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    caption = update.message.caption or "Nessuna didascalia"
    
    try:
        await update.message.reply_text("🔍 Sto analizzando il tuo piatto...")

        # Scarica la foto da Telegram
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Converte l'immagine in formato base64 per inviarla a OpenRouter
        base64_image = base64.b64encode(photo_bytes).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"

        response = client.chat.completions.create(
            model="google/gemini-2.5-flash:free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Utente ({user_name}) ti ha mandato la foto del suo pasto. Didascalia: {caption}. Valuta gli ingredienti e dai un riscontro nutrizionale."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        )
        
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Errore AI Foto: {e}")
        await update.message.reply_text("Scusami, non sono riuscita ad analizzare la foto, riprova più tardi.")

if __name__ == '__main__':
    token_pulito = TELEGRAM_BOT_TOKEN.strip()
    app = ApplicationBuilder().token(token_pulito).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Simonick (OpenRouter + Visione) è online e in ascolto su Telegram...")
    app.run_polling()