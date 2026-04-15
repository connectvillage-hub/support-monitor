from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class BizinfoScraper(BaseScraper):
    site_name = "기업마당"
    list_url = "https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do"

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
            if href and not href.startswith("http"):
                source_url = f"https://www.bizinfo.go.kr{href}"
            else:
                source_url = href or self.list_url
            category = tds[1].get_text(strip=True)
            deadline = tds[3].get_text(strip=True)
            org = tds[4].get_text(strip=True)
            results.append({
                "title": title, "source_url": source_url,
                "organization": org, "deadline": deadline,
                "status": "접수중", "category": category,
                "content_snippet": "",
            })
        return results
