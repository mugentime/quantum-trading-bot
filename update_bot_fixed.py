#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script limpio para actualizar el bot con conexion real a Binance
NO crea archivos adicionales, solo actualiza los existentes
"""

import os
import sys
import shutil
from datetime import datetime

print("=" * 60)
print("ACTUALIZADOR LIMPIO DEL BOT")
print("=" * 60)

# Verificar que estamos en el directorio correcto
if not os.path.exists('core/data_collector.py'):
    print("ERROR: Ejecuta este script desde la carpeta quantum_trading_bot")
    sys.exit(1)

# Hacer backup de los archivos originales
backup_dir = '.backups'
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
    print(f"Creado directorio de backups: {backup_dir}")

# Lista de archivos a actualizar
files_to_backup = [
    'core/data_collector.py',
    'core/correlation_engine.py', 
    'core/signal_generator.py'
]

# Hacer backup solo si no existe
for file in files_to_backup:
    backup_file = os.path.join(backup_dir, file.replace('/', '_') + '.original')
    if not os.path.exists(backup_file) and os.path.exists(file):
        shutil.copy2(file, backup_file)
        print(f"Backup creado: {backup_file}")

print("\nActualizando archivos del bot...")
print("Por favor espera...")
