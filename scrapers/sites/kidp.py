import re
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class KidpScraper(BaseScraper):
    site_name = "한국디자인진흥원"
    list_url = "https://kidp.or.kr/index.html?menuno=1202"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        tbody = soup.select_one("table tbody")
        if not tbody:
            return results
        for tr in tbody.select("tr"):
            tds = tr.select("td")
            if len(tds) < 3:
                continue
            title_el = tr.select_one("td.left a") or tr.select_one("td a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            onclick = title_el.get("onclick", "")
            m = re.search(r"submitForm\(this,\s*'view'\s*,\s*(\d+)", onclick)
            source_url = f"https://kidp.or.kr/index.html?menuno=1202&bbsNo={m.group(1)}&mode=view" if m else self.list_url
            results.append({"title": title, "source_url": source_url, "organization": "한국디자인진흥원", "deadline": "", "status": "", "category": "", "content_snippet": tds[2].get_text(strip=True) if len(tds) > 2 else ""})
        return results
