from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class BtpScraper(BaseScraper):
    site_name = "부산테크노파크"
    list_url = "https://www.btp.or.kr/kor/CMS/Board/Board.do?mCode=MN013"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        tbody = soup.select_one("table.bdListTbl tbody") or soup.select_one("table tbody")
        if not tbody:
            return results
        for tr in tbody.select("tr"):
            title_el = tr.select_one("td.subject a")
            if not title_el:
                continue
            title_span = title_el.select_one("span.titleHover") or title_el.select_one("span.subjectWr")
            title = title_span.get_text(strip=True) if title_span else title_el.get_text(strip=True)
            href = title_el.get("href", "")
            source_url = f"https://www.btp.or.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            period_el = tr.select_one("td.period")
            deadline = ""
            if period_el:
                deadline = period_el.get_text(strip=True)
                dday = period_el.select_one("span.dday")
                if dday:
                    deadline = deadline.replace(dday.get_text(strip=True), "").strip()
            status_el = tr.select_one("td.state span.status")
            results.append({"title": title, "source_url": source_url, "organization": "부산테크노파크", "deadline": deadline, "status": status_el.get_text(strip=True) if status_el else "", "category": "", "content_snippet": ""})
        return results
