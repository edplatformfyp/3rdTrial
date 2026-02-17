import cv2
import mediapipe as mp
import numpy as np
from server.shared.schemas import ProctorStatus
import time

class ProctorAgent:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            refine_landmarks=True
        )

    def process_frame(self, frame_bytes: bytes, user_id: str) -> ProctorStatus:
        # Convert bytes to numpy array
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return ProctorStatus(user_id=user_id, attention_score=0.0, is_looking_away=True, fraud_detected=True, timestamp=time.time())

        # MediaPipe expects RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        attention_score = 1.0
        is_looking_away = False
        fraud_detected = False

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Simple Head Pose Estimation (Yaw) logic
                # Using nose tip (1) and chin (152) and ear approximations
                # This is a simplified heuristic for strict 3D pose estimation
                
                img_h, img_w, _ = frame.shape
                face_3d = []
                face_2d = []

                # Landmarks for PnP
                # Nose tip: 1, Chin: 152, Left eye left corner: 33, Right eye right corner: 263
                # Left Mouth corner: 61, Right Mouth corner: 291
                idx_list = [1, 152, 33, 263, 61, 291]
                
                for idx in idx_list:
                    lm = face_landmarks.landmark[idx]
                    x, y = int(lm.x * img_w), int(lm.y * img_h)
                    face_2d.append([x, y])
                    face_3d.append([x, y, lm.z]) # Approximate Z, or use model Z
                
                face_2d = np.array(face_2d, dtype=np.float64)
                face_3d = np.array(face_3d, dtype=np.float64)

                # Camera matrix
                focal_length = 1 * img_w
                cam_matrix = np.array([ [focal_length, 0, img_h / 2],
                                        [0, focal_length, img_w / 2],
                                        [0, 0, 1]])

                # Distortion matrix
                dist_matrix = np.zeros((4, 1), dtype=np.float64)

                # Solve PnP
                success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)

                if success:
                    rmat, jac = cv2.Rodrigues(rot_vec)
                    angles, mtxR, mtxQ, Q, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

                    # angles[1] is yaw (y-axis rotation)
                    # angles[0] is pitch (x-axis rotation)
                    x_angle = angles[0] * 360
                    y_angle = angles[1] * 360

                    if abs(y_angle) > 30 or abs(x_angle) > 30:
                        is_looking_away = True
                        attention_score = 0.5 # Penalty
                        
        else:
            # No face detected
            is_looking_away = True
            attention_score = 0.0
            # Could be fraud if no user present
            
        return ProctorStatus(
            user_id=user_id,
            attention_score=attention_score,
            is_looking_away=is_looking_away,
            fraud_detected=fraud_detected,
            timestamp=time.time()
        )
