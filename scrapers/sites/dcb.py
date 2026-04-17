from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class DcbScraper(BaseScraper):
    site_name = "부산디자인진흥원"
    list_url = "https://dcb.or.kr/01_news/?mcode=0401010000"
    max_pages = 5

    def get_page_url(self, page_num):
        return f"https://dcb.or.kr/01_news/?mcode=0401010000&mode=1&page={page_num}"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        tbody = soup.select_one("table tbody")
        if not tbody:
            return results
        for tr in tbody.select("tr"):
            title_el = tr.select_one("td.link a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            source_url = f"https://dcb.or.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            st_el = tr.select_one("td.status span")
            status = ""
            if st_el:
                cls = st_el.get("class", [])
                status = "진행" if "st_ing" in cls else ("종료" if "st_end" in cls else st_el.get_text(strip=True))
            cat_el = tr.select_one("td.case")
            date_el = tr.select_one("td.date")
            results.append({"title": title, "source_url": source_url, "organization": "부산디자인진흥원", "deadline": "", "status": status, "category": cat_el.get_text(strip=True) if cat_el else "", "content_snippet": date_el.get_text(strip=True) if date_el else ""})
        return results
