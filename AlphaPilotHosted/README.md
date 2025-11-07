# AlphaPilot (Hosted Starter)

Este paquete está listo para desplegarse en **Render** (o Railway/Zeabur) con un solo contenedor que incluye:
- **API FastAPI** (Uvicorn)
- **Frontend estático** (Nginx)
- **Supervisord** para orquestar los procesos

## Despliegue en Render (paso a paso)
1. Sube este contenido a un repositorio de GitHub (público).
2. Entra a https://render.com → New → Web Service → conecta tu repo.
3. Runtime: **Docker**. Dockerfile path: `Dockerfile.hosted`.
4. Variables (opcional, Render no requiere ninguna para esta versión starter).
5. Crea el servicio → espera a que construya → **Open app**.

Tu app quedará publicada en una URL tipo: `https://tuservicio.onrender.com`.

## Desarrollo local (opcional)
```bash
# Construir y correr localmente
docker build -f Dockerfile.hosted -t alphapilot-hosted .
docker run -p 8080:8080 alphapilot-hosted
# Abre: http://localhost:8080
```

## Aviso importante
Este starter es didáctico. Para operar con dinero real:
- Debes integrar las APIs de tu bróker (por ejemplo Alpaca) con autenticación, KYC y cumplimiento normativo.
- Nunca prometas rendimientos garantizados; la inversión implica riesgo.
