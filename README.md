# DB Local Importer

Herramienta independiente para importar bases de datos Microsoft Access desde ubicaciones remotas (oficina) a ubicaciones locales, y actualizar automáticamente todos los vínculos de tablas vinculadas.

## Características

- ✅ **Descubrimiento automático**: Lee configuración desde archivo `.env`
- ✅ **Copia inteligente**: Copia bases de datos desde red de oficina a local
- ✅ **Actualización de vínculos**: Actualiza automáticamente tablas vinculadas
- ✅ **Modo ligero para correos**: Crea bases de correos con solo los últimos 5 registros
- ✅ **Verificación de red**: Comprueba accesibilidad antes de proceder
- ✅ **Logging detallado**: Registro completo de todas las operaciones
- ✅ **Modo solo vínculos**: Actualiza vínculos sin copiar bases de datos
- ✅ **Entorno virtual**: Instalación aislada y portable

## Instalación y Configuración

### Requisitos del Sistema
- Python 3.7+ (recomendado Python 3.8 o superior)
- Microsoft Access instalado
- Acceso a las bases de datos remotas (red de oficina)

### Instalación con Entorno Virtual (Recomendado)

#### 1. Clonar o descargar el proyecto
```bash
# Si usas Git
git clone <url-del-repositorio>
cd db-local-importer

# O simplemente descarga y extrae la carpeta del proyecto
```

#### 2. Crear entorno virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

#### 3. Configurar proxy (si es necesario)
Si tu oficina usa proxy para acceso a internet, configúralo antes de instalar dependencias:

**Con proxy:**
```bash
# En Windows:
set HTTP_PROXY=http://185.46.212.88:80
set HTTPS_PROXY=http://185.46.212.88:80

# En Linux/Mac:
export HTTP_PROXY=http://185.46.212.88:80
export HTTPS_PROXY=http://185.46.212.88:80
```

**Sin proxy:**
```bash
# En Windows:
set HTTP_PROXY=
set HTTPS_PROXY=

# En Linux/Mac:
unset HTTP_PROXY
unset HTTPS_PROXY
```

#### 4. Instalar dependencias
```bash
# Con el entorno virtual activado (y proxy configurado si es necesario)
pip install -r requirements.txt
```

#### 5. Verificar instalación
```bash
python db_local_importer.py --help
```

### Instalación Global (Alternativa)
Si prefieres no usar entorno virtual:

**Con proxy:**
```bash
# Configurar proxy primero
set HTTP_PROXY=http://185.46.212.88:80  # Windows
set HTTPS_PROXY=http://185.46.212.88:80  # Windows
# export HTTP_PROXY=http://185.46.212.88:80  # Linux/Mac
# export HTTPS_PROXY=http://185.46.212.88:80  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

**Sin proxy:**
```bash
pip install -r requirements.txt
```

### Uso en Diferentes Ubicaciones

#### Opción A: Copiar proyecto completo
1. Copia toda la carpeta `db-local-importer` a la ubicación deseada
2. Crea un nuevo entorno virtual en esa ubicación
3. Instala las dependencias
4. Configura tu archivo `.env`

#### Opción B: Instalación portable
1. Crea una carpeta para tu proyecto específico
2. Copia solo los archivos necesarios:
   - `db_local_importer.py`
   - `requirements.txt`
   - `.env.example` (renombrar a `.env`)
3. Sigue los pasos de instalación con entorno virtual

## Configuración

Crea un archivo `.env` en el directorio del proyecto con la siguiente configuración:

```env
# Contraseña para las bases de datos
DB_PASSWORD=tu_contraseña_aqui

# Directorio base para las bases de datos locales
LOCAL_DB_DIR=dbs-locales

# Rutas de bases de datos remotas a importar
# Los nombres de archivo se mantendrán iguales en local
DB_BRASS=\\servidor\ruta\brass.mdb
DB_CORREOS=\\servidor\ruta\correos.mdb
DB_TAREAS=\\servidor\ruta\tareas.mdb
DB_AGEDYS=\\servidor\ruta\agedys.mdb
```

**Nota:** Los archivos locales mantendrán los mismos nombres que los remotos y se guardarán en el directorio especificado en `LOCAL_DB_DIR`.

### 2. Estructura de directorios

El script creará automáticamente la carpeta `dbs-locales/` si no existe.

```
tu-proyecto/
├── .env
├── db_local_importer.py
├── requirements.txt
├── README.md
└── dbs-locales/          # Se crea automáticamente
    ├── BRASS_datos.accdb
    ├── correos_datos.accdb
    └── Tareas_datos1.accdb
```

## Uso

### Activar entorno virtual (si lo usas)
```bash
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### Proceso completo (copia + vínculos)
```bash
python db_local_importer.py
```

### Solo actualizar vínculos (sin copiar)
```bash
python db_local_importer.py --links-only
```

### Solo verificar conectividad
```bash
python db_local_importer.py --check-network
```

### Desactivar entorno virtual
```bash
deactivate
```

## Funcionalidades especiales

