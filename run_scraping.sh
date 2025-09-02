#!/bin/bash
# Script para ejecutar el Enhanced Futurepedia Scraper

echo "=== Enhanced Futurepedia Scraper ==="
echo "Verificando configuración del proyecto..."

#!/bin/bash

# Script para ejecutar el scraping de Futurepedia
# Modo profesional: scraping de todas las categorías

set -e  # Detener si hay errores

echo "======================================"
echo "🚀 FUTUREPEDIA AI TOOLS SCRAPER - MODO PROFESIONAL"
echo "======================================"

# Verificar dependencias
echo "🔍 Verificando dependencias..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    exit 1
fi

# Verificar archivo de requerimientos
if [ ! -f "requirements.txt" ]; then
    echo "❌ No se encuentra requirements.txt"
    exit 1
fi

# Verificar .env
if [ ! -f ".env" ]; then
    echo "❌ No se encuentra el archivo .env"
    echo "📝 Crea un archivo .env con las siguientes variables:"
    echo "FETCHFOX_API_KEY=tu_clave_aqui"
    echo "OPENROUTER_API_KEY=tu_clave_aqui"
    exit 1
fi

# Verificar archivo de categorías
if [ ! -f "futurepeida_io_categories.csv" ]; then
    echo "❌ No se encuentra el archivo futurepeida_io_categories.csv"
    exit 1
fi

# Verificar estructura de directorios
echo "📁 Verificando estructura de directorios..."
mkdir -p outputs/{json,csv}
mkdir -p logs

echo "✅ Dependencias verificadas"

# Mostrar información de categorías
echo ""
echo "📋 INFORMACIÓN DE CATEGORÍAS:"
TOTAL_CATEGORIES=$(tail -n +2 futurepeida_io_categories.csv | wc -l)
echo "   - Total de categorías a procesar: $TOTAL_CATEGORIES"
echo ""

# Ejecutar scraping
echo "🔥 Iniciando scraping profesional de todas las categorías..."
echo "📅 $(date)"
echo ""

# Parametros configurables
CSV_FILE="futurepeida_io_categories.csv"
MAX_WORKERS=12

echo "📋 Configuración:"
echo "   - Archivo CSV: $CSV_FILE"
echo "   - Workers por categoría: $MAX_WORKERS"
echo "   - Modo: Procesamiento de todas las categorías"
echo ""

# Ejecutar el scraper en modo profesional
python3 scrape.py --all --csv "$CSV_FILE" --max-workers $MAX_WORKERS

SCRAPING_EXIT_CODE=$?

echo ""
echo "======================================"
if [ $SCRAPING_EXIT_CODE -eq 0 ]; then
    echo "✅ SCRAPING PROFESIONAL COMPLETADO EXITOSAMENTE"
    
    # Mostrar estadísticas completas
    echo ""
    echo "📊 ESTADÍSTICAS FINALES:"
    
    # Contar archivos JSON generados
    JSON_COUNT=$(find outputs/json -name "*.json" 2>/dev/null | wc -l)
    echo "   - Total herramientas scrapeadas: $JSON_COUNT"
    
    # Contar archivos CSV generados por categoría
    CSV_COUNT=$(find outputs/csv -name "*.csv" 2>/dev/null | wc -l)
    echo "   - Categorías procesadas (CSV): $CSV_COUNT"
    
    # Mostrar tamaño de datos
    TOTAL_SIZE=$(du -sh outputs/ 2>/dev/null | cut -f1)
    echo "   - Tamaño total de datos: $TOTAL_SIZE"
    
    # Mostrar archivos CSV generados
    echo ""
    echo "📁 ARCHIVOS CSV GENERADOS POR CATEGORÍA:"
    find outputs/csv -name "*.csv" -type f -printf '%T@ %p
' 2>/dev/null | sort -nr | cut -d' ' -f2- | sed 's/^/     - /'
    
    # Mostrar resumen por categoría si existe el log
    if [ -f "scraping.log" ]; then
        echo ""
        echo "📈 RESUMEN POR CATEGORÍA:"
        echo "   (Ver scraping.log para detalles completos)"
        grep -i "éxitos\|fallos\|total categorías" scraping.log | tail -5 | sed 's/^/     /'
    fi
    
