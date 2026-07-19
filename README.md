# 💬 Sentiment Analyzer

A Python desktop tool that analyzes text as **Positive**, **Negative**, or
**Neutral** using Natural Language Processing (NLP).

Built for businesses and individuals who want to understand how people feel about their products, services, or content.

---

## 🖼️ What It Does

- **Single Text Analysis** - Type or paste any text and get instant sentiment feedback
- **Bulk CSV / Excel Analysis** - Upload a file with hundreds of reviews and analyze all rows at once
- **Visual Report** - Generates a pie chart showing the sentiment distribution
- **Output File** - Saves results as a clean CSV with Sentiment + Polarity Score columns
- **Simple GUI** - No coding needed, just click and analyze
- **Smart Text Column Defaults** - Auto-selects common review and social export columns such as `review_text`, `tweet_text`, and `Tweet Text`

---

## 📸 Sample Output

| review | Sentiment | Polarity Score |
|---|---|---|
| This product is amazing! | Positive | 0.75 |
| Worst purchase ever | Negative | -1.0 |
| The delivery was okay | Neutral | 0.0 |
| I love it so much | Positive | 0.35 |
| Terrible quality never buying again | Negative | -1.0 |

For bulk uploads, the app prioritizes `review_text`, `tweet_text`, and
`full_text` before generic aliases such as `review`, `comment`, `comments`,
`content`, `message`, and `text`. Normalization also accepts spaces,
underscores, hyphens, and letter-case differences. Xquik exports using the
canonical `text` field work directly, while the additional aliases support
transformed social datasets. You can still choose any column manually.

Xquik is an independent third-party service. Not affiliated with X Corp.
"Twitter" and "X" are trademarks of X Corp.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.12 | Core language |
| NLTK VADER | NLP sentiment analysis |
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
pip install nltk pandas matplotlib openpyxl
```

### 3. Download NLTK data (one-time only)
```bash
python -c "import nltk; nltk.download('vader_lexicon')"
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

- **E-commerce businesses** - Analyze customer reviews in bulk
- **Restaurants / Hotels** - Understand feedback from review exports
- **HR Teams** - Analyze employee survey responses
- **Students** - NLP project for data analytics coursework
- **Content Creators** - Analyze comment sections from YouTube/Instagram

---

## 📊 How Sentiment Scoring Works

VADER assigns a **compound score** between **-1.0 and +1.0** to every piece of
text:

| Score Range | Sentiment |
|---|---|
| >= 0.05 | 😊 Positive |
| > -0.05 and < 0.05 | 😐 Neutral |
| <= -0.05 | 😠 Negative |

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
