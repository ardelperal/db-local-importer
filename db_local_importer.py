import os
import shutil
import logging
import argparse
from dotenv import load_dotenv
import win32com.client
import pythoncom

class DBLocalImporter:
    """Clase para importar bases de datos de Access a un entorno local."""
    
    def __init__(self):
        """Inicializa el importador, carga configuración y prepara el logging."""
        self._setup_logging()
        self.logger.info("Inicializando DBLocalImporter...")
        
        # Cargar configuración desde .env
        load_dotenv()
        
        self.remote_base_dir = os.getenv('REMOTE_BASE_DIR')
        self.local_db_dir = os.getenv('LOCAL_DB_DIR')
        self.db_password = os.getenv('DB_PASSWORD')
        
        if not self.remote_base_dir or not self.local_db_dir:
            self.logger.error("[X] Error: REMOTE_BASE_DIR y LOCAL_DB_DIR deben estar definidos en .env")
            raise ValueError("Variables de entorno no configuradas")
        
        # Crear directorio local si no existe
        os.makedirs(self.local_db_dir, exist_ok=True)
        
        self.databases = self._discover_databases()

    def _setup_logging(self):
        """Configura el sistema de logging."""
        self.logger = logging.getLogger('DBLocalImporter')
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicación de handlers si se reinicializa
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        # Handler para la consola
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        # Handler para archivo de log
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_importer.log')
        fh = logging.FileHandler(log_file_path, mode='w')
        fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(file_formatter)
        self.logger.addHandler(fh)
        
        self.logger.info(f"Logging configurado. Archivo de log en: {log_file_path}")

    def _discover_databases(self) -> dict:
        """Descubre las bases de datos a importar desde las variables de entorno."""
        databases = {}
        for key, value in os.environ.items():
            if key.startswith('DB_') and key != 'DB_PASSWORD':
                db_name = key.lower()
                remote_path = value
                
                # Construir ruta local basada en el nombre de la base remota
                local_filename = os.path.basename(remote_path)
                local_path = os.path.join(self.local_db_dir, local_filename)
                
                databases[db_name] = (remote_path, local_path)
                
        self.logger.info(f"Descubiertas {len(databases)} bases de datos para procesar.")
        return databases

    def show_configuration(self):
        """Muestra la configuración actual."""
        self.logger.info("=== Configuración Actual ===")
        self.logger.info(f"Directorio base remoto: {self.remote_base_dir}")
        self.logger.info(f"Directorio local de BD: {self.local_db_dir}")
        self.logger.info(f"Contraseña de BD: {'Sí' if self.db_password else 'No'}")
        self.logger.info("Bases de datos a procesar:")
        
        for db_name, (remote_path, local_path) in self.databases.items():
            self.logger.info(f"  - {db_name}:")
            self.logger.info(f"    Remoto: {remote_path}")
            self.logger.info(f"    Local:  {local_path}")
        self.logger.info("===========================")

    def _check_network_accessibility(self) -> bool:
        """Verifica si las rutas de red remotas son accesibles."""
        self.logger.info("Verificando accesibilidad de red...")
        all_accessible = True
        
        # Verificar directorio base
        if not os.path.exists(self.remote_base_dir):
            self.logger.error(f"[X] Directorio base remoto no accesible: {self.remote_base_dir}")
            all_accessible = False
        else:
            self.logger.info(f"  [OK] Directorio base accesible: {self.remote_base_dir}")
        
        # Verificar cada base de datos remota
        for db_name, (remote_path, _) in self.databases.items():
            if not os.path.exists(remote_path):
                self.logger.warning(f"  [!] {db_name} - Ruta remota no accesible: {remote_path}")
                # No marcamos como error fatal, puede que solo se quieran actualizar vínculos
            else:
                self.logger.info(f"  [OK] {db_name} - Ruta remota accesible")
                
        return all_accessible

    def _check_access_availability(self) -> bool:
        """Verifica si la aplicación Microsoft Access está disponible."""
        try:
            pythoncom.CoInitialize()
            win32com.client.Dispatch("Access.Application")
            pythoncom.CoUninitialize()
            self.logger.info("[OK] Microsoft Access detectado.")
            return True
        except Exception as e:
            self.logger.error("[X] Error: Microsoft Access no parece estar instalado o accesible.")
            self.logger.debug(f"    Detalles del error: {e}")
            return False

    def copy_databases(self) -> bool:
        """Copia todas las bases de datos desde la ubicación remota a la local."""
        self.logger.info("=== Iniciando copia de bases de datos ===")
        success_count = 0
        total_count = len(self.databases)
        
        for db_name, (remote_path, local_path) in self.databases.items():
            self.logger.info(f"Procesando {db_name}...")
            
            try:
                if not os.path.exists(remote_path):
                    self.logger.warning(f"  [SKIP] No se encontró la base remota: {remote_path}")
                    continue
                
                # Lógica especial para DB_CORREOS
                if db_name == 'db_correos':
                    if self._setup_correos_database_light(remote_path, local_path):
                        success_count += 1
                    continue

                # Lógica general para otras bases de datos
                self.logger.info(f"  Copiando {remote_path} -> {local_path}")
                shutil.copy2(remote_path, local_path)
                self.logger.info(f"  [OK] Copia de {db_name} completada.")
                success_count += 1
                
            except Exception as e:
                self.logger.error(f"  [X] Error copiando {db_name}: {e}")
        
        self.logger.info(f"=== Copia finalizada: {success_count}/{total_count} exitosas ===")
        return success_count > 0

    def _setup_correos_database_light(self, remote_path: str, local_path: str) -> bool:
        """Crea una versión ligera de la base de datos de Correos."""
        self.logger.info("  [SPECIAL] Creando versión ligera de DB_CORREOS...")
        
        try:
            # Si ya existe, la eliminamos para recrearla
            if os.path.exists(local_path):
                os.remove(local_path)
            
            # Crear la base de datos vacía con la estructura correcta
            if not self._create_empty_database_with_structure(remote_path, local_path):
                return False
            
            # Llenar con los últimos registros
            if not self._fill_database_with_latest_records(remote_path, local_path):
                return False
            
            self.logger.info("  [OK] Versión ligera de DB_CORREOS creada exitosamente.")
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error creando DB_CORREOS ligera: {e}")
            return False

    def _create_empty_database_with_structure(self, remote_path: str, local_path: str) -> bool:
        """Crea una base de datos Access vacía con la misma estructura que la remota."""
        pythoncom.CoInitialize()
        
        try:
            filename = os.path.basename(local_path)
            
            self.logger.info(f"  [BUILD] Creando base de datos {filename} desde cero...")
            
            local_path_abs = os.path.abspath(local_path)
            
            # Paso 1: Crear base de datos vacía
            access = win32com.client.Dispatch("Access.Application")
            access.Visible = False
            access.NewCurrentDatabase(local_path_abs)
            access.Quit()
            access = None
            
            # Paso 2: Aplicar contraseña
            if self.db_password:
                self.logger.info(f"  [LOCK] Aplicando contraseña...")
                access = win32com.client.Dispatch("Access.Application")
                access.Visible = False
                access.OpenCurrentDatabase(local_path_abs, True)
                access.CurrentDb().NewPassword("", self.db_password)
                access.CloseCurrentDatabase()
                access.Quit()
                access = None
            
            # Paso 3: Analizar estructura de la base remota
            table_structure = self._analyze_remote_table_structure(remote_path)
            
            if not table_structure:
                return False
            
            # Paso 4: Crear tabla con la estructura analizada
            if not self._create_table_with_structure(local_path_abs, table_structure):
                return False
            
            self.logger.info(f"  [OK] Base de datos {filename} creada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error creando base de datos: {e}")
            return False
    
    def _analyze_remote_table_structure(self, remote_path: str) -> dict:
        """Analiza la estructura de la tabla principal en la base remota"""
        import pyodbc
        
        try:
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
            conn_str = f'DRIVER={driver};DBQ={remote_path};PWD={self.db_password};'
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Encontrar la tabla principal
            main_table_name = None
            tables = cursor.tables(tableType='TABLE')
            
            for table in tables:
                table_name = table.table_name
                if not table_name.startswith('MSys') and not table_name.startswith('~'):
                    main_table_name = table_name
                    break
            
            if not main_table_name:
                conn.close()
                return None
            
            # Obtener información de las columnas
            columns_info = []
            columns = cursor.columns(table=main_table_name)
            
            for col in columns:
                column_info = {
                    'name': col.column_name,
                    'type': col.type_name,
                    'size': col.column_size if hasattr(col, 'column_size') else None,
                    'nullable': col.nullable == 1 if hasattr(col, 'nullable') else True,
                    'default': col.column_def if hasattr(col, 'column_def') else None
                }
                columns_info.append(column_info)
            
            conn.close()
            
            return {
                'name': main_table_name,
                'columns': columns_info
            }
            
        except Exception as e:
            self.logger.error(f"  [X] Error analizando estructura remota: {e}")
            return None
    
    def _create_table_with_structure(self, local_path: str, table_structure: dict) -> bool:
        """Crea una tabla en la base local con la estructura especificada"""
        import pyodbc
        
        try:
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
            conn_str = f'DRIVER={driver};DBQ={local_path};PWD={self.db_password};'
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            table_name = table_structure['name']
            columns = table_structure['columns']
            
            # Construir la sentencia CREATE TABLE
            column_definitions = []
            
            for col in columns:
                col_def = f"[{col['name']}]"
                
                # Mapear tipos de datos
                access_type = self._map_odbc_type_to_access(col['type'], col.get('size'))
                col_def += f" {access_type}"
                
                if not col.get('nullable', True):
                    col_def += " NOT NULL"
                
                column_definitions.append(col_def)
            
            create_sql = f"CREATE TABLE [{table_name}] ({', '.join(column_definitions)})"
            
            cursor.execute(create_sql)
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error creando tabla: {e}")
            return False
    
    def _map_odbc_type_to_access(self, odbc_type: str, size: int = None) -> str:
        """Mapea tipos de datos ODBC a tipos de Access SQL"""
        type_mapping = {
            'COUNTER': 'AUTOINCREMENT',
            'INTEGER': 'INTEGER',
            'LONG': 'LONG',
            'SINGLE': 'SINGLE',
            'DOUBLE': 'DOUBLE',
            'CURRENCY': 'CURRENCY',
            'DATETIME': 'DATETIME',
            'BIT': 'YESNO',
            'BYTE': 'BYTE',
            'LONGBINARY': 'LONGBINARY',
            'LONGTEXT': 'MEMO'
        }
        
        if odbc_type in ['VARCHAR', 'CHAR', 'TEXT']:
            if size and size > 0:
                return f"TEXT({size})"
            else:
                return "TEXT(255)"
        
        return type_mapping.get(odbc_type.upper(), "TEXT(255)")
    
    def _fill_database_with_latest_records(self, remote_path: str, local_path: str) -> bool:
        """Llena la base local con los últimos 5 registros de la base remota"""
        import pyodbc
        
        try:
            self.logger.info(f"  [DATA] Obteniendo últimos 5 registros...")
            
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
            
            # Conectar a la base remota
            remote_conn_str = f'DRIVER={driver};DBQ={remote_path};PWD={self.db_password};'
            remote_conn = pyodbc.connect(remote_conn_str)
            remote_cursor = remote_conn.cursor()
            
            # Obtener la tabla principal
            main_table_name = None
            tables = remote_cursor.tables(tableType='TABLE')
            
            for table in tables:
                table_name = table.table_name
                if not table_name.startswith('MSys') and not table_name.startswith('~'):
                    main_table_name = table_name
                    break
            
            if not main_table_name:
                remote_conn.close()
                return True
            
            # Obtener columnas
            columns_info = remote_cursor.columns(table=main_table_name)
            column_names = [col.column_name for col in columns_info]
            
            # Intentar obtener los últimos 5 registros
            order_fields = ['ID', 'Id', 'id', 'Fecha', 'fecha', 'FechaCreacion', 'Timestamp']
            records = []
            
            for field in order_fields:
                if field in column_names:
                    try:
                        sql = f"SELECT TOP 5 * FROM [{main_table_name}] ORDER BY [{field}] DESC"
                        remote_cursor.execute(sql)
                        records = remote_cursor.fetchall()
                        if records:
                            break
                    except:
                        continue
            
            if not records:
                # Si no se pudo ordenar, tomar los primeros 5
                try:
                    sql = f"SELECT TOP 5 * FROM [{main_table_name}]"
                    remote_cursor.execute(sql)
                    records = remote_cursor.fetchall()
                except:
                    pass
            
            remote_conn.close()
            
            if not records:
                self.logger.info(f"  [OK] No hay registros para copiar")
                return True
            
            # Insertar registros en la base local
            local_conn_str = f'DRIVER={driver};DBQ={local_path};PWD={self.db_password};'
            local_conn = pyodbc.connect(local_conn_str)
            local_cursor = local_conn.cursor()
            
            # Construir INSERT
            placeholders = ', '.join(['?' for _ in column_names])
            insert_sql = f"INSERT INTO [{main_table_name}] ([{'], ['.join(column_names)}]) VALUES ({placeholders})"
            
            for record in records:
                try:
                    local_cursor.execute(insert_sql, record)
                except Exception as e:
                    self.logger.debug(f"    [!] Error insertando registro: {e}")
            
            local_conn.commit()
            local_conn.close()
            
            self.logger.info(f"  [OK] Insertados {len(records)} registros")
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error llenando base con registros: {e}")
            return False
    
    def update_all_database_links(self) -> bool:
        """Actualiza vínculos en todas las bases de datos locales"""
        self.logger.info("=== Iniciando actualización de vínculos ===")
        success_count = 0
        total_count = 0
        
        for db_name, (remote_path, local_path) in self.databases.items():
            if not os.path.exists(local_path):
                self.logger.warning(f"[SKIP] {db_name} - Base local no existe: {local_path}")
                continue
            
            total_count += 1
            
            try:
                self.logger.info(f"[LINK] Actualizando vínculos en {db_name}...")
                
                if self._update_database_links(local_path):
                    self.logger.info(f"  [OK] Vínculos actualizados en {db_name}")
                    success_count += 1
                else:
                    self.logger.error(f"  [X] Error actualizando vínculos en {db_name}")
                    
            except Exception as e:
                self.logger.error(f"[X] Error procesando vínculos en {db_name}: {e}")
        
        self.logger.info(f"=== Actualización de vínculos completada: {success_count}/{total_count} exitosas ===")
        return success_count == total_count
    
    def _update_database_links(self, db_path: str) -> bool:
        """Actualiza los vínculos de una base de datos específica"""
        try:
            pythoncom.CoInitialize()
            
            access = win32com.client.Dispatch("Access.Application")
            access.Visible = False
            
            # Abrir base de datos
            if self.db_password:
                access.OpenCurrentDatabase(db_path, False, self.db_password)
            else:
                access.OpenCurrentDatabase(db_path)
            
            db = access.CurrentDb()
            table_defs = db.TableDefs
            
            updated_count = 0
            
            for i in range(table_defs.Count):
                table_def = table_defs.Item(i)
                table_name = table_def.Name
                
                # Solo procesar tablas vinculadas
                if hasattr(table_def, 'Connect') and table_def.Connect:
                    connect_str = table_def.Connect
                    
                    if 'DATABASE=' in connect_str.upper():
                        # Extraer la ruta actual
                        parts = connect_str.split(';')
                        current_db_path = None
                        
                        for part in parts:
                            if part.upper().startswith('DATABASE='):
                                current_db_path = part[9:]  # Remover 'DATABASE='
                                break
                        
                        if current_db_path:
                            # Convertir a ruta local
                            new_local_path = self._convert_to_local_path(current_db_path)
                            
                            if new_local_path and os.path.exists(new_local_path):
                                try:
                                    # Actualizar el vínculo
                                    new_connect_str = connect_str.replace(current_db_path, new_local_path)
                                    table_def.Connect = new_connect_str
                                    table_def.RefreshLink()
                                    
                                    self.logger.debug(f"    [OK] Tabla {table_name} revinculada")
                                    updated_count += 1
                                    
                                except Exception as e:
                                    self.logger.debug(f"    [X] Error revinculando {table_name}: {e}")
            
            access.CloseCurrentDatabase()
            access.Quit()
            access = None
            
            self.logger.info(f"  [OK] {updated_count} tablas revinculadas")
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"  [X] Error actualizando vínculos: {e}")
            self.logger.debug(traceback.format_exc())
            return False
        finally:
            pythoncom.CoUninitialize()
    
    def _convert_to_local_path(self, remote_path: str) -> str:
        """Convierte una ruta remota a su equivalente local"""
        filename = os.path.basename(remote_path)
        
        # Buscar en nuestras bases de datos configuradas
        for db_name, (configured_remote, configured_local) in self.databases.items():
            if os.path.basename(configured_remote) == filename:
                return configured_local
        
        # Si no se encuentra, asumir que está en el directorio local
        return os.path.join(self.local_db_dir, filename)
    
    def setup_environment(self, force_links_only: bool = False) -> bool:
        """
        Ejecuta el proceso completo de importación
        
        Args:
            force_links_only: Si es True, solo actualiza vínculos sin copiar bases de datos
        
        Returns:
            bool: True si todo el proceso fue exitoso
        """
        self.logger.info("[START] Iniciando importación de bases de datos locales")

        try:
            # Primero, verificar si Access está disponible
            if not self._check_access_availability():
                return False

            # Mostrar configuración
            self.show_configuration()
            
            # Verificar accesibilidad de red (solo si no es modo force_links_only)
            if not force_links_only:
                if not self._check_network_accessibility():
                    self.logger.error("[X] No se puede acceder a las ubicaciones de red remotas")
                    self.logger.warning("   Opciones disponibles:")
                    self.logger.warning("   1. Ejecutar desde la red de oficina")
                    self.logger.warning("   2. Usar modo 'solo vínculos' si ya tienes las bases locales")
                    return False
                
                # Copiar bases de datos
                copy_success = self.copy_databases()
                
                if not copy_success:
                    self.logger.warning("[!] Algunas copias fallaron, continuando con vínculos...")
            else:
                self.logger.info("[LINK] Modo 'solo vínculos' - saltando copia")
                copy_success = True
            
            # Actualizar vínculos
            links_success = self.update_all_database_links()
            
            # Resultado final
            if copy_success and links_success:
                self.logger.info("[OK] Importación completada exitosamente")
                return True
            else:
                self.logger.warning("[!] Importación completada con algunos errores")
                return False
                
        except Exception as e:
            self.logger.error(f"[X] Error en importación: {e}")
            return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="DB Local Importer - Importa bases de datos Access a ubicaciones locales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python db_local_importer.py                    # Proceso completo
  python db_local_importer.py --links-only       # Solo actualizar vínculos
  python db_local_importer.py --check-network    # Solo verificar red
        """
    )
    
    parser.add_argument(
        '--links-only', 
        action='store_true',
        help='Solo actualizar vínculos de tablas (no copiar bases de datos)'
    )
    
    parser.add_argument(
        '--check-network', 
        action='store_true',
        help='Solo verificar accesibilidad de red y mostrar configuración'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DB LOCAL IMPORTER")
    print("=" * 60)
    print()
    
    try:
        importer = DBLocalImporter()
        
        if args.check_network:
            # Solo verificar red y mostrar configuración
            importer.show_configuration()
            network_ok = importer._check_network_accessibility()
            
            print()
            print("=" * 60)
            if network_ok:
                print("[OK] VERIFICACIÓN DE RED EXITOSA")
            else:
                print("[X] PROBLEMAS DE CONECTIVIDAD DE RED")
            print("=" * 60)
            
            return 0 if network_ok else 1
        
        # Ejecutar importación completa o solo vínculos
        success = importer.setup_environment(force_links_only=args.links_only)
        
        print()
        print("=" * 60)
        if success:
            print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
        else:
            print("[!] PROCESO COMPLETADO CON ERRORES")
        print("=" * 60)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n[X] Proceso cancelado por el usuario")
        return 1
    except Exception as e:
        print(f"\n[X] Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
