# Checklist de adaptación para producción (AWS EC2)

1. **Variables sensibles**
   - [ ] Copia `env.production` a `.env` y reemplaza `DATABASE_URL`, `SECRET_KEY`, dominios de `CORS_ORIGINS` y cualquier otro secreto antes de desplegar.

2. **URLs/IPs hardcodeadas**
   - [ ] Revisar el frontend (`front_rosaline`) y cualquier cliente móvil para asegurarse de que consumen el dominio final (`https://api.tienda.com` o IP pública temporal) en lugar de `localhost` o Railway.
   - [ ] Confirmar que los webhooks o integraciones externas usan el nuevo dominio.

3. **Conexiones a PostgreSQL**
   - [ ] Considerar ampliar `database.py` para usar parámetros de pool (`pool_size`, `max_overflow`, `pool_timeout`) leyendo `DB_POOL_*` del `.env` cuando migres a Aurora para optimizar conexiones y evitar saturación.
   - [ ] Configurar `pgbouncer` o RDS Proxy si el número de workers crece.

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
   - [ ] Agendar `systemd` o `cron` para respaldos periódicos mientras migras de Supabase a Aurora.

Completar esta lista garantiza que el backend FastAPI está alineado con las mejores prácticas de producción en AWS EC2.

