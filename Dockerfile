# Python Dockerfile para la aplicación de Boosting

FROM python:3.12-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalamos dependencias del sistema para Tkinter, Gráficos y EMOJIS 🚀
RUN apt-get update && apt-get install -y \
    python3-tk \
    tk-dev \
    libx11-6 \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

#requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia proyecto
COPY . .

# Comando para arrancar la app
CMD ["python", "main.py"]