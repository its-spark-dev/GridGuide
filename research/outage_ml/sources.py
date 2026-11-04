"""Bounded, explicit acquisition; external bytes stay in an ignored cache."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

SOURCES = {
    "pnnl-guidelines.docx": ("https://data.openei.org/files/6458/Guideline_OEDI_Updated.docx", 19878, "3295c29a75b07c07382ade83b1093efb9aa8e84696d11d73dad7ac0a8c760c6e"),
    "pnnl-disclaimer.docx": ("https://data.openei.org/files/6458/Disclaimer.docx", 13828, "249619dde1bcc1d81986f63105e4b019e0475beb09f23199e3a1e5af3628f227"),
    "pnnl-v2.zip": ("https://data.openei.org/files/6458/Outage_Dataset_R1.zip", 31260449, "44557bae7a5c8e02c611a14f75fe9e123d81d286f700b9fd88ac538edd910fe7"),
    "purdue.xlsx": ("https://engineering.purdue.edu/LASCI/research-data/outages/outage.xlsx", 660364, "1d64b446ef131f39c99beea2b1380396f94cfaac1e56c722eba0693e13ee253a"),
}
METADATA = {
    "pnnl-catalog.html": "https://data.openei.org/submissions/6458",
    "pnnl-data-gov.html": "https://catalog.data.gov/dataset/event-correlated-outage-dataset-in-america",
    "eaglei-metadata.json": "https://api.figshare.com/v2/articles/24237376",
    "purdue-catalog.html": "https://engineering.purdue.edu/LASCI/research-data/outages",
    "purdue-paper.xml": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6141375/fullTextXML",
    "zenodo-metadata.json": "https://zenodo.org/api/records/22651795",
    "zenodo-paper.xml": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13642956/fullTextXML",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(data: bytes, size: int, sha256: str) -> None:
    if len(data) != size or digest(data) != sha256:
        raise ValueError("Source identity changed; review a new version, do not silently accept it")


def fetch(url: str, limit: int) -> tuple[bytes, dict]:
    with urlopen(url, timeout=45) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Source exceeds acquisition byte budget")
        return data, {"url": url, "resolved_url": response.url,
                      "http_status": response.status, "content_type": response.headers.get("Content-Type"),
                      "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                      "bytes": len(data), "sha256": digest(data)}


def acquire(cache: Path) -> dict:
    """Fetch guides before data. Never downloads the large Zenodo files."""
    cache.mkdir(parents=True, exist_ok=True)
    records = {}
    for name, (url, size, checksum) in SOURCES.items():
        path, receipt = cache / name, cache / (name + ".receipt.json")
        if path.exists():
            validate(path.read_bytes(), size, checksum)
            if not receipt.exists():
                raise ValueError(f"Missing acquisition receipt: {receipt}")
            records[name] = json.loads(receipt.read_text())
            continue
        data, info = fetch(url, size)
        validate(data, size, checksum)
        path.write_bytes(data)
        receipt.write_text(json.dumps(info, indent=2) + "\n")
        records[name] = info
    for name, url in METADATA.items():
        path, receipt = cache / name, cache / (name + ".receipt.json")
        if not path.exists():
            data, info = fetch(url, 2_000_000)
            path.write_bytes(data)
            receipt.write_text(json.dumps(info, indent=2) + "\n")
        info = json.loads(receipt.read_text())
        validate(path.read_bytes(), info["bytes"], info["sha256"])
        records[name] = info
    meta = json.loads((cache / "zenodo-metadata.json").read_text())
    for item in meta["files"]:
        if not item["key"].endswith("_Sensitivity_Summary.csv"):
            continue
        name = item["key"]
        if item["size"] > 10_000:
            raise ValueError("Sensitivity summary exceeds budget")
        path, receipt = cache / name, cache / (name + ".receipt.json")
        if not path.exists():
            data, info = fetch(item["links"]["self"], 10_000)
            if len(data) != item["size"] or "md5:" + hashlib.md5(data).hexdigest() != item["checksum"]:
                raise ValueError("Zenodo publisher checksum mismatch")
            info["publisher_checksum"] = item["checksum"]
            path.write_bytes(data)
            receipt.write_text(json.dumps(info, indent=2) + "\n")
        info = json.loads(receipt.read_text())
        validate(path.read_bytes(), info["bytes"], info["sha256"])
        records[name] = info
    return records
