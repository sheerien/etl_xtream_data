import streamlit as st
import requests
import json
import re
import csv
import io
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

# =================== Utils ===================

def normalize_host_from_any(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def parse_server_block(text: str):
    host = username = password = None
    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith("host"):
            host = normalize_host_from_any(line.split(":", 1)[1].strip())
        elif line.lower().startswith("username"):
            username = line.split(":", 1)[1].strip()
        elif line.lower().startswith("password"):
            password = line.split(":", 1)[1].strip()
    return host, username, password

def parse_xtream_url(url: str):
    try:
        parsed = urlparse(url)
        q = parse_qs(parsed.query)
        username = q.get("username", [None])[0]
        password = q.get("password", [None])[0]
        if not username or not password:
            st.warning("Xtream URL must contain username and password.")
            return None, None, None
        return f"{parsed.scheme}://{parsed.netloc}", username, password
    except Exception:
        st.warning("Invalid Xtream URL.")
        return None, None, None

def safe_filename(name: str):
    return re.sub(r"[^\w\-]+", "_", name.lower()).strip("_")

# =================== API ===================

@st.cache_data(ttl=600)
def fetch_categories(host, u, p, kind):
    action = "get_vod_categories" if kind == "movie" else "get_series_categories"
    try:
        r = requests.get(f"{host}/player_api.php", params={
            "username": u, "password": p, "action": action
        }, timeout=30)
        r.raise_for_status()
        return r.json() or []
    except Exception:
        return []

@st.cache_data(ttl=600)
def fetch_items(host, u, p, category_id, kind):
    action = "get_vod_streams" if kind == "movie" else "get_series"
    params = {"username": u, "password": p, "action": action}
    if category_id != "all":
        params["category_id"] = category_id
    try:
        r = requests.get(f"{host}/player_api.php", params=params, timeout=60)
        r.raise_for_status()
        return r.json() or []
    except Exception:
        return []

@st.cache_data(ttl=600)
def fetch_series_info(host, u, p, series_id):
    try:
        r = requests.get(f"{host}/player_api.php", params={
            "username": u, "password": p,
            "action": "get_series_info",
            "series_id": series_id
        }, timeout=60)
        r.raise_for_status()
        return r.json() or {}
    except Exception:
        return {}

# =================== Builders ===================

def build_movie_url(host, u, p, stream_id, ext):
    return f"{host}/movie/{u}/{p}/{stream_id}.{ext}"

def build_m3u(items):
    lines = ["#EXTM3U"]
    for i in items:
        lines.append(f"#EXTINF:-1,{i['name']}")
        lines.append(i["url"])
        lines.append("")
    return "\n".join(lines)

def build_series_m3u(episodes):
    lines = ["#EXTM3U"]
    for e in episodes:
        lines.append(f"#EXTINF:-{e['season']},{e['episode']}")
        lines.append(e["url"])
        lines.append("")
    return "\n".join(lines)

def build_csv(items):
    if not items:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=items[0].keys())
    writer.writeheader()
    writer.writerows(items)
    return buf.getvalue()

# =================== UI ===================

st.set_page_config("Xtream Tool", "🎬", layout="wide")
st.title("🎬 Xtream Movies & Series Tool")

# -------- Server Info --------
st.subheader("🔐 Server Info")

server_block = st.text_area(
    "Server Block",
    height=120,
    placeholder="Host: http://server:port\nUsername: xxx\nPassword: xxx",
)

xtream_url = st.text_input(
    "Xtream URL",
    placeholder="http://server:port/get.php?username=USER&password=PASS&type=m3u",
)

host = username = password = None

if xtream_url.strip():
    host, username, password = parse_xtream_url(xtream_url)
elif server_block.strip():
    host, username, password = parse_server_block(server_block)

if not all([host, username, password]):
    st.info("Please enter valid server information.")
    st.stop()

st.success(f"Connected to {host}")

