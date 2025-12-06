# YouTube AI Scraping Agent

This project is an artificial intelligence agent that extracts the artist name from a given YouTube video URL, uses LLM to find their first album, retrieves song lyrics from Genius, and performs token analysis to generate a hash.

## Author

Tufan Özkan

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/tufanozkan/youtube_ai.git
   cd youtube_ai
   ```

2. Install the required libraries:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file: Create a file named `.env` in the main directory and add your API keys:
   ```
   APIFY_API_TOKEN=your_apify_token
   OPENROUTER_API_KEY=your_openrouter_key
   ```

## Usage

The script runs in two different modes: JSON output and Hash output.

### 1. JSON Mode (Step 5 Output)

Prints song analysis and metrics in JSON format.

```bash
python3 Cem_Dilmegani_YouTube_AI.py "https://www.youtube.com/watch?v=rSaC-YbSDpo" json
```

### 2. Hash Mode (Step 8 Output)

Prints the MD5 hash of the embedding vector.

```bash
python3 Cem_Dilmegani_YouTube_AI.py "https://www.youtube.com/watch?v=rSaC-YbSDpo" hash
```

---

## Security Note - `.gitignore`

⚠️ **CRITICAL STEP!** If you push API keys to GitHub, you will be disqualified.

Make sure your project folder has a `.gitignore` file and contains the following:

```text
.env
__pycache__/
.DS_Store
venv/
```

---

**Last Updated**: December 6, 2025
