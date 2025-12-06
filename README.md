# YouTube AI - Song Information Analysis Tool

An AI-powered Python application that automatically extracts artist information from YouTube videos and retrieves song details using the Genius API.

## 🎯 Features

- **YouTube Video Analysis**: Extract title and description information from YouTube videos
- **Artist Information Extraction**: Automatically identify artist names using OpenAI/OpenRouter API
- **Song Details**: Retrieve song lyrics and metadata from Genius.com API
- **Smart Token Management**: Token calculation and management for OpenRouter API usage
- **Error Handling**: Comprehensive error management and validation

## 📋 Requirements

- Python 3.8+
- Apify API Token
- OpenRouter API Key
- Internet Connection

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tufanozkan/youtube_ai.git
cd youtube_ai
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

### 4. Create .env File

Create a `.env` file in the project root directory and add your API keys:

```env
APIFY_API_TOKEN=your_apify_token_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

**How to Get API Keys:**

- **Apify Token**: From [Apify Dashboard](https://console.apify.com)
- **OpenRouter API Key**: From [OpenRouter Platform](https://openrouter.ai)

## 💻 Usage

### Running from Command Line

```bash
python Cem_Dilmegani_YouTube_AI.py --url "YouTube Video URL"
```

### Example Usage

```bash
python Cem_Dilmegani_YouTube_AI.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## 📦 Dependencies

| Package        | Version | Description                  |
| -------------- | ------- | ---------------------------- |
| apify-client   | Latest  | Apify API client             |
| openai         | Latest  | OpenAI/OpenRouter API client |
| tiktoken       | Latest  | OpenAI token counter         |
| python-dotenv  | Latest  | .env file management         |
| requests       | Latest  | HTTP requests                |
| beautifulsoup4 | Latest  | HTML/XML parsing             |

## 🔄 Workflow

1. **YouTube Analysis**: Extract title and description information from YouTube videos using Apify
2. **AI Processing**: Identify artist names using OpenRouter API
3. **Song Search**: Retrieve song information using Genius API
4. **Results**: Return artist and song information

## ⚙️ Configuration

### Environment Variables

- `APIFY_API_TOKEN`: Required for Apify API access
- `OPENROUTER_API_KEY`: Required for OpenRouter API access

## 🐛 Troubleshooting

### "API keys missing" Error

Make sure the `.env` file is in the project root directory and contains all required API keys.

### Rate Limiting

The Genius API applies rate limiting. Add delays between multiple requests.

## 📝 License

This project is open source. See the LICENSE file for details.

## 👨‍💻 Developer

- **Tufan Özkan** - [GitHub](https://github.com/tufanozkan)

## 🙏 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Contact & Support

For questions or suggestions, please open a [GitHub Issue](https://github.com/tufanozkan/youtube_ai/issues).

---

**Last Updated**: December 6, 2025
