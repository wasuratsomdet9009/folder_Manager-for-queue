import sys
import os
import subprocess
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QFileDialog, QListWidget, QMessageBox, QFrame, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap

class ImageViewer(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"ดูรูปภาพ - {os.path.basename(image_path)}")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #2d3436;") # พื้นหลังสีเข้มสำหรับดูรูป
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel()
        pixmap = QPixmap(image_path)
        # ปรับขนาดรูปให้พอดีกรอบอย่างสวยงาม
        label.setPixmap(pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

class FileDropListWidget(QListWidget):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.setAcceptDrops(True)
        # ตั้งค่าให้รับการวางไฟล์จากภายนอกอย่างเดียว ป้องกันการบั๊กขัดแย้งกับระบบของ QListWidget เอง
        self.setDragDropMode(self.DragDropMode.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            # เปลี่ยนสไตล์เฉพาะกรอบลิสต์ (ไม่รีเฟรชทั้งแอปพลิเคชันเพื่อลดอาการค้าง)
            self.setStyleSheet("border: 2px dashed #0984e3; background-color: #e8f4f8;")
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        # จำเป็นต้องมีใน macOS เพื่อบอกหน้าต่างว่าตำแหน่งที่เมาส์ลากผ่านนั้น "วางได้"
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("") # รีเซ็ตสไตล์กลับเป็นปกติ
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.setStyleSheet("") # รีเซ็ตสไตล์กลับเป็นปกติ
        if not self.parent_app.current_directory:
            self.parent_app.set_status("กรุณาเลือกพื้นที่ทำงานก่อนลากไฟล์ลงมา", is_error=True)
            QMessageBox.warning(self.parent_app, "ข้อผิดพลาด", "กรุณากดปุ่ม 'เลือกพื้นที่ทำงาน' ก่อนลากไฟล์ลงมาครับ")
            return

        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            copied_files = 0
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                
                # ตรวจสอบว่ามี path จริงในระบบ
                if not file_path or not os.path.exists(file_path):
                    continue
                    
                target_path = os.path.join(self.parent_app.current_directory, os.path.basename(file_path))
                
                # ป้องกันข้อผิดพลาดกรณีลากไฟล์จากโฟลเดอร์เดียวกันมาวางซ้ำตัวเอง
                if os.path.abspath(file_path) == os.path.abspath(target_path):
                    continue
                    
                # จัดการกรณีชื่อซ้ำ (Auto Rename) จะใส่เลขต่อท้ายให้
                base, ext = os.path.splitext(target_path)
                counter = 1
                while os.path.exists(target_path):
                    target_path = f"{base}_{counter}{ext}"
                    counter += 1
                    
                try:
                    # ตรวจสอบและรองรับทั้ง "ไฟล์" และ "โฟลเดอร์"
                    if os.path.isfile(file_path):
                        shutil.copy2(file_path, target_path) 
                    elif os.path.isdir(file_path):
                        shutil.copytree(file_path, target_path)
                    
                    copied_files += 1
                    
                    # ป้องกันหน้าต่างโปรแกรมค้าง (Not Responding) ขณะก็อปปี้ไฟล์
                    QApplication.processEvents()
                    
                except Exception as e:
                    self.parent_app.set_status(f"ผิดพลาดการนำเข้าไฟล์: {str(e)}", is_error=True)
        
            if copied_files > 0:
                self.parent_app.set_status(f"✅ นำเข้า {copied_files} รายการสำเร็จ!", is_success=True)
                self.parent_app.refresh_folder_list()
        else:
            super().dropEvent(event)

class FolderManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ระบบจัดการโฟลเดอร์ (Folder Manager) - Beta Test V0.3")
        self.resize(850, 600) # ขยายขนาดหน้าต่างเพื่อให้มีพื้นที่พรีวิว
        self.current_directory = ""

        # กำหนดฟอนต์หลัก (อ้างอิงจากระบบปฏิบัติการเพื่อแก้ปัญหา Font Missing บน Mac)
        self.main_font = self.font()
        self.main_font.setPointSize(10)
        self.setFont(self.main_font)

        self.init_ui()
        self.apply_stylesheet()

    def init_ui(self):
        # วิดเจ็ตหลัก
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 1. ส่วนเลือกไดเรกทอรี (Browse)
        path_layout = QHBoxLayout()
        self.lbl_path = QLabel("ยังไม่ได้เลือกโฟลเดอร์หลัก")
        self.lbl_path.setWordWrap(True)
        self.lbl_path.setStyleSheet("color: #7f8c8d; font-style: italic;")
        
        self.btn_up = QPushButton("⬆️ ย้อนกลับ")
        self.btn_up.setObjectName("btn_up")
        self.btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_up.clicked.connect(self.go_up_directory)
        self.btn_up.setEnabled(False)
        
        btn_browse = QPushButton("📁 เลือกพื้นที่ทำงาน")
        btn_browse.setObjectName("btn_browse")
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self.browse_directory)
        
        path_layout.addWidget(self.btn_up)
        path_layout.addWidget(self.lbl_path, stretch=1)
        path_layout.addWidget(btn_browse)
        main_layout.addLayout(path_layout)

        # เส้นแบ่ง
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("color: #bdc3c7;")
        main_layout.addWidget(line1)

        # 2. ส่วนสร้างโฟลเดอร์ใหม่
        create_layout = QHBoxLayout()
        self.txt_new_folder = QLineEdit()
        self.txt_new_folder.setPlaceholderText("พิมพ์ชื่อโฟลเดอร์ที่ต้องการสร้าง...")
        self.txt_new_folder.setFixedHeight(40)
        self.txt_new_folder.returnPressed.connect(self.create_folder) # กด Enter เพื่อสร้าง
        
        btn_create = QPushButton("➕ สร้างโฟลเดอร์")
        btn_create.setObjectName("btn_create")
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.setFixedHeight(40)
        btn_create.clicked.connect(self.create_folder)
        
        create_layout.addWidget(self.txt_new_folder, stretch=1)
        create_layout.addWidget(btn_create)
        main_layout.addLayout(create_layout)

        # 3. ส่วนแสดงรายการโฟลเดอร์, ไฟล์ และพรีวิว
        list_label_layout = QHBoxLayout()
        lbl_list = QLabel("โฟลเดอร์และไฟล์ที่มีอยู่ในระบบ (ลากไฟล์มาวางที่นี่ได้):")
        lbl_list.setStyleSheet("font-weight: bold; color: #2d3436; font-size: 14px;")
        list_label_layout.addWidget(lbl_list)
        main_layout.addLayout(list_label_layout)

        content_layout = QHBoxLayout()

        # ด้านซ้าย: ลิสต์รายการ
        self.folder_list = FileDropListWidget(self)
        self.folder_list.itemSelectionChanged.connect(self.check_selection)
        self.folder_list.itemDoubleClicked.connect(self.handle_item_double_click)
        content_layout.addWidget(self.folder_list, stretch=2)

        # ด้านขวา: พาเนลพรีวิว (Preview Panel)
        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("preview_panel")
        preview_layout = QVBoxLayout(self.preview_panel)
        
        lbl_preview_title = QLabel("พรีวิว / รายละเอียด")
        lbl_preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_preview_title.setStyleSheet("font-weight: bold; color: #636e72; border: none; font-size: 12px;")
        
        self.lbl_preview_img = QLabel("🖼️\nไม่มีรูปภาพ")
        self.lbl_preview_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview_img.setStyleSheet("color: #b2bec3; border: none; font-size: 14px;")
        self.lbl_preview_img.setMinimumSize(250, 250)
        
        self.lbl_preview_details = QLabel("-")
        self.lbl_preview_details.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.lbl_preview_details.setWordWrap(True)
        self.lbl_preview_details.setStyleSheet("color: #2d3436; border: none; font-size: 13px; margin-top: 10px;")
        
        preview_layout.addWidget(lbl_preview_title)
        preview_layout.addWidget(self.lbl_preview_img, stretch=1)
        preview_layout.addWidget(self.lbl_preview_details, stretch=1)
        
        content_layout.addWidget(self.preview_panel, stretch=1)
        main_layout.addLayout(content_layout)

        # 4. ปุ่มจัดการโฟลเดอร์ (แสดงเมื่อเลือกรายการ)
        action_layout = QHBoxLayout()
        
        self.btn_enter = QPushButton("➡️ เข้าไป / 👁️ ดูรูป")
        self.btn_enter.setObjectName("btn_enter")
        self.btn_enter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enter.clicked.connect(self.action_selected_item)
        self.btn_enter.setEnabled(False)
        
        self.btn_open = QPushButton("📂 เปิดดูใน OS")
        self.btn_open.setObjectName("btn_action")
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_selected_folder)
        self.btn_open.setEnabled(False) # ปิดไว้จนกว่าจะเลือก
        
        self.btn_delete = QPushButton("🗑️ ลบโฟลเดอร์")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_selected_folder)
        self.btn_delete.setEnabled(False) # ปิดไว้จนกว่าจะเลือก

        action_layout.addStretch()
        action_layout.addWidget(self.btn_enter)
        action_layout.addWidget(self.btn_open)
        action_layout.addWidget(self.btn_delete)
        main_layout.addLayout(action_layout)

        # 5. Status Bar จำลอง
        self.lbl_status = QLabel("พร้อมใช้งาน")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setObjectName("lbl_status")
        main_layout.addWidget(self.lbl_status)

    def apply_stylesheet(self):
        # การตกแต่งสไตล์แบบ Flat Design (Minimal & Clean)
        qss = """
        QMainWindow {
            background-color: #f0f2f5;
        }
        QLabel {
            color: #2d3436;
        }
        QLineEdit {
            border: 2px solid #dfe6e9;
            border-radius: 6px;
            padding: 5px 10px;
            background-color: white;
            font-size: 14px;
            color: #2d3436;
        }
        QLineEdit:focus {
            border: 2px solid #0984e3;
        }
        QPushButton {
            border-radius: 6px;
            padding: 8px 15px;
            font-weight: bold;
            font-size: 14px;
            border: none;
        }
        QPushButton#btn_up {
            background-color: #b2bec3;
            color: white;
        }
        QPushButton#btn_up:hover { background-color: #636e72; }
        QPushButton#btn_up:disabled { background-color: #dfe6e9; color: #b2bec3; }

        QPushButton#btn_browse {
            background-color: #2d3436;
            color: white;
        }
        QPushButton#btn_browse:hover { background-color: #636e72; }
        
        QPushButton#btn_create {
            background-color: #00b894;
            color: white;
        }
        QPushButton#btn_create:hover { background-color: #00cec9; }
        
        QPushButton#btn_enter {
            background-color: #fdcb6e;
            color: #2d3436;
        }
        QPushButton#btn_enter:hover { background-color: #ffeaa7; }
        QPushButton#btn_enter:disabled { background-color: #dfe6e9; color: #b2bec3; }
        
        QPushButton#btn_action {
            background-color: #0984e3;
            color: white;
        }
        QPushButton#btn_action:hover { background-color: #74b9ff; }
        QPushButton#btn_action:disabled { background-color: #dfe6e9; color: #b2bec3; }
        
        QPushButton#btn_delete {
            background-color: #d63031;
            color: white;
        }
        QPushButton#btn_delete:hover { background-color: #ff7675; }
        QPushButton#btn_delete:disabled { background-color: #dfe6e9; color: #b2bec3; }
        
        QListWidget {
            border: 1px solid #dfe6e9;
            border-radius: 6px;
            background-color: white;
            padding: 5px;
            font-size: 14px;
            color: #2d3436;
            outline: none;
        }
        QListWidget::item {
            padding: 10px;
            border-bottom: 1px solid #f1f2f6;
        }
        QListWidget::item:selected {
            background-color: #74b9ff;
            color: white;
            border-radius: 4px;
        }
        QListWidget::item:hover {
            background-color: #f1f2f6;
            color: #2d3436;
        }
        QFrame#preview_panel {
            background-color: white;
            border: 1px solid #dfe6e9;
            border-radius: 6px;
        }
        QLabel#lbl_status {
            color: #636e72;
            font-size: 12px;
            padding: 5px;
            border-radius: 4px;
        }
        """
        self.setStyleSheet(qss)

    def set_status(self, message, is_error=False, is_success=False):
        if is_error:
            self.lbl_status.setStyleSheet("color: #e74c3c; background-color: #fadbd8; font-weight: bold;")
        elif is_success:
            self.lbl_status.setStyleSheet("color: #27ae60; background-color: #d5f5e3; font-weight: bold;")
        else:
            self.lbl_status.setStyleSheet("color: #7f8c8d; background-color: transparent;")
        self.lbl_status.setText(message)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์หลัก")
        if directory:
            self.current_directory = directory
            self.update_path_label()
            self.refresh_folder_list()
            self.set_status("โหลดไดเรกทอรีสำเร็จ", is_success=True)

    def update_path_label(self):
        self.lbl_path.setText(f"พื้นที่ทำงาน: {self.current_directory}")
        self.lbl_path.setStyleSheet("color: #0984e3; font-weight: bold;")
        self.btn_up.setEnabled(True)

    def go_up_directory(self):
        if self.current_directory:
            parent_dir = os.path.dirname(self.current_directory)
            if parent_dir and parent_dir != self.current_directory:
                self.current_directory = parent_dir
                self.update_path_label()
                self.refresh_folder_list()
                self.set_status("ย้อนกลับไปยังโฟลเดอร์ก่อนหน้าแล้ว", is_success=True)

    def refresh_folder_list(self):
        self.folder_list.clear()
        if not self.current_directory:
            return
            
        try:
            # ดึงรายชื่อทั้งหมด (ทั้งไฟล์และโฟลเดอร์)
            items = os.listdir(self.current_directory)
            folders = []
            files = []
            
            for f in items:
                full_path = os.path.join(self.current_directory, f)
                if os.path.isdir(full_path):
                    folders.append(f)
                else:
                    files.append(f)
                    
            folders.sort()
            files.sort()
            
            for folder in folders:
                self.folder_list.addItem(f"📁 {folder}")
                
            for file in files:
                ext = file.lower().split('.')[-1]
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
                    self.folder_list.addItem(f"🖼️ {file}")
                else:
                    self.folder_list.addItem(f"📄 {file}")

        except Exception as e:
            self.set_status(f"ไม่สามารถอ่านข้อมูลได้: {str(e)}", is_error=True)

    def create_folder(self):
        if not self.current_directory:
            self.set_status("กรุณาเลือกพื้นที่ทำงาน (Browse) ก่อน!", is_error=True)
            return

        folder_name = self.txt_new_folder.text().strip()
        
        if not folder_name:
            self.set_status("กรุณาพิมพ์ชื่อโฟลเดอร์", is_error=True)
            return
            
        # ตรวจสอบอักขระที่ไม่ได้รับอนุญาต (เบื้องต้น)
        invalid_chars = '<>:"/\\|?*'
        if any(char in folder_name for char in invalid_chars):
            self.set_status('ชื่อโฟลเดอร์ห้ามมีตัวอักษร < > : " / \\ | ? *', is_error=True)
            return

        target_path = os.path.join(self.current_directory, folder_name)

        # การตรวจสอบโฟลเดอร์ซ้ำ
        if os.path.exists(target_path):
            self.set_status(f"❌ ล้มเหลว: มีโฟลเดอร์ชื่อ '{folder_name}' อยู่แล้ว!", is_error=True)
            # แจ้งเตือนแบบ Popup สำหรับข้อผิดพลาดสำคัญ
            QMessageBox.warning(self, "ชื่อซ้ำ", f"ไม่สามารถสร้างได้\nโฟลเดอร์ชื่อ '{folder_name}' มีอยู่แล้วในระบบ")
        else:
            try:
                os.makedirs(target_path)
                self.set_status(f"✅ สร้างโฟลเดอร์ '{folder_name}' สำเร็จ!", is_success=True)
                self.txt_new_folder.clear()
                self.refresh_folder_list()
            except Exception as e:
                self.set_status(f"เกิดข้อผิดพลาด: {str(e)}", is_error=True)

    def check_selection(self):
        # เปิด/ปิด ปุ่มจัดการเมื่อมีการเลือกรายการในลิสต์
        has_selection = len(self.folder_list.selectedItems()) > 0
        self.btn_enter.setEnabled(has_selection)
        self.btn_open.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

        if has_selection:
            item_text = self.folder_list.selectedItems()[0].text()
            if item_text.startswith("📁"):
                self.btn_enter.setText("➡️ เข้าไปในโฟลเดอร์")
            elif item_text.startswith("🖼️"):
                self.btn_enter.setText("👁️ เปิดดูรูปเต็ม")
            else:
                self.btn_enter.setText("📄 เปิดไฟล์")

            # --- อัปเดตส่วนพรีวิวและรายละเอียด ---
            path = self.get_selected_item_path()
            if path and os.path.exists(path):
                if os.path.isfile(path):
                    size_kb = os.path.getsize(path) / 1024
                    ext = path.lower().split('.')[-1]
                    
                    if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
                        # แสดงพรีวิวรูปภาพ
                        pixmap = QPixmap(path)
                        scaled_pixmap = pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.lbl_preview_img.setPixmap(scaled_pixmap)
                        
                        width = pixmap.width()
                        height = pixmap.height()
                        self.lbl_preview_details.setText(f"<b>ชื่อ:</b> {os.path.basename(path)}<br><br><b>ขนาดไฟล์:</b> {size_kb:.2f} KB<br><b>ความละเอียด:</b> {width} x {height} px")
                    else:
                        # กรณีเป็นไฟล์อื่นๆ (ไม่ใช่รูป)
                        self.lbl_preview_img.clear()
                        self.lbl_preview_img.setText("📄\nไอคอนไฟล์")
                        self.lbl_preview_details.setText(f"<b>ชื่อ:</b> {os.path.basename(path)}<br><br><b>ขนาดไฟล์:</b> {size_kb:.2f} KB<br><b>ประเภท:</b> {ext.upper()}")
                elif os.path.isdir(path):
                    # กรณีเป็นโฟลเดอร์
                    self.lbl_preview_img.clear()
                    self.lbl_preview_img.setText("📁\nไอคอนโฟลเดอร์")
                    try:
                        items_count = len(os.listdir(path))
                    except:
                        items_count = "?"
                    self.lbl_preview_details.setText(f"<b>ชื่อ:</b> {os.path.basename(path)}<br><br><b>จำนวนรายการข้างใน:</b> {items_count} รายการ")
        else:
            # ไม่มีอะไรถูกเลือก
            self.lbl_preview_img.clear()
            self.lbl_preview_img.setText("🖼️\nไม่มีรูปภาพ")
            self.lbl_preview_details.setText("-")

    def get_selected_item_path(self):
        selected_items = self.folder_list.selectedItems()
        if not selected_items:
            return None
        item_text = selected_items[0].text()
        
        # ตัด Emoji ด้านหน้าออก (Emoji + เว้นวรรค)
        if item_text.startswith("📁 ") or item_text.startswith("🖼️ ") or item_text.startswith("📄 "):
            file_name = item_text[2:].strip()
        else:
            file_name = item_text.strip()
            
        return os.path.join(self.current_directory, file_name)

    def action_selected_item(self):
        # ปุ่มถูกกด ให้จำลองเหมือนการดับเบิลคลิก
        self.handle_item_double_click(None)

    def handle_item_double_click(self, item):
        path = self.get_selected_item_path()
        if not path:
            return

        if os.path.isdir(path):
            self.current_directory = path
            self.update_path_label()
            self.refresh_folder_list()
            self.set_status(f"เข้าไปยังโฟลเดอร์ '{os.path.basename(path)}' แล้ว", is_success=True)
        elif os.path.isfile(path):
            ext = path.lower().split('.')[-1]
            if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
                self.viewer = ImageViewer(path, self)
                self.viewer.exec()
            else:
                self.open_selected_folder()

    def open_selected_folder(self):
        path = self.get_selected_item_path()
        if path:
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin": # macOS
                    subprocess.Popen(["open", path])
                else: # Linux
                    subprocess.Popen(["xdg-open", path])
                self.set_status("กำลังเปิด...")
            except Exception as e:
                self.set_status(f"ไม่สามารถเปิดได้: {str(e)}", is_error=True)

    def delete_selected_folder(self):
        path = self.get_selected_item_path()
        if not path:
            return
            
        item_name = os.path.basename(path)
        is_dir = os.path.isdir(path)
        item_type = "โฟลเดอร์" if is_dir else "ไฟล์"
        
        # ยืนยันก่อนลบ
        reply = QMessageBox.question(self, 'ยืนยันการลบ',
                                     f"คุณแน่ใจหรือไม่ว่าต้องการลบ{item_type}:\n'{item_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if is_dir:
                    os.rmdir(path)
                else:
                    os.remove(path)
                self.set_status(f"🗑️ ลบ{item_type} '{item_name}' แล้ว", is_success=True)
                self.refresh_folder_list()
            except OSError:
                self.set_status("❌ ลบไม่ได้: โฟลเดอร์ต้องว่างเปล่าจึงจะลบได้", is_error=True)
                QMessageBox.warning(self, "ข้อผิดพลาด", "สามารถลบได้เฉพาะโฟลเดอร์ที่ไม่มีไฟล์หรือโฟลเดอร์ย่อยอยู่ข้างในเท่านั้น")
            except Exception as e:
                self.set_status(f"เกิดข้อผิดพลาด: {str(e)}", is_error=True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FolderManagerApp()
    window.show()
    sys.exit(app.exec())