# -*- coding: utf-8 -*-
"""
ThongBaoService - Telegram Notification Service
Tách logic Telegram từ GUI, cung cấp các hàm gửi tin nhắn, log và xử lý command.
"""

import json
import os
import requests
import threading
import time
import html
from datetime import datetime
from typing import Optional, Dict, List, Any

# ===== PATH CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
LOG_FILE_PATH = os.path.join(DATA_DIR, "thong_bao_log.json")
API_CONFIG_PATH = os.path.join(DATA_DIR, "API.json")

# ===== CONSTANTS =====
MAX_LOG_RECORDS = 700


class ThongBaoService:
    """
    Telegram Notification Service
    Cung cấp các chức năng gửi tin nhắn, kiểm tra kết nối, lưu log và xử lý command.
    """
    
    def __init__(self):
        self._start_time = datetime.now()
        self._alert_enabled = True
        self._debug_mode = False
        self._config = self._load_api_config()
    
    def _load_api_config(self) -> Dict:
        """Load cấu hình từ API.json"""
        try:
            if os.path.exists(API_CONFIG_PATH):
                with open(API_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            "telegram": {
                "bot_token": "",
                "chat_id": ""
            }
        }
    
    def _save_api_config(self) -> bool:
        """Lưu cấu hình vào API.json"""
        try:
            os.makedirs(os.path.dirname(API_CONFIG_PATH), exist_ok=True)
            with open(API_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False
    
    # ==================== CORE TELEGRAM METHODS ====================
    
    def send_message(self, token: str, chat_id: str, message: str) -> Dict:
        """
        Gửi tin nhắn đến Telegram chat
        
        Args:
            token: Bot token
            chat_id: Chat ID đích
            message: Nội dung tin nhắn (hỗ trợ HTML)
            
        Returns:
            Dict với key 'ok' và 'result' hoặc 'error'
        """
        error_msg = ""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            # Lưu log
            log_data = {
                "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "chat_id": chat_id,
                "content": message[:200] if len(message) > 200 else message,
                "status": "success" if result.get("ok") else "fail",
                "error": "" if result.get("ok") else result.get("description", "Unknown error")
            }
            self.save_log(log_data)
            
            return result
        except Exception as e:
            error_msg = str(e)
            # Lưu log lỗi
            log_data = {
                "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "chat_id": chat_id,
                "content": message[:200] if len(message) > 200 else message,
                "status": "fail",
                "error": error_msg
            }
            self.save_log(log_data)
            return {"ok": False, "error": error_msg}
    
    def test_connection(self, token: str) -> Dict:
        """
        Kiểm tra kết nối Telegram Bot
        
        Args:
            token: Bot token
            
        Returns:
            Dict với thông tin bot hoặc lỗi
        """
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    # ==================== LOG METHODS ====================
    
    def save_log(self, data: Dict) -> bool:
        """
        Lưu log vào file JSON
        
        Args:
            data: Dict chứa time, chat_id, content, status, error
            
        Returns:
            True nếu thành công
        """
        try:
            # Đọc log hiện tại
            logs = self.load_log()
            
            # Thêm record mới vào cuối danh sách
            logs.append(data)
            
            # Giới hạn tối đa 700 records, xóa log cũ nhất ở đầu
            if len(logs) > MAX_LOG_RECORDS:
                logs = logs[-MAX_LOG_RECORDS:]
            
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            
            # Ghi file
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump({"logs": logs}, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            if self._debug_mode:
                print(f"[DEBUG] save_log error: {e}")
            return False
    
    def load_log(self) -> List[Dict]:
        """
        Đọc log từ file JSON
        
        Returns:
            List các record log
        """
        try:
            if os.path.exists(LOG_FILE_PATH):
                with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("logs", [])
        except Exception as e:
            if self._debug_mode:
                print(f"[DEBUG] load_log error: {e}")
        return []
    
    def clear_log(self) -> bool:
        """Xóa toàn bộ log"""
        try:
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump({"logs": []}, f, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    # ==================== COMMAND HANDLING ====================
    
    def handle_command(self, cmd: str, chat_id: str) -> str:
        """
        Xử lý Telegram command
        
        Args:
            cmd: Command string (e.g., "/start", "/status")
            chat_id: Chat ID của người gửi
            
        Returns:
            Text phản hồi
        """
        cmd = cmd.strip().lower()
        parts = cmd.split()
        command = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        # ===== SYSTEM COMMANDS =====
        if command == "/start":
            return self._cmd_start()
        elif command == "/status":
            return self._cmd_status()
        elif command == "/ping":
            return self._cmd_ping()
        elif command == "/restart":
            return self._cmd_restart()
        elif command == "/stop":
            return self._cmd_stop()
        elif command == "/uptime":
            return self._cmd_uptime()
        
        # ===== ALERT COMMANDS =====
        elif command == "/alert_on":
            return self._cmd_alert_on()
        elif command == "/alert_off":
            return self._cmd_alert_off()
        elif command == "/set_alert":
            return self._cmd_set_alert(args)
        elif command == "/test_alert":
            return self._cmd_test_alert(chat_id)
        
        # ===== CONFIG COMMANDS =====
        elif command == "/config":
            return self._cmd_config()
        elif command == "/set_chatid":
            return self._cmd_set_chatid(args)
        
        # ===== DEBUG COMMANDS =====
        elif command == "/log":
            return self._cmd_log()
        elif command == "/debug_on":
            return self._cmd_debug_on()
        elif command == "/debug_off":
            return self._cmd_debug_off()
        
        else:
            return self._cmd_help()
    
    # ===== SYSTEM COMMAND IMPLEMENTATIONS =====
    
    def _cmd_start(self) -> str:
        return """🤖 <b>Hệ thống Giám sát Lái xe</b>

Chào mừng bạn đến với bot thông báo!

<b>📋 Các lệnh có sẵn:</b>

<b>🔧 Hệ thống:</b>
/status - Trạng thái hệ thống
/ping - Kiểm tra kết nối
/uptime - Thời gian hoạt động
/restart - Khởi động lại
/stop - Dừng hệ thống

<b>🔔 Cảnh báo:</b>
/alert_on - Bật cảnh báo
/alert_off - Tắt cảnh báo
/set_alert N T - Đặt ngưỡng
/test_alert - Gửi cảnh báo test

<b>⚙️ Cấu hình:</b>
/config - Xem cấu hình
/set_chatid [ID] - Đổi chat ID

<b>🐛 Debug:</b>
/log - Xem log gần nhất
/debug_on - Bật chế độ debug
/debug_off - Tắt chế độ debug"""
    
    def _cmd_status(self) -> str:
        uptime = datetime.now() - self._start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        alert_status = "🟢 BẬT" if self._alert_enabled else "🔴 TẮT"
        debug_status = "🟢 BẬT" if self._debug_mode else "⚪ TẮT"
        
        return f"""📊 <b>Trạng thái Hệ thống</b>

🔹 <b>Trạng thái:</b> 🟢 Đang hoạt động
🔹 <b>Uptime:</b> {hours}h {minutes}m {seconds}s
🔹 <b>Cảnh báo:</b> {alert_status}
🔹 <b>Debug:</b> {debug_status}
🔹 <b>Thời gian:</b> {datetime.now().strftime("%H:%M:%S %d/%m/%Y")}"""
    
    def _cmd_ping(self) -> str:
        return "🏓 Pong! Bot đang hoạt động bình thường."
    
    def _cmd_restart(self) -> str:
        self._start_time = datetime.now()
        self._alert_enabled = True
        return "🔄 Hệ thống đã được khởi động lại."
    
    def _cmd_stop(self) -> str:
        self._alert_enabled = False
        return "⏹️ Hệ thống đã dừng. Dùng /restart để khởi động lại."
    
    def _cmd_uptime(self) -> str:
        uptime = datetime.now() - self._start_time
        days = uptime.days
        hours, remainder = divmod(int(uptime.total_seconds()) % 86400, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"""⏱️ <b>Thời gian hoạt động</b>

🔹 <b>Uptime:</b> {days} ngày, {hours} giờ, {minutes} phút, {seconds} giây
🔹 <b>Khởi động:</b> {self._start_time.strftime("%H:%M:%S %d/%m/%Y")}"""
    
    # ===== ALERT COMMAND IMPLEMENTATIONS =====
    
    def _cmd_alert_on(self) -> str:
        self._alert_enabled = True
        return "🔔 Đã BẬT cảnh báo."
    
    def _cmd_alert_off(self) -> str:
        self._alert_enabled = False
        return "🔕 Đã TẮT cảnh báo."
    
    def _cmd_set_alert(self, args: List[str]) -> str:
        if len(args) < 2:
            return "⚠️ Cú pháp: /set_alert N T\n\nN = số lần cảnh báo, T = thời gianeran (giây)"
        try:
            n = int(args[0])
            t = int(args[1])
            return f"✅ Đã đặt ngưỡng: {n} lần trong {t} giây"
        except ValueError:
            return "❌ Tham số không hợp lệ. N và T phải là số."
    
    def _cmd_test_alert(self, chat_id: str) -> str:
        return f"""🚨 <b>CẢNH BÁO TEST</b>

⚠️ <b>Loại:</b> Phát hiện buồn ngủ
👤 <b>Tài xế:</b> Nguyễn Văn A
🚗 <b>Biển số:</b> 30A-12345
📍 <b>Vị trí:</b> Quốc lộ 1A, Km 52
⏰ <b>Thời gian:</b> {datetime.now().strftime("%H:%M:%S %d/%m/%Y")}

<i>Đây là tin nhắn test từ Hệ thống Giám sát Lái xe</i>"""
    
    # ===== CONFIG COMMAND IMPLEMENTATIONS =====
    
    def _cmd_config(self) -> str:
        telegram_config = self._config.get("telegram", {})
        chat_id = telegram_config.get("chat_id", "N/A")
        token = telegram_config.get("bot_token", "")
        token_masked = token[:10] + "..." + token[-5:] if len(token) > 20 else "N/A"
        
        return f"""⚙️ <b>Cấu hình hiện tại</b>

🔹 <b>Chat ID:</b> {chat_id}
🔹 <b>Bot Token:</b> {token_masked}
🔹 <b>Log file:</b> {os.path.basename(LOG_FILE_PATH)}
🔹 <b>Max logs:</b> {MAX_LOG_RECORDS}"""
    
    def _cmd_set_chatid(self, args: List[str]) -> str:
        if not args:
            return "⚠️ Cú pháp: /set_chatid [ID]\n\nVí dụ: /set_chatid 123456789"
        
        new_id = args[0]
        if not new_id.lstrip('-').isdigit():
            return "❌ Chat ID không hợp lệ. Phải là số."
        
        self._config.setdefault("telegram", {})["chat_id"] = new_id
        if self._save_api_config():
            return f"✅ Đã cập nhật Chat ID thành: {new_id}"
        else:
            return "❌ Không thể lưu cấu hình."
    
    # ===== DEBUG COMMAND IMPLEMENTATIONS =====
    
    def _cmd_log(self) -> str:
        """
        Xem 5 log gần nhất (mới nhất → cũ nhất)
        An toàn với file JSON hỏng hoặc rỗng
        """
        try:
            logs = self.load_log()
        except Exception:
            return "⚠️ Lỗi đọc log\n\nFile log bị hỏng hoặc không thể đọc."
        
        if not logs:
            return "📋 Log trống\n\nChưa có log nào được ghi."
        
        # Lấy 5 log mới nhất và đảo thứ tự (mới → cũ)
        recent_logs = logs[-5:][::-1]
        log_text = "📋 5 Log gần nhất\n\n"
        
        for i, log in enumerate(recent_logs, 1):
            try:
                status_icon = "✅" if log.get("status") == "success" else "❌"
                time_str = str(log.get('time', 'N/A'))
                content = str(log.get('content', ''))
                # Escape HTML để tránh lỗi parse
                content = html.escape(content)
                log_text += f"{i}. {status_icon} {time_str}\n"
                log_text += f"   {content}\n\n"
            except Exception:
                log_text += f"{i}. ⚠️ Lỗi đọc log\n\n"
        
        return log_text
    
    def _cmd_debug_on(self) -> str:
        self._debug_mode = True
        return "🐛 Đã BẬT chế độ debug."
    
    def _cmd_debug_off(self) -> str:
        self._debug_mode = False
        return "🐛 Đã TẮT chế độ debug."
    
    def _cmd_help(self) -> str:
        return """❓ <b>Lệnh không hợp lệ</b>

Dùng /start để xem danh sách các lệnh có sẵn."""
    
    # ==================== UPDATE HANDLER ====================
    
    def process_update(self, update_json: Dict) -> Optional[str]:
        """
        Xử lý update từ Telegram
        
        Args:
            update_json: Update object từ Telegram API
            
        Returns:
            Text phản hồi hoặc None nếu không phải command
        """
        try:
            message = update_json.get("message", {})
            text = message.get("text", "")
            chat = message.get("chat", {})
            chat_id = str(chat.get("id", ""))
            
            if not text or not chat_id:
                return None
            
            # Kiểm tra nếu là command
            if text.startswith("/"):
                response = self.handle_command(text, chat_id)
                return response
            
            return None
        except Exception as e:
            if self._debug_mode:
                print(f"[DEBUG] process_update error: {e}")
            return None
    
    # ==================== UTILITY METHODS ====================
    
    def is_alert_enabled(self) -> bool:
        """Kiểm tra trạng thái cảnh báo"""
        return self._alert_enabled
    
    def get_default_token(self) -> str:
        """Lấy bot token từ config"""
        return self._config.get("telegram", {}).get("bot_token", "")
    
    def get_default_chat_id(self) -> str:
        """Lấy chat ID từ config"""
        return self._config.get("telegram", {}).get("chat_id", "")


# ===== SINGLETON INSTANCE =====
_service_instance: Optional[ThongBaoService] = None


def get_thong_bao_service() -> ThongBaoService:
    """Lấy singleton instance của ThongBaoService"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ThongBaoService()
    return _service_instance


# ===== AUTO-START TELEGRAM BOT =====
_bot_started = False
_bot_lock = threading.Lock()


def _telegram_polling_loop():
    """Long polling loop để nhận và xử lý updates từ Telegram"""
    service = get_thong_bao_service()
    token = service.get_default_token()
    
    if not token:
        print("[TelegramBot] Bot token không được cấu hình. Bot không thể khởi động.")
        return
    
    print("[TelegramBot] Bot đã khởi động với long polling...")
    
    last_update_id = 0
    
    while True:
        try:
            # Gọi getUpdates với timeout
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {
                "offset": last_update_id + 1,
                "timeout": 30
            }
            
            response = requests.get(url, params=params, timeout=35)
            result = response.json()
            
            if not result.get("ok"):
                print(f"[TelegramBot] Lỗi getUpdates: {result.get('description', 'Unknown error')}")
                time.sleep(5)
                continue
            
            updates = result.get("result", [])
            
            for update in updates:
                update_id = update.get("update_id", 0)
                if update_id > last_update_id:
                    last_update_id = update_id
                
                # Xử lý update
                reply = service.process_update(update)
                
                # Nếu có reply, gửi tin nhắn
                if reply:
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = str(chat.get("id", ""))
                    
                    if chat_id:
                        service.send_message(token, chat_id, reply)
        
        except requests.exceptions.Timeout:
            # Timeout là bình thường với long polling
            continue
        except requests.exceptions.RequestException as e:
            print(f"[TelegramBot] Lỗi kết nối: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"[TelegramBot] Lỗi không xác định: {e}")
            time.sleep(5)


def _start_telegram_bot():
    """Khởi động Telegram bot trong background thread"""
    global _bot_started
    
    with _bot_lock:
        if _bot_started:
            return
        _bot_started = True
    
    # Tạo daemon thread để chạy polling loop
    bot_thread = threading.Thread(target=_telegram_polling_loop, daemon=True)
    bot_thread.start()


# Auto-start khi module được import
_start_telegram_bot()


# ===== TEST =====
if __name__ == "__main__":
    service = ThongBaoService()
    
    print("=== Test Commands ===")
    print(service.handle_command("/start", "123"))
    print("\n" + "="*50 + "\n")
    print(service.handle_command("/status", "123"))
    print("\n" + "="*50 + "\n")
    print(service.handle_command("/ping", "123"))

    
