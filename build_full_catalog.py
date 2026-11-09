import urllib.request
import urllib.parse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
CONFIG_PATH = r'F:\Games\AniGUI-v3.4.1\anitsu_config.json'
CATALOG_MIN_PATH = os.path.join(os.path.dirname(__file__), 'catalog_min.json')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
ck = cfg.get('cookie', '')

def list_path(path):
    url = 'https://nuvem.anitsu.moe/api/files?path=' + urllib.parse.quote(path)
    req = urllib.request.Request(url, headers={'Cookie': ck, 'User-Agent': UA, 'Accept': '*/*'})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode()).get('files', [])
    except Exception as e:
        return []

def norm(text):
    if not text:
        return ''
    t = text.lower()
    t = re.sub(r'[\(\)\[\]\{\}\:\"\'\-\_\.\,\!\?]', ' ', t)
    return ' '.join(t.split())

KNOWN_MAP = {
    'rick e morty': ['rick and morty', 'rick e morty'],
    'avatar franquia': ['avatar the last airbender', 'avatar a lenda de aang', 'legend of korra', 'a lenda de korra'],
    'hora de aventura': ['adventure time', 'hora de aventura'],
    'as meninas superpoderosas': ['the powerpuff girls', 'powerpuff girls'],
    'as terriveis aventuras de billy e mandy': ['the grim adventures of billy and mandy', 'billy and mandy'],
    'os padrinhos magicos': ['the fairly oddparents', 'fairly oddparents'],
    'uma familia da pesada': ['family guy'],
    'a casa coruja': ['the owl house'],
    'invencivel': ['invincible'],
    'hotel hazbin': ['hazbin hotel'],
    'love death robots': ['love death and robots', 'love death & robots'],
    'castlevania noturno': ['castlevania nocturne'],
    'ei arnold': ['hey arnold'],
    'as aventuras de jimmy neutron o menino genio': ['the adventures of jimmy neutron', 'jimmy neutron'],
    'star wars the bad batch': ['the bad batch', 'star wars the bad batch'],
    'samurai jack': ['samurai jack'],
    'bojack horseman': ['bojack horseman'],
    'arcane': ['arcane league of legends', 'arcane'],
    'primal': ['genndy tartakovskys primal', 'primal'],
    'bob esponja': ['spongebob squarepants', 'spongebob'],
    'alice in borderland': ['alice in borderland', 'imawa no kuni no arisu'],
    'departamento de conspiracoes': ['inside job'],
    'desencanto': ['disenchantment'],
    'cuphead a serie': ['the cuphead show', 'cuphead']
}

def extract_aliases(name):
    aliases = set()
    n_clean = norm(name)
    aliases.add(n_clean)
    
    without_tags = re.sub(r'\[[^\]]*\]', '', name)
    without_year = re.sub(r'\(\d{4}[^\)]*\)', '', without_tags).strip()
    clean_norm = norm(without_year)
    if clean_norm:
        aliases.add(clean_norm)
        
    parens = re.findall(r'\(([^)]+)\)', name)
    for p in parens:
        if not re.match(r'^\d{4}', p.strip()):
            p_norm = norm(p)
            if len(p_norm) > 2:
                aliases.add(p_norm)
                
    if ' - ' in without_tags:
        parts = without_tags.split(' - ')
        for pt in parts:
            pt_norm = norm(pt)
            if len(pt_norm) > 2:
                aliases.add(pt_norm)
                
    for k, v_list in KNOWN_MAP.items():
        if k in clean_norm or clean_norm in k:
            for v in v_list:
                aliases.add(norm(v))
                
    return [a for a in aliases if len(a) > 1]

def build():
    print("Carregando catalog_min.json...", flush=True)
    with open(CATALOG_MIN_PATH, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    print(f"Catalog base com {len(existing)} animes.", flush=True)
    
    for item in existing:
        if 't' not in item: item['t'] = 'series'
        if 'c' not in item: item['c'] = 'anime'
            
    current_max_id = max(item['id'] for item in existing)
    next_id = max(current_max_id + 1, 60000)
    
    # 1. Desenhos/Filmes
    print("Coletando Desenhos/Filmes...", flush=True)
    filmes = list_path('Desenhos/Filmes')
    print(f"Encontrados {len(filmes)} Desenhos/Filmes.", flush=True)
    
    def process_filme(f):
        name = f['name']
        aliases = extract_aliases(name)
        tmdb_match = re.search(r'\[tmdb-(\d+)\]', name)
        tmdb_id = int(tmdb_match.group(1)) if tmdb_match else None
        
        subfiles = list_path(f"Desenhos/Filmes/{name}")
        for sf in subfiles:
            sf_name = sf.get('name', '')
            parts = re.split(r'\.(?:19|20)\d{2}\.|\.1080p|\.720p|\.BluRay|\.WEB', sf_name, flags=re.I)
            if parts and parts[0]:
                sf_alias = norm(parts[0])
                if len(sf_alias) > 3:
                    aliases.append(sf_alias)
        return {
            'n': name,
            'p': 'Desenhos/Filmes',
            'a': list(set(aliases)),
            't': 'movie',
            'c': 'desenhos',
            'tmdb': tmdb_id
        }

    with ThreadPoolExecutor(max_workers=8) as ex:
        filme_results = list(ex.map(process_filme, filmes))
        
    for res in filme_results:
        res['id'] = next_id
        existing.append(res)
        next_id += 1

    # 2. Desenhos/Séries
    print("Coletando Desenhos/Séries...", flush=True)
    series = list_path('Desenhos/Séries')
    print(f"Encontrados {len(series)} Desenhos/Séries.", flush=True)
    
    def process_serie(s):
        name = s['name']
        aliases = extract_aliases(name)
        return {
            'n': name,
            'p': 'Desenhos/Séries',
            'a': list(set(aliases)),
            't': 'series',
            'c': 'desenhos'
        }

    with ThreadPoolExecutor(max_workers=8) as ex:
        serie_results = list(ex.map(process_serie, series))
        
    for res in serie_results:
        res['id'] = next_id
        existing.append(res)
        next_id += 1

    # 3. Doramas
    print("Coletando Doramas...", flush=True)
    doramas = list_path('Doramas')
    print(f"Encontrados {len(doramas)} Doramas.", flush=True)
    for d in doramas:
        name = d['name']
        if name.startswith('[#'):
            continue
        aliases = extract_aliases(name)
        existing.append({
            'id': next_id,
            'n': name,
            'p': 'Doramas',
            'a': list(set(aliases)),
            't': 'series',
            'c': 'doramas'
        })
        next_id += 1

    print(f"Total de itens catalogados: {len(existing)}", flush=True)
    with open(CATALOG_MIN_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing, f, separators=(',', ':'), ensure_ascii=False)
    print("Arquivo catalog_min.json salvo com sucesso!", flush=True)

if __name__ == '__main__':
    build()
