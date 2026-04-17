import re
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper


class KStartupScraper(BaseScraper):
    site_name = "K스타트업"
    list_url = "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do"
    max_pages = 5

    def get_page_url(self, page_num):
        return f"https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?page={page_num}"

    def parse_programs(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for li in soup.select("ul > li.notice"):
            inner = li.select_one("div.inner")
            if not inner:
                continue
            title_el = inner.select_one("p.tit")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            link_el = inner.select_one("div.middle a")
            source_url = self.list_url
            if link_el:
                onclick = link_el.get("href", "") or link_el.get("onclick", "")
                m = re.search(r"go_view\(['\"]?(\d+)", onclick)
                if m:
                    source_url = f"https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?schM=view&pbancSn={m.group(1)}"
            spans = inner.select("div.bottom span.list")
            org, deadline = "", ""
            for span in spans:
                t = span.get_text(strip=True)
                if "마감일자" in t:
                    deadline = t.replace("마감일자", "").strip()
                elif "등록일자" not in t and "조회수" not in t and "시작일자" not in t and t and not org:
                    org = t
            cat_el = inner.select_one("span.flag")
            results.append({"title": title, "source_url": source_url, "organization": org, "deadline": deadline, "status": "접수중", "category": cat_el.get_text(strip=True) if cat_el else "", "content_snippet": ""})
        return results
