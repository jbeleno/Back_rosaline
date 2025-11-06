# Guía de Despliegue en Render

## Pasos para subir a GitHub

1. **Asegúrate de estar en el directorio correcto:**
   ```bash
   cd Back_rosaline
   ```

2. **Agrega los archivos al staging (excluyendo cache):**
   ```bash
   git add .
   git reset HEAD backend_tienda/app/__pycache__/
   git reset HEAD backend_tienda/htmlcov/
   git reset HEAD backend_tienda/.coverage
   ```

3. **Haz commit:**
   ```bash
   git commit -m "feat: Agregar sistema de auditoría, tests y configuración para Render"
   ```

4. **Haz push a GitHub:**
   ```bash
   git push origin main
   ```

## Configuración en Render.com

1. **Crea una cuenta en Render** (si no tienes una):
   - Ve a https://render.com
   - Regístrate con tu cuenta de GitHub

2. **Conecta tu repositorio:**
   - En el dashboard de Render, haz clic en "New" → "Web Service"
   - Selecciona tu repositorio: `jbeleno/Back_rosaline`
   - Render detectará automáticamente el archivo `render.yaml`

3. **Configura las variables de entorno:**
   Ve a la sección "Environment" y agrega:
   - `DATABASE_URL`: Tu URL de Supabase PostgreSQL
     ```
     postgresql://postgres:[TU_PASSWORD]@db.ozyjkmvsaogxrmewaafj.supabase.co:5432/postgres
     ```
   - `SECRET_KEY`: Genera una clave segura (mínimo 32 caracteres)
     Puedes generar una con: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `60` (opcional)
   - `CORS_ORIGINS`: `*` (para desarrollo) o URLs específicas de tu frontend (producción)

4. **Configuración del servicio:**
   - **Build Command:** `pip install -r backend_tienda/requirements.txt`
   - **Start Command:** `cd backend_tienda && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (o el plan que prefieras)

5. **Despliega:**
   - Haz clic en "Create Web Service"
   - Render comenzará el build y despliegue automáticamente
   - Espera a que termine el build (puede tardar unos minutos)

6. **Verifica el despliegue:**
   - Una vez desplegado, Render te dará una URL como: `https://backend-tienda.onrender.com`
   - Visita `https://tu-url.onrender.com/docs` para ver la documentación de la API

## Notas importantes

- ⚠️ **Nunca subas el archivo `.env` a GitHub** (ya está en `.gitignore`)
- 🔒 **Genera una `SECRET_KEY` diferente para producción**
- 🌐 **En producción, configura `CORS_ORIGINS` con las URLs específicas de tu frontend**
- 📊 **Los logs de auditoría están protegidos y solo accesibles para administradores**
- 🧪 **Ejecuta los tests localmente antes de hacer push:**
  ```bash
  cd backend_tienda
  pytest
  ```

## Troubleshooting

Si el despliegue falla:
1. Revisa los logs en Render para ver el error específico
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que `DATABASE_URL` sea correcta y accesible desde Render
4. Verifica que el `SECRET_KEY` tenga al menos 32 caracteres

