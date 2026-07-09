import subprocess
import sys
import re
import os
import threading
import queue
import cv2
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox


class VehicleCounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vehicle Entry/Exit Counter")
        self.root.geometry("950x620")

        self.video_path = tk.StringVar(value="data/video_easy.mp4")
        self.model_path = tk.StringVar(value="yolov8m.pt")
        self.conf = tk.StringVar(value="0.25")
        self.iou = tk.StringVar(value="0.45")
        self.entry_line_y = tk.StringVar(value="430")
        self.exit_line_y = tk.StringVar(value="330")

        self.process = None
        self.log_queue = queue.Queue()
        self.is_running = False

        self.build_ui()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="Vehicle Entry/Exit Counter",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=(15, 5))

        subtitle = tk.Label(
            self.root,
            text="AI Vehicle Monitoring and Counting System",
            font=("Arial", 11)
        )
        subtitle.pack(pady=(0, 15))

        form = tk.LabelFrame(self.root, text="Processing Configuration", padx=15, pady=15)
        form.pack(fill="x", padx=20)

        self.add_input(form, "Video Source", self.video_path, 0, browse=True)
        self.add_input(form, "Model", self.model_path, 1)
        self.add_input(form, "Confidence", self.conf, 2)
        self.add_input(form, "IoU", self.iou, 3)
        self.add_input(form, "Entry Line Y", self.entry_line_y, 4)
        self.add_input(form, "Exit Line Y", self.exit_line_y, 5)

        tk.Button(
            form,
            text="🎯 Pick Lines",
            command=self.pick_lines_visual,
            bg="#e0f7fa"
        ).grid(row=4, column=2, rowspan=2, padx=5, sticky="ns")

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)

        self.start_btn = tk.Button(
            button_frame,
            text="Start Processing",
            width=18,
            command=self.start_processing
        )
        self.start_btn.grid(row=0, column=0, padx=8)

        self.stop_btn = tk.Button(
            button_frame,
            text="Stop Processing",
            width=18,
            bg="#ff4d4d",
            fg="white",
            state=tk.DISABLED,
            command=self.stop_processing
        )
        self.stop_btn.grid(row=0, column=1, padx=8)

        tk.Button(
            button_frame,
            text="Reset",
            width=12,
            command=self.reset_form
        ).grid(row=0, column=2, padx=8)

        tk.Button(
            button_frame,
            text="Open Outputs",
            width=15,
            command=self.open_outputs
        ).grid(row=0, column=3, padx=8)

        result_frame = tk.LabelFrame(self.root, text="Processing Result", padx=10, pady=10)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.output_text = tk.Text(result_frame, height=16)
        self.output_text.pack(fill="both", expand=True)

    def add_input(self, parent, label, variable, row, browse=False):
        tk.Label(parent, text=label, width=15, anchor="w").grid(
            row=row, column=0, padx=5, pady=7
        )

        tk.Entry(parent, textvariable=variable, width=70).grid(
            row=row, column=1, padx=5, pady=7
        )

        if browse:
            tk.Button(
                parent,
                text="Browse",
                command=self.browse_video
            ).grid(row=row, column=2, padx=5)

    def browse_video(self):
        file_path = filedialog.askopenfilename(
            title="Select video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.video_path.set(file_path)

    def pick_lines_visual(self):
        video = self.video_path.get()
        if not Path(video).exists():
            messagebox.showerror("Error", "Không tìm thấy video đầu vào để lấy mẫu.")
            return

        cap = cv2.VideoCapture(video)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            messagebox.showerror("Error", "Không thể đọc frame từ video.")
            return

        clone = frame.copy()
        cv2.putText(clone, "Click lan 1: Chon Y cho vach VAO (Xanh)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(clone, "Click lan 2: Chon Y cho vach RA (Do)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        click_count = [0]

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if click_count[0] == 0:
                    self.entry_line_y.set(str(y))
                    mid_x = clone.shape[1] // 2
                    cv2.line(clone, (mid_x, y), (clone.shape[1], y), (0, 255, 0), 2)
                    cv2.imshow("Pick Lines - Nhan Esc de thoat", clone)
                    click_count[0] += 1
                elif click_count[0] == 1:
                    self.exit_line_y.set(str(y))
                    mid_x = clone.shape[1] // 2
                    cv2.line(clone, (0, y), (mid_x, y), (0, 0, 255), 2)
                    cv2.imshow("Pick Lines - Nhan Esc de thoat", clone)
                    click_count[0] += 1
                    
        cv2.namedWindow("Pick Lines - Nhan Esc de thoat")
        cv2.setMouseCallback("Pick Lines - Nhan Esc de thoat", mouse_callback)
        
        while True:
            cv2.imshow("Pick Lines - Nhan Esc de thoat", clone)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or click_count[0] == 2:  # ESC key or 2 clicks
                if click_count[0] == 2:
                    cv2.waitKey(500) # Give user a moment to see the drawn line
                break
                
        cv2.destroyWindow("Pick Lines - Nhan Esc de thoat")

    def start_processing(self):
        video = self.video_path.get()

        if not Path(video).exists():
            messagebox.showerror("Error", "Không tìm thấy video đầu vào.")
            return

        command = [
            sys.executable,
            "-u",
            "main.py",
            "--source", video,
            "--model", self.model_path.get(),
            "--conf", self.conf.get(),
            "--iou", self.iou.get(),
            "--entry_line_y", self.entry_line_y.get(),
            "--exit_line_y", self.exit_line_y.get()
        ]

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Đang khởi tạo...\n\n")
        
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        if os.path.exists("stop.flag"):
            os.remove("stop.flag")

        threading.Thread(target=self.run_process_thread, args=(command,), daemon=True).start()
        self.root.after(100, self.update_console)

    def stop_processing(self):
        if self.is_running:
            with open("stop.flag", "w") as f:
                f.write("STOP")
            self.output_text.insert(tk.END, "\n[Hệ thống] Đã nhận lệnh dừng khẩn cấp, đang dọn dẹp...\n")
            self.stop_btn.config(state=tk.DISABLED)

    def run_process_thread(self, command):
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
                universal_newlines=True
            )
            
            for line in iter(self.process.stdout.readline, ''):
                self.log_queue.put(line)
                
            self.process.stdout.close()
            self.process.wait()
            self.log_queue.put("___PROCESS_DONE___")
        except Exception as e:
            self.log_queue.put(f"Lỗi khi chạy tiến trình: {str(e)}")
            self.log_queue.put("___PROCESS_DONE___")

    def update_console(self):
        while not self.log_queue.empty():
            line = self.log_queue.get_nowait()
            if line == "___PROCESS_DONE___":
                self.is_running = False
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                
                # Check for output excel in text
                output_content = self.output_text.get("1.0", tk.END)
                match = re.search(r"Đã lưu báo cáo Excel tại:\s*(.*\.xlsx)", output_content)
                if match:
                    excel_path = match.group(1).strip()
                    messagebox.showinfo("Done", "Xử lý hoàn tất. Kiểm tra thư mục outputs.")
                    self.show_chart(excel_path)
                return
            else:
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
                
        if self.is_running:
            self.root.after(100, self.update_console)

    def reset_form(self):
        self.video_path.set("data/video_easy.mp4")
        self.model_path.set("yolov8m.pt")
        self.conf.set("0.25")
        self.iou.set("0.45")
        self.entry_line_y.set("288")
        self.exit_line_y.set("200")
        self.output_text.delete("1.0", tk.END)

    def open_outputs(self):
        outputs = Path("outputs")
        outputs.mkdir(exist_ok=True)
        subprocess.Popen(f'explorer "{outputs.resolve()}"')

    def show_chart(self, excel_path):
        try:
            import pandas as pd
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Đọc dữ liệu, bỏ 2 dòng tiêu đề đầu tiên của Excel
            df = pd.read_excel(excel_path, sheet_name=0, header=2) # Đọc sheet Summary
            # Bỏ dòng tổng cộng
            df = df[df['Loại xe'] != 'TỔNG CỘNG']
            df = df[df['Tổng'] > 0] # Chỉ lấy xe có dữ liệu
            
            if df.empty:
                return # Không có dữ liệu để vẽ

            # Tạo cửa sổ mới (Toplevel)
            chart_win = tk.Toplevel(self.root)
            chart_win.title("Thống kê Dữ liệu Giao thông")
            chart_win.geometry("900x450")
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.5))
            
            # Biểu đồ tròn: Tỷ lệ các loại xe
            ax1.pie(df['Tổng'], labels=df['Loại xe'], autopct='%1.1f%%', startangle=90)
            ax1.set_title("Tỷ lệ các loại xe")
            
            # Biểu đồ cột: So sánh Vào/Ra
            x = range(len(df['Loại xe']))
            width = 0.35
            ax2.bar([i - width/2 for i in x], df['Số xe Vào (Entry)'], width, label='Vào', color='green')
            ax2.bar([i + width/2 for i in x], df['Số xe Ra (Exit)'], width, label='Ra', color='red')
            ax2.set_title("Lưu lượng Vào / Ra")
            ax2.set_xticks(x)
            ax2.set_xticklabels(df['Loại xe'])
            ax2.legend()
            
            plt.tight_layout()
            
            # Đưa biểu đồ vào Tkinter
            canvas = FigureCanvasTkAgg(fig, master=chart_win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Lỗi biểu đồ", f"Không thể vẽ biểu đồ: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VehicleCounterApp(root)
    root.mainloop()