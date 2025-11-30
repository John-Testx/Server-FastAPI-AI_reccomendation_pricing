# 1. Usar una imagen base oficial de Python 3.10 (Compatible con todas tus librerías)
FROM python:3.10-slim

# 2. Configurar directorio de trabajo
WORKDIR /app

# 3. Instalar dependencias del sistema (necesarias para compilar algunas librerías)
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

# 4. Copiar y instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código
COPY . .

# 6. Comando de inicio (Railway inyecta la variable $PORT)
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"