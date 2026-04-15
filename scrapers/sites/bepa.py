from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class BepaScraper(BaseScraper):
    site_name = "부산경제진흥원"
    list_url = "https://www.bepa.kr/kor/view.do?no=1502"
    verify_ssl = False

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        tbody = soup.select_one("table.skin_01 tbody") or soup.select_one("table tbody")
        if not tbody:
            return results
        for tr in tbody.select("tr"):
            title_el = tr.select_one("td.title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            source_url = f"https://www.bepa.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            org_el = tr.select_one("td.orgNm")
            st_el = tr.select_one("td.shape span")
            status = ""
            if st_el:
                cls = st_el.get("class", [])
                status = "진행중" if "info_ing" in cls else ("마감" if "info_done" in cls else st_el.get_text(strip=True))
            results.append({"title": title, "source_url": source_url, "organization": org_el.get_text(strip=True) if org_el else "부산경제진흥원", "deadline": "", "status": status, "category": "", "content_snippet": ""})
        return results


class BkicScraper(BaseScraper):
    site_name = "부산지식산업센터"
    list_url = "http://bkic.bepa.kr/bsknow/view.do?no=1477"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        tbody = soup.select_one("table tbody")
        if not tbody:
            return results
        for tr in tbody.select("tr"):
            title_el = tr.select_one("td.l a.f14") or tr.select_one("td a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            source_url = f"http://bkic.bepa.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            tds = tr.select("td")
            results.append({"title": title, "source_url": source_url, "organization": "부산지식산업센터", "deadline": "", "status": "", "category": "", "content_snippet": tds[3].get_text(strip=True) if len(tds) > 3 else ""})
        return results
