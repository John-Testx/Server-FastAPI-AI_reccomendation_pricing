# 1. Usar una imagen base oficial de Python 3.10
FROM python:3.10-slim

# 2. Configurar directorio de trabajo
WORKDIR /app

# 3. Instalar dependencias del sistema
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

# --- NUEVO PASO: Actualizar pip a la última versión ---
RUN pip install --upgrade pip

# 4. Copiar y instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código
COPY . .

# 6. Comando de inicio
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"