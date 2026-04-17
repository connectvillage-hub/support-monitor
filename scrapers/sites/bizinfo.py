from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class BizinfoScraper(BaseScraper):
    site_name = "기업마당"
    list_url = "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"
    max_pages = 15

    def get_page_url(self, page_num):
        return f"https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do?rows=15&cpage={page_num}"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        table = soup.select_one("div.table_Type_1 table tbody") or soup.select_one("table tbody")
        if not table:
            return results
        for tr in table.select("tr"):
            tds = tr.select("td")
            if len(tds) < 6:
                continue
            title_el = tr.select_one("td.txt_l a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            source_url = f"https://www.bizinfo.go.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            results.append({
                "title": title, "source_url": source_url,
                "organization": tds[4].get_text(strip=True),
                "deadline": tds[3].get_text(strip=True),
                "status": "접수중", "category": tds[1].get_text(strip=True),
                "content_snippet": "",
            })
        return results
