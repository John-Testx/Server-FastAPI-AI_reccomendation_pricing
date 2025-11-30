# Usamos Python 3.10-slim que es 100% compatible con google-cloud-sql-connector
FROM python:3.10-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar librerías criptográficas y de base de datos
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip para evitar errores con paquetes nuevos
RUN pip install --no-cache-dir --upgrade pip

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Comando de ejecución
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"