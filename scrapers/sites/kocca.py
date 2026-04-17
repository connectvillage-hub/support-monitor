from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class KoccaScraper(BaseScraper):
    site_name = "한국콘텐츠진흥원"
    list_url = "https://www.kocca.kr/kocca/pims/list.do?menuNo=20410&recptSt="
    max_pages = 5

    def get_page_url(self, page_num):
        return f"https://www.kocca.kr/kocca/pims/list.do?menuNo=20410&recptSt=&pageIndex={page_num}"

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
            title_el = tr.select_one("td.AlignLeft a") or tr.select_one("td a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            source_url = f"https://www.kocca.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            cat_el = tr.select_one("td[data-label='구분'] span")
            dl_el = tr.select_one("td[data-label='접수기간']")
            results.append({"title": title, "source_url": source_url, "organization": "한국콘텐츠진흥원", "deadline": dl_el.get_text(strip=True) if dl_el else "", "status": "", "category": cat_el.get_text(strip=True) if cat_el else "", "content_snippet": ""})
        return results
