# (필수 설치: pip install sentence-transformers torch opencv-python Pillow)
import cv2
import os
import torch
import logging
from PIL import Image
from sentence_transformers import SentenceTransformer, util

# 로깅 설정 (Logging Setup)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AI 모델 로딩 (캐싱 적용 - 싱글톤 패턴 형태)
_model_cache = None

def load_model():
    """
    SentenceTransformer CLIP 모델을 로드합니다.
    """
    global _model_cache
    if _model_cache is None:
        try:
            logger.info("Loading CLIP model: clip-ViT-B-32")
            _model_cache = SentenceTransformer('clip-ViT-B-32')
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    return _model_cache

# 영상에서 프레임을 추출하고 AI 임베딩(Embedding)으로 변환하는 핵심 함수
def extract_frames_and_embeddings(video_path, model, progress_callback=None):
    """
    영상을 분석하여 프레임별 임베딩과 전체 길이를 반환합니다.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return [], 0

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        return [], 0

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(total_frames / fps) if fps > 0 else 0
    
    frames_data = []
    current_frame_idx = -1
    
    # cap.set 지원 여부 확인을 위한 플래그
    use_fast_seek = True

    for t in range(0, duration, 1): 
        target_frame = int(t * fps)
        
        if progress_callback:
            progress_callback(t + 1, duration)
        
        # 효율적 프레임 건너뛰기 (Fast Seeking attempt)
        if use_fast_seek:
            success = cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            if not success:
                logger.warning("cap.set(CAP_PROP_POS_FRAMES) failed. Falling back to sequential seek.")
                use_fast_seek = False

        if not use_fast_seek:
            while current_frame_idx < target_frame - 1:
                if not cap.grab(): break
                current_frame_idx += 1
            
        ret, frame = cap.read()
        if not ret: 
            break
        current_frame_idx = target_frame
        
        try:
            # BGR -> RGB 변환 및 PIL 이미지 생성
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img)
            
            # CLIP 임베딩 생성 (No Grad로 속도 향상)
            with torch.no_grad():
                embedding = model.encode(pil_img, convert_to_tensor=True)
            frames_data.append({"ts": t, "embedding": embedding})
        except Exception as e:
            logger.warning(f"Error processing frame at {t}s: {e}")
            continue
        
    cap.release()
    return frames_data, duration

def calculate_similarity(query_emb, frame_index):
    """
    쿼리 임베딩과 프레임 인덱스 간의 유사도를 계산합니다.
    """
    if not frame_index:
        return []
    
    frame_embs = torch.stack([f["embedding"] for f in frame_index])
    scores = util.cos_sim(query_emb, frame_embs)[0]
    return scores.cpu().numpy()

def search_similar_frames(query, frame_index, model, is_image=False, top_k=6):
    """
    텍스트 또는 이미지 쿼리를 기반으로 유사도가 높은 상위 프레임을 검색합니다.
    """
    if not frame_index:
        return []

    try:
        # 1. 쿼리 임베딩(Vector) 생성
        if is_image:
            # 이미지 입력 처리 (PIL 이미지 변환)
            if not isinstance(query, Image.Image):
                query_img = Image.open(query).convert("RGB")
            else:
                query_img = query
            query_emb = model.encode(query_img, convert_to_tensor=True)
        else:
            # 텍스트 입력 처리
            if not query or query.strip() == "":
                return []
            query_emb = model.encode(query, convert_to_tensor=True)

        # 2. 유사도 계산
        scores = calculate_similarity(query_emb, frame_index)

        # 3. 결과 리스트 구성 및 정렬
        results = []
        for i, score in enumerate(scores):
            results.append({
                "ts": frame_index[i]["ts"],
                "sim": float(score)
            })

        # 유사도(sim) 기준 내림차순 정렬 후 상위 k개 반환
        results = sorted(results, key=lambda x: x["sim"], reverse=True)
        return results[:top_k]
    except Exception as e:
        logger.error(f"Error during similarity search: {e}")
        return []

if __name__ == "__main__":
    # 직접 실행 시 테스트를 위한 코드 (Test code for direct execution)
    import sys
    
    logger.info("--- Backend Self-Test Start ---")
    try:
        model = load_model()
        logger.info("Model loaded successfully.")
        
        # 테스트할 영상 파일 경로 (사용자 환경에 맞춰 수정 가능)
        test_video = "test.mp4" 
        if os.path.exists(test_video):
            logger.info(f"Analyzing test video: {test_video}")
            frames, duration = extract_frames_and_embeddings(test_video, model)
            logger.info(f"Analysis complete. Duration: {duration}s, Frames indexed: {len(frames)}")
        else:
            logger.info("No 'test.mp4' found. Skipping frame extraction test.")
            
        logger.info("--- Backend Self-Test End ---")
    except Exception as e:
        logger.error(f"Test failed: {e}")
