from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import re
import time
import base64
import urllib.request
import urllib.parse
import threading
import requests

app = FastAPI(title="Anitsu Cloud & Filler Addon for Stremio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
SUPABASE_URL = 'https://auth.anitsu.moe'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzkxNzMwNDI5LCJleHAiOjE5NDk0MTA0Mjl9.vVKdnGvA4q4lZyZlLzQeO7qjc3J8kUlfnEke495fgjU'

TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'token_cache.json')
CATALOG_FILE = os.path.join(os.path.dirname(__file__), 'catalog_min.json')

DEFAULT_FALLBACK_TOKEN = '7t3e26zdcgtj'
DEFAULT_INITIAL_COOKIE = os.getenv('ANITSU_COOKIE', 'sb-auth-auth-token.0=base64-eyJhY2Nlc3NfdG9rZW4iOiAiZXlKaGJHY2lPaUpGVXpJMU5pSXNJbXRwWkNJNkltTmlPV1EwWkRreUxUbGpPV1V0TkROak1TMWhNekJqTFRobFkyVmlOamN5TW1ObE9DSXNJblI1Y0NJNklrcFhWQ0o5LmV5SnBjM01pT2lKb2RIUndjem92TDJGMWRHZ3VZVzVwZEhOMUxtMXZaUzloZFhSb0wzWXhJaXdpYzNWaUlqb2lOR1JqTXpNMFkyUXRZamxoTkMwME56RTNMVGhtWm1VdFlqQTJZbUkyTWpjelpERTNJaXdpWVhWa0lqb2lZWFYwYUdWdWRHbGpZWFJsWkNJc0ltVjRjQ0k2TVRjNU5ETXpOamMzT1N3aWFXRjBJam94TnprME16TXpNVGM1TENKbGJXRnBiQ0k2SW1Wa2RXRnlaRzloYm1SbGNuTnZialF6UUdkdFlXbHNMbU52YlNJc0luQm9iMjVsSWpvaUlpd2lZWEJ3WDIxbGRHRmtZWFJoSWpwN0ltMWxiV0psY2lJNmRISjFaU3dpY0hKdmRtbGtaWElpT2lKbGJXRnBiQ0lzSW5CeWIzWnBaR1Z5Y3lJNld5SmxiV0ZwYkNJc0ltUnBjMk52Y21RaVhYMHNJblZ6WlhKZmJXVjBZV1JoZEdFaU9uc2lZWFpoZEdGeUlqb2lJaXdpWVhaaGRHRnlYM1Z5YkNJNkltaDBkSEJ6T2k4dlkyUnVMbVJwYzJOdmNtUmhjSEF1WTI5dEwyRjJZWFJoY25Ndk1qazJNRGs0TkRFd016VTRPRGs0TmprNUwyVTBPV1JrWWpZelpEbGpPV1pqWVRnMFpHVTBZekUzTnpkbVl6QmhZemRtTG5CdVp5SXNJbU4xYzNSdmJWOWpiR0ZwYlhNaU9uc2laMnh2WW1Gc1gyNWhiV1VpT2lKQmJtUmxjbk52YmlKOUxDSmxiV0ZwYkNJNkltVmtkV0Z5Wkc5aGJtUmxjbk52YmpRelFHZHRZV2xzTG1OdmJTSXNJbVZ0WVdsc1gzWmxjbWxtYVdWa0lqcDBjblZsTENKbWRXeHNYMjVoYldVaU9pSmhibVJsY25OdmJqQXdNREVpTENKcGMzTWlPaUpvZEhSd2N6b3ZMMlJwYzJOdmNtUXVZMjl0TDJGd2FTSXNJbTVoYldVaU9pSmhibVJsY25OdmJqQXdNREVqTUNJc0luQm9iMjVsWDNabGNtbG1hV1ZrSWpwbVlXeHpaU3dpY0dsamRIVnlaU0k2SW1oMGRIQnpPaTh2WTJSdUxtUnBjMk52Y21SaGNIQXVZMjl0TDJGMllYUmhjbk12TWprMk1EazROREV3TXpVNE9EazROams1TDJVME9XUmtZall6WkRsak9XWmpZVGcwWkdVMFl6RTNOemRtWXpCaFl6ZG1MbkJ1WnlJc0luQnliM1pwWkdWeVgybGtJam9pTWprMk1EazROREV3TXpVNE9EazROams1SWl3aWMzVmlJam9pTWprMk1EazROREV3TXpVNE9EazROams1SWl3aWRYTmxjbTVoYldVaU9pSkJibVJsY25OdmJqUXpNVE1pZlN3aWNtOXNaU0k2SW1GMWRHaGxiblJwWTJGMFpXUWlMQ0poWVd3aU9pSmhZV3d4SWl3aVlXMXlJanBiZXlKdFpYUm9iMlFpT2lKdllYVjBhQ0lzSW5ScGJXVnpkR0Z0Y0NJNk1UYzVOREU1T0RJNE5YMWRMQ0p6WlhOemFXOXVYMmxrSWpvaU1EWTJNRE14TUdVdFpUWTBOaTAwWkdRMkxUa3dZV1F0WkRJeE5HVTNOemN3TjJZMklpd2lhWE5mWVc1dmJubHRiM1Z6SWpwbVlXeHpaWDAuVUJBbUdSVWZxR21CalBIbERnRk5waGl3ZHFBVnJVRG8zVy1YUkRMaml0bEVXemtOQlFpLU9PdF85X1QwN0pIUDBkeVhCV3lTMTJDSnJsLTQ1bHNIY2ciLCAidG9rZW5fdHlwZSI6ICJiZWFyZXIiLCAiZXhwaXJlc19pbiI6IDM2MDAsICJleHBpcmVzX2F0IjogMTc5NDMzNjc3OSwgInJlZnJlc2hfdG9rZW4iOiAiN3QzZTI2emRjZ3RqIiwgInVzZXIiOiB7ImlkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJhdWQiOiAiYXV0aGVudGljYXRlZCIsICJyb2xlIjogImF1dGhlbnRpY2F0ZWQiLCAiZW1haWwiOiAiZWR1YXJkb2FuZGVyc29uNDNAZ21haWwuY29tIiwgImVtYWlsX2NvbmZpcm1lZF9hdCI6ICIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4NjcxNVoiLCAicGhvbmUiOiAiIiwgImNvbmZpcm1lZF9hdCI6ICIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4NjcxNVoiLCAibGFzdF9zaWduX2luX2F0IjogIjIwMjYtMTEtMTBUMDI6MDg6MjUuNTIxMzkxWiIsICJhcHBfbWV0YWRhdGEiOiB7Im1lbWJlciI6IHRydWUsICJwcm92aWRlciI6ICJlbWFpbCIsICJwcm92aWRlcnMiOiBbImVtYWlsIiwgImRpc2NvcmQiXX0sICJ1c2VyX21ldGFkYXRhIjogeyJhdmF0YXIiOiAiIiwgImF2YXRhcl91cmwiOiAiaHR0cHM6Ly9jZG4uZGlzY29yZGFwcC5jb20vYXZhdGFycy8yOTYwOTg0MTAzNTg4OTg2OTkvZTQ5ZGRiNjNkOWM5ZmNhODRkZTRjMTc3N2ZjMGFjN2YucG5nIiwgImN1c3RvbV9jbGFpbXMiOiB7Imdsb2JhbF9uYW1lIjogIkFuZGVyc29uIn0sICJlbWFpbCI6ICJlZHVhcmRvYW5kZXJzb240M0BnbWFpbC5jb20iLCAiZW1haWxfdmVyaWZpZWQiOiB0cnVlL; sb-auth-auth-token.1=CAiZnVsbF9uYW1lIjogImFuZGVyc29uMDAwMSIsICJpc3MiOiAiaHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkiLCAibmFtZSI6ICJhbmRlcnNvbjAwMDEjMCIsICJwaG9uZV92ZXJpZmllZCI6IGZhbHNlLCAicGljdHVyZSI6ICJodHRwczovL2Nkbi5kaXNjb3JkYXBwLmNvbS9hdmF0YXJzLzI5NjA5ODQxMDM1ODg5ODY5OS9lNDlkZGI2M2Q5YzlmY2E4NGRlNGMxNzc3ZmMwYWM3Zi5wbmciLCAicHJvdmlkZXJfaWQiOiAiMjk2MDk4NDEwMzU4ODk4Njk5IiwgInN1YiI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcm5hbWUiOiAiQW5kZXJzb240MzEzIn0sICJpZGVudGl0aWVzIjogW3siaWRlbnRpdHlfaWQiOiAiZWFjNTEzMDQtOGMxMC00ZDdhLWIxMjUtNzk2ZDRhYWRiZDdlIiwgImlkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJ1c2VyX2lkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJpZGVudGl0eV9kYXRhIjogeyJlbWFpbCI6ICJlZHVhcmRvYW5kZXJzb240M0BnbWFpbC5jb20iLCAiZW1haWxfdmVyaWZpZWQiOiBmYWxzZSwgInBob25lX3ZlcmlmaWVkIjogZmFsc2UsICJzdWIiOiAiNGRjMzM0Y2QtYjlhNC00NzE3LThmZmUtYjA2YmI2MjczZDE3In0sICJwcm92aWRlciI6ICJlbWFpbCIsICJsYXN0X3NpZ25faW5fYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODUzNzRaIiwgImNyZWF0ZWRfYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODU0MjNaIiwgInVwZGF0ZWRfYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODU0MjNaIiwgImVtYWlsIjogImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSJ9LCB7ImlkZW50aXR5X2lkIjogIjdmMTJjOTY2LWU4OWItNDZkYy04MjY5LWY2NDllYWUxZWE0YSIsICJpZCI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcl9pZCI6ICI0ZGMzMzRjZC1iOWE0LTQ3MTctOGZmZS1iMDZiYjYyNzNkMTciLCAiaWRlbnRpdHlfZGF0YSI6IHsiYXZhdGFyX3VybCI6ICJodHRwczovL2Nkbi5kaXNjb3JkYXBwLmNvbS9hdmF0YXJzLzI5NjA5ODQxMDM1ODg5ODY5OS9lNDlkZGI2M2Q5YzlmY2E4NGRlNGMxNzc3ZmMwYWM3Zi5wbmciLCAiY3VzdG9tX2NsYWltcyI6IHsiZ2xvYmFsX25hbWUiOiAiQW5kZXJzb24ifSwgImVtYWlsIjogImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSIsICJlbWFpbF92ZXJpZmllZCI6IHRydWUsICJmdWxsX25hbWUiOiAiYW5kZXJzb24wMDAxIiwgImlzcyI6ICJodHRwczovL2Rpc2NvcmQuY29tL2FwaSIsICJuYW1lIjogImFuZGVyc29uMDAwMSMwIiwgInBob25lX3ZlcmlmaWVkIjogZmFsc2UsICJwaWN0dXJlIjogImh0dHBzOi8vY2RuLmRpc2NvcmRhcHAuY29tL2F2YXRhcnMvMjk2MDk4NDEwMzU4ODk4Njk5L2U0OWRkYjYzZDljOWZjYTg0ZGU0YzE3NzdmYzBhYzdmLnBuZyIsICJwcm92aWRlcl9pZCI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAic3ViIjogIjI5NjA5ODQxMDM1ODg5ODY5OSJ9LCAicHJvdmlkZXIiOiAiZGlzY29yZCIsICJsYXN0X3NpZ25faW5fYXQiOiAiMjAyNC0xMC0yMFQyMDoxNTo1MS42MjU1MzNaIiwgImNyZWF0ZWRfYXQiOiAiMjAyNC0xMC0yMFQyMDoxNTo1MS42MjU1OTJaIiwgInVwZGF0ZWRfYXQiOiAiMjAyNi0xMS0xMFQwMjowODoyNC44MzU3NTZaIiwgImVtYWlsIjogImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSJ9XSwgImNyZWF0ZWRfYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODMxODlaIiwgInVwZGF0ZWRfYXQiOiAiMjAyNi0xMS0xMFQxNzo1MDo1NC4wMzc3NjJaIiwgImlzX2Fub255bW91cyI6IGZhbHNlfX0=')
refresh_token = ''
current_cookie = DEFAULT_INITIAL_COOKIE
cookie_lock = threading.Lock()

