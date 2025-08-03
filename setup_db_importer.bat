@echo off
echo Configurando DB Local Importer...

REM Preguntar sobre proxy
echo.
echo ¿Estás en la oficina y necesitas configurar proxy? (s/n)
set /p usar_proxy=

if /i "%usar_proxy%"=="s" (
    echo Configurando proxy para pip...
    set HTTP_PROXY=http://185.46.212.88:80
    set HTTPS_PROXY=http://185.46.212.88:80
    echo Proxy configurado: %HTTP_PROXY%
) else (
    echo Limpiando configuración de proxy...
    set HTTP_PROXY=
    set HTTPS_PROXY=
    echo Sin proxy configurado
)

echo.
echo Creando entorno virtual...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo Instalando dependencias...
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
echo.
echo NOTA: Si tienes problemas con pip, ejecuta manualmente:
if /i "%usar_proxy%"=="s" (
    echo   set HTTP_PROXY=http://185.46.212.88:80
    echo   set HTTPS_PROXY=http://185.46.212.88:80
) else (
    echo   set HTTP_PROXY=
    echo   set HTTPS_PROXY=
)
echo   pip install -r requirements.txt
pause