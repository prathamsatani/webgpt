from bs4 import BeautifulSoup
import requests
from typing import List, Optional
import logging
import os
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

    def get_internal_links(self, base_url: str) -> Optional[List[str]]:
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
            logger.error("No sitemap found — cannot extract internal links.")
            return None

        all_links = []

        try:
            for sitemap in sitemap_urls:
                logger.info(f"Processing sitemap: {sitemap}")
                response = requests.get(sitemap)
                response.raise_for_status()

                for line in response.text.splitlines():
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
    
    def get_website_content(self, url: str) -> Optional[List[str]]:
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
            internal_links = self.get_internal_links(url)
            if not internal_links:
                logger.error("No internal links found. Aborting content fetch.")
                return None
            
            site_content = []
            for link in internal_links:
                logger.info(f"Fetching page: {link}")
                response = requests.get(link)
                response.raise_for_status()
                
                cleaned_html = self.clean_html(response.text)
                site_content.append(cleaned_html)
                logger.debug(f"Page fetched and cleaned: {link}")

            return site_content

        except requests.RequestException as e:
            logger.error(f"Error fetching webpage content: {e}")
            return None
