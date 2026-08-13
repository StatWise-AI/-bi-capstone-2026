"""
download_data.py
-----------------
Downloads the real-world DataCo Smart Supply Chain dataset (~180,500 orders,
53 columns) used for this project. The raw file is ~95MB, so it is NOT
committed to the GitHub repository. Run this script once after cloning.

Source: Constante, Fabian; Silva, Fernando; Pereira, Antonio (2019),
"DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS", Mendeley Data, V5,
doi: 10.17632/8gx2fvg2k6.5  (mirrored on GitHub for direct download)

Usage:
    python src/download_data.py
"""
import os
import sys
import urllib.request

RAW_URL = (
    "https://raw.githubusercontent.com/ashishpatel26/"
    "DataCo-SMART-SUPPLY-CHAIN-FOR-BIG-DATA-ANALYSIS/main/"
    "DataCoSupplyChainDataset.csv"
)
DESCRIPTION_URL = (
    "https://raw.githubusercontent.com/ashishpatel26/"
    "DataCo-SMART-SUPPLY-CHAIN-FOR-BIG-DATA-ANALYSIS/main/"
    "DescriptionDataCoSupplyChain.csv"
)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def download(url: str, dest: str) -> None:
    if os.path.exists(dest):
        print(f"[skip] {dest} already exists")
        return
    print(f"[download] {url}\n         -> {dest}")
    urllib.request.urlretrieve(url, dest)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"[done] {dest} ({size_mb:.1f} MB)")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    download(RAW_URL, os.path.join(OUT_DIR, "DataCoSupplyChainDataset.csv"))
    download(DESCRIPTION_URL, os.path.join(OUT_DIR, "DescriptionDataCoSupplyChain.csv"))
    print("\nAll set. Full dataset is in data/raw/. "
          "If the download ever fails (e.g. blocked network), a smaller "
          "5,000-row stratified sample is already committed at "
          "data/sample/DataCoSupplyChain_sample.csv so the pipeline still runs.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"[error] Could not download dataset automatically: {exc}")
        print("You can also download it manually from:")
        print(f"  {RAW_URL}")
        print("and place it at data/raw/DataCoSupplyChainDataset.csv")
        sys.exit(1)
