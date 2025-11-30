# 1. Usar Python 3.11 oficial (Mejor compatibilidad que 3.10 para librerías de Google recientes)
FROM python:3.11-slim

# 2. Configurar directorio de trabajo
WORKDIR /app

# 3. Instalar dependencias del sistema (necesarias para compilar scikit-learn y mysql)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 4. ACTUALIZAR PIP (Este paso es el que faltaba/fallaba antes)
# Usamos --root-user-action=ignore para evitar advertencias de root
RUN pip install --no-cache-dir --upgrade pip

# 5. Copiar e instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el resto del código
COPY . .

# 7. Comando de inicio
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"