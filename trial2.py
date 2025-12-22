import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path

# ------------------------- CONFIG -------------------------
OUTPUT_DIR = "learning_pack"
MIN_IMG_WIDTH = 100
MIN_IMG_HEIGHT = 100
MAX_IMAGES = 3
VALID_IMG_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# List of websites to try in order (Wikipedia first, then others)
TOP_SITES = [
    "https://en.wikipedia.org/wiki/",
    "https://www.forbes.com/search/?q=",
    "https://www.coursera.org/search?query=",
    "https://www.hubspot.com/search?term=",
    # Add more sites if needed
]

# ------------------------- HELPERS -------------------------
def fetch_page(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.text
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
    return None

def save_text(topic, text):
    topic_dir = Path(OUTPUT_DIR) / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    file_path = topic_dir / "website_text.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[INFO] Website text saved to {file_path}")

def get_image_dimensions(url):
    # Optional: could download image and get actual dimensions using PIL
    # For simplicity, return placeholder values
    return 200, 200  # assume all images are 200x200 for now

def filter_images(images):
    selected_images = []
    skipped_images = []
    seen_urls = set()

    for img in images:
        url = img.get("src") or img.get("data-src")
        if not url:
            skipped_images.append(("No URL", str(img)))
            continue
        if url in seen_urls:
            skipped_images.append(("Duplicate", url))
            continue
        seen_urls.add(url)

        # Convert relative URLs to absolute if needed
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            # Skip, need base URL context
            skipped_images.append(("Relative URL, skipped", url))
            continue

        if not url.lower().endswith(VALID_IMG_EXTENSIONS):
            skipped_images.append(("Invalid file type", url))
            continue

        width, height = get_image_dimensions(url)
        if width < MIN_IMG_WIDTH or height < MIN_IMG_HEIGHT:
            skipped_images.append((f"Too small {width}x{height}", url))
            continue

        selected_images.append(url)
        if len(selected_images) >= MAX_IMAGES:
            break

    for reason, url in skipped_images:
        print(f"[DEBUG] Skipped image ({reason}): {url}")

    return selected_images

def save_images(topic, image_urls):
    topic_dir = Path(OUTPUT_DIR) / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(image_urls, 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                ext = os.path.splitext(urlparse(url).path)[1]
                file_path = topic_dir / f"image_{i}{ext}"
                with open(file_path, "wb") as f:
                    f.write(res.content)
                print(f"[INFO] Image saved: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to download image {url}: {e}")

# ------------------------- MAIN -------------------------
def process_topic(topic):
    print(f"[INFO] Processing topic: {topic}")
    page_html = None
    for site in TOP_SITES:
        url = site + topic.replace(" ", "_")
        print(f"[INFO] Trying site: {url}")
        page_html = fetch_page(url)
        if page_html:
            print(f"[INFO] Fetched page from {url}")
            break
    if not page_html:
        print(f"[ERROR] Could not fetch any page for topic: {topic}")
        return

    soup = BeautifulSoup(page_html, "html.parser")

    # Save website text
    text_content = soup.get_text(separator="\n", strip=True)
    save_text(topic, text_content)

    # Find and filter images
    images = soup.find_all("img")
    print(f"[DEBUG] Found {len(images)} <img> tags")
    filtered_images = filter_images(images)
    if not filtered_images:
        print("[WARN] No valid images found after filtering")
    save_images(topic, filtered_images)

    print(f"[DONE] Learning pack ready for topic: {topic}")

# ------------------------- ENTRY -------------------------
if __name__ == "__main__":
    topics_input = input("Enter topic(s) (comma-separated if multiple): ")
    topics = [t.strip() for t in topics_input.split(",") if t.strip()]
    for topic in topics:
        process_topic(topic)
