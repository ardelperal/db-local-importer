#!/bin/bash
echo "Configurando DB Local Importer..."

# Preguntar sobre proxy
echo ""
echo "¿Estás en la oficina y necesitas configurar proxy? (s/n)"
read -p "Respuesta: " usar_proxy

if [[ "$usar_proxy" == "s" || "$usar_proxy" == "S" ]]; then
    echo "Configurando proxy para pip..."
    export HTTP_PROXY=http://185.46.212.88:80
    export HTTPS_PROXY=http://185.46.212.88:80
    echo "Proxy configurado: $HTTP_PROXY"
else
    echo "Limpiando configuración de proxy..."
    unset HTTP_PROXY
    unset HTTPS_PROXY
    echo "Sin proxy configurado"
fi

echo ""
echo "Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "Instalando dependencias..."
pip install -r requirements.txt

# Copiar archivo de configuración
if [ ! -f .env ]; then
    cp .env.example .env
fi

echo ""
echo "¡Configuración completada!"
echo ""
echo "Para usar:"
echo "1. Activa el entorno: source venv/bin/activate"
echo "2. Edita el archivo .env con tus bases de datos"
echo "3. Ejecuta: python db_local_importer.py"
echo "4. Desactiva cuando termines: deactivate"
echo ""
echo "NOTA: Si tienes problemas con pip, ejecuta manualmente:"
if [[ "$usar_proxy" == "s" || "$usar_proxy" == "S" ]]; then
    echo "  export HTTP_PROXY=http://185.46.212.88:80"
    echo "  export HTTPS_PROXY=http://185.46.212.88:80"
else
    echo "  unset HTTP_PROXY"
    echo "  unset HTTPS_PROXY"
fi
echo "  pip install -r requirements.txt"