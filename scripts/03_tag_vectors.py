import pandas as pd
import os

top500 = pd.read_csv('output/top500_anime.csv')
tags = pd.read_csv('data/ml-25m/tags.csv')

# 애니메이션 500편 태그만
anime_ids = set(top500['movieId'])
tags = tags[tags['movieId'].isin(anime_ids)]
tags['tag'] = tags['tag'].str.lower().str.strip()

# 상위 500개 태그 목록
top_tags = pd.read_csv('output/top500_tags.csv', names=['tag', 'count'], header=0)
tag_list = top_tags['tag'].tolist()

# 영화별 태그 벡터 생성
tag_matrix = pd.crosstab(tags['movieId'], tags['tag'])
tag_matrix = tag_matrix.reindex(columns=tag_list, fill_value=0)
tag_matrix = tag_matrix.reindex(top500['movieId'], fill_value=0)

os.makedirs('output', exist_ok=True)
tag_matrix.to_csv('output/tag_vectors.csv')
print(f"태그 벡터 생성 완료 {tag_matrix.shape[0]}편 x {tag_matrix.shape[1]}태그")