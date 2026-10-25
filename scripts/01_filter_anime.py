import pandas as pd
import os

movies = pd.read_csv('data/ml-25m/movies.csv')
ratings = pd.read_csv('data/ml-25m/ratings.csv')

anime = movies[movies['genres'].str.contains('Animation', na=False)]
print(f"애니메이션 전체: {len(anime)}편")

rating_counts = ratings.groupby('movieId').size().reset_index(name='rating_count')
rating_means = ratings.groupby('movieId')['rating'].mean().reset_index(name='rating_mean')

anime = anime.merge(rating_counts, on='movieId', how='left')
anime = anime.merge(rating_means, on='movieId', how='left')

top500 = anime.nlargest(500, 'rating_count')

os.makedirs('output', exist_ok=True)
top500.to_csv('output/top500_anime.csv', index=False)
print(f"상위 500편 저장 완료")