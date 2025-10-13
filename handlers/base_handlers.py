# handlers/base_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import validar_clave
from datetime import datetime

# Estados comunes (Se usan en todos los módulos de producción)
ESPERANDO_CLAVE, ESPERANDO_FECHA, ESPERANDO_EMPRESA, CONFIRMAR = range(4)

async def menu_base(update: Update, context: ContextTypes.DEFAULT_TYPE, area_name: str, area_key: str, state_clave: int):
    """Función de entrada base para todos los módulos de producción."""
    prompt = f"🔑 **{area_name}**\nIngrese la clave de acceso:"
    
    # Manejar mensaje o callback (si viene de un botón)
    if update.message:
        await update.message.reply_text(prompt)
    elif update.callback_query:
        await update.callback_query.edit_message_text(prompt)
    
    context.user_data["area_key"] = area_key # 'sardina', 'mesa', etc.
    context.user_data["area_name"] = area_name # 'Recepción de Sardinas', 'Mesa de Llenado', etc.
    return state_clave

async def recibir_clave_base(update: Update, context: ContextTypes.DEFAULT_TYPE, state_fecha: int):
    """Función para validar la clave de acceso."""
    area_key = context.user_data.get("area_key")
    if not validar_clave(area_key, update.message.text.strip()):
        await update.message.reply_text("❌ Clave incorrecta. Intente de nuevo:")
        return ConversationHandler.RETRY 
    
    await update.message.reply_text("📅 Ingrese la fecha de producción (**DD/MM/AAAA**):")
    return state_fecha

async def recibir_fecha_base(update: Update, context: ContextTypes.DEFAULT_TYPE, state_empresa: int):
    """Función para validar y guardar la fecha."""
    try:
        fecha_str = update.message.text.strip()
        # Validar y formatear la fecha a YYYY-MM-DD para la BD
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        context.user_data["fecha"] = fecha
    except ValueError:
        await update.message.reply_text("❌ **Formato de fecha inválido**. Use DD/MM/AAAA. Intente de nuevo:")
        return ConversationHandler.RETRY 
    
    kb = [[InlineKeyboardButton("Kamada", callback_data="empresa_Kamada")],
          [InlineKeyboardButton("Pariamar", callback_data="empresa_Pariamar")]]
    await update.message.reply_text("🏭 Seleccione la empresa de **fabricación**:", reply_markup=InlineKeyboardMarkup(kb))
    return state_empresa

async def recibir_empresa_base(update: Update, context: ContextTypes.DEFAULT_TYPE, next_state: int, prompt_text: str = None):
    """Función para guardar la empresa y pasar al siguiente estado específico."""
    q = update.callback_query
    await q.answer()
    context.user_data["empresa"] = q.data.split("_")[1] # Kamada o Pariamar
    
    if prompt_text:
        await q.edit_message_text(prompt_text)
    
    return next_state