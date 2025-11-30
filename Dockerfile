# 1. Usar Python 3.10 (Estabilidad máxima para librerías de Google y Scikit)
FROM python:3.10-slim

# 2. Configurar directorio
WORKDIR /app

# 3. Instalar dependencias de sistema CRÍTICAS
# Añadimos libffi-dev y libssl-dev para evitar fallos con criptografía/conexiones
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. ACTUALIZACIÓN FORZADA DE PIP
# Esto es vital para que pueda descargar las versiones modernas de las librerías
RUN pip install --no-cache-dir --upgrade pip

# 5. Copiar e instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el código
COPY . .

# 7. Ejecutar
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"