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

class WebCrawler:
    def __init__(self):
        logger.info("WebCrawler instance created.")
        self.internal_links = []
        self.recursion_depth = 0
        self.limit = None
        
    def clean_html(self, html: str, exclude_tags: List[str]) -> str:
        """
        Clean HTML content by removing unwanted tags.

        :param self: Description
        :param html: Description
        :type html: str
        :return: Description
        :rtype: str
        """
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

        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        hyperlinks = BeautifulSoup(response.text, "html.parser").find_all("a", href=True)

        for link in hyperlinks:
            href = link.get("href")
            if not href:
                continue
            # build absolute URL safely
            abs_url = urljoin(base_url, href)
            parsed = urlparse(abs_url)
            # only http(s) and same netloc
            if parsed.scheme in ("http", "https") and parsed.netloc == urlparse(base_url).netloc:
                if abs_url not in self.internal_links:
                    self.internal_links.append(abs_url)
                if len(self.internal_links) >= limit:
                    break

        print(self.internal_links)
        for link in list(self.internal_links):  # copy to avoid mutation issues
            # start recursion from depth 0 for each top-level link
            self.recursive_crawl_aux(base_url, link, depth=0)

    def recursive_crawl_aux(self, base_url, url, depth=0):
        """
        url must be absolute. depth is current recursion depth.
        """
        if depth >= self.limit:
            return

        # guard: only crawl same-host http(s) links
        parsed_base = urlparse(base_url)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or parsed.netloc != parsed_base.netloc:
            return

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return

        hyperlinks = BeautifulSoup(response.text, "html.parser").find_all("a", href=True)
        for link in hyperlinks:
            href = link.get("href")
            if not href:
                continue
            abs_link = urljoin(base_url, href)
            parsed_link = urlparse(abs_link)
            # ignore mailto:, tel:, javascript:, fragments, external hosts
            if parsed_link.scheme not in ("http", "https"):
                continue
            if parsed_link.netloc != parsed_base.netloc:
                continue
            # normalize (remove fragment)
            abs_link = abs_link.split('#', 1)[0]
            if abs_link not in self.internal_links:
                self.internal_links.append(abs_link)
                # recurse deeper
                self.recursive_crawl_aux(base_url, abs_link, depth + 1)


    def get_internal_links_using_sitemap(self, base_url: str, limit: int) -> Optional[List[str]]:
        """
        Extract internal links from the sitemap.

        :param self: Description
        :param base_url: Description
        :type base_url: str
        :return: Description
        :rtype: List[str] | None
        """
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
                    if limit:
                        if len(all_links) >= limit:
                            logger.info(f"Reached link limit of {limit}. Stopping extraction.")
                            break
                    line = line.strip()
                    if line.startswith("<loc>") and line.endswith("</loc>"):
                        link = line[5:-6]

                        if link.startswith(base_url):
                            all_links.append(link)
                            logger.debug(f"Internal link added: {link}")
                        else:
                            logger.debug(f"Skipping external link: {link}")

            logger.info(f"Total internal links found: {len(all_links)}")
            return all_links

        except requests.RequestException as e:
            logger.error(f"Error fetching internal links: {e}")
            return None
        except Exception as e:
            logger.exception(f"General error while processing sitemap: {e}")
            return None
    
    def get_internal_links(self, base_url: str, limit: int) -> Optional[List[str]]:
        """
        Get internal links using sitemap or recursive crawl.

        :param self: Description
        :param base_url: Description
        :type base_url: str
        :return: Description
        :rtype: List[str] | None
        """
        logger.info(f"Getting internal links for: {base_url}")

        links = self.get_internal_links_using_sitemap(base_url, limit)
        if links is not None:
            return links

        logger.info("Falling back to recursive crawl for internal links.")
        self.recursive_crawl(base_url, limit)
        return self.internal_links[:limit]
    
    def get_website_content(self, url: str, exclude_tags: List[str], limit: int) -> Optional[List[Dict[str, any]]]:
        """
        Fetch the HTML content of a webpage.

        :param self: Description
        :param url: Description
        :type url: str
        :return: Description
        :rtype: str | None
        """
        logger.info(f"Fetching content from URL: {url}")

        try:
            self.internal_links = self.get_internal_links(url, limit)
            if len(self.internal_links) == 0:
                logger.error("No internal links found. Aborting content fetch.")
                return None
            
            site_content = []
            for link in self.internal_links:
                logger.info(f"Fetching page: {link}")
                response = requests.get(link)
                response.raise_for_status()
                
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
    
if __name__ == "__main__":
    crawler = WebCrawler()
    test_url = "https://www.solutelabs.com"
    crawler.recursive_crawl(test_url, limit=5)
    print(f"Internal links found: {crawler.internal_links}")
    