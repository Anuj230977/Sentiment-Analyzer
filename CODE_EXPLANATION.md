# 🧠 Code Explanation — Sentiment Analyzer

A complete walkthrough of how `analyzer.py` works — every function, every logic decision, explained simply and clearly.

---

## 📦 Imports — What Each Library Does

```python
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import os
from datetime import datetime
```

| Import | Why It's Used |
|---|---|
| `tkinter` | Builds the desktop GUI window, buttons, labels |
| `filedialog` | Opens the file picker popup when user uploads a CSV |
| `messagebox` | Shows popups for results, warnings, and errors |
| `ttk` | Provides the styled dropdown (Combobox) for column selection |
| `pandas` | Reads CSV/Excel files and processes rows as a table |
| `TextBlob` | The NLP engine — analyzes sentiment of text |
| `matplotlib` | Draws and saves the pie chart |
| `os` | Creates output folders, builds file paths |
| `datetime` | Adds a timestamp to output filenames so they never overwrite each other |

---

## 🔧 SECTION 1 — The Core Sentiment Function

```python
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
```

### What it does:
This is the brain of the entire application. Every piece of text — whether typed manually or from a CSV row — passes through this function and comes out with a label and a score.

### Step-by-step logic:

**Step 1 — Safety check**
```python
if not isinstance(text, str) or text.strip() == "":
    return "Neutral", 0.0
```
If the input is empty, None, or not a string (e.g. a blank CSV cell), we return Neutral with score 0. This prevents crashes when processing messy data.

**Step 2 — Neutral word override**
```python
NEUTRAL_OVERRIDES = {"okay", "ok", "fine", "alright", "average", "moderate"}
words = set(text.strip().lower().split())
if words & NEUTRAL_OVERRIDES and len(text.split()) <= 6:
    return "Neutral", 0.0
```
TextBlob has a known limitation — it scores words like "okay" and "fine" as slightly positive (score ~0.5) because they appear in positive contexts in its training data. We fix this manually.

- `text.strip().lower().split()` → converts text to a set of lowercase words
- `words & NEUTRAL_OVERRIDES` → checks if ANY override word exists in the sentence
- `len(text.split()) <= 6` → only applies to SHORT phrases (≤6 words), so longer sentences like *"This is okay but I love the design"* still go through TextBlob normally

**Step 3 — TextBlob analysis**
```python
analysis = TextBlob(str(text))
polarity = analysis.sentiment.polarity
```
TextBlob reads the text and returns a polarity score between **-1.0** (most negative) and **+1.0** (most positive).

**Step 4 — Classify the score**
```python
if polarity > 0.2:
    return "Positive", round(polarity, 3)
elif polarity < -0.2:
    return "Negative", round(polarity, 3)
else:
    return "Neutral", round(polarity, 3)
```
We use **±0.2 as the threshold** (not ±0.1) to reduce false positives. Scores in the -0.2 to +0.2 range are classified as Neutral. `round(polarity, 3)` keeps the score clean (3 decimal places).

---

## 📊 SECTION 2 — Chart Generator

```python
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
```

### What it does:
Takes the analyzed DataFrame and creates a colored pie chart saved as a PNG file.

### Logic breakdown:

**Counting sentiments**
```python
counts = df["Sentiment"].value_counts()
```
Counts how many Positive, Negative, and Neutral rows exist. For example: `Positive: 4, Negative: 3, Neutral: 2`

**Color mapping**
```python
colors = {"Positive": "#4CAF50", "Negative": "#F44336", "Neutral": "#2196F3"}
pie_colors = [colors.get(label, "#999") for label in counts.index]
```
Each sentiment gets a meaningful color — green for positive, red for negative, blue for neutral. The list comprehension maps each label to its color in the correct order.

**Drawing the chart**
```python
ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=140)
```
- `counts.values` → the numbers (slice sizes)
- `labels=counts.index` → the labels (Positive, Negative, Neutral)
- `autopct="%1.1f%%"` → shows percentage on each slice (e.g. 44.4%)
- `startangle=140` → rotates the chart so it starts at a clean angle

**Saving**
```python
plt.savefig(chart_path, bbox_inches="tight", dpi=150)
plt.close()
```
`bbox_inches="tight"` removes extra whitespace around the chart. `dpi=150` gives a crisp, high-resolution image. `plt.close()` frees memory after saving.

---

## 📂 SECTION 3 — CSV / Excel Analyzer

```python
def analyze_csv():
    file_path = filedialog.askopenfilename(...)
    if not file_path:
        return
    ...
```

### What it does:
Handles the full pipeline for bulk file analysis — file selection, column picking, processing, saving output, and showing results.

### Logic breakdown:

**Opening the file**
```python
if file_path.endswith(".csv"):
    df = pd.read_csv(file_path, encoding="utf-8-sig")
else:
    df = pd.read_excel(file_path)
```
Detects whether the file is CSV or Excel and reads it accordingly. `encoding='utf-8-sig'` handles special characters and the BOM (Byte Order Mark) that Excel sometimes adds to CSV files — without this, the first column name can appear garbled.

**Column selection popup**
```python
col_menu = ttk.Combobox(col_window, textvariable=col_var, values=columns, state="readonly")
```
Instead of assuming which column has the text, we show the user a dropdown with all column names. This makes the tool work for ANY CSV structure — whether the column is called "review", "comment", "feedback", or anything else.

