# handlers/linea.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)
from config import validar_clave
from database import agregar_registro
from datetime import datetime

ESPERANDO_CLAVE, ESPERANDO_FECHA, ESPERANDO_EMPRESA, ESPERANDO_TIPO, ESPERANDO_IDS, ESPERANDO_CAJA, CONFIRMAR = range(7)

async def menu_linea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("🔑 Ingrese la clave de acceso para Línea:")
    else:
        await update.callback_query.message.edit_text("🔑 Ingrese la clave de acceso para Línea:")
    return ESPERANDO_CLAVE

async def recibir_clave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not validar_clave("linea", update.message.text.strip()):
        await update.message.reply_text("❌ Clave incorrecta. Ingrese la clave nuevamente:")
        return ESPERANDO_CLAVE
    
    context.user_data['responsable_registro'] = update.effective_user.id
    await update.message.reply_text("📅 Ingrese la fecha (DD/MM/AAAA):")
    return ESPERANDO_FECHA

async def recibir_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        fecha = datetime.strptime(update.message.text.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
        context.user_data['fecha'] = fecha
    except ValueError:
        await update.message.reply_text("❌ Formato de fecha inválido. Use DD/MM/AAAA.")
        return ESPERANDO_FECHA

    kb = [
        [InlineKeyboardButton("Kamada", callback_data="Kamada")],
        [InlineKeyboardButton("Pariamar", callback_data="Pariamar")]
    ]
    await update.message.reply_text("🏭 Seleccione la empresa que fabrica:", reply_markup=InlineKeyboardMarkup(kb))
    return ESPERANDO_EMPRESA

async def recibir_empresa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['empresa'] = query.data
    
    kb = [
        [InlineKeyboardButton("Tomate", callback_data="Tomate")],
        [InlineKeyboardButton("Aceite", callback_data="Aceite")]
    ]
    await query.edit_message_text("🥫 Seleccione el tipo de producción:", reply_markup=InlineKeyboardMarkup(kb))
    return ESPERANDO_TIPO

async def recibir_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['tipo'] = query.data
    
    await query.edit_message_text("👥 Ingrese los **IDs de los trabajadores** separados por coma (ej: 12, 34, 56):")
    return ESPERANDO_IDS

async def recibir_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ids = [int(x.strip()) for x in update.message.text.split(",") if x.strip().isdigit()]
        if not ids:
            raise ValueError
        context.user_data['ids'] = ids
    except ValueError:
        await update.message.reply_text("❌ IDs inválidos. Ingrese los IDs separados por coma (solo números enteros):")
        return ESPERANDO_IDS
        
    await update.message.reply_text("📦 Ingrese la cantidad de **cajas** producidas (solo números enteros positivos):")
    return ESPERANDO_CAJA

async def recibir_caja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cajas = int(update.message.text.strip())
        if cajas <= 0:
            raise ValueError
        context.user_data['cantidad'] = cajas
    except ValueError:
        await update.message.reply_text("❌ Cantidad inválida. Ingrese el número de cajas (solo números enteros positivos):")
        return ESPERANDO_CAJA
        
    d = context.user_data
    resumen = (
        f"**Confirme el Registro de Línea de Producción:**\n"
        f"Fecha: {d['fecha']}\n"
        f"Empresa: {d['empresa']}\n"
        f"Tipo: {d['tipo']}\n"
        f"Trabajadores ID: {', '.join(map(str, d['ids']))}\n"
        f"Cajas producidas: {d['cantidad']}\n"
        f"ID Responsable: {d['responsable_registro']}\n"
    )
    kb = [
        [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_si")],
        [InlineKeyboardButton("✏️ Editar", callback_data="editar_carga_linea")], 
        [InlineKeyboardButton("❌ Cancelar", callback_data="confirmar_no")]
    ]
    await update.message.reply_text(resumen, reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRMAR

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    if q.data == "editar_carga_linea": 
        await q.edit_message_text("✏️ Editando la carga de Línea. Ingrese la fecha (DD/MM/AAAA):")
        return ESPERANDO_FECHA
        
    d = context.user_data
    if q.data=="confirmar_si":
        for tid in d["ids"]:
            agregar_registro(
                trabajador_id=tid, 
                area="Línea", 
                empresa=d["empresa"], 
                cantidad=d["cantidad"], 
                responsable_id=d["responsable_registro"], 
                cantidad_auxiliar=None, 
                tipo=d["tipo"], 
                fecha=d["fecha"]
            )
        await q.edit_message_text("✅ Registro guardado.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menú", callback_data="/menu")]]))
    else:
        await q.edit_message_text("❌ Cancelado.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menú", callback_data="/menu")]]))
        
    return ConversationHandler.END

def build_linea_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("linea", menu_linea)],
        states={
            ESPERANDO_CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_clave)],
            ESPERANDO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha)],
            ESPERANDO_EMPRESA: [CallbackQueryHandler(recibir_empresa)],
            ESPERANDO_TIPO: [CallbackQueryHandler(recibir_tipo)],
            ESPERANDO_IDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ids)],
            ESPERANDO_CAJA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_caja)],
            CONFIRMAR: [CallbackQueryHandler(confirmar)],
        },
        fallbacks=[CommandHandler("cancel", confirmar)]
    )