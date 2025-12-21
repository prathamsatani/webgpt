from bs4 import BeautifulSoup
import requests
from typing import Dict, List, Optional
import logging
import os
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

load_dotenv()

# --------------------------
# Logging Configuration
# --------------------------
logging.basicConfig(
    level=os.getenv("LOGGING_LEVEL", "DEBUG"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("WebCrawler")

# Non-HTML extensions to skip
NON_HTML_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp', '.tiff',
    '.mp3', '.mp4', '.wav', '.avi', '.mov', '.webm', '.ogg', '.flac',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods',
    '.css', '.js', '.json', '.xml', '.rss', '.atom',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.exe', '.dmg', '.apk', '.msi',
}

class WebCrawler:
    def __init__(self):
        logger.info("WebCrawler instance created.")
        self.internal_links = []
        self.recursion_depth = 0
        self.limit = None

    def is_html_url(self, url: str) -> bool:
        """Check if URL likely points to HTML content based on extension."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # URLs ending with / or no extension are likely HTML
        if path.endswith('/') or '.' not in path.split('/')[-1]:
            return True
        
        # Check against known non-HTML extensions
        for ext in NON_HTML_EXTENSIONS:
            if path.endswith(ext):
                logger.debug(f"Skipping non-HTML URL: {url}")
                return False
        return True

    def is_html_response(self, response: requests.Response) -> bool:
        """Check if response Content-Type indicates HTML."""
        content_type = response.headers.get('Content-Type', '').lower()
        return 'text/html' in content_type

    def fetch_html(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Fetch URL only if it returns HTML content."""
        if not self.is_html_url(url):
            return None
        
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                return None
            
            if not self.is_html_response(response):
                logger.debug(f"Skipping non-HTML content at: {url}")
                return None
            
            return response
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
        
    def clean_html(self, html: str, exclude_tags: List[str]) -> str:
        """Clean HTML content by removing unwanted tags."""
        logger.debug("Cleaning HTML content")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(exclude_tags):
            tag.decompose()
        logger.debug("HTML cleaned successfully")
        return str(soup)

    def get_sitemap(self, url: str) -> Optional[List[str]]:
        robots_url = f"{url.rstrip('/')}/robots.txt"
        logger.debug(f"Fetching robots.txt from: {robots_url}")

        try:
            response = requests.get(robots_url)
            response.raise_for_status()
            sitemaps = []

            for line in response.text.splitlines():
                line = line.strip()
                if line.lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    sitemaps.append(sitemap_url)
                    logger.debug(f"Found sitemap: {sitemap_url}")

            if not sitemaps:
                logger.warning("No sitemap entries found in robots.txt")

            return sitemaps

        except requests.RequestException as e:
            logger.error(f"Error fetching sitemap: {e}")
            return None
    
    def recursive_crawl(self, base_url: str, limit: int) -> Optional[List[str]]:
        self.limit = limit
        self.internal_links = []
        self.recursion_depth = 0

        response = self.fetch_html(base_url)
        if response is None:
            logger.error(f"Failed to fetch {base_url}")
            return None
        
        hyperlinks = BeautifulSoup(response.text, "html.parser").find_all("a", href=True)

        for link in hyperlinks:
            href = link.get("href")
            if not href:
                continue
            abs_url = urljoin(base_url, href)
            parsed = urlparse(abs_url)
            
            if parsed.scheme in ("http", "https") and parsed.netloc == urlparse(base_url).netloc:
                # Only add if it's likely an HTML URL
                if self.is_html_url(abs_url) and abs_url not in self.internal_links:
                    self.internal_links.append(abs_url)
                if limit is not None and len(self.internal_links) >= limit:
                    break

        print(self.internal_links)
        for link in list(self.internal_links):
            self.recursive_crawl_aux(base_url, link, depth=limit)

    def recursive_crawl_aux(self, base_url, url, depth=0):
        """Recursively crawl URL. url must be absolute."""
        if depth is not None and depth >= self.limit:
            return

        parsed_base = urlparse(base_url)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or parsed.netloc != parsed_base.netloc:
            return

        # Skip non-HTML URLs
        if not self.is_html_url(url):
            return

        response = self.fetch_html(url)
        if response is None:
            return

        hyperlinks = BeautifulSoup(response.text, "html.parser").find_all("a", href=True)
        for link in hyperlinks:
            href = link.get("href")
            if not href:
                continue
            abs_link = urljoin(base_url, href)
            parsed_link = urlparse(abs_link)
            
            if parsed_link.scheme not in ("http", "https"):
                continue
            if parsed_link.netloc != parsed_base.netloc:
                continue
            
            abs_link = abs_link.split('#', 1)[0]
            
            # Only add HTML URLs
            if self.is_html_url(abs_link) and abs_link not in self.internal_links:
                self.internal_links.append(abs_link)
                if depth is not None:
                    depth += 1
                self.recursive_crawl_aux(base_url, abs_link, depth + 1 if depth is not None else None)

    def get_internal_links_using_sitemap(self, base_url: str, limit: int) -> Optional[List[str]]:
        """Extract internal HTML links from the sitemap."""
        logger.info(f"Extracting internal links for: {base_url}")

        sitemap_urls = self.get_sitemap(base_url)
        if not sitemap_urls:
            logger.info("No sitemap found — cannot extract internal links.")
            return None

        all_links = []
        
        try:
            for sitemap in sitemap_urls:
                logger.info(f"Processing sitemap: {sitemap}")
                response = requests.get(sitemap)
                response.raise_for_status()

                for line in response.text.splitlines():
                    if limit is not None and len(all_links) >= limit:
                        logger.info(f"Reached link limit of {limit}. Stopping extraction.")
                        break
                    line = line.strip()
                    if line.startswith("<loc>") and line.endswith("</loc>"):
                        link = line[5:-6]

                        # Only add HTML links
                        if link.startswith(base_url) and self.is_html_url(link):
                            all_links.append(link)
                            logger.debug(f"Internal link added: {link}")
                        else:
                            logger.debug(f"Skipping link: {link}")

            logger.info(f"Total internal links found: {len(all_links)}")
            return all_links

        except requests.RequestException as e:
            logger.error(f"Error fetching internal links: {e}")
            return None
        except Exception as e:
            logger.exception(f"General error while processing sitemap: {e}")
            return None
    
    def get_internal_links(self, base_url: str, limit: int) -> Optional[List[str]]:
        """Get internal HTML links using sitemap or recursive crawl."""
        logger.info(f"Getting internal links for: {base_url}")

        links = self.get_internal_links_using_sitemap(base_url, limit)
        if links is not None:
            return links

        logger.info("Falling back to recursive crawl for internal links.")
        self.recursive_crawl(base_url, limit)
        return self.internal_links[:limit]
    
    def get_website_content(self, url: str, exclude_tags: List[str], limit: int, exclude_pages: List[str]) -> Optional[List[Dict[str, any]]]:
        """Fetch HTML content from a website."""
        logger.info(f"Fetching content from URL: {url}")

        try:
            self.internal_links = self.get_internal_links(url, limit)
            if not self.internal_links:
                logger.error("No internal links found. Aborting content fetch.")
                return None
            
            site_content = []
            for link in self.internal_links:
                if any(exclude_page in link for exclude_page in exclude_pages):
                    logger.info(f"Skipping excluded page: {link}")
                    continue

                logger.info(f"Fetching page: {link}")
                
                response = self.fetch_html(link)
                if response is None:
                    continue
                
                cleaned_html = self.clean_html(response.text, exclude_tags)
                site_content.append({
                    "html": cleaned_html,
                    "url": link
                })
                logger.debug(f"Page fetched and cleaned: {link}")

            return site_content

        except requests.RequestException as e:
            logger.error(f"Error fetching webpage content: {e}")
            return None