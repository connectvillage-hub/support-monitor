from scrapers.base import BaseScraper


class BsiaScraper(BaseScraper):
    site_name = "부산기술창업투자원"
    list_url = "https://www.bsia.or.kr/api/announcements?pno=1&mcode=news02"
    use_api = True
    max_pages = 5

    def get_page_url(self, page_num):
        return f"https://www.bsia.or.kr/api/announcements?pno={page_num}&mcode=news02"

    def fetch_html(self):
        return self.fetch_json()

    def parse_programs(self, data):
        results = []
        for item in (data.get("list", []) if isinstance(data, dict) else []):
            title = item.get("bsa_title", "")
            if not title:
                continue
            bsa_seq = item.get("bsa_seq", "")
            url = f"https://www.bsia.or.kr/announcements/{bsa_seq}?mcode=news02" if bsa_seq else self.list_url
            dl = item.get("bsa_apl_edt", "") or item.get("bsa_edt", "") or ""
            if dl:
                dl = dl.split(" ")[0]
            results.append({"title": title.strip(), "source_url": url, "organization": item.get("bsa_agency", "") or "부산기술창업투자원", "deadline": dl, "status": "접수중", "category": item.get("bs_type_str", ""), "content_snippet": ""})
        return results
