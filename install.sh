#!/bin/bash

echo "======================================"
echo "  QUANTUM TRADING BOT - INSTALACION"
echo "======================================"
echo ""

echo "[1/5] Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

echo "[2/5] Actualizando pip..."
pip install --upgrade pip

echo "[3/5] Instalando dependencias..."
pip install -r requirements.txt

echo "[4/5] Creando archivo .env..."
cp .env.example .env

echo "[5/5] Creando directorios..."
mkdir -p logs data backtest_results

echo ""
echo "======================================"
echo "  INSTALACION COMPLETA!"
echo "======================================"
echo ""
echo "Siguientes pasos:"
echo "1. Edita el archivo .env con tus API keys de Binance"
echo "2. Ejecuta: python main.py"
echo ""
