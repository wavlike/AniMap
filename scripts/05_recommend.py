import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import json
import os

with open('output/animations.json', encoding='utf-8') as f:
    animations = json.load(f)

df = pd.DataFrame(animations)
tag_vectors = pd.read_csv('output/tag_vectors.csv', index_col=0)

# movieId 순서 맞추기
df = df.set_index('movieId')
tag_vectors = tag_vectors.reindex(df.index, fill_value=0)
df = df.reset_index()

movie_ids = df['movieId'].tolist()
n_movies = len(df)

# 코사인 유사도 계산
tag_matrix = tag_vectors.values
cosine_sim = cosine_similarity(tag_matrix)

# KNN 초기화
knn = NearestNeighbors(n_neighbors=10, metric='cosine')
knn.fit(np.random.rand(100, n_movies))

def recommend(liked_movie_ids, user_rating_vec=None, top_n=10):
    liked_indices = [movie_ids.index(mid) for mid in liked_movie_ids if mid in movie_ids]
    if not liked_indices:
        return []

    # 태그 유사도 (50%)
    tag_scores = cosine_sim[liked_indices].mean(axis=0)

    # 협업 필터링 (30%)
    if user_rating_vec is not None:
        cf_scores = np.array(user_rating_vec)
        cf_scores = cf_scores / cf_scores.max() if cf_scores.max() > 0 else cf_scores
    else:
        cf_scores = np.zeros(n_movies)

    # 다양성 (20%) - 제작사 + 문화권 기준
    liked_studios = df.iloc[liked_indices]['studio'].tolist()
    liked_cultures = df.iloc[liked_indices]['culture'].tolist()

    diversity_scores = []
    for _, row in df.iterrows():
        score = 0
        if row['studio'] not in liked_studios:
            score += 0.5
        if row['culture'] not in liked_cultures:
            score += 0.5
        diversity_scores.append(score)
    diversity_scores = np.array(diversity_scores)

    # 최종 점수
    final_scores = (0.5 * tag_scores) + (0.3 * cf_scores) + (0.2 * diversity_scores)

    for idx in liked_indices:
        final_scores[idx] = -1

    top_indices = final_scores.argsort()[::-1]
    seen_series = []
    filtered_indices = []
    for idx in top_indices:
        title = df.iloc[idx]['title'].split(':')[0].split('(')[0].strip()[:20]
        if title not in seen_series:
            seen_series.append(title)
            filtered_indices.append(idx)
        if len(filtered_indices) == top_n:
            break
    return df.iloc[filtered_indices].to_dict(orient='records')

# 테스트
spirited = df[df['title'].str.contains('Spirited', na=False)]['movieId'].values
if len(spirited) > 0:
    print("센과 치히로 좋아하는 사용자 추천")
    results = recommend([spirited[0]])
    for r in results:
        print(f"  [{r['studio']} / {r['culture']}] {r['title']} (평점: {r['rating_mean']:.2f})")

inside_out = df[df['title'].str.contains('Inside Out', na=False)]['movieId'].values
if len(inside_out) > 0:
    print("인사이드 아웃 좋아하는 사용자 추천")
    results = recommend([inside_out[0]])
    for r in results:
        print(f"  [{r['studio']} / {r['culture']}] {r['title']} (평점: {r['rating_mean']:.2f})")

# 캐싱
np.save('output/cosine_sim.npy', cosine_sim)
print("추천 알고리즘 업데이트 완료")