# Pagination state for movies
if "movies_page" not in st.session_state:
    st.session_state.movies_page = 1

PAGE_SIZE = 50

tab_movies, tab_series = st.tabs(["🎬 Movies", "📺 Series"])

# =================== MOVIES ===================

with tab_movies:
    cats = fetch_categories(host, username, password, "movie")
    cat_map = {"All Movies": "all"}
    cat_map.update({c["category_name"]: c["category_id"] for c in cats})

    cat_name = st.selectbox("Movie Category", cat_map.keys())
    movies = fetch_items(host, username, password, cat_map[cat_name], "movie")

    normalized = [{
        "name": m["name"],
        "url": build_movie_url(
            host, username, password,
            m["stream_id"],
            m.get("container_extension", "mp4")
        )
    } for m in movies]

    total_movies = len(normalized)
    visible_count = min(st.session_state.movies_page * PAGE_SIZE, total_movies)
    page_items = normalized[:visible_count]

    st.markdown(
        f"""
**Total movies:** {total_movies}  
**Each M3U page contains:** {PAGE_SIZE} movies  
**Showing:** {visible_count} / {total_movies}
"""
    )

    preview_format = st.radio(
        "Preview Format",
        ["M3U", "JSON"],
        index=0,
        horizontal=True,
        key="movie_preview"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("⬇️ M3U", build_m3u(normalized), "movies.m3u")
    with col2:
        st.download_button("⬇️ CSV", build_csv(normalized), "movies.csv")
    with col3:
        st.download_button("⬇️ JSON", json.dumps(normalized, indent=2), "movies.json")

    if visible_count < total_movies:
        if st.button("➕ Load More Movies", key="load_more_movies"):
            st.session_state.movies_page += 1

    with st.expander("📄 Preview Movies", expanded=True):
        if preview_format == "M3U":
            st.code(build_m3u(page_items), language="text")
        else:
            st.code(json.dumps(page_items, indent=2), language="json")

# =================== SERIES ===================

with tab_series:
    cats = fetch_categories(host, username, password, "series")
    cat_map = {"All Series": "all"}
    cat_map.update({c["category_name"]: c["category_id"] for c in cats})

    cat_name = st.selectbox("Series Category", cat_map.keys())
    series_list = fetch_items(host, username, password, cat_map[cat_name], "series")
    series_map = {s["name"]: s["series_id"] for s in series_list}

    series_name = st.selectbox("Select Series", series_map.keys())
    info = fetch_series_info(host, username, password, series_map[series_name])

    raw_eps = info.get("episodes", {})
    seasons = defaultdict(list)

    for season, eps in raw_eps.items():
        for idx, ep in enumerate(eps, 1):
            seasons[int(season)].append({
                "season": int(season),
                "episode": idx,
                "url": f"{host}/series/{username}/{password}/{ep['id']}.{ep.get('container_extension','mp4')}"
            })

    st.markdown(
        f"""
**Total seasons:** {len(seasons)}  
**Total episodes:** {sum(len(v) for v in seasons.values())}
"""
    )

    preview_format = st.radio(
        "Preview Format",
        ["M3U", "JSON"],
        index=0,
        horizontal=True,
        key="series_preview"
    )

    for season_num, eps in seasons.items():
        with st.expander(f"Season {season_num} ({len(eps)} episodes)", expanded=False):
            col1, col2, col3 = st.columns(3)
            fname = safe_filename(f"{series_name}_S{season_num}")

            with col1:
                st.download_button("⬇️ M3U", build_series_m3u(eps), f"{fname}.m3u")
            with col2:
                st.download_button("⬇️ CSV", build_csv(eps), f"{fname}.csv")
            with col3:
                st.download_button("⬇️ JSON", json.dumps(eps, indent=2), f"{fname}.json")

            if preview_format == "M3U":
                st.code(build_series_m3u(eps), language="text")
            else:
                st.code(json.dumps(eps, indent=2), language="json")
