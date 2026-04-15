from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class SmtechScraper(BaseScraper):
    site_name = "중소기업기술개발"
    list_url = "https://www.smtech.go.kr/front/main/main.do"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        notice_list = soup.select_one("div[name='ancmList']") or soup.select_one("div.notice_list")
        if not notice_list:
            return results
        for li in notice_list.select("li[id^='ancmDetail']"):
            dl = li.select_one("dl")
            if not dl:
                continue
            dt = dl.select_one("dt")
            if not dt:
                continue
            title_text = dt.get_text(strip=True)
            for span in dt.select("span"):
                title_text = title_text.replace(span.get_text(strip=True), "")
            title = title_text.strip()
            if not title:
                continue
            status_el = dt.select_one("span.ing_icon") or dt.select_one("span.com_icon")
            deadline_el = dt.select_one("span.endday")
            deadline = deadline_el.get_text(strip=True).replace("마감일", "").strip() if deadline_el else ""
            detail_el = dl.select_one("a.detail_bt") or dl.select_one("dd a[href*='notice02_detail']")
            source_url = self.list_url
            if detail_el:
                href = detail_el.get("href", "")
                source_url = f"https://www.smtech.go.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            dd = dl.select_one("dd")
            results.append({"title": title, "source_url": source_url, "organization": "중소기업기술정보진흥원", "deadline": deadline, "status": status_el.get_text(strip=True) if status_el else "", "category": "", "content_snippet": dd.get_text(strip=True) if dd else ""})
        return results
