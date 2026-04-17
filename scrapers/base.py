import hashlib
import re
import time
import traceback
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from scrapers.config import HEADERS, SCRAPE_DELAY


def is_current_period(title, deadline="", snippet=""):
    """과거 연도 공고 제외 + 마감일 지난 공고 제외."""
    now = datetime.now()
    cur_year = now.year
    text = f"{title} {deadline} {snippet}"

    for y in range(2020, cur_year):
        if re.search(rf"{y}[년\s.\-]", text) and not re.search(rf"{cur_year}[년\s.\-]", text):
            return False

    if deadline:
        dl_text = deadline.split("~")[-1].strip() if "~" in deadline else deadline.strip()
        m = re.search(r"(\d{4})\s*[\.\-/]\s*(\d{1,2})\s*[\.\-/]\s*(\d{1,2})", dl_text)
        if m:
            try:
                dl_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 23, 59)
                if dl_date < now:
                    return False
            except ValueError:
                pass

    return True


class BaseScraper:
    site_name = ""
    list_url = ""
    verify_ssl = True
    max_pages = 10  # 최대 탐색 페이지 수

    def fetch_html(self, url=None):
        url = url or self.list_url
        resp = requests.get(url, headers=HEADERS, timeout=30, verify=self.verify_ssl)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def fetch_json(self, url=None):
        url = url or self.list_url
        resp = requests.get(url, headers=HEADERS, timeout=30, verify=self.verify_ssl)
        resp.raise_for_status()
        return resp.json()

    def parse_programs(self, data):
        raise NotImplementedError

    def get_page_url(self, page_num):
        """Override in subclass to support pagination."""
        return None

    def compute_hash(self, source_url):
        raw = f"{self.site_name}|{source_url}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def scrape(self):
        from app import db, SupportProgram, ScrapeLog, classify_category

        log = ScrapeLog(source_site=self.site_name, scraped_at=datetime.now())
        try:
            all_programs = []

            # Page 1
            data = self.fetch_html() if not hasattr(self, "use_api") else self.fetch_json()
            page1 = self.parse_programs(data)
            all_programs.extend(page1)

            # Pages 2~max_pages
            for pg in range(2, self.max_pages + 1):
                page_url = self.get_page_url(pg)
                if not page_url:
                    break
                try:
                    time.sleep(1)
                    data = self.fetch_html(page_url) if not hasattr(self, "use_api") else self.fetch_json(page_url)
                    items = self.parse_programs(data)
                    if not items:
                        break
                    # Stop if all items on this page are expired
                    valid = [p for p in items if is_current_period(p.get("title",""), p.get("deadline",""), p.get("content_snippet",""))]
                    all_programs.extend(items)
                    if len(valid) == 0:
                        break
                except Exception:
                    break

            log.items_found = len(all_programs)

            new_count = 0
            for p in all_programs:
                if not is_current_period(p.get("title",""), p.get("deadline",""), p.get("content_snippet","")):
                    continue

                h = self.compute_hash(p["source_url"])
                if not SupportProgram.query.filter_by(hash_key=h).first():
                    cat = classify_category(p.get("title",""), p.get("organization",""), p.get("content_snippet",""))
                    db.session.add(SupportProgram(
                        source_site=self.site_name, source_url=p["source_url"],
                        title=p.get("title",""), organization=p.get("organization",""),
                        deadline=p.get("deadline",""), status=p.get("status",""),
                        category=cat, content_snippet=p.get("content_snippet",""),
                        first_seen=datetime.now(), is_new=True, is_read=False, hash_key=h,
                    ))
                    new_count += 1

            db.session.commit()
            log.new_items = new_count
            log.success = True
            print(f"  [{self.site_name}] {log.items_found}건 발견, {new_count}건 신규")
        except Exception as e:
            log.success = False
            log.error_message = traceback.format_exc()
            print(f"  [{self.site_name}] 오류: {e}")
            db.session.rollback()

        try:
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        time.sleep(SCRAPE_DELAY)
        return log
