# AniMap 🎬

애니메이션 추천 웹 서비스 — MovieLens 25M 데이터셋 기반 콘텐츠 필터링 + 클러스터링

## 주요 기능

- **지도형 탐색**: 애니메이션을 클러스터별로 시각화한 인터랙티브 맵
- **콘텐츠 기반 추천**: 태그 벡터 코사인 유사도를 이용한 유사 작품 추천
- **장르 / 스타일 필터**: 클러스터 이름 기반 필터링
- **평점 & 마이페이지**: 로그인 후 작품 평가 및 맞춤 추천

## 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| Backend | Python 3, Flask |
| Data | pandas, NumPy, scikit-learn |
| Frontend | Vanilla JS, CSS |
| DB | SQLite |
| 데이터셋 | [MovieLens 25M](https://grouplens.org/datasets/movielens/25m/) |

## 데이터 파이프라인 (`scripts/`)

```
01_filter_anime.py      → 애니메이션 장르 필터링 (Top 500)
02_process_tags.py      → 태그 전처리 및 정제
03_tag_vectors.py       → TF-IDF 태그 벡터 생성
04_clustering.py        → KMeans 클러스터링
05_recommend.py         → 코사인 유사도 행렬 계산
06_tmdb_fetch.py        → TMDB API 포스터/메타데이터 수집
07_classify_style.py    → 스타일 분류
```

## 로컬 실행

```bash
# 의존성 설치
pip install flask pandas numpy scikit-learn werkzeug

# MovieLens 25M 데이터셋을 data/ml-25m/ 에 위치시킨 후 스크립트 순서대로 실행
python scripts/01_filter_anime.py
...
python scripts/07_classify_style.py

# 서버 실행
python app.py
```

> **Note**: `data/` 폴더(원본 데이터셋)와 `output/` 폴더(전처리 결과)는 직접 생성해야 합니다.
> TMDB API 키는 `scripts/06_tmdb_fetch.py` 내 `API_KEY` 변수에 입력하세요.

## 프로젝트 구조

```
anime_recommendation/
├── app.py                 # Flask 메인 서버
├── scripts/               # 데이터 전처리 파이프라인
├── templates/             # Jinja2 HTML 템플릿
├── static/                # CSS, JS 정적 파일
└── output/                # 전처리 결과물 (생성 필요)
```
