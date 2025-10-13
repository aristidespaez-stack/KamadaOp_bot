# Bot de producción Kamada

Requisitos:
- Python 3.9+
- pip install python-telegram-bot pandas matplotlib openpyxl

Variables:
- BOT_TOKEN en env

Comandos:
- /start /menu /sardina /mesa /linea /empaque /trabajadores /resumen /reporte_periodo

Flujo recomendado:
1. Cargar trabajadores con /trabajadores -> Ingresar lista.
2. Registrar producción por área.
3. Generar reportes por fecha o por periodo.