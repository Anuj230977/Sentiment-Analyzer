import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import platform
import subprocess
import re
import uuid
from datetime import datetime
import threading
from pathlib import Path
from typing import Callable, Optional, Sequence
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
import warnings
warnings.filterwarnings("ignore")

# ─── One-time NLTK setup ──────────────────────────────────────
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    try:
        nltk.download("vader_lexicon", quiet=True)
    except (OSError, RuntimeError):
        pass


# ─── CORE SENTIMENT ENGINE ────────────────────────────────────
class SentimentEngine:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.neutral_overrides = {
            "okay", "ok", "fine", "alright", "average", "moderate",
            "so-so", "meh", "neutral", "normal"
        }

    def analyze(self, text: object) -> tuple[str, float]:
        if not isinstance(text, str) or not text.strip():
            return "Neutral", 0.0

        text_clean = text.strip()
        words = set(text_clean.lower().split())

        if words & self.neutral_overrides and len(text_clean.split()) <= 6:
            return "Neutral", 0.0

        score = self.sia.polarity_scores(text_clean)["compound"]

        if score >= 0.05:
            return "Positive", round(score, 3)
        elif score <= -0.05:
            return "Negative", round(score, 3)
        else:
            return "Neutral", round(score, 3)


# ─── FIXED & MORE ROBUST TOPIC EXTRACTION ─────────────────────
class TopicExtractor:
    def __init__(self, n_topics=6, n_top_words=4):
        self.n_topics = n_topics
        self.n_top_words = n_top_words
        self.vectorizer = None
        self.model = None
        self.topic_labels = []

    def _clean_text(self, text: object) -> str:
        """Light cleaning – keep meaning"""
        text = str(text).lower()
        text = re.sub(r'\d+', ' ', text)          # remove pure numbers
        text = re.sub(r'[^\w\s]', ' ', text)       # remove punctuation
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def fit_transform(self, texts: Sequence[object]) -> tuple[list[str], Optional[list[str]]]:
        original_texts = list(texts)
        cleaned = []
        valid_indices = []

        for i, t in enumerate(original_texts):
            ct = self._clean_text(t)
            if len(ct.split()) >= 2:          # very light filter
                cleaned.append(ct)
                valid_indices.append(i)

        if len(cleaned) < 8:                  # only abort on tiny data
            return ["Not enough data"] * len(original_texts), None

        # Adaptive min_df
        min_df = 1 if len(cleaned) < 40 else 2

        self.vectorizer = TfidfVectorizer(
            max_df=0.90,
            min_df=min_df,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=1000
        )

        try:
            tfidf = self.vectorizer.fit_transform(cleaned)
            if tfidf.shape[1] < 5:            # too few features
                return ["Not enough data"] * len(original_texts), None
        except (ValueError, TypeError):
            return ["Not enough data"] * len(original_texts), None

        # NMF cannot use more components than available TF-IDF features.
        n_topics = min(self.n_topics, tfidf.shape[1])
        if n_topics < 1:
            return ["Not enough data"] * len(original_texts), None

        try:
            self.model = NMF(n_components=n_topics, random_state=42, max_iter=600)
            W = self.model.fit_transform(tfidf)
        except (ValueError, TypeError, RuntimeError):
            return ["Not enough data"] * len(original_texts), None
        H = self.model.components_

        feature_names = self.vectorizer.get_feature_names_out()
        self.topic_labels = []

        for topic in H:
            top_indices = topic.argsort()[:-self.n_top_words-1:-1]
            top_words = [feature_names[i] for i in top_indices]
            # Remove any leftover number tokens
            top_words = [w for w in top_words if not re.search(r'\d', w)]
            label = ", ".join(top_words) if top_words else "general"
            self.topic_labels.append(label)

        # Build dominant topic list matching original length
        dominant = ["No text"] * len(original_texts)
        for idx, clean_idx in enumerate(valid_indices):
            topic_id = W[idx].argmax()
            dominant[clean_idx] = self.topic_labels[topic_id]

        return dominant, self.topic_labels


