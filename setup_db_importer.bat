@echo off
echo Configurando DB Local Importer...

REM Crear entorno virtual
python -m venv venv
call venv\Scripts\activate.bat

REM Instalar dependencias
pip install -r requirements.txt

REM Copiar archivo de configuración
if not exist .env copy .env.example .env

echo.
echo ¡Configuración completada!
echo.
echo Para usar:
echo 1. Activa el entorno: venv\Scripts\activate
echo 2. Edita el archivo .env con tus bases de datos
echo 3. Ejecuta: python db_local_importer.py
echo 4. Desactiva cuando termines: deactivate
pause