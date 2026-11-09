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

DEFAULT_FALLBACK_TOKEN = 'aare7gnvapun'
DEFAULT_INITIAL_COOKIE = os.getenv('ANITSU_COOKIE', 'sb-auth-auth-token.0=base64-eyJhY2Nlc3NfdG9rZW4iOiJleUpoYkdjaU9pSkZVekkxTmlJc0ltdHBaQ0k2SW1OaU9XUTBaRGt5TFRsak9XVXRORE5qTVMxaE16QmpMVGhsWTJWaU5qY3lNbU5sT0NJc0luUjVjQ0k2SWtwWFZDSjkuZXlKcGMzTWlPaUpvZEhSd2N6b3ZMMkYxZEdndVlXNXBkSE4xTG0xdlpTOWhkWFJvTDNZeElpd2ljM1ZpSWpvaU5HUmpNek0wWTJRdFlqbGhOQzAwTnpFM0xUaG1abVV0WWpBMlltSTJNamN6WkRFM0lpd2lZWFZrSWpvaVlYVjBhR1Z1ZEdsallYUmxaQ0lzSW1WNGNDSTZNVGM1TkRJd056azVPU3dpYVdGMElqb3hOemswTWpBME16azVMQ0psYldGcGJDSTZJbVZrZFdGeVpHOWhibVJsY25OdmJqUXpRR2R0WVdsc0xtTnZiU0lzSW5Cb2IyNWxJam9pSWl3aVlYQndYMjFsZEdGa1lYUmhJanA3SW0xbGJXSmxjaUk2ZEhKMVpTd2ljSEp2ZG1sa1pYSWlPaUpsYldGcGJDSXNJbkJ5YjNacFpHVnljeUk2V3lKbGJXRnBiQ0lzSW1ScGMyTnZjbVFpWFgwc0luVnpaWEpmYldWMFlXUmhkR0VpT25zaVlYWmhkR0Z5SWpvaUlpd2lZWFpoZEdGeVgzVnliQ0k2SW1oMGRIQnpPaTh2WTJSdUxtUnBjMk52Y21SaGNIQXVZMjl0TDJGMllYUmhjbk12TWprMk1EazROREV3TXpVNE9EazROams1TDJVME9XUmtZall6WkRsak9XWmpZVGcwWkdVMFl6RTNOemRtWXpCaFl6ZG1MbkJ1WnlJc0ltTjFjM1J2YlY5amJHRnBiWE1pT25zaVoyeHZZbUZzWDI1aGJXVWlPaUpCYm1SbGNuTnZiaUo5TENKbGJXRnBiQ0k2SW1Wa2RXRnlaRzloYm1SbGNuTnZialF6UUdkdFlXbHNMbU52YlNJc0ltVnRZV2xzWDNabGNtbG1hV1ZrSWpwMGNuVmxMQ0ptZFd4c1gyNWhiV1VpT2lKaGJtUmxjbk52YmpBd01ERWlMQ0pwYzNNaU9pSm9kSFJ3Y3pvdkwyUnBjMk52Y21RdVkyOXRMMkZ3YVNJc0ltNWhiV1VpT2lKaGJtUmxjbk52YmpBd01ERWpNQ0lzSW5Cb2IyNWxYM1psY21sbWFXVmtJanBtWVd4elpTd2ljR2xqZEhWeVpTSTZJbWgwZEhCek9pOHZZMlJ1TG1ScGMyTnZjbVJoY0hBdVkyOXRMMkYyWVhSaGNuTXZNamsyTURrNE5ERXdNelU0T0RrNE5qazVMMlUwT1dSa1lqWXpaRGxqT1daallUZzBaR1UwWXpFM056ZG1ZekJoWXpkbUxuQnVaeUlzSW5CeWIzWnBaR1Z5WDJsa0lqb2lNamsyTURrNE5ERXdNelU0T0RrNE5qazVJaXdpYzNWaUlqb2lNamsyTURrNE5ERXdNelU0T0RrNE5qazVJaXdpZFhObGNtNWhiV1VpT2lKQmJtUmxjbk52YmpRek1UTWlmU3dpY205c1pTSTZJbUYxZEdobGJuUnBZMkYwWldRaUxDSmhZV3dpT2lKaFlXd3hJaXdpWVcxeUlqcGJleUp0WlhSb2IyUWlPaUp2WVhWMGFDSXNJblJwYldWemRHRnRjQ0k2TVRjNU5ESXdORE01T1gxZExDSnpaWE56YVc5dVgybGtJam9pTWprd00yWXpPVEF0WW1OaE5DMDBaR0UzTFRoaE5EVXROelZrWm1FMU1XSmhNbVZqSWl3aWFYTmZZVzV2Ym5sdGIzVnpJanBtWVd4elpYMC5yaE0tTjBadzNQSjI0LVhQS3phb2JUaWl2SDZuRGRrdFpkREVNc3NDclNMUXZTdlZFQnpvR1VJaVhTNm8yWWl5SlUxSmZSQ2N5U0ItUFhRNlM4cUJrdyIsInRva2VuX3R5cGUiOiJiZWFyZXIiLCJleHBpcmVzX2luIjozNjAwLCJleHBpcmVzX2F0IjoxNzk0MjA3OTk5LCJyZWZyZXNoX3Rva2VuIjoiYWFyZTdnbnZhcHVuIiwidXNlciI6eyJpZCI6IjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsImF1ZCI6ImF1dGhlbnRpY2F0ZWQiLCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImVtYWlsIjoiZWR1YXJkb2FuZGVyc29uNDNAZ21haWwuY29tIiwiZW1haWxfY29uZmlybWVkX2F0IjoiMjAyNC0wMi0xNVQwMzowNzoyOC4xODY3MTVaIiwicGhvbmUiOiIiLCJjb25maXJtZWRfYXQiOiIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4NjcxNVoiLCJsYXN0X3NpZ25faW5fYXQiOiIyMDI2LTExLTA5VDA2OjA2OjM5LjIzODY2OTU0NFoiLCJhcHBfbWV0YWRhdGEiOnsibWVtYmVyIjp0cnVlLCJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIiwiZGlzY29yZCJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXIiOiIiLCJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9jZG4uZGlzY29yZGFwcC5jb20vYXZhdGFycy8yOTYwOTg0MTAzNTg4OTg2OTkvZTQ5ZGRiNjNkOWM5ZmNhODRkZTRjMTc3N2ZjMGFjN2YucG5nIiwiY3VzdG9tX2NsYWltcyI6eyJnbG9iYWxfbmFtZSI6IkFuZGVyc29uIn0sImVtYWlsIjoiZWR1YXJkb2FuZGVyc29uNDNAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6ImFuZGVyc29uMDAwMSIsImlzcyI6Imh0dHBzOi8vZ; sb-auth-auth-token.1=GlzY29yZC5jb20vYXBpIiwibmFtZSI6ImFuZGVyc29uMDAwMSMwIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9jZG4uZGlzY29yZGFwcC5jb20vYXZhdGFycy8yOTYwOTg0MTAzNTg4OTg2OTkvZTQ5ZGRiNjNkOWM5ZmNhODRkZTRjMTc3N2ZjMGFjN2YucG5nIiwicHJvdmlkZXJfaWQiOiIyOTYwOTg0MTAzNTg4OTg2OTkiLCJzdWIiOiIyOTYwOTg0MTAzNTg4OTg2OTkiLCJ1c2VybmFtZSI6IkFuZGVyc29uNDMxMyJ9LCJpZGVudGl0aWVzIjpbeyJpZGVudGl0eV9pZCI6ImVhYzUxMzA0LThjMTAtNGQ3YS1iMTI1LTc5NmQ0YWFkYmQ3ZSIsImlkIjoiNGRjMzM0Y2QtYjlhNC00NzE3LThmZmUtYjA2YmI2MjczZDE3IiwidXNlcl9pZCI6IjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsImlkZW50aXR5X2RhdGEiOnsiZW1haWwiOiJlZHVhcmRvYW5kZXJzb240M0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiNGRjMzM0Y2QtYjlhNC00NzE3LThmZmUtYjA2YmI2MjczZDE3In0sInByb3ZpZGVyIjoiZW1haWwiLCJsYXN0X3NpZ25faW5fYXQiOiIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4NTM3NFoiLCJjcmVhdGVkX2F0IjoiMjAyNC0wMi0xNVQwMzowNzoyOC4xODU0MjNaIiwidXBkYXRlZF9hdCI6IjIwMjQtMDItMTVUMDM6MDc6MjguMTg1NDIzWiIsImVtYWlsIjoiZWR1YXJkb2FuZGVyc29uNDNAZ21haWwuY29tIn0seyJpZGVudGl0eV9pZCI6IjdmMTJjOTY2LWU4OWItNDZkYy04MjY5LWY2NDllYWUxZWE0YSIsImlkIjoiMjk2MDk4NDEwMzU4ODk4Njk5IiwidXNlcl9pZCI6IjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsImlkZW50aXR5X2RhdGEiOnsiYXZhdGFyX3VybCI6Imh0dHBzOi8vY2RuLmRpc2NvcmRhcHAuY29tL2F2YXRhcnMvMjk2MDk4NDEwMzU4ODk4Njk5L2U0OWRkYjYzZDljOWZjYTg0ZGU0YzE3NzdmYzBhYzdmLnBuZyIsImN1c3RvbV9jbGFpbXMiOnsiZ2xvYmFsX25hbWUiOiJBbmRlcnNvbiJ9LCJlbWFpbCI6ImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmdWxsX25hbWUiOiJhbmRlcnNvbjAwMDEiLCJpc3MiOiJodHRwczovL2Rpc2NvcmQuY29tL2FwaSIsIm5hbWUiOiJhbmRlcnNvbjAwMDEjMCIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwicGljdHVyZSI6Imh0dHBzOi8vY2RuLmRpc2NvcmRhcHAuY29tL2F2YXRhcnMvMjk2MDk4NDEwMzU4ODk4Njk5L2U0OWRkYjYzZDljOWZjYTg0ZGU0YzE3NzdmYzBhYzdmLnBuZyIsInByb3ZpZGVyX2lkIjoiMjk2MDk4NDEwMzU4ODk4Njk5Iiwic3ViIjoiMjk2MDk4NDEwMzU4ODk4Njk5In0sInByb3ZpZGVyIjoiZGlzY29yZCIsImxhc3Rfc2lnbl9pbl9hdCI6IjIwMjQtMTAtMjBUMjA6MTU6NTEuNjI1NTMzWiIsImNyZWF0ZWRfYXQiOiIyMDI0LTEwLTIwVDIwOjE1OjUxLjYyNTU5MloiLCJ1cGRhdGVkX2F0IjoiMjAyNi0xMS0wOVQwNjowNjozOC41MzQyNzZaIiwiZW1haWwiOiJlZHVhcmRvYW5kZXJzb240M0BnbWFpbC5jb20ifV0sImNyZWF0ZWRfYXQiOiIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4MzE4OVoiLCJ1cGRhdGVkX2F0IjoiMjAyNi0xMS0wOVQwNjowNjozOS4yNDU4NTVaIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0sInByb3ZpZGVyX3Rva2VuIjoiTVRJM01EVTJNVEF3TVRZMU56UTNNVEF3TmcuNFRFanM2bXRybFp3S3E4R1F3aFd4WUhKeUpmbFVjIiwicHJvdmlkZXJfcmVmcmVzaF90b2tlbiI6IkRrMGxBaGpsR0tlZFlDQVZJNG4xeDl3QWR6N2o4eSJ9')
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

