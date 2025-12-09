import logging
from markdownify import markdownify as md
from typing import List, Dict, Optional
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
logger = logging.getLogger("Markdowner")


class Markdowner:
    def __init__(self):
        logger.info("Markdowner instance created.")

    # -------------------------------------------------------
    # Convert a single page to Markdown
    # -------------------------------------------------------
    def convert_to_markdown(self, cleaned_html: str) -> Optional[str]:
        """
        Convert a single page to Markdown

        :param self: Description
        :param url: Description
        :type url: str
        :return: Description
        :rtype: str | None
        """
        logger.info(f"Converting to markdown")

        try:
            markdown_content = md(cleaned_html, heading_style="ATX")

            logger.debug(
                f"Markdown conversion successful ({len(markdown_content)} chars)"
            )
            return markdown_content

        except Exception as e:
            logger.exception(f"Markdown conversion failed: {e}")

        return None

    # -------------------------------------------------------
    # Process whole site based on sitemap URLs
    # -------------------------------------------------------
    def markdownify_site(self, site_data: List[str]) -> Optional[List[Dict[str, any]]]:
        """
        Process the entire site and convert pages to Markdown.

        :param self: Description
        :param url: Description
        :type url: str
        :return: Description
        :rtype: List[Dict[str, Any]] | None
        """
        logger.info(f"Starting full-site markdown conversion")

        if not site_data:
            logger.error("No site data provided. Aborting.")
            return None

        output = []
        for page in site_data:
            logger.info(f"Processing page: {page}")
            markdown_content = self.convert_to_markdown(page)

            if markdown_content:
                output.append(markdown_content)

        logger.info(f"Successfully processed {len(output)} pages.")
        return output
