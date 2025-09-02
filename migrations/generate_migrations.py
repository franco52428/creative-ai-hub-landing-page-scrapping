#!/usr/bin/env python3
"""
Generador de Migraciones TypeORM Individuales
============================================

Este script genera migraciones TypeORM individuales para cada herramienta AI
desde los archivos JSON en tools_data/.

Autor: Sistema de Migraciones AI Hub
Fecha: Septiembre 2025
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


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


class MigrationGenerator:
    def __init__(self):
        self.project_root = get_project_root()
        self.tools_data_dir = self.project_root / "tools_data"
        self.migrations_dir = self.project_root / "migrations" / "tools_migrations"
        
        # Crear directorio de migraciones si no existe
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Directorio del proyecto: {self.project_root}")
        print(f"📁 Datos de herramientas: {self.tools_data_dir}")
        print(f"📁 Migraciones de salida: {self.migrations_dir}")

    def sanitize_filename(self, name: str) -> str:
        """Convierte nombre de herramienta a nombre válido para archivo/clase"""
        # Reemplazar caracteres especiales
        name = name.replace("-", "_").replace(" ", "_").replace(".", "_")
        name = "".join(c for c in name if c.isalnum() or c == "_")
        
        # Asegurar que empiece con letra
        if name and name[0].isdigit():
            name = f"Tool_{name}"
        
        return name or "UnknownTool"

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

    def generate_migration_content(self, tool_data: Dict[str, Any], class_name: str, timestamp: str) -> str:
        """Genera el contenido de la migración TypeORM"""
        
        # Extraer valores con valores por defecto
        fields = {
            'uuid': f"gen_random_uuid()",  # Función PostgreSQL para UUID
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

        values_str = ",\n            ".join(insert_values)

        return f'''import {{ MigrationInterface, QueryRunner }} from "typeorm";

export class {class_name}{timestamp} implements MigrationInterface {{
    name = '{class_name}{timestamp}'

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
            ) VALUES (
                {values_str}
            );
        `);
    }}

    public async down(queryRunner: QueryRunner): Promise<void> {{
        await queryRunner.query(`
            DELETE FROM landing_ia_catalog_item 
            WHERE name = {self.escape_sql_value(fields['name'])};
        `);
    }}
}}
'''

    def generate_migrations(self) -> List[str]:
        """Genera todas las migraciones individuales"""
        json_files = list(self.tools_data_dir.glob("*.json"))
        
        if not json_files:
            print("❌ No se encontraron archivos JSON en tools_data/")
            return []

        print(f"📊 Procesando {len(json_files)} herramientas...")
        
        generated_files = []
        errors = []
        base_timestamp = datetime.now().strftime("%Y%m%d%H%M")
        
        for i, json_file in enumerate(sorted(json_files)):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    tool_data = json.load(f)
                
                # Generar nombre de clase y timestamp único
                tool_name = tool_data.get('name', json_file.stem)
                class_name = f"Add{self.sanitize_filename(tool_name)}"
                timestamp = f"{base_timestamp}{i:02d}"  # Timestamp único por archivo
                
                # Generar contenido de migración
                migration_content = self.generate_migration_content(tool_data, class_name, timestamp)
                
                # Guardar archivo
                filename = f"{timestamp}-{class_name}.ts"
                file_path = self.migrations_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(migration_content)
                
                generated_files.append(filename)
                
                if (i + 1) % 50 == 0:  # Progreso cada 50 archivos
                    print(f"  ✅ Procesados {i + 1}/{len(json_files)} archivos...")
                
            except Exception as e:
                error_msg = f"Error procesando {json_file.name}: {str(e)}"
                errors.append(error_msg)
                print(f"  ⚠️  {error_msg}")
        
        # Resumen final
        print(f"\n📈 RESUMEN DE GENERACIÓN:")
        print(f"  ✅ Archivos procesados exitosamente: {len(generated_files)}")
        print(f"  ❌ Errores encontrados: {len(errors)}")
        
        if errors:
            print(f"\n⚠️  ERRORES DETALLADOS:")
            for error in errors[:5]:  # Mostrar solo los primeros 5 errores
                print(f"    • {error}")
            if len(errors) > 5:
                print(f"    • ... y {len(errors) - 5} errores más")
        
        print(f"\n📁 Migraciones generadas en: {self.migrations_dir}")
        
        return generated_files


def main():
    """Función principal"""
    print("🚀 GENERADOR DE MIGRACIONES TYPEORM - INDIVIDUALES")
    print("=" * 55)
    
    try:
        generator = MigrationGenerator()
        generated_files = generator.generate_migrations()
        
        if generated_files:
            print(f"\n🎉 ¡Proceso completado! Se generaron {len(generated_files)} migraciones.")
            print(f"📂 Ubicación: {generator.migrations_dir}")
            return 0
        else:
            print("\n❌ No se generaron migraciones.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Error crítico: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