def init_tokens():
    global refresh_token, current_cookie
    local_cfg = r'F:\Games\AniGUI-v3.4.1\anitsu_config.json'
    if os.path.exists(local_cfg):
        try:
            with open(local_cfg, 'r', encoding='utf-8') as f:
                cfg_d = json.load(f)
                live_ck = cfg_d.get('cookie')
                if live_ck:
                    with cookie_lock:
                        current_cookie = live_ck
                    print(f"[Anitsu Cloud] Loaded live cookie from AniGUI ({len(live_ck)} chars)")
        except Exception:
            pass

    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f).get('refresh_token')
                if saved:
                    refresh_token = saved
                    print(f"[Anitsu Cloud] Loaded refresh_token from local cache: {refresh_token[:6]}***")
                    return
        except Exception:
            pass
    refresh_token = os.getenv('ANITSU_REFRESH_TOKEN', DEFAULT_FALLBACK_TOKEN)
    print(f"[Anitsu Cloud] Using initial refresh_token: {refresh_token[:6]}***")

def init_catalog():
    global animes_list, title_index, tmdb_index
    if os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            animes_list = json.load(f)
        idx = {}
        tmdb_map = {}
        for a in animes_list:
            for al in a.get('a', []):
                if al and al not in idx:
                    idx[al] = a
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
            print(f"[Anitsu Cloud] Session token refreshed! User: {data.get('user', {}).get('email')}")
        else:
            print(f"[Anitsu Cloud] Refresh returned {res.status_code}. Using current active cookie.")
    except Exception as e:
        print("[Anitsu Cloud] Error refreshing token:", e)

