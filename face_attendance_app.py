import cv2
import os
import face_recognition
import pickle
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

class FaceAttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống Điểm danh Khuôn mặt")
        self.root.geometry("1000x600")
        self.root.configure(bg="#f0f0f0")

        self.dataset_path = "dataset/"
        if not os.path.exists(self.dataset_path):
            os.makedirs(self.dataset_path)

        self.attendance_file = "attendance.csv"
        if not os.path.exists(self.attendance_file):
            df = pd.DataFrame(columns=["Name", "Time"])
            df.to_csv(self.attendance_file, index=False)

        self.cap = None
        self.is_capturing = False
        self.is_attending = False
        self.known_face_encodings = []
        self.known_face_names = []

        self.create_main_menu()

    def create_main_menu(self):
        self.clear_window()

        tk.Label(self.root, text="Hệ thống Điểm danh Khuôn mặt", font=("Arial", 20, "bold"), bg="#f0f0f0").pack(pady=20)

        btn_style = {"font": ("Arial", 12), "width": 20, "bg": "#4CAF50", "fg": "white", "pady": 10}
        
        tk.Button(self.root, text="Chụp Ảnh Khuôn mặt", command=self.capture_face_ui, **btn_style).pack(pady=10)
        tk.Button(self.root, text="Điểm danh", command=self.attendance_ui, **btn_style).pack(pady=10)
        tk.Button(self.root, text="Mã hóa Khuôn mặt", command=self.encode_faces, **btn_style).pack(pady=10)
        
        # Sửa lỗi: Tạo bản sao btn_style và thay đổi bg cho nút Thoát
        exit_btn_style = btn_style.copy()
        exit_btn_style["bg"] = "#f44336"
        tk.Button(self.root, text="Thoát", command=self.quit_app, **exit_btn_style).pack(pady=10)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def capture_face_ui(self):
        self.clear_window()
        self.is_capturing = True

        tk.Label(self.root, text="Chụp Ảnh Khuôn mặt", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)

        input_frame = tk.Frame(self.root, bg="#f0f0f0")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Mã số SV:", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, padx=5)
        self.student_id_entry = tk.Entry(input_frame, font=("Arial", 12), width=20)
        self.student_id_entry.grid(row=0, column=1, padx=5)

        tk.Label(input_frame, text="Tên SV:", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=0, padx=5)
        self.student_name_entry = tk.Entry(input_frame, font=("Arial", 12), width=20)
        self.student_name_entry.grid(row=1, column=1, padx=5)

        self.video_label = tk.Label(self.root)
        self.video_label.pack(pady=10)

        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Chụp Ảnh", command=self.save_face, font=("Arial", 12), bg="#4CAF50", fg="white").grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Quay lại", command=self.create_main_menu, font=("Arial", 12), bg="#f44336", fg="white").grid(row=0, column=1, padx=10)

        self.count = 0
        self.start_webcam(self.update_capture_frame)

    def save_face(self):
        student_id = self.student_id_entry.get().strip()
        student_name = self.student_name_entry.get().strip()

        if not student_id or not student_name:
            messagebox.showerror("Lỗi", "Vui lòng nhập mã số và tên sinh viên!")
            return

        file_name = f"{self.dataset_path}/{student_id}_{student_name}_{self.count}.jpg"
        cv2.imwrite(file_name, self.current_frame)
        self.count += 1
        messagebox.showinfo("Thành công", f"Đã lưu: {file_name}")

    def update_capture_frame(self):
        if not self.is_capturing:
            return

        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((400, 300), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.root.after(10, self.update_capture_frame)

    def attendance_ui(self):
        self.clear_window()
        self.is_attending = True

        try:
            with open("face_encodings.pkl", "rb") as f:
                self.known_face_encodings, self.known_face_names = pickle.load(f)
        except FileNotFoundError:
            messagebox.showerror("Lỗi", "Chưa có dữ liệu mã hóa khuôn mặt. Vui lòng mã hóa trước!")
            self.create_main_menu()
            return

        tk.Label(self.root, text="Điểm danh Khuôn mặt", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)

        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(main_frame)
        self.video_label.pack(side=tk.LEFT, padx=20)

        list_frame = tk.Frame(main_frame, bg="#f0f0f0")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(list_frame, text="Kết quả Điểm danh", font=("Arial", 12, "bold"), bg="#f0f0f0").pack()

        self.attendance_tree = ttk.Treeview(list_frame, columns=("Name", "Time"), show="headings", height=10)
        self.attendance_tree.heading("Name", text="Tên sinh viên")
        self.attendance_tree.heading("Time", text="Thời gian")
        self.attendance_tree.column("Name", width=150)
        self.attendance_tree.column("Time", width=200)
        self.attendance_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Button(self.root, text="Quay lại", command=self.create_main_menu, font=("Arial", 12), bg="#f44336", fg="white").pack(pady=10)

        self.start_webcam(self.update_attendance_frame)

    def update_attendance_list(self):
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        
        try:
            df = pd.read_csv(self.attendance_file)
            if not df.empty and all(col in df.columns for col in ["Name", "Time"]):
                for _, row in df.tail(5).iterrows():
                    self.attendance_tree.insert("", "end", values=(row["Name"], row["Time"]))
        except pd.errors.EmptyDataError:
            pass
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file attendance.csv: {str(e)}")

    def update_attendance_frame(self):
        if not self.is_attending:
            return

        ret, frame = self.cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_face_names[first_match_index]
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    df = pd.DataFrame([[name, current_time]], columns=["Name", "Time"])
                    df.to_csv(self.attendance_file, mode="a", header=False, index=False)
                    self.update_attendance_list()

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            self.current_frame = frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((400, 300), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.root.after(10, self.update_attendance_frame)

    def encode_faces(self):
        known_face_encodings = []
        known_face_names = []

        for file_name in os.listdir(self.dataset_path):
            if file_name.endswith(".jpg"):
                name = file_name.split("_")[1]
                image_path = os.path.join(self.dataset_path, file_name)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(name)

        if not known_face_encodings:
            messagebox.showerror("Lỗi", "Không tìm thấy khuôn mặt nào trong dataset!")
            return

        with open("face_encodings.pkl", "wb") as f:
            pickle.dump((known_face_encodings, known_face_names), f)

        messagebox.showinfo("Thành công", "Đã lưu mã hóa khuôn mặt!")

    def start_webcam(self, update_func):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể mở webcam!")
            self.create_main_menu()
            return
        self.root.after(10, update_func)

    def quit_app(self):
        if self.cap:
            self.cap.release()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceAttendanceApp(root)
    root.mainloop()