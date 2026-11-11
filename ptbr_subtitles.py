"""Smart PT-BR / PT Stremio subtitle aggregator with release sync & episode fallback."""

from concurrent.futures import ThreadPoolExecutor
import io
import os
import re
import time
import urllib.parse
import zipfile

from fastapi import Response
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SUBDL_API_KEY = os.environ.get("SUBDL_API_KEY", "jjvG0ydzEIhEZ8nv5aMSq6a4K1x41-t1")
OSV3_BASE = "https://opensubtitles-v3.strem.io"
OSV3_PLUS_BASE = "https://opensubtitles.stremio.homes/pt-br|pt-pt/ai-translated=true|from=all|auto-adjustment=true"
CINEMETA_BASE = "https://v3-cinemeta.strem.io"
ANIZIP_BASE = "https://api.ani.zip"

PTBR_SUB_MANIFEST = {
    "id": "community.ptbr.smart.subs",
    "version": "1.0.0",
    "name": "🎬 Legendas PT-BR Sync",
    "description": (
        "Legendas PT-BR e PT sincronizadas por hash, qualidade e release "
        "(OpenSubtitles V3+, OpenSubtitles V3 e SubDL), sem CAM/TS no topo e "
        "com fallback automático para temporadas divididas."
    ),
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/256px-Flag_of_Brazil.svg.png",
    "resources": [
        {
            "name": "subtitles",
            "types": ["movie", "series", "anime"],
            "idPrefixes": ["tt", "kitsu"],
        }
    ],
    "types": ["movie", "series", "anime"],
    "idPrefixes": ["tt", "kitsu"],
    "catalogs": [],
}

_SOURCE_FAMILIES = {
    "bluray": ("bluray", "blu-ray", "bdrip", "brrip", "remux", "uhd"),
    "webdl": ("web-dl", "webdl", "amzn", "nf", "netflix", "dsnp", "hulu", "atvp", "hmax"),
    "webrip": ("webrip", "web-rip", "hdrip"),
    "hdtv": ("hdtv", "pdtv", "dvdrip"),
}
_CAM_RE = re.compile(r"\b(cam|cam-?rip|hdcam|hd-?ts|telesync|telecine|tsrip|screener|dvdscr)\b", re.I)
_FORCED_RE = re.compile(r"(for[çc]ad[ao]|forced|sdh[\s._-]*only|signs[\s._-]*only)", re.I)
_RES_RE = re.compile(r"\b(2160p|1080p|720p|480p|4k)\b", re.I)
_CODEC_RE = re.compile(r"\b(x264|x265|hevc|h\.?264|h\.?265|av1|xvid)\b", re.I)
_GROUP_RE = re.compile(r"-([a-z0-9]{2,16})(?:\.[a-z0-9]{2,4})?$", re.I)
_STOP_WORDS = {
    "1080p", "2160p", "720p", "480p", "4k", "x264", "x265", "hevc", "h264",
    "h265", "aac", "aac5", "ac3", "eac3", "ddp5", "ddp", "truehd", "atmos",
    "dts", "hdr", "hdr10", "dv", "10bit", "multi", "dual", "dublado", "legendado",
    "bluray", "remux", "web", "webdl", "webrip", "amzn", "nf", "mkv", "mp4",
    "srt", "vtt", "ass", "pt", "br", "ptbr", "pob", "por", "portuguese",
    "yts", "yify", "gg", "bz",
}

_meta_cache = {}
_kitsu_cache = {}
_srt_cache = {}
_CACHE_TTL_SEC = 6 * 3600
_SRT_TTL_SEC = 3600
_SRT_CACHE_MAX = 128


def build_public_base_url(request):
    """Resolve HTTPS public base URL cleanly behind reverse proxies like Render."""
    if request is None:
        return "https://anitsu-stremio-addon.onrender.com"
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    if host:
        if "onrender.com" in host:
            proto = "https"
        return f"{proto}://{host}".rstrip("/")
    return str(request.base_url).rstrip("/")


def _normalize_lang(raw_lang, lang_code=""):
    """Normalize provider language names/codes into Stremio ISO 639-2 codes."""
    val = f"{raw_lang or ''} {lang_code or ''}".lower()
    if any(tok in val for tok in ("pob", "pt-br", "br_pt", "brazil", "brasil")):
        return "pob"
    if any(tok in val for tok in ("por", "pt-pt", "portugu", "pt")):
        return "por"
    return "pob"


