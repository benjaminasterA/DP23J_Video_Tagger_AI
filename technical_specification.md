# 📜 기술시방서 (Technical Specification)

## 1. 기술 스택 (Technology Stack)
- **언어**: Python 3.10+
- **프레임워크**: Streamlit
- **AI 라이브러리**: Sentence-Transformers, Torch
- **영상 처리**: OpenCV (cv2)
- **데이터 처리**: Pandas, Numpy

## 2. API 및 주요 함수 명세 (Function Specification)

### 2.1. `load_model()`
- **역할**: CLIP 모델 로드 및 캐싱
- **반환값**: `SentenceTransformer` 객체
- **제약 사항**: 첫 실행 시 모델 다운로드 시간 필요 (약 600MB)

### 2.2. `extract_frames_and_embeddings(video_path, model, progress_callback)`
- **역할**: 영상 전처리 및 벡터 인덱싱
- **입력**: 영상 경로, 모델 객체, 진행률 콜백 함수
- **정밀도**: 사용자 설정 FPS에 따라 프레임 샘플링 수행
- **반환값**: `(list[dict], int)` - 인덱스 데이터 및 총 재생 시간

### 2.3. `search_similar_frames(query, frame_index, model, is_image)`
- **역할**: 쿼리 기반 시맨틱 검색
- **입력**: 텍스트 또는 이미지 경로, 인덱스 리스트, 모델 객체
- **알고리즘**: Cosine Similarity (Vector Dot Product)
- **반환값**: 유사도 점수 기준 내림차순 정렬된 검색 결과 (Top-K)

## 3. 기술적 제약 및 요구 사항 (Constraints)

### 3.1. 하드웨어 요구 사항
- **RAM**: 최소 8GB (안정적 동작을 위해 16GB 권장)
- **GPU**: CUDA 지원 시 성능 대폭 향상 (CPU 단독 동작 가능)

### 3.2. 네트워크 제약
- 모델 최초 로드 시 HuggingFace 서버 연결 필요

### 3.3. 영상 호맷 제약
- FFmpeg 지원 포맷 권장 (mp4, mov, avi, webm 등)
- 고해상도(4K 이상) 영상의 경우 인덱싱 속도가 저하될 수 있음

## 4. 보안 및 안정성 (Security & Stability)
- **임시 파일 처리**: `tempfile` 모듈을 통한 보안 임시 경로 사용 및 프로세스 종료 시 자동 삭제
- **예외 처리**: 모델 미로드 시 검색 차단, 영상 파일 부재 시 에러 핸들링 등 Robust 설계 적용
