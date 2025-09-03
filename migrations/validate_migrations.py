import sys
from pathlib import Path
from typing import List, Dict, Any
import re


def get_project_root() -> Path:
    """
    Detecta automáticamente la raíz del proyecto buscando tools_data/
    """
    current_path = Path.cwd().resolve()
    
    # Verificar si estamos en el directorio correcto
    if (current_path / "tools_data").exists():
        return current_path
    
    # Buscar en el directorio padre
    parent_path = current_path.parent
    if (parent_path / "tools_data").exists():
        return parent_path
    
    # Buscar dos niveles arriba
    grandparent_path = parent_path.parent
    if (grandparent_path / "tools_data").exists():
        return grandparent_path
    
    raise FileNotFoundError("No se encontró el directorio tools_data. Asegúrate de ejecutar desde el proyecto correcto.")


class MigrationValidator:
    def __init__(self):
        self.project_root = get_project_root()
        self.migrations_dir = self.project_root / "migrations" / "tools_migrations"
        
        print(f"📁 Directorio del proyecto: {self.project_root}")
        print(f"📁 Directorio de migraciones: {self.migrations_dir}")

    def find_migration_files(self) -> List[Path]:
        """Encuentra todos los archivos de migración .ts"""
        if not self.migrations_dir.exists():
            return []
        
        return list(self.migrations_dir.glob("*.ts"))

    def validate_migration_file(self, file_path: Path) -> Dict[str, Any]:
        """Valida un archivo de migración específico"""
        result = {
            'file': file_path.name,
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validaciones básicas
            self._validate_basic_structure(content, result)
            self._validate_class_declaration(content, result)
            self._validate_methods(content, result)
            self._validate_sql_syntax(content, result)
            self._calculate_stats(content, result)
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Error leyendo archivo: {str(e)}")
        
        return result

    def _validate_basic_structure(self, content: str, result: Dict[str, Any]):
        """Valida la estructura básica del archivo"""
        required_imports = ['MigrationInterface', 'QueryRunner']
        
        for import_name in required_imports:
            if import_name not in content:
                result['errors'].append(f"Falta import requerido: {import_name}")
                result['valid'] = False

    def _validate_class_declaration(self, content: str, result: Dict[str, Any]):
        """Valida la declaración de la clase"""
        class_pattern = r'export class (\w+) implements MigrationInterface'
        match = re.search(class_pattern, content)
        
        if not match:
            result['errors'].append("No se encontró declaración de clase válida")
            result['valid'] = False
            return
        
        class_name = match.group(1)
        result['stats']['class_name'] = class_name
        
        # Verificar que el nombre de la clase esté en la propiedad name
        name_pattern = rf"name = '{class_name}'"
        if name_pattern not in content:
            result['warnings'].append(f"La propiedad 'name' no coincide con el nombre de la clase")

    def _validate_methods(self, content: str, result: Dict[str, Any]):
        """Valida que existan los métodos up y down"""
        required_methods = ['up', 'down']
        
        for method in required_methods:
            method_pattern = rf'public async {method}\(queryRunner: QueryRunner\): Promise<void>'
            if not re.search(method_pattern, content):
                result['errors'].append(f"Falta método requerido: {method}")
                result['valid'] = False

    def _validate_sql_syntax(self, content: str, result: Dict[str, Any]):
        """Valida la sintaxis SQL básica"""
        # Verificar que hay queries SQL
        if 'queryRunner.query(' not in content:
            result['errors'].append("No se encontraron queries SQL")
            result['valid'] = False
            return
        
        # Verificar INSERT en método up
        if 'INSERT INTO landing_ia_catalog_item' not in content:
            result['warnings'].append("No se encontró INSERT en landing_ia_catalog_item")
        
        # Verificar DELETE en método down
        if 'DELETE FROM landing_ia_catalog_item' not in content:
            result['warnings'].append("No se encontró DELETE en método down")
        
        # Contar número de registros a insertar
        insert_count = content.count('gen_random_uuid()')
        if insert_count > 0:
            result['stats']['insert_count'] = insert_count

    def _calculate_stats(self, content: str, result: Dict[str, Any]):
        """Calcula estadísticas del archivo"""
        result['stats']['file_size'] = len(content)
        result['stats']['lines'] = content.count('\n') + 1
        
        # Verificar si es migración consolidada (muchos registros)
        insert_count = result['stats'].get('insert_count', 0)
        if insert_count > 50:
            result['stats']['type'] = 'consolidada'
        elif insert_count == 1:
            result['stats']['type'] = 'individual'
        else:
            result['stats']['type'] = 'múltiple'

    def validate_all_migrations(self) -> Dict[str, Any]:
        """Valida todas las migraciones y genera reporte"""
        migration_files = self.find_migration_files()
        
        if not migration_files:
            return {
                'total_files': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'files': [],
                'summary': {
                    'errors': ['No se encontraron archivos de migración'],
                    'warnings': []
                }
            }
        
        print(f"🔍 Validando {len(migration_files)} archivos de migración...")
        
        results = []
        valid_count = 0
        
        for file_path in sorted(migration_files):
            validation_result = self.validate_migration_file(file_path)
            results.append(validation_result)
            
            if validation_result['valid']:
                valid_count += 1
                print(f"  ✅ {file_path.name}")
            else:
                print(f"  ❌ {file_path.name}")
                for error in validation_result['errors']:
                    print(f"      • {error}")
        
        # Generar resumen
        summary = self._generate_summary(results)
        
        return {
            'total_files': len(migration_files),
            'valid_files': valid_count,
            'invalid_files': len(migration_files) - valid_count,
            'files': results,
            'summary': summary
        }

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera resumen de la validación"""
        all_errors = []
        all_warnings = []
        total_inserts = 0
        migration_types = {'individual': 0, 'múltiple': 0, 'consolidada': 0}
        
        for result in results:
            all_errors.extend(result['errors'])
            all_warnings.extend(result['warnings'])
            
            if 'insert_count' in result['stats']:
                total_inserts += result['stats']['insert_count']
            
            migration_type = result['stats'].get('type', 'desconocido')
            if migration_type in migration_types:
                migration_types[migration_type] += 1
        
        return {
            'errors': list(set(all_errors)),  # Eliminar duplicados
            'warnings': list(set(all_warnings)),
            'total_inserts': total_inserts,
            'migration_types': migration_types
        }

    def print_detailed_report(self, validation_result: Dict[str, Any]):
        """Imprime reporte detallado de validación"""
        print(f"\n📊 REPORTE DE VALIDACIÓN DETALLADO")
        print("=" * 50)
        
        print(f"📁 Total de archivos: {validation_result['total_files']}")
        print(f"✅ Archivos válidos: {validation_result['valid_files']}")
        print(f"❌ Archivos inválidos: {validation_result['invalid_files']}")
        
        if validation_result['summary']['total_inserts'] > 0:
            print(f"📝 Total de registros a insertar: {validation_result['summary']['total_inserts']}")
        
        # Tipos de migración
        types = validation_result['summary']['migration_types']
        if any(types.values()):
            print(f"\n📋 Tipos de migración:")
            for migration_type, count in types.items():
                if count > 0:
                    print(f"  • {migration_type.capitalize()}: {count}")
        
        # Errores globales
        if validation_result['summary']['errors']:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for error in validation_result['summary']['errors']:
                print(f"  • {error}")
        
        # Advertencias globales
        if validation_result['summary']['warnings']:
            print(f"\n⚠️  ADVERTENCIAS:")
            for warning in validation_result['summary']['warnings']:
                print(f"  • {warning}")
        
        # Resultado final
        if validation_result['invalid_files'] == 0:
            print(f"\n🎉 ¡TODAS LAS MIGRACIONES SON VÁLIDAS!")
            print(f"✅ Las migraciones están listas para ser ejecutadas")
        else:
            print(f"\n⚠️  Se encontraron {validation_result['invalid_files']} archivos con problemas")
            print(f"🔧 Revisa los errores antes de ejecutar las migraciones")


def main():
    """Función principal"""
    print("🔍 VALIDADOR DE MIGRACIONES TYPEORM")
    print("=" * 40)
    
    try:
        validator = MigrationValidator()
        validation_result = validator.validate_all_migrations()
        validator.print_detailed_report(validation_result)
        
        # Código de salida basado en validación
        if validation_result['invalid_files'] == 0 and validation_result['total_files'] > 0:
            return 0  # Éxito
        else:
            return 1  # Error o no hay archivos
            
    except Exception as e:
        print(f"\n💥 Error crítico: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
