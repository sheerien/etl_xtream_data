# Xtream Movies & Series Tool (Streamlit)

A simple Streamlit web tool to fetch movies and series from an Xtream Codes API server and export them as M3u, CSV, or JSON. This tool allows you to connect to an Xtream server using either a full Xtream URL or a server block, browse movie categories and export the movie list, browse series categories and export episodes per season, export results in M3u/CSV/JSON, preview results inside the app, and use pagination for movies.

## Features
- Connect using Xtream URL or Server Block
- Fetch and export Movies list by category
- Fetch and export Series list by category
- Fetch episodes per season for selected series
- Export formats: M3u, CSV, JSON
- Preview results inside the app
- Pagination for movies
- Cached API responses for 10 minutes for faster performance

## Requirements
- Python 3.10+
- Streamlit
- Requests

## Install dependencies
```bash
pip install streamlit requests
```

### Run the App

- Place the code in a file named app.py (or any name you want) then run:

```bash
streamlit run app.py
```

### How to Connect
Option A — Xtream URL

Enter a valid Xtream URL like:
http://server:port/get.php?username=USER&password=PASS&type=m3u
The app automatically extracts host, username, and password.

Option B — Server Block

Paste a server block like:

```bash
Host: http://server:port
Username: USER
Password: PASS
```

### Movies Tab

Select a movie category. The tool fetches movies from that category. You can export the result as M3u, CSV, or JSON. Preview the output inside the app. Click “Load More Movies” to paginate.

Movies Output Example (M3u)

```bash
#EXTM3U
#EXTINF:-1,Movie Name
http://host/movie/username/password/stream_id.mp4
```

### Series Tab

Select a series category. Select a series name. The tool fetches seasons and episodes. For each season you can export M3u, CSV, or JSON. Preview the output inside the app.

Series Output Example (M3u)

```bash
#EXTM3U
#EXTINF:-1,Episode Name
http://host/series/username/password/episode_id.mp4
```

### Code Structure

Utilities: parse_xtream_url(), parse_server_block(), normalize_host_from_any(), safe_filename()
API Functions: fetch_categories(), fetch_items(), fetch_series_info()
Builders: build_movie_url(), build_m3u(), build_series_m3u(), build_csv()

Notes

Cached responses expire after 10 minutes.
If the server returns invalid data, the app returns empty results.
Movie pagination uses a page size of 50 items.

License

Add your preferred license file (MIT / GPL / Apache / etc.)

Future Improvements

Add support for live TV streams, filtering by language/quality/year, better error handling and UI notifications, export of full metadata (duration, rating, plot, poster, etc.).
