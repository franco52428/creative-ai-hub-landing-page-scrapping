# 🚀 Sistema de Migraciones TypeORM - AI Tools Hub

## 📋 Descripción

Este directorio contiene un sistema completo para generar migraciones TypeORM a partir de los datos JSON de herramientas AI. El sistema procesa **216 herramientas** y genera migraciones listas para usar en proyectos Node.js con TypeORM.

## 📁 Estructura del Directorio

```
migrations/
├── 📄 README.md                           # Esta documentación
├── 📄 SETUP_COMPLETE.md                   # Guía de setup completo
├── 🐍 generate_migrations.py              # Generador de migraciones individuales
├── 🐍 generate_consolidated_migration.py  # Generador de migración consolidada
├── 🐍 validate_migrations.py              # Validador de migraciones
└── 📁 tools_migrations/                   # Archivos TypeScript generados
    ├── 📄 20250902144900-AddTool_40h.ts   # Migración individual (ejemplo)
    ├── 📄 20250902144901-Addabby.ts       # Migración individual (ejemplo)
    ├── ...                                 # 214 migraciones más
    └── 📄 20250902*-AddAllAiTools*.ts     # Migración consolidada (todas)
```

## 🎯 Archivos Generados

### ✅ Estadísticas Actuales
- **📊 Archivos procesados**: 216 archivos JSON
- **📄 Migraciones generadas**: 217 archivos TypeScript (.ts)
- **📝 Líneas de código**: 12,782 líneas
- **💾 Tamaño total**: 976KB
- **📋 Tipos**: 216 individuales + 1 consolidada

### 🔧 Scripts de Python

| Script | Propósito | Uso |
|--------|-----------|-----|
| `generate_migrations.py` | Genera una migración por cada herramienta | Ideal para desarrollo |
| `generate_consolidated_migration.py` | Genera UNA migración con todas las herramientas | Ideal para producción |
| `validate_migrations.py` | Valida que las migraciones estén bien formadas | Control de calidad |

## 🚀 Uso en Proyectos TypeORM

### 1. Copiar Migraciones
```bash
# Opción A: Usar migraciones individuales (recomendado para desarrollo)
cp migrations/tools_migrations/202509*-Add*.ts your-project/src/migrations/

# Opción B: Usar solo la migración consolidada (recomendado para producción)
cp migrations/tools_migrations/*AddAllAiTools*.ts your-project/src/migrations/
```

### 2. Configurar TypeORM DataSource
```typescript
// src/data-source.ts
import { DataSource } from "typeorm";

export const AppDataSource = new DataSource({
    type: "postgres",
    host: "localhost",
    port: 5432,
    username: "your_username",
    password: "your_password",
    database: "your_database",
    synchronize: false,
    logging: false,
    entities: ["src/entity/**/*.ts"],
    migrations: ["src/migrations/**/*.ts"],
    migrationsTableName: "typeorm_migrations",
    subscribers: ["src/subscriber/**/*.ts"],
});
```

### 3. Ejecutar Migraciones
```bash
# Instalar TypeORM CLI (si no está instalado)
npm install -g typeorm

# Ejecutar migraciones
npm run typeorm migration:run

# Verificar estado
npm run typeorm migration:show
```

## 🗃️ Esquema de Base de Datos

Las migraciones crean registros en la tabla `landing_ia_catalog_item` con estos campos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `uuid` | UUID | Identificador único (generado automáticamente) |
| `name` | VARCHAR | Nombre de la herramienta AI |
| `description` | TEXT | Descripción completa |
| `short_description` | VARCHAR | Descripción corta |
| `logo_url` | VARCHAR | URL del logo |
| `website_url` | VARCHAR | URL del sitio web |
| `category` | VARCHAR | Categoría de la herramienta |
| `tags` | JSON | Array de tags |
| `pricing_type` | VARCHAR | Tipo de pricing (free, paid, freemium) |
| `pricing_details` | TEXT | Detalles del pricing |
| `features` | JSON | Array de características |
| `use_cases` | JSON | Array de casos de uso |
| `rating` | DECIMAL | Calificación (1-5) |
| `reviews_count` | INTEGER | Número de reviews |
| `social_media` | JSON | Enlaces de redes sociales |
| `created_at` | TIMESTAMP | Fecha de creación |
| `updated_at` | TIMESTAMP | Fecha de actualización |
| `is_active` | BOOLEAN | Estado activo/inactivo |
| `metadata` | JSON | Metadatos adicionales |

## 🔄 Regenerar Migraciones

Para regenerar las migraciones (desde el directorio raíz del proyecto):

```bash
# Regenerar todas las migraciones
./generate_migrations.sh

# O ejecutar scripts individuales desde migrations/
cd migrations/
python3 generate_migrations.py          # Solo individuales
python3 generate_consolidated_migration.py  # Solo consolidada
python3 validate_migrations.py          # Solo validar
```

## ⚡ Opciones de Deployment

### 🔧 Opción 1: Migraciones Individuales
**Ventajas:**
- Control granular
- Fácil debugging
- Rollback selectivo
- Ideal para desarrollo

**Uso:**
```bash
# Ejecutar todas
npm run typeorm migration:run

# Rollback una migración específica
npm run typeorm migration:revert
```

### 🚀 Opción 2: Migración Consolidada
**Ventajas:**
- Deployment rápido
- Una sola operación
- Menos archivos
- Ideal para producción

**Uso:**
```bash
# Solo ejecutar la migración consolidada
npm run typeorm migration:run
```

## 🛡️ Validación y Control de Calidad

Todas las migraciones han sido validadas:

✅ **217 archivos válidos**  
✅ **0 errores encontrados**  
✅ **Sintaxis TypeORM correcta**  
✅ **SQL bien formado**  
✅ **Métodos up/down implementados**  

## 📚 Recursos Adicionales

- **Documentación TypeORM**: https://typeorm.io/migrations
- **PostgreSQL UUID**: Usa `gen_random_uuid()` para generar UUIDs
- **Logs de generación**: Revisa la salida del script para detalles

## 🎯 Datos Procesados

Las migraciones incluyen **216 herramientas AI** reales extraídas de:
- **40h.json** - Herramienta de productividad
- **abby.json** - Asistente AI
- **addy-ai.json** - Herramienta de automatización
- **...y 213 herramientas más**

Cada herramienta incluye datos completos como descripción, categoría, pricing, características, y metadatos.

---

## 💡 Tips y Mejores Prácticas

1. **Backup**: Siempre haz backup de tu base de datos antes de ejecutar migraciones
2. **Testing**: Prueba las migraciones en un entorno de desarrollo primero
3. **Monitoring**: Monitorea la ejecución de migraciones en producción
4. **Rollback**: Ten un plan de rollback preparado

---

🎉 **¡Sistema de migraciones listo para usar!**
