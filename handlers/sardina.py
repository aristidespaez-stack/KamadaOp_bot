# handlers/sardina.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from config import validar_clave
from database import agregar_registro
from datetime import datetime

# Definición de estados
ESPERANDO_CLAVE, ESPERANDO_FECHA, ESPERANDO_EMPRESA, ESPERANDO_PROVEEDOR, ESPERANDO_CESTAS, ESPERANDO_KG, ESPERANDO_ID_TRABAJADOR, CONFIRMAR = range(8)

async def menu_sardina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("🔑 Ingrese la clave de acceso para Sardina:")
    else:
        await update.callback_query.message.edit_text("🔑 Ingrese la clave de acceso para Sardina:")
    return ESPERANDO_CLAVE

async def recibir_clave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not validar_clave("sardina", update.message.text.strip()):
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
    await update.message.reply_text("🏭 Seleccione la empresa que compra:", reply_markup=InlineKeyboardMarkup(kb))
    return ESPERANDO_EMPRESA

async def recibir_empresa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['empresa'] = query.data
    
    await query.edit_message_text("🚛 Ingrese el nombre del **Proveedor de Sardinas**:")
    return ESPERANDO_PROVEEDOR 

async def recibir_proveedor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    proveedor = update.message.text.strip()
    if not proveedor:
        await update.message.reply_text("El nombre del proveedor no puede estar vacío. Ingrese el proveedor:")
        return ESPERANDO_PROVEEDOR
        
    context.user_data['proveedor'] = proveedor
    await update.message.reply_text("🐟 Ingrese la cantidad de **Cestas** recibidas (solo números enteros positivos):")
    return ESPERANDO_CESTAS

async def recibir_cestas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cestas = int(update.message.text.strip())
        if cestas <= 0:
            raise ValueError
        context.user_data['cestas'] = cestas
    except ValueError:
        await update.message.reply_text("❌ Cantidad inválida. Ingrese el número de cestas (solo números enteros positivos):")
        return ESPERANDO_CESTAS
        
    await update.message.reply_text("⚖️ Ingrese la cantidad de **Kg** recibidos (solo números positivos, puede usar decimales):")
    return ESPERANDO_KG

async def recibir_kg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # CAMBIO: Usar float() para permitir decimales
        kg = float(update.message.text.strip())
        if kg <= 0:
            raise ValueError
        context.user_data['kg'] = kg
    except ValueError:
        # Mensaje de error actualizado
        await update.message.reply_text("❌ Cantidad inválida. Ingrese la cantidad de Kg (solo números positivos, puede usar decimales):")
        return ESPERANDO_KG
        
    await update.message.reply_text("👤 Ingrese el **ID del Trabajador** que recibió la sardina (solo números enteros):")
    return ESPERANDO_ID_TRABAJADOR

async def recibir_id_trabajador(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        trabajador_id = int(update.message.text.strip())
        if trabajador_id <= 0:
            raise ValueError
        context.user_data['trabajador_id'] = trabajador_id
    except ValueError:
        await update.message.reply_text("❌ ID inválido. Ingrese el ID del trabajador (solo números enteros positivos):")
        return ESPERANDO_ID_TRABAJADOR
    
    d = context.user_data
    resumen = (
        f"**Confirme el Registro de Sardina:**\n"
        f"Fecha: {d['fecha']}\n"
        f"Empresa: {d['empresa']}\n"
        f"Proveedor: {d['proveedor']}\n" 
        f"Cestas: {d['cestas']}\n"
        f"Kg: {d['kg']}\n"
        f"ID Trabajador (Receptor): {d['trabajador_id']}\n" 
        f"ID Responsable (Supervisor): {d['responsable_registro']}\n" 
    )
    kb = [
        [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_si")],
        [InlineKeyboardButton("✏️ Editar", callback_data="editar_carga_sardina")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="confirmar_no")]
    ]
    await update.message.reply_text(resumen, reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRMAR

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    if q.data == "editar_carga_sardina": 
        await q.edit_message_text("✏️ Editando la carga de Sardina. Ingrese la fecha (DD/MM/AAAA):")
        return ESPERANDO_FECHA
        
    if q.data == "confirmar_si":
        d = context.user_data
        
        agregar_registro(
            trabajador_id=d["trabajador_id"],
            area="Sardina", 
            empresa=d["empresa"], 
            cantidad=d["kg"], # Se pasa como float a la función (aunque la DB use INTEGER)
            responsable_id=d["responsable_registro"],
            tipo=d["proveedor"], 
            cantidad_auxiliar=d["cestas"],
            fecha=d["fecha"]
        )
        
        await q.edit_message_text("✅ Registro guardado.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menú", callback_data="/menu")]]))
    else:
        await q.edit_message_text("❌ Registro cancelado.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menú", callback_data="/menu")]]))
    return ConversationHandler.END

def build_sardina_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("sardina", menu_sardina)],
        states={
            ESPERANDO_CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_clave)],
            ESPERANDO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha)],
            ESPERANDO_EMPRESA: [CallbackQueryHandler(recibir_empresa)],
            ESPERANDO_PROVEEDOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_proveedor)], 
            ESPERANDO_CESTAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cestas)],
            ESPERANDO_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_kg)],
            ESPERANDO_ID_TRABAJADOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_id_trabajador)], 
            CONFIRMAR: [CallbackQueryHandler(confirmar)],
        },
        fallbacks=[CommandHandler("cancel", confirmar)]
    )