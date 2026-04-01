import sys
import os
import shutil
import csv
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTableWidget, 
                             QTableWidgetItem, QStackedWidget, QComboBox, 
                             QFileDialog, QListWidget, QHeaderView,
                             QAbstractItemView, QLineEdit, QMessageBox, QFrame, QProgressBar,
                             QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor
import time
import json
import tempfile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ส่วนการนำเข้า Firebase พร้อมระบบเช็คไลบรารี
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# ==========================================
# ชุดไอคอน SVG สำหรับ UI
# ==========================================
SVGS = {
    "folder": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-1.22-1.82A2 2 0 0 0 7.53 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>',
    "download": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
    "save": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>',
    "camera": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    "users": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "image": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
    "check_circle": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "server": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19c2.5 0 4.5-2 4.5-4.5 0-2.3-1.7-4.2-4-4.5.3-.6.5-1.3.5-2 0-2.2-1.8-4-4-4-1.4 0-2.7.8-3.4 2C10.3 5.4 9.3 5 8 5 5.8 5 4 6.8 4 9c0 .4.1.8.2 1.2C2.1 10.7 1 12.7 1 15c0 2.2 1.8 4 4 4"/></svg>',
    "list": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>'
}

# ==========================================
# ส่วนของ Folder Watcher
# ==========================================
class PhotoHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            time.sleep(0.5)
            self.callback(event.src_path)

class FolderWatcherThread(QThread):
    new_photo_signal = pyqtSignal(str)

    def __init__(self, watch_dir):
        super().__init__()
        self.watch_dir = watch_dir
        self.observer = None

    def run(self):
        if not self.watch_dir or not os.path.exists(self.watch_dir):
            return
        handler = PhotoHandler(self.emit_new_photo)
        self.observer = Observer()
        self.observer.schedule(handler, self.watch_dir, recursive=False)
        self.observer.start()
        try:
            while self.observer.is_alive():
                self.msleep(500)
        except Exception:
            self.observer.stop()
        self.observer.join()

    def emit_new_photo(self, path):
        valid_extensions = ('.jpg', '.jpeg', '.png', '.raw', '.tif', '.tiff')
        if path.lower().endswith(valid_extensions):
            self.new_photo_signal.emit(path)

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

