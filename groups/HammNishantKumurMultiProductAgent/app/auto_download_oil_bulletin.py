"""
auto_download_oil_bulletin.py
===============================
Downloads the latest "Price developments 2005 onwards" workbook directly
from the European Commission's official Weekly Oil Bulletin page, replacing
the local copy -- no manual browser download needed.

Source page (for reference / if this ever needs checking by hand):
https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en

The direct file link below is the same one used to build this project
originally. Document links on this site are generated once per file and
have stayed stable across at least the last two years of bulletin updates,
but government sites do occasionally restructure -- if this script ever
starts failing, that's the first thing to check by visiting the page above
and copying the current "Price developments 2005 onwards (xlsx)" link.
"""
import os
import sys
import requests
from datetime import datetime

DIRECT_URL = (
    "https://energy.ec.europa.eu/document/download/"
    "906e60ca-8b6a-44e7-8589-652854d2fd3f_en"
    "?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx"
)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(APP_DIR, "Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx")


def main():
    print(f"Downloading latest Oil Bulletin data from the European Commission...")
    try:
        resp = requests.get(DIRECT_URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"\nDownload failed: {e}")
        print("This usually means either your internet connection is down, or the "
              "European Commission has changed the download link. Check by visiting:")
        print("  https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en")
        print("and looking for 'Price developments 2005 onwards (xlsx)' -- if the link "
              "there differs from the one in this script, update DIRECT_URL accordingly.")
        sys.exit(1)

    content = resp.content
    size_mb = len(content) / (1024 * 1024)

    # Sanity check: the real file is consistently a few MB. A tiny response
    # (a few KB) usually means we got an HTML error page instead of the
    # actual spreadsheet -- fail loudly rather than silently overwriting
    # good data with garbage.
    if size_mb < 1.0:
        print(f"\nDownload returned only {size_mb:.2f} MB -- too small to be the real file "
              f"(it's normally several MB). Not overwriting your existing copy.")
        print("The link likely returned an error page instead of the spreadsheet. "
              "Check the official page manually:")
        print("  https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en")
        sys.exit(1)

    # Back up the previous copy, just in case
    if os.path.exists(TARGET_PATH):
        backup_path = TARGET_PATH.replace(".xlsx", f"_backup_{datetime.now().strftime('%Y%m%d')}.xlsx")
        os.replace(TARGET_PATH, backup_path)
        print(f"Backed up previous file to: {os.path.basename(backup_path)}")

    with open(TARGET_PATH, "wb") as f:
        f.write(content)

    print(f"Downloaded {size_mb:.1f} MB -- saved as {os.path.basename(TARGET_PATH)}")
    print("Ready for extract_master.py.")


if __name__ == "__main__":
    main()
