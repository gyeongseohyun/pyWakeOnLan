# ip, mac 유효성 검사 필요
# 창 크기에 따른 pc table 크기 변화 필요
# 더블클릭, delete, 단축키
# 아이콘 변경
# json_keys를 통한 유지보수성 향상

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import json

class WOLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.json_file = "PCList.json"

        self.title("Wake on LAN")
        self.geometry("600x600")
        self.build_layout()

        self.pc_list = []
        self.json_keys = ["name", "ip", "mac", "port"]
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
        self.button_wol = tk.Button(self.toolbar_frame, text="Wake Up", width=10, state=tk.DISABLED)
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
        self.tree = ttk.Treeview(self, columns=self.json_keys, show='headings', height=20)
        
        # 컬럼 헤더 설정
        self.tree.heading('name', text='PC Name')
        self.tree.heading('ip', text='IP Address')
        self.tree.heading('mac', text='MAC Address')
        self.tree.heading('port', text='Port')

        # 컬럼 너비 설정
        self.tree.column('name', width=150)
        self.tree.column('ip', width=150)
        self.tree.column('mac', width=180)
        self.tree.column('port', width=80)

        # 스크롤바 생성
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 테이블과 스크롤바 배치
        self.tree.place(x=10, y=50, width=570, height=535)
        scrollbar.place(x=580, y=50, height=535)

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
            values = [
                pc.get("name", ""),
                pc.get("ip", ""),
                pc.get("mac", ""),
                pc.get("port", "")
            ]
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
    def set_window_title(self):
        """각 윈도우의 제목 반환"""
        pass

    def build_layout(self):
        # name
        self.label_name = tk.Label(self, text="PC NAME")
        self.label_name.place(x=30, y=30)
        self.entry_name = tk.Entry(self, width=30)
        self.entry_name.place(x=120, y=30)
        self.entry_name.focus()
        # ip
        self.label_ip = tk.Label(self, text="IP ADDRESS")
        self.label_ip.place(x=30, y=50)
        self.entry_ip = tk.Entry(self, width=30)
        self.entry_ip.place(x=120, y=50)
        # mac
        self.label_mac = tk.Label(self, text="MAC ADDRESS")
        self.label_mac.place(x=30, y=70)
        self.entry_mac = tk.Entry(self, width=30)
        self.entry_mac.place(x=120, y=70)
        # port(숫자만 입력 가능)
        self.label_port = tk.Label(self, text="PORT")
        self.label_port.place(x=30, y=90)
        vcmd = (self.register(self.validate_port_number), '%P')
        self.entry_port = tk.Entry(self, width=30, validate='key', validatecommand=vcmd)
        self.entry_port.place(x=120, y=90)

        # OK
        self.button_OK = tk.Button(self, text="OK", width=8, command=self.save_pc_list)
        self.button_OK.place(x=275, y=140)
        # Cancel
        self.button_Cancel = tk.Button(self, text="Cancel", width=8, command=self.destroy)
        self.button_Cancel.place(x=350, y=140)

    @abstractmethod
    def add_layout(self):
        """추가적인 레이아웃 설정"""
        pass

    @abstractmethod
    def save_pc_list(self):
        """데이터 저장"""
        pass

    def on_enter_key(self, event):
        self.save_pc_list()
        return "break"

    def on_up_key(self, event):
        current_widget = event.widget

        # 커서가 맨 위에 있으면 이동하지 않음
        if current_widget == self.entry_name:
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

    def validate_port_number(self, value):
        # 빈 문자열 허용
        if value == "":
            return True
        
        # 숫자인지 확인
        try:
            num = int(value)
        except ValueError:
            return False
        
        # 1-65535 범위 내인지 확인
        if 1 <= num <= 65535:
            return True
        else:
            return False


class NewPCWindow(PCWindowBase):
    def __init__(self, master=None):
        super().__init__(master)

    def set_window_title(self):
        return "New PC"
    
    def add_layout(self):
        self.entry_port.insert(0, "9")

    def save_pc_list(self):
        # Entry에서 값 가져오기
        pc_name = self.entry_name.get()
        ip_address = self.entry_ip.get()
        mac_address = self.entry_mac.get()
        port = self.entry_port.get()
        
        # 유효성 검사
        if not pc_name:
            messagebox.showerror("Input Error", "PC name is required.")
            self.entry_name.focus()
            return
        if not ip_address:
            messagebox.showerror("Input Error", "IP address is required.")
            self.entry_ip.focus()
            return
        if not mac_address:
            messagebox.showerror("Input Error", "MAC address is required.")
            self.entry_mac.focus()
            return
        if not port:
            messagebox.showerror("Input Error", "Port number is required.")
            self.entry_port.focus()
            return
        
        port = int(port)
        
        # pc_list에 추가
        new_pc = {
            "name": pc_name,
            "ip": ip_address,
            "mac": mac_address,
            "port": port
        }
        self.master.pc_list.append(new_pc)
        
        # json 파일에 쓰기
        self.master.save_pc_list()
        
        # pc_table 새로고침
        self.master.refresh_pc_table()

        self.destroy()


class EditPCWindow(PCWindowBase):
    def __init__(self, master=None):
        self.selected_pc = master.tree.selection()
        super().__init__(master)

    def set_window_title(self):
        return "EDIT PC"

    def add_layout(self):
        pc_info = self.master.tree.item(self.selected_pc[0], "values")
        self.entry_name.insert(0, f"{pc_info[0]}")
        self.entry_ip.insert(0, f"{pc_info[1]}")
        self.entry_mac.insert(0, f"{pc_info[2]}")
        self.entry_port.delete(0, tk.END)
        self.entry_port.insert(0, f"{pc_info[3]}")
    
    def save_pc_list(self):
        # Entry에서 값 가져오기
        pc_name = self.entry_name.get()
        ip_address = self.entry_ip.get()
        mac_address = self.entry_mac.get()
        port = self.entry_port.get()
        
        # 유효성 검사
        if not pc_name:
            messagebox.showerror("Input Error", "PC name is required.")
            self.entry_name.focus()
            return
        if not ip_address:
            messagebox.showerror("Input Error", "IP address is required.")
            self.entry_ip.focus()
            return
        if not mac_address:
            messagebox.showerror("Input Error", "MAC address is required.")
            self.entry_mac.focus()
            return
        if not port:
            messagebox.showerror("Input Error", "Port number is required.")
            self.entry_port.focus()
            return
        
        port = int(port)
        
        # pc_list 수정
        pc_index = self.master.tree.index(self.selected_pc[0])
        self.master.pc_list[pc_index]["name"] = pc_name
        self.master.pc_list[pc_index]["ip"] = ip_address
        self.master.pc_list[pc_index]["mac"] = mac_address
        self.master.pc_list[pc_index]["port"] = port
        
        # json 파일에 쓰기
        self.master.save_pc_list()
        
        # pc_table 새로고침
        self.master.refresh_pc_table()

        self.destroy()

app = WOLApp()
app.mainloop()