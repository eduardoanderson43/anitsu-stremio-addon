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

DEFAULT_FALLBACK_TOKEN = 'at4jx3pg4gwq'
DEFAULT_INITIAL_COOKIE = os.getenv('ANITSU_COOKIE', 'sb-auth-auth-token.0=base64-eyJhY2Nlc3NfdG9rZW4iOiAiZXlKaGJHY2lPaUpGVXpJMU5pSXNJbXRwWkNJNkltTmlPV1EwWkRreUxUbGpPV1V0TkROak1TMWhNekJqTFRobFkyVmlOamN5TW1ObE9DSXNJblI1Y0NJNklrcFhWQ0o5LmV5SnBjM01pT2lKb2RIUndjem92TDJGMWRHZ3VZVzVwZEhOMUxtMXZaUzloZFhSb0wzWXhJaXdpYzNWaUlqb2lOR1JqTXpNMFkyUXRZamxoTkMwME56RTNMVGhtWm1VdFlqQTJZbUkyTWpjelpERTNJaXdpWVhWa0lqb2lZWFYwYUdWdWRHbGpZWFJsWkNJc0ltVjRjQ0k2TVRjNU5ESXdNelkwT1N3aWFXRjBJam94TnprME1qQXdNRFE1TENKbGJXRnBiQ0k2SW1Wa2RXRnlaRzloYm1SbGNuTnZialF6UUdkdFlXbHNMbU52YlNJc0luQm9iMjVsSWpvaUlpd2lZWEJ3WDIxbGRHRmtZWFJoSWpwN0ltMWxiV0psY2lJNmRISjFaU3dpY0hKdmRtbGtaWElpT2lKbGJXRnBiQ0lzSW5CeWIzWnBaR1Z5Y3lJNld5SmxiV0ZwYkNJc0ltUnBjMk52Y21RaVhYMHNJblZ6WlhKZmJXVjBZV1JoZEdFaU9uc2lZWFpoZEdGeUlqb2lJaXdpWVhaaGRHRnlYM1Z5YkNJNkltaDBkSEJ6T2k4dlkyUnVMbVJwYzJOdmNtUmhjSEF1WTI5dEwyRjJZWFJoY25Ndk1qazJNRGs0TkRFd016VTRPRGs0TmprNUwyVTBPV1JrWWpZelpEbGpPV1pqWVRnMFpHVTBZekUzTnpkbVl6QmhZemRtTG5CdVp5SXNJbU4xYzNSdmJWOWpiR0ZwYlhNaU9uc2laMnh2WW1Gc1gyNWhiV1VpT2lKQmJtUmxjbk52YmlKOUxDSmxiV0ZwYkNJNkltVmtkV0Z5Wkc5aGJtUmxjbk52YmpRelFHZHRZV2xzTG1OdmJTSXNJbVZ0WVdsc1gzWmxjbWxtYVdWa0lqcDBjblZsTENKbWRXeHNYMjVoYldVaU9pSmhibVJsY25OdmJqQXdNREVpTENKcGMzTWlPaUpvZEhSd2N6b3ZMMlJwYzJOdmNtUXVZMjl0TDJGd2FTSXNJbTVoYldVaU9pSmhibVJsY25OdmJqQXdNREVqTUNJc0luQm9iMjVsWDNabGNtbG1hV1ZrSWpwbVlXeHpaU3dpY0dsamRIVnlaU0k2SW1oMGRIQnpPaTh2WTJSdUxtUnBjMk52Y21SaGNIQXVZMjl0TDJGMllYUmhjbk12TWprMk1EazROREV3TXpVNE9EazROams1TDJVME9XUmtZall6WkRsak9XWmpZVGcwWkdVMFl6RTNOemRtWXpCaFl6ZG1MbkJ1WnlJc0luQnliM1pwWkdWeVgybGtJam9pTWprMk1EazROREV3TXpVNE9EazROams1SWl3aWMzVmlJam9pTWprMk1EazROREV3TXpVNE9EazROams1SWl3aWRYTmxjbTVoYldVaU9pSkJibVJsY25OdmJqUXpNVE1pZlN3aWNtOXNaU0k2SW1GMWRHaGxiblJwWTJGMFpXUWlMQ0poWVd3aU9pSmhZV3d4SWl3aVlXMXlJanBiZXlKdFpYUm9iMlFpT2lKdllYVjBhQ0lzSW5ScGJXVnpkR0Z0Y0NJNk1UYzVOREU1T0RRNU0zMWRMQ0p6WlhOemFXOXVYMmxrSWpvaVpqRTJZakF5T1dRdFptUmhZaTAwTURKaUxXRTJZekl0Wm1Vd1lUUmlaVGc1T0RBeUlpd2lhWE5mWVc1dmJubHRiM1Z6SWpwbVlXeHpaWDAuWVZrWURWTmZSbDNraW0wbEtoUk52UFRPa2NoSmNCNXNFS2pRbllpZTdfaVR3aHdYV1g1N2dHNjJzdjBQcDFGZktWT0RjWmFYb1Nua1lHZ0tpdFFrS2ciLCAidG9rZW5fdHlwZSI6ICJiZWFyZXIiLCAiZXhwaXJlc19pbiI6IDM2MDAsICJleHBpcmVzX2F0IjogMTc5NDIwMzY0OSwgInJlZnJlc2hfdG9rZW4iOiAiYXQ0angzcGc0Z3dxIiwgInVzZXIiOiB7ImlkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJhdWQiOiAiYXV0aGVudGljYXRlZCIsICJyb2xlIjogImF1dGhlbnRpY2F0ZWQiLCAiZW1haWwiOiAiZWR1YXJkb2FuZGVyc29uNDNAZ21haWwuY29tIiwgImVtYWlsX2NvbmZpcm1lZF9hdCI6ICIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4NjcxNVoiLCAicGhvbmUiOiAiIiwgImNvbmZpcm1lZF9hdCI6ICIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4NjcxNVoiLCAibGFzdF9zaWduX2luX2F0IjogIjIwMjYtMTEtMDlUMDQ6Mjg6MTMuODIyMDI5WiIsICJhcHBfbWV0YWRhdGEiOiB7Im1lbWJlciI6IHRydWUsICJwcm92aWRlciI6ICJlbWFpbCIsICJwcm92aWRlcnMiOiBbImVtYWlsIiwgImRpc2NvcmQiXX0sICJ1c2VyX21ldGFkYXRhIjogeyJhdmF0YXIiOiAiIiwgImF2YXRhcl91cmwiOiAiaHR0cHM6Ly9jZG4uZGlzY29yZGFwcC5jb20vYXZhdGFycy8yOTYwOTg0MTAzNTg4OTg2OTkvZTQ5ZGRiNjNkOWM5ZmNhODRkZTRjMTc3N2ZjMGFjN2YucG5nIiwgImN1c3RvbV9jbGFpbXMiOiB7Imdsb2JhbF9uYW1lIjogIkFuZGVyc29uIn0sICJlbWFpbCI6ICJlZHVhcmRvYW5kZXJzb240M0BnbWFpbC5jb20iLCAiZW1haWxfdmVyaWZpZWQiOiB0cnVlLCAiZnVsbF9uYW1lIjogImFuZGVyc29uMDAwMSIsICJpc3MiOiAiaHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkiLCAibmFtZSI6ICJhbmRlcnNvbjAwMDEjMCIsICJwaG9uZV92ZXJpZmllZCI6IGZhbHNlLCAicGljdHVyZSI6ICJodHRwczovL2Nkbi5kaXNjb3JkYXBwLmNvbS9hdmF0YXJzLzI5NjA5ODQxMDM1ODg5ODY5OS9lNDlkZGI2M2Q5YzlmY2E4NGRlNGMxNzc3ZmMwYWM3Zi5wbmciLCAicHJvdmlkZXJfaWQiOiAiMjk2MDk4NDEwMzU4ODk4Njk5IiwgInN1YiI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcm5hbWUiOiAiQW5kZXJzb240MzEzIn0sICJpZGVudGl0aWVzIjogW3siaWRlbnRpdHlfaWQiOiAiZWFjNTEzMDQtOGMxMC00ZDdhLWIxMjUtNzk2ZDRhYWRiZDdlIiwgImlkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJ1c2VyX2lkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJpZGVudGl0eV9kYXRhIjogeyJlbWFpbCI6ICJlZHVhcmRvYW5kZXJzb240M0BnbWFpbC5jb20iLCAiZW1haWxfdmVyaWZpZWQiOiBmYWxzZSwgInBob25lX3ZlcmlmaWVkIjogZmFsc2UsICJzdWIiOiAiNGRjMzM0Y2QtYjlhNC00NzE3LThmZmUtYjA2YmI2MjczZDE3In0sICJwcm92aWRlciI6ICJlbWFpbCIsICJsYXN0X3NpZ25faW5fYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODUzNzRaIiwgImNyZWF0ZWRfYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODU0MjNaIiwgInVwZGF0ZWRfYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODU0MjNaIiwgImVtYWlsIjogImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSJ9LCB7ImlkZW50aXR5X2lkIjogIjdmMTJjOTY2LWU4OWItNDZkYy04MjY5LWY2NDllYWUxZWE0YSIsICJpZCI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcl9pZCI6ICI0ZGMzMzRjZC1iOWE0LTQ3MTctOGZmZS1iMDZiYjYyNzNkMTciLCAiaWRlbnRpdHlfZGF0YSI6IHsiYXZhdGFyX3VybCI6ICJodHRwczovL2Nkbi5kaXNjb3JkYXBwLmNvbS9hdmF0YXJzLzI5NjA5ODQxMDM1ODg5ODY5OS9lNDlkZGI2M2Q5YzlmY2E4NGRlNGMxNzc3ZmMwYWM3Zi5wbmciLCAiY3VzdG9tX2NsYWltcyI6IHsiZ2xvYmFsX25hbWUiOiAiQW5kZXJzb24ifSwgImVtYWlsIjogImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSIsICJlbWFpbF92ZXJpZmllZCI6IHRydWUsICJmdWxsX25hbWUiOiAiYW5kZXJzb24wMDAxIiwgImlzcyI6ICJodHRwczovL2Rpc2NvcmQuY29tL2FwaSIsICJuYW1lIjogImFuZGVyc29uMDAwMSMwIiwgInBob25lX3ZlcmlmaWVkIjogZmFsc2UsICJwaWN0dXJlIjogImh0dHBzOi8vY2RuLmRpc2NvcmRhcHAuY29tL2F2YXRhcnMvMjk2MDk4NDEwMzU4ODk4Njk5L2U0OWRkYjYzZDljOWZjYTg0ZGU0YzE3NzdmYzBhYzdmLnBuZyIsICJwcm92aWRlcl9pZCI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcm5hbWUiOiAiQW5kZXJzb240MzEzIn0sICJwcm92aWRlciI6ICJkaXNjb3JkIiwgImxhc3Rfc2lnbl9pbl9hdCI6ICIyMDI0LTEwLTIwVDIwOjE1OjUxLjYyNTUzM1oiLCAiY3JlYXRlZF9hdCI6ICIyMDI0LTEwLTIwVDIwOjE1OjUxLjYyNTU5MloiLCAidXBkYXRlZF9hdCI6ICIyMDI2LTExLTA5VDA0OjI4OjEzLjAzODMyOFoiLCAiZW1haWwiOiAiZWR1YXJkb2FuZGVyc29uNDNAZ21haWwuY29tIn1dLCAiY3JlYXRlZF9hdCI6ICIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4MzE4OVoiLCAidXBkYXRlZF9hdCI6ICIyMDI2LTExLTA5VDA0OjU0OjA5LjE2MDY5NVoiLCAiaXNfYW5vbnltb3VzIjogZmFsc2V9fQ==; sb-auth-auth-token.1=CAiZnVsbF9uYW1lIjogImFuZGVyc29uMDAwMSIsICJpc3MiOiAiaHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkiLCAibmFtZSI6ICJhbmRlcnNvbjAwMDEjMCIsICJwaG9uZV92ZXJpZmllZCI6IGZhbHNlLCAicGljdHVyZSI6ICJodHRwczovL2Nkbi5kaXNjb3JkYXBwLmNvbS9hdmF0YXJzLzI5NjA5ODQxMDM1ODg5ODY5OS9lNDlkZGI2M2Q5YzlmY2E4NGRlNGMxNzc3ZmMwYWM3Zi5wbmciLCAicHJvdmlkZXJfaWQiOiAiMjk2MDk4NDEwMzU4ODk4Njk5IiwgInN1YiI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcm5hbWUiOiAiQW5kZXJzb240MzEzIn0sICJpZGVudGl0aWVzIjogW3siaWRlbnRpdHlfaWQiOiAiZWFjNTEzMDQtOGMxMC00ZDdhLWIxMjUtNzk2ZDRhYWRiZDdlIiwgImlkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJ1c2VyX2lkIjogIjRkYzMzNGNkLWI5YTQtNDcxNy04ZmZlLWIwNmJiNjI3M2QxNyIsICJpZGVudGl0eV9kYXRhIjogeyJlbWFpbCI6ICJlZHVhcmRvYW5kZXJzb240M0BnbWFpbC5jb20iLCAiZW1haWxfdmVyaWZpZWQiOiBmYWxzZSwgInBob25lX3ZlcmlmaWVkIjogZmFsc2UsICJzdWIiOiAiNGRjMzM0Y2QtYjlhNC00NzE3LThmZmUtYjA2YmI2MjczZDE3In0sICJwcm92aWRlciI6ICJlbWFpbCIsICJsYXN0X3NpZ25faW5fYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODUzNzRaIiwgImNyZWF0ZWRfYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODU0MjNaIiwgInVwZGF0ZWRfYXQiOiAiMjAyNC0wMi0xNVQwMzowNzoyOC4xODU0MjNaIiwgImVtYWlsIjogImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSJ9LCB7ImlkZW50aXR5X2lkIjogIjdmMTJjOTY2LWU4OWItNDZkYy04MjY5LWY2NDllYWUxZWE0YSIsICJpZCI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcl9pZCI6ICI0ZGMzMzRjZC1iOWE0LTQ3MTctOGZmZS1iMDZiYjYyNzNkMTciLCAiaWRlbnRpdHlfZGF0YSI6IHsiYXZhdGFyX3VybCI6ICJodHRwczovL2Nkbi5kaXNjb3JkYXBwLmNvbS9hdmF0YXJzLzI5NjA5ODQxMDM1ODg5ODY5OS9lNDlkZGI2M2Q5YzlmY2E4NGRlNGMxNzc3ZmMwYWM3Zi5wbmciLCAiY3VzdG9tX2NsYWltcyI6IHsiZ2xvYmFsX25hbWUiOiAiQW5kZXJzb24ifSwgImVtYWlsIjogImVkdWFyZG9hbmRlcnNvbjQzQGdtYWlsLmNvbSIsICJlbWFpbF92ZXJpZmllZCI6IHRydWUsICJmdWxsX25hbWUiOiAiYW5kZXJzb24wMDAxIiwgImlzcyI6ICJodHRwczovL2Rpc2NvcmQuY29tL2FwaSIsICJuYW1lIjogImFuZGVyc29uMDAwMSMwIiwgInBob25lX3ZlcmlmaWVkIjogZmFsc2UsICJwaWN0dXJlIjogImh0dHBzOi8vY2RuLmRpc2NvcmRhcHAuY29tL2F2YXRhcnMvMjk2MDk4NDEwMzU4ODk4Njk5L2U0OWRkYjYzZDljOWZjYTg0ZGU0YzE3NzdmYzBhYzdmLnBuZyIsICJwcm92aWRlcl9pZCI6ICIyOTYwOTg0MTAzNTg4OTg2OTkiLCAidXNlcm5hbWUiOiAiQW5kZXJzb240MzEzIn0sICJwcm92aWRlciI6ICJkaXNjb3JkIiwgImxhc3Rfc2lnbl9pbl9hdCI6ICIyMDI0LTEwLTIwVDIwOjE1OjUxLjYyNTUzM1oiLCAiY3JlYXRlZF9hdCI6ICIyMDI0LTEwLTIwVDIwOjE1OjUxLjYyNTU5MloiLCAidXBkYXRlZF9hdCI6ICIyMDI2LTExLTA5VDA0OjI4OjEzLjAzODMyOFoiLCAiZW1haWwiOiAiZWR1YXJkb2FuZGVyc29uNDNAZ21haWwuY29tIn1dLCAiY3JlYXRlZF9hdCI6ICIyMDI0LTAyLTE1VDAzOjA3OjI4LjE4MzE4OVoiLCAidXBkYXRlZF9hdCI6ICIyMDI2LTExLTA5VDA0OjU0OjA5LjE2MDY5NVoiLCAiaXNfYW5vbnltb3VzIjogZmFsc2V9fQ==')
refresh_token = ''
current_cookie = DEFAULT_INITIAL_COOKIE
cookie_lock = threading.Lock()

