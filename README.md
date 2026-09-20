# 💬 Sentiment Analyzer Pro

A Python desktop application that analyzes text sentiment using a modern NLP pipeline. It classifies reviews as **Positive**, **Negative**, or **Neutral** and also extracts the dominant topic behind each review.

Built for local analysis of product feedback, customer reviews, surveys, and support tickets without sending data to a cloud service.

---

## 🖼️ What It Does

- **Single Text Analysis** — Paste any sentence or paragraph and get instant sentiment output
- **Bulk CSV / Excel Analysis** — Analyze large review files in one click
- **Column Selection** — Choose the exact text column from uploaded data files
- **Sentiment Scoring** — Uses VADER to score text on a scale from -1.0 to +1.0
- **Topic Extraction** — Identifies the main topic behind each review using lightweight topic modeling
- **Dashboard & Charts** — Generates summary tables, pie charts, histograms, and topic charts
- **Output Export** — Saves results to CSV and Excel files in a timestamped `sentiment_output` folder
- **Desktop GUI** — Runs as a local Tkinter app with progress updates and cancel support

---

## 📸 Sample Output

| review | Sentiment | Polarity Score | Dominant Topic |
|---|---|---:|---|
| This product is amazing! | Positive | 0.636 | product quality |
| Worst purchase ever | Negative | -0.624 | product defects |
| The delivery was okay | Neutral | 0.0 | logistics |
| I love it so much | Positive | 0.669 | customer satisfaction |
| Terrible quality never buying again | Negative | -0.744 | quality issues |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.10+ | Core language |
| NLTK VADER | Sentiment scoring and lexical analysis |
| scikit-learn | TF-IDF + topic extraction with NMF |
| Pandas | CSV/Excel loading and result management |
| Matplotlib | PIE, histogram, and topic charts |
| Tkinter | Desktop GUI |
| OpenPyXL | Excel export support |
| NumPy | Statistical and chart-related processing |

---

## 🚀 How to Run

### 1. Clone the repo
```bash
git clone https://github.com/Anuj230977/sentiment-analyzer.git
cd sentiment-analyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download VADER data (one-time only)
```bash
python -c "import nltk; nltk.download('vader_lexicon')"
```

### 4. Run the app
```bash
python analyzer.py
```

---

## � Download the Windows EXE

The latest compiled Windows build is published in the GitHub Releases section for direct download:

https://github.com/Anuj230977/sentiment-analyzer/releases

Once a new version is published, the `.exe` appears under the release assets and can be downloaded directly without cloning the repository.

To build the executable locally on Windows:

```powershell
cd "D:\MY PROJECTS\sentiment-analyzer"
py -3 -m PyInstaller --onefile --windowed analyzer.py
```

The generated program will appear in the `dist` folder. After that, you upload the `.exe` to a GitHub Release under "Assets" so users can download it directly.

---

## �📂 Project Structure

```text
sentiment-analyzer/
├── analyzer.py                 # Main desktop application
├── README.md                  # Project overview and usage guide
├── CODE_EXPLANATION.md        # Detailed technical walkthrough
├── requirements.txt           # Python dependencies
├── SentimentAnalyzerPro.spec  # PyInstaller build spec
├── sample_reviews_v2.csv      # Sample dataset for bulk analysis
├── test_reviews.csv           # Small test dataset
├── LICENSE                    # MIT license
├── .gitignore                 # Ignores output and temporary files
├── sentiment_output/          # Auto-generated results folder
└── .git/                      # Git metadata
```

---

## 💡 Use Cases

- **E-commerce** — Review sentiment analysis for product feedback
- **Retail / Hospitality** — Customer satisfaction trend analysis
- **Support Teams** — Complaint extraction from email or ticket text
- **Students** — NLP project for academic and portfolio use
- **Product Teams** — Monitor recurring themes in user reviews

---

## 📊 How Sentiment Scoring Works

The project uses **VADER**, which calculates a compound score between **-1.0 and +1.0** for the text:

| Score Range | Sentiment |
|---|---|
| > 0.05 | 😊 Positive |
| -0.05 to 0.05 | 😐 Neutral |
| < -0.05 | 😠 Negative |

Short phrases containing neutral words like *"okay"*, *"fine"*, *"average"*, and *"alright"* are intentionally treated as **Neutral** when the sentence is short; this makes everyday review wording behave more naturally.

---

## 📦 Output Files

When a file is analyzed, the app creates a timestamped output folder named `sentiment_output` and saves:

- CSV file with review text, sentiment, polarity score, and dominant topic
- Excel workbook with summary sheets
- Pie chart image
- Histogram image
- Topic-frequency chart image

---

## 👤 Author

**Anuj Jadhav**
- 🎓 BBA-CA Graduate | Full Stack Developer
- 📧 anuj1230567@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/anujjadhav)
- 🐙 [GitHub](https://github.com/Anuj230977)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