# ==========================================
# หน้าต่างหลักของโปรแกรม (GUI)
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KMITL Photo Studio - Audit & Sync")
        self.resize(1350, 850)
        
        # ตัวแปรระบบ
        self.src_folder = ""
        self.dest_folder = ""
        self.backup_folder = ""
        self.watcher_thread = None
        self.participants_data = [] 
        self.current_participant = None 
        self.config_file = "app_config.json" 
        
        self.db = None
        self.is_db_connected = False
        
        # Setup UI
        self.setup_ui()
        self.apply_flat_design_style()
        
        # เริ่มการเชื่อมต่อ Firestore
        self.init_firebase()
        self.start_system_timers()
        self.load_config() 
        self.fetch_firebase_data()

    def get_icon(self, name, color="#333333"):
        if not hasattr(self, "icon_dir"):
            self.icon_dir = os.path.join(tempfile.gettempdir(), "photo_manager_icons_v_fixed")
            os.makedirs(self.icon_dir, exist_ok=True)
            
        svg_content = SVGS.get(name, "").replace("{color}", color)
        icon_path = os.path.join(self.icon_dir, f"{name}_{color.replace('#','')}.svg")
        
        if not os.path.exists(icon_path):
            with open(icon_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
                
        return QIcon(icon_path)

    def log_event(self, message, level="INFO"):
        """ ระบบ Audit Log: บันทึกเหตุการณ์ลงใน UI """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {level}: {message}"
        
        item = QListWidgetItem(log_text)
        if level == "ERROR":
            item.setForeground(QColor("#DC3545"))
        elif level == "SUCCESS":
            item.setForeground(QColor("#28A745"))
        elif level == "WARNING":
            item.setForeground(QColor("#E04111"))
        else:
            item.setForeground(QColor("#212529"))
            
        self.audit_list.insertItem(0, item)
        print(log_text)

    def init_firebase(self):
        """ ส่วนสำหรับเชื่อมต่อ Firestore พร้อมระบบ Debug """
        self.log_event("กำลังตรวจสอบสภาพแวดล้อม...", "INFO")
        self.log_event(f"Python Exec: {sys.executable}", "INFO")
        
        if not FIREBASE_AVAILABLE:
            self.log_event("ERROR: ไม่พบโมดูล firebase-admin ใน Python ชุดนี้", "ERROR")
            self.is_db_connected = False
            return

        try:
            # ------------------------------------------------------------------
            # API KEY (Service Account JSON)
            # ------------------------------------------------------------------
            firebase_config = {
                "type": "service_account",
                "project_id": "drawprobase",
                "private_key_id": "a4580d72bc049bee81e040ea34946791dbdb5de4",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCg+JQMX4rHqn6I\nQuf+h6+LkBk6Eq5TFOzCl5QmZb+UmTxWCvkMKfCo/m/Kskdc5iK4nm+9hnRDZwtM\ntlVjD/OWYhglUtn46FbglhlcJP3zGE5xc7HEL2GLZ3ZJi6gD4bs7SexIO9pxD6s3\nwGA0sZkcabbstk3AsLiFTaJw4OaojXlCWdw1gAdN6aFOluamKWMvmpjM9RKRmUSf\nyUt6KIb6ZtDzhytEdUnQqJCL6D3qv/V03txv41aqbO8vMirQvPCv2qoQQZcZZv7c\n5E6ez/AXKrg1PIR/1OsiQkVzmI6JA+eXRpHVB66/22UtjZG+2h/szYKi1/79uegD\nUNWqwD7vAgMBAAECggEAB1miZPg93YUe9vjbIAexD9XaGQk+VYPYlcAXHzO5Lj9a\n/nDM023c09KeZyqB0K+feT+eyZAooeVEIlIXDwls7Xp4MMgaNN/jC6k+6jK0N9Pt\nzQdj4BnrwdJNF+mdF+RISNpExD2baVs2TbrmibFsVNxM4n0mirxnCIs1diMG1T5h\n9XcLGItl+zw07L1L+UuopCMsy7b/sppbCEXL7p0ylGEiq4NDzxjmHD/RFA6qUI/c\nNKLgRLKNM+fLaWXtBR/6A9ExhMCB+UjToUdHzuWfX+ToAdFTHFEKPDoVEo0fd28n\nZWhsjIH1lucrvwS1IjAEfL1iV5fWvBXWTouf0psHWQKBgQDRSt2oe+jOoQIIusXj\nDc/FsKy270vFDY9wneep3HmKl2pjSr2QP+sDPJCmAjTjP5DzNFAuglADSfnM6hXt\n/u4Ox7k6q7+6xaYRPZN6pvmkxll4Q+cFEOAuSrfCULFEquvtSTNuzZI1b1a8a9hZ\nL1uiCA89yV6+uOH87ZCsoSBGiQKBgQDE5Qyvoe/5cdF35ynLNixdvOGRt7IqFyzO\nLd4FVC/5eLJXGt7LMU5q7GJmVeGEkT90KJjeIKmeiJ1IELn+XaKkgGMFZ3/Jx/yP\n2oWlX1rpcsFuluzLTTzOhwOUJhhDRolXobZoSRKol1Q6CtrOUeMfg1DjzFOgALLt\nqVNQEfp7twKBgGcs9SD+FMLodMxA5xUL1gWrFzoHtd6q1K+76FzAp9o+0t+oFNNr\n7ztlPBnatJ/i0l5Sx8Rl0XQNn+v46l6tckYvB4145cf5b+jH5lBsyF0Gu0yijNze\neOXZR8WvafRkHnKXx5c0GIPnI2c38yvkQNQcDQd0ohR7qEy8ALpZpEOhAoGBAKqe\nbbLYmlJHbiQAHjhpNmL4ZWPXkj1lHb+BAa8OeBAvpiNTNpNPo8uGEfLqIuW01A69\ni1KZbULi0aB8ViB1VZZFZwls2dCqS1MBIuTeT7KSbcp+YK3/vVyepNxBcq8BtcxJ\nZv7Rq6iKkkNF2rwFO9K4AWWVTzYMxQCrxXVSTwPbAoGBAK/mqUWprGLUKnXXs34j\nqdSv1LMJ12/I7h7M+MahWm/nRUk0ZCjIx9fSE6dB2C5jWrJlhKz6JFvAGBkdF/Ov\nkzEtsjXx0dzmQFOGvKB3ZJoj3hPPa7mqTO+Wrxt59NkDeZ8WWleSUL7/igw/thnc\nnKQzl0iDj72gwkjW2QtOKdqG\n-----END PRIVATE KEY-----\n",
                "client_email": "firebase-adminsdk-fbsvc@drawprobase.iam.gserviceaccount.com",
                "client_id": "111205400659926196582",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40drawprobase.iam.gserviceaccount.com",
                "universe_domain": "googleapis.com"
            }

            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            # ยืนยันการเชื่อมต่อจริงโดยลองดึงข้อมูล
            self.db.collection('participants').limit(1).get(timeout=10)
            self.is_db_connected = True
            self.log_event("เชื่อมต่อ Firestore สำเร็จ!", "SUCCESS")
        except Exception as e:
            self.log_event(f"Firestore เชื่อมต่อล้มเหลว: {str(e)}", "ERROR")
            self.is_db_connected = False

    def check_db_connection(self):
        """ Heartbeat ระบบตรวจสอบสถานะ Firestore """
        if not FIREBASE_AVAILABLE or not self.db:
            self.update_db_status_ui(False)
            return

        try:
            self.db.collection('participants').limit(1).get(timeout=5)
            if not self.is_db_connected:
                self.log_event("กลับมาเชื่อมต่อ Firestore ได้อีกครั้ง", "SUCCESS")
            self.update_db_status_ui(True)
        except Exception as e:
            if self.is_db_connected:
                self.log_event(f"ขาดการติดต่อกับ Firestore: {str(e)}", "ERROR")
            self.update_db_status_ui(False)

    def update_db_status_ui(self, connected):
        self.is_db_connected = connected
        if connected:
            self.lbl_db_status.setText(" FIRESTORE ONLINE")
            self.lbl_db_status.setStyleSheet("color: #28A745; background: rgba(40, 167, 69, 0.1); border-radius: 4px; padding: 4px; font-weight: bold;")
            self.lbl_db_icon.setPixmap(self.get_icon("cloud", "#28A745").pixmap(18, 18))
        else:
            self.lbl_db_status.setText(" FIRESTORE OFFLINE")
            self.lbl_db_status.setStyleSheet("color: #DC3545; background: rgba(220, 53, 69, 0.1); border-radius: 4px; padding: 4px; font-weight: bold;")
            self.lbl_db_icon.setPixmap(self.get_icon("cloud_off", "#DC3545").pixmap(18, 18))

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ---------------- Sidebar ----------------
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 40, 20, 20)
        self.sidebar_layout.setSpacing(10)

        self.logo_label = QLabel("PHOTO STUDIO")
        self.logo_label.setObjectName("logo")
        self.sidebar_layout.addWidget(self.logo_label)

        self.clock_label = QLabel("00:00:00")
        self.clock_label.setObjectName("clock")
        self.sidebar_layout.addWidget(self.clock_label)
        
        self.db_status_box = QFrame()
        self.db_status_box.setObjectName("db_status_box")
        self.db_status_layout = QHBoxLayout(self.db_status_box)
        self.db_status_layout.setContentsMargins(10, 5, 10, 5)
        self.lbl_db_icon = QLabel()
        self.lbl_db_status = QLabel(" INITIALIZING...")
        self.db_status_layout.addWidget(self.lbl_db_icon)
        self.db_status_layout.addWidget(self.lbl_db_status)
        self.db_status_layout.addStretch()
        self.sidebar_layout.addWidget(self.db_status_box)

        self.sidebar_layout.addSpacing(10)

        # Dashboard Card
        self.dash_card = QFrame()
        self.dash_card.setObjectName("dash_card")
        self.dash_layout = QVBoxLayout(self.dash_card)
        self.dash_layout.addWidget(QLabel("ความคืบหน้าภาพถ่าย", objectName="dash_label"))
        self.lbl_percent_val = QLabel("0%", objectName="percent_text")
        self.dash_layout.addWidget(self.lbl_percent_val)
        self.progress_bar = QProgressBar(objectName="dash_progress")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.dash_layout.addWidget(self.progress_bar)
        self.lbl_stats = QLabel("รอถ่าย: 0 | เสร็จแล้ว: 0", objectName="stat_small")
        self.dash_layout.addWidget(self.lbl_stats)
        self.sidebar_layout.addWidget(self.dash_card)

        # Workflow Steps
        self.workflow_frame = QFrame(objectName="workflow_frame")
        self.wf_layout = QVBoxLayout(self.workflow_frame)
        self.wf_layout.addWidget(QLabel("ขั้นตอนปัจจุบัน", objectName="wf_title"))
        self.step1 = QLabel("1. ตั้งค่าโฟลเดอร์")
        self.step2 = QLabel("2. เลือกรายชื่อผู้เข้าแข่ง")
        self.step3 = QLabel("3. โหมดถ่ายภาพสด")
        self.step4 = QLabel("4. ตรวจสอบและปิดงาน")
        self.steps = [self.step1, self.step2, self.step3, self.step4]
        for s in self.steps:
            s.setObjectName("wf_step")
            self.wf_layout.addWidget(s)
        self.sidebar_layout.addWidget(self.workflow_frame)

        # Navigation Buttons
        self.btn_page1 = QPushButton("  หน้าแรก: ตั้งค่า & รายชื่อ")
        self.btn_page1.setIcon(self.get_icon("users", "#FFFFFF"))
        self.btn_page1.setObjectName("nav_btn_active")
        
        self.btn_page2 = QPushButton("  โหมดถ่ายภาพ: Live View")
        self.btn_page2.setIcon(self.get_icon("image", "#212529"))
        self.btn_page2.setObjectName("nav_btn")
        
        self.btn_page3 = QPushButton("  บันทึกกิจกรรม (Audit Log)")
        self.btn_page3.setIcon(self.get_icon("list", "#212529"))
        self.btn_page3.setObjectName("nav_btn")
        
        for btn in [self.btn_page1, self.btn_page2, self.btn_page3]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()
        
        # ---------------- Content Area ----------------
        self.content_area = QWidget(objectName="content_area")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        
        self.stacked_widget = QStackedWidget()
        self.setup_page1()
        self.setup_page2()
        self.setup_page3()
        self.content_layout.addWidget(self.stacked_widget)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_area)

        self.btn_page1.clicked.connect(self.goto_page1)
        self.btn_page2.clicked.connect(self.goto_page2)
        self.btn_page3.clicked.connect(self.goto_page3)

    def setup_page1(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("การจัดการข้อมูลและโฟลเดอร์", objectName="page_title"))
        self.btn_import_csv = QPushButton(" นำเข้าข้อมูล (CSV)", objectName="primary_btn")
        self.btn_import_csv.setIcon(self.get_icon("download", "#FFFFFF"))
        self.btn_import_csv.clicked.connect(self.import_csv_to_firebase)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_import_csv)
        layout.addLayout(header_layout)

        folders_layout = QHBoxLayout()
        self.lbl_src = self.create_folder_card(folders_layout, "Source (C1)", "folder", self.select_folder, 'src')
        self.lbl_dest = self.create_folder_card(folders_layout, "Destination", "server", self.select_folder, 'dest')
        self.lbl_backup = self.create_folder_card(folders_layout, "Backup", "save", self.select_folder, 'backup')
        layout.addLayout(folders_layout)

        filter_layout = QHBoxLayout()
        self.type_combo = QComboBox(objectName="flat_input")
        self.type_combo.addItems(["แสดงทั้งหมด", "ประเภท ต.", "ประเภท ป."])
        self.type_combo.currentTextChanged.connect(self.filter_table)
        self.search_input = QLineEdit(objectName="flat_input")
        self.search_input.setPlaceholderText("🔍 ค้นหารหัส หรือ ชื่อผู้เข้าแข่งขัน...")
        self.search_input.textChanged.connect(self.filter_table)
        filter_layout.addWidget(QLabel("หมวดหมู่:"), 0, Qt.AlignmentFlag.AlignVCenter)
        filter_layout.addWidget(self.type_combo)
        filter_layout.addSpacing(15)
        filter_layout.addWidget(self.search_input, 1)
        layout.addLayout(filter_layout)

        self.table = QTableWidget(0, 4, objectName="flat_table")
        self.table.setHorizontalHeaderLabels(["รหัส (ID)", "ชื่อ-นามสกุล", "สถานศึกษา", "สถานะ"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.btn_create_folder = QPushButton(" ยืนยันรายชื่อและเข้าสู่โหมดถ่ายภาพ", objectName="success_btn")
        self.btn_create_folder.setIcon(self.get_icon("camera", "#FFFFFF"))
        self.btn_create_folder.setFixedHeight(55)
        self.btn_create_folder.clicked.connect(self.check_and_create_folders)
        layout.addWidget(self.btn_create_folder)
        self.stacked_widget.addWidget(page)

    def create_folder_card(self, parent_layout, title, icon_name, connect_func, arg):
        card = QFrame(objectName="folder_card")
        layout = QVBoxLayout(card)
        h_box = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(self.get_icon(icon_name, "#E04111").pixmap(22, 22))
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-weight: 800; color: #212529;")
        h_box.addWidget(icon_lbl)
        h_box.addWidget(t_lbl)
        h_box.addStretch()
        layout.addLayout(h_box)
        p_lbl = QLabel("ยังไม่ได้ตั้งค่า")
        p_lbl.setStyleSheet("color: #495057; font-size: 11px;")
        p_lbl.setWordWrap(True)
        layout.addWidget(p_lbl)
        btn = QPushButton("เลือก", objectName="outline_btn_small")
        btn.setFixedWidth(60)
        btn.clicked.connect(lambda: connect_func(arg))
        layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignRight)
        parent_layout.addWidget(card)
        return p_lbl

    def setup_page2(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.lbl_current_session = QLabel("LIVE SHOOTING: STANDBY", objectName="live_header")
        self.lbl_current_session.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_current_session)
        split_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        self.file_list = QListWidget(objectName="flat_list")
        left_layout.addWidget(QLabel("📸 ไฟล์รูปภาพที่เข้ามา:"))
        left_layout.addWidget(self.file_list)
        right_layout = QVBoxLayout()
        self.image_preview = QLabel("Waiting for camera input...", objectName="preview_box")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.image_preview)
        self.btn_finish_session = QPushButton(" ยืนยันผลงานและเสร็จสิ้นขั้นตอน (FINISH)", objectName="finish_btn")
        self.btn_finish_session.setIcon(self.get_icon("check_circle", "#FFFFFF"))
        self.btn_finish_session.setFixedHeight(60)
        self.btn_finish_session.clicked.connect(self.finish_session)
        right_layout.addWidget(self.btn_finish_session)
        split_layout.addLayout(left_layout, 1)
        split_layout.addLayout(right_layout, 2)
        layout.addLayout(split_layout)
        self.file_list.itemClicked.connect(self.preview_selected_image)
        self.stacked_widget.addWidget(page)

    def setup_page3(self):
        """ หน้า Audit Log """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("บันทึกกิจกรรมระบบ (Audit Log)", objectName="page_title"))
        self.audit_list = QListWidget(objectName="flat_list")
        layout.addWidget(self.audit_list)
        self.btn_clear_log = QPushButton(" ล้างบันทึกกิจกรรม", objectName="outline_btn_small")
        self.btn_clear_log.setFixedWidth(150)
        self.btn_clear_log.clicked.connect(lambda: self.audit_list.clear())
        layout.addWidget(self.btn_clear_log, 0, Qt.AlignmentFlag.AlignRight)
        self.stacked_widget.addWidget(page)

    # ==========================================
    # Logic & Workflow Functions
    # ==========================================
    def start_system_timers(self):
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(lambda: self.clock_label.setText(datetime.now().strftime("%H:%M:%S")))
        self.timer_clock.start(1000)

        self.timer_db = QTimer(self)
        self.timer_db.timeout.connect(self.check_db_connection)
        self.timer_db.start(30000) 

    def set_workflow_step(self, step_num):
        for i, step_label in enumerate(self.steps):
            if i + 1 < step_num:
                step_label.setStyleSheet("color: #28A745; font-weight: bold; text-decoration: line-through;")
            elif i + 1 == step_num:
                step_label.setStyleSheet("color: #FFFFFF; background-color: #E04111; border-radius: 4px; padding: 4px; font-weight: 800;")
            else:
                step_label.setStyleSheet("color: #ADB5BD; font-weight: normal;")

    def update_dashboard(self):
        total = len(self.participants_data)
        if total == 0: return
        finished = sum(1 for p in self.participants_data if "เสร็จสิ้น" in p.get("folder_status", ""))
        percent = int((finished / total) * 100)
        self.progress_bar.setValue(percent)
        self.lbl_percent_val.setText(f"{percent}%")
        self.lbl_stats.setText(f"รอถ่าย: {total - finished} | เสร็จแล้ว: {finished}")

    def finish_session(self):
        if not self.current_participant: return
        item_id = self.current_participant["id"]
        status_text = "✅ ถ่ายภาพเสร็จสิ้น"
        self.log_event(f"กำลังบันทึกสถานะเสร็จสิ้นของ {item_id}", "INFO")

        if self.db and self.is_db_connected:
            try:
                self.db.collection('participants').document(item_id).update({'folder_status': status_text})
                self.log_event(f"บันทึกลง Firestore สำเร็จ: {item_id}", "SUCCESS")
            except Exception as e:
                self.log_event(f"บันทึกล้มเหลว: {str(e)}", "ERROR")

        for item in self.participants_data:
            if item["id"] == item_id:
                item["folder_status"] = status_text
                break

        self.refresh_table()
        self.update_dashboard()
        QMessageBox.information(self, "Studio System", f"บันทึกงานของ {item_id} เรียบร้อยแล้ว!")
        self.current_participant = None
        self.goto_page1()

    def goto_page1(self):
        self.set_nav_active(self.btn_page1)
        self.stacked_widget.setCurrentIndex(0)
        self.set_workflow_step(1 if not self.table.selectedItems() else 2)

    def goto_page2(self):
        if not self.current_participant:
            QMessageBox.warning(self, "System", "กรุณาเลือกรายชื่อและเริ่มถ่ายภาพก่อน!")
            return
        self.set_nav_active(self.btn_page2)
        self.stacked_widget.setCurrentIndex(1)
        self.set_workflow_step(3)

    def goto_page3(self):
        self.set_nav_active(self.btn_page3)
        self.stacked_widget.setCurrentIndex(2)

    def set_nav_active(self, active_btn):
        for btn in [self.btn_page1, self.btn_page2, self.btn_page3]:
            btn.setObjectName("nav_btn")
            if btn == self.btn_page1: btn.setIcon(self.get_icon("users", "#212529"))
            if btn == self.btn_page2: btn.setIcon(self.get_icon("image", "#212529"))
            if btn == self.btn_page3: btn.setIcon(self.get_icon("list", "#212529"))
            
        active_btn.setObjectName("nav_btn_active")
        if active_btn == self.btn_page1: active_btn.setIcon(self.get_icon("users", "#FFFFFF"))
        if active_btn == self.btn_page2: active_btn.setIcon(self.get_icon("image", "#FFFFFF"))
        if active_btn == self.btn_page3: active_btn.setIcon(self.get_icon("list", "#FFFFFF"))
        self.sidebar.setStyleSheet(self.sidebar.styleSheet())

    def import_csv_to_firebase(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "เลือกไฟล์ CSV", "", "CSV Files (*.csv)")
        if not file_paths: return
        self.log_event(f"กำลังนำเข้าข้อมูลจาก CSV {len(file_paths)} ไฟล์", "INFO")
        try:
            for filepath in file_paths:
                with open(filepath, encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        item_id = row.get('ลำดับ', '').strip()
                        name = row.get('ชื่อผู้เข้าแข่งขัน', '').strip()
                        if item_id and name:
                            data = {'id': item_id, 'name': name, 'school': row.get('ชื่อสถานศึกษา', '').strip(), 'folder_status': 'รอการตรวจสอบ'}
                            if self.db and self.is_db_connected: 
                                self.db.collection('participants').document(item_id).set(data)
                            exists = False
                            for idx, existing in enumerate(self.participants_data):
                                if existing['id'] == item_id:
                                    self.participants_data[idx] = data
                                    exists = True; break
                            if not exists: self.participants_data.append(data)
            self.refresh_table()
            self.update_dashboard()
            self.log_event("นำเข้าข้อมูล CSV และส่งขึ้น Firestore เรียบร้อย", "SUCCESS")
            QMessageBox.information(self, "System", "นำเข้าข้อมูลสำเร็จ!")
        except Exception as e:
            self.log_event(f"นำเข้าล้มเหลว: {str(e)}", "ERROR")

    def fetch_firebase_data(self):
        if self.db and self.is_db_connected:
            self.log_event("กำลังดึงรายชื่อจาก Firestore...", "INFO")
            try:
                docs = self.db.collection('participants').stream()
                self.participants_data = [doc.to_dict() for doc in docs]
                self.participants_data.sort(key=lambda x: x.get('id', ''))
                self.refresh_table()
                self.update_dashboard()
                self.log_event(f"ดึงข้อมูลสำเร็จ: {len(self.participants_data)} รายชื่อ", "SUCCESS")
            except Exception as e:
                self.log_event(f"ดึงข้อมูลล้มเหลว: {str(e)}", "ERROR")

    def refresh_table(self):
        self.table.setRowCount(0)
        for data in self.participants_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(data.get("id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(data.get("school", "")))
            status = data.get("folder_status", "รอการตรวจสอบ")
            item = QTableWidgetItem(status)
            if "เสร็จสิ้น" in status:
                item.setIcon(self.get_icon("check_circle", "#28A745"))
                item.setForeground(QColor("#28A745"))
            elif "กำลังถ่าย" in status:
                item.setIcon(self.get_icon("camera", "#17A2B8"))
                item.setForeground(QColor("#17A2B8"))
            self.table.setItem(row, 3, item)

    def filter_table(self):
        filter_type = self.type_combo.currentText()
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            item_id = self.table.item(row, 0).text().lower()
            name = self.table.item(row, 1).text().lower()
            type_match = True
            if filter_type == "ประเภท ต." and not item_id.startswith("ต"): type_match = False
            elif filter_type == "ประเภท ป." and not item_id.startswith("ป"): type_match = False
            search_match = search_text in item_id or search_text in name
            self.table.setRowHidden(row, not (type_match and search_match))

    def select_folder(self, folder_type):
        path = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์")
        if path:
            if folder_type == 'src': 
                self.src_folder = path; self.lbl_src.setText(path); 
                self.log_event(f"ต้นทาง: {path}", "INFO")
                self.start_folder_watcher()
            elif folder_type == 'dest': 
                self.dest_folder = path; self.lbl_dest.setText(path)
                self.log_event(f"ปลายทาง: {path}", "INFO")
            elif folder_type == 'backup': 
                self.backup_folder = path; self.lbl_backup.setText(path)
                self.log_event(f"สำรอง: {path}", "INFO")
            self.save_config()

    def check_and_create_folders(self):
        if not self.dest_folder or not self.src_folder:
            QMessageBox.warning(self, "Check", "ตั้งค่าโฟลเดอร์ไม่ครบ!"); return
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Check", "เลือกรายชื่อในตารางก่อน!"); return

        row = selected[0].row()
        item_id = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '.')]).strip()
        folder_name = f"{item_id}-{safe_name}"
        full_path = os.path.join(self.dest_folder, folder_name)

        if not os.path.exists(full_path): 
            os.makedirs(full_path)
            self.log_event(f"สร้างโฟลเดอร์: {folder_name}", "INFO")
        
        status = "กำลังถ่ายภาพ"
        if self.db and self.is_db_connected: 
            try:
                self.db.collection('participants').document(item_id).update({'folder_status': status})
            except Exception: pass
        
        self.current_participant = {"id": item_id, "name": name, "safe_name": safe_name, "folder_path": full_path}
        self.lbl_current_session.setText(f"LIVE SHOOTING: {item_id} - {name}")
        self.file_list.clear()
        
        if os.path.exists(full_path):
            for f in os.listdir(full_path):
                if os.path.isfile(os.path.join(full_path, f)):
                    self.file_list.addItem(f)
                    self.file_list.item(self.file_list.count()-1).setData(Qt.ItemDataRole.UserRole, os.path.join(full_path, f))

        self.goto_page2()

    def start_folder_watcher(self):
        if self.watcher_thread: self.watcher_thread.stop()
        if self.src_folder:
            self.log_event(f"เริ่มเฝ้าดูโฟลเดอร์: {self.src_folder}", "INFO")
            self.watcher_thread = FolderWatcherThread(self.src_folder)
            self.watcher_thread.new_photo_signal.connect(self.process_new_photo)
            self.watcher_thread.start()

    def process_new_photo(self, file_path):
        if not self.current_participant: return
        target_dir = self.current_participant["folder_path"]
        img_number = len(os.listdir(target_dir)) + 1
        ext = os.path.splitext(file_path)[1]
        new_filename = f"{self.current_participant['id']}-{self.current_participant['safe_name']}_{img_number}{ext}"
        new_dest_path = os.path.join(target_dir, new_filename)

        try:
            shutil.move(file_path, new_dest_path)
            self.log_event(f"ย้ายภาพ: {new_filename}", "SUCCESS")
            if self.backup_folder: shutil.copy2(new_dest_path, os.path.join(self.backup_folder, new_filename))
            self.file_list.insertItem(0, new_filename)
            self.file_list.item(0).setData(Qt.ItemDataRole.UserRole, new_dest_path)
            self.show_image_preview(new_dest_path)
        except Exception as e: 
            self.log_event(f"ย้ายภาพล้มเหลว: {str(e)}", "ERROR")

    def preview_selected_image(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path: self.show_image_preview(path)

    def show_image_preview(self, path):
        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(self.image_preview.width(), self.image_preview.height(), 
                               Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_preview.setPixmap(pixmap)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.src_folder = config.get("src_folder", "")
                    if self.src_folder: self.lbl_src.setText(self.src_folder); self.start_folder_watcher()
                    self.dest_folder = config.get("dest_folder", "")
                    if self.dest_folder: self.lbl_dest.setText(self.dest_folder)
                    self.backup_folder = config.get("backup_folder", "")
                    if self.backup_folder: self.lbl_backup.setText(self.backup_folder)
            except Exception: pass

    def save_config(self):
        config = {"src_folder": self.src_folder, "dest_folder": self.dest_folder, "backup_folder": self.backup_folder}
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception: pass

    def apply_flat_design_style(self):
        self.setStyleSheet("""
        QMainWindow, #content_area { background-color: #FDFDFD; }
        #sidebar { background-color: #FFFFFF; border-right: 2px solid #E9ECEF; }
        #logo { font-size: 22px; font-weight: 900; color: #E04111; letter-spacing: 1px; margin-bottom: 5px; }
        #clock { font-size: 32px; font-weight: 800; color: #212529; }
        #db_status_text { font-size: 11px; letter-spacing: 0.5px; }
        
        #dash_card { background-color: #212529; border-radius: 12px; padding: 15px; }
        #dash_label { color: #ADB5BD; font-size: 12px; font-weight: bold; }
        #percent_text { color: #FFFFFF; font-size: 38px; font-weight: 900; margin: 5px 0; }
        #dash_progress { height: 8px; border-radius: 4px; background: #495057; border: none; }
        #dash_progress::chunk { background-color: #E04111; border-radius: 4px; }
        #stat_small { color: #6C757D; font-size: 11px; margin-top: 5px; }

        #workflow_frame { background-color: #F8F9FA; border-radius: 8px; border: 1px solid #DEE2E6; padding: 5px; }
        #wf_title { font-weight: 800; color: #212529; margin-bottom: 5px; font-size: 13px; }
        #wf_step { font-size: 13px; color: #495057; padding: 2px; }

        #nav_btn { background: transparent; color: #212529; text-align: left; padding: 14px; font-size: 14px; font-weight: 600; border: none; border-radius: 8px; }
        #nav_btn:hover { background: #F1F3F5; }
        #nav_btn_active { background: #E04111; color: #FFFFFF; text-align: left; padding: 14px; font-size: 14px; font-weight: 700; border-radius: 8px; }

        #page_title { font-size: 26px; font-weight: 900; color: #212529; }
        #folder_card { background: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 10px; padding: 12px; min-width: 200px; }
        #outline_btn_small { background: white; color: #E04111; border: 1.5px solid #E04111; border-radius: 5px; font-weight: bold; font-size: 11px; padding: 4px; }
        #outline_btn_small:hover { background: #FFF5F2; }

        #flat_input { background: #FFFFFF; border: 2px solid #E9ECEF; border-radius: 8px; padding: 12px; color: #212529; font-weight: 600; }
        #flat_input:focus { border: 2px solid #E04111; }
        #flat_table { background: white; border: 1px solid #DEE2E6; color: #212529; font-weight: 500; }
        QHeaderView::section { background: #F8F9FA; color: #212529; padding: 15px; font-weight: 800; border: none; border-bottom: 2px solid #E04111; }

        #primary_btn { background: #212529; color: #FFFFFF; font-weight: bold; padding: 12px 20px; border-radius: 8px; border: none; }
        #success_btn { background: #E04111; color: #FFFFFF; font-size: 18px; font-weight: 800; border-radius: 10px; }
        #finish_btn { background: #28A745; color: #FFFFFF; font-size: 18px; font-weight: 800; border-radius: 10px; }

        #live_header { font-size: 20px; font-weight: 900; color: #FFFFFF; background: #212529; padding: 20px; border-radius: 10px; }
        #preview_box { background: #F1F3F5; border: 2px dashed #CED4DA; border-radius: 12px; color: #ADB5BD; font-size: 18px; font-weight: bold; }
        #flat_list { background: white; border: 1px solid #DEE2E6; border-radius: 10px; color: #212529; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Sarabun", 10) 
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())