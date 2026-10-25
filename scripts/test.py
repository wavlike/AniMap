import pandas as pd

tags = pd.read_csv('../data/ml-25m/tags.csv')

# 지울 태그 (제작사, 문화권, 배우, 기술 관련)
remove_keywords = [
    'pixar', 'disney', 'ghibli', 'dreamworks', 'illumination',
    'japanese', 'korean', 'american', 'english', 'french',
    'actor', 'actress', 'director', 'writer',
    'blu-ray', 'dvd', 'collection', 'watched', 'favorite',
    'seen', 'own', '3d'
]

# 필터링
def should_keep(tag):
    tag_lower = str(tag).lower()
    for keyword in remove_keywords:
        if keyword in tag_lower:
            return False
    return True

tags_clean = tags[tags['tag'].apply(should_keep)]

# 저장
tags_clean.to_csv('../data/ml-25m/tags_clean.csv', index=False)

print(f"원본: {len(tags)}")
print(f"정리 후: {len(tags_clean)}")