# 07_classify_style.py
import pandas as pd
import requests
import time

TMDB_API_KEY = "a4e7e71180d8f2bec20d54038eaa61bb"

# 제작사 → 화풍
STYLE_MAP = {
    "Pixar": "3D_realistic",
    "Walt Disney Animation": "3D_cartoon",
    "DreamWorks": "3D_cartoon",
    "Studio Ghibli": "2D_watercolor",
    "Studio Chizu": "2D_watercolor",
    "Kyoto Animation": "2D_digital",
    "CoMix Wave Films": "2D_digital",
    "Laika": "stop_motion",
}

def get_tmdb_info(title, year=None):
    """제목으로 TMDb 정보 가져오기"""
    # 1. 검색
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": title}
    if year:
        params["year"] = year
    
    try:
        results = requests.get(search_url, params=params, timeout=5).json()
        if not results.get('results'):
            return None
        
        movie_id = results['results'][0]['id']
        
        # 2. 상세 정보
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        detail = requests.get(detail_url, params={"api_key": TMDB_API_KEY}, timeout=5).json()
        
        companies = [c['name'] for c in detail.get('production_companies', [])]
        
        # 3. 화풍 분류
        for company in companies:
            for key in STYLE_MAP:
                if key in company:
                    return STYLE_MAP[key]
        return "unknown"
        
    except:
        return None

# 메인
df = pd.read_csv('../output/top500_anime.csv')
print(f"📊 {len(df)}편 처리 시작\n")

styles = []
for i, row in df.iterrows():
    title = row['title']
    
    # 연도 추출
    year = None
    if '(' in title:
        try:
            year = int(title.split('(')[-1].split(')')[0])
            title = title.split('(')[0].strip()
        except:
            pass
    
    # API 호출
    style = get_tmdb_info(title, year)
    styles.append(style)
    
    if (i + 1) % 50 == 0:
        print(f"진행: {i+1}/{len(df)}")
    
    time.sleep(0.3)

# 결과 저장
df['style'] = styles

print("\n📊 화풍 분포:")
print(df['style'].value_counts())

df.to_csv('../output/movies_with_style.csv', index=False)
print("\n✅ 완료!")