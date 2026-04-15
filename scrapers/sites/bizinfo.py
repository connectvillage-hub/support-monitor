from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class BizinfoScraper(BaseScraper):
    site_name = "기업마당"
    list_url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        table = soup.select_one("table tbody")
        if not table:
            return results
        for tr in table.select("tr"):
            tds = tr.select("td")
            if len(tds) < 5:
                continue
            title_el = tr.select_one("td.txt_l a") or tr.select_one("td a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            source_url = f"https://www.bizinfo.go.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            results.append({"title": title, "source_url": source_url, "organization": tds[4].get_text(strip=True) if len(tds) > 4 else "", "deadline": tds[3].get_text(strip=True) if len(tds) > 3 else "", "status": "접수중", "category": tds[1].get_text(strip=True) if len(tds) > 1 else "", "content_snippet": ""})
        return results
