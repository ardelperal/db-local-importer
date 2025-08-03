# Instalación Rápida - DB Local Importer

## 🚀 Instalación Automática (Recomendado)

### Windows
1. Abre PowerShell o CMD en la carpeta del proyecto
2. Ejecuta el script de instalación:
   ```cmd
   setup_db_importer.bat
   ```
3. El script creará automáticamente el entorno virtual e instalará las dependencias

### Linux/Mac
1. Abre terminal en la carpeta del proyecto
2. Da permisos de ejecución y ejecuta:
   ```bash
   chmod +x setup_db_importer.sh
   ./setup_db_importer.sh
   ```

## 📋 Instalación Manual

### 1. Crear entorno virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar archivo .env
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus bases de datos
# (usar tu editor favorito)
```

## 🎯 Uso Rápido

### Activar entorno e importar bases de datos
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Ejecutar importación completa
python db_local_importer.py

# Desactivar cuando termines
deactivate
```

### Comandos útiles
```bash
# Solo verificar conectividad
python db_local_importer.py --check-network

# Solo actualizar vínculos (sin copiar)
python db_local_importer.py --links-only

# Ver ayuda
python db_local_importer.py --help
```

## 🔧 Solución de Problemas

### Error: "python no se reconoce como comando"
- Instala Python desde [python.org](https://python.org)
- Asegúrate de marcar "Add Python to PATH" durante la instalación

### Error: "No se puede crear entorno virtual"
```bash
# Instalar venv si no está disponible
python -m pip install virtualenv
```

### Error: "pip no funciona"
```bash
# Actualizar pip
python -m pip install --upgrade pip
```

## 📁 Estructura después de la instalación
```
db-local-importer/
├── venv/                    # Entorno virtual (creado automáticamente)
├── .env                     # Tu configuración (copia de .env.example)
├── db_local_importer.py     # Script principal
├── requirements.txt         # Dependencias
├── setup_db_importer.bat   # Script de instalación Windows
├── setup_db_importer.sh    # Script de instalación Linux/Mac
└── dbs-locales/            # Bases de datos locales (se crea automáticamente)
```

## ✅ Verificar instalación
```bash
# Con el entorno virtual activado
python db_local_importer.py --help
```

Si ves la ayuda del comando, ¡la instalación fue exitosa! 🎉