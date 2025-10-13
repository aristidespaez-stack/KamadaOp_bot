# handlers/resumen_por_fecha.py
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup 
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters
from database import obtener_registros_por_fecha
from config import validar_clave

ESPERANDO_CLAVE, ESPERANDO_FECHA = range(2)

async def resumen(update: Update, context):
    if update.message:
        await update.message.reply_text("🔑 Ingrese la clave de reportes:")
    else:
        await update.callback_query.message.edit_text("🔑 Ingrese la clave de reportes:")
    return ESPERANDO_CLAVE

async def recibir_clave(update: Update, context):
    if not validar_clave("reportes", update.message.text.strip()):
        await update.message.reply_text("Clave incorrecta.")
        return ESPERANDO_CLAVE
    await update.message.reply_text("Ingrese fecha (DD/MM/AAAA):")
    return ESPERANDO_FECHA

async def recibir_fecha(update: Update, context):
    try:
        fecha = pd.to_datetime(update.message.text.strip(), dayfirst=True).strftime("%Y-%m-%d")
    except:
        await update.message.reply_text("Formato inválido.")
        return ESPERANDO_FECHA
    rows = obtener_registros_por_fecha(fecha)
    if not rows:
        await update.message.reply_text("No hay registros para esa fecha.")
        return ConversationHandler.END
        
    # COLUMNAS CORREGIDAS: Incluye 'Trabajador ID' y excluye 'ResponsableID'
    df = pd.DataFrame(rows, columns=["Fecha","Area","Empresa","Tipo","Cantidad","Trabajador ID","Nombre"])
    excel_path = f"resumen_{fecha}.xlsx"
    df.to_excel(excel_path, index=False)
    
    fig, ax = plt.subplots(figsize=(10, max(2, len(df)*0.3)))
    ax.axis('off')
    tabla = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='left', loc='center')
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(8)
    tabla.scale(1, 1.2)
    jpg_path = f"resumen_{fecha}.jpg"
    plt.savefig(jpg_path, bbox_inches='tight')
    
    await update.message.reply_text("📊 Reporte generado.")
    await update.message.reply_document(open(excel_path, "rb"))
    await update.message.reply_photo(open(jpg_path, "rb"))
    
    # NUEVO: Botón de volver al menú
    kb = [[InlineKeyboardButton("🏠 Menú", callback_data="/menu")]]
    await update.message.reply_text("✅ Operación finalizada.", reply_markup=InlineKeyboardMarkup(kb))
    
    return ConversationHandler.END

def build_resumen_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("resumen", resumen)],
        states={
            ESPERANDO_CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_clave)],
            ESPERANDO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha)],
        },
        fallbacks=[CommandHandler("cancel", resumen)]
    )