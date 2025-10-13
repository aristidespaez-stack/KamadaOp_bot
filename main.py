# main.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
from database import init_db
from config import autorizado, es_admin, ADMINISTRADORES, agregar_usuario_autorizado, remover_usuario_autorizado # Importar nuevas funciones
import logging

# Configuración básica de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# handlers
from handlers.sardina import build_sardina_handler
from handlers.mesa import build_mesa_handler
from handlers.linea import build_linea_handler
from handlers.empaque import build_empaque_handler
from handlers.trabajadores import build_trabajadores_handler
from handlers.resumen_por_fecha import build_resumen_handler
from handlers.reporte_periodo import build_reporte_periodo_handler

TOKEN = os.getenv("BOT_TOKEN", "8213379352:AAHg4aGI2EownzzRy-7yCFxTJD3ml2XHRFs")

def _menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐟 Sardina", callback_data="/sardina")],
        [InlineKeyboardButton("🍽️ Mesa", callback_data="/mesa")],
        [InlineKeyboardButton("🏭 Línea", callback_data="/linea")],
        [InlineKeyboardButton("📦 Empaque", callback_data="/empaque")],
        [InlineKeyboardButton("📊 Resumen por fecha", callback_data="/resumen")],
        [InlineKeyboardButton("📈 Reporte por periodo", callback_data="/reporte_periodo")],
        [InlineKeyboardButton("👥 Trabajadores", callback_data="/trabajadores")]
    ])

# NUEVA FUNCIÓN: Envía la solicitud al administrador
async def enviar_solicitud_acceso(application, solicitante_id, username):
    for admin_id in ADMINISTRADORES:
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Autorizar", callback_data=f"auth_approve_{solicitante_id}")],
                [InlineKeyboardButton("❌ Rechazar", callback_data=f"auth_reject_{solicitante_id}")]
            ])
            mensaje = f"🔔 **SOLICITUD DE ACCESO**\nUsuario: @{username} (ID: `{solicitante_id}`)\n¿Desea autorizarlo?"
            await application.bot.send_message(
                chat_id=admin_id,
                text=mensaje,
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"No se pudo enviar la solicitud al admin {admin_id}: {e}")

# Manejadores de /start y /menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if autorizado(user_id):
        await update.message.reply_text("📋 Menú principal", reply_markup=_menu_keyboard())
    else:
        # Si no está autorizado, informa al usuario y envía una solicitud al administrador
        await update.message.reply_text("❌ No autorizado. Su solicitud de acceso ha sido enviada al administrador.")
        await enviar_solicitud_acceso(context.application, user_id, user.username or "N/A")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not autorizado(user_id):
        await update.message.reply_text("❌ No autorizado. Por favor, use /start para solicitar acceso.")
        return
        
    await update.message.reply_text("📋 Menú principal", reply_markup=_menu_keyboard())

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not autorizado(user_id):
        await query.message.reply_text("❌ No autorizado. Por favor, use /start para solicitar acceso.")
        return
        
    # Enviar el comando para iniciar el handler correspondiente
    await query.message.chat.send_message(query.data)

# NUEVA FUNCIÓN: Maneja la respuesta del administrador (Aprobar/Rechazar)
async def handle_autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    admin_id = update.effective_user.id
    if not es_admin(admin_id):
        await query.edit_message_text("❌ Sólo los administradores pueden gestionar accesos.")
        return
        
    # Parsear el callback_data: auth_[approve/reject]_[user_id]
    action, _, target_id = query.data.split('_')
    target_id = int(target_id)
    
    # Intentar obtener el nombre de usuario (opcional, para el mensaje de confirmación)
    try:
        target_user = await context.application.bot.get_chat(target_id)
        target_username = target_user.username or f"ID: {target_id}"
    except Exception:
        target_username = f"ID: {target_id}"

    
    if action == "auth" and query.data.startswith("auth_approve"):
        # Autorizar y notificar al usuario y al administrador
        agregar_usuario_autorizado(target_id)
        
        # Mensaje al administrador (edita el mensaje de solicitud)
        await query.edit_message_text(f"✅ Acceso APROBADO para @{target_username}.")
        
        # Notificar al usuario (opcional)
        try:
            await context.application.bot.send_message(
                chat_id=target_id, 
                text="🎉 ¡Felicidades! El administrador ha APROBADO tu acceso. Usa /start para entrar al menú.",
                reply_markup=_menu_keyboard()
            )
        except Exception:
            # Esto puede fallar si el usuario bloqueó el bot
            pass 
            
    elif action == "auth" and query.data.startswith("auth_reject"):
        # Rechazar y notificar al administrador
        remover_usuario_autorizado(target_id)
        
        # Mensaje al administrador (edita el mensaje de solicitud)
        await query.edit_message_text(f"❌ Acceso RECHAZADO para @{target_username}.")
        
        # Notificar al usuario (opcional)
        try:
             await context.application.bot.send_message(
                chat_id=target_id, 
                text="❌ Lamentablemente, tu solicitud de acceso ha sido RECHAZADA por el administrador."
            )
        except Exception:
            pass

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos base con chequeo de autorización
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))

    # Manejador de la autorización (debe ir antes que el menu_callback)
    app.add_handler(CallbackQueryHandler(handle_autorizacion, pattern="^auth_"))

    # Callback menu principal (envía el comando correspondiente)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^/.*$"))

    # ConversationHandlers
    app.add_handler(build_sardina_handler())
    app.add_handler(build_mesa_handler())
    app.add_handler(build_linea_handler())
    app.add_handler(build_empaque_handler())
    app.add_handler(build_trabajadores_handler())
    app.add_handler(build_resumen_handler())
    app.add_handler(build_reporte_periodo_handler())

    app.run_polling()

if __name__ == "__main__":
    main()