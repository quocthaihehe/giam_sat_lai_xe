import flet as ft
import time
import os
import json
import threading
from . import laucher_user

# ========== TẮT TẤT CẢ LOGGING ĐỂ GIAO DIỆN SẠCH SẼ ==========
import warnings
import logging
import sys

# Tắt tất cả warnings
warnings.filterwarnings("ignore")

# Tắt logging của insightface
# logging.getLogger('insightface').setLevel(logging.ERROR)

# Tắt logging của onnxruntime
# logging.getLogger('onnxruntime').setLevel(logging.ERROR)

# Tắt logging của ultralytics
# logging.getLogger('ultralytics').setLevel(logging.ERROR)

# Tắt FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

# Redirect stderr để ẩn các log từ C++ libraries
class SuppressOutput:
    def __enter__(self):
        self._original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self._original_stderr
# ============================================================

# Import AI model ở top level để tránh import trong thread
try:
    from src.BUS.ai_core.login_user.Arc_face import ArcFaceModel
    ARCFACE_AVAILABLE = True
except Exception as e:
    import traceback
    traceback.print_exc()
    ARCFACE_AVAILABLE = False
    ArcFaceModel = None

# Singleton instance của model (khởi tạo 1 lần duy nhất)
_global_arcface_model = None

def get_arcface_model(config=None):
    """
    Lấy singleton instance của ArcFace model
    Chỉ khởi tạo 1 lần duy nhất trong toàn bộ ứng dụng
    """
    global _global_arcface_model
    
    if not ARCFACE_AVAILABLE:
        print("❌ [MODEL] ArcFace not available")
        return None
    
    if _global_arcface_model is None:
        if config is None:
            config = {
                'confidence_threshold': 0.5,
                'min_face_size': 30,
                'cosine_threshold': 0.5
            }
        
        print("🔧 [MODEL] Initializing ArcFace model (first time)...")
        _global_arcface_model = ArcFaceModel(config)
        print("✅ [MODEL] ArcFace model initialized and cached")
    
    return _global_arcface_model


