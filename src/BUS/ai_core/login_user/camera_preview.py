"""
Live Camera Preview Helper for Face Recognition
Provides real-time camera feed with oval guide overlay
"""

import cv2
import numpy as np
import base64
import threading
import time
from typing import Callable, Optional

# ========== SILENT MODE - TẮT TẤT CẢ LOG ==========
SILENT_MODE = False  # Set to False để bật lại logging

def log_print(*args, **kwargs):
    """Print wrapper - chỉ print khi SILENT_MODE = False"""
    if not SILENT_MODE:
        print(*args, **kwargs)
# ==================================================

class LiveCameraPreview:
    """
    Live camera preview với oval guide overlay
    Tự động phát hiện và chụp khuôn mặt
    """
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.thread = None
        self.current_frame = None
        self.face_detected = False
        self.auto_captured = False
        
    def start(self, on_frame_callback: Callable[[str], None], 
             on_auto_capture: Optional[Callable[[np.ndarray], None]] = None):
        """
        Bắt đầu camera preview
        
        Args:
            on_frame_callback: Function nhận base64 frame để hiển thị
            on_auto_capture: Function được gọi khi tự động chụp ảnh
        """
        log_print(f"📷 [CAMERA] Starting camera index {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            pass
            return False
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_running = True
        self.on_frame_callback = on_frame_callback
        self.on_auto_capture = on_auto_capture
        self.auto_captured = False
        
        # Start thread
        self.thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.thread.start()
        
        log_print("✅ [CAMERA] Camera started successfully")
        return True
    
    def stop(self):
        """Dừng camera - Thread-safe"""
        self.is_running = False
        
        # CRITICAL FIX: Prevent deadlock - không join nếu đang ở trong camera thread
        if self.thread and threading.current_thread() != self.thread:
            self.thread.join(timeout=2)
        elif self.thread:
            pass
        
        if self.cap:
            self.cap.release()
        pass
    
    def reset_capture(self):
        """Reset trạng thái capture để cho phép chụp lại ngay lập tức"""
        self.auto_captured = False
        pass
    
    def _camera_loop(self):
        """Loop chính để đọc frames - OPTIMIZED (Log tối thiểu)"""
        frame_count = 0
        last_detection_time = 0
        detection_interval = 0.5  # Chỉ detect mỗi 500ms
        
        # Load face cascade 1 lần duy nhất
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        log_print("🔧 [CAMERA] Face cascade classifier loaded")
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                pass
                break
            
            frame_count += 1
            current_time = time.time()
            
            # Flip horizontally (mirror effect)
            frame = cv2.flip(frame, 1)
            self.current_frame = frame.copy()
            
            # Tăng resolution lên 480x360 để rõ hơn
            display_frame = cv2.resize(frame, (480, 360))
            
            # Chỉ detect face theo interval thời gian
            if current_time - last_detection_time > detection_interval:
                small_frame = cv2.resize(frame, (320, 240))
                self.face_detected = self._detect_face_in_oval(small_frame)
                last_detection_time = current_time
                
                # LOGIC GỐC: Chụp ngay khi phát hiện mặt
                if self.face_detected and not self.auto_captured:
                    if self.on_auto_capture:
                        pass
                        self.auto_captured = True
                        self.on_auto_capture(frame)
            
            # Vẽ oval guide (không có countdown)
            overlay = self._draw_oval_guide(display_frame.copy())
            
            # Giảm JPEG quality xuống 45% để tăng tốc encoding
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 45]
            _, buffer = cv2.imencode('.jpg', overlay, encode_param)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Callback để update UI
            if self.on_frame_callback:
                self.on_frame_callback(f"data:image/jpeg;base64,{img_base64}")
            
            # Target 30 FPS
            time.sleep(0.033)
    
    def _draw_oval_guide(self, frame: np.ndarray) -> np.ndarray:
        """Vẽ oval guide đơn giản"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Vẽ nền tối xung quanh oval
        mask = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        axes = (int(w * 0.35), int(h * 0.50))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        
        darkened = frame.copy()
        darkened = cv2.addWeighted(darkened, 0.3, darkened, 0, 0)
        
        mask_inv = cv2.bitwise_not(mask)
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        mask_inv_3ch = cv2.cvtColor(mask_inv, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        
        result = (frame.astype(np.float32) * mask_3ch + darkened.astype(np.float32) * mask_inv_3ch).astype(np.uint8)
        
        # Vẽ viền oval
        color = (0, 255, 0) if self.face_detected else (255, 255, 255)
        thickness = 3 if self.face_detected else 2
        cv2.ellipse(result, center, axes, 0, 0, 360, color, thickness)
        
        # Text hướng dẫn
        if not self.face_detected:
            text = "Dat mat vao khung oval"
            text_color = (255, 255, 255)
        else:
            text = "Dang xu ly..."
            text_color = (0, 255, 0)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        text_size = cv2.getTextSize(text, font, font_scale, 1)[0]
        text_x = (w - text_size[0]) // 2
        text_y = h - 20
        
        cv2.putText(result, text, (text_x+1, text_y+1), font, font_scale, (0, 0, 0), 2)
        cv2.putText(result, text, (text_x, text_y), font, font_scale, text_color, 1)
        
        return result
    
    
    def _draw_oval_guide_with_countdown(self, frame: np.ndarray, countdown: int = None) -> np.ndarray:
        """
        Vẽ oval guide với số đếm ngược
        
        Args:
            frame: Frame gốc (480x360)
            countdown: Số đếm ngược (3, 2, 1) hoặc None
            
        Returns:
            Frame có oval overlay và số đếm ngược
        """
        h, w = frame.shape[:2]
        
        # Tạo overlay
        overlay = frame.copy()
        
        # Vẽ nền tối xung quanh oval
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # Oval parameters
        center = (w // 2, h // 2)
        axes = (int(w * 0.35), int(h * 0.50))
        
        # Vẽ oval trắng trên mask
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        
        # Tạo dark overlay bên ngoài oval
        darkened = frame.copy()
        darkened = cv2.addWeighted(darkened, 0.3, darkened, 0, 0)
        
        # Composite
        mask_inv = cv2.bitwise_not(mask)
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        mask_inv_3ch = cv2.cvtColor(mask_inv, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        
        result = (frame.astype(np.float32) * mask_3ch + darkened.astype(np.float32) * mask_inv_3ch).astype(np.uint8)
        
        # Vẽ viền oval
        color = (0, 255, 0) if self.face_detected else (255, 255, 255)
        thickness = 3 if self.face_detected else 2
        cv2.ellipse(result, center, axes, 0, 0, 360, color, thickness)
        
        # VẼ SỐ ĐẾM NGƯỢC (NẾU CÓ)
        if countdown is not None and countdown >= 0:
            # Số đếm ngược lớn ở giữa màn hình
            font = cv2.FONT_HERSHEY_DUPLEX  # Fixed: BOLD doesn't exist in cv2
            font_scale = 4.0
            text = str(countdown) if countdown > 0 else "GO!"
            text_size = cv2.getTextSize(text, font, font_scale, 8)[0]
            text_x = (w - text_size[0]) // 2
            text_y = (h + text_size[1]) // 2
            
            # Shadow
            cv2.putText(result, text, (text_x+3, text_y+3), font, font_scale, (0, 0, 0), 10)
            # Main text
            cv2.putText(result, text, (text_x, text_y), font, font_scale, (0, 255, 0), 8)
            
            # Text hướng dẫn
            guide_text = "Giữ yên!" if countdown > 0 else "Đang chụp..."
            guide_font_scale = 0.6
            guide_size = cv2.getTextSize(guide_text, cv2.FONT_HERSHEY_SIMPLEX, guide_font_scale, 2)[0]
            guide_x = (w - guide_size[0]) // 2
            guide_y = text_y + 60
            
            cv2.putText(result, guide_text, (guide_x+1, guide_y+1), cv2.FONT_HERSHEY_SIMPLEX, guide_font_scale, (0, 0, 0), 3)
            cv2.putText(result, guide_text, (guide_x, guide_y), cv2.FONT_HERSHEY_SIMPLEX, guide_font_scale, (255, 255, 255), 2)
        else:
            # Text hướng dẫn bình thường
            if not self.face_detected:
                text = "Đưa mặt vào khung hình"
                text_color = (255, 255, 255)
            else:
                text = "Phát hiện khuôn mặt..."
                text_color = (0, 255, 0)
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45
            text_size = cv2.getTextSize(text, font, font_scale, 1)[0]
            text_x = (w - text_size[0]) // 2
            text_y = h - 20
            
            # Shadow
            cv2.putText(result, text, (text_x+1, text_y+1), font, font_scale, (0, 0, 0), 2)
            cv2.putText(result, text, (text_x, text_y), font, font_scale, text_color, 1)
        
        return result
    
    def _detect_face_in_oval(self, frame: np.ndarray) -> bool:
        """
        Phát hiện khuôn mặt trong vùng oval
        
        Args:
            frame: Frame gốc (có thể là resolution nhỏ)
            
        Returns:
            True nếu có mặt trong oval
        """
        try:
            # Sử dụng cascade đã load sẵn
            if not hasattr(self, 'face_cascade'):
                return False
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Relax parameters để sensitive hơn
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=2,
                minSize=(20, 20)
            )
            
            if len(faces) > 0:
                # Lấy khuôn mặt lớn nhất
                (x, y, w_face, h_face) = max(faces, key=lambda f: f[2] * f[3])
                
                # Kiểm tra xem mặt có trong vùng oval không
                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2
                
                # Oval parameters
                oval_w, oval_h = int(w * 0.35), int(h * 0.50)
                
                # Center của mặt
                face_center_x = x + w_face // 2
                face_center_y = y + h_face // 2
                
                # Kiểm tra trong oval (ellipse equation)
                normalized_x = (face_center_x - center_x) / oval_w
                normalized_y = (face_center_y - center_y) / oval_h
                distance = normalized_x**2 + normalized_y**2
                
                # Tăng margin lên 1.5 để dễ detect hơn
                if distance <= 1.5:
                    return True
            
            return False
            
        except Exception as e:
            pass
            return False