animes_list = []
title_index = {}
tmdb_index = {}
cache_files = {}
cache_filler = {}
cache_name = {}

ONE_PIECE_OFFSETS = {
    1: 0, 2: 8, 3: 30, 4: 47, 5: 60, 6: 69, 7: 91, 8: 130, 9: 143,
    10: 195, 11: 226, 12: 325, 13: 381, 14: 481, 15: 516, 16: 578,
    17: 627, 18: 745, 19: 778, 20: 876, 21: 891, 22: 1084, 23: 1154
}

def norm(text):
    if not text:
        return ''
    t = text.lower()
    t = re.sub(r'[\(\)\[\]\{\}\:\"\'\-\_\.\,\!\?]', ' ', t)
    return ' '.join(t.split())

def is_cookie_expired(cookie_str, buffer_seconds=300):
    if not cookie_str:
        return True
    try:
        chunk_map = {}
        for part in cookie_str.split(';'):
            part = part.strip()
            if '=' in part:
                k, v = part.split('=', 1)
                if 'auth-token' in k:
                    chunk_map[k.split('.')[-1]] = v
        if not chunk_map:
            return True
        raw_b64 = ''.join(chunk_map[str(i)] for i in range(len(chunk_map)) if str(i) in chunk_map)
        if raw_b64.startswith('base64-'):
            raw_b64 = raw_b64[7:]
        raw_b64 += '=' * (-len(raw_b64) % 4)
        sess = json.loads(base64.b64decode(raw_b64).decode('utf-8'))
        exp = sess.get('expires_at')
        if not exp:
            return True
        return time.time() >= (exp - buffer_seconds)
    except Exception:
        return True

def init_tokens():
    global refresh_token, current_cookie
    possible_cfgs = [
        r'C:\Users\eduar\Desktop\AniGUI-v3.4.1\anitsu_config.json',
        os.path.expanduser(r'~\Desktop\AniGUI-v3.4.1\anitsu_config.json'),
        r'F:\Games\AniGUI-v3.4.1\anitsu_config.json',
    ]
    for cfg_path in possible_cfgs:
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as fp:
                    cfg_d = json.load(fp)
                    live_ck = cfg_d.get('cookie')
                    if live_ck:
                        with cookie_lock:
                            current_cookie = live_ck
                        chunk_map = {}
                        for part in live_ck.split(';'):
                            part = part.strip()
                            if '=' in part:
                                k, v = part.split('=', 1)
                                if 'auth-token' in k:
                                    chunk_map[k.split('.')[-1]] = v
                        if chunk_map:
                            raw_b64 = ''.join(chunk_map[str(i)] for i in range(len(chunk_map)) if str(i) in chunk_map)
                            if raw_b64.startswith('base64-'):
                                raw_b64 = raw_b64[7:]
                            raw_b64 += '=' * (-len(raw_b64) % 4)
                            sess = json.loads(base64.b64decode(raw_b64).decode('utf-8'))
                            rf = sess.get('refresh_token')
                            if rf:
                                refresh_token = rf
                                print(f"[Anitsu Cloud] Extracted refresh_token from {cfg_path}: {rf[:6]}***")
                                if is_cookie_expired(current_cookie):
                                    refresh_session()
                                else:
                                    print(f"[Anitsu Cloud] Cookie is still valid. Skipping immediate refresh.")
                                return
            except Exception as e:
                print(f"[Anitsu Cloud] Error reading {cfg_path}:", e)

    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as fp:
                saved = json.load(fp).get('refresh_token')
                if saved:
                    refresh_token = saved
                    print(f"[Anitsu Cloud] Loaded refresh_token from local cache: {refresh_token[:6]}***")
                    if is_cookie_expired(current_cookie):
                        refresh_session()
                    return
        except Exception:
            pass
    refresh_token = os.getenv('ANITSU_REFRESH_TOKEN', DEFAULT_FALLBACK_TOKEN)
    print(f"[Anitsu Cloud] Using fallback refresh_token: {refresh_token[:6]}***")
    if is_cookie_expired(current_cookie):
        refresh_session()
GENERIC_WORDS = {'no', 'the', 'da', 'de', 'do', 'new', 'brand', 'season', 'movie', 'filme', 'part', 'arc', 'to', 'wa', 'ga', 'o', 'a', 'in', 'of', 'and', 's01', 's02', 's03', 's04', 's1', 's2', 'um', 'uma', 'dia', 'man'}
cache_title_resolution = {}
cache_subtitles = {}

