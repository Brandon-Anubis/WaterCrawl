import re
import html2text
import trafilatura
from lxml import html


class HtmlFilter:
    def __init__(self, html_content, scrape_options):
        self.html_content = html_content
        self.scrape_options = scrape_options
        # Parse with lxml only when needed for simple mode
        self.tree = None

    def filter_html(self):
        extraction_mode = self.scrape_options.get("extraction_mode", "simple")

        if self.scrape_options.get("only_main_content") and extraction_mode == 'advanced':
            # Advanced mode using trafilatura
            extracted_content = trafilatura.extract(self.html_content, output_format='html', include_comments=False, include_tables=True)
            if extracted_content is not None:
                return extracted_content
            # Fallback to simple mode processing if extraction fails
            extraction_mode = 'simple'

        # The rest of the logic is for simple filtering or when only_main_content is false
        try:
            self.tree = html.fromstring(self.html_content)
        except Exception:
            # Return original content if HTML parsing fails
            return self.html_content

        # Step 1: Handle includeTags if provided
        if self.scrape_options.get("include_tags"):
            return self._handle_include_tags()

        # Step 2: Remove unwanted elements like <script>, <style>, etc.
        self._remove_unwanted_tags()

        # Step 3: Handle excludeTags
        if self.scrape_options.get("exclude_tags"):
            self._handle_exclude_tags()

        # Step 4: If onlyMainContent and simple mode, remove non-main content
        if self.scrape_options.get("only_main_content") and extraction_mode == 'simple':
            self._remove_non_main_content()

        # Return the final cleaned HTML
        return self._get_cleaned_html()

    def _handle_include_tags(self):
        include_tags = self.scrape_options["include_tags"]
        # Create a new root element to hold the tags to keep
        new_root = html.Element("div")

        for tag in include_tags:
            for element in self.tree.cssselect(tag):
                new_root.append(element)

        return html.tostring(new_root, pretty_print=True, encoding="unicode")

    def _remove_unwanted_tags(self):
        # Remove common unwanted tags like script, style, etc.
        for unwanted_tag in ["script", "style", "noscript", "meta", "head"]:
            for element in self.tree.cssselect(unwanted_tag):
                element.getparent().remove(element)

    def _handle_exclude_tags(self):
        exclude_tags = self.scrape_options["exclude_tags"]
        for tag in exclude_tags:
            # Handle wildcards or specific tags
            if tag.startswith("*") and tag.endswith("*"):  # For wildcard search
                regex_pattern = re.compile(tag[1:-1], re.IGNORECASE)
                for element in self.tree.cssselect("*"):
                    if regex_pattern.search(element.tag):
                        element.getparent().remove(element)
            else:
                for element in self.tree.cssselect(tag):
                    element.getparent().remove(element)

    def _remove_non_main_content(self):
        # Define a list of tags to exclude from non-main content
        exclude_non_main_tags = ["header", "footer", "nav", "aside"]

        # Add custom selectors from options
        custom_selectors = self.scrape_options.get("custom_only_main_content_selectors", [])

        all_selectors_to_remove = exclude_non_main_tags + custom_selectors

        for selector in all_selectors_to_remove:
            try:
                for element in self.tree.cssselect(selector):
                    # Check if the element has a parent before trying to remove it
                    if element.getparent() is not None:
                        element.getparent().remove(element)
            except Exception:
                # Skip invalid CSS selectors
                continue

    def _get_cleaned_html(self):
        # Return the final cleaned HTML
        return html.tostring(self.tree, pretty_print=True, encoding="unicode")


class HtmlToMarkdown:
    def __init__(self, html_content):
        self.html_content = html_content

    def convert_to_markdown(self):
        h = html2text.HTML2Text()
        h.body_width = 0
        return h.handle(self.html_content)
