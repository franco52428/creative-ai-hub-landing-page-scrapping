import os
import re
import json
import time
import random
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from retrying import retry

try:
    from fake_useragent import UserAgent
except Exception:
    UserAgent = None  # fallback más abajo

# ==== Config por defecto (si ya tienes config.settings, puedes importarla y sobreescribir) ====
class _DefaultConfig:
    BASE_URL = "https://www.futurepedia.io"
    TOOLS_DIR = "tools_data"
    DATA_DIR = "category_data"
    TIMEOUT = 30
    DELAY_BETWEEN_REQUESTS = 1.0
    MAX_PAGES_PER_CATEGORY = 200  # por seguridad, alto para no cortar antes
    CONN_RETRIES = 3
    ITEMS_PER_PAGE_HINT = 20  # solo como heurística

    # API keys por variables de entorno
    FETCHFOX_API_KEY = os.getenv("FETCHFOX_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

    # Endpoints
    FETCHFOX_API_URL = os.getenv("FETCHFOX_API_URL", "https://api.fetchfox.ai/v1/scrape")
    OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")

Config = _DefaultConfig()

# ==== Plantilla y traducciones básicas (si ya existen en config.settings, puedes quitarlas aquí) ====
TOOL_TEMPLATE: Dict = {
    "slug": "",
    "image_url": "",
    "redirect_url": "",
    "demo_url": "",
    "technical_requirements": "Navegador web moderno, conexión a internet estable",
    "searchIndexEn": "",
    "searchIndexEs": "",
    "translations": {
        "es": {"title": "", "shortDescription": "", "longDescription": "", "tags": "", "pricingInfo": "", "category": "", "appType": ""},
        "pt": {"title": "", "shortDescription": "", "longDescription": "", "tags": "", "pricingInfo": "", "category": "", "appType": ""},
        "en": {"title": "", "shortDescription": "", "longDescription": "", "tags": "", "pricingInfo": "", "category": "", "appType": ""},
        "fr": {"title": "", "shortDescription": "", "longDescription": "", "tags": "", "pricingInfo": "", "category": "", "appType": ""},
        "de": {"title": "", "shortDescription": "", "longDescription": "", "tags": "", "pricingInfo": "", "category": "", "appType": ""},
    },
}

CATEGORY_TRANSLATIONS = {
    "personal-assistant": {"es": "asistente-personal", "pt": "assistente-pessoal", "en": "personal-assistant", "fr": "assistant-personnel", "de": "personlicher-assistent"},
    "research-assistant": {"es": "asistente-investigacion", "pt": "assistente-pesquisa", "en": "research-assistant", "fr": "assistant-recherche", "de": "forschungsassistent"},
    "spreadsheet-assistant": {"es": "asistente-hojas-calculo", "pt": "assistente-planilhas", "en": "spreadsheet-assistant", "fr": "assistant-feuilles-calcul", "de": "tabellenkalkulation-assistent"},
    "translators": {"es": "traductores", "pt": "tradutores", "en": "translators", "fr": "traducteurs", "de": "ubersetzer"},
    "presentations": {"es": "presentaciones", "pt": "apresentacoes", "en": "presentations", "fr": "presentations", "de": "prasentationen"},
    "email-assistant": {"es": "asistente-email", "pt": "assistente-email", "en": "email-assistant", "fr": "assistant-email", "de": "email-assistent"},
    "search-engine": {"es": "motor-busqueda", "pt": "motor-busca", "en": "search-engine", "fr": "moteur-recherche", "de": "suchmaschine"},
    "prompt-generators": {"es": "generadores-prompts", "pt": "geradores-prompts", "en": "prompt-generators", "fr": "generateurs-prompts", "de": "prompt-generatoren"},
    "writing-generators": {"es": "generadores-escritura", "pt": "geradores-escrita", "en": "writing-generators", "fr": "generateurs-ecriture", "de": "schreib-generatoren"},
    "storyteller": {"es": "narrador", "pt": "contador-historias", "en": "storyteller", "fr": "conteur", "de": "geschichtenerzahler"},
    "summarizer": {"es": "resumidor", "pt": "sumarizador", "en": "summarizer", "fr": "resumeur", "de": "zusammenfasser"},
    "code-assistant": {"es": "asistente-codigo", "pt": "assistente-codigo", "en": "code-assistant", "fr": "assistant-code", "de": "code-assistent"},
    "no-code": {"es": "sin-codigo", "pt": "sem-codigo", "en": "no-code", "fr": "sans-code", "de": "kein-code"},
    "sql-assistant": {"es": "asistente-sql", "pt": "assistente-sql", "en": "sql-assistant", "fr": "assistant-sql", "de": "sql-assistent"},
}

logger = logging.getLogger(__name__)

# ==== Utilidades ====
def _rand_ua() -> str:
    if UserAgent:
        try:
            return UserAgent().random
        except Exception:
            pass
    # fallback UA conocido y válido
    return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"


def _sleep_with_jitter(base: float):
    time.sleep(base + random.uniform(0, base * 0.6))


@dataclass
class ToolInfo:
    name: str
    url: str
    slug: str
    image_url: str = ""
    short_description: str = ""
    category: str = ""


class OpenRouterTranslator:
    """
    Traducción en lote (un solo request por idioma) devolviendo JSON estrictamente estructurado.
    """
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Opcionales recomendados por OpenRouter:
            "HTTP-Referer": "https://your-domain.example",  # cambia si quieres
            "X-Title": "Futurepedia Scraper",
        }

    def translate_dict(self, payload_en: Dict[str, str], target_lang: str) -> Dict[str, str]:
        """
        Recibe un diccionario en inglés y pide al LLM devolver **solo JSON válido** con mismas keys.
        """
        if not self.api_key:
            # sin API key: devolver marcado para no romper pipeline
            return {k: f"[TRANSLATE-{target_lang}] {v}" for k, v in payload_en.items()}

        system = (
            "You are a professional technical translator. "
            "Return ONLY strict JSON, utf-8, with the SAME KEYS as input. "
            "No commentary, no markdown, no trailing commas. Keep meaning precise."
        )
        user = {
            "instruction": f"Translate each value from English to {target_lang}. Keep style concise, natural and domain-correct. Return JSON only.",
            "input": payload_en,
        }

        body = {
            "model": Config.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        }

        try:
            resp = requests.post(Config.OPENROUTER_API_URL, headers=self._headers(), json=body, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            # Limpia bloqueos (a veces devuelven ```json ... ```)
            text = text.strip().strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Fallo traduciendo a {target_lang}: {e}")
            return {k: f"[TRANSLATE-{target_lang}] {v}" for k, v in payload_en.items()}


class FuturepediaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": _rand_ua(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.7,es-ES;q=0.5",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        os.makedirs(Config.TOOLS_DIR, exist_ok=True)
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        self.translator = OpenRouterTranslator(
            api_key=Config.OPENROUTER_API_KEY, api_url=Config.OPENROUTER_API_URL, model=Config.OPENROUTER_MODEL
        )

        # memoria de slugs ya procesados (resume)
        self._seen = set(os.path.splitext(fn)[0] for fn in os.listdir(Config.TOOLS_DIR) if fn.endswith(".json"))

    # ---- HTTP helpers -------------------------------------------------------
    @retry(stop_max_attempt_number=Config.CONN_RETRIES, wait_exponential_multiplier=1000, wait_exponential_max=6000)
    def _get(self, url: str) -> Optional[requests.Response]:
        logger.info(f"GET {url}")
        r = self.session.get(url, timeout=Config.TIMEOUT)
        r.raise_for_status()
        _sleep_with_jitter(Config.DELAY_BETWEEN_REQUESTS)
        return r

    @retry(stop_max_attempt_number=Config.CONN_RETRIES, wait_fixed=2500)
    def _fetchfox(self, url: str, selectors: Dict) -> Optional[Dict]:
        """
        API FetchFox: estructura mínima "url" + "selectors".
        Si no hay API key, retorna None para forzar fallback.
        """
        if not Config.FETCHFOX_API_KEY:
            return None
        payload = {"url": url, "selectors": selectors}
        headers = {"Authorization": f"Bearer {Config.FETCHFOX_API_KEY}", "Content-Type": "application/json"}
        logger.info(f"FetchFox {url}")
        try:
            resp = requests.post(Config.FETCHFOX_API_URL, json=payload, headers=headers, timeout=Config.TIMEOUT)
            resp.raise_for_status()
            _sleep_with_jitter(Config.DELAY_BETWEEN_REQUESTS)
            return resp.json()
        except Exception as e:
            logger.warning(f"FetchFox error ({url}): {e}")
            return None

    # ---- Category listing ---------------------------------------------------
    def _extract_category_name(self, category_url: str) -> str:
        return category_url.rstrip("/").split("/")[-1]

    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """
        Detecta paginación buscando rel=next o enlaces con texto 'Next'.
        """
        if soup.find("link", rel="next"):
            return True
        a_next = soup.find("a", string=re.compile(r"next", re.I)) or soup.find("a", attrs={"aria-label": re.compile("next", re.I)})
        return bool(a_next)

    def _parse_cards_bs4(self, html_doc: str, category_url: str) -> List[ToolInfo]:
        soup = BeautifulSoup(html_doc, "html.parser")
        tools = []
        # Los listados suelen tener anchors a /tool/...
        for a in soup.select("a[href*='/tool/']"):
            try:
                href = a.get("href") or ""
                tool_url = urljoin(Config.BASE_URL, href)
                slug = tool_url.rstrip("/").split("/")[-1]
                name_el = a.find(["h2", "h3", "h4"])
                name = name_el.get_text(strip=True) if name_el else a.get_text(strip=True)[:80]
                img_el = a.find("img")
                image_url = ""
                if img_el and img_el.get("src"):
                    image_url = img_el.get("src")
                    if not image_url.startswith("http"):
                        image_url = urljoin(Config.BASE_URL, image_url)
                desc_el = a.find("p")
                desc = desc_el.get_text(strip=True) if desc_el else ""
                tools.append(ToolInfo(name=name, url=tool_url, slug=slug, image_url=image_url, short_description=desc, category=self._extract_category_name(category_url)))
            except Exception as e:
                logger.debug(f"Card parse error: {e}")
        logger.info(f"Cards detectadas: {len(tools)}")
        return tools

    def _list_page_tools(self, category_url: str, page: int) -> Tuple[List[ToolInfo], bool]:
        """
        Devuelve (tools_en_pagina, hay_mas_paginas)
        Intenta FetchFox -> fallback bs4.
        """
        url = f"{category_url}?page={page}" if page > 1 else category_url

        # FetchFox
        selectors = {
            "cards": {
                "selector": "a[href*='/tool/']",
                "type": "multiple",
                "output": {
                    "href": {"selector": "", "type": "attribute", "attribute": "href"},
                    "name": {"selector": "h2, h3, h4", "type": "text"},
                    "img": {"selector": "img", "type": "attribute", "attribute": "src"},
                    "desc": {"selector": "p", "type": "text"},
                },
            }
        }
        data = self._fetchfox(url, selectors)
        tools: List[ToolInfo] = []
        has_next = False

        if data and "cards" in data:
            for card in data["cards"]:
                href = (card.get("href") or "").strip()
                if not href:
                    continue
                tool_url = urljoin(Config.BASE_URL, href)
                slug = tool_url.rstrip("/").split("/")[-1]
                name = (card.get("name") or "").strip() or slug
                img = (card.get("img") or "").strip()
                if img and not img.startswith("http"):
                    img = urljoin(Config.BASE_URL, img)
                desc = (card.get("desc") or "").strip()
                tools.append(ToolInfo(name=name, url=tool_url, slug=slug, image_url=img, short_description=desc, category=self._extract_category_name(category_url)))

            # Para saber si hay next en FetchFox, pedimos también el link rel=next:
            # Hacemos un GET rápido y revisamos rel=next.
            try:
                r = self._get(url)
                has_next = self._has_next_page(BeautifulSoup(r.text, "html.parser"))
            except Exception:
                has_next = False
        else:
            # Fallback bs4
            r = self._get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            tools = self._parse_cards_bs4(r.text, category_url)
            has_next = self._has_next_page(soup)

        # Filtra duplicados
        uniq = {}
        for t in tools:
            uniq[t.slug] = t
        tools = list(uniq.values())

        logger.info(f"Página {page} -> tools: {len(tools)} | next: {has_next}")
        return tools, has_next

    def get_all_tools_from_category(self, category_url: str) -> List[ToolInfo]:
        all_tools: List[ToolInfo] = []
        page = 1
        while page <= Config.MAX_PAGES_PER_CATEGORY:
            tools, has_next = self._list_page_tools(category_url, page)
            if not tools and page > 1:
                break
            all_tools.extend(tools)
            if not has_next:
                break
            page += 1
        logger.info(f"Total tools en {category_url}: {len(all_tools)}")
        return all_tools

    # ---- Tool detail --------------------------------------------------------
    def _decode_redirect(self, href: str) -> str:
        """
        Algunas páginas usan /redirect?to=<URL codificada>.
        """
        try:
            if "redirect" in href:
                q = parse_qs(urlparse(href).query)
                to = q.get("to", [])
                if to:
                    return to[0]
            return href
        except Exception:
            return href

    def _tool_selectors(self) -> Dict:
        return {
            "title": {"selector": "h1", "type": "text"},
            "meta_desc": {"selector": "meta[name='description']", "type": "attribute", "attribute": "content"},
            "og_desc": {"selector": "meta[property='og:description']", "type": "attribute", "attribute": "content"},
            "og_img": {"selector": "meta[property='og:image']", "type": "attribute", "attribute": "content"},
            "visit": {"selector": "a[href*='redirect'], a[class*='visit'], a[class*='website']", "type": "attribute", "attribute": "href"},
            "pricing": {"selector": ".pricing, .price, [class*='pricing'], [class*='price']", "type": "text"},
            "tags": {"selector": ".tag, .category, [class*='tag'], [class*='category']", "type": "text", "multiple": True},
        }

    def _scrape_detail_fetchfox(self, tool_url: str) -> Optional[Dict]:
        data = self._fetchfox(tool_url, self._tool_selectors())
        if not data:
            return None
        return {
            "title": (data.get("title") or "").strip(),
            "desc": (data.get("meta_desc") or data.get("og_desc") or "").strip(),
            "image": (data.get("og_img") or "").strip(),
            "redirect": self._decode_redirect((data.get("visit") or "").strip()),
            "pricing": (data.get("pricing") or "Information not available").strip(),
            "tags": [t.strip().lower() for t in (data.get("tags") or []) if t and isinstance(t, str)],
        }

    def _scrape_detail_bs4(self, tool_url: str) -> Dict:
        r = self._get(tool_url)
        soup = BeautifulSoup(r.text, "html.parser")
        title_el = soup.find("h1") or soup.find("title")
        title = title_el.get_text(strip=True) if title_el else tool_url.rstrip("/").split("/")[-1]
        desc = ""
        for sel in ["meta[name='description']", "meta[property='og:description']", ".description", ".summary", "p"]:
            el = soup.select_one(sel)
            if el:
                desc = el.get("content") if el.name == "meta" else el.get_text(strip=True)
                if desc:
                    break
        redir = ""
        for sel in ["a[href*='redirect']", "a[class*='visit']", "a[class*='website']", "a[href^='http']:not([href*='futurepedia'])"]:
            el = soup.select_one(sel)
            if el and el.get("href"):
                redir = el.get("href")
                break
        redir = self._decode_redirect(redir)
        pricing = "Information not available"
        for sel in [".pricing", ".price", "[class*='pricing']", "[class*='price']"]:
            el = soup.select_one(sel)
            if el:
                pricing = el.get_text(strip=True)
                break
        tags = []
        for sel in [".tag", ".category", "[class*='tag']", "[class*='category']"]:
            for el in soup.select(sel):
                t = el.get_text(strip=True).lower()
                if t and t not in tags:
                    tags.append(t)
        og_img = ""
        og = soup.select_one("meta[property='og:image']")
        if og and og.get("content"):
            og_img = og.get("content")
        return {"title": title, "desc": desc, "image": og_img, "redirect": redir, "pricing": pricing, "tags": tags}

    def scrape_tool_details(self, tool_info: ToolInfo) -> Dict:
        """
        Mezcla FetchFox y fallback BS4; normaliza y traduce.
        """
        # Si ya lo tenemos, retornamos (resume)
        existing_path = os.path.join(Config.TOOLS_DIR, f"{tool_info.slug}.json")
        if os.path.exists(existing_path):
            with open(existing_path, "r", encoding="utf-8") as f:
                return json.load(f)

        detail = self._scrape_detail_fetchfox(tool_info.url) or self._scrape_detail_bs4(tool_info.url)

        title = detail["title"] or tool_info.name
        desc = detail["desc"] or tool_info.short_description
        tags = detail["tags"] or []
        redirect = detail["redirect"] or ""
        image_url = detail["image"] or tool_info.image_url

        data = json.loads(json.dumps(TOOL_TEMPLATE))  # copia profunda segura
        data["slug"] = tool_info.slug
        data["image_url"] = image_url
        data["redirect_url"] = redirect
        data["demo_url"] = ""  # si detectas demos, completa aquí
        data["searchIndexEn"] = f"{title.lower()} {desc.lower()} {' '.join(tags)}"
        data["searchIndexEs"] = self._translate_search_terms(data["searchIndexEn"])

        # base EN
        data["translations"]["en"].update(
            {
                "title": title,
                "shortDescription": (tool_info.short_description or (desc[:180] + "…")).strip(),
                "longDescription": desc.strip(),
                "tags": ", ".join(tags[:12]),
                "pricingInfo": detail["pricing"],
                "category": tool_info.category,
                "appType": self._determine_app_type(title, desc, tags),
            }
        )

        # Traducción en lote -> es, pt, fr, de
        en = data["translations"]["en"]
        pack = {
            "title": en["title"],
            "shortDescription": en["shortDescription"],
            "longDescription": en["longDescription"],
            "tags": en["tags"],
            "pricingInfo": en["pricingInfo"],
            "category": en["category"],
            "appType": en["appType"],
        }

        for lang in ["es", "pt", "fr", "de"]:
            # Category: usa diccionario si existe
            cat = en["category"]
            cat_map = CATEGORY_TRANSLATIONS.get(cat, {})
            cat_trans = cat_map.get(lang)
            # Traduce todo en lote
            translated = self.translator.translate_dict(pack, lang)
            if cat_trans:
                translated["category"] = cat_trans
            data["translations"][lang].update(translated)

        return data

    # ---- Persistencia -------------------------------------------------------
    def _save_tool_json(self, tool_data: Dict) -> bool:
        try:
            path = os.path.join(Config.TOOLS_DIR, f"{tool_data['slug']}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tool_data, f, indent=2, ensure_ascii=False)
            self._seen.add(tool_data["slug"])
            logger.info(f"Saved: {path}")
            return True
        except Exception as e:
            logger.exception(f"Error guardando JSON: {e}")
            return False

    def _save_category_csv(self, rows: List[Dict], category_name: str) -> bool:
        import csv
        try:
            path = os.path.join(Config.DATA_DIR, f"{category_name}_tools.csv")
            fieldnames = [
                "slug",
                "title_en",
                "title_es",
                "short_description_en",
                "short_description_es",
                "category",
                "app_type",
                "pricing_en",
                "pricing_es",
                "image_url",
                "redirect_url",
                "tags_en",
                "tags_es",
                "search_index_en",
                "search_index_es",
            ]
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for t in rows:
                    writer.writerow(
                        {
                            "slug": t["slug"],
                            "title_en": t["translations"]["en"]["title"],
                            "title_es": t["translations"]["es"]["title"],
                            "short_description_en": t["translations"]["en"]["shortDescription"],
                            "short_description_es": t["translations"]["es"]["shortDescription"],
                            "category": t["translations"]["en"]["category"],
                            "app_type": t["translations"]["en"]["appType"],
                            "pricing_en": t["translations"]["en"]["pricingInfo"],
                            "pricing_es": t["translations"]["es"]["pricingInfo"],
                            "image_url": t["image_url"],
                            "redirect_url": t["redirect_url"],
                            "tags_en": t["translations"]["en"]["tags"],
                            "tags_es": t["translations"]["es"]["tags"],
                            "search_index_en": t["searchIndexEn"],
                            "search_index_es": t["searchIndexEs"],
                        }
                    )
            logger.info(f"CSV guardado: {path}")
            return True
        except Exception as e:
            logger.exception(f"Error guardando CSV: {e}")
            return False

    # ---- Categoría end-to-end ----------------------------------------------
    def scrape_category(self, category_url: str, max_workers: int = 4) -> bool:
        """
        - Lista todas las herramientas (paginación robusta).
        - Scrapea cada ficha en paralelo controlado.
        - Guarda JSON por herramienta y CSV de la categoría.
        - Evita duplicados si ya existen (resume).
        """
        logger.info(f"== Categoría {category_url}")
        tools_info = self.get_all_tools_from_category(category_url)
        if not tools_info:
            return False

        # Filtra las ya procesadas
        to_process = [ti for ti in tools_info if ti.slug not in self._seen]
        logger.info(f"{len(tools_info)} tools encontradas | a procesar: {len(to_process)} | ya vistas: {len(tools_info) - len(to_process)}")

        results: List[Dict] = []
        if not to_process:
            # cargar de disco para el CSV
            for ti in tools_info:
                path = os.path.join(Config.TOOLS_DIR, f"{ti.slug}.json")
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        results.append(json.load(f))
            category_name = self._extract_category_name(category_url)
            self._save_category_csv(results, category_name)
            return True

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(self.scrape_tool_details, ti): ti.slug for ti in to_process}
            for fut in as_completed(futs):
                slug = futs[fut]
                try:
                    data = fut.result()
                    if data and data.get("slug"):
                        if self._save_tool_json(data):
                            results.append(data)
                except Exception as e:
                    logger.error(f"Fallo en tool {slug}: {e}")

        # Agrega también las ya existentes para CSV completo
        for ti in tools_info:
            path = os.path.join(Config.TOOLS_DIR, f"{ti.slug}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    results.append(json.load(f))

        # CSV
        category_name = self._extract_category_name(category_url)
        self._save_category_csv(results, category_name)
        return True

    # ---- Heurísticas --------------------------------------------------------
    def _translate_search_terms(self, english_terms: str) -> str:
        mapping = {
            "assistant": "asistente",
            "personal": "personal",
            "ai": "ia",
            "artificial intelligence": "inteligencia artificial",
            "tool": "herramienta",
            "generator": "generador",
            "code": "codigo",
            "research": "investigacion",
            "writing": "escritura",
            "image": "imagen",
            "video": "video",
            "audio": "audio",
            "chat": "chat",
            "chatbot": "chatbot",
        }
        res = english_terms.lower()
        for en, es in mapping.items():
            res = res.replace(en, es)
        return res

    def _determine_app_type(self, title: str, description: str, tags: List[str]) -> str:
        text = f"{title} {description} {' '.join(tags)}".lower()
        if any(w in text for w in ["assistant", "chatbot", "chat"]):
            return "assistant"
        if any(w in text for w in ["generator", "create", "generate"]):
            return "generator"
        if any(w in text for w in ["research", "search", "find"]):
            return "research"
        if any(w in text for w in ["write", "writing", "text"]):
            return "writing"
        if any(w in text for w in ["image", "photo", "picture"]):
            return "image"
        if any(w in text for w in ["video", "movie"]):
            return "video"
        if any(w in text for w in ["audio", "music", "sound"]):
            return "audio"
        if any(w in text for w in ["code", "programming", "development"]):
            return "code"
        return "other"
