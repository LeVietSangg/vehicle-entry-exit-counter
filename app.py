import subprocess
import sys
import re
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

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)

        tk.Button(
            button_frame,
            text="Start Processing",
            width=18,
            command=self.start_processing
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            button_frame,
            text="Reset",
            width=12,
            command=self.reset_form
        ).grid(row=0, column=1, padx=8)

        tk.Button(
            button_frame,
            text="Open Outputs",
            width=15,
            command=self.open_outputs
        ).grid(row=0, column=2, padx=8)

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

    def start_processing(self):
        video = self.video_path.get()

        if not Path(video).exists():
            messagebox.showerror("Error", "Không tìm thấy video đầu vào.")
            return

        command = [
            sys.executable,
            "main.py",
            "--source", video,
            "--model", self.model_path.get(),
            "--conf", self.conf.get(),
            "--iou", self.iou.get(),
            "--entry_line_y", self.entry_line_y.get(),
            "--exit_line_y", self.exit_line_y.get(),
        ]

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Đang xử lý video...\n\n")
        self.root.update()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

            self.output_text.insert(tk.END, result.stdout)

            if result.stderr:
                self.output_text.insert(tk.END, "\n--- ERROR ---\n")
                self.output_text.insert(tk.END, result.stderr)

            # Phân tích log để lấy đường dẫn file Excel
            match = re.search(r"Đã lưu báo cáo Excel tại:\s*(.*\.xlsx)", result.stdout)
            
            messagebox.showinfo("Done", "Xử lý hoàn tất. Kiểm tra thư mục outputs.")
            
            if match:
                excel_path = match.group(1).strip()
                self.show_chart(excel_path)

        except Exception as e:
            messagebox.showerror("Error", str(e))

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