def get_subtitles_for_media(video_id, title="", is_movie=False):
    cache_key = f"{video_id}:{is_movie}"
    if cache_key in cache_subtitles:
        return cache_subtitles[cache_key]

    parts = video_id.split(':')
    imdb_id = None
    season_num = 1
    ep_num = 1

    if video_id.startswith('tt'):
        imdb_id = parts[0]
        if len(parts) >= 3:
            season_num = int(parts[1])
            ep_num = int(parts[2])
        elif len(parts) == 2:
            season_num = 1
            ep_num = int(parts[1])
    elif video_id.startswith('kitsu') and len(parts) >= 2:
        kid = parts[1]
        ep_num = int(parts[2]) if len(parts) >= 3 else 1
        try:
            r = requests.get(f'https://api.ani.zip/mappings?kitsu_id={kid}', headers={'User-Agent': UA}, timeout=2.5)
            if r.status_code == 200:
                imdb_id = r.json().get('mappings', {}).get('imdb_id')
        except Exception:
            pass
    elif video_id.startswith('mal') and len(parts) >= 2:
        mal_id = parts[1]
        ep_num = int(parts[2]) if len(parts) >= 3 else 1
        try:
            r = requests.get(f'https://api.ani.zip/mappings?mal_id={mal_id}', headers={'User-Agent': UA}, timeout=2.5)
            if r.status_code == 200:
                imdb_id = r.json().get('mappings', {}).get('imdb_id')
        except Exception:
            pass

    if not imdb_id and title:
        try:
            prefer_t = "movie" if is_movie else "series"
            r = requests.get(f'https://v3-cinemeta.strem.io/catalog/{prefer_t}/top/search={urllib.parse.quote(title)}.json', headers={'User-Agent': UA}, timeout=2.0)
            if r.status_code == 200:
                metas = r.json().get('metas', [])
                if metas:
                    imdb_id = metas[0].get('id')
        except Exception:
            pass

    subs = []
    if imdb_id:
        # 1. LegendasBR
        try:
            if is_movie:
                url = f'https://legendas.legendasbr.site/subtitles/movie/{imdb_id}.json'
            else:
                url = f'https://legendas.legendasbr.site/subtitles/series/{imdb_id}%3A{season_num}%3A{ep_num}.json'
            r = requests.get(url, headers={'User-Agent': UA}, timeout=3.0)
            if r.status_code == 200:
                for s in r.json().get('subtitles', []):
                    subs.append({
                        'id': s.get('id', 'legbr-por'),
                        'url': s.get('url'),
                        'lang': 'por'
                    })
        except Exception:
            pass

        # 2. LegendasDivx
        try:
            if is_movie:
                ld_url = f'https://e1d6cc1ff4a7-legendasdivx-stremio.baby-beamup.club/%7B%22token%22%3A%22530373430363.5b9179f61f816aa0d70d79739098b0f0%22%2C%22langs%22%3A%22br%22%2C%22rips%22%3A0%2C%22pcks%22%3A1%7D/subtitles/movie/{imdb_id}.json'
            else:
                ld_url = f'https://e1d6cc1ff4a7-legendasdivx-stremio.baby-beamup.club/%7B%22token%22%3A%22530373430363.5b9179f61f816aa0d70d79739098b0f0%22%2C%22langs%22%3A%22br%22%2C%22rips%22%3A0%2C%22pcks%22%3A1%7D/subtitles/series/{imdb_id}%3A{season_num}%3A{ep_num}.json'
            r = requests.get(ld_url, headers={'User-Agent': UA}, timeout=2.5)
            if r.status_code == 200:
                for item in r.json().get('subtitles', []):
                    subs.append({
                        'id': item.get('id'),
                        'url': item.get('url'),
                        'lang': 'por'
                    })
        except Exception:
            pass

    if subs:
        cache_subtitles[cache_key] = subs
    return subs

def init_catalog():
    global animes_list, title_index, tmdb_index
    if os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            animes_list = json.load(f)
        idx = {}
        tmdb_map = {}
        for a in animes_list:
            n_clean = norm(a.get('n', ''))
            if n_clean and n_clean not in idx:
                idx[n_clean] = a
            for al in a.get('a', []):
                al_clean = norm(al)
                if al_clean and al_clean not in idx:
                    idx[al_clean] = a
            if a.get('tmdb'):
                tmdb_map[str(a['tmdb'])] = a
        title_index = idx
        tmdb_index = tmdb_map
        print(f"[Anitsu Cloud] Loaded {len(animes_list)} titles, indexed {len(title_index)} aliases.")

