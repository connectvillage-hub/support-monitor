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
            title_el = row.select_one("strong.bbs-subject-txt")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            # Remove "공지사항" prefix from pinned rows
            title = title.replace("공지사항", "").strip()
            if not title:
                continue
            link_el = row.select_one("div.bbs-title a")
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                source_url = f"https://www.kfme.or.kr{href}"
            else:
                source_url = href or self.list_url
            date_el = row.select_one("div[data-label='등록일']")
            results.append({
                "title": title, "source_url": source_url,
                "organization": "소상공인연합회", "deadline": "",
                "status": "", "category": "",
                "content_snippet": date_el.get_text(strip=True) if date_el else "",
            })
        return results
