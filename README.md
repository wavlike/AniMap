# AniMap 🎬

**애니메이션 탐색형 추천 시스템** — 태그 기반 추천과 2D 맵 시각화를 통한 새로운 애니메이션 발견 경험

MovieLens 25M 데이터셋의 크라우드소싱 태그와 TMDb 메타데이터를 결합해, 애니메이션 500편을 2D 지도 위에 배치하고
**"왜 이 작품이 추천되었는지"** 를 설명하는 콘텐츠 기반 추천 웹 서비스입니다.

> 26-1 미래컨셉스튜디오 기말 프로젝트

---

## 프로젝트 개요

### 배경

- OTT 플랫폼이 늘어나면서 **콘텐츠 과부하 및 분산** 문제가 심화되었습니다.
- 일반 OTT 추천은 **왜 이 작품이 추천되었는지** 과정을 알기 어렵고, 같은 제작사·문화권 위주로 추천이 반복됩니다.
- 다양한 문화권/제작사의 애니메이션을 폭넓게 추천받을 수 있는 시스템이 필요합니다.

### 목표

- 사용자의 취향을 분석해 **클러스터(제작사·문화권)** 와 **태그 유사도** 를 기반으로 애니메이션을 추천
- 애니메이션을 **2D 공간에 배치**해, 취향을 중심으로 다른 문화권/제작사의 작품까지 탐색할 수 있는 **탐색형 추천 시스템** 제공

### 선행 사례 분석

| 서비스 | 추천 방식 |
|--------|-----------|
| Netflix | 사용자 행동 데이터 기반 개인화 추천, 실시간 추천 및 지속적 학습 |
| YouTube | 사용자 행동을 '신호'로 수집·분석, 단일 지표가 아닌 복합 신호 기반 모델 |
| Spotify | 에디토리얼 큐레이션 + 머신러닝 기반 개인화 알고리즘 결합 |
| **AniMap** | 평가 즉시 추천 결과를 시각화, MovieLens 크라우드소싱 태그 기반 알고리즘, 태그 빈도를 품질 지표로 활용 |

### 기존 서비스와의 차별점

| 항목 | 기존 OTT/플랫폼 | AniMap |
|------|----------------|--------|
| 추천 방식 | 목록형 스크롤 추천 | **2D 지도 기반 탐색** |
| 추천 범위 | 같은 제작사/문화권 중심 | **제작사/문화권 교차 추천** |
| 추천 이유 | 제공되지 않음 | **공통 태그 및 특성 설명** |
| 필터 기능 | 장르, 연도 등 기본 필터 | 주연 성별, 스타일(2D/3D), 테마 등 확장 필터 |
| 사용자 경험 | 수동적 소비 | 능동적 탐색 및 발견 |
| 시각화 | 없음 | 2D 맵으로 유사도를 직관적으로 표현 |

---

## 주요 기능

- **지도형 탐색** (`/map`): 500편을 PCA 2D 좌표에 배치하고 클러스터별 색상으로 표시. 내가 좋아한 작품(liked)과 추천 작품(rec)을 강조
- **콘텐츠 기반 추천** (`/api/recommend`): 태그 벡터 코사인 유사도 70% + 제작사·문화권 다양성 30%
- **추천 이유 설명** (`/api/match/<id>`): 좋아한 작품들과의 평균 유사도 및 **공통 태그** 제공
- **취향 분석** (`/analyze`): 평점 가중 태그 점수로 6가지 감정 축(따뜻함·깊이·경이로움·성장·우울함·모험)과 대표 태그 Top 8 산출
- **확장 필터**: 여성 주연, 2D/3D, 장르 기반 테마(성장·모험·판타지·가족·로맨스·코미디·드라마·음악·SF)
- **회원 기능**: 회원가입/로그인(Werkzeug 비밀번호 해시), 평점 저장, 보고 싶은 작품(watchlist), 마이페이지