engine = SentimentEngine()
topic_extractor = TopicExtractor(n_topics=6, n_top_words=4)
cancel_event = threading.Event()
root: Optional[tk.Tk] = None
analyze_text_btn: Optional[tk.Button] = None
analyze_file_btn: Optional[tk.Button] = None
cancel_btn: Optional[tk.Button] = None
progress_bar: Optional[ttk.Progressbar] = None
status_label: Optional[tk.Label] = None
text_input: Optional[tk.Text] = None
result_label: Optional[tk.Label] = None


def load_input_file(file_path: str) -> pd.DataFrame:
    """Load a CSV or Excel file, trying common CSV encodings."""
    if file_path.lower().endswith(".csv"):
        last_error: Optional[UnicodeDecodeError] = None
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return pd.read_csv(file_path, encoding=encoding, quotechar='"')
            except UnicodeDecodeError as error:
                last_error = error
        raise ValueError("The CSV file could not be decoded with a supported encoding.") from last_error
    return pd.read_excel(file_path)


def create_output_paths(output_dir: str, timestamp: Optional[datetime] = None) -> tuple[str, str]:
    """Return unique CSV and Excel paths for one analysis run."""
    stamp = (timestamp or datetime.now()).strftime("%Y%m%d_%H%M%S_%f")
    stamp = f"{stamp}_{uuid.uuid4().hex[:8]}"
    base = Path(output_dir) / f"sentiment_result_{stamp}"
    return str(base.with_suffix(".csv")), str(base.with_suffix(".xlsx"))


