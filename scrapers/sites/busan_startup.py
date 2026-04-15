from scrapers.base import BaseScraper


class BusanStartupScraper(BaseScraper):
    site_name = "부산창업포털"
    list_url = "https://www.busanstartup.kr/_Api/bizListData?deadline=N&mcode=biz02&pageNo=1"
    use_api = True

    def fetch_html(self):
        return self.fetch_json()

    def parse_programs(self, data):
        results = []
        for item in (data.get("list", []) if isinstance(data, dict) else []):
            title = item.get("busi_title", "")
            if not title:
                continue
            code = item.get("busi_code", "")
            url = f"https://www.busanstartup.kr/biz_sup/{code}?mcode=biz02" if code else self.list_url
            dl = item.get("appl_edate", "") or ""
            if dl:
                dl = dl.split(" ")[0]
            results.append({"title": title.strip(), "source_url": url, "organization": item.get("busi_comp", ""), "deadline": dl, "status": "접수중", "category": item.get("busi_gubun", ""), "content_snippet": ""})
        return results