animes_list = []
title_index = {}
tmdb_index = {}
cache_files = {}
cache_filler = {}
cache_name = {}

def norm(text):
    if not text:
        return ''
    t = text.lower()
    t = re.sub(r'[\(\)\[\]\{\}\:\"\'\-\_\.\,\!\?]', ' ', t)
    return ' '.join(t.split())

def init_tokens():
    global refresh_token
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
            print(f"[Anitsu Cloud] Refresh failed with status {res.status_code}: {res.text}")
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
    tokens = set(cleaned.split())
    best_match = None
    best_score = 0
    for alias, anime in title_index.items():
        if cleaned in alias or alias in cleaned:
            return anime
        alias_tokens = set(alias.split())
        common = len(tokens.intersection(alias_tokens))
        if common > best_score and common >= min(len(tokens), 2):
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

def find_episode_file(anime, season_num, ep_num):
    root_folder = f"{anime['p']}/{anime['n']}"
    is_movie = anime.get('t') == 'movie' or 'Filmes' in anime.get('p', '')
    
    def search_folder(folder, target_season, target_ep, depth=0):
        if depth > 3:
            return None
        files = anitsu_list_files(folder)
        if not files:
            return None
            
        video_files = [f for f in files if not f.get('is_directory') and f.get('name', '').lower().endswith(('.mkv', '.mp4'))]
        if video_files:
            if is_movie:
                # For movies, pick the best video file
                def score_movie(vf):
                    n = vf.get('name', '').lower()
                    score = 0
                    if '1080' in n: score += 10
                    if 'bluray' in n or 'bd' in n: score += 5
                    if 'dual' in n or 'dublado' in n: score += 5
                    return score
                video_files.sort(key=score_movie, reverse=True)
                return f"{folder}/{video_files[0]['name']}", video_files[0]

            patterns = [
                re.compile(rf'[\s\-_]0*{target_ep}\b'),
                re.compile(rf'[eE]0*{target_ep}\b'),
                re.compile(rf'ep\s*0*{target_ep}\b', re.I),
                re.compile(rf'epis[oó]dio\s*0*{target_ep}\b', re.I)
            ]
            for pat in patterns:
                for vf in video_files:
                    if pat.search(vf['name']):
                        return f"{folder}/{vf['name']}", vf
            if len(video_files) == 1 and target_ep == 1:
                return f"{folder}/{video_files[0]['name']}", video_files[0]
                
        subdirs = [f['name'] for f in files if f.get('is_directory')]
        if not subdirs:
            return None
            
        if depth == 0 and len(subdirs) > 1 and not is_movie:
            filtered = [s for s in subdirs if not any(x in s.lower() for x in ['ova', 'chuugakkou'])]
            pat = re.compile(rf'(?:season|temporada|s|part)\s*0?{target_season}\b', re.I)
            matched = [s for s in filtered if pat.search(s)]
            if not matched and target_season == 1:
                matched = [s for s in filtered if not re.search(r'(?:season|temporada|s|part)\s*[2-9]\b', s, re.I)]
            if matched:
                subdirs = matched
                
        def score_dir(dname):
            d = dname.lower()
            score = 0
            if '1080' in d: score += 10
            if 'bd' in d or 'blu-ray' in d or 'bluray' in d: score += 5
            if 'anipakku' in d: score += 3
            if 'dual' in d: score += 3
            if '720' in d: score -= 5
            return score
            
        subdirs.sort(key=score_dir, reverse=True)
        for s in subdirs:
            res = search_folder(f"{folder}/{s}", target_season, target_ep, depth + 1)
            if res:
                return res
        return None
        
    return search_folder(root_folder, season_num, ep_num, 0)

