import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from ddgs import DDGS

# ---------------- CONFIG ---------------- #

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

BASE_OUTPUT_DIR = "learning_pack"
MIN_IMAGE_COUNT = 3
TIMEOUT = 15

# ---------------------------------------- #


def sanitize_folder_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def search_web(topic: str):
    query = f"{topic} tutorial explanation"
    print(f"[INFO] Search query: {query}")

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=10):
            results.append(r)

    return results


def score_page(url: str, topic: str):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code != 200:
            return 0, 0

        soup = BeautifulSoup(resp.text, "lxml")

        text_score = soup.get_text().lower().count(topic.lower())
        images = extract_image_urls(soup, url)

        return text_score, len(images)

    except Exception:
        return 0, 0


def extract_image_urls(soup, base_url):
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue

        src = urljoin(base_url, src)
        parsed = urlparse(src)

        if parsed.scheme.startswith("http") and any(
            src.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]
        ):
            images.append(src)

    return list(set(images))


def select_best_site(results, topic):
    candidates = []

    for r in results:
        url = r.get("href")
        if not url:
            continue

        score, image_count = score_page(url, topic)

        if image_count == 0:
            print(f"[DEBUG] Rejected (no images): {url}")
            continue

        print(f"[DEBUG] Score {score} | Images {image_count} | {url}")
        candidates.append((score, image_count, url))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def download_images(image_urls, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    saved = 0

    for idx, url in enumerate(image_urls, start=1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code != 200:
                continue

            ext = os.path.splitext(urlparse(url).path)[1]
            filename = f"image_{idx}{ext}"
            path = os.path.join(output_dir, filename)

            with open(path, "wb") as f:
                f.write(r.content)

            saved += 1

        except Exception as e:
            print(f"[WARN] Failed to download image: {url}")

    return saved


def process_topic(topic: str):
    print(f"\n[INFO] Processing topic: {topic}")

    results = search_web(topic)
    best_site = select_best_site(results, topic)

    if not best_site:
        raise RuntimeError("No valid site with images found")

    print(f"[INFO] Selected site: {best_site}")

    resp = requests.get(best_site, headers=HEADERS, timeout=TIMEOUT)
    soup = BeautifulSoup(resp.text, "lxml")

    image_urls = extract_image_urls(soup, best_site)

    if len(image_urls) < MIN_IMAGE_COUNT:
        raise RuntimeError("Image extraction failed (should not happen)")

    topic_dir = os.path.join(BASE_OUTPUT_DIR, sanitize_folder_name(topic))
    image_dir = os.path.join(topic_dir, "images")

    saved = download_images(image_urls, image_dir)

    if saved == 0:
        raise RuntimeError("Images detected but none saved")

    with open(os.path.join(topic_dir, "source.txt"), "w", encoding="utf-8") as f:
        f.write(best_site)

    print(f"[INFO] Saved {saved} images")
    print(f"[DONE] Learning pack ready → {topic_dir}")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    topics = input("Enter topic(s) (comma-separated if multiple): ")

    for t in topics.split(","):
        t = t.strip()
        if not t:
            continue
        process_topic(t)