## 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| Backend | Python 3, Flask, Flask Session, Werkzeug |
| Data | pandas, NumPy, scikit-learn |
| Frontend | HTML5, CSS3, JavaScript (ES6), SVG, Fetch API, LocalStorage |
| DB | SQLite3 (회원 정보) |
| 외부 데이터 | [MovieLens 25M](https://grouplens.org/datasets/movielens/25m/) (평점 2,500만 건 / 태그 110만 건), [TMDb API](https://developer.themoviedb.org/) (포스터, 줄거리, 제작사, 제작 국가) |

### 시스템 구조

```
사용자(웹 브라우저)
   │  Fetch API / LocalStorage
   ▼
Flask 서버 (app.py) ──────────► SQLite (users.db: 회원 정보, 평점, watchlist)
   │
   ▼
추천 엔진 (Python) ◄─────────── 데이터 저장소 (output/)
   │                              ├─ animations.json   작품 메타데이터 + 클러스터 + 2D 좌표
   ▼                              ├─ cosine_sim.npy    500×500 코사인 유사도 행렬
추천 결과 생성                    └─ tag_vectors.csv   500편 × 500태그 벡터
```

---

## 데이터 파이프라인 (`scripts/`)

### 전체 흐름

```
 MovieLens 25M                                                   TMDb API
 (movies / ratings / tags / links)                                   │
        │                                                            │
        ▼                                                            │
 [01] 애니메이션 필터링 ──► top500_anime.csv                          │
        │                                                            │
        ▼                                                            │
 [02] 태그 정제·선별 ────► top500_tags.csv                            │
        │                                                            │
        ▼                                                            │
 [03] 태그 벡터 생성 ────► tag_vectors.csv (500편 × 500태그)          │
        │                                                            │
        ├──────────────────────────────────────────┐                 │
        ▼                                          ▼                 ▼
 [04] 클러스터링 + PCA 2D 좌표  ◄──────────  [06] TMDb 메타데이터 수집
      ──► animations.json (cluster, x, y)        ──► animations.json (poster, overview, studio, culture)
        │
        ▼
 [05] 코사인 유사도 행렬 ──► cosine_sim.npy
        │
        ▼
 app.py (Flask) 에서 로드하여 추천·지도·분석 API 제공

 [07] 화풍(스타일) 분류 ──► movies_with_style.csv   (보조 스크립트)
```

| 단계 | 스크립트 | 입력 | 출력 | 핵심 처리 |
|------|----------|------|------|-----------|
| 01 | `01_filter_anime.py` | `movies.csv`, `ratings.csv` | `top500_anime.csv` | Animation 장르 + 평점 수 Top 500 |
| 02 | `02_process_tags.py` | `tags.csv`, `top500_anime.csv` | `top500_tags.csv` | 정규화, 불용어 제거, 빈도 Top 500 태그 |
| 03 | `03_tag_vectors.py` | `tags.csv`, `top500_*.csv` | `tag_vectors.csv` | 영화 × 태그 빈도 행렬 |
| 04 | `04_clustering.py` | `animations.json`, `tag_vectors.csv` | `animations.json`, `top500_with_clusters.csv` | 규칙 기반 7개 클러스터 + PCA 2D 좌표 |
| 05 | `05_recommend.py` | `animations.json`, `tag_vectors.csv` | `cosine_sim.npy` | 코사인 유사도 행렬, 추천 함수 검증 |
| 06 | `06_tmdb_fetch.py` | `top500_with_clusters.csv`, `links.csv` | `animations.json` | TMDb 포스터/줄거리, 제작사·문화권 분류 |
| 07 | `07_classify_style.py` | `top500_anime.csv` | `movies_with_style.csv` | 제작사 기반 화풍 분류 |

---

### 01. 애니메이션 필터링 — `01_filter_anime.py`

MovieLens 25M에서 추천 대상이 될 애니메이션 500편을 선정합니다.

1. `movies.csv`에서 `genres`에 **`Animation`** 이 포함된 작품만 추출
2. `ratings.csv`를 `movieId`로 그룹화해 **평점 개수(`rating_count`)** 와 **평균 평점(`rating_mean`)** 계산 후 병합
3. `rating_count` 기준 **상위 500편** 선택 → 충분한 사용자 반응(=태그)이 쌓인 작품 위주로 데이터 품질 확보

- **출력** `output/top500_anime.csv` — `movieId, title, genres, rating_count, rating_mean`

### 02. 태그 전처리 및 정제 — `02_process_tags.py`

태그 벡터는 **내용 기반 유사도** 계산에 쓰이므로, 작품 내용과 무관한 태그를 제거하는 것이 핵심입니다.

1. `tags.csv`에서 Top 500 애니메이션에 달린 태그만 필터링
2. 소문자 변환 + 앞뒤 공백 제거로 표기 통일 (`Funny` / `funny ` → `funny`)
3. 불용어(stopwords) 제거

   | 분류 | 예시 | 제거 이유 |
   |------|------|-----------|
   | 주관적 평가어 | `good`, `boring`, `favorite`, `seen`, `classic` | 내용이 아닌 개인 평가 |
   | 제작사 | `pixar`, `disney`, `studio ghibli`, `dreamworks`, `laika` | 클러스터 기준으로만 사용 |
   | 나라/문화권 | `japan`, `japanese`, `british`, `french`, `korean` | 클러스터 기준으로만 사용 |
   | 감독/인물 | `hayao miyazaki`, `makoto shinkai`, `mamoru hosoda` | 제작사 정보와 중복 |
   | 포맷/매체 | `animation`, `anime`, `stop motion`, `3d animation` | 모든 작품 공통 / 내용과 무관 |

4. 남은 태그를 빈도순으로 정렬해 **상위 500개 태그** 선별

- **출력** `output/top500_tags.csv` — `tag, count` (예: `funny 769`, `surreal 524`, ...)

> **제작사·문화권 태그를 벡터에서 뺀 이유**: 이 태그들이 남아 있으면 "같은 지브리 작품"끼리만 유사도가 높아져
> 교차 추천이 불가능해집니다. 그래서 이 정보는 **클러스터(04)와 다양성 점수(05)** 에서만 쓰고, 태그 벡터는 순수하게
> 작품의 분위기·테마·내용만 표현하도록 분리했습니다. 등장인물 이름 태그 등은 AI 보조 + 수동 검토로 추가 정리했습니다
> (`scripts/test.py`는 키워드 포함 여부로 태그를 걸러 보던 실험용 스크립트, `result.txt`는 제거 대상 태그 빈도 집계 결과입니다).

### 03. 태그 벡터 생성 — `03_tag_vectors.py`

각 작품을 500차원 태그 벡터로 표현합니다.

1. Top 500 애니메이션의 태그를 다시 정규화(소문자·strip)
2. `pd.crosstab(movieId, tag)`로 **영화 × 태그 빈도 행렬** 생성 — 값은 해당 태그를 단 사용자 수
3. 열을 `top500_tags.csv`의 500개 태그 순서로, 행을 Top 500 영화 순서로 `reindex` (없는 값은 0)

- **출력** `output/tag_vectors.csv` — 500행(영화) × 500열(태그)
- 태그 빈도가 높을수록 많은 사용자가 동의한 특성이므로, **태그 빈도 자체가 품질/신뢰도 지표** 역할을 합니다.

### 04. 클러스터링 + 2D 좌표 — `04_clustering.py`

#### 시도 1 — KMeans (실패)

처음에는 KMeans로 비슷한 태그 패턴끼리 6개 그룹으로 묶었으나 **클러스터 0에 481편이 몰리는** 결과가 나왔습니다.

- 메이저 작품은 다양한 태그를 갖지만, 마이너 작품은 태그가 거의 없어 **벡터가 0에 가까움** → 한 군집으로 뭉침
- 묶이더라도 감정 위주로만 나뉘어 서비스에서 의미 있는 그룹이 되지 못함

#### 수정 — 규칙 기반 7개 클러스터

`animations.json`의 `studio`, `culture` 값을 보고 **제작사 → 문화권 순서로** 클러스터 번호를 직접 부여합니다.

| 우선순위 | 조건 | 클러스터 | 이름 | 편수 |
|---------|------|:-------:|------|-----:|
| 1 | studio = Ghibli | 0 | Ghibli | 20 |
| 1 | studio = Pixar | 1 | Pixar | 35 |
| 1 | studio = Disney | 2 | Disney | 90 |
| 1 | studio ∈ {DreamWorks, Illumination, Warner} | 3 | DreamWorks/서양 | 83 |
| 2 | studio = other 이고 culture = japanese | 4 | 일본(기타) | 59 |
| 2 | studio = other 이고 culture = european | 5 | 유럽 | 39 |
| 3 | 해당 없음 | 6 | 기타 | 174 |

#### PCA 2D 지도 좌표

- 태그 벡터를 `PCA(n_components=2, random_state=42)`로 **2차원으로 압축** → 각 작품의 `x`, `y` 좌표
- 태그가 비슷한 작품은 지도 위에서 **인접하게 배치**되며, 사용자는 지도를 이동하며 작품을 탐색
- 축 해석(대략적 경향): **X축** 밝고 유쾌함 ↔ 어둡고 진지함 / **Y축** 환상·모험 ↔ 현실·일상

- **출력** `output/animations.json` (`cluster`, `x`, `y` 갱신), `output/top500_with_clusters.csv`

### 05. 추천 알고리즘 + 유사도 행렬 — `05_recommend.py`

1. `animations.json` 순서에 맞춰 태그 벡터를 정렬
2. `sklearn.metrics.pairwise.cosine_similarity`로 **500 × 500 코사인 유사도 행렬** 계산
3. 추천 함수를 테스트 케이스(센과 치히로의 행방불명, 인사이드 아웃)로 검증
4. 행렬을 캐싱해 서버 실행 시 매번 계산하지 않도록 함

- **출력** `output/cosine_sim.npy`

#### 최종 추천 스코어 (`app.py`의 `recommend()`)

```
Score = 0.7 × Similarity + 0.3 × Diversity
```

| 구성 요소 | 비중 | 계산 방식 |
|-----------|:----:|-----------|
| 태그 유사도 | 70% | 사용자가 좋아한 작품들과 후보 작품 간 **코사인 유사도의 평균** |
| 다양성 점수 | 30% | 후보의 **제작사**가 좋아한 작품들과 다르면 +0.5, **문화권**이 다르면 +0.5 (최대 1.0) |

후처리:
- 이미 좋아한 작품은 점수를 `-1`로 만들어 제외
- 제목에서 `:`·`(` 앞부분(최대 20자)을 시리즈명으로 보고 **같은 시리즈는 1편만** 남김 (예: Toy Story 2, 3 중복 방지)
- 상위 12편 반환

→ **태그가 비슷하면서도 새로운 스튜디오·문화권의 작품이 높은 점수**를 받는 구조입니다.

> `05_recommend.py` 내부에는 실험 단계의 `태그 50% + 협업 필터링 30% + 다양성 20%` 버전이 남아 있지만,
> 사용자 평점 데이터가 부족해 협업 필터링은 서비스(`app.py`)에서 제외하고 `0.7 / 0.3` 가중치를 사용합니다.

### 06. TMDb 메타데이터 수집 — `06_tmdb_fetch.py`

1. `links.csv`의 `tmdbId`로 MovieLens ↔ TMDb 작품 매칭
2. `GET /3/movie/{tmdbId}?language=ko-KR` 호출 (요청 간 0.3초 대기)
3. 수집 항목: 포스터(`w300`), 한국어 줄거리, 제작 국가, 제작사 목록
4. **문화권 분류** (`origin_country`)

   | 국가 코드 | culture |
   |-----------|---------|
   | JP | japanese |
   | KR | korean |
   | US, CA | western |
   | FR, GB, DE, IT, ES | european |
   | 그 외 | other |

5. **제작사 분류** (`production_companies` 문자열 포함 여부, 위에서부터 우선 적용)
   `ghibli` → Ghibli, `pixar` → Pixar, `dreamworks` → DreamWorks, `illumination` → Illumination, `warner` → Warner, `disney` → Disney, 그 외 → other

- **출력** `output/animations.json` — `movieId, title, poster, overview, culture, studio, production_companies, rating_count, rating_mean, cluster, x, y`

### 07. 화풍(스타일) 분류 — `07_classify_style.py`

TMDb 검색 API(제목 + 개봉연도)로 작품을 찾고 제작사에 따라 화풍을 매핑합니다.

| 제작사 | 화풍 |
|--------|------|
| Pixar | 3D_realistic |
| Walt Disney Animation, DreamWorks | 3D_cartoon |
| Studio Ghibli, Studio Chizu | 2D_watercolor |
| Kyoto Animation, CoMix Wave Films | 2D_digital |
| Laika | stop_motion |
| 그 외 | unknown |

- **출력** `output/movies_with_style.csv`
- ⚠️ 이 스크립트만 경로가 `../output/` 기준이므로 `scripts/` 폴더 안에서 실행해야 합니다.

### 서비스에서 추가로 쓰이는 파생 데이터 (`app.py`)

- **여성 주연 필터**: `female protagonist`, `strong female lead`, `strong female character`, `heroine` 태그가 하나라도 있는 작품 (현재 26편, `female_movies.txt`)
- **취향 분석 감정 축**: 감정별 키워드 태그(예: 따뜻함 = family, friendship, cute, funny, heartwarming)에 대해 평점 가중 태그 빈도를 합산 후 최댓값으로 정규화
- **추천 이유**: 대상 작품과 좋아한 작품들의 태그 벡터에서 값이 0보다 큰 태그의 교집합 → 공통 태그로 표시

---

## 로컬 실행

```bash
# 1. 의존성 설치
pip install flask pandas numpy scikit-learn werkzeug requests

# 2. MovieLens 25M 다운로드 후 data/ml-25m/ 에 압축 해제
#    (movies.csv, ratings.csv, tags.csv, links.csv 필요)

# 3. 파이프라인 실행 (프로젝트 루트에서)
python scripts/01_filter_anime.py
python scripts/02_process_tags.py
python scripts/03_tag_vectors.py
python scripts/06_tmdb_fetch.py      # TMDb 메타데이터 → animations.json
python scripts/04_clustering.py      # 클러스터 + PCA 좌표 → animations.json 갱신
python scripts/05_recommend.py       # cosine_sim.npy 생성
(cd scripts && python 07_classify_style.py)   # 선택

# 4. 서버 실행 → http://127.0.0.1:5000
python app.py
```

> **실행 순서 주의**: `06_tmdb_fetch.py`는 `top500_with_clusters.csv`(04의 출력)를 읽고, `04_clustering.py`는
> `animations.json`(06의 출력)을 읽는 **상호 의존** 구조입니다. 저장소의 `output/`에 이미 결과물이 포함되어 있으므로
> 그대로 `python app.py`만 실행해도 동작하며, 처음부터 재생성할 때는 06이 요구하는 `cluster, x, y` 컬럼을 가진
> 임시 `top500_with_clusters.csv`를 먼저 만든 뒤 06 → 04 → 05 순서로 실행하세요.

> **TMDb API 키**는 `scripts/06_tmdb_fetch.py`, `scripts/07_classify_style.py`의 `TMDB_API_KEY` 변수에 입력하세요.
> `users.db`(SQLite)는 서버 첫 실행 시 자동 생성됩니다.

## 배포 (Render)

Flask 서버이므로 GitHub Pages(정적 호스팅)로는 실행할 수 없고, GitHub 저장소와 연동되는 [Render](https://render.com)로 배포합니다.
저장소 루트의 `render.yaml`, `requirements.txt`에 설정이 들어 있습니다.

1. Render에 GitHub 계정으로 가입
2. **New → Blueprint** → `wavlike/AniMap` 저장소 선택 → **Apply**
3. 빌드가 끝나면 `https://animap-xxxx.onrender.com` 형태의 주소로 접속

- `main`에 push하면 자동으로 재배포됩니다.
- 무료 플랜은 15분간 접속이 없으면 잠들어, 다음 첫 접속 시 30초~1분 정도 걸립니다.
- 무료 플랜의 디스크는 재배포·재시작 시 초기화되므로 `users.db`(회원·평점 데이터)가 유지되지 않습니다. 회원 데이터를 계속 보관하려면 외부 DB(Supabase 등)로 옮겨야 합니다.

## 프로젝트 구조

```
AniMap/
├── app.py                    # Flask 메인 서버 (라우트, 추천·분석 API, 회원 DB)
├── scripts/                  # 데이터 전처리 파이프라인 (01 ~ 07)
│   └── test.py               # 태그 키워드 필터링 실험용
├── templates/                # Jinja2 HTML 템플릿 (index, rate, analyze, map, movie, mypage, login, signup ...)
├── static/                   # CSS, JS 정적 파일
├── output/                   # 전처리 결과물
│   ├── top500_anime.csv
│   ├── top500_tags.csv
│   ├── tag_vectors.csv
│   ├── top500_with_clusters.csv
│   ├── animations.json
│   └── cosine_sim.npy
├── female_movies.txt         # 여성 주연 태그 작품 목록
└── result.txt                # 제작사/문화권 태그 빈도 집계
```

## 성과 및 한계

**성과**
- ✓ 애니메이션 추천 시스템 구현 (콘텐츠 기반 필터링)
- ✓ PCA 기반 2D 지도 시각화
- ✓ 감정 축 기반 취향 분석
- ✓ 로그인 및 회원 정보(평점·watchlist) 저장

**현재 한계**
- 협업 필터링 미구현 (사용자 수 부족)
- OTT 플랫폼 제공 정보 미구현
- 여성 주연 데이터 부족 (태그 기반 26편)
- 태그가 적은 마이너 작품은 벡터가 희소해 유사도 정확도가 낮음

**향후 계획**
- 협업 필터링 추가 및 회원 시스템 고도화 (Supabase 연동)
- 화풍 등 다양한 분류 기준 추가
- OTT 시청 가능 정보 제공
