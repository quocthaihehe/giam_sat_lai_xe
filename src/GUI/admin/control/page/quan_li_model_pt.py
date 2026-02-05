import flet as ft
import cv2
import threading
import time
import json
import os

def QuanLiModel(page_title, page):
    
    # =================== PHÁT HIỆN CAMERA CÓ SẴN ===================
    def get_available_cameras():
        """Phát hiện tất cả camera có sẵn trên hệ thống - kiểm tra thực tế bằng cách đọc frame"""
        available_cameras = []
        # Kiểm tra tối đa 5 camera
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Dùng CAP_DSHOW cho Windows để nhanh hơn
            if cap.isOpened():
                # Thử đọc frame để xác nhận camera thực sự hoạt động
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Chỉ thêm vào danh sách nếu đọc được frame thực tế
                    backend_name = cap.getBackendName()
                    camera_name = f"Camera {i}"
                    if backend_name:
                        camera_name = f"Camera {i} ({backend_name})"
                    available_cameras.append({"index": i, "name": camera_name})
                cap.release()
        
        # Nếu không tìm thấy camera nào, trả về danh sách rỗng
        if not available_cameras:
            available_cameras = [{"index": -1, "name": "Không tìm thấy camera"}]
        
        return available_cameras
    
    cameras = get_available_cameras()
    
    # =================== MODEL NHẬN DIỆN SINH TRẮC HỌC ===================
    # Global model instance
    current_face_model = None
    
    biometric_models = ["ArcFace (v2.1)", "FaceNet (v1.0)", "DeepFace (v1.5)"]
    
    def on_model_select(e):
        """Callback khi admin chọn model"""
        nonlocal current_face_model
        
        model_name = e.control.value
        print(f"\n{'='*70}")
        print(f"🔄 [MODEL SELECT] Admin đang chọn: {model_name}")
        print(f"{'='*70}")
        
        # Lấy config từ UI
        config = {
            'confidence_threshold': float(bio_threshold.value),
            'min_face_size': int(bio_min_face_size.value),
            'cosine_threshold': float(bio_cosine_threshold.value)
        }
        
        try:
            if "ArcFace" in model_name:
                from src.BUS.ai_core.Arc_face import ArcFaceModel
                current_face_model = ArcFaceModel(config)
                print(f"✅ [SUCCESS] Loaded ArcFace model với config:")
                print(f"   ├─ Confidence: {config['confidence_threshold']}")
                print(f"   ├─ Min Face Size: {config['min_face_size']}px")
                print(f"   └─ Cosine Threshold: {config['cosine_threshold']}")
                
            elif "FaceNet" in model_name:
                print(f"⚠️  [WARNING] FaceNet chưa được triển khai")
                print(f"   Thành viên nhóm sẽ tạo src/BUS/ai_core/FaceNet.py")
                
            elif "DeepFace" in model_name:
                print(f"⚠️  [WARNING] DeepFace chưa được triển khai")
                print(f"   Thành viên nhóm sẽ tạo src/BUS/ai_core/DeepFace.py")
                
        except Exception as ex:
            print(f"❌ [ERROR] Không thể load model: {ex}")
            current_face_model = None
    
    selected_biometric = ft.Dropdown(
        label="Chọn Model Sinh Trắc Học",
        width=300,
        options=[ft.dropdown.Option(m) for m in biometric_models],
        value=biometric_models[0],
        on_change=on_model_select
    )
    
    bio_file_path = ft.Text("Chưa chọn file", size=12, color=ft.Colors.GREY, italic=True)
    
    def pick_bio_model(e: ft.FilePickerResultEvent):
        print(f"🔵 [DEBUG] Bio file picker called")
        if e.files:
            print(f"✅ [SUCCESS] Selected file: {e.files[0].path}")
            bio_file_path.value = e.files[0].path
            bio_file_path.italic = False
            bio_file_path.color = ft.Colors.GREEN
            bio_file_path.update()
        else:
            print(f"⚠️  [WARNING] No file selected")
    
    bio_file_picker = ft.FilePicker(on_result=pick_bio_model)
    print(f"🔵 [DEBUG] Adding bio_file_picker to page.overlay")
    page.overlay.append(bio_file_picker)
    page.update()  # CRITICAL: Update page to register the file picker
    print(f"✅ [SUCCESS] bio_file_picker added and page updated")
    
    # Load config from model_config.json
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "model_config.json")
    loaded_config = {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            face_config = loaded_config.get("face_recognition", {})
            print(f"✅ [CONFIG] Loaded model_config.json")
            print(f"   ├─ Confidence: {face_config.get('confidence_threshold', 0.75)}")
            print(f"   ├─ Min Face Size: {face_config.get('min_face_size', 40)}")
            print(f"   └─ Cosine Threshold: {face_config.get('cosine_threshold', 0.75)}")
    except Exception as e:
        print(f"⚠️  [CONFIG] Could not load config: {e}, using defaults")
        loaded_config = {
            "face_recognition": {
                "confidence_threshold": 0.75,
                "min_face_size": 40,
                "cosine_threshold": 0.75
            }
        }
    
    face_config = loaded_config.get("face_recognition", {})
    default_confidence = face_config.get('confidence_threshold', 0.75)
    default_min_face = face_config.get('min_face_size', 40)
    default_cosine = face_config.get('cosine_threshold', 0.75)
    
    bio_threshold = ft.Text(f"{default_confidence:.2f}", weight="bold", color=ft.Colors.BLUE)
    bio_min_face_size = ft.Text(f"{default_min_face}", weight="bold", color=ft.Colors.BLUE)
    bio_cosine_threshold = ft.Text(f"{default_cosine:.2f}", weight="bold", color=ft.Colors.BLUE)
    
    def update_bio_threshold(e):
        bio_threshold.value = f"{e.control.value:.2f}"
        bio_threshold.update()
        if current_face_model:
            current_face_model.confidence_threshold = e.control.value
            print(f"🔄 [CONFIG UPDATE] Confidence threshold: {e.control.value:.2f}")
    
    def update_bio_min_face(e):
        bio_min_face_size.value = f"{int(e.control.value)}"
        bio_min_face_size.update()
        if current_face_model:
            current_face_model.min_face_size = int(e.control.value)
            print(f"🔄 [CONFIG UPDATE] Min face size: {int(e.control.value)}px")
    
    def update_bio_cosine_threshold(e):
        bio_cosine_threshold.value = f"{e.control.value:.2f}"
        bio_cosine_threshold.update()
        if current_face_model:
            current_face_model.cosine_threshold = e.control.value
            print(f"🔄 [CONFIG UPDATE] Cosine threshold: {e.control.value:.2f}")
    
    def save_config(e):
        """Lưu cấu hình hiện tại vào model_config.json"""
        try:
            # Đọc config hiện tại
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Cập nhật face_recognition settings (bao gồm file path)
            config_data["face_recognition"] = {
                "model_name": selected_biometric.value,
                "model_path": bio_file_path.value if bio_file_path.value != "Chưa chọn file" else "",
                "confidence_threshold": float(bio_threshold.value),
                "min_face_size": int(bio_min_face_size.value),
                "cosine_threshold": float(bio_cosine_threshold.value)
            }
            
            # Ghi lại file
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ [SAVE] Biometric configuration saved to model_config.json")
            print(f"   ├─ Model: {selected_biometric.value}")
            print(f"   ├─ Model Path: {bio_file_path.value}")
            print(f"   ├─ Confidence: {bio_threshold.value}")
            print(f"   ├─ Min Face Size: {bio_min_face_size.value}")
            print(f"   └─ Cosine Threshold: {bio_cosine_threshold.value}")
            
            # Show success message
            page.open(ft.SnackBar(
                content=ft.Text("✅ Đã lưu cấu hình sinh trắc học!"),
                bgcolor=ft.Colors.GREEN_700
            ))
            
        except Exception as ex:
            print(f"❌ [SAVE ERROR] {ex}")
            import traceback
            traceback.print_exc()
            page.open(ft.SnackBar(
                content=ft.Text(f"❌ Lỗi lưu cấu hình: {ex}"),
                bgcolor=ft.Colors.RED_700
            ))
    
    def test_biometric_model(e):
        """Test model sinh trắc học và log ra terminal"""
        print(f"\n{'='*70}")
        print(f"🧪 [TEST] Starting Biometric Model Test")
        print(f"{'='*70}")
        
        if not current_face_model:
            print(f"❌ [TEST ERROR] No model loaded! Please select a model first.")
            page.open(ft.SnackBar(
                content=ft.Text("❌ Chưa load model! Hãy chọn model trước."),
                bgcolor=ft.Colors.RED_700
            ))
            return
        
        print(f"📋 [TEST] Model Configuration:")
        print(f"   ├─ Model Name: {selected_biometric.value}")
        print(f"   ├─ Model Path: {bio_file_path.value}")
        print(f"   ├─ Confidence Threshold: {bio_threshold.value}")
        print(f"   ├─ Min Face Size: {bio_min_face_size.value}px")
        print(f"   └─ Cosine Threshold: {bio_cosine_threshold.value}")
        
        print(f"\n✅ [TEST] Model is loaded and ready")
        print(f"   Model Type: {type(current_face_model).__name__}")
        
        # Show success
        page.open(ft.SnackBar(
            content=ft.Text("✅ Model test completed! Check terminal for details."),
            bgcolor=ft.Colors.GREEN_700
        ))
        
        print(f"{'='*70}\n")
    
    biometric_config_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=1, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        content=ft.Column([
            ft.Text("🔐 Model Nhận Diện Sinh Trắc Học", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
            ft.Divider(),
            selected_biometric,
            ft.Container(height=10),
            ft.ElevatedButton(
                "Browse File (.pt)",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: bio_file_picker.pick_files(
                    allowed_extensions=["pt"],
                    dialog_title="Chọn Model Sinh Trắc Học (.pt)"
                ),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    padding=15
                )
            ),
            ft.Container(height=5),
            bio_file_path,
            ft.Container(height=10),
            ft.Text("Tham Số Model:", size=14, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("Ngưỡng Độ Tin Cậy: "), bio_threshold
            ]),
            ft.Slider(min=0.3, max=1.0, divisions=70, value=default_confidence, on_change=update_bio_threshold),
            
            ft.Row([
                ft.Text("Kích Thước Khuôn Mặt Tối Thiểu (px): "), bio_min_face_size
            ]),
            ft.Slider(min=20, max=100, divisions=80, value=default_min_face, on_change=update_bio_min_face),
            
            ft.Row([
                ft.Text("Ngưỡng Cosine Similarity: "), bio_cosine_threshold
            ]),
            ft.Slider(min=0.2, max=1.0, divisions=80, value=default_cosine, on_change=update_bio_cosine_threshold),
            
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("Lưu Cấu Hình", icon=ft.Icons.SAVE, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, on_click=save_config),
                ft.ElevatedButton("Test Model", icon=ft.Icons.PLAY_ARROW, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=test_biometric_model)
            ])
        ])
    )

    # =================== MODEL NHẬN DIỆN NGỦ GẬT ===================
    drowsiness_models = ["YOLOv8n-Drowsy (v1.0)", "YOLOv11-Drowsy (v2.0)", "Custom-CNN (v1.2)"]
    selected_drowsiness = ft.Dropdown(
        label="Chọn Model Nhận Diện Ngủ Gật",
        width=300,
        options=[ft.dropdown.Option(m) for m in drowsiness_models],
        value=drowsiness_models[0]
    )
    
    drowsy_file_path = ft.Text("Chưa chọn file", size=12, color=ft.Colors.GREY, italic=True)
    
    def pick_drowsy_model(e: ft.FilePickerResultEvent):
        print(f"🟠 [DEBUG] Drowsy file picker called")
        if e.files:
            print(f"✅ [SUCCESS] Selected file: {e.files[0].path}")
            drowsy_file_path.value = e.files[0].path
            drowsy_file_path.italic = False
            drowsy_file_path.color = ft.Colors.GREEN
            drowsy_file_path.update()
        else:
            print(f"⚠️  [WARNING] No file selected")
    
    drowsy_file_picker = ft.FilePicker(on_result=pick_drowsy_model)
    print(f"🟠 [DEBUG] Adding drowsy_file_picker to page.overlay")
    page.overlay.append(drowsy_file_picker)
    page.update()  # CRITICAL: Update page to register the file picker
    print(f"✅ [SUCCESS] drowsy_file_picker added and page updated")
    
    drowsy_conf = ft.Text("0.50", weight="bold", color=ft.Colors.ORANGE)
    drowsy_iou = ft.Text("0.45", weight="bold", color=ft.Colors.ORANGE)
    
    def update_drowsy_conf(e):
        drowsy_conf.value = f"{e.control.value:.2f}"
        drowsy_conf.update()
    
    def update_drowsy_iou(e):
        drowsy_iou.value = f"{e.control.value:.2f}"
        drowsy_iou.update()
    
    def save_drowsy_config(e):
        """Lưu cấu hình ngủ gật vào model_config.json"""
        try:
            # Đọc config hiện tại
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Cập nhật drowsiness_detection settings (bao gồm file path)
            config_data["drowsiness_detection"] = {
                "model_name": selected_drowsiness.value,
                "model_path": drowsy_file_path.value if drowsy_file_path.value != "Chưa chọn file" else "",
                "confidence_threshold": float(drowsy_conf.value),
                "iou_threshold": float(drowsy_iou.value)
            }
            
            # Ghi lại file
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ [SAVE] Drowsiness detection configuration saved to model_config.json")
            print(f"   ├─ Model: {selected_drowsiness.value}")
            print(f"   ├─ Model Path: {drowsy_file_path.value}")
            print(f"   ├─ Confidence: {drowsy_conf.value}")
            print(f"   └─ IoU Threshold: {drowsy_iou.value}")
            
            # Show success message
            page.open(ft.SnackBar(
                content=ft.Text("✅ Đã lưu cấu hình ngủ gật!"),
                bgcolor=ft.Colors.ORANGE_700
            ))
            
        except Exception as ex:
            print(f"❌ [SAVE ERROR] {ex}")
            import traceback
            traceback.print_exc()
            page.open(ft.SnackBar(
                content=ft.Text(f"❌ Lỗi lưu cấu hình: {ex}"),
                bgcolor=ft.Colors.RED_700
            ))
    
    def test_drowsy_model(e):
        """Test model ngủ gật và log ra terminal"""
        print(f"\n{'='*70}")
        print(f"😴 [TEST] Starting Drowsiness Detection Model Test")
        print(f"{'='*70}")
        
        print(f"📋 [TEST] Model Configuration:")
        print(f"   ├─ Model Name: {selected_drowsiness.value}")
        print(f"   ├─ Model Path: {drowsy_file_path.value}")
        print(f"   ├─ Confidence Threshold: {drowsy_conf.value}")
        print(f"   └─ IoU Threshold: {drowsy_iou.value}")
        
        if drowsy_file_path.value == "Chưa chọn file":
            print(f"\n⚠️  [TEST WARNING] No model file selected")
        else:
            print(f"\n✅ [TEST] Model configuration logged successfully")
        
        # Show success
        page.open(ft.SnackBar(
            content=ft.Text("✅ Model test completed! Check terminal for details."),
            bgcolor=ft.Colors.ORANGE_700
        ))
        
        print(f"{'='*70}\n")
    
    drowsiness_config_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=1, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        content=ft.Column([
            ft.Text("😴 Model Nhận Diện Ngủ Gật", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
            ft.Divider(),
            selected_drowsiness,
            ft.Container(height=10),
            ft.ElevatedButton(
                "Browse File (.pt)",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: drowsy_file_picker.pick_files(
                    allowed_extensions=["pt"],
                    dialog_title="Chọn Model Ngủ Gật (.pt)"
                ),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.ORANGE,
                    color=ft.Colors.WHITE,
                    padding=15
                )
            ),
            ft.Container(height=5),
            drowsy_file_path,
            ft.Container(height=10),
            ft.Text("Tham Số Model:", size=14, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("Ngưỡng Tin Cậy (Confidence): "), drowsy_conf
            ]),
            ft.Slider(min=0, max=1, divisions=100, value=0.50, on_change=update_drowsy_conf),
            
            ft.Row([
                ft.Text("Ngưỡng IoU (NMS): "), drowsy_iou
            ]),
            ft.Slider(min=0, max=1, divisions=100, value=0.45, on_change=update_drowsy_iou),
            
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("Lưu Cấu Hình", icon=ft.Icons.SAVE, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE, on_click=save_drowsy_config),
                ft.ElevatedButton("Test Model", icon=ft.Icons.PLAY_ARROW, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=test_drowsy_model)
            ])
        ])
    )
    
    # =================== CẤU HÌNH CAMERA ===================
    selected_camera_index = ft.Ref[ft.Dropdown]()
    selected_camera_dropdown = ft.Dropdown(
        ref=selected_camera_index,
        label="Chọn Camera",
        width=300,
        options=[ft.dropdown.Option(key=str(cam["index"]), text=cam["name"]) for cam in cameras],
        value=str(cameras[0]["index"]) if cameras else "0"
    )
    
    camera_status = ft.Text("Chưa test", size=12, color=ft.Colors.GREY, italic=True)
    
    # Hàm log ra terminal
    def add_log(message, log_type="info"):
        """In log ra terminal thay vì hiển thị trong UI"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Chọn prefix theo loại log
        if log_type == "success":
            prefix = "✅ [SUCCESS]"
        elif log_type == "error":
            prefix = "❌ [ERROR]"
        elif log_type == "warning":
            prefix = "⚠️  [WARNING]"
        else:  # info
            prefix = "ℹ️  [INFO]"
        
        print(f"{prefix} [{timestamp}] {message}")
    
    
    is_testing = False
    test_thread = None
    
    def test_camera(e):
        nonlocal is_testing, test_thread
        
        camera_idx = int(selected_camera_dropdown.value)
        
        # Kiểm tra nếu không có camera
        if camera_idx == -1:
            camera_status.value = "❌ Không có camera nào được phát hiện"
            camera_status.color = ft.Colors.RED
            camera_status.italic = False
            add_log("Không tìm thấy camera nào trong hệ thống", "error")
            add_log("Vui lòng kết nối camera và nhấn 'Refresh Cameras'", "warning")
            
            camera_status.update()
            return
        
        camera_status.value = f"Đang test Camera {camera_idx}..."
        camera_status.color = ft.Colors.ORANGE
        camera_status.update()
        add_log(f"Bắt đầu test Camera {camera_idx}...", "info")
        
        # Thử mở camera với DSHOW backend (Windows)
        cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)
        
        if cap.isOpened():
            # Thử đọc frame để xác nhận camera thực sự hoạt động
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Camera thực sự hoạt động
                camera_status.value = f"✅ Camera {camera_idx} hoạt động tốt!"
                camera_status.color = ft.Colors.GREEN
                camera_status.italic = False
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                add_log(f"✅ Camera {camera_idx} hoạt động tốt!", "success")
                add_log(f"Resolution: {width}x{height}, FPS: {fps}", "success")
            else:
                # Camera mở được nhưng không đọc được frame
                camera_status.value = f"❌ Camera {camera_idx} không phản hồi"
                camera_status.color = ft.Colors.RED
                
                add_log(f"Camera {camera_idx} mở được nhưng không đọc được frame", "error")
                add_log("Camera có thể đang được sử dụng bởi ứng dụng khác", "warning")
            
            cap.release()
        else:
            camera_status.value = f"❌ Không thể mở Camera {camera_idx}"
            camera_status.color = ft.Colors.RED
            
            add_log(f"Không thể mở Camera {camera_idx}", "error")
            add_log("Vui lòng kiểm tra kết nối camera và driver", "warning")
        
        camera_status.update()
    
    camera_count_text = ft.Text(f"📊 Tổng số camera phát hiện: {len(cameras) if cameras and cameras[0]['index'] != -1 else 0}", size=13, color=ft.Colors.GREY_700)
    
    def refresh_cameras(e):
        """Quét lại danh sách camera"""
        nonlocal cameras
        
        # Hiển thị loading
        camera_status.value = "🔄 Đang quét camera..."
        camera_status.color = ft.Colors.BLUE
        camera_status.update()
        add_log("Bắt đầu quét camera trong hệ thống...", "info")
        
        # Quét lại
        cameras = get_available_cameras()
        
        # Cập nhật dropdown
        selected_camera_dropdown.options = [ft.dropdown.Option(key=str(cam["index"]), text=cam["name"]) for cam in cameras]
        selected_camera_dropdown.value = str(cameras[0]["index"]) if cameras else "-1"
        selected_camera_dropdown.update()
        
        # Cập nhật số lượng
        camera_count_text.value = f"📊 Tổng số camera phát hiện: {len(cameras) if cameras and cameras[0]['index'] != -1 else 0}"
        camera_count_text.update()
        
        # Thông báo kết quả
        if cameras and cameras[0]["index"] != -1:
            camera_status.value = f"✅ Tìm thấy {len(cameras)} camera"
            camera_status.color = ft.Colors.GREEN
            add_log(f"Tìm thấy {len(cameras)} camera trong hệ thống", "success")
            for cam in cameras:
                add_log(f"  → {cam['name']}", "info")
        else:
            camera_status.value = "❌ Không tìm thấy camera nào"
            camera_status.color = ft.Colors.RED
            add_log("Không tìm thấy camera nào", "error")
        camera_status.update()
    
    camera_config_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=1, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        content=ft.Column([
            ft.Text("📹 Cấu Hình Camera", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
            ft.Divider(),
            selected_camera_dropdown,
            ft.Container(height=10),
            camera_count_text,
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    "Test Camera",
                    icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                    on_click=test_camera,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PURPLE,
                        color=ft.Colors.WHITE,
                        padding=15
                    )
                ),
                ft.ElevatedButton(
                    "Refresh Cameras", 
                    icon=ft.Icons.REFRESH, 
                    on_click=refresh_cameras, 
                    bgcolor=ft.Colors.BLUE_GREY, 
                    color=ft.Colors.WHITE
                )
            ]),
            ft.Container(height=10),
            camera_status,
            ft.Container(height=5),
            ft.Text("* Log sẽ hiển thị trong terminal/console", size=11, color=ft.Colors.GREY, italic=True),
            ft.Container(height=10),
            ft.ElevatedButton("Lưu Cấu Hình", icon=ft.Icons.SAVE, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE)
        ])
    )
    
    # =================== KHO LƯU TRỮ MODEL ===================
    model_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Loại Model")),
            ft.DataColumn(ft.Text("Tên File")),
            ft.DataColumn(ft.Text("Version")),
            ft.DataColumn(ft.Text("Ngày Upload")),
            ft.DataColumn(ft.Text("Accuracy")),
            ft.DataColumn(ft.Text("Kích thước")),
            ft.DataColumn(ft.Text("Trạng thái")),
            ft.DataColumn(ft.Text("Hành động")),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.FACE, color=ft.Colors.BLUE)),
                ft.DataCell(ft.Text("facenet_model.h5")),
                ft.DataCell(ft.Text("v1.0.0")),
                ft.DataCell(ft.Text("20/01/2026")),
                ft.DataCell(ft.Text("98.5%")),
                ft.DataCell(ft.Text("25 MB")),
                ft.DataCell(ft.Container(content=ft.Text("Active", color="white", size=10), bgcolor="blue", padding=5, border_radius=5)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Tải xuống"),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Cấu hình"),
                ])),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.REMOVE_RED_EYE, color=ft.Colors.ORANGE)),
                ft.DataCell(ft.Text("yolov8n_drowsy.pt")),
                ft.DataCell(ft.Text("v1.0.0")),
                ft.DataCell(ft.Text("18/01/2026")),
                ft.DataCell(ft.Text("92.5%")),
                ft.DataCell(ft.Text("12 MB")),
                ft.DataCell(ft.Container(content=ft.Text("Active", color="white", size=10), bgcolor="orange", padding=5, border_radius=5)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Tải xuống"),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Cấu hình"),
                ])),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.REMOVE_RED_EYE, color=ft.Colors.ORANGE)),
                ft.DataCell(ft.Text("yolov11_drowsy.pt")),
                ft.DataCell(ft.Text("v2.0.0 (Beta)")),
                ft.DataCell(ft.Text("25/01/2026")),
                ft.DataCell(ft.Text("94.1%")),
                ft.DataCell(ft.Text("15 MB")),
                ft.DataCell(ft.Text("Backup")),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.UPLOAD, tooltip="Kích hoạt", icon_color="green"),
                    ft.IconButton(ft.Icons.DELETE, icon_color="red", tooltip="Xóa"),
                ])),
            ]),
        ],
        border=ft.border.all(1, ft.Colors.GREY_200),
        border_radius=10,
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_100),
        heading_row_color=ft.Colors.GREY_50,
    )

    list_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20, expand=True,
        content=ft.Column([
            ft.Row([
                ft.Text("📦 Kho Lưu Trữ Model", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton("Upload Model Sinh Trắc", icon=ft.Icons.UPLOAD_FILE, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                    ft.ElevatedButton("Upload Model Ngủ Gật", icon=ft.Icons.UPLOAD_FILE, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Container(content=model_table, expand=True, padding=0)
        ])
    )

    return ft.Column([
        ft.Text("⚙️ " + page_title, size=24, weight=ft.FontWeight.BOLD),
        ft.Container(height=10),
        # Hàng 1: 2 Model Cards (rộng hơn)
        ft.Row([
            ft.Container(content=biometric_config_card, expand=True),
            ft.Container(width=15),
            ft.Container(content=drowsiness_config_card, expand=True),
        ]),
        ft.Container(height=15),
        # Hàng 2: Camera Card ở bên trái
        ft.Row([
            ft.Container(content=camera_config_card, width=500),
        ]),
        ft.Container(height=20),
        # Phần kho lưu trữ
        ft.Container(content=list_card, expand=True)
    ], expand=True, scroll=ft.ScrollMode.AUTO)