def _parse_extra(extra_str):
    """Parse Stremio path extra parameters (`filename=...&videoHash=...&videoSize=...`)."""
    if not extra_str:
        return "", "", ""
    parsed = urllib.parse.parse_qs(extra_str.lstrip("/"), keep_blank_values=False)
    filename = (parsed.get("filename") or [""])[0]
    video_hash = (parsed.get("videoHash") or [""])[0]
    video_size = (parsed.get("videoSize") or [""])[0]
    return filename, video_hash, video_size


def _resolve_kitsu_to_imdb(kitsu_id):
    """Map Kitsu ID to IMDb ID using Ani.Zip with TTL caching."""
    now = time.time()
    cached = _kitsu_cache.get(kitsu_id)
    if cached and (now - cached[0]) < _CACHE_TTL_SEC:
        return cached[1]
    imdb_id = ""
    try:
        r = requests.get(f"{ANIZIP_BASE}/mappings?kitsu_id={kitsu_id}", headers={"User-Agent": UA}, timeout=3.5)
        if r.status_code == 200:
            imdb_id = r.json().get("mappings", {}).get("imdb_id") or ""
    except Exception:
        pass
    if imdb_id:
        _kitsu_cache[kitsu_id] = (now, imdb_id)
    return imdb_id


def _parse_video_id(type_, video_id):
    """Return `(imdb_id, season, episode, is_movie, raw_kitsu_id)`."""
    vid = urllib.parse.unquote(video_id or "")
    parts = vid.split(":")
    imdb_id = ""
    season = None
    episode = None
    kitsu_raw = ""

    if parts[0] == "kitsu" and len(parts) >= 2:
        kitsu_raw = vid
        imdb_id = _resolve_kitsu_to_imdb(parts[1])
        if len(parts) >= 3 and parts[2].isdigit():
            season = 1
            episode = int(parts[2])
    elif parts[0].startswith("tt"):
        imdb_id = parts[0]
        if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
            season = int(parts[1])
            episode = int(parts[2])

    is_movie = type_ == "movie" or (season is None and episode is None)
    return imdb_id, season, episode, is_movie, kitsu_raw


def _fetch_osv3_plus(type_, query_id, extra_part):
    """Fetch PT-BR / PT subtitles from OpenSubtitles V3+ (release names & hash sync)."""
    if not query_id:
        return []
    vid_enc = urllib.parse.quote(query_id, safe=":")
    url = f"{OSV3_PLUS_BASE}/subtitles/{type_}/{vid_enc}{extra_part}.json"
    out = []
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=4.2)
        if r.status_code != 200:
            return []
        for idx, s in enumerate(r.json().get("subtitles", [])):
            sub_url = s.get("url") or ""
            if sub_url.startswith("/"):
                sub_url = urllib.parse.urljoin("https://opensubtitles.stremio.homes", sub_url)
            if not sub_url.startswith("http"):
                continue
            raw_id = str(s.get("id") or "")
            sub_id = str(s.get("sub_id") or "")
            if not sub_id and "|" in raw_id:
                parts = raw_id.split("|")
                if len(parts) >= 2 and parts[1].isdigit():
                    sub_id = parts[1]
            release = raw_id.split("|", 2)[2] if raw_id.count("|") >= 2 else raw_id
            lang = _normalize_lang(s.get("lang"), s.get("lang_code"))
            out.append({
                "source": "osv3_plus",
                "idx": idx,
                "sub_id": sub_id,
                "release": release,
                "lang": lang,
                "url": sub_url,
                "ai_translated": bool(s.get("ai_translated")),
                "from_trusted": bool(s.get("from_trusted")),
            })
    except Exception:
        pass
    return out


def _fetch_osv3_legacy(type_, query_id, extra_part):
    """Fetch strictly PT-BR / PT subtitles from OpenSubtitles v3 (catches anime/hash gaps)."""
    if not query_id:
        return []
    vid_enc = urllib.parse.quote(query_id, safe=":")
    url = f"{OSV3_BASE}/subtitles/{type_}/{vid_enc}{extra_part}.json"
    out = []
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=4.2)
        if r.status_code != 200:
            return []
        pt_idx = 0
        for s in r.json().get("subtitles", []):
            raw_lang = str(s.get("lang") or "").lower()
            if raw_lang not in ("pob", "por", "pt-br", "pt"):
                continue
            sub_url = s.get("url") or ""
            if not sub_url.startswith("http"):
                continue
            sub_id = str(s.get("id") or "")
            lang = "pob" if raw_lang in ("pob", "pt-br") else "por"
            out.append({
                "source": "osv3",
                "idx": pt_idx,
                "sub_id": sub_id,
                "release": f"OpenSubtitles-{sub_id}",
                "lang": lang,
                "url": sub_url,
                "ai_translated": False,
                "from_trusted": False,
            })
            pt_idx += 1
    except Exception:
        pass
    return out


