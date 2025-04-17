import streamlit as st
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import re
import pandas as pd

st.set_page_config(page_title="Kunst am Bau – Ausschreibungen Finder", layout="wide")
st.title("🎨 Kunst am Bau – Ausschreibungen Finder")

URL = "https://www.bbk-bundesverband.de/ausschreibungen/aktuelle-ausschreibungen"
KEYWORDS = ["kunst am bau", "kunst und bau", "künstlerische gestaltung"]

@st.cache_data(show_spinner=True)
def scrape_bbk():
    relevante_ausschreibungen = []
    response = requests.get(URL)
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a", href=True)

    total_links = len(links)
    with st.spinner(f"Durchsuche {total_links} Links..."):
        for i, link in enumerate(links):
            href = link["href"]
            title = link.get_text(strip=True)

            if not href.startswith("http"):
                href = "https://www.bbk-bundesverband.de" + href

            try:
                if ".pdf" in href:
                    pdf_response = requests.get(href)
                    pdf = fitz.open(stream=pdf_response.content, filetype="pdf")
                    text = ""
                    for page in pdf:
                        text += page.get_text()
                else:
                    sub_resp = requests.get(href)
                    sub_soup = BeautifulSoup(sub_resp.content, "html.parser")
                    text = sub_soup.get_text()

                if any(kw in text.lower() for kw in KEYWORDS):
                    deadline_match = re.search(r"(?i)(frist.*?[:\s\s]*)(\d{1,2}\.\d{1,2}\.\d{4})", text)
                    ort_match = re.search(r"(?i)(ort[:\s]+)([A-ZÄÖÜa-zäöü\s\-]+)", text)
                    frist = deadline_match.group(2) if deadline_match else "?"
                    ort = ort_match.group(2).strip() if ort_match else "?"

                    relevante_ausschreibungen.append({
                        "Titel": title,
                        "Frist": frist,
                        "Ort": ort,
                        "Link": href
                    })
            except Exception as e:
                st.error(f"Fehler bei Link {i+1}/{total_links}: {href}. Fehler: {str(e)}")

            # Fortschrittsanzeige
            progress = (i + 1) / total_links * 100
            st.progress(progress)

    return pd.DataFrame(relevante_ausschreibungen)

if st.button("🔍 Jetzt nach Ausschreibungen suchen"):
    with st.spinner("Durchsuche BBK-Website nach relevanten Ausschreibungen..."):
        df = scrape_bbk()

    if not df.empty:
        st.success(f"{len(df)} relevante Ausschreibungen gefunden.")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Als CSV herunterladen",
            data=csv,
            file_name="kunst_am_bau_ausschreibungen.csv",
            mime="text/csv",
        )
    else:
        st.info("Keine relevanten Ausschreibungen gefunden.")
else:
    st.info("Klicke auf den Button, um nach Ausschreibungen zu suchen.")
