import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import os
from datetime import datetime

# ─── CORE FUNCTION ───────────────────────────────────────────────
NEUTRAL_OVERRIDES = {"okay", "ok", "fine", "alright", "average", "moderate"}

def get_sentiment(text):
    if not isinstance(text, str) or text.strip() == "":
        return "Neutral", 0.0
    words = set(text.strip().lower().split())
    if words & NEUTRAL_OVERRIDES and len(text.split()) <= 6:
        return "Neutral", 0.0
    analysis = TextBlob(str(text))
    polarity = analysis.sentiment.polarity
    if polarity > 0.2:
        return "Positive", round(polarity, 3)
    elif polarity < -0.2:
        return "Negative", round(polarity, 3)
    else:
        return "Neutral", round(polarity, 3)

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

# ─── ANALYZE CSV ─────────────────────────────────────────────────
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

        # Let user pick the text column
        columns = list(df.columns)
        col_window = tk.Toplevel(root)
        col_window.title("Select Text Column")
        col_window.geometry("300x120")
        tk.Label(col_window, text="Which column has the text?").pack(pady=10)
        col_var = tk.StringVar(value=columns[0])
        col_menu = ttk.Combobox(col_window, textvariable=col_var, values=columns, state="readonly")
        col_menu.pack()

        def confirm_col():
            selected_col = col_var.get()
            col_window.destroy()

            df["Sentiment"], df["Polarity Score"] = zip(*df[selected_col].map(get_sentiment))

            # Save output
            output_dir = os.path.join(os.path.dirname(file_path), "sentiment_output")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(output_dir, f"sentiment_result_{timestamp}.csv")
            df.to_csv(out_path, index=False, encoding="utf-8-sig")

            chart_path = generate_chart(df, output_dir)

            counts = df["Sentiment"].value_counts().to_dict()
            messagebox.showinfo("✅ Done!", (
                f"Analyzed {len(df)} rows\n\n"
                f"😊 Positive: {counts.get('Positive', 0)}\n"
                f"😐 Neutral:  {counts.get('Neutral', 0)}\n"
                f"😠 Negative: {counts.get('Negative', 0)}\n\n"
                f"Results saved to:\n{out_path}\n\n"
                f"Chart saved to:\n{chart_path}"
            ))

        tk.Button(col_window, text="Analyze", command=confirm_col, bg="#4CAF50", fg="white").pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ─── ANALYZE SINGLE TEXT ─────────────────────────────────────────
def analyze_text():
    text = text_input.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Empty", "Please enter some text first.")
        return
    sentiment, score = get_sentiment(text)
    emoji = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}[sentiment]
    result_label.config(text=f"{emoji} {sentiment}  |  Score: {score}")

# ─── GUI ─────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Sentiment Analyzer — by Anuj")
root.geometry("500x420")
root.resizable(False, False)
root.configure(bg="#1e1e2e")

tk.Label(root, text="💬 Sentiment Analyzer", font=("Arial", 16, "bold"),
         bg="#1e1e2e", fg="#cdd6f4").pack(pady=15)

tk.Label(root, text="Type or paste text below:", bg="#1e1e2e", fg="#a6adc8").pack()
text_input = tk.Text(root, height=6, width=55, font=("Arial", 11),
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

tk.Label(root, text="Or analyze a whole CSV / Excel file:", bg="#1e1e2e", fg="#a6adc8").pack(pady=5)
tk.Button(root, text="📂 Upload CSV / Excel File", command=analyze_csv,
          bg="#a6e3a1", fg="#1e1e2e", font=("Arial", 11, "bold"),
          relief="flat", padx=20, pady=6).pack(pady=5)

tk.Label(root, text="Built with Python + TextBlob + Tkinter",
         bg="#1e1e2e", fg="#585b70", font=("Arial", 9)).pack(side="bottom", pady=8)

root.mainloop()