#!/usr/bin/env python3
"""
DB Local Importer - Herramienta independiente para importar bases de datos Access

Funcionalidades:
1. Copia bases de datos desde ubicaciones remotas (oficina) a ubicaciones locales
2. Actualiza vínculos de tablas vinculadas para que apunten a bases de datos locales
3. Mantiene los mismos nombres de archivo que las bases remotas

Autor: Sistema de Gestión
Fecha: 2024
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import win32com.client
import pythoncom
from dotenv import load_dotenv
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_local_importer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DBLocalImporter:
    """Clase para importar bases de datos Access a ubicaciones locales"""
    
    def __init__(self):
        """Inicializar configuración"""
        self.logger = logging.getLogger(__name__)
        
        load_dotenv()
        self.project_root = Path(__file__).parent
        self.db_password = os.getenv('DB_PASSWORD', '')
        self.local_db_dir = os.getenv('LOCAL_DB_DIR', 'dbs-locales')
        
        # Descubrir automáticamente las bases de datos desde el .env
        self.databases = self._discover_databases_from_env()
        
        # Crear directorio local si no existe
        self._ensure_local_directory()
    
    def _discover_databases_from_env(self) -> Dict[str, Tuple[str, str]]:
        """
        Descubre automáticamente las bases de datos desde las variables de entorno
        
        Returns:
            Dict con mapeo de bases de datos: {nombre: (remote_path, local_path)}
        """
        databases = {}
        
        # Obtener todas las variables de entorno
        env_vars = dict(os.environ)
        
        # Buscar variables DB_*
        db_vars = {k: v for k, v in env_vars.items() if k.startswith('DB_') and k != 'DB_PASSWORD'}
        
        for db_var, remote_path in db_vars.items():
            # Extraer nombre de la base de datos (ej: DB_BRASS -> BRASS)
            db_name = db_var.replace('DB_', '')
            
            # Obtener nombre del archivo desde la ruta remota
            filename = os.path.basename(remote_path)
            
            # Construir ruta local manteniendo el mismo nombre
            local_path = os.path.join(self.local_db_dir, filename)
            
            databases[db_name] = (remote_path, local_path)
            
            self.logger.debug(f"Base de datos descubierta: {db_name}")
            self.logger.debug(f"  Remota: {remote_path}")
            self.logger.debug(f"  Local: {local_path}")
        
        self.logger.info(f"Descubiertas {len(databases)} bases de datos desde .env")
        return databases
    
    def _ensure_local_directory(self):
        """Crear directorio local si no existe"""
        # Convertir a ruta absoluta si es relativa
        if not os.path.isabs(self.local_db_dir):
            self.local_db_dir = str(self.project_root / self.local_db_dir)
        
        os.makedirs(self.local_db_dir, exist_ok=True)
        self.logger.debug(f"Directorio local asegurado: {self.local_db_dir}")
    
    def _check_network_accessibility(self) -> bool:
        """Verifica si las ubicaciones de red remotas son accesibles"""
        network_locations = set()
        
        for db_name, (remote_path, local_path) in self.databases.items():
            if remote_path.startswith('\\\\'):
                # Extraer la parte del servidor de red
                parts = remote_path.split('\\')
                if len(parts) >= 4:
                    network_root = f"\\\\{parts[2]}\\{parts[3]}"
                    network_locations.add(network_root)
        
        if not network_locations:
            self.logger.info("No se encontraron ubicaciones de red para verificar")
            return True
        
        self.logger.info("[NET] Verificando accesibilidad de ubicaciones de red...")
        
        all_accessible = True
        for network_location in network_locations:
            try:
                if os.path.exists(network_location):
                    self.logger.info(f"  [OK] {network_location} - Accesible")
                else:
                    self.logger.error(f"  [X] {network_location} - No accesible")
                    all_accessible = False
            except Exception as e:
                self.logger.error(f"  [X] {network_location} - Error: {e}")
                all_accessible = False
        
        if not all_accessible:
            self.logger.error("[!] Algunas ubicaciones de red no son accesibles")
            self.logger.error("   Verifica tu conexión a la red de oficina")
        
        return all_accessible
    
    def show_configuration(self):
        """Muestra la configuración descubierta desde el .env"""
        self.logger.info("=== CONFIGURACIÓN DESCUBIERTA ===")
        self.logger.info(f"Directorio local: {self.local_db_dir}")
        self.logger.info(f"Contraseña configurada: {'Sí' if self.db_password else 'No'}")
        
        if not self.databases:
            self.logger.warning("No se encontraron bases de datos configuradas")
            return
        
        for db_name, (remote_path, local_path) in self.databases.items():
            filename = os.path.basename(remote_path)
            
            self.logger.info(f"\n[DB] {db_name}:")
            self.logger.info(f"  Archivo: {filename}")
            self.logger.info(f"  Remota: {remote_path}")
            self.logger.info(f"  Local: {local_path}")
            
            # Verificar existencia
            exists_remote = "[OK]" if os.path.exists(remote_path) else "[X]"
            exists_local = "[OK]" if os.path.exists(local_path) else "[X]"
            
            self.logger.info(f"  Estado remoto: {exists_remote}")
            self.logger.info(f"  Estado local: {exists_local}")
        
        self.logger.info("=" * 50)
    
    def copy_databases(self) -> bool:
        """
        Copia todas las bases de datos desde ubicaciones remotas a locales
        
        Returns:
            bool: True si todas las copias fueron exitosas
        """
        self.logger.info("=== Iniciando copia de bases de datos ===")
        success_count = 0
        total_count = len(self.databases)
        
        for db_name, (remote_path, local_path) in self.databases.items():
            try:
                filename = os.path.basename(remote_path)
                
                self.logger.info(f"[COPY] Procesando {db_name} ({filename})...")
                
                if not os.path.exists(remote_path):
                    self.logger.error(f"  [X] Archivo remoto no encontrado: {remote_path}")
                    continue
                
                # Manejo especial para base de datos de correos
                if 'correos' in filename.lower():
                    if self._setup_correos_database_light(remote_path, local_path):
                        self.logger.info(f"  [OK] {db_name} configurada exitosamente (modo ligero)")
                        success_count += 1
                    else:
                        self.logger.error(f"  [X] Error configurando {db_name} en modo ligero")
                else:
                    # Copia normal
                    try:
                        shutil.copy2(remote_path, local_path)
                        self.logger.info(f"  [OK] {db_name} copiada exitosamente")
                        success_count += 1
                    except Exception as e:
                        self.logger.error(f"  [X] Error copiando {db_name}: {e}")
                        
            except Exception as e:
                self.logger.error(f"[X] Error procesando {db_name}: {e}")
        
        self.logger.info(f"=== Copia completada: {success_count}/{total_count} exitosas ===")
        return success_count == total_count
    
    def _setup_correos_database_light(self, remote_path: str, local_path: str) -> bool:
        """
        Configura la base de datos de correos en modo ligero (solo últimos 5 registros)
        """
        try:
            filename = os.path.basename(local_path)
            
            self.logger.info(f"  [EMAIL] Configurando base de correos (modo ligero)...")
            
            # Si la base local existe, eliminarla para recrearla
            if os.path.exists(local_path):
                self.logger.info(f"  [DELETE] Eliminando base local existente...")
                os.remove(local_path)
            
            # Crear la base de datos desde cero
            if not self._create_database_from_scratch(remote_path, local_path):
                return False
            
            # Llenar con los últimos 5 registros
            return self._fill_database_with_latest_records(remote_path, local_path)
                
        except Exception as e:
            self.logger.error(f"  [X] Error configurando base de correos: {e}")
            return False
    
    def _create_database_from_scratch(self, remote_path: str, local_path: str) -> bool:
        """Crea una base de datos Access desde cero con estructura idéntica a la remota"""
        import pyodbc
        
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
            self.logger.error(f"  [X] Error actualizando vínculos: {e}")
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