def _fetch_subdl(imdb_id, season, episode, is_movie, public_base_url):
    """Fetch PT-BR / PT subtitles from SubDL API and point to clean UTF-8 unzip proxy."""
    if not imdb_id or not SUBDL_API_KEY:
        return []
    params = {
        "api_key": SUBDL_API_KEY,
        "imdb_id": imdb_id,
        "languages": "BR_PT,PT",
    }
    if not is_movie and season is not None and episode is not None:
        params["season_number"] = str(season)
        params["episode_number"] = str(episode)
    out = []
    try:
        r = requests.get("https://api.subdl.com/api/v1/subtitles", params=params, headers={"User-Agent": UA}, timeout=4.2)
        if r.status_code != 200:
            return []
        data = r.json()
        if not data.get("status"):
            return []
        for idx, s in enumerate(data.get("subtitles", [])):
            raw_url = str(s.get("url") or "")
            zip_path = raw_url.split("?")[0]
            if not re.match(r"^/subtitle/[A-Za-z0-9_.\-/]+\.zip$", zip_path):
                continue
            lang = _normalize_lang(s.get("lang"), s.get("language"))
            release = s.get("release_name") or s.get("name") or f"SubDL-{idx}"
            if s.get("hi"):
                release = f"{release} [HI]"
            q = {"u": zip_path}
            if episode is not None:
                q["ep"] = str(episode)
            proxy_url = f"{public_base_url}/ptbr-subs/subdl-srt?{urllib.parse.urlencode(q)}"
            out.append({
                "source": "subdl",
                "idx": idx,
                "sub_id": f"subdl:{zip_path}",
                "release": release,
                "lang": lang,
                "url": proxy_url,
                "ai_translated": "ai" in str(s.get("author") or "").lower(),
                "from_trusted": False,
            })
    except Exception:
        pass
    return out


def _get_cinemeta_series_episodes(imdb_id):
    """Fetch Cinemeta episode list sorted by `(season, episode)` with caching."""
    now = time.time()
    cached = _meta_cache.get(imdb_id)
    if cached and (now - cached[0]) < _CACHE_TTL_SEC:
        return cached[1]
    eps = []
    try:
        r = requests.get(f"{CINEMETA_BASE}/meta/series/{imdb_id}.json", headers={"User-Agent": UA}, timeout=3.5)
        if r.status_code == 200:
            raw_videos = r.json().get("meta", {}).get("videos", [])
            eps = [
                v for v in raw_videos
                if isinstance(v.get("season"), int) and isinstance(v.get("episode"), int) and v["season"] >= 1
            ]
            eps.sort(key=lambda v: (v["season"], v["episode"]))
    except Exception:
        pass
    if eps:
        _meta_cache[imdb_id] = (now, eps)
    return eps


def _resolve_cinemeta_split_episode(imdb_id, season, episode):
    """Map TMDB multi-part season numbering (e.g., Lupin S1E7 -> S2E2) via Cinemeta."""
    eps = _get_cinemeta_series_episodes(imdb_id)
    if not eps:
        return None, None
    season_eps = [v for v in eps if v["season"] == season]
    # If the requested episode doesn't exist in Cinemeta's season N, locate its global ordinal.
    if not any(v["episode"] == episode for v in season_eps):
        before_season = [v for v in eps if v["season"] < season]
        global_idx = len(before_season) + episode - 1
        if 0 <= global_idx < len(eps):
            target = eps[global_idx]
            return target["season"], target["episode"]
    return None, None


def _source_family(text):
    low = (text or "").lower()
    for fam, markers in _SOURCE_FAMILIES.items():
        if any(m in low for m in markers):
            return fam
    return ""


def _release_group(text):
    clean = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", (text or "").strip())
    m = _GROUP_RE.search(clean)
    if m and len(m.group(1)) >= 2:
        grp = m.group(1).lower()
        if grp not in _STOP_WORDS and grp not in ("srt", "vtt", "ass", "forced", "forcada", "forçada"):
            return grp
    return ""


def _meaningful_tokens(text):
    tokens = set(re.findall(r"[a-z0-9]{3,}", (text or "").lower()))
    return {t for t in tokens if t not in _STOP_WORDS and not t.isdigit()}


