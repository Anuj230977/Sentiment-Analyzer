from datetime import datetime
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
import nltk
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# ─── CORE LOGIC ───────────────────────────────────────────────
class SentimentEngine:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.neutral_overrides = {"okay", "ok", "fine", "alright", "average", "moderate"}

    def analyze(self, text):
        if not isinstance(text, str) or text.strip() == "":
            return "Neutral", 0.0
        
        text_clean = text.strip()
        words = set(text_clean.lower().split())
        
        # Fast-track neutrality for short, generic responses
        if words & self.neutral_overrides and len(text_clean.split()) <= 6:
            return "Neutral", 0.0
        
        # Using VADER for better handling of negations ("not good", "hardly great")
        score = self.sia.polarity_scores(text_clean)['compound']
        
        if score >= 0.05:
            return "Positive", round(score, 3)
        elif score <= -0.05:
            return "Negative", round(score, 3)
        else:
            return "Neutral", round(score, 3)

TEXT_COLUMN_ALIASES = (
    "review text",
    "tweet text",
    "full text",
    "review",
    "comment",
    "comments",
    "content",
    "message",
    "text",
)

engine = None
root = None
text_input = None
result_label = None
status_label = None
progress_bar = None


def get_engine():
    global engine
    if engine is not None:
        return engine
    try:
        engine = SentimentEngine()
    except LookupError:
        nltk.download("vader_lexicon", quiet=True)
        engine = SentimentEngine()
    return engine


def normalize_column_name(column):
    return str(column).strip().lower().replace("-", " ").replace("_", " ")


def default_text_column(columns):
    lookup = {normalize_column_name(column): column for column in columns}
    for alias in TEXT_COLUMN_ALIASES:
        if alias in lookup:
            return lookup[alias]
    return columns[0] if columns else ""


def non_empty_text_rows(df, selected_col):
    text_values = df[selected_col].fillna("").astype(str).str.strip()
    return df.loc[text_values != ""].copy()

# ─── GENERATE CHART ──────────────────────────────────────────────
def generate_chart(df, output_dir):
    counts = df["Sentiment"].value_counts()
    colors = {"Positive": "#4CAF50", "Negative": "#F44336", "Neutral": "#2196F3"}
    pie_colors = [colors.get(label, "#999") for label in counts.index]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%",
           colors=pie_colors, startangle=140)
    ax.set_title("Sentiment Distribution", fontsize=14, fontweight="bold")

    chart_path = os.path.join(output_dir, "sentiment_chart.png")
    plt.savefig(chart_path, bbox_inches="tight", dpi=150)
    plt.close()
    return chart_path

# ─── ANALYZE CSV (THREADED) ──────────────────────────────────────
def run_analysis_thread(df, selected_col, file_path, progress_bar, status_label):
    try:
        df = non_empty_text_rows(df, selected_col)
        if df.empty:
            root.after(0, lambda: messagebox.showwarning("No Text Rows", "No non-empty text rows found."))
            root.after(0, lambda: status_label.config(text="Idle"))
            root.after(0, lambda: progress_bar.config(mode='determinate', value=0))
            return

        total_rows = len(df)
        sentiments = []
        scores = []

        for i, text in enumerate(df[selected_col].astype(str), start=1):
            sent, score = get_engine().analyze(text)
            sentiments.append(sent)
            scores.append(score)
            
            # Update progress bar every 10 rows to save CPU (Thread-Safe)
            if i % 10 == 0 or i == total_rows:
                progress = int((i / total_rows) * 100)
                # Pass a sticky note to the main thread to safely update the UI
                root.after(0, lambda p=progress: progress_bar.configure(value=p))
                root.after(0, lambda p=progress: status_label.config(text=f"Processing: {p}%"))

        df["Sentiment"] = sentiments
        df["Polarity Score"] = scores

        # Save output
        output_dir = os.path.join(os.path.dirname(file_path), "sentiment_output")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(output_dir, f"sentiment_result_{timestamp}.csv")
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

        generate_chart(df, output_dir)
        
        counts = df["Sentiment"].value_counts().to_dict()
        
        # Final UI Update back in main thread
        root.after(0, lambda: messagebox.showinfo("✅ Done!", (
            f"Analyzed {total_rows} rows\n\n"
            f"😊 Positive: {counts.get('Positive', 0)}\n"
            f"😐 Neutral:  {counts.get('Neutral', 0)}\n"
            f"😠 Negative: {counts.get('Negative', 0)}\n\n"
            f"Results saved to:\n{out_path}"
        )))
        root.after(0, lambda: status_label.config(text="Analysis Complete!"))
        root.after(0, lambda: progress_bar.config(mode='determinate', value=0))

    except Exception as e:
        root.after(
            0,
            lambda error_message=str(e): messagebox.showerror(
                "Error",
                error_message,
            ),
        )

