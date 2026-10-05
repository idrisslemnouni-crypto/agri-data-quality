"""Download and validate the immutable, attributed source archive."""

import hashlib
import logging
import time
import urllib.request
import zipfile
from pathlib import Path

LOGGER = logging.getLogger(__name__)
SOURCE_URL = "https://zenodo.org/records/7751191/files/county-data.zip?download=1"
SOURCE_MD5 = "b7cf000262da294caffc2fea39932246"
SOURCE_BYTES = 50_051_357
FILES = ("YIELD_COUNTY_US.csv", "METEO_COUNTY_US.csv", "SOIL_COUNTY_US.csv")


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(path: Path) -> None:
    if path.stat().st_size != SOURCE_BYTES or file_hash(path, "md5") != SOURCE_MD5:
        raise ValueError("Source archive does not match the official size and MD5 checksum")


def download_data(raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive = raw_dir / "county-data.zip"
    if not archive.exists():
        temporary = archive.with_suffix(".part")
        request = urllib.request.Request(
            SOURCE_URL, headers={"User-Agent": "crop-yield-portfolio/0.1"}
        )
        for attempt in range(3):
            try:
                with (
                    urllib.request.urlopen(request, timeout=90) as source,
                    temporary.open("wb") as dest,
                ):
                    while chunk := source.read(1024 * 1024):
                        dest.write(chunk)
                verify_archive(temporary)
                temporary.replace(archive)
                break
            except (OSError, ValueError):
                temporary.unlink(missing_ok=True)
                if attempt == 2:
                    raise
                LOGGER.warning("Download failed; retrying (%s/3)", attempt + 1)
                time.sleep(2)
    verify_archive(archive)
    with zipfile.ZipFile(archive) as source:
        for name in FILES:
            with source.open(f"county-data/{name}") as origin, (raw_dir / name).open("wb") as dest:
                while chunk := origin.read(1024 * 1024):
                    dest.write(chunk)
    LOGGER.info("Verified source archive; extracted %s files", len(FILES))
    return raw_dir
