from lxml import html
import requests


def scrape_excel(file):
    report_urls = _get_report_urls(file)
    return [requests.get(url).content for url in report_urls]


def _get_report_urls(file):
    """source inconsistencies:
    file extentions used are 'xls' and 'xlsx'
    file naming is singular and plural
    """
    base_url = "https://www.asisa.org.za/"
    stats_page = "statistics/collective-investments-schemes/local-fund-statistics/"

    response = requests.get(f"{base_url}{stats_page}")

    page = html.fromstring(response.content)
    urls_on_page = page.xpath("//a/@href")

    return [f"{base_url}{url}" for url in urls_on_page if "xls" in url and file in url]
