import os
import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import string

# ----------------------------
# 1. User input
# ----------------------------
topic = input("Enter the topic you want to learn about: ")
print(f"[INFO] Topic received: {topic}")

# ----------------------------
# 2. Free web search with ddgs
# ----------------------------
def free_search_ddgs(query, max_results=10):
    print("[INFO] Running free web search (ddgs)...")
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, region="wt-wt", safesearch="Off"):
            url = r.get("href")
            if url and url.startswith("http"):
                results.append(url)
                print(f"[DEBUG] Found URL: {url}")
                if len(results) >= max_results:
                    break
    print(f"[INFO] Collected {len(results)} search results")
    return results

search_results = free_search_ddgs(topic)
if len(search_results) == 0:
    print("[ERROR] No search results found. Exiting...")
    exit()
print(f"[INFO] Top search result: {search_results[0]}")

# ----------------------------
# 3. Improved site + image selection
# ----------------------------
def normalize(text):
    # Remove punctuation and lowercase
    return text.translate(str.maketrans('', '', string.punctuation)).lower()

def select_site_and_images(topic, search_results, top_n=5):
    chosen_site = search_results[0]
    print(f"[INFO] Selected site: {chosen_site}")

    try:
        res = requests.get(chosen_site, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Select main content
        content_div = soup.find(id="mw-content-text") or soup.body
        img_tags = content_div.find_all("img") if content_div else soup.find_all("img")
        print(f"[INFO] Found {len(img_tags)} images in main content")

        selected_images = []
        topic_keywords = [normalize(w) for w in topic.split()]

        for img in img_tags:
            src = img.get("src")
            alt = normalize(img.get("alt") or "")
            if not src:
                continue

            # Skip logos/icons/banners
            if re.search(r'logo|icon|banner|favicon|wiki|emblem|flag', src, re.I):
                continue

            # Normalize src for keyword matching
            src_lower = normalize(src)

            # Match keywords
            if any(k in alt or k in src_lower for k in topic_keywords):
                selected_images.append(urljoin(chosen_site, src))

        # Fallback: largest images by width*height or assume SVGs if no size
        if not selected_images:
            print("[INFO] No keyword-matched images, selecting largest content images as fallback")
            img_candidates = []
            for img in img_tags:
                src = img.get("src")
                if not src:
                    continue
                try:
                    width = int(img.get("width") or 0)
                    height = int(img.get("height") or 0)
                    area = width*height
                    # Include even SVGs if no size
                    if area == 0 and src.lower().endswith(".svg"):
                        area = 10000  # give them moderate priority
                    if area > 0:
                        img_candidates.append((area, urljoin(chosen_site, src)))
                except:
                    continue
            img_candidates.sort(reverse=True)
            selected_images = [x[1] for x in img_candidates[:top_n]]

        print(f"[INFO] {len(selected_images)} images selected")
        return chosen_site, selected_images
    except Exception as e:
        print(f"[ERROR] Site fetch failed: {e}")
        return chosen_site, []

site, images_to_download = select_site_and_images(topic, search_results, top_n=5)

# ----------------------------
# 4. Download images
# ----------------------------
os.makedirs("images", exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0"}

for idx, img_url in enumerate(images_to_download, start=1):
    try:
        print(f"[INFO] Downloading image: {img_url}")
        response = requests.get(img_url, headers=headers, timeout=15)
        if "image" not in response.headers.get("Content-Type", ""):
            print(f"[WARNING] Not an image: {img_url}")
            continue
        filename = os.path.join("images", f"{idx}_{os.path.basename(img_url)}")
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"[INFO] Image saved: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to download {img_url}: {e}")

# ----------------------------
# 5. Download site text
# ----------------------------
try:
    print(f"[INFO] Fetching site text from: {site}")
    response = requests.get(site, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove scripts, styles, nav, header, footer
    for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
        tag.decompose()

    text = soup.get_text(separator='\n')
    text_lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = '\n'.join(text_lines)

    with open("website_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("[INFO] Website text saved to website_text.txt")
except Exception as e:
    print(f"[ERROR] Failed to save text: {e}")

print("[DONE] Learning pack ready!")
