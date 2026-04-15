import re
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class ArteScraper(BaseScraper):
    site_name = "한국문화예술교육진흥원"
    list_url = "https://arte.or.kr/notice/business/notice/Business_BoardList.do"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        tbody = soup.select_one("table tbody")
        if not tbody:
            return results
        for tr in tbody.select("tr"):
            tds = tr.select("td")
            if len(tds) < 4:
                continue
            title_el = tr.select_one("td.Lalign a span") or tr.select_one("td.Lalign a") or tr.select_one("td a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link_el = tr.select_one("td.Lalign a") or tr.select_one("td a")
            source_url = self.list_url
            if link_el:
                href = link_el.get("href", "")
                m = re.search(r"fnView\(['\"]([^'\"]+)['\"]", href)
                if m:
                    source_url = f"https://arte.or.kr/notice/business/notice/Business_BoardView.do?board_id={m.group(1)}"
            status_el = tr.select_one("td span.txtred") or tr.select_one("td span.txtgray2")
            status = status_el.get_text(strip=True) if status_el else ""
            results.append({"title": title, "source_url": source_url, "organization": "한국문화예술교육진흥원", "deadline": "", "status": status, "category": "", "content_snippet": ""})
        return results
