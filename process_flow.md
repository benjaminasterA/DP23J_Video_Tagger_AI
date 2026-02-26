# ⚙️ 공정도 (Process Flow)

## 1. 사용자 워크플로우 (User Workflow)

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Front as 프론트엔드 (UI)
    participant Back as 백엔드 (AI/Logic)

    User->>Front: 1. 영상 업로드 & FPS 설정
    Front->>Back: 2. 모델 로드 & 인덱싱 요청
    Back->>Back: 프레임 추출 및 벡터 변환
    Back-->>Front: 3. 인덱싱 완료 데이터 반환
    User->>Front: 4. 자연어 검색어 입력
    Front->>Back: 5. 유사도 검색 요청
    Back-->>Front: 6. 상위 결과 리스트 반환
    User->>Front: 7. 장면 이동 & 태깅
    Front->>Front: 8. 태그 목록 업데이트 & 데이터 저장
```

## 2. 데이터 흐름도 (Data Flow)

### 2.1. 인덱싱 흐름 (Indexing Flow)
1. **Input**: Raw Video File
2. **Process**: 
   - Decoded Frames (CV2)
   - Image Normalization (PIL)
   - Feature Extraction (CLIP)
3. **Output**: Latent Space Vectors (Embedding)

### 2.2. 검색 흐름 (Search Flow)
1. **Query**: "A person in red glasses" (Text or Image)
2. **Encoding**: Query $\rightarrow$ Embedding Vector
3. **Comparison**: Vector Similarity Calculation (Dot Product)
4. **Ranking**: Sort by Score $\rightarrow$ Timestamp mapping
5. **UI Update**: Result Card Display with "Jump to Scene"

## 3. 탭 내비게이션 자동화 흐름 (Tab Automation)
- **Trigger**: AI 검색 결과의 `👉 장면 이동` 버튼 클릭
- **Action**:
  1. `st.session_state.start_time` 업데이트
  2. `st.session_state.active_tab`을 '수동 태깅'으로 설정
  3. `st.rerun()` 호출을 통해 즉시 탭 이동 및 비디오 시간 동기화
