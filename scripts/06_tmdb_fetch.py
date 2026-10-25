import pandas as pd
import requests
import json
import time
import os

TMDB_API_KEY = 'a4e7e71180d8f2bec20d54038eaa61bb'

top500 = pd.read_csv('output/top500_with_clusters.csv')
links = pd.read_csv('data/ml-25m/links.csv')

top500 = top500.merge(links[['movieId', 'tmdbId']], on='movieId', how='left')

results = []

for i, row in top500.iterrows():
    tmdb_id = row['tmdbId']
    if pd.isna(tmdb_id):
        continue

    tmdb_id = int(tmdb_id)

    try:
        url = f'https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}&language=ko-KR'
        res = requests.get(url).json()

        title = row['title']
        poster = f"https://image.tmdb.org/t/p/w300{res.get('poster_path', '')}" if res.get('poster_path') else ''
        overview = res.get('overview', '')
        origin_country = res.get('origin_country', [])
        production_companies = [c['name'] for c in res.get('production_companies', [])]

        # 문화권 분류
        if any(c in ['JP'] for c in origin_country):
            culture = 'japanese'
        elif any(c in ['KR'] for c in origin_country):
            culture = 'korean'
        elif any(c in ['US', 'CA'] for c in origin_country):
            culture = 'western'
        elif any(c in ['FR', 'GB', 'DE', 'IT', 'ES'] for c in origin_country):
            culture = 'european'
        else:
            culture = 'other'

        # 제작사 분류
        studio = 'other'
        company_str = ' '.join(production_companies).lower()
        if 'ghibli' in company_str:
            studio = 'Ghibli'
        elif 'pixar' in company_str:
            studio = 'Pixar'
        elif 'dreamworks' in company_str:
            studio = 'DreamWorks'
        elif 'illumination' in company_str:
            studio = 'Illumination'
        elif 'warner' in company_str:
            studio = 'Warner'
        elif 'disney' in company_str:
            studio = 'Disney'

        results.append({
            'movieId': int(row['movieId']),
            'title': title,
            'poster': poster,
            'overview': overview,
            'culture': culture,
            'studio': studio,
            'production_companies': production_companies,
            'rating_count': int(row['rating_count']),
            'rating_mean': float(row['rating_mean']),
            'cluster': int(row['cluster']),
            'x': float(row['x']),
            'y': float(row['y'])
        })

        if i % 50 == 0:
            print(f"{i}/500 완료...")

        time.sleep(0.3)

    except Exception as e:
        print(f"오류 ({tmdb_id}): {e}")
        continue

os.makedirs('output', exist_ok=True)
with open('output/animations.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ 완료! 총 {len(results)}편 저장 → output/animations.json")