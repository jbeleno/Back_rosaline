# Checklist de adaptación para producción (AWS EC2)

1. **Variables sensibles**
   - [ ] Copia `env.production` a `.env` y reemplaza `DATABASE_URL`, `SECRET_KEY`, dominios de `CORS_ORIGINS` y cualquier otro secreto antes de desplegar.

2. **URLs/IPs hardcodeadas**
   - [ ] Revisar el frontend (`front_rosaline`) y cualquier cliente móvil para asegurarse de que consumen el dominio final (`https://api.tienda.com` o IP pública temporal) en lugar de `localhost` o Railway.
   - [ ] Confirmar que los webhooks o integraciones externas usan el nuevo dominio.

3. **Conexiones a Amazon Aurora PostgreSQL**
   - [x] `database.py` ya está configurado con parámetros de pool (`pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`) leyendo `DB_POOL_*` del `.env` para optimizar conexiones y evitar saturación.
   - [ ] Verificar que la `DATABASE_URL` apunta correctamente a Aurora: `postgresql://postgres:Ecommerce2025!@ecommerce-aurora-db.c5qc4qo884xb.us-east-2.rds.amazonaws.com:5432/postgres`
   - [ ] Configurar RDS Proxy o ajustar el pool si el número de workers crece significativamente.
   - [ ] Verificar que el Security Group de Aurora permite conexiones desde tu instancia EC2 (puerto 5432).

4. **CORS**
   - [ ] Ajustar `CORS_ORIGINS` en `.env` con los dominios reales del frontend (producción y, si aplica, staging). Evitar `*` en producción.

5. **Logging**
   - [ ] Habilitar `uvicorn`/`gunicorn` logs en CloudWatch o sistema centralizado (`LOG_LEVEL=INFO` por defecto). Considerar activar `STRUCTURED_LOGS=true` cuando se agregue soporte en la app.
   - [ ] Revisar que `print` en `main.py` (líneas de advertencia al crear tablas) no se ejecute en producción; usa un logger para integrarlo con Gunicorn si necesitas ese mensaje.

6. **Auditoría y seguridad**
   - [ ] Validar que `audit.py` almacene IPs reales cuando hay reverse proxy (usa encabezado `X-Forwarded-For` si es necesario).
   - [ ] Revisar políticas de rotación del `SECRET_KEY` y tokens JWT (`ACCESS_TOKEN_EXPIRE_MINUTES`).

7. **Automatización**
   - [ ] Ejecutar `deploy.sh` después de subir cambios para instalar dependencias, habilitar systemd y recargar Nginx.
   - [ ] Configurar respaldos automáticos de Aurora usando AWS Backup o snapshots programados.

Completar esta lista garantiza que el backend FastAPI está alineado con las mejores prácticas de producción en AWS EC2.

