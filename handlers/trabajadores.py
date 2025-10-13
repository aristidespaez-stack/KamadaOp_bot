# handlers/trabajadores.py
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)
from database import upsert_trabajador
from config import validar_clave, es_admin
import io

ESPERANDO_CLAVE, ESPERANDO_EXCEL = range(2)

async def menu_trabajadores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not es_admin(user_id):
        await update.message.reply_text("⛔ Acceso denegado. Solo los administradores pueden gestionar trabajadores.")
        return ConversationHandler.END
        
    await update.message.reply_text("🔑 Ingrese la clave de acceso para gestión de trabajadores:")
    return ESPERANDO_CLAVE

async def recibir_clave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not validar_clave("trabajadores", update.message.text.strip()):
        await update.message.reply_text("❌ Clave incorrecta. Intente de nuevo:")
        return ESPERANDO_CLAVE
        
    msg = ("📄 Adjunte el archivo **Excel (.xlsx)** con la lista de trabajadores.\n"
           "**Requisitos del archivo:**\n"
           "1. Debe tener una columna llamada **'ID'** (con el ID numérico).\n"
           "2. Debe tener una columna llamada **'Nombre'** (con el nombre completo).")
    await update.message.reply_text(msg)
    return ESPERANDO_EXCEL

async def recibir_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo acepta archivos .xlsx
    if not update.message.document or not update.message.document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ Por favor, envíe un archivo con extensión **.xlsx** o **.xls**.")
        return ESPERANDO_EXCEL
    
    file_id = update.message.document.file_id
    file_info = await context.bot.get_file(file_id)
    file_bytes = io.BytesIO()
    await file_info.download_to_memory(file_bytes)
    file_bytes.seek(0)
    
    try:
        df = pd.read_excel(file_bytes)
        
        # Validación de columnas
        if 'ID' not in df.columns or 'Nombre' not in df.columns:
            await update.message.reply_text("❌ El archivo Excel debe contener las columnas **'ID'** y **'Nombre'**.")
            return ESPERANDO_EXCEL
            
        # Limpieza de datos
        df = df[['ID', 'Nombre']].dropna()
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(-1).astype(int)
        df = df[df['ID'] > 0]
        
        if df.empty:
             await update.message.reply_text("❌ No se encontraron filas con IDs válidos y nombres. Verifique los datos.")
             return ESPERANDO_EXCEL

        # UPSERT en la base de datos
        count = 0
        for index, row in df.iterrows():
            upsert_trabajador(row['ID'], row['Nombre'])
            count += 1
            
        msg = f"✅ ¡Carga de trabajadores realizada con éxito! Se **insertaron/actualizaron {count}** registros.\n"
        await update.message.reply_text(msg, 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menú Principal", callback_data="/menu")]]))
        
        return ConversationHandler.END
    
    except Exception as e:
        await update.message.reply_text(f"❌ Ocurrió un error al procesar el archivo: {e}\nPor favor, revise el formato.")
        return ESPERANDO_EXCEL

def build_trabajadores_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("trabajadores", menu_trabajadores)],
        states={
            ESPERANDO_CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_clave)],
            ESPERANDO_EXCEL: [MessageHandler(filters.ATTACHMENT, recibir_excel)]
        },
        fallbacks=[CommandHandler("cancel", menu_trabajadores)]
    )