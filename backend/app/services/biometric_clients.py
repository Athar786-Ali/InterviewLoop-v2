import base64
from functools import lru_cache
from math import sqrt

import cv2
import numpy as np

from app.core.config import settings
from app.core.exceptions import AppError

ARC_FACE_MODEL_NAME = "ArcFace"


def decode_base64_image(image_base64: str) -> np.ndarray:
    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except (ValueError, cv2.error) as exc:
        raise AppError("INVALID_IMAGE", "Image payload is not valid base64 image data.", 400) from exc

    if image is None:
        raise AppError("INVALID_IMAGE", "Image payload could not be decoded.", 400)
    return image


class DeepFaceArcFaceClient:
    def __init__(self) -> None:
        self._model_loaded = False

    def _ensure_model_loaded(self) -> None:
        if self._model_loaded:
            return
        from deepface import DeepFace

        DeepFace.build_model(ARC_FACE_MODEL_NAME)
        self._model_loaded = True

    def embedding_from_base64(self, image_base64: str) -> list[float]:
        self._ensure_model_loaded()
        image = decode_base64_image(image_base64)

        from deepface import DeepFace

        representations = DeepFace.represent(
            img_path=image,
            model_name=ARC_FACE_MODEL_NAME,
            enforce_detection=True,
        )
        if not representations:
            raise AppError("FACE_NOT_DETECTED", "No face was detected in the image.", 400)
        return [float(value) for value in representations[0]["embedding"]]

    def is_match(self, candidate: list[float], enrolled_embeddings: list[list[float]]) -> bool:
        return self.min_cosine_distance(candidate, enrolled_embeddings) <= settings.face_match_threshold

    def min_cosine_distance(self, candidate: list[float], enrolled_embeddings: list[list[float]]) -> float:
        if not enrolled_embeddings:
            raise AppError("BIOMETRIC_NOT_ENROLLED", "No biometric enrollment exists for this account.", 404)
        return min(self._cosine_distance(candidate, enrolled) for enrolled in enrolled_embeddings)

    def _cosine_distance(self, left: list[float], right: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(left, right))
        left_norm = sqrt(sum(a * a for a in left))
        right_norm = sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 1.0
        return 1.0 - (dot_product / (left_norm * right_norm))


class BlinkLivenessDetector:
    def __init__(self) -> None:
        cascade_path = cv2.data.haarcascades + "haarcascade_eye.xml"
        self.eye_cascade = cv2.CascadeClassifier(cascade_path)

    def verify(self, frame_images_base64: list[str]) -> bool:
        blink_count = 0
        closed_streak = 0
        eyes_were_open = False

        for image_base64 in frame_images_base64:
            frame = decode_base64_image(image_base64)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
            eyes_open = len(eyes) >= 1

            if eyes_open:
                if eyes_were_open and closed_streak >= settings.liveness_eye_closed_frames:
                    blink_count += 1
                eyes_were_open = True
                closed_streak = 0
            elif eyes_were_open:
                closed_streak += 1

        return blink_count >= settings.liveness_min_blinks


@lru_cache(maxsize=1)
def get_arcface_client() -> DeepFaceArcFaceClient:
    return DeepFaceArcFaceClient()


@lru_cache(maxsize=1)
def get_liveness_detector() -> BlinkLivenessDetector:
    return BlinkLivenessDetector()
