# 더블클릭, delete, 단축키
# 아이콘 변경
# 다중선택
# DDNS지원

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import json
import re

class WOLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.json_file = "PCList.json"

        self.title("Wake on LAN")
        self.geometry("600x600")
        self.build_layout()

        # pc_list와 json에 저장할 항목들
        self.json_keys = ["name", "ip", "mac", "port"]
        self.field_labels = {
            "name": "PC Name",
            "ip": "IP Address", 
            "mac": "MAC Address",
            "port": "Port Number"
        }
        # pc_table에 표시할 칼럼 (json_keys의 부분집합)
        self.table_columns = ["name", "ip", "mac", "port"]
        self.table_widths = {
            "name": 150,
            "ip": 150,
            "mac": 180,
            "port": 80
        }
        # 유효성 검증 (부분집합인지 확인)
        self._validate_table_columns()

        self.pc_list = []
        self.load_pc_list()
        self.build_pc_table()
    
    def build_layout(self):
        # 툴바 프레임 생성
        self.toolbar_frame = tk.Frame(self, bg='lightgray', height=40)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        self.toolbar_frame.pack_propagate(False)
        # new
        self.button_new = tk.Button(self.toolbar_frame, text="New", width=8, command=self.new_pc)
        self.button_new.pack(side=tk.LEFT, padx=4)
        # edit
        self.button_edit = tk.Button(self.toolbar_frame, text="Edit", width=8, state=tk.DISABLED, command=self.edit_pc)
        self.button_edit.pack(side=tk.LEFT, padx=2)
        # delete
        self.button_delete = tk.Button(self.toolbar_frame, text="Delete", width=8, state=tk.DISABLED, command=self.delete_pc)
        self.button_delete.pack(side=tk.LEFT, padx=2)
        # 구분선
        separator = tk.Frame(self.toolbar_frame, width=2, bg='gray')
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        # wol
        self.button_wol = tk.Button(self.toolbar_frame, text="Wake Up", width=10, state=tk.DISABLED, command=self.wol)
        self.button_wol.pack(side=tk.LEFT, padx=2)
        # refresh
        self.button_refresh = tk.Button(self.toolbar_frame, text="Refresh", width=8, command=self.refresh_pc_table)
        self.button_refresh.pack(side=tk.RIGHT, padx=4)
    
    def load_pc_list(self):
        if not os.path.exists(self.json_file):
            self.pc_list = []
            return
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.pc_list = data.get("pc_list", [])
        except json.JSONDecodeError as e:
            result = messagebox.askyesno(
                "JSON File Error",
                "The JSON file format is invalid.\nFile may be corrupted or damaged.\n\nDo you want to reset the file?",
                icon='error'
            )
            if result:
                self.pc_list = []
                self.save_pc_list()
            else:
                self.destroy()
                exit(1)

    def save_pc_list(self):
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump({"pc_list": self.pc_list}, f, indent=2, ensure_ascii=False)

    def build_pc_table(self):
        # Treeview 생성
        self.tree = ttk.Treeview(self, columns=self.table_columns, show='headings', height=20)
        
        # 컬럼 헤더, 너비 설정
        for column in self.table_columns:
            self.tree.heading(column, text=self.field_labels[column])
            self.tree.column(column, width=self.table_widths[column])
        
        # 스크롤바 생성
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # 테이블과 스크롤바 배치
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0), pady=(0, 10), expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))

        # 창 크기 조절
        tree_width = sum(self.table_widths.values()) + 10
        self.geometry(f"{tree_width + 30}x600")
        self.minsize(f"{tree_width + 30}", 300)

        # PC 목록 로드
        self.refresh_pc_table()

        # 선택 이벤트 바인딩
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)  # 선택 변경 시 발생
        self.tree.bind('<Button-1>', self.on_tree_click)

    def refresh_pc_table(self):
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # PC 목록 데이터 추가
        for pc in self.pc_list:
            values = [pc.get(column, "") for column in self.table_columns]
            self.tree.insert('', 'end', values=values)
    
    def new_pc(self):
        new_window = NewPCWindow(self)
    
    def edit_pc(self):
        new_window = EditPCWindow(self)

    def delete_pc(self):
        selected_pc = self.tree.selection()
        pc_index = self.tree.index(selected_pc[0])

        # 삭제 확인 다이얼로그
        pc_name = self.pc_list[pc_index]['name']
        result = messagebox.askyesno(
            "Delete Confirmation",
            f"Are you sure you want to delete '{pc_name}'?\n\nThis action cannot be undone.",
            icon='warning'
        )

        if result:
            del self.pc_list[pc_index]
            self.save_pc_list()
            self.refresh_pc_table()

    def wol(self):
        selected_pc = self.tree.selection()

        # 선택된 PC 정보 가져오기
        pc_index = self.tree.index(selected_pc[0])
        pc_info = self.pc_list[pc_index]
        pc_name = pc_info.get('name', 'Unknown PC')

        # Wake up 확인 다이얼로그
        result = messagebox.askyesno(
            "Wake on LAN",
            f"Do you want to wake up '{pc_name}'?",
            icon='question'
        )

        if result:
            pass

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        
        if selected_items:
            self.button_edit.config(state=tk.NORMAL)
            self.button_delete.config(state=tk.NORMAL)
            self.button_wol.config(state=tk.NORMAL)
        else:
            self.button_edit.config(state=tk.DISABLED)
            self.button_delete.config(state=tk.DISABLED)
            self.button_wol.config(state=tk.DISABLED)

    def on_tree_click(self, event):
        # 클릭한 위치의 아이템 확인
        item = self.tree.identify_row(event.y)
        
        # 빈 곳을 클릭했으면 선택 해제
        if not item:
            self.tree.selection_remove(self.tree.selection())

    def validate_ip_address(self, ip: str) -> bool:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            try:
                num = int(part)
            except ValueError:
                return False
            if not 0 <= num <= 255:
                return False
        return True

    def validate_mac_address(self, mac: str) -> bool:
        # XX:XX:XX:XX:XX:XX 또는 XX-XX-XX-XX-XX-XX 형식
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac))

    def validate_port_number(self, num: int) -> bool:
        # 정수인지 확인
        try:
            num = int(num)
        except ValueError:
            return False
        
        # 1-65535 범위 내인지 확인
        if 1 <= num <= 65535:
            return True
        else:
            return False
    
    def validate_pc(self, pc: dict) -> tuple[bool, str]:
        """
        tuple[bool, str]: 검증 결과
        - (True, ""): 모든 데이터가 유효함
        - (False, key): 유효하지 않은 데이터와 필드의 키
        """
        # ip
        if not self.validate_ip_address(pc["ip"]):
            return False, "ip"
        # mac
        if not self.validate_mac_address(pc["mac"]):
            return False, "mac"
        # port
        if not self.validate_port_number(pc["port"]):
            return False, "port"
        
        return True, ""

    def _validate_table_columns(self):
        """table_columns가 json_keys의 부분집합인지 검증"""
        invalid_columns = set(self.table_columns) - set(self.json_keys)
        if invalid_columns:
            raise ValueError(f"Invalid table columns: {invalid_columns}. "
                           f"All table columns must be in json_keys: {self.json_keys}")
    

