# -*- coding: utf-8 -*-
from flask import Flask, jsonify, render_template, request, session, redirect
import json
import sqlite3
import numpy as np
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'animap_secret_2024_!@#$'

DB_PATH = 'users.db'

# ── 데이터 로딩 ──────────────────────────────────────────────

with open('output/animations.json', encoding='utf-8') as f:
    animations = json.load(f)

df = pd.DataFrame(animations)
cosine_sim = np.load('output/cosine_sim.npy')
movie_ids = df['movieId'].tolist()

genres_df = pd.read_csv('output/top500_anime.csv')[['movieId', 'genres']]
df = df.merge(genres_df, on='movieId', how='left')
df['genres'] = df['genres'].fillna('')

tag_vectors_df = pd.read_csv('output/tag_vectors.csv', index_col=0)
tag_vectors_df.index = tag_vectors_df.index.astype(int)

CLUSTER_NAMES = {
    0: 'Ghibli', 1: 'Pixar', 2: 'Disney',
    3: 'DreamWorks/서양', 4: '일본(기타)', 5: '유럽', 6: '기타'
}

EMOTION_CLUSTERS = {
    '따뜻함': ['family', 'friendship', 'cute', 'funny', 'heartwarming'],
    '깊이':   ['emotional', 'thought provoking', 'dramatic', 'moving', 'psychological'],
    '경이로움': ['visually appealing', 'beautiful', 'dreamlike', 'surreal', 'atmospheric', 'fairy tale'],
    '성장':   ['coming of age', 'independent', 'growing up', 'identity'],
    '우울함': ['dark', 'sad', 'dystopia', 'melancholy', 'bittersweet'],
    '모험':   ['adventure', 'action', 'exciting', 'quest'],
}

EMOTION_COLORS = {
    '따뜻함': '#e07b54',
    '깊이':   '#6b7c8f',
    '경이로움': '#c9a84c',
    '성장':   '#5a8f6b',
    '우울함': '#9e9e9e',
    '모험':   '#7b6fa0',
}

TAG_KO = {
    'coming of age': '성장', 'emotional': '감성적', 'family': '가족',
    'fantasy': '판타지', 'independent': '독립', 'visually appealing': '시각적 아름다움',
    'thought provoking': '생각할 거리', 'friendship': '우정', 'adventure': '모험',
    'funny': '유머', 'beautiful': '아름다움', 'romance': '로맨틱', 'dark': '다크',
    'musical': '뮤지컬', 'sci-fi': 'SF', 'dystopia': '디스토피아',
    'atmospheric': '분위기있는', 'dreamlike': '몽환적', 'fairy tale': '동화',
    'surreal': '초현실적', 'cute': '귀여움', 'heartwarming': '따뜻함',
    'sad': '슬픔', 'melancholy': '우울', 'action': '액션',
    'talking animals': '동물', 'dramatic': '드라마틱', 'moving': '감동적',
}

_female_tags = {'female protagonist', 'strong female lead', 'strong female character', 'heroine'}
_female_ids = set(
    tag_vectors_df.index[tag_vectors_df[
        [t for t in _female_tags if t in tag_vectors_df.columns]
    ].sum(axis=1) > 0].tolist()
)

CONDITION_FILTER = {
    # is_3d 컬럼 기반: Pixar/Illumination=무조건 3D, Ghibli=무조건 2D, 나머지=CGI 점수 판별
    '여성':  lambda r: r.get('movieId') in _female_ids,
    '2D':   lambda r: not r.get('is_3d', False),
    '3D':   lambda r: bool(r.get('is_3d', False)),
    '성장':  lambda r: 'Drama' in r.get('genres', '') or 'Adventure' in r.get('genres', ''),
    '모험':  lambda r: 'Adventure' in r.get('genres', ''),
    '판타지': lambda r: 'Fantasy' in r.get('genres', ''),
    '가족':  lambda r: 'Children' in r.get('genres', ''),
    '로맨스': lambda r: 'Romance' in r.get('genres', ''),
    '코미디': lambda r: 'Comedy' in r.get('genres', ''),
    '드라마': lambda r: 'Drama' in r.get('genres', ''),
    '음악':  lambda r: 'Musical' in r.get('genres', ''),
    'SF':   lambda r: 'Sci-Fi' in r.get('genres', ''),
}

