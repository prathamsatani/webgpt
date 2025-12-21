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
    
    def clean_markdown(self, markdown_content: str) -> str:
        """
        Clean the markdown content by removing unwanted characters or formatting.

        :param self: Description
        :param markdown_content: Description
        :type markdown_content: str
        :return: Description
        :rtype: str
        """
        logger.info("Cleaning markdown content.")
        # Example cleaning process (can be expanded as needed)
        cleaned_content = markdown_content.replace("\r\n", "").replace("\n\n", "").replace("  ", " ").replace("\t", " ").replace("`", "")
        logger.debug(f"Cleaned markdown content length: {len(cleaned_content)}")
        return cleaned_content

    # -------------------------------------------------------
    # Convert a single page to Markdown
    # -------------------------------------------------------
    def convert_to_markdown(self, cleaned_html: str, clean_markdown: bool=False) -> Optional[str]:
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
            if clean_markdown:
                markdown_content = self.clean_markdown(markdown_content)
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