def refresh_session():
    global current_cookie, refresh_token
    if not refresh_token:
        return
    try:
        url = f'{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token'
        res = requests.post(
            url,
            json={'refresh_token': refresh_token},
            headers={'apikey': SUPABASE_ANON_KEY, 'Authorization': f'Bearer {SUPABASE_ANON_KEY}'},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            new_rf = data.get('refresh_token')
            if new_rf:
                refresh_token = new_rf
                try:
                    with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump({'refresh_token': new_rf, 'updated_at': time.time()}, f)
                except Exception:
                    pass
            sess_json = json.dumps(data)
            sess_b64 = 'base64-' + base64.b64encode(sess_json.encode('utf-8')).decode('utf-8')
            chunks = [sess_b64[i:i+3000] for i in range(0, len(sess_b64), 3000)]
            cookie_str = '; '.join([f'sb-auth-auth-token.{i}={c}' for i, c in enumerate(chunks)])
            with cookie_lock:
                current_cookie = cookie_str
            anitsu_cfg_path = r'C:\Users\eduar\Desktop\AniGUI-v3.4.1\anitsu_config.json'
            if os.path.exists(anitsu_cfg_path):
                try:
                    with open(anitsu_cfg_path, 'r', encoding='utf-8') as f:
                        cfg_d = json.load(f)
                    cfg_d['cookie'] = cookie_str
                    with open(anitsu_cfg_path, 'w', encoding='utf-8') as f:
                        json.dump(cfg_d, f, indent=2)
                except Exception:
                    pass
            print(f"[Anitsu Cloud] Session token refreshed! User: {data.get('user', {}).get('email')}")
        else:
            print(f"[Anitsu Cloud] Refresh returned {res.status_code}. Using current active cookie.")
    except Exception as e:
        print("[Anitsu Cloud] Error refreshing token:", e)

def refresh_worker():
    while True:
        time.sleep(900)
        if is_cookie_expired(current_cookie, buffer_seconds=900):
            refresh_session()

@app.on_event("startup")
def startup():
    init_tokens()
    init_catalog()
    if is_cookie_expired(current_cookie):
        refresh_session()
    t = threading.Thread(target=refresh_worker, daemon=True)
    t.start()

# --- Landing Page ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse(content=get_anitsu_manifest())

    host = request.headers.get("host", "localhost:8080")
    proto = request.headers.get("x-forwarded-proto", "http")
    base_url = f"{proto}://{host}"
    stremio_base = base_url.replace("https://", "").replace("http://", "")

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stremio Anime Cloud Addons</title>
    <link rel="icon" href="https://nuvem.anitsu.moe/icon.png">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background: #0f1015; color: #f0f2f5; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; max-width: 650px; }}
        .header h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #a855f7, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; }}
        .header p {{ color: #94a3b8; font-size: 1.05rem; line-height: 1.5; }}
        .status-badge {{ display: inline-flex; align-items: center; gap: 8px; background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; padding: 6px 14px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; margin-top: 15px; }}
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 10px #22c55e; }}
        
        .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; max-width: 800px; width: 100%; }}
        .card {{ background: #181924; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 24px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 10px 25px rgba(0,0,0,0.4); transition: transform 0.2s, border-color 0.2s; }}
        .card:hover {{ transform: translateY(-3px); border-color: rgba(168, 85, 247, 0.4); }}
        .card-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }}
        .card-icon {{ width: 48px; height: 48px; border-radius: 12px; object-fit: cover; background: #28293d; }}
        .card-title {{ font-size: 1.25rem; font-weight: 700; color: #fff; }}
        .card-desc {{ color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 24px; }}
        
        .btn {{ display: block; text-align: center; text-decoration: none; font-weight: 700; font-size: 1rem; padding: 12px 20px; border-radius: 10px; cursor: pointer; transition: all 0.2s; }}
        .btn-primary {{ background: linear-gradient(135deg, #7c3aed, #4f46e5); color: #fff; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.35); margin-bottom: 10px; }}
        .btn-primary:hover {{ opacity: 0.92; box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5); }}
        .btn-secondary {{ background: rgba(255, 255, 255, 0.06); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem; padding: 8px 14px; }}
        .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.12); color: #fff; }}
        
        .footer {{ margin-top: 50px; text-align: center; color: #64748b; font-size: 0.85rem; }}
        .toast {{ position: fixed; bottom: 20px; background: #22c55e; color: #000; font-weight: 700; padding: 10px 20px; border-radius: 8px; display: none; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Stremio Anime Cloud Addons</h1>
        <p>Servidores 24/7 de alta velocidade com reprodução instantânea para Android TV, Celular e PC.</p>
        <div class="status-badge">
            <span class="status-dot"></span>
            <span>Online & Conectado · {len(animes_list)} Títulos (Animes, Desenhos, Filmes e Doramas)</span>
        </div>
    </div>

    <div class="container">
        <!-- Card 1: Anitsu Nuvem -->
        <div class="card">
            <div>
                <div class="card-header">
                    <img src="https://nuvem.anitsu.moe/icon.png" class="card-icon" alt="Anitsu">
                    <div>
                        <div class="card-title">☁️ Anitsu Nuvem [PT-BR]</div>
                        <div style="font-size: 0.8rem; color: #a855f7;">Animes · Desenhos · Filmes · Doramas</div>
                    </div>
                </div>
                <div class="card-desc">
                    5.700+ Títulos em 1080p Fansub Dual com dublagens e legendas oficiais em português, transmitidos diretamente da nuvem sem torrents.
                </div>
            </div>
            <div>
                <a href="stremio://{stremio_base}/manifest.json" class="btn btn-primary">➕ Instalar no Stremio</a>
                <button class="btn btn-secondary" style="width: 100%;" onclick="copyManifest('{base_url}/manifest.json')">📋 Copiar Link do Manifesto</button>
            </div>
        </div>

        <!-- Card 2: Anime Filler Guide -->
        <div class="card">
            <div>
                <div class="card-header">
                    <img src="https://animefillerchecker.com/icon128.png" class="card-icon" alt="Filler Guide">
                    <div>
                        <div class="card-title">🛡️ Guia de Fillers</div>
                        <div style="font-size: 0.8rem; color: #38bdf8;">Anime Filler Guide</div>
                    </div>
                </div>
                <div class="card-desc">
                    Identifica na hora se cada episódio de animes longos (One Piece, Naruto, Bleach, etc.) é Cânon Oficial, Filler ou Misto diretamente na lista de opções.
                </div>
            </div>
            <div>
                <a href="stremio://{stremio_base}/filler/manifest.json" class="btn btn-primary">➕ Instalar no Stremio</a>
                <button class="btn btn-secondary" style="width: 100%;" onclick="copyManifest('{base_url}/filler/manifest.json')">📋 Copiar Link do Manifesto</button>
            </div>
        </div>
    </div>

    <div class="footer">
        Deploy 24/7 Ativo no Render · OmniRoute Stremio Cloud Addon
    </div>

    <div id="toast" class="toast">Link copiado com sucesso!</div>

    <script>
        function copyManifest(url) {{
            navigator.clipboard.writeText(url).then(function() {{
                var t = document.getElementById('toast');
                t.style.display = 'block';
                setTimeout(function() {{ t.style.display = 'none'; }}, 2500);
            }});
        }}
    </script>
</body>
</html>"""
    return html_content

def find_anime_by_title(title):
    if not title:
        return None
    cleaned = norm(title)
    if cleaned in title_index:
        return title_index[cleaned]

    cleaned_no_movie = re.sub(r'\b(the movie|movie|filme|season \d+|s\d+)\b', '', cleaned).strip()
    if cleaned_no_movie and cleaned_no_movie in title_index:
        return title_index[cleaned_no_movie]

    cleaned_words = cleaned.split()
    cleaned_tokens = set(cleaned_words)
    sig_query = cleaned_tokens - GENERIC_WORDS

    # 1. Regex full phrase / word boundary match
    best_match = None
    best_len = 0
    for alias, anime in title_index.items():
        if len(alias) < 4:
            continue
        alias_words = alias.split()
        if len(alias_words) == 1 and len(cleaned_words) > 1:
            continue
        if re.search(r'\b' + re.escape(alias) + r'\b', cleaned):
            if len(alias) > best_len:
                best_len = len(alias)
                best_match = anime
        elif len(cleaned_words) >= 2 and re.search(r'\b' + re.escape(cleaned) + r'\b', alias):
            if len(cleaned) > best_len:
                best_len = len(cleaned)
                best_match = anime

    if best_match:
        return best_match

    # 2. Token overlap with strict significant token ratio
    if not sig_query:
        return None

    min_required_sig = max(2, int(0.75 * len(sig_query))) if len(sig_query) >= 2 else 1

    best_score = 0
    for alias, anime in title_index.items():
        alias_tokens = set(alias.split())
        sig_alias = alias_tokens - GENERIC_WORDS
        if not sig_alias:
            continue
        common_sig = sig_query.intersection(sig_alias)
        if len(common_sig) < min_required_sig:
            continue

        alias_ratio = len(common_sig) / len(sig_alias)
        query_ratio = len(common_sig) / len(sig_query)
        if query_ratio >= 0.7 or (alias_ratio >= 0.7 and len(common_sig) >= 2):
            score = len(common_sig) * 10 + len(cleaned_tokens.intersection(alias_tokens))
            if score > best_score:
                best_score = score
                best_match = anime

    return best_match

def anitsu_list_files(path):
    if path in cache_files:
        return cache_files[path]
    with cookie_lock:
        ck = current_cookie
    url = 'https://nuvem.anitsu.moe/api/files?path=' + urllib.parse.quote(path)
    headers = {'Cookie': ck, 'User-Agent': UA, 'Accept': '*/*'}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 401:
            refresh_session()
            with cookie_lock:
                ck = current_cookie
            headers['Cookie'] = ck
            r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            files = r.json().get('files', [])
            cache_files[path] = files
            return files
    except Exception:
        pass
    return []

def resolve_stremio_title(video_id, prefer_type="series"):
    parts = video_id.split(':')
    if parts[0].startswith('kitsu') and len(parts) >= 2:
        series_id = f"{parts[0]}:{parts[1]}"
        kid = parts[1]
    elif parts[0].startswith('mal') and len(parts) >= 2:
        series_id = f"{parts[0]}:{parts[1]}"
        kid = None
    else:
        series_id = parts[0]
        kid = None

    cache_key = f"{prefer_type}:{series_id}"
    if cache_key in cache_title_resolution:
        return cache_title_resolution[cache_key]

    resolved_title = None
    if kid:
        try:
            r = requests.get(f'https://kitsu.io/api/edge/anime/{kid}', headers={'User-Agent': UA}, timeout=3.0)
            if r.status_code == 200:
                attrs = r.json().get('data', {}).get('attributes', {})
                resolved_title = attrs.get('canonicalTitle') or attrs.get('titles', {}).get('en') or attrs.get('titles', {}).get('en_jp')
        except Exception:
            pass
    elif series_id.startswith('mal') and len(parts) >= 2:
        mal_id = parts[1]
        try:
            r = requests.get(f'https://api.ani.zip/mappings?mal_id={mal_id}', headers={'User-Agent': UA}, timeout=3.0)
            if r.status_code == 200:
                imdb_id = r.json().get('mappings', {}).get('imdb_id')
                if imdb_id:
                    r2 = requests.get(f'https://v3-cinemeta.strem.io/meta/{prefer_type}/{imdb_id}.json', headers={'User-Agent': UA}, timeout=2.0)
                    if r2.status_code == 200:
                        resolved_title = r2.json().get('meta', {}).get('name')
        except Exception:
            pass
    elif series_id.startswith('tt'):
        endpoints = [f'https://v3-cinemeta.strem.io/meta/{prefer_type}/{series_id}.json']
        alt_type = "movie" if prefer_type == "series" else "series"
        endpoints.append(f'https://v3-cinemeta.strem.io/meta/{alt_type}/{series_id}.json')
        for ep in endpoints:
            try:
                r = requests.get(ep, headers={'User-Agent': UA}, timeout=2.0)
                if r.status_code == 200:
                    name = r.json().get('meta', {}).get('name')
                    if name:
                        resolved_title = name
                        break
            except Exception:
                pass

    if resolved_title:
        cache_title_resolution[cache_key] = resolved_title
    return resolved_title

def extract_episode_from_filename(fn):
    # Strip CRC32/hashes in [] or () first to prevent matching hex inside checksums
    fn_clean = re.sub(r'[\(\[][0-9a-fA-F]{8}[\)\]]', ' ', fn)

    # 1. Standard SxxExx (e.g. S01E02, s1e2)
    m = re.search(r'(?i)\b[sS]\d+\s*[-_ ]?\s*[eE]0*(\d+)\b', fn_clean)
    if m:
        return int(m.group(1))

    # 2. Multi-episode range (e.g. 01-02, 001 e 002, 01a02, 01 to 02)
    m_rng = re.search(r'(?i)(?:^|[^\d])0*(\d{1,4})\s*(?:[-_]| e | a | to )\s*0*(\d{1,4})(?:[^\d]|$)', fn_clean)
    if m_rng:
        st, en = int(m_rng.group(1)), int(m_rng.group(2))
        if 1 <= st <= 2000 and 1 <= en <= 2000 and abs(en - st) <= 15:
            return (st, en)

    # 3. Chapter / Capitulo / Episode / Ep
    m = re.search(r'(?i)(?:^|[\s_\[\(\.\-])(?:chapter|capitulo|cap|episode|ep)[_\s.-]*0*(\d+)\b', fn_clean)
    if m:
        return int(m.group(1))

    # 4. Standard E01, Ep01 (not preceded by letters or digits)
    m = re.search(r'(?i)(?:^|[\s_\[\(\.\-])[eE]0*(\d+)\b', fn_clean)
    if m:
        return int(m.group(1))

    cleaned = fn_clean
    cleaned = re.sub(r'\b(19\d\d|20\d\d)\b', ' ', cleaned)
    cleaned = re.sub(r'(?i)\d{3,4}x\d{3,4}', ' ', cleaned)
    cleaned = re.sub(r'(?i)\b(2160p|1080p|1080i|720p|480p|576p|4k)\b', ' ', cleaned)
    cleaned = re.sub(r'(?i)(?:x264|x265|h264|h265|hevc|avc|10bit|8bit|hi10p)', ' ', cleaned)
    cleaned = re.sub(r'(?i)\b(ac3|aac|dvd|bd|flac|eac3|ddp?)\b', ' ', cleaned)
    cleaned = re.sub(r'\b\d+\.\d+\b', ' ', cleaned)
    cleaned = re.sub(r'(?i)\b(?:s|season|temporada)\s*0*\d+\b', ' ', cleaned)

    nums = re.findall(r'(?:^|[^\d])0*(\d{1,4})(?:[^\d]|$)', cleaned)
    if nums:
        return int(nums[0])
    return None

def find_all_episode_files(anime, season_num, ep_num, video_id=""):
    root_folder = f"{anime['p']}/{anime['n']}"
    is_movie = anime.get('t') == 'movie' or 'Filmes' in anime.get('p', '')

    target_eps = [ep_num]
    # Handle One Piece season-to-absolute mapping
    if 'one piece' in anime['n'].lower() or 'tt0388629' in video_id:
        if season_num > 1:
            base_offset = ONE_PIECE_OFFSETS.get(season_num, 0)
            abs_ep = base_offset + ep_num
            target_eps = [abs_ep, abs_ep + 1, abs_ep - 1]
        elif season_num == 1 and ep_num > 60:
            target_eps = [ep_num]

    found_releases = []

    def walk(folder, depth=0):
        if depth > 4:
            return
        files = anitsu_list_files(folder)
        if not files:
            return

        video_files = [f for f in files if not f.get('is_directory') and f.get('name', '').lower().endswith(('.mkv', '.mp4'))]
        if video_files:
            if is_movie:
                for vf in video_files:
                    found_releases.append((f"{folder}/{vf['name']}", vf))
                return

            for vf in video_files:
                name = vf['name']
                # Clean crc32 checksums like [16892632]
                name_clean = re.sub(r'\[[a-fA-F0-9]{8}\]', '', name)
                
                # Filter wrong seasons if file explicitly specifies S02 when we want S01
                s_file_match = re.search(r'\b(?:s|season)\s*0?(\d+)\b', name_clean.lower())
                if s_file_match and season_num <= 10 and 'one piece' not in anime['n'].lower():
                    if int(s_file_match.group(1)) != season_num:
                        continue

                ep_info = extract_episode_from_filename(name_clean)
                matched = False
                if isinstance(ep_info, int):
                    if ep_info in target_eps:
                        matched = True
                elif isinstance(ep_info, tuple):
                    st, en = ep_info
                    if any(st <= t_ep <= en for t_ep in target_eps):
                        matched = True

                if matched:
                    found_releases.append((f"{folder}/{name}", vf))
                    return # found in this folder

        subdirs = [f['name'] for f in files if f.get('is_directory')]
        for s in subdirs:
            s_lower = s.lower()
            if any(bad in s_lower for bad in ['filme', 'movie', 'live action', 'série', 'taose', 'especiais', 'especial', 'spin off', 'spin-off', 'extras', 'ova']):
                continue

            # Check season folder
            s_dir_match = re.search(r'\b(?:s|season|temporada)\s*0?(\d+)\b', s_lower)
            if s_dir_match and season_num <= 10 and 'one piece' not in anime['n'].lower():
                if int(s_dir_match.group(1)) != season_num:
                    continue

            # Check range folder e.g. [878-1088] or 01-130
            rng = re.findall(r'(\d+)[\s\-_]+(\d+)', s)
            in_range = False
            has_range = False
            for st_str, en_str in rng:
                st, en = int(st_str), int(en_str)
                if st > en: st, en = en, st
                if en >= 1900 and en <= 2030 and st >= 1900:
                    continue
                has_range = True
                for t_ep in target_eps:
                    if st <= t_ep <= en:
                        in_range = True
                        break
                if in_range:
                    break

            if has_range and not in_range:
                continue

            walk(f"{folder}/{s}", depth + 1)

    walk(root_folder, 0)

    # Sort releases: Hardsub & Fansubs with Notes prioritized, then 1080p BD & Dual
    def score_rel(item):
        p, vf = item
        n = vf.get('name', '').lower()
        pl = p.lower()
        score = 0
        is_hardsub = 'hardsub' in n or 'hardsub' in pl
        is_hacchi = 'hacchi' in pl or 'hacchi' in n
        if is_hardsub:
            score += 35 # High priority so complete Fansub Hardsub with notes & karaoke is always prominent!
        elif is_hacchi:
            score += 25
        if '1080' in n or '1080' in pl: score += 20
        if 'bluray' in n or 'bd' in n or 'bd' in pl: score += 15
        if 'dual' in n or 'dublado' in n or 'dual' in pl: score += 18
        if 'netflix' in pl or 'nf' in n: score += 12
        if 'opex' in pl: score += 10
        if 'cr' in pl or 'crunchyroll' in pl: score += 8
        if 'kyoshiro' in pl: score += 15
        if 'sennin' in pl: score += 14
        if '720' in n and not is_hardsub: score -= 10
        if ('480' in n or '576' in n) and not is_hardsub: score -= 20
        return score

    found_releases.sort(key=score_rel, reverse=True)
    return found_releases

def format_stream_card(anime, vf, remote_path, season_num, ep_num, is_movie=False, is_proxy=False):
    filename = vf.get('name', '')
    fn = filename.lower()
    pl = remote_path.lower()

    is_hardsub = 'hardsub' in fn or 'hardsub' in pl
    is_hacchi = 'hacchi' in pl or 'hacchi' in fn
    is_dual = ('dual' in fn or 'dublado' in fn or 'dual' in pl or 'dublado' in pl) and not is_hardsub

    # 1. Resolution & Left Badge
    if is_hardsub:
        res_tag = '1080P' if ('1080' in fn or '1080' in pl) else ('720P' if ('720' in fn or '720' in pl) else '480P')
        name = f"HARDSUB ⚡\n({res_tag} Fansub) ★★★"
    else:
        if '2160' in fn or '4k' in fn or '4k' in pl:
            res = '2160P ⚡'
        elif '1080' in fn or '1080' in pl:
            res = '1080P ⚡'
        elif '720' in fn or '720' in pl:
            res = '720P ⚡'
        elif '480' in fn or 'dvd' in fn or '576' in fn or 'dvd' in pl:
            res = '480P ⚡'
        else:
            res = '1080P ⚡'

        if 'remux' in fn or 'remux' in pl:
            src = '(Remux) ★★★'
        elif 'bluray' in fn or 'bd' in fn or 'bd' in pl:
            src = '(Bluray) ★★★'
        elif 'web' in fn or 'nf' in fn or 'netflix' in pl or 'cr' in pl or 'onegai' in pl:
            src = '(Web-dl) ★★★'
        elif 'hdtv' in fn or 'hdtv' in pl:
            src = '(Hdtv) ★★'
        elif 'dvd' in fn or 'dvd' in pl:
            src = '(Dvdrip) ★'
        else:
            src = '★★★'

        name = f"{res}\n{src}"

    # 2. Codec
    if 'hevc' in fn or 'x265' in fn or 'h265' in fn or 'h.265' in fn:
        codec = 'HEVC 10bit'
    elif 'avc' in fn or 'x264' in fn or 'h264' in fn or 'h.264' in fn:
        codec = 'AVC'
    else:
        codec = 'AVC'

    # 3. Audio & Channels
    if 'ddp' in fn:
        audio = '♫ DDP 5.1'
    elif '5.1' in fn:
        audio = '♫ DD 5.1'
    elif 'flac' in fn:
        audio = '♫ FLAC 2.0'
    elif 'aac' in fn:
        audio = '♫ AAC 2.0'
    else:
        audio = '♫ DD 2.0'

    if is_dual:
        audio += ' · Dual Áudio (Dublado PT-BR)'
    elif is_hardsub:
        audio += ' · Hardsub (Legenda Embutida)'
    else:
        audio += ' · Legendado PT-BR'

    # 4. Group / Release Name
    group_str = ""
    if 'netflix' in pl:
        group_str = " · Netflix"
    elif 'anime onegai' in pl or 'onegai' in pl:
        group_str = " · Anime Onegai"
    elif 'animensk' in pl or 'animensk' in fn:
        group_str = " · AnimeNSK"
    elif 'reiji' in pl or 'reiji' in fn:
        group_str = " · Reiji"
    elif 'opex' in pl:
        group_str = " · Opex"
    elif 'kyoshiro' in pl:
        group_str = " · Kyoshiro"
    elif 'sennin' in pl:
        group_str = " · Sennin"
    elif 'harlley' in pl:
        group_str = " · Harlley"
    elif 'mattmurdock' in pl:
        group_str = " · Mattmurdock"
    elif 'shakaw' in pl:
        group_str = " · ShaKaw"
    elif 'hacchi' in pl or 'hacchi' in fn:
        group_str = " · Hacchi Fansub"
    elif 'cr' in pl:
        group_str = " · Crunchyroll"
    else:
        m_grp = re.search(r'-([a-zA-Z0-9_]+)(?:\.[a-zA-Z0-9]+)?$', filename)
        if m_grp:
            group_str = f" · {m_grp.group(1)}"

    # 5. Clean Title
    clean_title = re.sub(r'\[[^\]]*\]', '', anime['n']).strip()
    clean_title = re.sub(r'\(\d{4}[^\)]*\)', '', clean_title).strip()

    # 6. Size
    size_bytes = vf.get('size', 0)
    size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
    if size_mb >= 1024:
        size_str = f"{size_mb/1024:.2f} GB"
    elif size_mb > 0:
        size_str = f"{int(size_mb)} MB"
    else:
        size_str = "HD"

    # 7. Cloud provider tag
    cloud_tag = "☁️ Nuvem Anitsu [Alta Velocidade 24/7]"

    # 8. Languages & Player flags
    if is_hardsub:
        lang_str = "✔ Legenda Fixa + Notas de Tradução & Karaokê"
    elif is_hacchi:
        lang_str = "✔ JA · Legendado Fansub (Com Notas de Tradução)"
    elif is_dual:
        lang_str = "✔ PT-BR (Dublado) · JA · SUB"
    else:
        lang_str = "✔ JA · Legendado PT-BR · SUB"
    player_str = "✔ EXOPLAYER SAFE"

    if is_hardsub:
        line1 = f"{clean_title} S{season_num:02d} E{ep_num:02d}{group_str} [Hardsub Completo]"
    elif is_movie:
        line1 = f"{clean_title} [Filme]{group_str}"
    else:
        line1 = f"{clean_title} S{season_num:02d} E{ep_num:02d}{group_str}"

    line2 = f"{codec} {audio}"
    line3 = f"⚡ {size_str} · {cloud_tag}"
    line4 = f"{lang_str} {player_str}"

    title = f"{line1}\n{line2}\n{line3}\n{line4}"
    return name, title

def get_anitsu_manifest():
    return {
        "id": "community.anitsu.cloud",
        "version": "1.3.0",
        "name": "☁️ Anitsu Nuvem [PT-BR]",
        "description": "5.800+ Animes, Filmes de Anime, Desenhos e Doramas em Fansub 1080p PT-BR direto da Nuvem Anitsu com múltiplas opções de releases e legendas integradas!",
        "logo": "https://nuvem.anitsu.moe/icon.png",
        "resources": ["catalog", "meta", "stream", "subtitles"],
        "types": ["anime", "series", "movie"],
        "idPrefixes": ["anitsu:", "kitsu", "tt", "mal"],
        "catalogs": [
            {
                "id": "anitsu-anime",
                "name": "☁️ Anitsu · Animes (PT-BR)",
                "type": "anime",
                "extra": [
                    {"name": "search", "isRequired": False},
                    {"name": "skip", "isRequired": False}
                ]
            },
            {
                "id": "anitsu-desenhos",
                "name": "🎨 Anitsu · Desenhos & Cartoons (PT-BR)",
                "type": "series",
                "extra": [
                    {"name": "search", "isRequired": False},
                    {"name": "skip", "isRequired": False}
                ]
            },
            {
                "id": "anitsu-filmes",
                "name": "🎬 Anitsu · Filmes de Animes & Animações (PT-BR)",
                "type": "movie",
                "extra": [
                    {"name": "search", "isRequired": False},
                    {"name": "skip", "isRequired": False}
                ]
            },
            {
                "id": "anitsu-doramas",
                "name": "🎭 Anitsu · Doramas Asiáticos (PT-BR)",
                "type": "series",
                "extra": [
                    {"name": "search", "isRequired": False},
                    {"name": "skip", "isRequired": False}
                ]
            }
        ]
    }

# --- Anitsu Addon Routes ---
@app.get("/manifest.json")
def manifest():
    return get_anitsu_manifest()

@app.get("/catalog/{type_}/{catalog_id}.json")
@app.get("/catalog/{type_}/{catalog_id}/search={search}.json")
def catalog(type_: str, catalog_id: str, search: str = "", skip: int = 0):
    if catalog_id == "anitsu-desenhos":
        filtered = [a for a in animes_list if a.get('c') == 'desenhos' and a.get('t') == 'series']
    elif catalog_id == "anitsu-filmes":
        filtered = [a for a in animes_list if a.get('t') == 'movie']
    elif catalog_id == "anitsu-doramas":
        filtered = [a for a in animes_list if a.get('c') == 'doramas']
    elif catalog_id == "anitsu-anime" or catalog_id == "anitsu-popular":
        filtered = [a for a in animes_list if a.get('c', 'anime') == 'anime']
    else:
        filtered = [a for a in animes_list if a.get('t', 'series') == type_ or a.get('c') == type_]

    if search:
        s = norm(search)
        filtered = [a for a in filtered if s in norm(a['n']) or any(s in al for al in a.get('a', []))]

    sliced = filtered[skip:skip+50]
    metas = []
    for a in sliced:
        stremio_type = "movie" if a.get('t') == 'movie' else ("anime" if a.get('c') == 'anime' else "series")
        cat_badge = "Anime" if a.get('c') == 'anime' else ("Desenho" if a.get('c') == 'desenhos' else "Dorama")
        metas.append({
            "id": f"anitsu:{a['id']}",
            "type": stremio_type,
            "name": a['n'],
            "poster": a.get('img') or "https://nuvem.anitsu.moe/icon.png",
            "description": f"Disponível na Nuvem Anitsu ({a['p']}) · 1080p Dual PT-BR",
            "genres": [cat_badge, "PT-BR"]
        })
    return {"metas": metas}

@app.get("/meta/{type_}/{video_id}.json")
def meta(type_: str, video_id: str):
    match = re.search(r'anitsu:(\d+)', video_id)
    if not match:
        return {"meta": {}}
    aid = int(match.group(1))
    anime = next((a for a in animes_list if a['id'] == aid), None)
    if not anime:
        return {"meta": {}}
    
    root_folder = f"{anime['p']}/{anime['n']}"
    files = anitsu_list_files(root_folder)
    videos = []
    is_movie = anime.get('t') == 'movie' or 'Filmes' in anime.get('p', '')

    if is_movie:
        videos.append({
            "id": f"anitsu:{aid}",
            "title": anime['n'],
            "released": "2024-01-01"
        })
    else:
        subdirs = [f['name'] for f in files if f.get('is_directory')]
        seasons_map = {}
        if subdirs:
            for sname in subdirs:
                s_lower = sname.lower()
                s_match = re.search(r'\b(?:s|season|temporada)\s*0?(\d+)\b', s_lower)
                s_num = int(s_match.group(1)) if s_match else 1
                if s_num not in seasons_map:
                    seasons_map[s_num] = set()
                s_files = anitsu_list_files(f"{root_folder}/{sname}")
                for vf in s_files:
                    if not vf.get('is_directory') and vf['name'].lower().endswith(('.mkv', '.mp4')):
                        ep = extract_episode_from_filename(vf['name'])
                        if isinstance(ep, int):
                            seasons_map[s_num].add(ep)
                        elif isinstance(ep, tuple):
                            for x in range(ep[0], ep[1]+1):
                                seasons_map[s_num].add(x)
        else:
            seasons_map[1] = set()
            for vf in files:
                if not vf.get('is_directory') and vf['name'].lower().endswith(('.mkv', '.mp4')):
                    ep = extract_episode_from_filename(vf['name'])
                    if isinstance(ep, int):
                        seasons_map[1].add(ep)
                    elif isinstance(ep, tuple):
                        for x in range(ep[0], ep[1]+1):
                            seasons_map[1].add(x)

        for s_num in sorted(seasons_map.keys()):
            eps = sorted(seasons_map[s_num])
            if not eps:
                eps = list(range(1, 13))
            for ep in eps:
                videos.append({
                    "id": f"anitsu:{aid}:{s_num}:{ep}",
                    "title": f"Episódio {ep}",
                    "season": s_num,
                    "episode": ep
                })

    stremio_type = "movie" if is_movie else ("anime" if anime.get('c') == 'anime' else "series")
    cat_badge = "Anime" if anime.get('c') == 'anime' else ("Desenho" if anime.get('c') == 'desenhos' else "Dorama")

    return {
        "meta": {
            "id": f"anitsu:{aid}",
            "type": stremio_type,
            "name": anime['n'],
            "poster": anime.get('img') or "https://nuvem.anitsu.moe/icon.png",
            "genres": [cat_badge, "PT-BR"],
            "videos": videos
        }
    }

def find_monogatari_streams(video_id, title, season_num, ep_num, base_url=""):
    base = "Animes/Letra M/Monogatari Series"
    t_lower = (title or '').lower()
    
    is_main_bake = 'bakemonogatari' in t_lower or 'tt1480925' in video_id or video_id.startswith('kitsu:4363') or video_id.startswith('mal:5081')
    target_folder = None
    target_ep = ep_num
    is_movie = False
    clean_title = "Bakemonogatari"

    if is_main_bake:
        if season_num == 1:
            target_folder = f"{base}/01. Bakemonogatari"
            target_ep = ep_num
        elif season_num == 2:
            clean_title = "Nisemonogatari"
            target_folder = f"{base}/03. Nisemonogatari"
            target_ep = ep_num
        elif season_num == 3:
            clean_title = "Monogatari Series: Second Season"
            if 1 <= ep_num <= 5:
                target_folder = f"{base}/05. Monogatari Series - Second Season/Arc 01： Nekomonogatari (Shiro)"
                target_ep = ep_num
            elif 6 <= ep_num <= 9:
                target_folder = f"{base}/05. Monogatari Series - Second Season/Arc 02： Kabukimonogatari"
                target_ep = ep_num - 5
            elif 10 <= ep_num <= 13:
                target_folder = f"{base}/05. Monogatari Series - Second Season/Arc 03： Otorimonogatari"
                target_ep = ep_num - 9
            elif 14 <= ep_num <= 17:
                target_folder = f"{base}/05. Monogatari Series - Second Season/Arc 04： Onimonogatari"
                target_ep = ep_num - 13
            elif 18 <= ep_num <= 23:
                target_folder = f"{base}/05. Monogatari Series - Second Season/Arc 05： Koimonogatari"
                target_ep = ep_num - 17
            else:
                target_folder = f"{base}/05. Monogatari Series - Second Season"
                target_ep = ep_num
        elif season_num == 4:
            clean_title = "Owarimonogatari"
            target_folder = f"{base}/09. Owarimonogatari"
            target_ep = ep_num
        elif season_num == 5:
            clean_title = "Owarimonogatari 2nd Season"
            target_folder = f"{base}/10. Owarimonogatari 2nd Season"
            target_ep = ep_num
        elif season_num == 6:
            clean_title = "Monogatari Series: Off & Monster Season"
            target_folder = f"{base}/12. Monogatari Series - Off & Monster Season"
            target_ep = ep_num
        elif season_num == 0:
            if ep_num == 2:
                clean_title = "Kizumonogatari I: Tekketsu-hen"
                target_folder = f"{base}/02. Kizumonogatari/Filme 1 "
                is_movie = True
            elif ep_num == 19:
                clean_title = "Kizumonogatari II: Nekketsu-hen"
                target_folder = f"{base}/02. Kizumonogatari/Filme 2"
                is_movie = True
            elif ep_num == 20:
                clean_title = "Kizumonogatari III: Reiketsu-hen"
                target_folder = f"{base}/02. Kizumonogatari/Filme 3"
                is_movie = True
            elif 3 <= ep_num <= 6:
                clean_title = "Nekomonogatari (Kuro)"
                target_folder = f"{base}/04. Nekomonogatari (Kuro)"
                target_ep = ep_num - 2
            elif 10 <= ep_num <= 14:
                clean_title = "Hanamonogatari"
                target_folder = f"{base}/06. Hanamonogatari"
                target_ep = ep_num - 9
            elif 15 <= ep_num <= 18:
                clean_title = "Tsukimonogatari"
                target_folder = f"{base}/07. Tsukimonogatari"
                target_ep = ep_num - 14
            elif 21 <= ep_num <= 32:
                clean_title = "Koyomimonogatari"
                target_folder = f"{base}/08. Koyomimonogatari"
                target_ep = ep_num - 20
            elif 33 <= ep_num <= 38:
                clean_title = "Zoku Owarimonogatari"
                target_folder = f"{base}/11. Zoku Owarimonogatari"
                target_ep = ep_num - 32
    else:
        clean_title = title or "Monogatari Series"
        if 'kizumonogatari' in t_lower:
            is_movie = True
            if 'ii' in t_lower or '2' in t_lower or 'nekketsu' in t_lower:
                clean_title = "Kizumonogatari II: Nekketsu-hen"
                target_folder = f"{base}/02. Kizumonogatari/Filme 2"
            elif 'iii' in t_lower or '3' in t_lower or 'reiketsu' in t_lower:
                clean_title = "Kizumonogatari III: Reiketsu-hen"
                target_folder = f"{base}/02. Kizumonogatari/Filme 3"
            else:
                clean_title = "Kizumonogatari I: Tekketsu-hen"
                target_folder = f"{base}/02. Kizumonogatari/Filme 1 "
        elif 'nisemonogatari' in t_lower:
            clean_title = "Nisemonogatari"
            target_folder = f"{base}/03. Nisemonogatari"
            target_ep = ep_num
        elif 'nekomonogatari' in t_lower:
            clean_title = "Nekomonogatari (Kuro)"
            target_folder = f"{base}/04. Nekomonogatari (Kuro)"
            target_ep = ep_num
        elif 'hanamonogatari' in t_lower:
            clean_title = "Hanamonogatari"
            target_folder = f"{base}/06. Hanamonogatari"
            target_ep = ep_num
        elif 'tsukimonogatari' in t_lower:
            clean_title = "Tsukimonogatari"
            target_folder = f"{base}/07. Tsukimonogatari"
            target_ep = ep_num
        elif 'koyomimonogatari' in t_lower:
            clean_title = "Koyomimonogatari"
            target_folder = f"{base}/08. Koyomimonogatari"
            target_ep = ep_num
        elif 'zoku owari' in t_lower:
            clean_title = "Zoku Owarimonogatari"
            target_folder = f"{base}/11. Zoku Owarimonogatari"
            target_ep = ep_num
        elif 'owarimonogatari' in t_lower:
            if season_num == 2 or '2nd' in t_lower or 'season 2' in t_lower:
                clean_title = "Owarimonogatari 2nd Season"
                target_folder = f"{base}/10. Owarimonogatari 2nd Season"
            else:
                clean_title = "Owarimonogatari"
                target_folder = f"{base}/09. Owarimonogatari"
            target_ep = ep_num

    if not target_folder:
        return []

    found = []
    def walk(curr, depth=0):
        if depth > 4: return
        files = anitsu_list_files(curr)
        if not files: return
        vfiles = [f for f in files if not f.get('is_directory') and f['name'].lower().endswith(('.mkv', '.mp4'))]
        if vfiles:
            for vf in vfiles:
                if is_movie:
                    found.append((f"{curr}/{vf['name']}", vf))
                else:
                    ep = extract_episode_from_filename(vf['name'])
                    if ep == target_ep or (isinstance(ep, tuple) and ep[0] <= target_ep <= ep[1]):
                        found.append((f"{curr}/{vf['name']}", vf))
            return
        for sf in files:
            if sf.get('is_directory'):
                walk(f"{curr}/{sf['name']}", depth + 1)

    walk(target_folder, 0)

    subs = get_subtitles_for_media(video_id, title=clean_title, is_movie=is_movie)
    cards = []
    dummy_anime = {'id': 28524, 'n': clean_title, 'p': base}
    for p, vf in found:
        name, title_card = format_stream_card(dummy_anime, vf, p, season_num, ep_num, is_movie=is_movie)
        stream_item = {
            "name": name,
            "title": title_card,
            "url": f"{base_url}/proxy-stream?path={urllib.parse.quote(p)}",
            "behaviorHints": {
                "notWebReady": False,
                "bingeGroup": f"anitsu-28524-{season_num}"
            }
        }
        if subs:
            stream_item["subtitles"] = subs
        cards.append(stream_item)
    return cards

@app.get("/stream/{type_}/{video_id}.json")
def stream(type_: str, video_id: str, request: Request = None):
    base_url = str(request.base_url).rstrip('/') if request else 'https://anitsu-stremio-addon.onrender.com'
    parts = video_id.split(':')
    matched_anime = None
    season_num = 1
    ep_num = 1
    is_movie = type_ == "movie" or (len(parts) == 1 and video_id.startswith('tt'))
    title = None

    if video_id.startswith('anitsu:'):
        aid = int(parts[1])
        matched_anime = next((a for a in animes_list if a['id'] == aid), None)
        if len(parts) >= 4:
            season_num = int(parts[2])
            ep_num = int(parts[3])
    elif video_id.startswith('kitsu'):
        prefer = "movie" if is_movie else "series"
        title = resolve_stremio_title(video_id, prefer_type=prefer)
        if title:
            matched_anime = find_anime_by_title(title)
        if len(parts) >= 4:
            season_num = int(parts[2])
            ep_num = int(parts[3])
        elif len(parts) >= 3:
            season_num = 1
            ep_num = int(parts[2])
        else:
            season_num = 1
            ep_num = 1
    elif video_id.startswith('mal'):
        prefer = "movie" if is_movie else "series"
        title = resolve_stremio_title(video_id, prefer_type=prefer)
        if title:
            matched_anime = find_anime_by_title(title)
        if len(parts) >= 4:
            season_num = int(parts[2])
            ep_num = int(parts[3])
        elif len(parts) >= 3:
            season_num = 1
            ep_num = int(parts[2])
        else:
            season_num = 1
            ep_num = 1
    elif video_id.startswith('tt'):
        prefer = "movie" if is_movie else "series"
        title = resolve_stremio_title(video_id, prefer_type=prefer)
        if title:
            matched_anime = find_anime_by_title(title)
        if len(parts) >= 3:
            season_num = int(parts[1])
            ep_num = int(parts[2])
        elif len(parts) == 2:
            season_num = 1
            ep_num = int(parts[1])

    title_check = (title or '').lower()
    if ('monogatari' in title_check or 'tt1480925' in video_id or video_id.startswith('kitsu:4363') or video_id.startswith('mal:5081')):
        m_streams = find_monogatari_streams(video_id, title or 'Bakemonogatari', season_num, ep_num, base_url=base_url)
        if m_streams:
            return {"streams": m_streams}

    if not matched_anime:
        return {"streams": []}

    if matched_anime.get('t') == 'movie':
        is_movie = True

    res_list = find_all_episode_files(matched_anime, season_num, ep_num, video_id=video_id)
    if not res_list:
        return {"streams": []}

    with cookie_lock:
        ck = current_cookie

    streams = []

    # Display best distinct releases, guaranteeing Hardsub is included
    chosen_releases = []
    hardsub_rel = next((r for r in res_list if 'hardsub' in r[0].lower() or 'hardsub' in r[1].get('name', '').lower()), None)
    for r in res_list:
        if r not in chosen_releases:
            chosen_releases.append(r)
        if len(chosen_releases) >= 5:
            break
    if hardsub_rel and hardsub_rel not in chosen_releases:
        chosen_releases.append(hardsub_rel)

    subs = get_subtitles_for_media(video_id, title=(matched_anime['n'] if matched_anime else ''), is_movie=is_movie)

    for r_idx, (remote_path, vf) in enumerate(chosen_releases):
        card_name, card_title = format_stream_card(
            matched_anime, vf, remote_path, season_num, ep_num, is_movie=is_movie, is_proxy=False
        )
        proxy_url = f"{base_url}/proxy-stream?path={urllib.parse.quote(remote_path)}"

        stream_entry = {
            "name": card_name,
            "title": card_title,
            "url": proxy_url,
            "behaviorHints": {
                "notWebReady": False,
                "bingeGroup": f"anitsu-{matched_anime['id']}-{r_idx}"
            }
        }
        if subs:
            stream_entry["subtitles"] = subs
        streams.append(stream_entry)

    return {"streams": streams}

@app.get("/subtitles/{type_}/{video_id}.json")
def subtitles(type_: str, video_id: str):
    is_movie = type_ == "movie"
    subs = get_subtitles_for_media(video_id, is_movie=is_movie)
    return {"subtitles": subs}

@app.get("/proxy-stream")
def proxy_stream(path: str, request: Request):
    with cookie_lock:
        ck = current_cookie
    anitsu_url = 'https://nuvem.anitsu.moe/api/download?path=' + urllib.parse.quote(path)
    headers = {'Cookie': ck, 'User-Agent': UA, 'Accept': '*/*'}
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header

    try:
        req = requests.get(anitsu_url, headers=headers, stream=True, timeout=15)
        if req.status_code == 401:
            refresh_session()
            with cookie_lock:
                ck = current_cookie
            headers['Cookie'] = ck
            req = requests.get(anitsu_url, headers=headers, stream=True, timeout=15)
    except Exception as e:
        return Response(status_code=502, content="Failed to connect to cloud storage")

    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
        'Accept-Ranges': 'bytes'
    }
    for h in ['Content-Type', 'Content-Length', 'Content-Range', 'Content-Disposition']:
        if h in req.headers:
            response_headers[h] = req.headers[h]

    def content_generator():
        try:
            for chunk in req.iter_content(chunk_size=131072):
                if chunk:
                    yield chunk
        finally:
            req.close()

    media_type = req.headers.get('Content-Type', 'video/mp4')
    return StreamingResponse(
        content_generator(),
        status_code=req.status_code,
        headers=response_headers,
        media_type=media_type
    )

# --- Filler Guide Addon Routes ---
KNOWN_SLUGS = {
    'tt0988824': 'naruto-shippuden', 'tt0409591': 'naruto', 'tt0388629': 'one-piece',
    'tt0434665': 'bleach', 'tt14946658': 'bleach-thousand-year-blood-war',
    'tt0131179': 'detective-conan', 'tt2098220': 'hunter-x-hunter-2011',
    'tt0112159': 'rurouni-kenshin', 'tt0106179': 'yu-yu-hakusho', 'tt5626028': 'black-clover',
    'tt6342474': 'boruto-naruto-next-generations', 'tt0280249': 'dragon-ball-z',
    'tt0988818': 'gintama', 'tt0423731': 'samurai-champloo', 'tt1856014': 'fairy-tail', 'tt2560140': 'attack-on-titan',
    'tt4263482': 'my-hero-academia', 'tt12343534': 'jujutsu-kaisen', 'tt10855794': 'demon-slayer-kimetsu-no-yaiba'
}

def get_filler_data(slug):
    if slug in cache_filler:
        return cache_filler[slug]
    try:
        r = requests.get(f'https://www.animefillerlist.com/shows/{slug}', headers={'User-Agent': UA}, timeout=6)
        if r.status_code == 200:
            episodes = {}
            rows = re.findall(r'<tr class="([^"]*)" id="eps-(\d+)"><td class="Number">(\d+)</td><td class="Title"><a[^>]*>([^<]+)</a></td><td class="Type"><span>([^<]+)</span>', r.text)
            for r_class, eps_id, num_str, title, ep_type in rows:
                num = int(num_str)
                ep_type_clean = ep_type.strip().lower()
                v = 'canon' if 'manga canon' in ep_type_clean else ('anime_canon' if 'anime canon' in ep_type_clean else ('mixed' if 'mixed' in ep_type_clean else ('filler' if 'filler' in ep_type_clean else 'unknown')))
                episodes[num] = {'number': num, 'title': title.strip(), 'type': v, 'raw_type': ep_type.strip()}
            if episodes:
                cache_filler[slug] = episodes
                return episodes
    except Exception:
        pass
    return None

@app.get("/filler/manifest.json")
def filler_manifest():
    return {
        "id": "community.animefiller.cloud",
        "version": "1.0.0",
        "name": "Guia de Fillers em Animes",
        "description": "Identifica episódios Cânon, Filler e Mistos em animes longos direto na lista de reprodução.",
        "logo": "https://animefillerchecker.com/icon128.png",
        "resources": ["stream"],
        "types": ["series", "anime"],
        "idPrefixes": ["tt", "kitsu"]
    }

@app.get("/filler/stream/{type_}/{video_id}.json")
def filler_stream(type_: str, video_id: str):
    parts = video_id.split(':')
    if len(parts) < 2:
        return {"streams": []}
    series_id = parts[0]
    season_num = 1
    ep_num = 1
    if series_id.startswith('kitsu'):
        series_id = f'{parts[0]}:{parts[1]}'
        ep_num = int(parts[2]) if len(parts) >= 3 else int(parts[1])
    else:
        if len(parts) >= 3:
            season_num = int(parts[1])
            ep_num = int(parts[2])
        else:
            ep_num = int(parts[1])

    if 'tt0388629' in series_id and season_num > 1:
        base_offset = ONE_PIECE_OFFSETS.get(season_num, 0)
        ep_num = base_offset + ep_num

    slug = KNOWN_SLUGS.get(series_id) or norm(resolve_stremio_title(video_id, prefer_type="series")).replace(' ', '-')
    filler_data = get_filler_data(slug)
    if not filler_data or ep_num not in filler_data:
        return {"streams": []}

    ep = filler_data[ep_num]
    ep_type = ep['type']
    if ep_type == 'canon':
        title = "✅ CÂNON — História Oficial"
        desc = f"────────────────────────────\n✅ CÂNON (Manga Canon)\n📖 Episódio {ep_num}: {ep['title']}\n🌟 Conteúdo oficial do mangá. Seguro assistir!\n────────────────────────────"
    elif ep_type == 'filler':
        next_canon = next((filler_data[n] for n in range(ep_num + 1, max(filler_data.keys()) + 1) if n in filler_data and filler_data[n]['type'] in ['canon', 'anime_canon', 'mixed']), None)
        next_hint = f"\n▶ Próximo Cânon: Ep. {next_canon['number']} ({next_canon['title']})" if next_canon else ""
        title = "⛔ FILLER — Descartável"
        desc = f"────────────────────────────\n⛔ FILLER (Não Oficial)\n⚠️ Episódio {ep_num}: {ep['title']}\n💡 Pode pular sem perder a história!{next_hint}\n────────────────────────────"
    elif ep_type == 'mixed':
        title = "⚠️ MISTO — Cânon + Filler"
        desc = f"────────────────────────────\n⚠️ MISTO (Canon + Filler)\n🎬 Episódio {ep_num}: {ep['title']}\n⚖️ Contém trechos do autor mesclados com cenas extras.\n────────────────────────────"
    elif ep_type == 'anime_canon':
        title = "🔵 ANIME CÂNON — Original Relevante"
        desc = f"────────────────────────────\n🔵 ANIME CÂNON\n📺 Episódio {ep_num}: {ep['title']}\n📌 Criado para o anime, importante para a trama.\n────────────────────────────"
    else:
        return {"streams": []}

    return {"streams": [{"name": title, "description": desc, "externalUrl": f"https://www.animefillerlist.com/shows/{slug}"}]}

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