**Running sentiment on every row**
```python
df["Sentiment"], df["Polarity Score"] = zip(*df[selected_col].map(get_sentiment))
```
This is the most powerful line in the file. Here's what it does:
- `df[selected_col].map(get_sentiment)` → applies `get_sentiment()` to every row in the chosen column
- Each call returns a tuple: `("Positive", 0.75)` for example
- `zip(*...)` → unzips the list of tuples into two separate lists
- These get assigned as two new columns: `Sentiment` and `Polarity Score`

All of this happens in a single line instead of a slow loop.

**Saving output with timestamp**
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = os.path.join(output_dir, f"sentiment_result_{timestamp}.csv")
```
Every output file gets a unique timestamp in its name (e.g. `sentiment_result_20250521_143022.csv`). This means running the tool multiple times never overwrites previous results.

**Showing the summary popup**
```python
messagebox.showinfo("✅ Done!", (
    f"Analyzed {len(df)} rows\n\n"
    f"😊 Positive: {counts.get('Positive', 0)}\n"
    ...
))
```
Uses `.get('Positive', 0)` instead of direct dictionary access — this safely handles the case where a category has 0 rows (so it won't throw a KeyError if all reviews are positive and there are no negatives).

---

## ✍️ SECTION 4 — Single Text Analyzer

```python
def analyze_text():
    text = text_input.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Empty", "Please enter some text first.")
        return
    sentiment, score = get_sentiment(text)
    emoji = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}[sentiment]
    result_label.config(text=f"{emoji} {sentiment}  |  Score: {score}")
```

### What it does:
Reads whatever the user typed in the text box, runs it through `get_sentiment()`, and updates the result label on screen.

### Logic breakdown:

**Reading text from the box**
```python
text = text_input.get("1.0", tk.END).strip()
```
In Tkinter, `Text` widgets use `"1.0"` (line 1, character 0) as the starting position and `tk.END` as the end. `.strip()` removes any trailing newlines that Tkinter automatically adds.

**Displaying the result**
```python
emoji = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}[sentiment]
result_label.config(text=f"{emoji} {sentiment}  |  Score: {score}")
```
Maps the sentiment string to a matching emoji using a dictionary, then updates the label's text live — no need to reload the window.

---

## 🎨 SECTION 5 — The GUI

```python
root = tk.Tk()
root.title("Sentiment Analyzer — by Anuj")
root.geometry("500x420")
root.resizable(False, False)
root.configure(bg="#1e1e2e")
```

### Design decisions:
- **Fixed size** (`resizable(False, False)`) — prevents layout breaking on resize
- **Dark theme** (`#1e1e2e`) — professional look inspired by Catppuccin Mocha theme
- **Two sections** — top half for single text input, bottom half for CSV upload, separated by a divider line

### Key widgets:

| Widget | Purpose |
|---|---|
| `tk.Text` | Multi-line text input box for pasting reviews |
| `tk.Button` (Analyze Text) | Triggers `analyze_text()` |
| `tk.Label` (result_label) | Shows the sentiment result live |
| `tk.Button` (Upload CSV) | Triggers `analyze_csv()` |

### Color palette used:

| Color | Hex | Used For |
|---|---|---|
| Dark background | `#1e1e2e` | Window background |
| Text input bg | `#313244` | Input box |
| Main text | `#cdd6f4` | Labels and input text |
| Subtle text | `#a6adc8` | Secondary labels |
| Blue button | `#89b4fa` | Analyze Text button |
| Green button | `#a6e3a1` | Upload CSV button |
| Result text | `#a6e3a1` | Sentiment result label |
| Divider | `#45475a` | Separator line |

---

## 🔄 Full Data Flow Diagram

```
User Input (text or CSV)
        │
        ▼
 get_sentiment(text)
        │
        ├── Empty/None? ──────────────► Return Neutral, 0.0
        │
        ├── Contains neutral word
        │   in short phrase? ─────────► Return Neutral, 0.0
        │
        └── TextBlob Analysis
                │
                ├── polarity > 0.2 ──► Return Positive, score
                ├── polarity < -0.2 ─► Return Negative, score
                └── else ────────────► Return Neutral, score
                        │
                        ▼
              [For CSV] Add columns to DataFrame
                        │
                        ▼
              Save output CSV + Generate PNG chart
                        │
                        ▼
              Show summary popup to user
```

---

## 💡 Key Concepts Learned in This Project

| Concept | Where It's Used |
|---|---|
| NLP with TextBlob | `get_sentiment()` |
| DataFrame column mapping with `.map()` | Bulk CSV analysis |
| Tuple unpacking with `zip(*...)` | Splitting sentiment results into two columns |
| Tkinter GUI building | Entire GUI section |
| Matplotlib pie charts | `generate_chart()` |
| File I/O with Pandas | Reading CSV/Excel, writing output |
| Datetime timestamping | Unique output filenames |
| Dictionary-based emoji mapping | Result display |
| Set intersection (`&`) for word matching | Neutral override logic |

---

*Built by Anuj Jadhav — TY BBA-CA Student*
*Part of the Freelance Portfolio Series — Project 2 of 3*