def refresh_worker():
    while True:
        time.sleep(1800)
        refresh_session()

@app.on_event("startup")
def startup():
    init_tokens()
    init_catalog()
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

    cleaned_tokens = set(cleaned.split())

    best_match = None
    best_len = 0

    for alias, anime in title_index.items():
        if len(alias) < 3:
            continue
        if re.search(r'\b' + re.escape(alias) + r'\b', cleaned):
            if len(alias) > best_len:
                best_len = len(alias)
                best_match = anime
        elif re.search(r'\b' + re.escape(cleaned) + r'\b', alias):
            if len(cleaned) > best_len:
                best_len = len(cleaned)
                best_match = anime

    if best_match:
        return best_match

    best_score = 0
    for alias, anime in title_index.items():
        if len(alias) < 4:
            continue
        alias_tokens = set(alias.split())
        common = len(cleaned_tokens.intersection(alias_tokens))
        if common > best_score and common >= min(len(cleaned_tokens), 2):
            best_score = common
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
    series_id = parts[0]
    if series_id.startswith('kitsu'):
        kid = parts[1]
        try:
            r = requests.get(f'https://kitsu.io/api/edge/anime/{kid}', headers={'User-Agent': UA}, timeout=4)
            if r.status_code == 200:
                return r.json().get('data', {}).get('attributes', {}).get('canonicalTitle')
        except Exception:
            pass
    elif series_id.startswith('tt'):
        endpoints = [f'https://v3-cinemeta.strem.io/meta/{prefer_type}/{series_id}.json']
        alt_type = "movie" if prefer_type == "series" else "series"
        endpoints.append(f'https://v3-cinemeta.strem.io/meta/{alt_type}/{series_id}.json')
        for ep in endpoints:
            try:
                r = requests.get(ep, headers={'User-Agent': UA}, timeout=4)
                if r.status_code == 200:
                    name = r.json().get('meta', {}).get('name')
                    if name:
                        return name
            except Exception:
                pass
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

            for t_ep in target_eps:
                ep_patterns = [
                    re.compile(rf'(?:^|[^\d])0*{t_ep}(?:[^\d]|$)'),
                    re.compile(rf'[eE]0*{t_ep}(?:[^\d]|$)'),
                    re.compile(rf'ep\s*0*{t_ep}(?:[^\d]|$)', re.I)
                ]
                for vf in video_files:
                    name = vf['name']
                    # Clean crc32 checksums like [16892632]
                    name_clean = re.sub(r'\[[a-fA-F0-9]{8}\]', '', name)
                    
                    # Filter wrong seasons if file explicitly specifies S02 when we want S01
                    s_file_match = re.search(r'\b(?:s|season)\s*0?(\d+)\b', name_clean.lower())
                    if s_file_match and season_num <= 10 and 'one piece' not in anime['n'].lower():
                        if int(s_file_match.group(1)) != season_num:
                            continue

                    for pat in ep_patterns:
                        if pat.search(name_clean):
                            found_releases.append((f"{folder}/{name}", vf))
                            return # found in this folder

        subdirs = [f['name'] for f in files if f.get('is_directory')]
        for s in subdirs:
            s_lower = s.lower()
            if any(bad in s_lower for bad in ['filme', 'movie', 'live action', 'série', 'taose', 'especiais', 'ova']):
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

    # Sort releases: 1080p, BD, Netflix, Web, Dual first
    def score_rel(item):
        p, vf = item
        n = vf.get('name', '').lower()
        pl = p.lower()
        score = 0
        if '1080' in n or '1080' in pl: score += 20
        if 'bluray' in n or 'bd' in n or 'bd' in pl: score += 15
        if 'dual' in n or 'dublado' in n or 'dual' in pl: score += 12
        if 'netflix' in pl or 'nf' in n: score += 12
        if 'opex' in pl: score += 10
        if 'cr' in pl or 'crunchyroll' in pl: score += 8
        if 'kyoshiro' in pl: score += 15
        if 'sennin' in pl: score += 14
        if '720' in n: score -= 10
        if '480' in n or '576' in n: score -= 20
        return score

    found_releases.sort(key=score_rel, reverse=True)
    return found_releases