def build_sentiment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create count and percentage rows for the sentiment dashboard/export."""
    total_rows = len(df)
    summary = df["Sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative"], fill_value=0
    ).rename_axis("Sentiment").reset_index(name="Count")
    summary["Percentage"] = (summary["Count"] / total_rows * 100).round(1)
    return summary


# ─── CHARTS ───────────────────────────────────────────────────
def generate_charts(df: pd.DataFrame, output_dir: str) -> tuple[str, str, Optional[str]]:
    colors = {"Positive": "#a6e3a1", "Negative": "#f38ba8", "Neutral": "#89b4fa"}

    # Pie
    counts = df["Sentiment"].value_counts()
    pie_colors = [colors.get(label, "#6c7086") for label in counts.index]

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index, autopct="%1.1f%%",
        colors=pie_colors, startangle=140,
        textprops={"color": "#cdd6f4", "fontsize": 11}, pctdistance=0.75
    )
    for at in autotexts:
        at.set_color("#1e1e2e")
        at.set_fontweight("bold")
    ax.set_title("Sentiment Distribution", fontsize=14, fontweight="bold", color="#cdd6f4", pad=12)
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")
    pie_path = os.path.join(output_dir, "sentiment_pie.png")
    plt.savefig(pie_path, bbox_inches="tight", dpi=150, facecolor=fig.get_facecolor())
    plt.close()

    # Histogram
    n = len(df)
    bins = max(5, n) if n <= 15 else (12 if n <= 50 else min(35, int(np.sqrt(n)) + 5))

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.hist(df["Polarity Score"], bins=bins, color="#89b4fa",
            edgecolor="#1e1e2e", alpha=0.92, linewidth=0.6)
    ax.axvline(0, color="#f38ba8", linestyle="--", linewidth=1.6, label="Neutral line")
    ax.set_title("Polarity Score Distribution", fontsize=13, fontweight="bold", color="#cdd6f4", pad=10)
    ax.set_xlabel("Polarity Score", color="#a6adc8")
    ax.set_ylabel("Frequency", color="#a6adc8")
    ax.tick_params(colors="#a6adc8")
    ax.legend(facecolor="#313244", edgecolor="#45475a", labelcolor="#cdd6f4")
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")
    for spine in ax.spines.values():
        spine.set_color("#45475a")
    hist_path = os.path.join(output_dir, "score_histogram.png")
    plt.savefig(hist_path, bbox_inches="tight", dpi=150, facecolor=fig.get_facecolor())
    plt.close()

    # Topic Frequency Bar Chart
    topic_path = None
    if "Dominant Topic" in df.columns:
        topic_counts = (
            df[~df["Dominant Topic"].isin(["Not enough data", "No text", "general"])]
            ["Dominant Topic"]
            .value_counts()
            .head(8)
        )
        if not topic_counts.empty:
            fig, ax = plt.subplots(figsize=(9, 5.5))
            bars = ax.barh(topic_counts.index.astype(str), topic_counts.values,
                           color="#89b4fa", edgecolor="#1e1e2e", height=0.65)
            ax.set_title("Top Topics by Frequency", fontsize=14, fontweight="bold",
                         color="#cdd6f4", pad=12)
            ax.set_xlabel("Number of Reviews", color="#a6adc8")
            ax.tick_params(colors="#a6adc8")
            ax.invert_yaxis()
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.25, bar.get_y() + bar.get_height()/2,
                        f"{int(width)}", va="center", color="#cdd6f4", fontsize=10)
            fig.patch.set_facecolor("#1e1e2e")
            ax.set_facecolor("#1e1e2e")
            for spine in ax.spines.values():
                spine.set_color("#45475a")
            plt.tight_layout()
            topic_path = os.path.join(output_dir, "topic_frequency.png")
            plt.savefig(topic_path, bbox_inches="tight", dpi=150, facecolor=fig.get_facecolor())
            plt.close()

    return pie_path, hist_path, topic_path


# ─── RESULTS TABLE ────────────────────────────────────────────
def show_results_table(df: pd.DataFrame, output_dir: str, text_col: str) -> None:
    win = tk.Toplevel(root)
    win.title("Analysis Results Preview")
    win.geometry("1100x540")
    win.configure(bg="#1e1e2e")
    win.transient(root)

    tk.Label(win, text="Results Preview (first 150 rows)",
             bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 12, "bold")).pack(pady=(12, 6))

    frame = tk.Frame(win, bg="#1e1e2e")
    frame.pack(fill="both", expand=True, padx=12, pady=4)

    preferred = [text_col, "Sentiment", "Polarity Score", "Dominant Topic"]
    other = [c for c in df.columns if c not in preferred]
    cols = preferred + other

    tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#313244", foreground="#cdd6f4",
                    fieldbackground="#313244", rowheight=26, borderwidth=0, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", background="#45475a", foreground="#cdd6f4",
                    relief="flat", font=("Segoe UI", 9, "bold"))
    style.map("Treeview", background=[("selected", "#89b4fa")])

    for col in cols:
        tree.heading(col, text=col)
        width = 280 if col == text_col else (160 if col == "Dominant Topic" else 100)
        tree.column(col, width=width, anchor="w")

    for _, row in df.head(150).iterrows():
        values = [str(row.get(c, ""))[:120] for c in cols]
        tree.insert("", "end", values=values)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    btn_frame = tk.Frame(win, bg="#1e1e2e")
    btn_frame.pack(pady=10)

    def open_folder():
        if platform.system() == "Windows":
            os.startfile(output_dir)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", output_dir])
        else:
            subprocess.Popen(["xdg-open", output_dir])

    tk.Button(btn_frame, text="📂 Open Output Folder", command=open_folder,
              bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
              relief="flat", padx=14, pady=5, cursor="hand2").pack(side="left", padx=6)
    tk.Button(btn_frame, text="Close", command=win.destroy,
              bg="#45475a", fg="#cdd6f4", font=("Segoe UI", 10),
              relief="flat", padx=14, pady=5, cursor="hand2").pack(side="left", padx=6)


def show_summary_dashboard(summary: pd.DataFrame, output_dir: str) -> None:
    """Show counts and percentages from the completed analysis."""
    win = tk.Toplevel(root)
    win.title("Analysis Summary")
    win.geometry("430x300")
    win.configure(bg="#1e1e2e")
    win.transient(root)

    tk.Label(win, text="Sentiment Summary", bg="#1e1e2e", fg="#cdd6f4",
             font=("Segoe UI", 15, "bold")).pack(pady=(18, 12))
    frame = tk.Frame(win, bg="#313244")
    frame.pack(fill="x", padx=28)
    headers = ("Sentiment", "Count", "Percentage")
    for column, header in enumerate(headers):
        tk.Label(frame, text=header, bg="#45475a", fg="#cdd6f4",
                 font=("Segoe UI", 10, "bold"), width=14).grid(row=0, column=column, padx=1, pady=1)
    for row, values in enumerate(summary.itertuples(index=False), start=1):
        for column, value in enumerate((values.Sentiment, values.Count, f"{values.Percentage:.1f}%")):
            tk.Label(frame, text=str(value), bg="#313244", fg="#cdd6f4",
                     font=("Segoe UI", 10), width=14).grid(row=row, column=column, padx=1, pady=5)
    tk.Label(win, text=f"Output folder: {output_dir}", bg="#1e1e2e", fg="#6c7086",
             font=("Segoe UI", 8), wraplength=380).pack(pady=(16, 8))
    tk.Button(win, text="Close", command=win.destroy, bg="#45475a", fg="#cdd6f4",
              relief="flat", padx=18, pady=5, cursor="hand2").pack()


# ─── MAIN ANALYSIS THREAD ─────────────────────────────────────
def run_analysis_thread(df: pd.DataFrame, selected_col: str, file_path: str) -> None:
    try:
        total_rows = len(df)
        texts = df[selected_col].fillna("").astype(str).tolist()

        sentiments, scores = [], []
        step = max(1, total_rows // 50)

        for i, text in enumerate(texts):
            if cancel_event.is_set():
                root.after(0, finish_cancelled)
                return
            sent, score = engine.analyze(text)
            sentiments.append(sent)
            scores.append(score)
            if i % step == 0 or i == total_rows - 1:
                progress = int(((i + 1) / total_rows) * 100)
                root.after(0, lambda p=progress: progress_bar.configure(value=p))
                root.after(0, lambda p=progress: status_label.config(text=f"Processing: {p}%"))

        df = df.copy()
        df["Sentiment"] = sentiments
        df["Polarity Score"] = scores

        root.after(0, lambda: status_label.config(text="Extracting topics..."))
        if cancel_event.is_set():
            root.after(0, finish_cancelled)
            return
        dominant_topics, topic_list = topic_extractor.fit_transform(texts)
        df["Dominant Topic"] = dominant_topics

        output_dir = os.path.join(os.path.dirname(file_path), "sentiment_output")
        os.makedirs(output_dir, exist_ok=True)
        csv_path, excel_path = create_output_paths(output_dir)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Detailed", index=False)

            summary = build_sentiment_summary(df)
            summary.to_excel(writer, sheet_name="Sentiment Summary", index=False)

            if topic_list is not None:
                topic_df = df[~df["Dominant Topic"].isin(["Not enough data", "No text", "general"])].copy()
                if not topic_df.empty:
                    topic_summary = (
                        topic_df.groupby("Dominant Topic")
                        .agg(
                            Count=("Dominant Topic", "count"),
                            Avg_Score=("Polarity Score", "mean"),
                            Positive=("Sentiment", lambda x: (x == "Positive").sum()),
                            Negative=("Sentiment", lambda x: (x == "Negative").sum()),
                            Neutral=("Sentiment", lambda x: (x == "Neutral").sum())
                        )
                        .reset_index()
                    )
                    topic_summary["Avg_Score"] = topic_summary["Avg_Score"].round(3)
                    topic_summary = topic_summary.sort_values("Count", ascending=False)
                    topic_summary.to_excel(writer, sheet_name="Topics Summary", index=False)

        generate_charts(df, output_dir)

        counts = df["Sentiment"].value_counts().to_dict()

        def finish(tr: int = total_rows, c: dict = counts, od: str = output_dir,
                   d: pd.DataFrame = df, tc: str = selected_col,
                   s: pd.DataFrame = summary) -> None:
            progress_bar.configure(value=100)
            status_label.config(text="Analysis Complete!")
            set_buttons_state("normal")
            cancel_event.clear()
            messagebox.showinfo(
                "✅ Analysis Complete",
                f"Analyzed {tr} rows\n\n"
                f"😊 Positive : {c.get('Positive', 0)}\n"
                f"😐 Neutral  : {c.get('Neutral', 0)}\n"
                f"😠 Negative : {c.get('Negative', 0)}\n\n"
                f"Topics + charts saved.\nFiles in:\n{od}"
            )
            show_summary_dashboard(s, od)
            show_results_table(d, od, tc)

        root.after(0, finish)

    except (OSError, ValueError, KeyError, ImportError, RuntimeError) as error:
        root.after(0, lambda e=error: finish_error(e))


def finish_cancelled() -> None:
    """Reset the interface after a cooperative cancellation."""
    cancel_event.clear()
    progress_bar.configure(value=0)
    status_label.config(text="Analysis cancelled")
    set_buttons_state("normal")


def finish_error(error: BaseException) -> None:
    """Display a handled analysis error and restore the controls."""
    cancel_event.clear()
    messagebox.showerror("Analysis Error", str(error))
    set_buttons_state("normal")
    status_label.config(text="Error occurred")


def set_buttons_state(state: str) -> None:
    analyze_text_btn.config(state=state)
    analyze_file_btn.config(state=state)
    cancel_btn.config(state="normal" if state == "disabled" else "disabled")


def cancel_analysis() -> None:
    """Request cancellation; the worker stops at its next safe checkpoint."""
    cancel_event.set()
    status_label.config(text="Cancelling...")
    cancel_btn.config(state="disabled")


# ─── FILE ANALYSIS ────────────────────────────────────────────
def analyze_csv() -> None:
    file_path = filedialog.askopenfilename(
        title="Select CSV or Excel File",
        filetypes=[("CSV / Excel", "*.csv *.xlsx *.xls")]
    )
    if not file_path:
        return

    try:
        df = load_input_file(file_path)

        if df.empty:
            messagebox.showwarning("Empty File", "The selected file has no data.")
            return

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if len(df) >= 10000 or file_size_mb >= 10:
            proceed = messagebox.askyesno(
                "Large File",
                f"This file has {len(df):,} rows and is {file_size_mb:.1f} MB.\n\n"
                "Analysis may take a while. Continue?"
            )
            if not proceed:
                return

        columns = list(df.columns)

        col_window = tk.Toplevel(root)
        col_window.title("Select Text Column")
        col_window.geometry("340x180")
        col_window.configure(bg="#1e1e2e")
        col_window.transient(root)
        col_window.grab_set()
        col_window.resizable(False, False)

        tk.Label(col_window, text="Which column contains the text?",
                 bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 11)).pack(pady=(20, 10))

        col_var = tk.StringVar(value=columns[0])
        col_menu = ttk.Combobox(col_window, textvariable=col_var, values=columns,
                                state="readonly", font=("Segoe UI", 10), width=34)
        col_menu.pack(pady=4)

        def start_analysis():
            selected_col = col_var.get()
            col_window.destroy()

            non_empty = df[selected_col].fillna("").astype(str).str.strip().ne("").sum()
            if non_empty == 0:
                messagebox.showwarning("Empty Column", f"Column '{selected_col}' has no usable text.")
                return

            set_buttons_state("disabled")
            cancel_event.clear()
            progress_bar.configure(value=0)
            status_label.config(text="Starting analysis...")

            thread = threading.Thread(
                target=run_analysis_thread,
                args=(df, selected_col, file_path),
                daemon=True
            )
            thread.start()

        tk.Button(col_window, text="Analyze Now", command=start_analysis,
                  bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=18, pady=7, cursor="hand2").pack(pady=18)

    except (OSError, UnicodeDecodeError, ValueError, KeyError, ImportError) as error:
        messagebox.showerror("File Error", str(error))


# ─── SINGLE TEXT ──────────────────────────────────────────────
def analyze_text() -> None:
    text = text_input.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Empty", "Please enter some text first.")
        return
    sentiment, score = engine.analyze(text)
    emoji = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}[sentiment]
    result_label.config(text=f"{emoji}  {sentiment}   |   Score: {score}")


def main() -> None:
    """Create and run the desktop application."""
    global root, analyze_text_btn, analyze_file_btn, cancel_btn
    global progress_bar, status_label, text_input, result_label

    root = tk.Tk()
    root.title("Sentiment Analyzer Pro")
    root.geometry("540x620")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Horizontal.TProgressbar",
                    troughcolor="#313244", background="#89b4fa", thickness=14, borderwidth=0)

    tk.Label(root, text="💬  Sentiment Analyzer Pro",
             font=("Segoe UI", 18, "bold"), bg="#1e1e2e", fg="#cdd6f4").pack(pady=(18, 4))
    tk.Label(root, text="Sentiment + Topic Extraction  •  Local & Private",
             font=("Segoe UI", 9), bg="#1e1e2e", fg="#6c7086").pack()

    tk.Label(root, text="Type or paste text below:",
             bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 10)).pack(pady=(16, 4))

    text_input = tk.Text(root, height=5, width=60, font=("Segoe UI", 11),
                         bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                         relief="flat", padx=10, pady=8, wrap="word")
    text_input.pack(pady=4)

    analyze_text_btn = tk.Button(root, text="Analyze Text", command=analyze_text,
                                 bg="#89b4fa", fg="#1e1e2e", font=("Segoe UI", 11, "bold"),
                                 relief="flat", padx=22, pady=6, cursor="hand2")
    analyze_text_btn.pack(pady=8)

    result_label = tk.Label(root, text="Result will appear here",
                            font=("Segoe UI", 13), bg="#1e1e2e", fg="#a6e3a1")
    result_label.pack(pady=6)

    tk.Frame(root, height=1, bg="#45475a").pack(fill="x", padx=40, pady=12)

    tk.Label(root, text="Bulk Analysis (CSV / Excel)",
             bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 10)).pack()

    analyze_file_btn = tk.Button(root, text="📂  Upload CSV / Excel File", command=analyze_csv,
                                 bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 11, "bold"),
                                 relief="flat", padx=20, pady=7, cursor="hand2")
    analyze_file_btn.pack(pady=8)

    cancel_btn = tk.Button(root, text="Cancel Analysis", command=cancel_analysis,
                           state="disabled", bg="#f38ba8", fg="#1e1e2e",
                           font=("Segoe UI", 10, "bold"), relief="flat", padx=18, pady=5,
                           cursor="hand2")
    cancel_btn.pack(pady=(0, 6))

    status_label = tk.Label(root, text="Idle", bg="#1e1e2e", fg="#6c7086", font=("Segoe UI", 9))
    status_label.pack(pady=(8, 2))

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=340, mode="determinate",
                                   style="Custom.Horizontal.TProgressbar")
    progress_bar.pack(pady=4)

    tk.Label(root, text="Powered by VADER + Topic Modeling  •  Local & Private",
             bg="#1e1e2e", fg="#585b70", font=("Segoe UI", 8)).pack(side="bottom", pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()