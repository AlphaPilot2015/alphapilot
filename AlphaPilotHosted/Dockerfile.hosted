# ====== Etapa 1: Python + deps ======
FROM python:3.11-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# ====== Etapa 2: Nginx + Supervisor + Python ======
FROM debian:12-slim AS stage-1
RUN apt-get update && apt-get install -y --no-install-recommends \
      nginx supervisor python3 ca-certificates gettext-base \
    && rm -rf /var/lib/apt/lists/*

COPY --from=api /usr/local /usr/local
COPY --from=api /app /app
COPY frontend /var/www/html
COPY infra/nginx.tmpl.conf /etc/nginx/nginx.tmpl.conf
COPY infra/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh
ENV PORT=8080
EXPOSE 8080
CMD ["/start.sh"]