def format_stream_card(anime, vf, remote_path, season_num, ep_num, is_movie=False, is_proxy=False):
    filename = vf.get('name', '')
    fn = filename.lower()
    pl = remote_path.lower()

    # 1. Resolution & Left Badge
    if '2160' in fn or '4k' in fn or '4k' in pl:
        res = '2160P ⚡'
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
    elif 'web' in fn or 'nf' in fn or 'netflix' in pl or 'cr' in pl:
        src = '(Web-dl) ★★★'
    elif 'hdtv' in fn or 'hdtv' in pl:
        src = '(Hdtv) ★★'
    elif 'dvd' in fn or 'dvd' in pl:
        src = '(Dvdrip) ★'
    else:
        src = '★★★'

    if is_proxy:
        name = f"{res.replace('⚡', '🛡️')}\n(Proxy) ★★"
    else:
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

    is_dual = 'dual' in fn or 'dublado' in fn or 'dual' in pl or 'dublado' in pl
    if is_dual:
        audio += ' · Dual Áudio'
    else:
        audio += ' · Legendado PT-BR'

    # 4. Group / Release Name
    group_str = ""
    if 'netflix' in pl:
        group_str = " · Netflix DUAL"
    elif 'opex' in pl:
        group_str = " · Opex FHD"
    elif 'kyoshiro' in pl:
        group_str = " · Kyoshiro BD"
    elif 'sennin' in pl:
        group_str = " · Sennin RMZ"
    elif 'harlley' in pl:
        group_str = " · Harlley DUAL"
    elif 'mattmurdock' in pl:
        group_str = " · Mattmurdock DUAL"
    elif 'shakaw' in pl:
        group_str = " · ShaKaw"
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
    if is_proxy:
        cloud_tag = "☁️ Nuvem Render [Proxy 24/7]"
    else:
        cloud_tag = "☁️ Nuvem Anitsu [Sem Espera / Sem Torrent]"

    # 8. Languages & Player flags
    if is_dual:
        lang_str = "✔ PT-BR (Dublado) · JA · SUB"
    else:
        lang_str = "✔ JA · Legendado PT-BR · SUB"
    player_str = "✔ EXOPLAYER SAFE"

    if is_movie:
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
        "version": "1.2.0",
        "name": "☁️ Anitsu Nuvem [PT-BR]",
        "description": "5.800+ Animes, Filmes de Anime, Desenhos e Doramas em Fansub 1080p PT-BR direto da Nuvem Anitsu com múltiplas opções de releases!",
        "logo": "https://nuvem.anitsu.moe/icon.png",
        "resources": ["catalog", "meta", "stream"],
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
        if subdirs:
            for s_idx, sname in enumerate(subdirs):
                s_files = anitsu_list_files(f"{root_folder}/{sname}")
                vfiles = [f for f in s_files if not f.get('is_directory') and f['name'].lower().endswith(('.mkv', '.mp4'))]
                vfiles.sort(key=lambda x: x['name'])
                for ep_idx, vf in enumerate(vfiles):
                    videos.append({
                        "id": f"anitsu:{aid}:{s_idx+1}:{ep_idx+1}",
                        "title": vf['name'],
                        "season": s_idx + 1,
                        "episode": ep_idx + 1
                    })
        else:
            vfiles = [f for f in files if not f.get('is_directory') and f['name'].lower().endswith(('.mkv', '.mp4'))]
            vfiles.sort(key=lambda x: x['name'])
            for ep_idx, vf in enumerate(vfiles):
                videos.append({
                    "id": f"anitsu:{aid}:1:{ep_idx+1}",
                    "title": vf['name'],
                    "season": 1,
                    "episode": ep_idx + 1
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

@app.get("/stream/{type_}/{video_id}.json")
def stream(type_: str, video_id: str, request: Request):
    parts = video_id.split(':')
    matched_anime = None
    season_num = 1
    ep_num = 1
    is_movie = type_ == "movie" or (len(parts) == 1 and video_id.startswith('tt'))

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
        season_num = 1
        ep_num = int(parts[2]) if len(parts) >= 3 else (int(parts[1]) if len(parts) >= 2 else 1)
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

    if not matched_anime:
        return {"streams": []}

    if matched_anime.get('t') == 'movie':
        is_movie = True

    res_list = find_all_episode_files(matched_anime, season_num, ep_num, video_id=video_id)
    if not res_list:
        return {"streams": []}

    with cookie_lock:
        ck = current_cookie

    base_url = str(request.base_url).rstrip('/')
    streams = []

    # Display up to 5 best distinct releases
    for r_idx, (remote_path, vf) in enumerate(res_list[:5]):
        card_name_direct, card_title_direct = format_stream_card(
            matched_anime, vf, remote_path, season_num, ep_num, is_movie=is_movie, is_proxy=False
        )
        card_name_proxy, card_title_proxy = format_stream_card(
            matched_anime, vf, remote_path, season_num, ep_num, is_movie=is_movie, is_proxy=True
        )

        direct_url = f"https://nuvem.anitsu.moe/api/download?path={urllib.parse.quote(remote_path)}"
        proxy_url = f"{base_url}/proxy-stream?path={urllib.parse.quote(remote_path)}"

        streams.append({
            "name": card_name_direct,
            "title": card_title_direct,
            "url": direct_url,
            "behaviorHints": {
                "notWebReady": False,
                "bingeGroup": f"anitsu-{matched_anime['id']}-{r_idx}",
                "proxyHeaders": {
                    "request": {
                        "Cookie": ck,
                        "User-Agent": UA,
                        "Accept": "*/*"
                    }
                }
            }
        })
        # Add proxy option for the best release
        if r_idx == 0:
            streams.append({
                "name": card_name_proxy,
                "title": card_title_proxy,
                "url": proxy_url,
                "behaviorHints": {
                    "notWebReady": False,
                    "bingeGroup": f"anitsu-{matched_anime['id']}-proxy-{r_idx}"
                }
            })

    return {"streams": streams}

@app.get("/proxy-stream")
def proxy_stream(path: str, request: Request):
    with cookie_lock:
        ck = current_cookie
    anitsu_url = 'https://nuvem.anitsu.moe/api/download?path=' + urllib.parse.quote(path)
    headers = {'Cookie': ck, 'User-Agent': UA, 'Accept': '*/*'}
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header

    req = requests.get(anitsu_url, headers=headers, stream=True)
    response_headers = {}
    for h in ['Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges', 'Content-Disposition']:
        if h in req.headers:
            response_headers[h] = req.headers[h]

    return StreamingResponse(req.iter_content(chunk_size=65536), status_code=req.status_code, headers=response_headers)

# --- Filler Guide Addon Routes ---
KNOWN_SLUGS = {
    'tt0988824': 'naruto-shippuden', 'tt0409591': 'naruto', 'tt0388629': 'one-piece',
    'tt0434665': 'bleach', 'tt14946658': 'bleach-thousand-year-blood-war',
    'tt0131179': 'detective-conan', 'tt2098220': 'hunter-x-hunter-2011',
    'tt0112159': 'rurouni-kenshin', 'tt0106179': 'yu-yu-hakusho', 'tt5626028': 'black-clover',
    'tt6342474': 'boruto-naruto-next-generations', 'tt0280249': 'dragon-ball-z',
    'tt0423731': 'gintama', 'tt1856014': 'fairy-tail', 'tt2560140': 'attack-on-titan',
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
