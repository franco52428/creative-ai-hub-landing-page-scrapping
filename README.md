# 🤖 Enhanced Futurepedia AI Tools Scraper

Sistema profesional de scraping para herramientas de IA desde Futurepedia.io con capacidades avanzadas de procesamiento, traducciones automáticas y arquitectura híbrida FetchFox + BeautifulSoup.

## ✨ Características Profesionales

### 🔥 **Arquitectura Híbrida Avanzada**
- **FetchFox API**: Scraping principal con alta eficiencia
- **BeautifulSoup Fallback**: Respaldo automático para máxima robustez
- **Concurrent Processing**: Hasta 12 workers paralelos por categoría
- **Smart Retry Logic**: Sistema inteligente de reintentos con backoff

### 🌍 **Traducciones AI-Powered**
- **OpenRouter Integration**: Traducciones automáticas con DeepSeek
- **5 Idiomas Soportados**: Español, Francés, Alemán, Portugués, Italiano  
- **Preservación de Contexto**: Mantiene terminología técnica correcta
- **Rate Limiting Inteligente**: Gestión automática de límites API

### 📊 **Procesamiento Batch Profesional**
- **Modo `--all`**: Procesamiento automático de todas las categorías
- **CSV-Driven**: Configuración basada en archivo CSV centralizado
- **Progress Tracking**: Progreso detallado `[X/14]` categorías
- **Error Recovery**: Continúa con siguiente categoría si una falla

### 🗂️ **Gestión de Datos Inteligente**
- **Detección de Duplicados**: Evita re-scraping de herramientas existentes
- **Resume Capability**: Reanuda desde última herramienta procesada
- **Structured Output**: JSON individual + CSV consolidado por categoría
- **Smart Pagination**: Detección automática de páginas con contenido

## 🏗️ Estructura del Proyecto

```
scraping/
├── 📁 scrapers/
│   ├── futurepedia_scraper.py   # Enhanced scraper engine
│   └── __init__.py              # Package initialization
├── 📁 outputs/                  # Generated data
│   ├── json/                    # Individual tool files
│   └── csv/                     # Category consolidated data  
├── 📁 .github/                  # Project documentation
│   └── instructions/            # Architecture & rules
├── 🔧 scrape.py                 # CLI orchestrator
├── 🚀 run_scraping.sh           # Professional execution script
├── 📋 futurepeida_io_categories.csv  # Category URLs
├── ⚙️ requirements.txt          # Python dependencies
├── 🔐 .env                      # API keys configuration
└── 📖 README.md                 # This file
```

## �️ Migraciones TypeORM

El proyecto incluye un sistema profesional para generar migraciones TypeORM a partir de los datos scrapeados:

```bash
# Generar todas las migraciones
./generate_migrations.sh
```

**Estructura de salida:**
```
migrations/
├── tools_migrations/         # Archivos .ts de migraciones
├── generate_migrations.py   # Generador principal
├── validate_migrations.py   # Validador
└── README.md                # Documentación técnica
```

Ver documentación completa en: [`migrations/README.md`](migrations/README.md)

## �🚀 Instalación y Configuración

### 1. **Clonar el Repositorio**
```bash
git clone <repository-url>
cd scraping
```

### 2. **Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### 3. **Configurar Variables de Entorno**
Crear archivo `.env`:
```bash
# APIs requeridas
FETCHFOX_API_KEY=tu_clave_fetchfox_aqui
OPENROUTER_API_KEY=tu_clave_openrouter_aqui

# Configuración opcional
ENABLE_FETCHFOX=true
ENABLE_TRANSLATIONS=true
TARGET_LANGUAGES=es,fr,de,pt,it
DEFAULT_MAX_WORKERS=8
DEFAULT_REQUEST_DELAY=2
DEFAULT_TIMEOUT=30
```

### 4. **Obtener API Keys**

