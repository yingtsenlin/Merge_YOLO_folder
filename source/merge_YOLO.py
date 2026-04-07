import os
import shutil
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def merge_yolo_folders(base_path, folder_prefix, log_callback=None, confirm_callback=None):
    """
    base_path: 存放所有東西的資料夾 (例如 dataset)
    folder_prefix: 資料夾的前綴，例如 'CGTD01_260310_075343'
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    origin_dir = os.path.join(base_path, "origin")

    # 1. 搜尋符合前綴的資料夾並提取結尾數字
    pattern = re.compile(rf"^{re.escape(folder_prefix)}_(\d+)$")
    folders = []
    
    for entry in os.listdir(origin_dir):
        match = pattern.match(entry)
        if match:
            folders.append({
                'name': entry,
                'index': int(match.group(1))
            })

    if not folders:
        log(f"❌ 找不到符合前綴 '{folder_prefix}' 的資料夾。")
        return

    # 2. 依照數字小到大排序
    folders.sort(key=lambda x: x['index'])
    
    # 3. 檢查數字缺漏
    indices = [f['index'] for f in folders]
    missing = [i for i in range(min(indices), max(indices) + 1) if i not in indices]
    if missing:
        log(f"⚠️  提醒：發現資料夾編號缺漏！缺少的編號為: {missing}")
        if confirm_callback and not confirm_callback(missing):
            log("❌ 使用者取消合併作業。")
            return
    else:
        log(f"✅ 資料夾編號連續，未發現缺漏。")

    # 4. 建立輸出的合併資料夾
    output_dir = os.path.join(base_path, "results", f"{folder_prefix}_MERGED")
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)

    # 5. 開始合併與重新命名
    log(f"🚀 開始合併至: {output_dir}")
    
    first_folder = True
    for folder in folders:
        folder_name = folder['name']
        folder_idx = folder['index']
        src_path = os.path.join(origin_dir, folder_name)

        # 處理 classes.txt (只從第一個資料夾複製一次)
        if first_folder:
            shutil.copy(os.path.join(src_path, "classes.txt"), output_dir)
            first_folder = False

        # 處理 images 與 labels
        for sub_type in ["images", "labels"]:
            src_sub = os.path.join(src_path, sub_type)
            if not os.path.exists(src_sub):
                continue
                
            for filename in os.listdir(src_sub):
                name, ext = os.path.splitext(filename)
                # 新檔名格式: frame_000000_1.jpg
                new_filename = f"{folder_idx}_{name}{ext}"
                
                src_file = os.path.join(src_sub, filename)
                dst_file = os.path.join(output_dir, sub_type, new_filename)
                
                shutil.copy2(src_file, dst_file)
        
        log(f"--- 已完成資料夾: {folder_name}")

    log(f"\n✨ 合併完成！")

# --- 使用設定 ---
def create_gui():
    def browse_folder():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            path_entry.delete(0, tk.END)
            path_entry.insert(0, folder_selected)

    def start_merge():
        target_path = path_entry.get().strip()
        prefix = prefix_entry.get().strip()

        # 清空並準備日誌區域
        log_text.delete(1.0, tk.END)
        
        def log_msg(msg):
            log_text.insert(tk.END, msg + "\n")
            log_text.see(tk.END)
            log_text.update()  # 強制更新 UI，讓日誌即時顯示出來
            
        def confirm_missing(missing_list):
            return messagebox.askyesno("發現缺漏", f"資料夾編號有缺漏：\n{missing_list}\n\n請問是否要繼續執行合併？")
        
        if not target_path or not prefix:
            messagebox.showwarning("警告", "請輸入完整的 Target Path 與 Prefix！")
            return
            
        origin_path = os.path.join(target_path, "origin")
        if not os.path.exists(origin_path):
            messagebox.showwarning("警告", f"在目標路徑中找不到 'origin' 資料夾！\n請確認路徑: {origin_path}")
            return

        try:
            merge_yolo_folders(target_path, prefix, log_callback=log_msg, confirm_callback=confirm_missing)
            messagebox.showinfo("成功", "合併程序已完成！")
        except Exception as e:
            log_msg(f"❌ 執行時發生錯誤:\n{str(e)}")
            messagebox.showerror("錯誤", f"執行時發生錯誤:\n{str(e)}")

    # 建立主視窗
    root = tk.Tk()
    root.title("YOLO 資料夾合併工具")
    root.resizable(False, False) # 固定視窗大小

    # Target Path 介面
    tk.Label(root, text="Target Path:").grid(row=0, column=0, padx=10, pady=15, sticky="e")
    path_entry = tk.Entry(root, width=45)
    path_entry.grid(row=0, column=1, padx=5, pady=15)
    path_entry.insert(0, "../dataset/")  # 預設值
    tk.Button(root, text="瀏覽...", command=browse_folder).grid(row=0, column=2, padx=10, pady=15)

    # Prefix 介面
    tk.Label(root, text="Prefix:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    prefix_entry = tk.Entry(root, width=45)
    prefix_entry.grid(row=1, column=1, padx=5, pady=5)

    # 執行按鈕
    tk.Button(root, text="開始合併", command=start_merge, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15).grid(row=2, column=1, pady=10)

    # 日誌顯示區
    tk.Label(root, text="執行日誌:").grid(row=3, column=0, padx=10, pady=5, sticky="ne")
    log_text = scrolledtext.ScrolledText(root, width=55, height=15)
    log_text.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="w")

    root.mainloop()

if __name__ == "__main__":
    create_gui()