else
    echo "❌ ERROR EN EL SCRAPING PROFESIONAL (código: $SCRAPING_EXIT_CODE)"
    echo "📝 Revisa scraping.log para más detalles"
    
    # Mostrar últimos errores del log
    if [ -f "scraping.log" ]; then
        echo ""
        echo "🔍 ÚLTIMOS ERRORES:"
        grep -i "error\|falló" scraping.log | tail -3 | sed 's/^/     /'
    fi
fi

echo ""
echo "📝 LOG COMPLETO: scraping.log"
echo "🕐 Finalizado: $(date)"
echo "======================================"

echo "Directorio del proyecto verificado"

# Verificar dependencias de Python
echo " Verificando dependencias de Python..."
python3 -c "
import sys
missing = []
try:
    import requests
except ImportError:
    missing.append('requests')
try:
    import bs4
except ImportError:
    missing.append('beautifulsoup4')
try:
    import retrying
except ImportError:
    missing.append('retrying')
try:
    import fake_useragent
except ImportError:
    missing.append('fake-useragent')

if missing:
    print(f' Faltan dependencias: {missing}')
    print('   Instalando automáticamente...')
    sys.exit(1)
else:
    print(' Todas las dependencias están disponibles')
"

# Instalar dependencias si faltan
if [ $? -ne 0 ]; then
    echo "Instalando dependencias..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo " Error instalando dependencias"
        exit 1
    fi
fi

# Verificar configuración
echo " Verificando configuración..."
if [ ! -f ".env" ]; then
    echo " Error: Archivo .env no encontrado"
    exit 1
fi

# Mostrar configuración actual
echo "📋 Configuración actual:"
source .env
echo "   - Delay entre requests: ${DELAY_BETWEEN_REQUESTS:-1.0}s"
echo "   - Máximo reintentos: ${MAX_RETRIES:-3}"
echo "   - Timeout: ${TIMEOUT:-30}s"
echo "   - FetchFox API: $([ -n "$FETCHFOX_API_KEY" ] && echo "✅ Configurado" || echo "❌ No configurado (usará fallback)")"
echo "   - OpenRouter API: $([ -n "$OPENROUTER_API_KEY" ] && echo "✅ Configurado" || echo "❌ No configurado (usará placeholders)")"

# Crear directorios necesarios
echo "📁 Creando directorios de salida..."
mkdir -p tools_data category_data

echo ""
echo "🚀 Iniciando scraping del Enhanced Futurepedia Scraper..."
echo "   Categoría objetivo: AI Personal Assistant Tools"
echo "   Modo: Híbrido (FetchFox + BeautifulSoup)"
echo "   Concurrencia: 4 workers por defecto"
echo ""

# Ejecutar el scraper con la nueva implementación
python3 scrape.py --category "AI Personal Assistant Tools" --max-workers 4

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ¡Scraping completado exitosamente!"
    echo ""
    echo "📊 Archivos generados:"
    
    # Contar archivos JSON generados
    json_count=$(find tools_data -name "*.json" 2>/dev/null | wc -l)
    csv_count=$(find category_data -name "*.csv" 2>/dev/null | wc -l)
    
    echo "   - Tools JSON: ${json_count} archivos en tools_data/"
    echo "   - Category CSV: ${csv_count} archivos en category_data/"
    
    if [ $json_count -gt 0 ]; then
        echo ""
        echo "📁 Ejemplos de archivos generados:"
        find tools_data -name "*.json" | head -3 | while read file; do
            echo "   - $file"
        done
    fi
    
    if [ $csv_count -gt 0 ]; then
        echo ""
        echo "📊 CSVs de categoría generados:"
        find category_data -name "*.csv" | head -3 | while read file; do
            echo "   - $file"
        done
    fi
    
    echo ""
    echo "📝 Para más categorías, ejecuta:"
    echo "   python3 scrape.py --category 'Nombre de Categoría'"
    echo ""
    echo "🔧 Para configurar APIs y mejorar funcionalidad:"
    echo "   - Edita .env y agrega FETCHFOX_API_KEY"
    echo "   - Edita .env y agrega OPENROUTER_API_KEY"
    
else
    echo ""
    echo "❌ Error durante el scraping"
    echo "   Revisa los logs para más detalles"
    echo "   Puedes intentar con menor concurrencia:"
    echo "   python3 scrape.py --category 'AI Personal Assistant Tools' --max-workers 2"
fi
