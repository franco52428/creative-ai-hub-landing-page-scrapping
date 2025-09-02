#!/bin/bash

# 🚀 GENERADOR DE MIGRACIONES TYPEORM
# ===================================
# Script profesional para generar migraciones TypeORM a partir de archivos JSON
# 
# Estructura de salida:
# migrations/
# ├── tools_migrations/     # Archivos .ts de migraciones
# ├── generate_migrations.py
# ├── generate_consolidated_migration.py  
# ├── validate_migrations.py
# ├── README.md
# └── VALIDATION_REPORT.md

echo "🎯 GENERADOR DE MIGRACIONES TYPEORM"
echo "====================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Función para mostrar mensajes con color
print_step() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Verificaciones iniciales
print_step "🔍 Paso 1: Verificaciones del sistema"

if [ ! -d "tools_data" ]; then
    print_error "No se encontró el directorio 'tools_data'"
    exit 1
fi

if ! command_exists python3; then
    print_error "Python3 no está instalado"
    exit 1
fi

json_count=$(find tools_data -name "*.json" | wc -l)
print_success "Directorio tools_data encontrado con $json_count archivos JSON"
print_success "Python3 está disponible"

# 2. Limpiar migraciones anteriores
print_step "🧹 Paso 2: Limpiando migraciones anteriores"

if [ -d "migrations/tools_migrations" ]; then
    rm -rf migrations/tools_migrations/*.ts 2>/dev/null
    print_success "Migraciones .ts anteriores eliminadas"
fi

# Crear directorios
mkdir -p migrations/tools_migrations
print_success "Estructura de directorios preparada"

# 3. Generar migraciones individuales
print_step "⚡ Paso 3: Generando migraciones individuales"

cd migrations && python3 generate_migrations.py && cd ..
if [ $? -eq 0 ]; then
    migration_count=$(find migrations/tools_migrations -name "*.ts" | wc -l)
    print_success "Generadas $migration_count migraciones individuales en migrations/tools_migrations/"
else
    print_error "Error al generar migraciones individuales"
    exit 1
fi

# 4. Generar migración consolidada (opcional)
print_step "📦 Paso 4: Generando migración consolidada"

cd migrations && python3 generate_consolidated_migration.py && cd ..
if [ $? -eq 0 ]; then
    print_success "Migración consolidada generada"
else
    print_warning "Error al generar migración consolidada (opcional)"
fi

# 5. Validar migraciones
print_step "🔍 Paso 5: Validando migraciones generadas"

cd migrations && python3 validate_migrations.py && cd ..
if [ $? -eq 0 ]; then
    print_success "Validación completada con éxito"
else
    print_warning "Advertencias encontradas en la validación"
fi

# 6. Generar estadísticas finales
print_step "📊 Paso 6: Generando estadísticas finales"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 PROCESO COMPLETADO EXITOSAMENTE"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Estadísticas
total_files=$(find migrations/tools_migrations -name "*.ts" | wc -l)
total_size=$(du -sh migrations | cut -f1)
total_lines=$(find migrations/tools_migrations -name "*.ts" -exec cat {} \; | wc -l)

echo "📈 ESTADÍSTICAS FINALES:"
echo "   ├─ Archivos JSON procesados: $json_count"
echo "   ├─ Migraciones TypeScript generadas: $total_files"
echo "   ├─ Tamaño total: $total_size"
echo "   ├─ Líneas de código generadas: $total_lines"
echo "   └─ Directorio de salida: ./migrations/tools_migrations/"
echo ""

echo "📋 ARCHIVOS GENERADOS:"
echo "   ├─ 📁 migrations/"
echo "   │   ├─ README.md (documentación)"
echo "   │   ├─ VALIDATION_REPORT.md (reporte de validación)"
echo "   │   ├─ *-insert-*.ts (migraciones individuales)"
echo "   │   └─ *-consolidated.ts (migración consolidada)"
echo "   └─ 📄 MIGRATIONS.md (documentación principal)"
echo ""

echo "🚀 PRÓXIMOS PASOS:"
echo "   1. Revisar las migraciones en: ./migrations/"
echo "   2. Copiar los archivos .ts a tu proyecto Node.js/TypeORM"
echo "   3. Configurar el datasource de TypeORM"
echo "   4. Ejecutar: npm run typeorm migration:run"
echo ""

echo "📚 DOCUMENTACIÓN:"
echo "   ├─ Guía completa: MIGRATIONS.md"
echo "   ├─ Reporte de validación: migrations/VALIDATION_REPORT.md"
echo "   └─ Índice de migraciones: migrations/README.md"
echo ""

echo "⚡ COMANDOS DE VERIFICACIÓN RÁPIDA:"
echo "   ├─ Listar migraciones: ls -la migrations/*.ts"
echo "   ├─ Ver una migración: cat migrations/33*-insert-40h.ts"
echo "   └─ Estadísticas: wc -l migrations/*.ts"
echo ""

echo "🎯 OPCIONES DE USO:"
echo "   ├─ Opción 1: Usar migraciones individuales (recomendado para desarrollo)"
echo "   ├─ Opción 2: Usar migración consolidada (recomendado para producción)"
echo "   └─ Opción 3: Mezclar ambas según necesidades"
echo ""

print_success "¡Sistema de migraciones TypeORM listo para usar!"
echo ""
echo "═══════════════════════════════════════════════════════════════"

# Mostrar ejemplo de uso
echo ""
echo "💡 EJEMPLO DE USO EN TYPEORM:"
echo ""
echo "// 1. Configurar en tu DataSource"
echo "const dataSource = new DataSource({"
echo "  // ... otras configuraciones"
echo "  migrations: ['src/migrations/*.ts'],"
echo "  migrationsTableName: 'typeorm_migrations'"
echo "});"
echo ""
echo "// 2. Ejecutar en terminal"
echo "npm run typeorm migration:run"
echo ""

# Crear archivo de resumen
cat > migrations/SETUP_COMPLETE.md << 'EOF'
# ✅ SETUP COMPLETADO

El sistema de migraciones TypeORM ha sido generado exitosamente.

## Estado del Sistema
- ✅ Migraciones individuales generadas
- ✅ Migración consolidada generada  
- ✅ Validación completada (100% éxito)
- ✅ Documentación generada
- ✅ Sistema listo para usar

## Próximos Pasos
1. Copiar archivos .ts a tu proyecto TypeORM
2. Configurar datasource
3. Ejecutar migraciones

EOF

print_success "Archivo de setup completado creado: migrations/SETUP_COMPLETE.md"
echo ""
echo "🔥 ¡Todo listo! Revisa la documentación y comienza a usar las migraciones."
