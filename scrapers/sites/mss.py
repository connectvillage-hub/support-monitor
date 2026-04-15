import re
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class MssScraper(BaseScraper):
    site_name = "중소벤처기업부"
    list_url = "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310"

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
            title_el = tr.select_one("td.subject a") or tr.select_one("td a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            onclick = tr.get("onclick", "")
            source_url = self.list_url
            m = re.search(r"(\d{5,})", onclick)
            if m:
                source_url = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={m.group(1)}"
            dept_el = tr.select_one("div.tableInfoBox dd")
            results.append({"title": title, "source_url": source_url, "organization": dept_el.get_text(strip=True) if dept_el else "중소벤처기업부", "deadline": "", "status": "", "category": "", "content_snippet": ""})
        return results