class PCWindowBase(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.title(self.set_window_title())
        self.geometry("450x180")
        self.resizable(False, False)
        self.build_layout()
        self.add_layout()
        
        # 키 바인딩
        self.bind('<Return>', self.on_enter_key)
        self.bind('<Up>', self.on_up_key)
        self.bind('<Down>', self.on_down_key)
        self.bind('<Left>', self.on_left_key)
        self.bind('<Right>', self.on_right_key)

        # 창을 모달로 설정
        self.transient(master)
        self.grab_set()

    @abstractmethod
    def set_window_title(self) -> str:
        """각 윈도우의 제목 반환"""

    def build_layout(self):
        self.entries = []

        x_pos_label = 30
        x_pos_entry = 120
        y_pos = 30
        entry_width = 30
        y_interval = 20

        entry_to_button_gap = 30
        button_width = 8

        # json_keys를 순회하며 동적으로 레이아웃 생성
        for key in self.master.json_keys:
            # 레이블 생성 (WOLApp의 field_labels 사용)
            label_text = self.master.field_labels[key]
            label = tk.Label(self, text=label_text)
            label.place(x=x_pos_label, y=y_pos)

            # 엔트리 생성
            if key == "port":
                # port는 정수인지 검사
                vcmd = (self.register(self.validate_integer), '%P')
                entry = tk.Entry(self, width=entry_width, validate='key', validatecommand=vcmd)
            else:
                entry = tk.Entry(self, width=entry_width)
            entry.place(x=x_pos_entry, y=y_pos)
            self.entries.append(entry)

            y_pos += y_interval

        # 첫 번째 엔트리에 포커스
        if self.entries:
            self.entries[0].focus()

        y_pos_button = y_pos + entry_to_button_gap

        # OK
        self.button_OK = tk.Button(self, text="OK", width=button_width, command=self.apply_changes)
        self.button_OK.place(x=275, y=y_pos_button)
        # Cancel
        self.button_Cancel = tk.Button(self, text="Cancel", width=button_width, command=self.destroy)
        self.button_Cancel.place(x=350, y=y_pos_button)

        # 창 높이 조정
        window_height = y_pos_button + 40
        self.geometry(f"450x{window_height}")

    @abstractmethod
    def add_layout(self):
        """추가적인 레이아웃 설정"""

    def apply_changes(self):
        """템플릿 메서드 - 공통 저장 로직"""
        # 필드 검사
        if not self.check_required_fields():
            return
        
        # 데이터 가져오기
        pc = self.get_entry_data()

        # 유효성 검사
        is_valid, key = self.master.validate_pc(pc)
        if not is_valid:
            # 에러 메시지 출력
            messagebox.showerror("Input Error", f"Invalid {self.master.field_labels[key]} format")
            # 포커스 이동
            field_index = self.master.json_keys.index(key)
            self.entries[field_index].focus()
            return

        # pc_list 변경 (자식 클래스에서 구현)
        self.update_pc_list(pc)
        
        # 저장 및 새로고침
        self.master.save_pc_list()
        self.master.refresh_pc_table()

        self.destroy()

    @abstractmethod
    def update_pc_list(self, pc: dict):
        """PC 리스트를 업데이트하는 구체적인 방법"""

    def on_enter_key(self, event):
        self.apply_changes()
        return "break"

    def on_up_key(self, event):
        current_widget = event.widget

        # 커서가 맨 위에 있으면 이동하지 않음
        if current_widget == self.entries[0]:
            return "break"
        
        # 이전 위젯으로 이동
        current_widget.tk_focusPrev().focus()
        return "break"
    
    def on_down_key(self, event):
        current_widget = event.widget

        # 커서가 맨 아래에 있으면 이동하지 않음
        if current_widget == self.button_Cancel:
            return "break"
        
        # 다음 위젯으로 이동
        current_widget.tk_focusNext().focus()
        return "break"

    def on_left_key(self, event):
        current_widget = event.widget
        
        # Cancel 버튼에서만 좌측 방향키 작동
        if current_widget == self.button_Cancel:
            self.button_OK.focus()
            return "break"
    
    def on_right_key(self, event):
        current_widget = event.widget
        
        # OK 버튼에서만 우측 방향키 작동
        if current_widget == self.button_OK:
            self.button_Cancel.focus()
            return "break"

    def validate_integer(self, value: str) -> bool:
        # 빈 문자열 허용
        if value == "":
            return True
        
        # 정수인지 확인
        try:
            num = int(value)
        except ValueError:
            return False
        
        return True

    def check_required_fields(self) -> bool:
        for i, key in enumerate(self.master.json_keys):
            entry = self.entries[i]
            if not entry.get():
                field_name = self.master.field_labels[key]
                messagebox.showerror("Input Error", f"{field_name} is required.")
                entry.focus()
                return False
        return True
    
    def get_entry_data(self) -> dict:
        data = {}
        for i, key in enumerate(self.master.json_keys):
            entry = self.entries[i]
            value = entry.get()
            # port는 정수로 변환
            if key == "port":
                value = int(value)
            data[key] = value
        return data
    

class NewPCWindow(PCWindowBase):
    def __init__(self, master=None):
        super().__init__(master)

    def set_window_title(self):
        return "New PC"
    
    def add_layout(self):
        # port 기본값 9로 설정
        port_index = self.master.json_keys.index("port")
        self.entries[port_index].insert(0, "9")

    def update_pc_list(self, pc):
        # pc_list에 추가
        self.master.pc_list.append(pc)


class EditPCWindow(PCWindowBase):
    def __init__(self, master=None):
        self.selected_pc = master.tree.selection()
        super().__init__(master)

    def set_window_title(self):
        return "EDIT PC"

    def add_layout(self):
        # 엔트리에 현재 pc 정보 입력
        pc_index = self.master.tree.index(self.selected_pc[0])
        for i in range(len(self.entries)):
            self.entries[i].insert(0, f"{self.master.pc_list[pc_index][self.master.json_keys[i]]}")

    def update_pc_list(self, pc):
        # pc_list 수정
        pc_index = self.master.tree.index(self.selected_pc[0])
        self.master.pc_list[pc_index] = pc

app = WOLApp()
app.mainloop()