def _score_candidate(cand, stream_filename, has_hash_signal):
    """Score candidate subtitle so the best release/hash-synced PT-BR sub ranks #1."""
    rel = cand.get("release") or ""
    score = 1000 if cand["lang"] == "pob" else 0
    stream_cam = bool(_CAM_RE.search(stream_filename or ""))
    sub_cam = bool(_CAM_RE.search(rel))

    if sub_cam and not stream_cam:
        score -= 2500
    if _FORCED_RE.search(rel):
        score -= 1800

    # Hash/release priority from OpenSubtitles providers (pos 0 is strongest match).
    idx = cand.get("idx", 10)
    if cand["source"] in ("osv3_plus", "osv3"):
        score += max(0, 160 - idx * 25)
        if has_hash_signal and idx == 0:
            score += 260
    elif cand["source"] == "subdl":
        score += max(0, 80 - idx * 15)

    if stream_filename and rel and cand["source"] != "osv3":
        s_fam = _source_family(stream_filename)
        r_fam = _source_family(rel)
        if s_fam and r_fam:
            if s_fam == r_fam:
                score += 220
            elif {s_fam, r_fam} & {"bluray"} and {s_fam, r_fam} & {"webdl", "webrip", "hdtv"}:
                score -= 160

        s_grp = _release_group(stream_filename)
        r_grp = _release_group(rel)
        if s_grp and r_grp and s_grp == r_grp:
            score += 360

        s_res = {m.lower() for m in _RES_RE.findall(stream_filename)}
        r_res = {m.lower() for m in _RES_RE.findall(rel)}
        if s_res and r_res and (s_res & r_res):
            score += 80

        s_cod = {m.lower().replace(".", "") for m in _CODEC_RE.findall(stream_filename)}
        r_cod = {m.lower().replace(".", "") for m in _CODEC_RE.findall(rel)}
        if s_cod and r_cod and (s_cod & r_cod):
            score += 40

        overlap = len(_meaningful_tokens(stream_filename) & _meaningful_tokens(rel))
        score += min(overlap, 5) * 45

    if not cand.get("ai_translated"):
        score += 45
    if cand.get("from_trusted"):
        score += 35
    if cand["source"] == "osv3_plus":
        score += 20

    return score


def _collect_for_target(type_, os_type, query_id, imdb_id, season, episode, is_movie, extra_part, public_base_url, kitsu_id=""):
    """Fetch PT-BR / PT subtitles concurrently across providers for one canonical ID."""
    with ThreadPoolExecutor(max_workers=4) as pool:
        fut_v3p = pool.submit(_fetch_osv3_plus, os_type, query_id or kitsu_id, extra_part)
        fut_v3 = pool.submit(_fetch_osv3_legacy, os_type, query_id, extra_part)
        fut_subdl = pool.submit(_fetch_subdl, imdb_id, season, episode, is_movie, public_base_url)
        fut_v3p_kitsu = (
            pool.submit(_fetch_osv3_plus, os_type, kitsu_id, extra_part)
            if kitsu_id and query_id and kitsu_id != query_id
            else None
        )

        candidates = []
        candidates.extend(fut_v3p.result())
        candidates.extend(fut_v3.result())
        candidates.extend(fut_subdl.result())
        if fut_v3p_kitsu is not None:
            candidates.extend(fut_v3p_kitsu.result())
    return candidates


def _build_extra_part(filename, video_hash, video_size):
    """Build URL-safe Stremio extra path suffix from parsed parameters."""
    params = {}
    if video_hash:
        params["videoHash"] = video_hash
    if video_size:
        params["videoSize"] = video_size
    if filename:
        params["filename"] = filename
    if not params:
        return ""
    return "/" + urllib.parse.urlencode(params)