### Base de datos de correos
Las bases de datos que contengan "correos" en el nombre se procesan de forma especial:
- Se crea una nueva base de datos desde cero
- Se copia solo la estructura de la tabla principal
- Se importan únicamente los últimos 5 registros
- Esto reduce significativamente el tamaño y mejora el rendimiento

### Actualización de vínculos
El script analiza automáticamente todas las tablas vinculadas en cada base de datos y:
- Identifica las rutas remotas actuales
- Las convierte a rutas locales equivalentes
- Actualiza los vínculos usando COM de Access
- Reporta cualquier problema encontrado

## Logs

Todas las operaciones se registran en:
- `db_local_importer.log` (archivo)
- Consola (salida estándar)

## Casos de uso

### Desarrollo local
Cuando trabajas desde casa o sin acceso a la red de oficina:
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Ejecutar importación completa
python db_local_importer.py

# Desactivar cuando termines
deactivate
```

### Actualización periódica
Para actualizar solo los vínculos después de cambios en la estructura:
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows

# Actualizar solo vínculos
python db_local_importer.py --links-only

# Desactivar
deactivate
```

### Verificación de conectividad
Para comprobar si puedes acceder a las bases remotas:
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows

# Verificar conectividad
python db_local_importer.py --check-network

# Desactivar
deactivate
```

## Solución de problemas

### Error: "No se puede acceder a ubicaciones de red"
- Verifica tu conexión VPN
- Ejecuta desde la red de oficina
- Usa `--check-network` para diagnosticar

### Error: "Base de datos no encontrada"
- Verifica las rutas en el archivo `.env`
- Asegúrate de que tienes permisos de acceso
- Comprueba que la contraseña sea correcta

### Error: "No se pueden actualizar vínculos"
- Verifica que Microsoft Access esté instalado
- Ejecuta como administrador si es necesario
- Comprueba que las bases locales existan

### Problemas con pip y proxy

#### Error: "pip no puede descargar paquetes" o "Connection timeout"
Si estás en una oficina con proxy, configura las variables de entorno:

**Windows:**
```cmd
set HTTP_PROXY=http://185.46.212.88:80
set HTTPS_PROXY=http://185.46.212.88:80
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
export HTTP_PROXY=http://185.46.212.88:80
export HTTPS_PROXY=http://185.46.212.88:80
pip install -r requirements.txt
```

#### Error: "pip funciona pero sigue fallando"
Prueba con parámetros adicionales de pip:
```bash
pip install -r requirements.txt --proxy http://185.46.212.88:80 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

#### Si no hay proxy (desde casa o red sin proxy)
Asegúrate de limpiar las variables de proxy:

**Windows:**
```cmd
set HTTP_PROXY=
set HTTPS_PROXY=
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
unset HTTP_PROXY
unset HTTPS_PROXY
pip install -r requirements.txt
```

## Integración en otros proyectos

### Método 1: Copia completa con entorno virtual
Para usar esta herramienta en otros proyectos de forma aislada:

1. **Copia la carpeta completa** a tu nuevo proyecto:
   ```bash
   cp -r db-local-importer/ /ruta/a/tu/nuevo/proyecto/
   cd /ruta/a/tu/nuevo/proyecto/db-local-importer/
   ```

2. **Crea un nuevo entorno virtual**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura tu archivo `.env`**:
   ```bash
   cp .env.example .env
   # Edita .env con tus bases de datos específicas
   ```

5. **Ejecuta según tus necesidades**:
   ```bash
   python db_local_importer.py
   ```

### Método 2: Instalación mínima
Para una instalación más ligera:

1. **Crea carpeta para el importador**:
   ```bash
   mkdir mi-proyecto/db-importer
   cd mi-proyecto/db-importer
   ```

2. **Copia solo archivos esenciales**:
   - `db_local_importer.py`
   - `requirements.txt`
   - `.env.example` → renombrar a `.env`

3. **Configura entorno virtual**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

4. **Personaliza configuración**:
   - Edita `.env` con tus bases de datos
   - Ajusta rutas según tu proyecto

### Método 3: Script de instalación automática
Crea un script `setup_db_importer.bat` (Windows) o `setup_db_importer.sh` (Linux/Mac):

**Windows (`setup_db_importer.bat`):**
```batch
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
```

**Linux/Mac (`setup_db_importer.sh`):**
```bash
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
```

### Ventajas del uso con entornos virtuales

✅ **Aislamiento**: Las dependencias no interfieren con otros proyectos  
✅ **Portabilidad**: Fácil de mover entre diferentes máquinas  
✅ **Versionado**: Control preciso de versiones de dependencias  
✅ **Limpieza**: Fácil de eliminar sin afectar el sistema  
✅ **Múltiples proyectos**: Diferentes configuraciones por proyecto  

### Notas importantes

- **Siempre activa el entorno virtual** antes de usar la herramienta
- **Cada proyecto puede tener su propia configuración** de bases de datos
- **El entorno virtual se puede eliminar** sin afectar Python del sistema
- **Mantén actualizado** el archivo `requirements.txt` si añades dependencias

La herramienta es completamente independiente y portable cuando se usa con entornos virtuales.