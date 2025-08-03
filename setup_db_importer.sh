#!/bin/bash
echo "Configurando DB Local Importer..."

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
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