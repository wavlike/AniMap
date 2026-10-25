import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
import json
import os

with open('output/animations.json', encoding='utf-8') as f:
    animations = json.load(f)

df = pd.DataFrame(animations)
tag_vectors = pd.read_csv('output/tag_vectors.csv', index_col=0)

df = df.set_index('movieId')
tag_vectors = tag_vectors.reindex(df.index, fill_value=0)
df = df.reset_index()

# 제작사 + 문화권 기준으로 클러스터 수동 지정
def assign_cluster(row):
    studio = row['studio']
    culture = row['culture']
    if studio == 'Ghibli':
        return 0
    elif studio == 'Pixar':
        return 1
    elif studio == 'Disney':
        return 2
    elif studio in ['DreamWorks', 'Illumination', 'Warner']:
        return 3
    elif culture == 'japanese':
        return 4
    elif culture == 'european':
        return 5
    else:
        return 6

df['cluster'] = df.apply(assign_cluster, axis=1)

# PCA로 2D 좌표 생성
pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(tag_vectors)
df['x'] = coords[:, 0]
df['y'] = coords[:, 1]

# animations.json 업데이트
for movie in animations:
    row = df[df['movieId'] == movie['movieId']]
    if not row.empty:
        movie['cluster'] = int(row.iloc[0]['cluster'])
        movie['x'] = float(row.iloc[0]['x'])
        movie['y'] = float(row.iloc[0]['y'])

with open('output/animations.json', 'w', encoding='utf-8') as f:
    json.dump(animations, f, ensure_ascii=False, indent=2)

df.to_csv('output/top500_with_clusters.csv', index=False)

# 클러스터별 분포 확인
cluster_names = {0: 'Ghibli', 1: 'Pixar', 2: 'Disney', 3: 'DreamWorks/기타서양', 4: '일본(기타)', 5: '유럽', 6: '기타'}
clusters = {}
for m in animations:
    c = m['cluster']
    clusters[c] = clusters.get(c, 0) + 1

print("클러스터별 분포:")
for c in sorted(clusters.keys()):
    print(f"  클러스터 {c} ({cluster_names[c]}): {clusters[c]}편")

print("완료")