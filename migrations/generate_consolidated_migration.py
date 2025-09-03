import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


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


class ConsolidatedMigrationGenerator:
    def __init__(self):
        self.project_root = get_project_root()
        self.tools_data_dir = self.project_root / "tools_data"
        self.migrations_dir = self.project_root / "migrations" / "tools_migrations"
        
        # Crear directorio de migraciones si no existe
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Directorio del proyecto: {self.project_root}")
        print(f"Datos de herramientas: {self.tools_data_dir}")
        print(f"Migraciones de salida: {self.migrations_dir}")

    def escape_sql_value(self, value: Any) -> str:
        """Escapa valores para SQL de manera segura"""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escapar comillas simples duplicándolas
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, list):
            # Convertir array a JSON string
            json_str = json.dumps(value, ensure_ascii=False)
            escaped = json_str.replace("'", "''")
            return f"'{escaped}'"
        else:
            # Convertir a JSON para otros tipos
            json_str = json.dumps(value, ensure_ascii=False)
            escaped = json_str.replace("'", "''")
            return f"'{escaped}'"

    def generate_insert_values(self, tool_data: Dict[str, Any]) -> str:
        """Genera los valores para un INSERT de una herramienta"""
        
        # Extraer valores con valores por defecto
        fields = {
            'uuid': f"gen_random_uuid()",
            'name': tool_data.get('name', ''),
            'description': tool_data.get('description', ''),
            'short_description': tool_data.get('short_description', ''),
            'logo_url': tool_data.get('logo_url', ''),
            'website_url': tool_data.get('website_url', ''),
            'category': tool_data.get('category', ''),
            'tags': tool_data.get('tags', []),
            'pricing_type': tool_data.get('pricing_type', ''),
            'pricing_details': tool_data.get('pricing_details', ''),
            'features': tool_data.get('features', []),
            'use_cases': tool_data.get('use_cases', []),
            'rating': tool_data.get('rating', None),
            'reviews_count': tool_data.get('reviews_count', 0),
            'social_media': tool_data.get('social_media', {}),
            'created_at': "CURRENT_TIMESTAMP",
            'updated_at': "CURRENT_TIMESTAMP",
            'is_active': "true",
            'metadata': "{}"
        }

        # Construir valores para INSERT
        insert_values = []
        for key, value in fields.items():
            if key in ['uuid', 'created_at', 'updated_at'] or (key == 'is_active' and value == "true"):
                insert_values.append(value)  # Sin comillas para funciones
            else:
                insert_values.append(self.escape_sql_value(value))

        return "(" + ", ".join(insert_values) + ")"

    def generate_consolidated_migration(self) -> str:
        """Genera UNA migración con TODAS las herramientas"""
        json_files = list(self.tools_data_dir.glob("*.json"))
        
        if not json_files:
            print("No se encontraron archivos JSON en tools_data/")
            return ""

        print(f"📊 Procesando {len(json_files)} herramientas en una sola migración...")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        class_name = f"AddAllAiTools{timestamp}"
        
        # Procesar todos los archivos
        all_insert_values = []
        processed_count = 0
        errors = []
        
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    tool_data = json.load(f)
                
                insert_values = self.generate_insert_values(tool_data)
                all_insert_values.append(insert_values)
                processed_count += 1
                
                if processed_count % 50 == 0:  # Progreso cada 50 archivos
                    print(f"  ✅ Procesados {processed_count}/{len(json_files)} archivos...")
                
            except Exception as e:
                error_msg = f"Error procesando {json_file.name}: {str(e)}"
                errors.append(error_msg)
                print(f"  ⚠️  {error_msg}")

        if not all_insert_values:
            print("❌ No se pudieron procesar archivos JSON válidos")
            return ""

        # Generar contenido de migración consolidada
        values_section = ",\n            ".join(all_insert_values)
        
        migration_content = f'''import {{ MigrationInterface, QueryRunner }} from "typeorm";

export class {class_name} implements MigrationInterface {{
    name = '{class_name}'

    public async up(queryRunner: QueryRunner): Promise<void> {{
        await queryRunner.query(`
            INSERT INTO landing_ia_catalog_item (
                uuid,
                name,
                description,
                short_description,
                logo_url,
                website_url,
                category,
                tags,
                pricing_type,
                pricing_details,
                features,
                use_cases,
                rating,
                reviews_count,
                social_media,
                created_at,
                updated_at,
                is_active,
                metadata
            ) VALUES
            {values_section};
        `);
    }}

    public async down(queryRunner: QueryRunner): Promise<void> {{
        await queryRunner.query(`
            DELETE FROM landing_ia_catalog_item 
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
        `);
    }}
}}
'''

        # Guardar archivo
        filename = f"{timestamp}-{class_name}.ts"
        file_path = self.migrations_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(migration_content)

        # Resumen final
        print(f"\n📈 RESUMEN DE GENERACIÓN CONSOLIDADA:")
        print(f"  ✅ Herramientas procesadas: {processed_count}")
        print(f"  ❌ Errores encontrados: {len(errors)}")
        print(f"  📄 Archivo generado: {filename}")
        
        if errors:
            print(f"\n⚠️  ERRORES DETALLADOS:")
            for error in errors[:5]:  # Mostrar solo los primeros 5 errores
                print(f"    • {error}")
            if len(errors) > 5:
                print(f"    • ... y {len(errors) - 5} errores más")
        
        print(f"\n📁 Migración generada en: {file_path}")
        
        return filename


def main():
    """Función principal"""
    print("🚀 GENERADOR DE MIGRACIÓN TYPEORM - CONSOLIDADA")
    print("=" * 50)
    
    try:
        generator = ConsolidatedMigrationGenerator()
        generated_file = generator.generate_consolidated_migration()
        
        if generated_file:
            print(f"\n🎉 ¡Proceso completado! Migración consolidada generada.")
            print(f"📂 Ubicación: {generator.migrations_dir}")
            return 0
        else:
            print("\n❌ No se pudo generar la migración consolidada.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Error crítico: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
