# ===== Stage 1: build del runtime con Python + deps del sistema =====
FROM python:3.11-slim AS base

# Paquetes que necesitamos (nginx, supervisor, utilidades)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor gettext-base ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*

# Crear directorios destino
WORKDIR /app
RUN mkdir -p /var/www/html /etc/nginx /etc/supervisor/conf.d

# ===== Stage 2: copiar tu código =====
# Copiamos backend
COPY app /app/app
# Si tuvieras requirements.txt, descomenta:
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r /app/requirements.txt
# (para tu demo sin deps extras, FastAPI & Uvicorn ya están en la imagen base si los añades)
RUN pip install --no-cache-dir fastapi uvicorn

# Copiamos frontend estático
COPY frontend /var/www/html

# Copiamos configs y start
COPY infra/nginx.tmpl.conf /etc/nginx/nginx.tmpl.conf
COPY infra/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Variables requeridas por Render
ENV PORT=8080

# Exponemos el puerto
EXPOSE 8080

# Arranque
CMD ["/start.sh"]
