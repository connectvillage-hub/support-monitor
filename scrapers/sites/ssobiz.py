from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class SsobizScraper(BaseScraper):
    site_name = "소상공인연합회"
    list_url = "https://www.kfme.or.kr/kr/board/notice.php?cate=1"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        container = soup.select_one("article.bbs-list-tbody")
        if not container:
            return results
        for row in container.select("div.bbs-list-row"):
            title_el = row.select_one("div.bbs-title a strong.bbs-subject-txt") or row.select_one("div.bbs-title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link_el = row.select_one("div.bbs-title a")
            href = link_el.get("href", "") if link_el else ""
            source_url = f"https://www.kfme.or.kr{href}" if href and not href.startswith("http") else (href or self.list_url)
            date_el = row.select_one("div[data-label='등록일']")
            results.append({"title": title, "source_url": source_url, "organization": "소상공인연합회", "deadline": "", "status": "", "category": "", "content_snippet": date_el.get_text(strip=True) if date_el else ""})
        return results
