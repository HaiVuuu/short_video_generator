import os
import re
import csv
import json
import requests
import importlib.util

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TOPICS_CSV = os.path.join(BASE_DIR, "topics.example.csv")
HEADERS = {"User-Agent": "        "}
XXXXX_API = "         "


def load_topics():
    if not os.path.exists(TOPICS_CSV):
        return []
    with open(TOPICS_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if row.get("id")]


def story_dir(story_id):
    # Trả về đường dẫn thuần túy, tuyệt đối không tạo thư mục ở đây
    return os.path.join(OUTPUT_DIR, str(story_id).zfill(3))


def status_file(story_id):
    return os.path.join(story_dir(story_id), "status.json")


def load_status(story_id):
    sf = status_file(story_id)
    if os.path.exists(sf):
        try:
            with open(sf, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_status(story_id, step_name, status, error_msg=None):
    d = story_dir(story_id)
    os.makedirs(d, exist_ok=True)
    data = load_status(story_id)
    data[step_name] = {
        "status": status,
        "error": error_msg
    }
    with open(status_file(story_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def step_done(story_id, step_name):
    data = load_status(story_id)
    return data.get(step_name, {}).get("status") == "done"


def load_step_module(scripts_dir, filename):
    module_name = filename.replace(".py", "")
    module_path = os.path.join(scripts_dir, filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strip_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def is_archival_artwork(page_data, file_title):
    """
    Xác thực khách quan: 
    - Chặn bìa sách scan, nhãn barcode thư viện, mã xếp giá (NRLF...).
    - Chặn ảnh chụp live concert/sự kiện thực tế bên ngoài.
    - Giữ lại tranh vẽ, minh họa, bản in cổ, tranh khắc gỗ.
    """
    title_lower = file_title.lower()
    
    # 1. Chặn các file scan bìa, nhãn lưu kho thư viện
    cover_and_doc_junk = [
        "book_cover", "bookcover", "binding", "spine", "title_page",
        "barcode", "ex_libris", "catalogue", "page_1.", "page1.",
        "frontispiece", "nrlf", "uc-nrlf"
    ]
    if any(junk in title_lower for junk in cover_and_doc_junk):
        return False

    categories = [cat.get("title", "").lower() for cat in page_data.get("categories", [])]
    cat_blob = " ".join(categories)

    # 2. Chặn các sự kiện biểu diễn, ban nhạc, ảnh chụp thực tế
    negative_indicators = [
        "concert", "rock band", "musical group", "live performance", 
        "book covers", "library catalogs"
    ]
    if any(term in cat_blob for term in negative_indicators):
        return False

    # 3. Kiểm tra xem có chứa từ khóa hội họa, minh họa, tranh khắc hay không
    art_indicators = [
        "illustration", "engraving", "painting", "drawing", 
        "woodcut", "woodblock", "print", "fairy tale", "andersen", "art"
    ]
    has_art_cat = any(term in cat_blob for term in art_indicators)
    has_art_title = any(term in title_lower for term in art_indicators)

    # 4. Kiểm tra trường mô tả
    imageinfo = page_data.get("imageinfo", [{}])[0]
    meta = imageinfo.get("extmetadata", {})
    desc = meta.get("ImageDescription", {}).get("value", "").lower()

    if any(junk in desc for junk in ["book cover", "binding of", "library of congress", "barcode"]):
        return False

    return has_art_cat or has_art_title or ("art" in cat_blob)


def search_commons_file(file_title, image_width=1080):
    params = {
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo|categories",
        "iiprop": "url|extmetadata|mime|size",  # Lấy thêm width/height
        "iiurlwidth": image_width,
        "cllimit": 50,
        "format": "json",
    }
    try:
        r = requests.get(WIKIMEDIA_API, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            imageinfo = page.get("imageinfo")
            if not imageinfo:
                continue
            info = imageinfo[0]
            url = info.get("thumburl") or info.get("url")
            if not url:
                continue

            if not is_archival_artwork(page, file_title):
                continue

            meta = info.get("extmetadata", {})
            w = info.get("width", 0)
            h = info.get("height", 0)
            orientation = "Portrait (Đứng)" if h >= w else "Landscape (Ngang)"

            return {
                "url": url,
                "artist": strip_html(meta.get("Artist", {}).get("value", "")),
                "title": strip_html(meta.get("ObjectName", {}).get("value", "")) or file_title.replace("File:", ""),
                "description": strip_html(meta.get("ImageDescription", {}).get("value", "")),
                "license": strip_html(meta.get("LicenseShortName", {}).get("value", "")),
                "page_url": f"https://commons.wikimedia.org/wiki/{file_title.replace(' ', '_')}",
                "orientation": orientation,
                "dimensions": f"{w}x{h}"
            }
    except Exception:
        pass
    return None


def fetch_artwork_candidates(row, max_candidates=5, image_width=1080):
    """Tìm và gom tối đa max_candidates tác phẩm đạt chuẩn."""
    tale = row["tale"].strip()
    style = row.get("illustrator_style", "").strip()
    clean_tale = re.sub(r"[:\-\(\)].*$", "", tale).strip()
    clean_style = re.sub(r"(?i)painting|style|classical|miniature", "", style).strip()

    search_stages = []
    if clean_style:
        search_stages.append(f'"{clean_tale}" "{clean_style}"')
        search_stages.append(f"{clean_tale} {clean_style}")

    search_stages.extend([
        f'"{clean_tale}" illustration',
        f'"{clean_tale}" fairy tale',
        f"{clean_tale} drawing",
        f"{clean_tale} painting"
    ])

    candidates = []
    seen_titles = set()

    for query in search_stages:
        params = {
            "action": "query",
            "list": "search",
            "srnamespace": 6,
            "srsearch": f"{query} -cover -binding -band",
            "srlimit": 10,
            "format": "json",
        }
        try:
            r = requests.get(WIKIMEDIA_API, params=params, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            hits = r.json().get("query", {}).get("search", [])
            for hit in hits:
                title = hit["title"]
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                info = search_commons_file(title, image_width=image_width)
                if info:
                    candidates.append(info)
                    if len(candidates) >= max_candidates:
                        return candidates
        except Exception:
            continue

    return candidates


def execute_waterfall_search(row, image_width=1080):
    """
    Quy trình tìm kiếm phân tầng tự nhiên:
    - Bắt đầu từ Tên truyện + Tác giả / Phong cách
    - Nới lỏng dần qua minh họa, bản vẽ tranh cổ tích
    - Loại bỏ bìa sách và ban nhạc mà không chặn nhầm bản scan tranh
    """
    tale = row["tale"].strip()
    style = row.get("illustrator_style", "").strip()
    clean_tale = re.sub(r"[:\-\(\)].*$", "", tale).strip()
    clean_style = re.sub(r"(?i)painting|style|classical|miniature", "", style).strip()

    search_stages = []

    # Giai đoạn 1: Tên truyện + Nghệ sĩ chỉ định
    if clean_style:
        search_stages.append(f'"{clean_tale}" "{clean_style}"')
        search_stages.append(f"{clean_tale} {clean_style}")

    # Giai đoạn 2: Tìm kiếm minh họa nghệ thuật tự nhiên (bỏ chữ 'plate' gây hẹp kết quả)
    search_stages.append(f'"{clean_tale}" illustration')
    search_stages.append(f'"{clean_tale}" fairy tale')
    search_stages.append(f'"{clean_tale}" drawing')
    search_stages.append(f"{clean_tale} painting")
    search_stages.append(f"{clean_tale} engraving")

    for query in search_stages:
        params = {
            "action": "query",
            "list": "search",
            "srnamespace": 6,
            "srsearch": f"{query} -cover -binding -band",
            "srlimit": 10,
            "format": "json",
        }
        try:
            r = requests.get(WIKIMEDIA_API, params=params, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            hits = r.json().get("query", {}).get("search", [])
            for hit in hits:
                info = search_commons_file(hit["title"], image_width=image_width)
                if info:
                    return info
        except Exception:
            continue

    return None


def print_summary():
    print("\n=======================================================")
    print("PIPELINE EXECUTION SUMMARY")
    print("=======================================================")
    if not os.path.exists(OUTPUT_DIR):
        print("No output generated yet.")
        return
    for item in sorted(os.listdir(OUTPUT_DIR)):
        item_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(item_path):
            sf = os.path.join(item_path, "status.json")
            if os.path.exists(sf):
                try:
                    with open(sf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    print(f"Story {item}:")
                    for step, info in data.items():
                        st = info.get("status")
                        err = f" (Error: {info.get('error')})" if info.get("error") else ""
                        print(f"  - {step}: {st}{err}")
                except Exception:
                    pass
