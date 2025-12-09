import logging
from markdownify import markdownify as md
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
load_dotenv()

# --------------------------
# Logging Configuration
# --------------------------
logging.basicConfig(
    level=os.getenv("LOGGING_LEVEL", "DEBUG"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("Markdowner")


class Markdowner:
    def __init__(self):
        logger.info("Markdowner instance created.")

    # -------------------------------------------------------
    # Fetch sitemap URLs from robots.txt
    # -------------------------------------------------------
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

    # -------------------------------------------------------
    # Clean HTML by removing unnecessary tags
    # -------------------------------------------------------
    def clean_html(self, html: str) -> str:
        '''
        Clean HTML content by removing unwanted tags.
        
        :param self: Description
        :param html: Description
        :type html: str
        :return: Description
        :rtype: str
        '''
        logger.debug("Cleaning HTML content")

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["a", "img", "style", "script", "nav", "form", "header", "head"]):
            tag.decompose()

        logger.debug("HTML cleaned successfully")
        return str(soup)

    # -------------------------------------------------------
    # Extract internal links from sitemap
    # -------------------------------------------------------
    def get_internal_links(self, base_url: str) -> Optional[List[str]]:
        '''
        Extract internal links from the sitemap.
                
        :param self: Description
        :param base_url: Description
        :type base_url: str
        :return: Description
        :rtype: List[str] | None
        '''
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

    # -------------------------------------------------------
    # Convert a single page to Markdown
    # -------------------------------------------------------
    def convert_to_markdown(self, url: str) -> Optional[str]:
        '''
        Convert a single page to Markdown
        
        :param self: Description
        :param url: Description
        :type url: str
        :return: Description
        :rtype: str | None
        '''
        logger.info(f"Converting to markdown: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()

            cleaned_html = self.clean_html(response.text)
            markdown_content = md(cleaned_html, heading_style="ATX")

            logger.debug(f"Markdown conversion successful ({len(markdown_content)} chars)")
            return markdown_content

        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
        except Exception as e:
            logger.exception(f"Markdown conversion failed for {url}: {e}")

        return None

    # -------------------------------------------------------
    # Process whole site based on sitemap URLs
    # -------------------------------------------------------
    def markdownify_site(self, url: str) -> Optional[List[Dict[str, any]]]:
        '''
        Process the entire site and convert pages to Markdown.
        
        :param self: Description
        :param url: Description
        :type url: str
        :return: Description
        :rtype: List[Dict[str, Any]] | None
        '''
        logger.info(f"Starting full-site markdown conversion for: {url}")

        internal_links = self.get_internal_links(url)
        if not internal_links:
            logger.error("Failed to retrieve internal links. Aborting.")
            return None

        output = []
        for link in internal_links:
            logger.info(f"Processing page: {link}")
            markdown_content = self.convert_to_markdown(link)

            if markdown_content:
                output.append({
                    "url": link,
                    "markdown": markdown_content,
                    "metadata": {
                        "source": link,
                        "type": "markdown",
                        "content_length": len(markdown_content),
                    }
                })

        logger.info(f"Successfully processed {len(output)} pages.")
        return output


# -------------------------------------------------------
# Main Execution
# -------------------------------------------------------
if __name__ == "__main__":
    url = "https://www.solutelabs.com"
    markdowner = Markdowner()
    result = markdowner.markdownify_site(url)

    if result:
        print("Markdown conversion successful.")
    else:
        print("Markdown conversion failed.")
