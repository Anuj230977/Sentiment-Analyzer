# 💬 Sentiment Analyzer

A Python desktop tool that analyzes the sentiment of text — whether it's **Positive**, **Negative**, or **Neutral** — using Natural Language Processing (NLP).

Built for businesses and individuals who want to understand how people feel about their products, services, or content.

---

## 🖼️ What It Does

- **Single Text Analysis** — Type or paste any text and get instant sentiment feedback
- **Bulk CSV / Excel Analysis** — Upload a file with hundreds of reviews and analyze all rows at once
- **Visual Report** — Generates a pie chart showing the sentiment distribution
- **Output File** — Saves results as a clean CSV with Sentiment + Polarity Score columns
- **Simple GUI** — No coding needed, just click and analyze

---

## 📸 Sample Output

| review | Sentiment | Polarity Score |
|---|---|---|
| This product is amazing! | Positive | 0.75 |
| Worst purchase ever | Negative | -1.0 |
| The delivery was okay | Neutral | 0.0 |
| I love it so much | Positive | 0.35 |
| Terrible quality never buying again | Negative | -1.0 |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.12 | Core language |
| TextBlob | NLP sentiment analysis |
| NLTK | Language processing backend |
| Pandas | CSV/Excel reading and processing |
| Matplotlib | Pie chart generation |
| Tkinter | Desktop GUI |
| OpenPyXL | Excel file support |

---

## 🚀 How to Run

### 1. Clone the repo
```bash
git clone https://github.com/Anuj230977/sentiment-analyzer.git
cd sentiment-analyzer
```

### 2. Install dependencies
```bash
pip install textblob nltk pandas matplotlib openpyxl
```

### 3. Download NLTK data (one-time only)
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('punkt_tab')"
```

### 4. Run the app
```bash
python analyzer.py
```

---

## 📂 Project Structure

```
sentiment-analyzer/
├── analyzer.py          # Main application file
├── README.md            # Project documentation
├── CODE_EXPLANATION.md  # Detailed code walkthrough
└── .gitignore           # Ignores output folders and temp files
```

---

## 💡 Use Cases

- **E-commerce businesses** — Analyze customer reviews in bulk
- **Restaurants / Hotels** — Understand feedback from review exports
- **HR Teams** — Analyze employee survey responses
- **Students** — NLP project for data analytics coursework
- **Content Creators** — Analyze comment sections from YouTube/Instagram

---

## 📊 How Sentiment Scoring Works

TextBlob assigns a **polarity score** between **-1.0 and +1.0** to every piece of text:

| Score Range | Sentiment |
|---|---|
| > 0.2 | 😊 Positive |
| -0.2 to 0.2 | 😐 Neutral |
| < -0.2 | 😠 Negative |

Common neutral words like *"okay", "fine", "alright"* in short phrases are automatically classified as Neutral regardless of score.

---

## 👤 Author

**Anuj Jadhav**
- 🎓 TY BBA-CA Student
- 📧 anuj1230567@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/anujjadhav)
- 🐙 [GitHub](https://github.com/Anuj230977)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
