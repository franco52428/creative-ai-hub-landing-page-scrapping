import sys
import csv
import argparse
import logging
from pathlib import Path
from scrapers.futurepedia_scraper import FuturepediaScraper


project_root = Path(__file__).parent
sys.path.append(str(project_root))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("scraping.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_categories(csv_filename: str = "futurepeida_io_categories.csv"):
    """
    Lee el CSV con las categorías (columna: Category).
    """
    categories = []
    csv_path = project_root / csv_filename
    if not csv_path.exists():
        logger.error(f"No existe el archivo de categorías: {csv_path}")
        return categories

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = (row.get("Category") or "").strip()
                if url:
                    categories.append(url)
    except Exception as e:
        logger.exception(f"Error cargando categorías: {e}")
    return categories


def scrape_single_category(category_input: str, max_workers: int = 4):
    """
    Scrapea una sola categoría, con concurrencia configurable.
    Acepta tanto URL completas como nombres de categoría.
    """
    # Si parece una URL completa, usarla directamente
    if category_input.startswith("http"):
        category_url = category_input
    else:
        # Convertir nombre a URL
        category_url = convert_category_name_to_url(category_input)
    
    logger.info(f"==> Iniciando categoría: {category_input}")
    logger.info(f"== Categoría {category_url}")
    scraper = FuturepediaScraper()
    ok = scraper.scrape_category(category_url, max_workers=max_workers)
    if ok:
        logger.info(f"==> OK categoría: {category_input}")
    else:
        logger.error(f"==> FALLÓ categoría: {category_input}")
    return ok


def convert_category_name_to_url(category_name: str) -> str:
    """
    Convierte un nombre de categoría en inglés a su URL correspondiente en Futurepedia.
    """
    # Mapeo de nombres comunes a URLs
    category_mapping = {
        "AI Personal Assistant Tools": "https://www.futurepedia.io/ai-tools/personal-assistant",
        "personal-assistant": "https://www.futurepedia.io/ai-tools/personal-assistant",
        "Research Assistant": "https://www.futurepedia.io/ai-tools/research-assistant",
        "research-assistant": "https://www.futurepedia.io/ai-tools/research-assistant",
        "Spreadsheet Assistant": "https://www.futurepedia.io/ai-tools/spreadsheet-assistant",
        "spreadsheet-assistant": "https://www.futurepedia.io/ai-tools/spreadsheet-assistant",
        "Translators": "https://www.futurepedia.io/ai-tools/translators",
        "translators": "https://www.futurepedia.io/ai-tools/translators",
        "Presentations": "https://www.futurepedia.io/ai-tools/presentations",
        "presentations": "https://www.futurepedia.io/ai-tools/presentations",
        "Email Assistant": "https://www.futurepedia.io/ai-tools/email-assistant",
        "email-assistant": "https://www.futurepedia.io/ai-tools/email-assistant",
        "Search Engine": "https://www.futurepedia.io/ai-tools/search-engine",
        "search-engine": "https://www.futurepedia.io/ai-tools/search-engine",
        "Prompt Generators": "https://www.futurepedia.io/ai-tools/prompt-generators",
        "prompt-generators": "https://www.futurepedia.io/ai-tools/prompt-generators",
        "Writing Generators": "https://www.futurepedia.io/ai-tools/writing-generators",
        "writing-generators": "https://www.futurepedia.io/ai-tools/writing-generators",
        "Storyteller": "https://www.futurepedia.io/ai-tools/storyteller",
        "storyteller": "https://www.futurepedia.io/ai-tools/storyteller",
        "Summarizer": "https://www.futurepedia.io/ai-tools/summarizer",
        "summarizer": "https://www.futurepedia.io/ai-tools/summarizer",
        "Code Assistant": "https://www.futurepedia.io/ai-tools/code-assistant",
        "code-assistant": "https://www.futurepedia.io/ai-tools/code-assistant",
        "No Code": "https://www.futurepedia.io/ai-tools/no-code",
        "no-code": "https://www.futurepedia.io/ai-tools/no-code",
        "SQL Assistant": "https://www.futurepedia.io/ai-tools/sql-assistant",
        "sql-assistant": "https://www.futurepedia.io/ai-tools/sql-assistant",
    }
    
    # Buscar en el mapeo
    if category_name in category_mapping:
        return category_mapping[category_name]
    
    # Si no está en el mapeo, intentar convertir automáticamente
    # Convertir a minúsculas, reemplazar espacios por guiones, quitar caracteres especiales
    slug = category_name.lower().replace(" ", "-").replace("&", "").replace(",", "")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    url = f"https://www.futurepedia.io/ai-tools/{slug}"
    
    logger.warning(f"Categoría no mapeada: '{category_name}' -> generando URL: {url}")
    return url


def scrape_all_categories(csv_filename: str, max_workers: int = 4):
    categories = load_categories(csv_filename)
    if not categories:
        logger.error("No se encontraron categorías para procesar.")
        return

    logger.info(f"Se encontraron {len(categories)} categorías.")
    results = []

    # Ejecuta categoría por categoría (secuencial), pero cada categoría procesa herramientas en paralelo
    for idx, url in enumerate(categories, 1):
        logger.info(f"[{idx}/{len(categories)}] Procesando: {url}")
        ok = scrape_single_category(url, max_workers=max_workers)
        results.append((url, ok))

    ok_count = sum(1 for _, ok in results if ok)
    fail_count = len(results) - ok_count
    logger.info("======== RESUMEN FINAL ========")
    logger.info(f"Total categorías: {len(results)} | Éxitos: {ok_count} | Fallos: {fail_count}")

    if fail_count > 0:
        logger.info("Categorías con fallo:")
        for url, ok in results:
            if not ok:
                logger.info(f"  - {url}")


def main():
    parser = argparse.ArgumentParser(description="AI Tools Web Scraper (Futurepedia)")
    parser.add_argument(
        "--category", 
        type=str, 
        help="URL de categoría a scrapear"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Scrapear todas las categorías del CSV"
    )
    parser.add_argument(
        "--csv", 
        type=str, 
        default="futurepeida_io_categories.csv", 
        help="Archivo CSV de categorías"
    )
    parser.add_argument(
        "--max-workers", 
        type=int, 
        default=4, 
        help="Hilos en scraping de herramientas"
    )
    
    args = parser.parse_args()
    
    if args.category:
        scrape_single_category(args.category, max_workers=args.max_workers)
    elif args.all:
        scrape_all_categories(args.csv, max_workers=args.max_workers)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