def get_anitsu_manifest():
    return {
        "id": "community.anitsu.cloud",
        "version": "1.1.0",
        "name": "☁️ Anitsu Nuvem [PT-BR]",
        "description": "5.700+ Animes, Desenhos Animados, Filmes e Doramas em Fansub 1080p PT-BR direto da Nuvem Anitsu!",
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
                "name": "🎬 Anitsu · Filmes Animados (PT-BR)",
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
        filtered = [a for a in animes_list if a.get('c') == 'desenhos' and a.get('t') == 'movie']
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

def format_stream_card(anime, vf, season_num, ep_num, is_movie=False, is_proxy=False):
    filename = vf.get('name', '')
    fn = filename.lower()

    # 1. Resolution & Left Badge
    if '2160' in fn or '4k' in fn:
        res = '2160P ⚡'
    elif '720' in fn:
        res = '720P ⚡'
    elif '480' in fn or 'dvd' in fn:
        res = '480P ⚡'
    else:
        res = '1080P ⚡'

    if 'remux' in fn:
        src = '(Remux) ★★★'
    elif 'bluray' in fn or 'bd' in fn:
        src = '(Bluray) ★★★'
    elif 'web' in fn or 'nf' in fn:
        src = '(Web-dl) ★★★'
    elif 'hdtv' in fn:
        src = '(Hdtv) ★★'
    elif 'dvd' in fn:
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
    if 'ddp' in fn or '5.1' in fn:
        audio = '♫ DD 5.1'
    elif 'flac' in fn:
        audio = '♫ FLAC 2.0'
    elif 'aac' in fn:
        audio = '♫ AAC 2.0'
    else:
        audio = '♫ DD 2.0'

    if 'dual' in fn:
        audio += ' · Dual Áudio'
    elif 'dublado' in fn:
        audio += ' · Dublado PT-BR'

    # 4. Group
    m_grp = re.search(r'-([a-zA-Z0-9_]+)(?:\.[a-zA-Z0-9]+)?$', filename)
    group_str = f" · {m_grp.group(1)}" if m_grp else ""

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
    has_dual = 'dual' in fn or 'dublado' in fn or 'pt-br' in anime.get('p', '').lower()
    if has_dual:
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
        title = resolve_stremio_title(video_id, prefer_type="series")
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

    res = find_episode_file(matched_anime, season_num, ep_num)
    if not res:
        return {"streams": []}

    remote_path, vf = res
    card_name_direct, card_title_direct = format_stream_card(matched_anime, vf, season_num, ep_num, is_movie=is_movie, is_proxy=False)
    card_name_proxy, card_title_proxy = format_stream_card(matched_anime, vf, season_num, ep_num, is_movie=is_movie, is_proxy=True)
    
    # 1. Direct stream URL with proxyHeaders (streams straight from Anitsu Nuvem!)
    direct_url = f"https://nuvem.anitsu.moe/api/download?path={urllib.parse.quote(remote_path)}"
    
    # 2. Proxy fallback URL via this host
    base_url = str(request.base_url).rstrip('/')
    proxy_url = f"{base_url}/proxy-stream?path={urllib.parse.quote(remote_path)}"

    with cookie_lock:
        ck = current_cookie

    return {
        "streams": [
            {
                "name": card_name_direct,
                "title": card_title_direct,
                "url": direct_url,
                "behaviorHints": {
                    "notWebReady": False,
                    "bingeGroup": f"anitsu-{matched_anime['id']}",
                    "proxyHeaders": {
                        "request": {
                            "Cookie": ck,
                            "User-Agent": UA,
                            "Accept": "*/*"
                        }
                    }
                }
            },
            {
                "name": card_name_proxy,
                "title": card_title_proxy,
                "url": proxy_url,
                "behaviorHints": {
                    "notWebReady": False,
                    "bingeGroup": f"anitsu-{matched_anime['id']}-proxy"
                }
            }
        ]
    }

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
    if series_id.startswith('kitsu'):
        series_id = f'{parts[0]}:{parts[1]}'
        ep_num = int(parts[2]) if len(parts) >= 3 else int(parts[1])
    else:
        ep_num = int(parts[2]) if len(parts) >= 3 else int(parts[1])

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