#### **FetchFox API** (Scraping Principal)
- Registro: [fetchfoxai.com](https://fetchfoxai.com)
- Plan gratuito: 1,000 requests/mes
- Plan Pro: $20/mes para proyectos escalables

#### **OpenRouter API** (Traducciones AI)
- Registro: [openrouter.ai](https://openrouter.ai)  
- Créditos gratuitos al registro
- Modelo usado: `deepseek/deepseek-chat` (económico y eficiente)

## 🎯 Uso Profesional

### **Comando Básico - Una Categoría**
```bash
python3 scrape.py --category "https://www.futurepedia.io/ai-tools/personal-assistant" --max-workers 8
```

### **Comando Profesional - Todas las Categorías**
```bash
python3 scrape.py --all --csv futurepeida_io_categories.csv --max-workers 12
```

### **Script de Ejecución Automática**
```bash
./run_scraping.sh
```

### **Opciones Disponibles**
```bash
python3 scrape.py --help

Options:
  --category CATEGORY       URL de categoría específica a scrapear
  --all                     Procesar todas las categorías del CSV
  --csv CSV                 Archivo CSV de categorías (default: futurepeida_io_categories.csv)
  --max-workers MAX_WORKERS Hilos paralelos por categoría (default: 4)
```

## 📈 Capacidades y Rendimiento

### **Volumen de Datos**
- **14+ categorías** disponibles en CSV
- **~200-250 herramientas** por categoría (promedio)
- **Total estimado: ~3,000 herramientas**
- **Tiempo estimado: 2-3 horas** (modo profesional completo)

### **Rendimiento Optimizado**
- **Concurrent Processing**: 12 workers simultáneos
- **Smart Caching**: Evita re-scraping de datos existentes
- **Pagination Detection**: Automática hasta final de contenido
- **Error Recovery**: Continúa automáticamente ante fallos temporales

### **Ejemplo de Rendimiento Real**
```
✅ Categoría: AI Personal Assistant Tools
   - 215 herramientas scrapeadas
   - Tiempo: 4.5 minutos
   - Workers: 8 paralelos
   - Success rate: 100%
```

## 🗃️ Estructura de Datos

### **Output JSON (por herramienta)**
```json
{
    "name": "Tool Name",
    "url": "https://www.futurepedia.io/tool/tool-name",
    "description": "Tool description...",
    "category": "personal-assistant",
    "pricing": "Free/Paid/Freemium", 
    "features": ["feature1", "feature2"],
    "translations": {
        "es": { "name": "Nombre", "description": "Descripción..." },
        "fr": { "name": "Nom", "description": "Description..." }
    },
    "scraped_at": "2025-08-29T10:30:00Z"
}
```

### **Output CSV (por categoría)**  
```csv
name,url,description,category,pricing,features,scraped_at
Tool Name,https://...,Description...,personal-assistant,Free,"feature1,feature2",2025-08-29T10:30:00Z
```

## 🔧 Arquitectura Técnica

### **Hybrid Scraping Strategy**
1. **Primary**: FetchFox API para requests complejos
2. **Fallback**: BeautifulSoup para máxima compatibilidad  
3. **Smart Detection**: Automática según response y disponibilidad

### **AI Translation Pipeline**  
1. **Content Extraction**: Texto base en inglés
2. **OpenRouter Processing**: DeepSeek model para traducciones
3. **Context Preservation**: Mantiene terminología técnica
4. **Quality Assurance**: Validación automática de output

### **Concurrent Architecture**
```python
# Ejemplo de configuración interna
ThreadPoolExecutor(max_workers=12) 
├── Tool 1 Scraping + Translation
├── Tool 2 Scraping + Translation  
├── Tool 3 Scraping + Translation
└── ... (hasta 12 simultáneos)
```

## 📊 Monitoreo y Logs

### **Logging Estructurado**
```bash
tail -f scraping.log
```

### **Métricas en Tiempo Real**
- Herramientas procesadas por minuto
- Success/failure rates por categoría  
- Tiempo estimado de finalización
- Usage de APIs (FetchFox + OpenRouter)

### **Ejemplo de Log Output**
```
2025-08-29 10:30:15 | INFO | [1/14] Procesando: AI Personal Assistant Tools
2025-08-29 10:30:16 | INFO | 215 tools encontradas | a procesar: 200 | ya vistas: 15
2025-08-29 10:32:45 | INFO | ✅ Categoría completada: 215 herramientas en 2.5 min
2025-08-29 10:32:46 | INFO | [2/14] Procesando: Research Assistant Tools...
```

## 🛠️ Solución de Problemas

### **Errores Comunes**

#### **API Key Missing**
```bash
Error: FETCHFOX_API_KEY not found in environment
```
**Solución**: Verificar archivo `.env` con las API keys correctas

#### **Rate Limit Exceeded**  
```bash
Warning: OpenRouter rate limit hit, retrying in 60s...
```
**Solución**: El sistema maneja automáticamente con backoff inteligente

#### **Connection Timeout**
```bash
Error: Timeout connecting to Futurepedia
```
**Solución**: Verificar conexión a internet, el sistema reintentará automáticamente

### **Optimización de Rendimiento**

#### **Para Proyectos Grandes**
```bash
# Reducir workers si hay timeouts
python3 scrape.py --all --max-workers 6

# Para conexiones lentas  
python3 scrape.py --all --max-workers 4
```

#### **Para Máximo Rendimiento**
```bash
# Configuración agresiva (requiere APIs premium)
python3 scrape.py --all --max-workers 16
```

## 🔄 Actualizaciones y Mantenimiento

### **Actualizar Categorías**
Editar `futurepeida_io_categories.csv`:
```csv
Category
https://www.futurepedia.io/ai-tools/nueva-categoria
```

### **Backup de Datos**
```bash
# Backup automático de outputs
tar -czf backup_$(date +%Y%m%d).tar.gz outputs/
```

### **Limpiar Cache**
```bash
# Limpiar datos antiguos para re-scraping completo
rm -rf outputs/json/* outputs/csv/*
```

## 📞 Soporte y Contribuciones

### **Reportar Issues**
- Incluir logs relevantes de `scraping.log`
- Especificar configuración de `.env` (sin API keys)
- Describir comportamiento esperado vs actual

### **Mejoras Futuras Planificadas**
- [ ] Dashboard web para monitoreo en tiempo real
- [ ] Soporte para más sitios (ProductHunt, etc.)
- [ ] API REST para consulta de datos scrapeados
- [ ] Clasificación automática por tags ML
- [ ] Integración con bases de datos (PostgreSQL/MongoDB)

---

## ⚡ Quick Start

```bash
# Setup completo en 3 comandos
pip install -r requirements.txt
cp .env.example .env  # Editar con tus API keys
./run_scraping.sh     # Ejecutar modo profesional
```

**🎉 ¡Tu scraper profesional de herramientas AI está listo!**

## 🚀 Instalación

1. **Clonar el repositorio** (si corresponde) o navegar al directorio:
```bash
cd /home/jhoto/tools-hub-ai/scraping
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno** (opcional):
```bash
# Las configuraciones por defecto están en .env
# Puedes modificar según tus necesidades
```

## 📖 Uso

### Scraping de Categorías

#### 1. Scraping de una categoría específica
```bash
python main.py --category "https://www.futurepedia.io/ai-tools/personal-assistant"
```

#### 2. Scraping de todas las categorías
```bash
python main.py --all
```

### Gestión de Datos

#### Ver estadísticas del scraping
```bash
python utils.py --stats
```

#### Generar CSV maestro con todas las herramientas
```bash
python utils.py --master-csv
```

#### Limpiar herramientas incompletas
```bash
python utils.py --clean
```

#### Listar todas las categorías encontradas
```bash
python utils.py --categories
```

## Estructura de Datos

Cada herramienta se almacena como un archivo JSON con la siguiente estructura:

```json
{
    "slug": "nombre-herramienta",
    "image_url": "https://example.com/image.jpg",
    "redirect_url": "https://herramienta-oficial.com",
    "demo_url": "https://demo.herramienta.com",
    "technical_requirements": "Navegador web moderno, conexión a internet",
    "searchIndexEn": "términos de búsqueda en inglés",
    "searchIndexEs": "términos de búsqueda en español",
    "translations": {
        "es": {
            "title": "Nombre de la Herramienta",
            "shortDescription": "Descripción corta",
            "longDescription": "Descripción detallada",
            "tags": "etiquetas, separadas, por, comas",
            "pricingInfo": "Información de precios",
            "category": "categoria",
            "appType": "tipo-de-aplicacion"
        },
        "en": { ... },
        "pt": { ... },
        "fr": { ... },
        "de": { ... }
    }
}
```

## 🔧 Configuración

### Variables de Entorno (.env)

```bash
# Configuración de scraping
DELAY_BETWEEN_REQUESTS=2      # Segundos entre peticiones
MAX_RETRIES=3                 # Máximo número de reintentos
TIMEOUT=30                    # Timeout en segundos

# Directorios
TOOLS_DIR=tools               # Directorio para JSONs individuales
DATA_DIR=data                # Directorio para CSVs consolidados

# URLs base
BASE_URL=https://www.futurepedia.io
CATEGORY_BASE_URL=https://www.futurepedia.io/ai-tools

# Paginación
MAX_PAGES_PER_CATEGORY=50     # Máximo páginas por categoría
ITEMS_PER_PAGE=20            # Items esperados por página
```

## 📈 Categorías Disponibles

El archivo `futurepeida_io_categories.csv` contiene las categorías a procesar:

- AI Personal Assistant Tools
- Research Assistant Tools
- Spreadsheet Assistant Tools
- Translators
- Presentations
- Email Assistant
- Search Engine
- Prompt Generators
- Writing Generators
- Storyteller
- Summarizer
- Code Assistant
- No Code
- SQL Assistant

## 🚦 Proceso de Scraping

1. **Carga de categoría**: Lee la URL de la categoría
2. **Descubrimiento de herramientas**: Navega por todas las páginas de la categoría
3. **Extracción de datos**: Para cada herramienta, extrae información detallada
4. **Procesamiento de datos**: Aplica transformaciones y traducciones
5. **Almacenamiento**: Guarda JSON individual y actualiza CSV de categoría

## 📋 Archivos Generados

### Por Categoría:
- `data/{categoria}_tools.csv` - CSV con todas las herramientas de la categoría
- `tools/{slug}.json` - JSON individual por cada herramienta

### Consolidados:
- `data/master_tools.csv` - CSV maestro con todas las herramientas
- `scraping.log` - Log detallado de todas las operaciones

## 🛠️ Características Técnicas

- **Manejo de errores robusto** con reintentos automáticos
- **Rate limiting** para evitar bloqueos
- **User Agent rotation** para evitar detección
- **Logging estructurado** con correlación de eventos
- **Extracción flexible** que se adapta a cambios en el sitio
- **Validación de datos** antes del almacenamiento

## 🔍 Monitoreo y Logs

Los logs se guardan en `scraping.log` e incluyen:
- Inicio y fin de operaciones
- Errores y advertencias
- Estadísticas de progreso
- URLs procesadas
- Datos extraídos

Ejemplo de log:
```
2025-08-27 10:30:15,123 - INFO - Starting to scrape category: https://www.futurepedia.io/ai-tools/personal-assistant
2025-08-27 10:30:17,456 - INFO - Found 25 tools on page 1
2025-08-27 10:30:20,789 - INFO - Scraping tool 1/25: ChatGPT Assistant
2025-08-27 10:30:23,012 - INFO - Saved tool data to tools/chatgpt-assistant.json
```

## 📊 Métricas de Calidad

El sistema rastrea automáticamente:
- Número de herramientas extraídas por categoría
- Porcentaje de herramientas con imágenes
- Porcentaje de herramientas con URLs de redirección
- Herramientas con datos incompletos

## 🚨 Consideraciones Importantes

### Respeto por el Sitio Web
- Delays configurables entre peticiones
- User agents realistas
- Respeto por robots.txt
- Monitoreo de códigos de respuesta

### Calidad de Datos
- Validación automática de campos requeridos
- Limpieza de datos inconsistentes
- Detección de duplicados
- Verificación de URLs

### Escalabilidad
- Arquitectura modular para agregar nuevos sitios
- Procesamiento por lotes
- Almacenamiento eficiente
- Capacidad de resumir scraping interrumpido

## 🔄 Próximos Pasos

1. **Completar Futurepedia**: Procesar todas las categorías disponibles
2. **Agregar más sitios**: Integrar otros directorios de IA
3. **Mejorar traducciones**: Implementar servicio de traducción automática
4. **Sistema de ranking**: Integrar sistema de puntuación y comentarios
5. **API**: Crear API REST para acceso a los datos
6. **Dashboard**: Interfaz web para gestión y visualización

## 🤝 Contribuciones

Para agregar nuevos scrapers o mejorar los existentes:

1. Crear nuevo scraper en `scrapers/`
2. Seguir la interfaz establecida
3. Actualizar configuración en `config/settings.py`
4. Agregar tests y documentación
5. Actualizar este README

## 📞 Soporte

Para problemas o mejoras, revisar:
- Logs en `scraping.log`
- Configuración en `.env`
- Estadísticas con `python utils.py --stats`

---

**Última actualización**: 27 de Agosto, 2025
**Versión**: 1.0.0
**Estado**: Producción - Primera categoría lista para scraping