class UserUI:
    def __init__(self, page: ft.Page, go_back_callback=None):
        self.page = page
        self.go_back_callback = go_back_callback
        self.page.title = "Đăng Kí / Đăng Nhập Tài Xế"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # =====================================================================
        # --- CẤU HÌNH TÀI NGUYÊN (ĐÃ SỬA: Thêm self. và khớp tên biến) ---
        # =====================================================================
        
        # 1. Ảnh nền chính (Khớp với self.bg_image_path bên dưới)
        self.bg_image_path = r"src\GUI\data\image_user\backround.jpg"
        
        # 2. Icon hiển thị ở màn hình Login (Khớp với self.login_car_icon_path bên dưới)
        # Bạn có thể thay bằng đường dẫn ảnh chiếc xe hoặc logo tùy ý
        self.login_car_icon_path = r"src\GUI\data\image_laucher\image_btnlogo_user.png"
        
        # 3. Avatar mặc định cho Dashboard
        self.avatar_url = "https://avatars.githubusercontent.com/u/1?v=4"
        
        # --- TRẠNG THÁI NGƯỜI DÙNG ---
        self.current_user_name = "Hieu"
        self.current_user_id = "12345"

        # Khởi động vào màn hình Đăng nhập
        self.show_login_view()

    # =========================================================================
    # 1. MÀN HÌNH ĐĂNG NHẬP (LOGIN VIEW)
    # =========================================================================
    def show_login_view(self):
        self.page.clean()
        
        # Input fields
        user_input = ft.TextField(label="Tài khoản", value= "user01", prefix_icon=ft.Icons.PERSON, border_radius=10, bgcolor=ft.Colors.WHITE, text_size=14)
        pass_input = ft.TextField(label="Mật khẩu", value= "123456", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True, border_radius=10, bgcolor=ft.Colors.WHITE, text_size=14)

        # Login Card
        login_card = ft.Container(
            width=400,
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12),
            content=ft.Column([
                # Nút quay lại và Logo
                ft.Container(
                    content=ft.Stack([
                        ft.Container(
                            content=ft.Column([
                                ft.Image(
                                    src=self.login_car_icon_path, 
                                    width=100, height=80, 
                                    fit=ft.ImageFit.CONTAIN,
                                    error_content=ft.Column([
                                        ft.Icon(ft.Icons.DIRECTIONS_CAR_FILLED, size=60, color=ft.Colors.BLUE),
                                        ft.Text("Ảnh lỗi", size=10, color=ft.Colors.RED)
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                                ),
                                ft.Text("ĐĂNG NHẬP", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                                ft.Text("Hệ thống giám sát lái xe", size=14, color=ft.Colors.GREY),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=ft.Colors.GREEN_700,
                                on_click=lambda e: self._go_back_to_main(),
                                tooltip="Quay lại"
                            ),
                            left=0,
                            top=0
                        )
                    ]),
                    height=150
                ),
                ft.Container(height=10),
                
                user_input,
                ft.Container(height=15),
                pass_input,
                ft.Container(
                    content=ft.TextButton(
                        "Quên mật khẩu?",
                        on_click=lambda e: self._handle_forgot_password(),
                        style=ft.ButtonStyle(color=ft.Colors.BLUE_700)
                    ),
                    alignment=ft.alignment.center_right
                ),
                ft.Container(height=10),
                
                # Nút Đăng nhập
                ft.ElevatedButton(
                    "Đăng nhập", 
                    width=float("inf"), 
                    height=50,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700, 
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=lambda e: self._handle_login(user_input.value, pass_input.value)
                ),
                
                ft.Container(height=15),
                
                # Nút đăng nhập bằng khuôn mặt
                ft.ElevatedButton(
                    "Đăng nhập bằng khuôn mặt",
                    width=float("inf"),
                    height=50,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=lambda e: self._handle_face_login()
                ),
                
                ft.Container(height=20),
                ft.TextButton("Đăng ký tài khoản mới", on_click=lambda e: self.show_register_view())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # Layout chính
        layout = ft.Stack([
            # Lớp 1: Ảnh nền
            ft.Image(
                src=self.bg_image_path,
                width=float("inf"), height=float("inf"),
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(bgcolor="#E0F2F1")
            ),
            # Lớp 2: Phủ mờ
            ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK)),
            
            # Lớp 3: Card đăng nhập
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=login_card
            )
        ], expand=True)
        
        self.page.add(layout)

    # =========================================================================
    # 2. MÀN HÌNH ĐĂNG KÝ
    # =========================================================================
    def show_register_view(self):
        self.page.clean()
        
        input_style = {"border_radius": 10, "bgcolor": ft.Colors.WHITE, "text_size": 14, "content_padding": 15}
        
        txt_name = ft.TextField(label="Họ tên", prefix_icon=ft.Icons.PERSON_OUTLINE, **input_style)
        txt_phone = ft.TextField(label="SĐT", prefix_icon=ft.Icons.PHONE, **input_style)
        txt_username = ft.TextField(label="Tên đăng nhập", prefix_icon=ft.Icons.ACCOUNT_CIRCLE, **input_style)
        txt_password = ft.TextField(label="Mật khẩu", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True, can_reveal_password=True, **input_style)
        txt_password_confirm = ft.TextField(label="Nhập lại mật khẩu", prefix_icon=ft.Icons.LOCK_RESET, password=True, can_reveal_password=True, **input_style)

        register_card = ft.Container(
            width=450,
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12),
            content=ft.Column([
                ft.Stack([
                    ft.Container(
                        content=ft.Column([
                            ft.Image(src=self.login_car_icon_path, width=60, height=60, fit=ft.ImageFit.CONTAIN),
                            ft.Text("ĐĂNG KÝ TÀI XẾ MỚI", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                            ft.Text("Điền đầy đủ thông tin", size=12, color=ft.Colors.GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: self.show_login_view(),
                            tooltip="Quay lại"
                        ),
                        left=0,
                        top=0
                    )
                ]),
                
                ft.Container(height=20),
                txt_name,
                ft.Container(height=10),
                txt_phone,
                ft.Container(height=10),
                txt_username,
                ft.Container(height=10),
                txt_password,
                ft.Container(height=10),
                txt_password_confirm,
                ft.Container(height=20),
                
                # Nút Đăng ký bằng khuôn mặt (NÚT DUY NHẤT)
                ft.ElevatedButton(
                    "Đăng Ký Bằng Khuôn Mặt",
                    icon=ft.Icons.FACE,
                    width=float("inf"),
                    height=50,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=lambda e: self._handle_face_register(
                        txt_name, txt_phone, txt_username, txt_password, txt_password_confirm
                    )
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        )

        layout = ft.Stack([
            ft.Image(src=self.bg_image_path, width=float("inf"), height=float("inf"), fit=ft.ImageFit.COVER),
            ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK)),
            ft.Container(expand=True, alignment=ft.alignment.center, content=register_card)
        ], expand=True)
        
        self.page.add(layout)

    # =========================================================================
    # 3. MÀN HÌNH DASHBOARD
    # =========================================================================
    def show_dashboard_view(self):
        self.page.clean()
        
        user_info_card = ft.Container(
            width=350,
            padding=15,
            bgcolor="#D1E2D3",
            border=ft.border.all(1, ft.Colors.BLACK54),
            border_radius=15,
            content=ft.Row([
                ft.CircleAvatar(src=self.avatar_url, radius=30, bgcolor=ft.Colors.WHITE),
                ft.Column([
                    ft.Text(self.current_user_name, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLACK),
                    ft.Text(f"ID : {self.current_user_id}", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK),
                ], spacing=3)
            ], alignment=ft.MainAxisAlignment.START)
        )

        def create_dashboard_btn(text, icon, bg_color):
            return ft.Container(
                width=350, height=80,
                bgcolor=bg_color,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.BLACK54),
                padding=ft.padding.symmetric(horizontal=20),
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK26, offset=ft.Offset(0, 3)),
                ink=True,
                on_click=lambda e: print(f"Click: {text}"),
                content=ft.Row([
                    ft.Container(
                        width=50, height=50,
                        border=ft.border.all(2, ft.Colors.BLACK),
                        border_radius=25,
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, color=ft.Colors.BLACK, size=30)
                    ),
                    ft.Container(width=15),
                    ft.Text(text, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
                ])
            )

        btn_start = create_dashboard_btn("Bắt Đầu Phiên Lái", ft.Icons.PLAY_ARROW, "#4CAF50")
        btn_history = create_dashboard_btn("Lịch Sử Phiên Lái", ft.Icons.HISTORY, "#2E7D9E")
        btn_settings = create_dashboard_btn("Cài Đặt", ft.Icons.SETTINGS, "#D68936")

        content_column = ft.Column(
            [
                ft.Container(height=50),
                user_info_card,
                ft.Container(height=30),
                btn_start,
                ft.Container(height=15),
                btn_history,
                ft.Container(height=15),
                btn_settings,
                ft.Container(expand=True),
                ft.Text("© 2026 Driver Driver v1.0.0", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(height=20)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        layout = ft.Stack([
            ft.Image(
                src=self.bg_image_path,
                width=float("inf"), height=float("inf"),
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(bgcolor=ft.Colors.BLUE_GREY_900)
            ),
            ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
            ft.Container(
                content=content_column,
                alignment=ft.alignment.center,
                expand=True
            )
        ], expand=True)
        
        self.page.add(layout)

    # =========================================================================
    # 4. LOGIC XỬ LÝ
    # =========================================================================
    def _go_back_to_main(self):
        if self.go_back_callback:
            self.page.controls.clear()
            self.page.update()
            self.go_back_callback()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Không thể quay lại"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()

    def _handle_login(self, user, pwd):
        """
        Xử lý đăng nhập với 2 bước:
        1. Xác thực username + password
        2. Xác thực khuôn mặt (tự động)
        """
        # Kiểm tra tài khoản trống
        if not user:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Tài khoản không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Kiểm tra mật khẩu trống
        if not pwd:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Mật khẩu không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Hiển thị thông báo đang xác thực
        self.page.open(ft.SnackBar(ft.Text("🔄 Đang xác thực tài khoản..."), bgcolor=ft.Colors.BLUE_400))
        self.page.update()
        
        time.sleep(0.3)  # Hiệu ứng loading nhẹ
        
        # Đọc tài khoản từ file JSON
        try:
            accounts_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "accounts.json")
            with open(accounts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_accounts = data.get("user_accounts", [])
            
            # Kiểm tra tài khoản
            account_found = None
            for acc in user_accounts:
                if acc["username"] == user and acc["password"] == pwd:
                    account_found = acc
                    break
            
            if account_found:
                # BƯỚC 1 THÀNH CÔNG: Username/Password đúng
                
                # Kiểm tra xem user đã đăng ký khuôn mặt chưa
                if 'face_data' not in account_found:
                    self.page.open(ft.SnackBar(
                        ft.Text("⚠️ Tài khoản chưa đăng ký khuôn mặt! Vui lòng đăng ký khuôn mặt trước khi đăng nhập."), 
                        bgcolor=ft.Colors.ORANGE_600
                    ))
                    self.page.update()
                    return
                
                # ĐÃ ĐĂNG KÝ KHUÔN MẶT → VÀO THẲNG HỆ THỐNG
                self.page.open(ft.SnackBar(
                    ft.Text(f"✅ Đăng nhập thành công! Xin chào {account_found['name']}"), 
                    bgcolor=ft.Colors.GREEN_600
                ))
                self.page.update()
                
                # Lưu thông tin user
                self.current_user_name = account_found["name"]
                self.current_user_id = account_found["driver_id"]
                
                time.sleep(1)
                
                # Chuyển sang trang chủ
                self.page.controls.clear()
                self.page.update()
                laucher_user.main(self.page, self.go_back_callback, user_account=account_found)
                
            else:
                # Thông báo lỗi tài khoản/mật khẩu
                self.page.open(ft.SnackBar(ft.Text("❌ Sai tên đăng nhập hoặc mật khẩu!"), bgcolor=ft.Colors.RED_600))
                self.page.update()
        except FileNotFoundError:
            self.page.open(ft.SnackBar(ft.Text("❌ Không tìm thấy file tài khoản!"), bgcolor=ft.Colors.RED_600))
            self.page.update()
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"❌ Lỗi hệ thống: {str(e)}"), bgcolor=ft.Colors.RED_600))
            self.page.update()

    def _handle_forgot_password(self):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("🔑 Tính năng khôi phục mật khẩu đang phát triển..."),
            bgcolor=ft.Colors.ORANGE_400
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _handle_face_login_verification(self, account_data: dict, username: str, password: str):
        """
        Xác thực khuôn mặt sau khi username/password đã đúng
        So sánh vector embedding với face_data đã lưu
        """
        import cv2
        import tempfile
        from pathlib import Path
        from src.BUS.ai_core.login_user.camera_preview import LiveCameraPreview
        
        print("\n" + "="*70)
        print(f"📷 [FACE LOGIN] Xác thực khuôn mặt cho {username}")
        print("="*70)
        
        # UI Elements
        dialog_message = ft.Text(
            "🔄 Đang tải AI model và khởi động camera...", 
            size=15, 
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
            text_align=ft.TextAlign.CENTER
        )
        
        # Camera view với placeholder
        camera_view = ft.Image(
            width=480,
            height=360,
            fit=ft.ImageFit.CONTAIN,
            border_radius=15,
            # Placeholder: 1x1 transparent PNG
            src_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        btn_close = ft.ElevatedButton(
            "Hủy",
            icon=ft.Icons.CLOSE,
            bgcolor=ft.Colors.RED_400,
            color=ft.Colors.WHITE,
            on_click=lambda e: close_dialog()
        )
        
        # Progress indicator
        progress_ring = ft.ProgressRing(visible=True, width=30, height=30, color=ft.Colors.BLUE_700)
        
        # Dialog
        face_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.FACE_RETOUCHING_NATURAL, color=ft.Colors.BLUE_700, size=30),
                ft.Text("Xác Thực Khuôn Mặt", weight=ft.FontWeight.BOLD, size=20),
            ]),
            content=ft.Container(
                width=660,
                height=600,
                content=ft.Column([
                    # Loading message BÊN NGOÀI khung camera
                    ft.Row([
                        progress_ring,
                        ft.Container(width=10),
                        dialog_message
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Container(height=10),
                    
                    # Camera view
                    ft.Container(
                        content=camera_view,
                        border=ft.border.all(3, ft.Colors.BLUE_700),
                        border_radius=15,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=15,
                            color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_700)
                        )
                    ),
                    
                    ft.Container(height=15),
                    
                    # Hướng dẫn
                    ft.Container(
                        padding=15,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=10,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=20),
                                ft.Text("Hướng dẫn:", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                            ]),
                            ft.Container(height=5),
                            ft.Text("• Đặt khuôn mặt vào khung oval màu trắng", size=13, color=ft.Colors.BLUE_800),
                            ft.Text("• Giữ yên khi khung chuyển sang màu xanh", size=13, color=ft.Colors.BLUE_800),
                            ft.Text("• Hệ thống sẽ tự động nhận diện", size=13, color=ft.Colors.BLUE_800),
                        ], spacing=3)
                    ),
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            actions=[btn_close],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Camera preview instance
        camera = None
        processing = False
        frame_counter = 0
        
        # MỞI DIALOG NGAY LẬP TỨC (trước khi load model)
        self.page.open(face_dialog)
        self.page.update()
        
        # LOAD MODEL VÀ CAMERA TRONG BACKGROUND THREAD
        def initialize_ai_and_camera():
            """Load AI model và khởi động camera trong background"""
            nonlocal camera
            
            try:
                # BƯỚC 1: Load AI Model
                dialog_message.value = "🤖 Đang tải AI model..."
                dialog_message.update()
                
                print("\n🔧 [MODEL] Getting ArcFace model instance...")
                config = {
                    'confidence_threshold': 0.5,
                    'min_face_size': 30,
                    'cosine_threshold': 0.5
                }
                
                arcface_model = get_arcface_model(config)
                
                if arcface_model is None:
                    print("❌ [CRITICAL ERROR] Failed to get ArcFace model")
                    dialog_message.value = "❌ Lỗi: Không thể khởi tạo AI model"
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                    dialog_message.update()
                    progress_ring.update()
                    return
                
                print("✅ [OPTIMIZATION] Model ready!")
                
                # BƯỚC 2: Khởi động Camera
                dialog_message.value = "📷 Đang khởi động camera..."
                dialog_message.update()
                
                camera = LiveCameraPreview(camera_index=0)
                success = camera.start(
                    on_frame_callback=update_frame,
                    on_auto_capture=lambda frame: on_auto_capture(frame, arcface_model)
                )
                
                if success:
                    dialog_message.value = "✅ Camera sẵn sàng - Hãy đặt mặt vào khung oval"
                    dialog_message.color = ft.Colors.GREEN_700
                    progress_ring.visible = False
                else:
                    dialog_message.value = "❌ Không thể mở camera"
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                
                dialog_message.update()
                progress_ring.update()
                
            except Exception as ex:
                print(f"❌ [INIT ERROR]: {ex}")
                import traceback
                traceback.print_exc()
                
                dialog_message.value = f"❌ Lỗi: {str(ex)}"
                dialog_message.color = ft.Colors.RED
                progress_ring.visible = False
                dialog_message.update()
                progress_ring.update()
        
        def update_frame(base64_img: str):
            """Update camera view - Batch update mỗi 2 frames"""
            nonlocal frame_counter
            try:
                frame_counter += 1
                camera_view.src_base64 = base64_img.split(",")[1]
                if frame_counter % 2 == 0:
                    camera_view.update()
            except Exception as e:
                print(f"⚠️  [FRAME UPDATE] Error: {e}")
        
        def on_auto_capture(frame: 'np.ndarray', arcface_model):
            """Callback khi tự động chụp ảnh - So sánh với face_data đã lưu"""
            nonlocal processing
            
            if processing:
                return
            
            processing = True
            
            # Update UI
            dialog_message.value = "🔍 Đang xác thực khuôn mặt..."
            dialog_message.color = ft.Colors.ORANGE
            progress_ring.visible = True
            dialog_message.update()
            progress_ring.update()
            
            def process_face_verification():
                nonlocal processing
                try:
                    # Lưu ảnh tạm
                    temp_dir = tempfile.gettempdir()
                    captured_image_path = str(Path(temp_dir) / "face_login_verify.jpg")
                    cv2.imwrite(captured_image_path, frame)
                    
                    # Sử dụng verify_face của model để so sánh
                    matched, similarity = arcface_model.verify_face(
                        captured_image_path, 
                        username, 
                        password
                    )
                    
                    if matched:
                        # XÁC THỰC THÀNH CÔNG
                        dialog_message.value = f"✅ Xác thực thành công! Độ tương đồng: {similarity:.2%}"
                        dialog_message.color = ft.Colors.GREEN
                        
                        self.page.open(ft.SnackBar(
                            ft.Text(f"✅ Đăng nhập thành công! Xin chào {account_data['name']}"),
                            bgcolor=ft.Colors.GREEN_600
                        ))
                        
                        # Lưu thông tin user
                        self.current_user_name = account_data["name"]
                        self.current_user_id = account_data["driver_id"]
                        
                        # Đóng dialog và chuyển trang
                        import time
                        time.sleep(1.5)
                        close_dialog()
                        
                        # Chuyển sang trang chủ
                        self.page.controls.clear()
                        self.page.update()
                        laucher_user.main(self.page, self.go_back_callback, user_account=account_data)
                    else:
                        # XÁC THỰC THẤT BẠI
                        dialog_message.value = f"❌ Khuôn mặt không khớp! Độ tương đồng: {similarity:.2%}\\nVui lòng thử lại."
                        dialog_message.color = ft.Colors.RED
                        processing = False
                        
                        # Reset camera để thử lại
                        if camera:
                            camera.reset_capture()
                    
                    progress_ring.visible = False
                    dialog_message.update()
                    progress_ring.update()
                    self.page.update()
                    
                except Exception as ex:
                    print(f"❌ [ERROR] Face verification failed: {ex}")
                    import traceback
                    traceback.print_exc()
                    
                    dialog_message.value = f"❌ Lỗi: {str(ex)}\\nVui lòng thử lại."
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                    processing = False
                    
                    if camera:
                        camera.reset_capture()
                    
                    dialog_message.update()
                    progress_ring.update()
            
            # Chạy trong background thread
            import threading
            process_thread = threading.Thread(target=process_face_verification, daemon=True)
            process_thread.start()
        
        
        def close_dialog():
            """\u0110\u00f3ng dialog v\u00e0 d\u1eebng camera"""
            nonlocal camera
            if camera:
                camera.stop()
            self.page.close(face_dialog)
            self.page.update()
        
        # KHỚI ĐỘNG BACKGROUND THREAD để load model + camera
        import threading
        import traceback
        init_thread = threading.Thread(target=initialize_ai_and_camera, daemon=True)
        init_thread.start()
    
    def _handle_register(self, name, phone, username, password, password_confirm):
        # Kiểm tra từng trường riêng biệt
        if not name:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Họ tên không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not phone:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Số điện thoại không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not username:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Tên đăng nhập không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not password:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Mật khẩu không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not password_confirm:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Vui lòng nhập lại mật khẩu!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Kiểm tra mật khẩu khớp
        if password != password_confirm:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Mật khẩu nhập lại không khớp!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Thông báo đang xử lý
        self.page.open(ft.SnackBar(ft.Text("🔄 Đang xử lý đăng ký..."), bgcolor=ft.Colors.BLUE_400))
        self.page.update()
        
        time.sleep(0.5)
        
        try:
            # Đọc file accounts.json
            accounts_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "accounts.json")
            if os.path.exists(accounts_path):
                with open(accounts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"admin_accounts": [], "user_accounts": []}
            
            # Kiểm tra username đã tồn tại chưa
            for acc in data.get("user_accounts", []):
                if acc["username"] == username:
                    self.page.open(ft.SnackBar(ft.Text("❌ Tên đăng nhập đã tồn tại!"), bgcolor=ft.Colors.RED_600))
                    self.page.update()
                    return
            
            # Tự động tạo driver_id (TX001, TX002, ...)
            existing_ids = [acc.get("driver_id", "") for acc in data.get("user_accounts", [])]
            driver_id = f"TX{len(existing_ids) + 1:03d}"
            
            # Thêm tài khoản mới
            new_account = {
                "username": username,
                "password": password,
                "name": name,
                "driver_id": driver_id,
                "phone": phone,
                "plan": "Normal"
            }
            data["user_accounts"].append(new_account)
            
            # Lưu file
            with open(accounts_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Thông báo thành công
            self.page.open(ft.SnackBar(ft.Text("✅ Đăng ký thành công! Đang chuyển sang trang đăng nhập..."), bgcolor=ft.Colors.GREEN_600))
            self.page.update()
            
            time.sleep(1.5)
            self.show_login_view()
            
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"❌ Lỗi: {str(e)}"), bgcolor=ft.Colors.RED_600))
            self.page.update()
    
    
    
    def _handle_face_register(self, txt_name, txt_phone, txt_username, txt_password, txt_password_confirm):
        """Đăng ký khuôn mặt với Live Camera Preview + Auto Capture + Form Validation"""
        
        # ==================== VALIDATION ====================
        name = txt_name.value.strip() if txt_name.value else ""
        phone = txt_phone.value.strip() if txt_phone.value else ""
        username = txt_username.value.strip() if txt_username.value else ""
        password = txt_password.value.strip() if txt_password.value else ""
        password_confirm = txt_password_confirm.value.strip() if txt_password_confirm.value else ""
        
        if not name:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Vui lòng nhập HỌ TÊN trước khi đăng ký khuôn mặt!"), bgcolor=ft.Colors.ORANGE_600))
            self.page.update()
            return
        if not phone:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Vui lòng nhập SỐ ĐIỆN THOẠI trước khi đăng ký khuôn mặt!"), bgcolor=ft.Colors.ORANGE_600))
            self.page.update()
            return
        if not username:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Vui lòng nhập TÊN ĐĂNG NHẬP trước khi đăng ký khuôn mặt!"), bgcolor=ft.Colors.ORANGE_600))
            self.page.update()
            return
        if not password:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Vui lòng nhập MẬT KHẨU trước khi đăng ký khuôn mặt!"), bgcolor=ft.Colors.ORANGE_600))
            self.page.update()
            return
        if not password_confirm:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Vui lòng NHẬP LẠI MẬT KHẨU trước khi đăng ký khuôn mặt!"), bgcolor=ft.Colors.ORANGE_600))
            self.page.update()
            return
        if password != password_confirm:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Mật khẩu nhập lại không khớp!"), bgcolor=ft.Colors.RED_600))
            self.page.update()
            return
        
        # Tạo driver_id tự động
        import os
        import json
        try:
            accounts_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "accounts.json")
            if os.path.exists(accounts_path):
                with open(accounts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"admin_accounts": [], "user_accounts": []}
            
            # Kiểm tra username đã tồn tại chưa
            for acc in data.get("user_accounts", []):
                if acc["username"] == username:
                    self.page.open(ft.SnackBar(ft.Text("❌ Tên đăng nhập đã tồn tại!"), bgcolor=ft.Colors.RED_600))
                    self.page.update()
                    return
            
            # Tự động tạo driver_id - FIXED: Tìm ID lớn nhất thay vì đếm số lượng
            existing_ids = [acc.get("driver_id", "") for acc in data.get("user_accounts", [])]
            
            # Lọc ra các ID dạng "TXNNN" và lấy số
            id_numbers = []
            for id_str in existing_ids:
                if id_str.startswith("TX") and len(id_str) >= 3:
                    try:
                        num = int(id_str[2:])  # Lấy phần số sau "TX"
                        id_numbers.append(num)
                    except ValueError:
                        continue
            
            # Tìm số lớn nhất và cộng 1
            next_number = max(id_numbers) + 1 if id_numbers else 1
            driver_id = f"TX{next_number:03d}"
            
            print(f"✅ [ID GENERATION] Existing IDs: {existing_ids}")
            print(f"✅ [ID GENERATION] Max number: {max(id_numbers) if id_numbers else 0}")
            print(f"✅ [ID GENERATION] New driver_id: {driver_id}")
        except Exception as e:
            print(f"❌ [VALIDATION] Error: {e}")
            driver_id = "TX999"
        
        # ==================== CAMERA PREVIEW ====================
        import cv2
        import tempfile
        from pathlib import Path
        from src.BUS.ai_core.login_user.camera_preview import LiveCameraPreview
        
        print("\n" + "="*70)
        print(f"📷 [FACE REGISTER] Bắt đầu đăng ký khuôn mặt cho {username}")
        print("="*70)
        
        # UI Elements
        dialog_message = ft.Text(
            "🔄 Đang tải AI model và khởi động camera...", 
            size=15, 
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
            text_align=ft.TextAlign.CENTER
        )
        
        # Camera view với placeholder
        camera_view = ft.Image(
            width=480,
            height=360,
            fit=ft.ImageFit.CONTAIN,
            border_radius=15,
            # Placeholder: 1x1 transparent PNG
            src_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        btn_close = ft.ElevatedButton(
            "Đóng",
            icon=ft.Icons.CLOSE,
            bgcolor=ft.Colors.RED_400,
            color=ft.Colors.WHITE,
            on_click=lambda e: close_dialog()
        )
        
        # Progress indicator
        progress_ring = ft.ProgressRing(visible=True, width=30, height=30, color=ft.Colors.BLUE_700)
        
        # Dialog
        face_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.FACE_RETOUCHING_NATURAL, color=ft.Colors.GREEN_700, size=30),
                ft.Text("Đăng Ký Khuôn Mặt", weight=ft.FontWeight.BOLD, size=20),
            ]),
            content=ft.Container(
                width=660,
                height=650,
                content=ft.Column([
                    # Loading message BÊN NGOÀI khung camera
                    ft.Row([
                        progress_ring,
                        ft.Container(width=10),
                        dialog_message
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Container(height=10),
                    
                    # Camera view với border đẹp
                    ft.Container(
                        content=camera_view,
                        border=ft.border.all(3, ft.Colors.GREEN_700),
                        border_radius=15,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=15,
                            color=ft.Colors.with_opacity(0.3, ft.Colors.GREEN_700)
                        )
                    ),
                    
                    ft.Container(height=15),
                    
                    # Hướng dẫn với icons
                    ft.Container(
                        padding=15,
                        bgcolor=ft.Colors.GREEN_50,
                        border_radius=10,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.GREEN_700, size=20),
                                ft.Text("Hướng dẫn:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                            ]),
                            ft.Container(height=5),
                            ft.Text("• Đặt khuôn mặt vào khung oval màu trắng", size=13, color=ft.Colors.GREEN_800),
                            ft.Text("• Giữ yên khi khung chuyển sang màu xanh", size=13, color=ft.Colors.GREEN_800),
                            ft.Text("• Hệ thống sẽ tự động chụp ảnh", size=13, color=ft.Colors.GREEN_800),
                        ], spacing=3)
                    ),
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            actions=[btn_close],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
        
        # MỞ DIALOG NGAY LẬP TỨC (trước khi load model)
        self.page.open(face_dialog)
        self.page.update()
        
        # Camera preview instance
        camera = None
        processing = False
        frame_counter = 0
        
        # LOAD MODEL VÀ CAMERA TRONG BACKGROUND THREAD
        def initialize_ai_and_camera():
            """Load AI model và khởi động camera trong background"""
            nonlocal camera
            
            try:
                # BƯỚC 1: Load AI Model
                dialog_message.value = "🤖 Đang tải AI model..."
                dialog_message.update()
                
                print("\n🔧 [OPTIMIZATION] Getting ArcFace model instance...")
                config = {
                    'confidence_threshold': 0.5,
                    'min_face_size': 30,
                    'cosine_threshold': 0.5
                }
                
                arcface_model = get_arcface_model(config)
                
                if arcface_model is None:
                    print("❌ [CRITICAL ERROR] Failed to get ArcFace model")
                    dialog_message.value = "❌ Lỗi: Không thể khởi tạo AI model"
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                    dialog_message.update()
                    progress_ring.update()
                    return
                
                print("✅ [OPTIMIZATION] Model ready!")
                
                # BƯỚC 2: Khởi động Camera
                dialog_message.value = "📷 Đang khởi động camera..."
                dialog_message.update()
                
                camera = LiveCameraPreview(camera_index=0)
                success = camera.start(
                    on_frame_callback=update_frame,
                    on_auto_capture=lambda frame: on_auto_capture(frame, arcface_model)
                )
                
                if success:
                    dialog_message.value = "✅ Camera sẵn sàng - Hãy đặt mặt vào khung oval"
                    dialog_message.color = ft.Colors.GREEN_700
                    progress_ring.visible = False
                else:
                    dialog_message.value = "❌ Không thể mở camera"
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                
                dialog_message.update()
                progress_ring.update()
                
            except Exception as ex:
                print(f"❌ [INIT ERROR]: {ex}")
                traceback.print_exc()
                
                dialog_message.value = f"❌ Lỗi: {str(ex)}"
                dialog_message.color = ft.Colors.RED
                progress_ring.visible = False
                dialog_message.update()
                progress_ring.update()


        
        def update_frame(base64_img: str):
            """Update camera view với frame mới - Batch update mỗi 2 frames"""
            nonlocal frame_counter
            try:
                frame_counter += 1
                camera_view.src_base64 = base64_img.split(",")[1]  # Remove data:image/jpeg;base64,
                # Chỉ update UI mỗi 2 frames để giảm overhead (-50% UI calls)
                if frame_counter % 2 == 0:
                    camera_view.update()
            except Exception as e:
                print(f"⚠️  [FRAME UPDATE] Error: {e}")
        
        def on_auto_capture(frame: 'np.ndarray', arcface_model):
            """Callback khi tự động chụp ảnh - RUN IN BACKGROUND THREAD"""
            nonlocal processing
            
            if processing:
                return
            
            processing = True
            
            # Update UI ngay lập tức
            dialog_message.value = "✅ Phát hiện khuôn mặt! Đang xử lý..."
            dialog_message.color = ft.Colors.GREEN
            progress_ring.visible = True
            dialog_message.update()
            progress_ring.update()
            
            # CRITICAL FIX: Chạy xử lý nặng trong background thread
            # Tránh block camera thread
            def process_face_registration():
                nonlocal processing
                try:
                    # Lưu ảnh tạm
                    temp_dir = tempfile.gettempdir()
                    captured_image_path = str(Path(temp_dir) / "face_register_auto.jpg")
                    cv2.imwrite(captured_image_path, frame)
                    
                    # OPTIMIZATION: Sử dụng model đã khởi tạo sẵn
                    # Không cần load lại!
                    
                    # Lấy thông tin user từ form (real data)
                    user_data = {
                        'username': username,
                        'password': password,  
                        'name': name,
                        'phone': phone,
                        'driver_id': driver_id
                    }
                    
                    print(f"✅ [USER DATA] Using form data: {name} ({username}) - {driver_id}")
                    
                    # Register face với model đã sẵn sàng
                    success = arcface_model.register_face(captured_image_path, user_data)
                    
                    if success:
                        dialog_message.value = "✅ Đăng ký khuôn mặt thành công!"
                        dialog_message.color = ft.Colors.GREEN
                        
                        # Show success snackbar
                        self.page.open(ft.SnackBar(
                            ft.Text("✅ Đăng ký khuôn mặt thành công! Đang chuyển về màn hình đăng nhập..."),
                            bgcolor=ft.Colors.GREEN_600
                        ))
                        
                        # Đóng dialog
                        import time
                        time.sleep(1.5)
                        close_dialog()
                        
                        # Reset tất cả textbox về rỗng
                        txt_name.value = ""
                        txt_phone.value = ""
                        txt_username.value = ""
                        txt_password.value = ""
                        txt_password_confirm.value = ""
                        
                        # Update textboxes
                        txt_name.update()
                        txt_phone.update()
                        txt_username.update()
                        txt_password.update()
                        txt_password_confirm.update()
                        
                        # Chờ 0.5s để user thấy form đã reset
                        time.sleep(0.5)
                        
                        # Chuyển về màn hình đăng nhập
                        self.show_login_view()
                    else:
                        # CRITICAL FIX: Reset camera để cho phép thử lại ngay
                        dialog_message.value = "❌ Không thể đăng ký. Giữ nguyên vị trí và thử lại!"
                        dialog_message.color = ft.Colors.ORANGE_600
                        processing = False
                        
                        # Reset camera capture state
                        if camera:
                            camera.reset_capture()
                    
                    progress_ring.visible = False
                    dialog_message.update()
                    progress_ring.update()
                    self.page.update()
                    
                except Exception as ex:
                    print(f"❌ [ERROR] Face registration failed: {ex}")
                    dialog_message.value = f"❌ Lỗi: {str(ex)}. Giữ nguyên vị trí và thử lại!"
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                    processing = False
                    
                    # Reset camera để cho phép thử lại
                    if camera:
                        camera.reset_capture()
                    
                    dialog_message.update()
                    progress_ring.update()
            
            # Chạy trong background thread
            import threading
            process_thread = threading.Thread(target=process_face_registration, daemon=True)
            process_thread.start()
        
        def close_dialog():
            """Đóng dialog và dừng camera"""
            nonlocal camera
            if camera:
                camera.stop()
            self.page.close(face_dialog)
            self.page.update()
        
        # Mở dialog
        self.page.open(face_dialog)
        self.page.update()
        
        # Khởi động AI model và camera trong background thread
        import threading
        import traceback
        init_thread = threading.Thread(target=initialize_ai_and_camera, daemon=True)
        init_thread.start()

    
    def _handle_face_login(self):
        """Đăng nhập bằng khuôn mặt - Tự động quét tất cả accounts"""
        import cv2
        import tempfile
        import os
        import json
        from pathlib import Path
        from src.BUS.ai_core.login_user.camera_preview import LiveCameraPreview
        
        # UI Elements
        dialog_message = ft.Text(
            "Đang khởi động camera...", 
            size=14,
            color=ft.Colors.BLACK,
            text_align=ft.TextAlign.CENTER
        )
        camera_view = ft.Image(
            width=480,
            height=360,
            fit=ft.ImageFit.CONTAIN,
            border_radius=15,
            # Placeholder 1x1 transparent PNG
            src_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        btn_close = ft.ElevatedButton(
            "Đóng",
            icon=ft.Icons.CLOSE,
            bgcolor=ft.Colors.RED_400,
            color=ft.Colors.WHITE,
            on_click=lambda e: close_dialog()
        )
        
        # Progress indicator
        progress_ring = ft.ProgressRing(visible=False, width=40, height=40)
        
        # Dialog
        face_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.FACE_RETOUCHING_NATURAL, color=ft.Colors.BLUE_700, size=30),
                ft.Text("Đăng Nhập Khuôn Mặt", weight=ft.FontWeight.BOLD, size=20),
            ]),
            content=ft.Container(
                width=660,
                height=600,
                content=ft.Column([
                    dialog_message,
                    ft.Container(height=10),
                    
                    # Camera view
                    ft.Container(
                        content=camera_view,
                        border=ft.border.all(3, ft.Colors.BLUE_700),
                        border_radius=15,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=15,
                            color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_700)
                        )
                    ),
                    
                    ft.Container(height=15),
                    
                    # Hướng dẫn
                    ft.Container(
                        padding=15,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=10,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=20),
                                ft.Text("Hướng dẫn:", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                            ]),
                            ft.Container(height=5),
                            ft.Text("• Đặt khuôn mặt vào khung oval màu trắng", size=13, color=ft.Colors.BLUE_800),
                            ft.Text("• Giữ yên khi khung chuyển sang màu xanh", size=13, color=ft.Colors.BLUE_800),
                            ft.Text("• Hệ thống sẽ tự động nhận diện", size=13, color=ft.Colors.BLUE_800),
                        ], spacing=3)
                    ),
                    
                    ft.Container(height=10),
                    
                    # Progress
                    ft.Row([
                        progress_ring
                    ], alignment=ft.MainAxisAlignment.CENTER)
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            actions=[btn_close],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Camera preview instance
        camera = None
        processing = False
        frame_counter = 0
        
        def update_frame(base64_img: str):
            """Update camera view - Batch update mỗi 2 frames"""
            nonlocal frame_counter

            # Chỉ log mỗi 30 frames để tránh lag
            if frame_counter % 30 == 0:
                print(f"🎥 [UPDATE_FRAME] Called! Counter: {frame_counter}")

            try:
                frame_counter += 1
                camera_view.src_base64 = base64_img.split(",")[1]
                if frame_counter % 2 == 0:
                    camera_view.update()
                    
                    # Chỉ log mỗi 30 frames
                    if frame_counter % 30 == 0:
                        print(f"✅ [UPDATE_FRAME] Frame #{frame_counter} updated")
            except Exception as e:
                print(f"⚠️  [FRAME UPDATE] Error: {e}")
        
        def on_auto_capture(frame: 'np.ndarray'):
            """Callback khi tự động chụp ảnh - Quét tất cả accounts"""
            nonlocal processing
            
            print(f"\n{'='*70}")
            print(f"📷 [CALLBACK] on_auto_capture được gọi! Frame shape: {frame.shape}")
            print(f"{'='*70}")
            
            if processing:
                print(f"⚠️  [CALLBACK] Already processing, skipping...")
                return
            
            processing = True
            
            # Update UI
            dialog_message.value = "🔍 Đang quét khuôn mặt..."
            dialog_message.color = ft.Colors.ORANGE
            progress_ring.visible = True
            dialog_message.update()
            progress_ring.update()
            
            print(f"✅ [CALLBACK] UI updated, starting background thread...")
            
            def process_face_login():
                nonlocal processing
                print(f"\n🚀 [THREAD] process_face_login thread started!")
                try:
                    # Lưu ảnh tạm
                    print(f"💾 [SAVE] Saving captured image...")
                    temp_dir = tempfile.gettempdir()
                    captured_image_path = str(Path(temp_dir) / "face_login_auto.jpg")
                    cv2.imwrite(captured_image_path, frame)
                    print(f"✅ [SAVE] Image saved to: {captured_image_path}")
                    
                    # Load config from central config file
                    print(f"📂 [CONFIG] Loading model configuration...")
                    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "model_config.json")
                    
                    model_name = "ArcFace (v2.1)"  # Default
                    config = {
                        'confidence_threshold': 0.75,
                        'min_face_size': 40,
                        'cosine_threshold': 0.3
                    }
                    
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            model_config = json.load(f)
                            face_config = model_config.get("face_recognition", {})
                            
                            # Get model name from config
                            model_name = face_config.get('model_name', 'ArcFace (v2.1)')
                            
                            config = {
                                'confidence_threshold': face_config.get('confidence_threshold', 0.75),
                                'min_face_size': face_config.get('min_face_size', 40),
                                'cosine_threshold': face_config.get('cosine_threshold', 0.3)
                            }
                            print(f"✅ [CONFIG] Loaded from model_config.json:")
                            print(f"   ├─ Model: {model_name}")
                            print(f"   ├─ Confidence: {config['confidence_threshold']}")
                            print(f"   ├─ Min Face Size: {config['min_face_size']}px")
                            print(f"   └─ Cosine Threshold: {config['cosine_threshold']}")
                    except FileNotFoundError:
                        print(f"⚠️  [CONFIG] model_config.json not found, using defaults")
                    except Exception as e:
                        print(f"⚠️  [CONFIG] Error loading config: {e}, using defaults")
                    
                    # Load model dynamically based on model_name
                    print(f"\n🤖 [MODEL] Loading {model_name}...")
                    model = None
                    
                    if "ArcFace" in model_name:
                        # Sử dụng singleton model
                        model = get_arcface_model(config)
                        if model:
                            print(f"✅ [MODEL] ArcFace model loaded successfully!")
                        else:
                            print(f"❌ [MODEL ERROR] Failed to get ArcFace model")

                        
                    elif "FaceNet" in model_name:
                        print(f"❌ [MODEL ERROR] FaceNet chưa được triển khai!")
                        print(f"   Vui lòng chọn ArcFace trong Model Test UI")
                        
                        # Update UI
                        dialog_message.value = "❌ Model FaceNet chưa được hỗ trợ!\nVui lòng chọn ArcFace trong cài đặt."
                        dialog_message.color = ft.Colors.RED
                        progress_ring.visible = False
                        processing = False
                        dialog_message.update()
                        progress_ring.update()
                        return  # Stop execution
                        
                    elif "DeepFace" in model_name:
                        print(f"❌ [MODEL ERROR] DeepFace chưa được triển khai!")
                        print(f"   Vui lòng chọn ArcFace trong Model Test UI")
                        
                        # Update UI
                        dialog_message.value = "❌ Model DeepFace chưa được hỗ trợ!\nVui lòng chọn ArcFace trong cài đặt."
                        dialog_message.color = ft.Colors.RED
                        progress_ring.visible = False
                        processing = False
                        dialog_message.update()
                        progress_ring.update()
                        return  # Stop execution
                    
                    else:
                        print(f"❌ [MODEL ERROR] Unknown model: {model_name}")
                        
                        # Update UI
                        dialog_message.value = f"❌ Model không xác định: {model_name}"
                        dialog_message.color = ft.Colors.RED
                        progress_ring.visible = False
                        processing = False
                        dialog_message.update()
                        progress_ring.update()
                        return  # Stop execution
                    
                    # Final check if model loaded successfully
                    if model is None:
                        print(f"❌ [MODEL ERROR] Failed to load model: {model_name}")
                        print(f"   This should not happen if model_name is correct")
                        
                        # Update UI
                        dialog_message.value = f"❌ Lỗi: Không thể load model {model_name}"
                        dialog_message.color = ft.Colors.RED
                        progress_ring.visible = False
                        processing = False
                        dialog_message.update()
                        progress_ring.update()
                        return
                    
                    # Đọc tất cả user accounts
                    print(f"📂 [FILE] Loading accounts.json...")
                    accounts_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "accounts.json")
                    print(f"📂 [FILE] Path: {accounts_path}")
                    with open(accounts_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        user_accounts = data.get("user_accounts", [])
                    
                    print(f"🔍 [SCAN] Đang quét {len(user_accounts)} tài khoản...")
                    dialog_message.value = "🔍 Đang tải AI models..."
                    dialog_message.update()
                    
                    # Quét từng account
                    matched_account = None
                    best_similarity = 0.0
                    accounts_with_face = [acc for acc in user_accounts if acc.get('face_data')]
                    total_accounts = len(accounts_with_face)
                    
                    print(f"🔍 [SCAN] Tìm thấy {total_accounts} tài khoản có face data")
                    
                    for idx, account in enumerate(accounts_with_face, 1):
                        username = account['username']
                        password = account['password']  # Lấy password từ JSON
                        
                        # Update UI với progress
                        dialog_message.value = f"🔍 Đang quét ({idx}/{total_accounts}): {account.get('name', username)}..."
                        dialog_message.update()
                        
                        print(f"  → [{idx}/{total_accounts}] Kiểm tra: {username}")
                        
                        try:
                            # Verify face
                            matched, similarity = model.verify_face(
                                captured_image_path,
                                username,
                                password
                            )
                            
                            print(f"    Similarity: {similarity:.2%} ({'✅ MATCH' if matched else '❌ NO MATCH'})")
                            
                            if matched and similarity > best_similarity:
                                best_similarity = similarity
                                matched_account = account
                                
                                # Early termination nếu match rất cao (>90%)
                                if similarity > 0.90:
                                    print(f"    ⚡ High confidence match! Early termination.")
                                    break
                        
                        except Exception as e:
                            print(f"    ⚠️  Lỗi khi verify {username}: {e}")
                            continue
                    
                    # Kết quả
                    if matched_account:
                        print(f"\n✅ [SUCCESS] Tìm thấy: {matched_account['name']} ({best_similarity:.2%})")
                        
                        dialog_message.value = f"✅ Xin chào {matched_account['name']}!"
                        dialog_message.color = ft.Colors.GREEN
                        
                        # Show success snackbar
                        self.page.open(ft.SnackBar(
                            ft.Text(f"✅ Đăng nhập thành công! Xin chào {matched_account['name']}"),
                            bgcolor=ft.Colors.GREEN_600
                        ))
                        
                        # Đóng dialog và chuyển trang
                        import time
                        time.sleep(1.5)
                        close_dialog()
                        
                        # Chuyển sang main user với thông tin tài khoản
                        self.page.controls.clear()
                        self.page.update()
                        laucher_user.main(self.page, self.go_back_callback, user_account=matched_account)
                    else:
                        print(f"\n❌ [FAILED] Không tìm thấy khuôn mặt khớp")
                        
                        dialog_message.value = "❌ Không tìm thấy khuôn mặt trong hệ thống"
                        dialog_message.color = ft.Colors.RED
                        processing = False
                    
                    progress_ring.visible = False
                    dialog_message.update()
                    progress_ring.update()
                    self.page.update()
                    
                except FileNotFoundError:
                    print(f"❌ [ERROR] Không tìm thấy file accounts.json")
                    dialog_message.value = "❌ Lỗi: Không tìm thấy dữ liệu tài khoản"
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                    processing = False
                    dialog_message.update()
                    progress_ring.update()
                except Exception as ex:
                    print(f"❌ [ERROR] Face login failed: {ex}")
                    import traceback
                    traceback.print_exc()
                    dialog_message.value = f"❌ Lỗi: {str(ex)}"
                    dialog_message.color = ft.Colors.RED
                    progress_ring.visible = False
                    processing = False
                    dialog_message.update()
                    progress_ring.update()
            
            # Chạy trong background thread
            # Start background thread
            print(f"🧵 [THREAD] Creating thread...")
            process_thread = threading.Thread(target=process_face_login, daemon=True)
            print(f"🧵 [THREAD] Starting thread...")
            process_thread.start()
            print(f"✅ [THREAD] Thread started successfully!")
        
        def close_dialog():
            """Đóng dialog và dừng camera"""
            nonlocal camera
            if camera:
                camera.stop()
            self.page.close(face_dialog)
            self.page.update()
        
        # Mở dialog
        self.page.open(face_dialog)
        self.page.update()
        
        # Khởi động camera
        try:
            camera = LiveCameraPreview(camera_index=0)
            success = camera.start(
                on_frame_callback=update_frame,
                on_auto_capture=on_auto_capture
            )
            
            if success:
                dialog_message.value = "✅ Camera sẵn sàng - Hãy đặt mặt vào khung oval"
                dialog_message.color = ft.Colors.GREEN_700
                dialog_message.update()
            else:
                dialog_message.value = "❌ Không thể mở camera"
                dialog_message.color = ft.Colors.RED
                dialog_message.update()
                
        except Exception as ex:
            dialog_message.value = f"❌ Lỗi camera: {str(ex)}"
            dialog_message.color = ft.Colors.RED
            dialog_message.update()
            print(f"❌ [CAMERA ERROR]: {ex}")


# --- Entry Point ---
def main(page: ft.Page, go_back_callback=None):
    UserUI(page, go_back_callback)

if __name__ == "__main__":
    ft.app(target=main)