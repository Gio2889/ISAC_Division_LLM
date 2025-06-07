# custom_wiki_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class CustomWikiScraper:
    def __init__(self, base_url,print_logs = False):
        self.base_url = base_url
        self.print_logs = print_logs
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _is_valid_wiki_url(self, url):
        """Check if URL belongs to the same wiki domain"""
        return urlparse(url).netloc == urlparse(self.base_url).netloc
    
    def scrape_page(self, url):
        """Scrape content from a single wiki page"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements (customize per wiki structure)
            for element in soup.select('.sidebar, .infobox, .navbox, .mw-editsection, .reference'):
                element.decompose()
            
            # Identify main content area (common patterns)
            content_selectors = [
                '#mw-content-text',  # MediaWiki standard
                '.mw-parser-output',  # Alternative MediaWiki
                '.page-content',  # Fandom wikis
                '#content',  # Generic
                'article'  # HTML5
            ]
            
            content = None
            for selector in content_selectors:
                if soup.select_one(selector):
                    content = soup.select_one(selector)
                    break
            
            if not content:
                return None
                
            text = content.get_text(separator='\n', strip=True)
            return {
                "url": url,
                "title": soup.title.string if soup.title else url,
                "content": text
            }
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_entire_wiki(self, max_pages=100):
        """Crawl through wiki starting from base URL"""
        visited = set()
        to_visit = {self.base_url}
        documents = []
        
        while to_visit and len(documents) < max_pages:
            url = to_visit.pop()
            if url in visited:
                continue
                
            visited.add(url)
            page_data = self.scrape_page(url)
            
            if page_data:
                documents.append({
                    "source": f"Custom Wiki: {page_data['title']}",
                    "content": page_data['content']
                })
                if self.print_logs:
                    print(f"Scraped: {page_data['title']}")
                
                # Find new links on page
                response = self.session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    if (self._is_valid_wiki_url(full_url) and
                        '#section' not in full_url and
                        'Special:' not in full_url and
                        'File:' not in full_url and
                        full_url not in visited):
                        to_visit.add(full_url)
        
        return documents