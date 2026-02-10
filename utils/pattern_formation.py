"""
FaceSense Unique Pattern Formation - Visual overlay on camera feed.
Creates a distinctive geometric pattern from facial landmarks for a unique UX.
Pattern: Triangular mesh connecting eyes, nose, mouth - forms a "face signature" overlay.
"""
import cv2
import numpy as np
from typing import Tuple, List, Optional


def get_facial_landmarks(face_rect: Tuple[int, int, int, int], gray: Optional[np.ndarray] = None) -> List[Tuple[int, int]]:
    """
    Estimate facial landmark points from face region for pattern formation.
    Uses geometric heuristics (no external landmark model) for simplicity.
    Returns: [(x,y), ...] - eyes, nose tip, mouth corners
    """
    x, y, w, h = face_rect
    cx, cy = x + w // 2, y + h // 2
    
    # Geometric landmark estimates (proportional to face dimensions)
    landmarks = [
        (int(cx - w * 0.25), int(cy - h * 0.2)),   # Left eye
        (int(cx + w * 0.25), int(cy - h * 0.2)),   # Right eye
        (int(cx), int(cy)),                         # Nose tip
        (int(cx - w * 0.2), int(cy + h * 0.3)),    # Left mouth
        (int(cx + w * 0.2), int(cy + h * 0.3)),    # Right mouth
        (int(cx), int(cy + h * 0.35)),             # Chin center
        (int(cx - w * 0.4), int(cy)),              # Left face edge
        (int(cx + w * 0.4), int(cy)),              # Right face edge
    ]
    return landmarks


def draw_face_pattern(frame: np.ndarray, face_rect: Tuple[int, int, int, int], 
                      color: Tuple[int, int, int] = (0, 255, 200),
                      animate_phase: float = 0) -> np.ndarray:
    """
    Draw unique FaceSense pattern overlay on the face region.
    Pattern: Interconnected triangular mesh forming a face "signature" - distinctive & modern.
    """
    x, y, w, h = face_rect
    landmarks = get_facial_landmarks(face_rect)
    
    # Clamp landmarks to frame
    h_frame, w_frame = frame.shape[:2]
    landmarks = [
        (max(0, min(lx, w_frame - 1)), max(0, min(ly, h_frame - 1)))
        for lx, ly in landmarks
    ]
    
    overlay = frame.copy()
    
    # Draw connecting lines - triangular mesh pattern
    connections = [
        (0, 1), (0, 2), (1, 2),  # Eye-nose triangle
        (0, 3), (1, 4), (2, 3), (2, 4), (3, 4),  # Lower face
        (0, 6), (1, 7), (3, 6), (4, 7), (5, 3), (5, 4),
        (6, 2), (7, 2), (6, 3), (7, 4),
    ]
    
    thickness = max(1, min(w, h) // 80)
    for i, j in connections:
        if i < len(landmarks) and j < len(landmarks):
            pt1, pt2 = landmarks[i], landmarks[j]
            cv2.line(overlay, pt1, pt2, color, thickness)
    
    # Draw nodes with glow effect (pulsing based on animate_phase)
    pulse = 1 + 0.2 * np.sin(animate_phase)
    radius = int(max(2, min(w, h) * 0.04 * pulse))
    for i, pt in enumerate(landmarks):
        cv2.circle(overlay, pt, radius + 2, (30, 30, 30), -1)
        cv2.circle(overlay, pt, radius, color, -1)
    
    # Outer hexagon-style frame (unique FaceSense branding)
    pts = np.array(landmarks[:6], dtype=np.int32)
    cv2.polylines(overlay, [pts], True, (0, 200, 255), 1)
    
    # Blend overlay
    alpha = 0.6
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    return frame


def draw_pattern_formation_ui(frame: np.ndarray, face_rects: List[Tuple[int, int, int, int]],
                              status: str = "Detecting...", animate_phase: float = 0) -> np.ndarray:
    """
    Main UI: Draw pattern on all detected faces + status.
    """
    for rect in face_rects:
        draw_face_pattern(frame, rect, (0, 255, 200), animate_phase)
    
    # Status banner
    cv2.putText(frame, f"FaceSense Pattern | {status}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"FaceSense Pattern | {status}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 1)
    
    return frame