def analyze_csv():
    file_path = filedialog.askopenfilename(
        title="Select CSV or Excel File",
        filetypes=[("CSV/Excel Files", "*.csv *.xlsx *.xls")]
    )
    if not file_path:
        return

    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, encoding="utf-8-sig")
        else:
            df = pd.read_excel(file_path)

        columns = list(df.columns)
        if not columns:
            messagebox.showerror("Error", "The file does not contain any columns.")
            return

        col_window = tk.Toplevel(root)
        col_window.title("Select Text Column")
        col_window.geometry("300x150")
        col_window.configure(bg="#1e1e2e")
        
        tk.Label(col_window, text="Which column has the text?", bg="#1e1e2e", fg="#cdd6f4").pack(pady=10)
        col_var = tk.StringVar(value=default_text_column(columns))
        col_menu = ttk.Combobox(col_window, textvariable=col_var, values=columns, state="readonly")
        col_menu.pack(pady=5)

        def start_analysis():
            selected_col = col_var.get()
            col_window.destroy()
            
            # Change UI to loading state
            progress_bar.config(mode='determinate')
            status_label.config(text="Starting analysis...")
            
            # RUN IN THREAD to prevent GUI freeze
            thread = threading.Thread(target=run_analysis_thread, args=(df, selected_col, file_path, progress_bar, status_label), daemon=True)
            thread.start()

        tk.Button(col_window, text="Analyze Now", command=start_analysis, bg="#4CAF50", fg="white", relief="flat").pack(pady=15)

    except Exception as e:
        messagebox.showerror("Error", str(e))

def analyze_text():
    text = text_input.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Empty", "Please enter some text first.")
        return
    sentiment, score = get_engine().analyze(text)
    emoji = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}[sentiment]
    result_label.config(text=f"{emoji} {sentiment}  |  Score: {score}")

# ─── GUI ─────────────────────────────────────────────────────────
def build_gui():
    global root, text_input, result_label, status_label, progress_bar

    root = tk.Tk()
    root.title("Sentiment Analyzer Pro - by Anuj")
    root.geometry("500x500")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    tk.Label(root, text="💬 Sentiment Analyzer", font=("Arial", 18, "bold"),
             bg="#1e1e2e", fg="#cdd6f4").pack(pady=15)

    tk.Label(root, text="Type or paste text below:", bg="#1e1e2e", fg="#a6adc8").pack()
    text_input = tk.Text(root, height=5, width=55, font=("Arial", 11),
                         bg="#313244", fg="#cdd6f4", insertbackground="white",
                         relief="flat", padx=8, pady=8)
    text_input.pack(pady=8)

    tk.Button(root, text="Analyze Text", command=analyze_text,
              bg="#89b4fa", fg="#1e1e2e", font=("Arial", 11, "bold"),
              relief="flat", padx=20, pady=6).pack(pady=5)

    result_label = tk.Label(root, text="Result will appear here",
                            font=("Arial", 13), bg="#1e1e2e", fg="#a6e3a1")
    result_label.pack(pady=10)

    tk.Label(root, text="─" * 55, bg="#1e1e2e", fg="#45475a").pack()

    tk.Label(root, text="Bulk Analysis:", bg="#1e1e2e", fg="#a6adc8").pack(pady=5)
    tk.Button(root, text="📂 Upload CSV / Excel File", command=analyze_csv,
              bg="#a6e3a1", fg="#1e1e2e", font=("Arial", 11, "bold"),
              relief="flat", padx=20, pady=6).pack(pady=5)

    status_label = tk.Label(
        root,
        text="Idle",
        bg="#1e1e2e",
        fg="#585b70",
        font=("Arial", 10),
    )
    status_label.pack(pady=(15, 0))
    progress_bar = ttk.Progressbar(
        root,
        orient="horizontal",
        length=300,
        mode="indeterminate",
    )
    progress_bar.pack(pady=5)

    tk.Label(root, text="Powered by VADER",
             bg="#1e1e2e", fg="#585b70", font=("Arial", 9)).pack(side="bottom", pady=8)
    return root


def main():
    build_gui().mainloop()


if __name__ == "__main__":
    main()