def get_ptbr_subtitles(type_, video_id, extra="", public_base_url="https://anitsu-stremio-addon.onrender.com"):
    """Aggregate, deduplicate, and rank PT-BR / PT subtitles for Stremio."""
    filename, video_hash, video_size = _parse_extra(extra)
    imdb_id, season, episode, is_movie, kitsu_raw = _parse_video_id(type_, video_id)
    os_type = "movie" if is_movie else "series"

    if imdb_id and not is_movie and season is not None and episode is not None:
        query_id = f"{imdb_id}:{season}:{episode}"
    else:
        query_id = imdb_id

    extra_part = _build_extra_part(filename, video_hash, video_size)
    candidates = _collect_for_target(
        type_, os_type, query_id, imdb_id, season, episode, is_movie, extra_part, public_base_url, kitsu_id=kitsu_raw
    )

    # Fallback for split-part shows where TMDB/AIOMetadata season numbering differs from IMDb/OpenSubtitles (e.g., Lupin).
    usable = [c for c in candidates if not _FORCED_RE.search(c.get("release") or "")]
    if not usable and not is_movie and imdb_id and season is not None and episode is not None:
        alt_season, alt_ep = _resolve_cinemeta_split_episode(imdb_id, season, episode)
        if alt_season is not None and alt_ep is not None:
            alt_qid = f"{imdb_id}:{alt_season}:{alt_ep}"
            candidates.extend(
                _collect_for_target(
                    type_, "series", alt_qid, imdb_id, alt_season, alt_ep, False, extra_part, public_base_url
                )
            )

    # Deduplicate by OpenSubtitles numeric sub_id (preferring OpenSubtitles V3+ over V3 legacy) and URL.
    dedup = {}
    for c in candidates:
        key = c["sub_id"] or c["url"]
        prev = dedup.get(key)
        if prev is None or (c["source"] == "osv3_plus" and prev["source"] != "osv3_plus"):
            dedup[key] = c

    has_hash_signal = bool(video_hash or filename)
    ranked = sorted(dedup.values(), key=lambda c: _score_candidate(c, filename, has_hash_signal), reverse=True)

    subtitles = []
    seen_ids = set()
    for idx, c in enumerate(ranked[:20]):
        prefix = {"osv3_plus": "OSv3+", "osv3": "OSv3", "subdl": "SubDL"}.get(c["source"], "SUB")
        lang_tag = "BR" if c["lang"] == "pob" else "PT"
        rel_clean = (c.get("release") or "").strip()[:58]
        label = f"[{prefix} {lang_tag}] {rel_clean}" if rel_clean else f"[{prefix} {lang_tag}] #{idx+1}"
        if label in seen_ids:
            label = f"{label} ({idx+1})"
        seen_ids.add(label)
        subtitles.append({
            "id": label,
            "url": c["url"],
            "lang": c["lang"],
        })
    return subtitles


def _decode_subtitle_bytes(raw_bytes):
    """Decode SRT/VTT/ASS bytes cleanly as UTF-8, falling back to CP1252/Latin-1."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def _pick_zip_entry(names, episode=None):
    """Choose the best subtitle file inside a SubDL archive, matching episode if season pack."""
    sub_files = [n for n in names if n.lower().endswith((".srt", ".vtt", ".ass")) and "__MACOSX" not in n]
    if not sub_files:
        return None
    if len(sub_files) > 1 and episode is not None:
        ep_pat = re.compile(rf"(?:e0?{episode}\b|[ex]0?{episode}\b|\b0?{episode}\b)", re.I)
        matched = [n for n in sub_files if ep_pat.search(n)]
        if matched:
            sub_files = matched
    sub_files.sort(key=lambda n: (0 if n.lower().endswith(".srt") else 1, len(n)))
    return sub_files[0]


def fetch_subdl_srt_response(zip_path, ep=None):
    """Download, unzip, normalize to UTF-8, and return a SubDL subtitle safely."""
    if not zip_path or not re.match(r"^/subtitle/[A-Za-z0-9_.\-/]+\.zip$", zip_path):
        return Response(content="Invalid subtitle path", status_code=400)
    if not SUBDL_API_KEY:
        return Response(content="Missing SubDL API key", status_code=503)

    cache_key = f"{zip_path}:{ep or ''}"
    now = time.time()
    cached = _srt_cache.get(cache_key)
    if cached and (now - cached[0]) < _SRT_TTL_SEC:
        return Response(content=cached[1], media_type="text/plain; charset=utf-8", headers={"Access-Control-Allow-Origin": "*"})

    dl_url = f"https://dl.subdl.com{zip_path}?api_key={urllib.parse.quote(SUBDL_API_KEY)}"
    try:
        r = requests.get(dl_url, headers={"User-Agent": UA}, timeout=8.0)
        if r.status_code != 200 or not r.content:
            return Response(content="Subtitle unavailable", status_code=404)
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            chosen = _pick_zip_entry(zf.namelist(), episode=ep)
            if not chosen:
                return Response(content="No subtitle file in archive", status_code=404)
            text = _decode_subtitle_bytes(zf.read(chosen))
        if len(_srt_cache) >= _SRT_CACHE_MAX:
            _srt_cache.clear()
        _srt_cache[cache_key] = (now, text)
        return Response(
            content=text,
            media_type="text/plain; charset=utf-8",
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=3600"},
        )
    except Exception:
        return Response(content="Failed to unpack subtitle", status_code=502)
