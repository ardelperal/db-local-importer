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

## Instalación

### Requisitos
- Python 3.7+
- Microsoft Access instalado
- Acceso a las bases de datos remotas (red de oficina)

### Dependencias
```bash
pip install -r requirements.txt
```

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
Cuando trabajas desde casa o sin acceso a la red de oficina, ejecuta:
```bash
python db_local_importer.py
```

### Actualización periódica
Para actualizar solo los vínculos después de cambios en la estructura:
```bash
python db_local_importer.py --links-only
```

### Verificación de conectividad
Para comprobar si puedes acceder a las bases remotas:
```bash
python db_local_importer.py --check-network
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

## Integración en otros proyectos

Para usar esta herramienta en otros proyectos:

1. Copia la carpeta completa a tu proyecto
2. Modifica el archivo `.env` con tus bases de datos
3. Ejecuta el script según tus necesidades

La herramienta es completamente independiente y no tiene dependencias específicas del proyecto original.