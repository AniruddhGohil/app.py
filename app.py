import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd

# ---------------- CONFIG ----------------
TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# ---------------- HELPER FUNCTIONS ----------------
def normalize_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")

def is_internal_link(base_url, link):
    return urlparse(link).netloc == urlparse(base_url).netloc or urlparse(link).netloc == ""

def crawl_site(start_url, max_pages=20):
    visited = set()
    to_visit = [start_url]
    redirects = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        st.write(f"🔍 Crawling: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=False)
        except requests.RequestException as e:
            st.write(f"❌ Error fetching {url}: {e}")
            continue

        # Check for redirect
        if 300 <= resp.status_code < 400:
            location = resp.headers.get("Location")
            if location:
                final_url = urljoin(url, location)
                try:
                    final_resp = requests.get(final_url, headers=HEADERS, timeout=TIMEOUT)
                    redirects.append({
                        "Source URL": url,
                        "Redirect URL": final_url,
                        "Final Status": final_resp.status_code
                    })
                except requests.RequestException:
                    redirects.append({
                        "Source URL": url,
                        "Redirect URL": final_url,
                        "Final Status": "Error"
                    })

        # Parse links for crawling
        soup = BeautifulSoup(resp.text, "html.parser")
        for link in soup.find_all("a", href=True):
            full_link = urljoin(url, link["href"])
            if is_internal_link(start_url, full_link) and full_link not in visited:
                to_visit.append(full_link)

    return redirects

# ---------------- STREAMLIT APP ----------------
st.set_page_config(page_title="Internal Link Redirect Checker", layout="wide")

st.title("🔗 Internal Link Redirect Checker")
st.markdown("Check your site's internal links and replace redirects with direct URLs for better SEO.")

base_url = st.text_input("Enter your website URL", placeholder="https://example.com")
max_pages = st.slider("Max pages to crawl", 5, 200, 20)

if st.button("Start Checking"):
    if base_url:
        base_url = normalize_url(base_url)
        st.info(f"Starting crawl from: {base_url}")
        data = crawl_site(base_url, max_pages=max_pages)

        if data:
            df = pd.DataFrame(data)
            st.subheader("Found Redirects")
            st.dataframe(df)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "redirects.csv", "text/csv")
        else:
            st.success("✅ No internal redirects found!")
    else:
        st.error("Please enter a website URL.")

# ---------------- FOOTER ----------------
st.markdown(
    """
    <hr>
    <p style="text-align:center;">
    Created by <b>Aniruddh Gohil</b> with ❤️ <br>
    <a href="https://github.com/AniruddhGohil" target="_blank">GitHub</a> |
    <a href="https://x.com/AniruddhGohil_" target="_blank">Twitter</a>
    </p>
    """,
    unsafe_allow_html=True
)