EXCLUDE_TAGS = {
    'animation', 'pixar', 'disney', 'anime', 'animated', 'studio ghibli',
    'hayao miyazaki', 'japan', 'computer animation', 'stop motion', 'claymation',
}


# ── 데이터베이스 ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, movie_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, movie_id)
    )''')
    conn.commit()
    conn.close()

init_db()


# ── 추천 알고리즘 ─────────────────────────────────────────────

def recommend(liked_movie_ids, top_n=12):
    liked_indices = [movie_ids.index(mid) for mid in liked_movie_ids if mid in movie_ids]
    if not liked_indices:
        return []

    tag_scores = cosine_sim[liked_indices].mean(axis=0)

    liked_studios = set(df.iloc[liked_indices]['studio'])
    liked_cultures = set(df.iloc[liked_indices]['culture'])

    diversity_scores = np.array([
        (0.5 if row['studio'] not in liked_studios else 0) +
        (0.5 if row['culture'] not in liked_cultures else 0)
        for _, row in df.iterrows()
    ])

    final_scores = (0.7 * tag_scores) + (0.3 * diversity_scores)
    for idx in liked_indices:
        final_scores[idx] = -1

    top_indices = final_scores.argsort()[::-1]
    seen_series, filtered_indices = [], []
    for idx in top_indices:
        title = df.iloc[idx]['title'].split(':')[0].split('(')[0].strip()[:20]
        if title not in seen_series:
            seen_series.append(title)
            filtered_indices.append(idx)
        if len(filtered_indices) == top_n:
            break

    return df.iloc[filtered_indices].to_dict(orient='records')


# ── 페이지 라우트 ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rate')
def rate():
    return render_template('rate.html')

@app.route('/analyze')
def analyze_page():
    return render_template('analyze.html')

@app.route('/map')
def map_page():
    return render_template('map.html')

@app.route('/movie/<int:movie_id>')
def movie_page(movie_id):
    return render_template('movie.html', movie_id=movie_id)


# ── 인증 라우트 ───────────────────────────────────────────────

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get('user_id'):
        return redirect('/')
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        password = request.form.get('password', '')
        if not nickname or not password:
            return render_template('signup.html', error='닉네임과 비밀번호를 입력해주세요')
        if len(nickname) < 2 or len(nickname) > 20:
            return render_template('signup.html', error='닉네임은 2~20자여야 해요')
        if len(password) < 4:
            return render_template('signup.html', error='비밀번호는 4자 이상이어야 해요')
        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO users (nickname, password_hash) VALUES (?, ?)',
                (nickname, generate_password_hash(password))
            )
            conn.commit()
            row = conn.execute('SELECT id FROM users WHERE nickname = ?', (nickname,)).fetchone()
            session['user_id'] = row['id']
            session['nickname'] = nickname
            return redirect('/')
        except sqlite3.IntegrityError:
            return render_template('signup.html', error='이미 사용 중인 닉네임이에요')
        finally:
            conn.close()
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect('/')
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        password = request.form.get('password', '')
        conn = get_db()
        row = conn.execute(
            'SELECT id, nickname, password_hash FROM users WHERE nickname = ?', (nickname,)
        ).fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            session['user_id'] = row['id']
            session['nickname'] = row['nickname']
            next_url = request.form.get('next', '').strip()
            # 외부 URL로의 오픈 리다이렉트 방지
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('/')
        return render_template('login.html', error='닉네임 또는 비밀번호가 틀렸어요')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/mypage')
def mypage():
    if not session.get('user_id'):
        return redirect('/login')
    return render_template('mypage.html')


# ── API ───────────────────────────────────────────────────────

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    if not session.get('user_id'):
        return jsonify({'error': 'not logged in'}), 401
    conn = get_db()
    rows = conn.execute(
        'SELECT movie_id, added_at FROM watchlist WHERE user_id = ? ORDER BY added_at DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    movie_map = {m['movieId']: m for m in animations}
    result = []
    for row in rows:
        movie = movie_map.get(row['movie_id'], {})
        if movie:
            result.append({
                'movieId': row['movie_id'],
                'title': movie.get('title', ''),
                'poster': movie.get('poster', ''),
                'studio': movie.get('studio', ''),
                'cluster': movie.get('cluster', 6),
                'added_at': row['added_at'],
            })
    return jsonify(result)


@app.route('/api/watchlist/<int:movie_id>', methods=['POST'])
def toggle_watchlist(movie_id):
    if not session.get('user_id'):
        return jsonify({'error': 'not logged in'}), 401
    conn = get_db()
    existing = conn.execute(
        'SELECT id FROM watchlist WHERE user_id = ? AND movie_id = ?',
        (session['user_id'], movie_id)
    ).fetchone()
    if existing:
        conn.execute('DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?',
                     (session['user_id'], movie_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'removed'})
    else:
        conn.execute('INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)',
                     (session['user_id'], movie_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'added'})


@app.route('/api/movies')
def get_movies():
    conditions = request.args.getlist('condition')
    result_df = df.copy()
    if conditions:
        mask = pd.Series([True] * len(result_df), index=result_df.index)
        for cond in conditions:
            fn = CONDITION_FILTER.get(cond)
            if fn:
                mask = mask & result_df.apply(fn, axis=1)
        filtered = result_df[mask]
        if len(filtered) >= 10:
            result_df = filtered
    total = len(result_df)
    sample = result_df.sort_values('rating_count', ascending=False).head(60).to_dict(orient='records')
    return jsonify({'total': total, 'movies': sample})


@app.route('/api/analyze', methods=['POST'])
def analyze_api():
    data = request.get_json()
    ratings = data.get('ratings', {})
    if not ratings:
        return jsonify({'error': 'no ratings'}), 400

    emotion_scores = {k: 0.0 for k in EMOTION_CLUSTERS}
    tag_scores = {}
    total_weight = sum(ratings.values()) or 1

    for mid_str, rating in ratings.items():
        mid = int(mid_str)
        weight = rating / total_weight
        if mid not in tag_vectors_df.index:
            continue
        tag_vec = tag_vectors_df.loc[mid]
        for emotion, keywords in EMOTION_CLUSTERS.items():
            for kw in keywords:
                if kw in tag_vec.index:
                    emotion_scores[emotion] += weight * float(tag_vec[kw])
        for tag, score in tag_vec.items():
            if float(score) > 0:
                tag_scores[tag] = tag_scores.get(tag, 0) + weight * float(score)

    max_e = max(emotion_scores.values()) or 1
    emotion_norm = {k: round(min(v / max_e, 1.0), 2) for k, v in emotion_scores.items()}

    top_tags = sorted(
        [(k, v) for k, v in tag_scores.items() if k not in EXCLUDE_TAGS and v > 0],
        key=lambda x: -x[1]
    )[:8]
    top_tags_ko = [{'en': t, 'ko': TAG_KO.get(t, t)} for t, _ in top_tags]

    return jsonify({
        'emotion_scores': emotion_norm,
        'emotion_colors': EMOTION_COLORS,
        'top_tags': top_tags_ko,
    })


@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    liked_ids = data.get('liked_ids', [])
    return jsonify(recommend(liked_ids))


@app.route('/api/save_ratings', methods=['POST'])
def save_ratings():
    if not session.get('user_id'):
        return jsonify({'error': 'not logged in'}), 401
    data = request.get_json()
    ratings = data.get('ratings', {})
    user_id = session['user_id']
    conn = get_db()
    for movie_id_str, rating in ratings.items():
        conn.execute(
            '''INSERT INTO user_ratings (user_id, movie_id, rating) VALUES (?, ?, ?)
               ON CONFLICT(user_id, movie_id) DO UPDATE SET rating=excluded.rating, rated_at=CURRENT_TIMESTAMP''',
            (user_id, int(movie_id_str), rating)
        )
    conn.commit()
    conn.close()
    return jsonify({'saved': len(ratings)})


@app.route('/api/my_ratings')
def my_ratings():
    if not session.get('user_id'):
        return jsonify({'error': 'not logged in'}), 401
    conn = get_db()
    rows = conn.execute(
        'SELECT movie_id, rating, rated_at FROM user_ratings WHERE user_id = ? ORDER BY rated_at DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()

    movie_map = {m['movieId']: m for m in animations}
    result = []
    for row in rows:
        movie = movie_map.get(row['movie_id'], {})
        if movie:
            result.append({
                'movieId': row['movie_id'],
                'title': movie.get('title', ''),
                'poster': movie.get('poster', ''),
                'rating': row['rating'],
                'rated_at': row['rated_at'],
                'studio': movie.get('studio', ''),
                'cluster': movie.get('cluster', 6),
            })
    return jsonify(result)


@app.route('/api/map')
def get_map():
    liked_ids = set(request.args.getlist('liked', type=int))
    rec_ids   = set(request.args.getlist('rec',   type=int))
    result = []
    for m in animations:
        mid = m['movieId']
        kind = 'liked' if mid in liked_ids else ('rec' if mid in rec_ids else 'other')
        result.append({
            'movieId': mid,
            'title': m['title'],
            'x': m.get('x', 0),
            'y': m.get('y', 0),
            'kind': kind,
            'cluster': m.get('cluster', 6),
            'poster': m.get('poster', ''),
        })
    return jsonify(result)


@app.route('/api/movie/<int:movie_id>')
def get_movie(movie_id):
    movie = next((m for m in animations if m['movieId'] == movie_id), None)
    if not movie:
        return jsonify({'error': 'not found'}), 404
    movie = dict(movie)
    row = df[df['movieId'] == movie_id]
    if not row.empty:
        movie['genres'] = row.iloc[0]['genres']
    return jsonify(movie)


@app.route('/api/match/<int:movie_id>', methods=['POST'])
def get_match(movie_id):
    data = request.get_json()
    liked_ids = data.get('liked_ids', [])

    if movie_id not in movie_ids:
        return jsonify({'match': 0, 'common_tags': [], 'diff': []})

    target_idx = movie_ids.index(movie_id)
    liked_indices = [movie_ids.index(mid) for mid in liked_ids if mid in movie_ids]
    if not liked_indices:
        return jsonify({'match': 0, 'common_tags': [], 'diff': []})

    avg_sim = float(cosine_sim[liked_indices, target_idx].mean())
    match_pct = int(min(avg_sim * 150 + 40, 99))

    common_tags = []
    if movie_id in tag_vectors_df.index:
        target_tags = set(tag_vectors_df.loc[movie_id][tag_vectors_df.loc[movie_id] > 0].index)
        for mid in liked_ids:
            if mid in tag_vectors_df.index:
                liked_tags = set(tag_vectors_df.loc[mid][tag_vectors_df.loc[mid] > 0].index)
                common_tags.extend(target_tags & liked_tags)
        common_tags = [
            {'en': t, 'ko': TAG_KO.get(t, t)}
            for t in list(set(common_tags) - EXCLUDE_TAGS)[:5]
        ]

    target_movie = df[df['movieId'] == movie_id].iloc[0]
    liked_df = df[df['movieId'].isin(liked_ids)]
    diff = []
    if not liked_df.empty:
        liked_studio = liked_df['studio'].mode()[0]
        liked_culture = liked_df['culture'].mode()[0]
        if target_movie['studio'] != liked_studio:
            diff.append(f"스튜디오: {liked_studio} → {target_movie['studio']}")
        if target_movie['culture'] != liked_culture:
            culture_ko = {'japanese': '일본', 'western': '서양', 'european': '유럽',
                          'korean': '한국', 'other': '기타'}
            diff.append(f"문화권: {culture_ko.get(liked_culture, liked_culture)} → {culture_ko.get(target_movie['culture'], target_movie['culture'])}")

    return jsonify({'match': match_pct, 'common_tags': common_tags, 'diff': diff})


@app.route('/api/styles')
def get_styles():
    cluster_counts = df['cluster'].value_counts().sort_index().to_dict()
    return jsonify(cluster_counts)


if __name__ == '__main__':
    app.run(debug=True)
