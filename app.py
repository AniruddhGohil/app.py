import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import tldextract
from urllib.parse import urljoin, urlparse

TIMEOUT = 10

def is_internal_link(link, base_domain):
    parsed = urlparse(link)
    return parsed.netloc == "" or base_domain in parsed.netloc

def get_links_from_page(url, base_domain):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            full_url = urljoin(url, a["href"])
            if is_internal_link(full_url, base_domain):
                links.append(full_url.split("#")[0])
        return list(set(links))
    except:
        return []

def check_redirect(url):
    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        final_url = r.url
        return r.status_code, final_url
    except:
        return None, None

st.title("🔗 Internal Link Redirect Checker")
st.write("Checks internal links for 301/302 redirects and suggests the final 200 URLs.")

start_url = st.text_input("Enter Website URL (e.g., https://example.com)")
max_pages = st.slider("Max Pages to Crawl", 1, 200, 20)

if st.button("Start Crawling") and start_url:
    base_domain = tldextract.extract(start_url).registered_domain
    to_crawl = [start_url]
    crawled = set()
    results = []

    with st.spinner("Crawling in progress..."):
        while to_crawl and len(crawled) < max_pages:
            current_url = to_crawl.pop(0)
            if current_url in crawled:
                continue
            crawled.add(current_url)

            links = get_links_from_page(current_url, base_domain)

            for link in links:
                status, final_url = check_redirect(link)
                if status in [301, 302]:
                    results.append({
                        "Source Page": current_url,
                        "Old Link": link,
                        "Status": status,
                        "Final Destination": final_url,
                        "Final Status": requests.get(final_url, timeout=TIMEOUT).status_code
                    })

            for link in links:
                if link not in crawled and link not in to_crawl:
                    to_crawl.append(link)

    if results:
        df = pd.DataFrame(results)
        st.dataframe(df)
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="internal_link_redirect_report.csv",
            mime="text/csv"
        )
    else:
        st.info("No redirects found or no pages crawled.")
