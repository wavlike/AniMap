import pandas as pd
import os

tags = pd.read_csv('data/ml-25m/tags.csv')
top500 = pd.read_csv('output/top500_anime.csv')

# 애니메이션 500편에 해당하는 태그만 필터링
anime_ids = set(top500['movieId'])
tags = tags[tags['movieId'].isin(anime_ids)]

# 소문자 변환 & 공백 제거
tags['tag'] = tags['tag'].str.lower().str.strip()

# 무의미한 태그 제거
stopwords = [
    # 주관적 평가어
    'seen', 'watched', 'good', 'bad', 'great', 'excellent', 'amazing',
    'favorite', 'favourite', 'boring', 'awful', 'terrible', 'nice',
    'cool', 'best', 'worst', 'old', 'new', 'classic',
    # 제작사
    'pixar', 'disney', 'studio ghibli', 'dreamworks', 'illumination',
    'aardman', 'aardman studios', 'disney animated feature', 'disney classics',
    'disney renaissance', 'pixar animation', 'dreamworks animation',
    'warner bros', 'laika', 'animation studio',
    # 나라/문화권
    'japan', 'japanese', 'british', 'french', 'american', 'korean',
    'chinese', 'european', 'japanese influence', 'british comedy',
    # 감독/인물
    'hayao miyazaki', 'miyazaki', 'makoto shinkai', 'mamoru hosoda',
    'woman director', 'directorial debut',
    # 포맷/매체 정보 (내용과 무관)
    'animation', 'animated', 'anime', 'computer animation',
    'stop motion', 'claymation', '3d animation', '2d animation',
]
tags = tags[~tags['tag'].isin(stopwords)]

# 빈도 기준 상위 500개 태그 선별
top_tags = tags['tag'].value_counts().head(500)

os.makedirs('output', exist_ok=True)
top_tags.to_csv('output/top500_tags.csv', header=True)
print(f"상위 500개 태그 저장 완료")
print(top_tags.head(20))