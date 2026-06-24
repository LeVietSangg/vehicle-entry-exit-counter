import subprocess
import sys
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

            messagebox.showinfo("Done", "Xử lý hoàn tất. Kiểm tra thư mục outputs.")

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


if __name__ == "__main__":
    root = tk.Tk()
    app = VehicleCounterApp(root)
    root.mainloop()