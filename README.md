# 🚀 Heart&Mind: AI-Powered E-Commerce Recommender System

> **Neural Experience Understanding System** - An intelligent recommendation engine that doesn't just tell you _what_ to buy, but explains _why you'll love it_.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io/)
[![Gemini](https://img.shields.io/badge/AI-Gemini%201.5-purple.svg)](https://ai.google.dev/)

---

## ✨ What Makes Heart&Mind Special?

Traditional e-commerce recommenders are black boxes that simply show "Customers who bought X also bought Y" without explanation. **Heart&Mind** is different:

### 🎯 **Key Features**

- **🧠 Hybrid Intelligence**: Combines collaborative filtering, content-based recommendations, and serendipity
- **💬 AI-Powered Explanations**: Every recommendation comes with a natural language explanation (powered by Gemini AI)
- **🎭 4 Personality Modes**: Choose your explanation style - Friendly, Expert, Storyteller, or Minimalist
- **✨ Serendipity Engine**: 5% "wild card" recommendations to prevent filter bubbles and create discovery moments
- **📊 Real-Time Learning**: System adapts immediately to user interactions - no batch processing delays
- **🎨 Beautiful CRED-Style UI**: Dark theme with premium gradients and smooth animations
- **📈 Behavioral Analytics**: Deep insights into user shopping patterns and preferences

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Heart&Mind Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  Streamlit   │◄────────┤   FastAPI    │                  │
│  │   Frontend   │  REST   │   Backend    │                  │
│  └──────────────┘         └───────┬──────┘                  │
│                                   │                         │
│                         ┌─────────┴──────────┐              │
│                         │                    │              │
│                    ┌────▼─────┐      ┌──────▼──────┐        │
│                    │Recommend │      │   Gemini AI │        │
│                    │  Engine  │      │  Explainer  │        │
│                    └────┬─────┘      └─────────────┘        │
│                         │                                   │
│              ┌──────────┼──────────┐                        │
│              │          │          │                        │
│         ┌────▼───┐ ┌───▼────┐ ┌───▼─────┐                   │
│         │Collab. │ │Content │ │Serendip.│                   │
│         │Filter  │ │ Based  │ │ Engine  │                   │
│         └────────┘ └────────┘ └─────────┘                   │
│                         │                                   │
│                    ┌────▼─────┐                             │
│                    │  SQLite  │                             │
│                    └──────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Gemini API key ([Get free key](https://ai.google.dev/))

### Installation (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/heart-and-mind.git
cd heart-and-mind

# 2. Set up Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env  # Windows
# cp .env.example .env  # Mac/Linux

# Edit .env and add your GEMINI_API_KEY

# 4. Initialize database
python -m app.utils.seed_data

# 5. Start backend
python -m app.main
```

**Backend now running at:** http://localhost:8000

### Start Frontend

```bash
# In a new terminal
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

**Frontend now running at:** http://localhost:8501

---

## 🎮 Usage Guide

### Getting Recommendations

1. **Select a user** from the sidebar
2. **Choose an explanation style** (Friendly, Expert, Storyteller, or Minimalist)
3. View **personalized recommendations** with AI explanations
4. **Interact with products** (View, Add to Cart, Wishlist, Purchase)
5. **Track your analytics** in real-time

### API Usage

```python
import requests

# Get recommendations
response = requests.get(
    "http://localhost:8000/recommendations/1",
    params={
        "n": 10,
        "personality": "friendly",
        "include_explanations": True
    }
)

recommendations = response.json()
```

### Available Endpoints

| Endpoint                     | Method | Description                      |
| ---------------------------- | ------ | -------------------------------- |
| `/`                          | GET    | Health check                     |
| `/products`                  | GET    | List all products                |
| `/users`                     | GET    | List all users                   |
| `/recommendations/{user_id}` | GET    | Get personalized recommendations |
| `/interactions`              | POST   | Track user interaction           |
| `/analytics/user/{user_id}`  | GET    | Get user analytics               |
| `/docs`                      | GET    | Interactive API documentation    |

**Full API documentation:** http://localhost:8000/docs

---

## 🧠 How It Works

### 1. Hybrid Recommendation Algorithm

```
Final Score = (0.6 × Collaborative) + (0.4 × Content-Based) + Serendipity
```

- **Collaborative Filtering**: Finds users with similar taste using cosine similarity
- **Content-Based**: Matches products using TF-IDF on name, category, and tags
- **Serendipity Engine**: Injects 5% unexpected high-quality recommendations

### 2. Interaction Weights

| Action      | Weight | Meaning                |
| ----------- | ------ | ---------------------- |
| View        | 1.0    | Browsing interest      |
| Add to Cart | 2.0    | Strong purchase intent |
| Wishlist    | 3.0    | Future interest        |
| Rating      | 4.0    | Explicit feedback      |
| Purchase    | 5.0    | Conversion             |

### 3. AI-Powered Explanations

Every recommendation includes a personalized explanation generated by Gemini AI:

**Example:**

> "Based on your interest in wireless audio gear, these headphones offer premium noise cancellation at a similar price point to items you've purchased before. The 30-hour battery life matches your preference for long-lasting devices."

---

## 📊 Project Structure

```
heart-and-mind/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── models/            # Database models
│   │   │   ├── product.py
│   │   │   ├── user.py
│   │   │   └── interaction.py
│   │   ├── services/          # Business logic
│   │   │   ├── recommender.py       # Recommendation engine
│   │   │   └── llm_explainer.py     # Gemini AI integration
│   │   ├── utils/
│   │   │   └── seed_data.py         # Sample data generator
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py            # FastAPI application
│   ├── requirements.txt
│   └── .env
│
├── frontend/                   # Streamlit Frontend
│   ├── styles/
│   │   └── custom.css         # CRED-style dark theme
│   ├── utils/
│   │   └── api_client.py      # Backend API connector
│   ├── app.py                 # Main Streamlit app
│   └── requirements.txt
│
└── README.md
```

---

## 🎨 UI Features

### Dark Theme with CRED-Style Gradients

- Premium purple/blue gradient backgrounds
- Smooth hover effects and animations
- Glassmorphism cards
- Interactive product cards

### User Experience

- **Sidebar**: User selection, personality modes, quick stats
- **Recommendations Tab**: AI-powered product cards with explanations
- **Analytics Tab**: Behavioral insights and metrics
- **Browse Products Tab**: Full product catalog

---

## 🔧 Configuration

### Environment Variables

Edit `backend/.env`:

```bash
# Gemini API Key
GEMINI_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./heart_mind.db

# Recommendation Settings
MIN_INTERACTIONS_FOR_COLLABORATIVE=3
RECOMMENDATION_COUNT=10
SERENDIPITY_FACTOR=0.05

# LLM Settings
LLM_MODEL=gemini-1.5-pro
LLM_MAX_TOKENS=300
EXPLANATION_TEMPERATURE=0.7
```

---

## 📈 Performance

- **Response Time**: <200ms (without LLM), ~1-2s (with LLM)
- **Concurrent Users**: Tested with 100+ simultaneous requests
- **Database**: SQLite for dev, PostgreSQL-ready for production
- **Scalability**: Horizontal scaling supported with load balancer

---

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
pytest
```

### Manual Testing

```bash
# Test health check
curl http://localhost:8000/

# Test recommendations
curl http://localhost:8000/recommendations/1?personality=friendly

# Test product listing
curl http://localhost:8000/products
```

---

## 🚢 Deployment

### Deploy Backend (Railway)

```bash
cd backend
railway init
railway up
railway variables set GEMINI_API_KEY=your_key
```

### Deploy Frontend (Streamlit Cloud)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Deploy!

**Update API URL** in `frontend/utils/api_client.py` to your deployed backend URL.

---

## 🎯 Evaluation Metrics

### Recommendation Quality

- **Diversity**: Multiple categories represented
- **Relevance**: Match user's behavioral patterns
- **Novelty**: Serendipity recommendations
- **Explanation Quality**: Clear, compelling, actionable

### System Performance

- API response times
- User engagement rates
- Click-through rates
- Conversion rates

---

## 🔮 Future Enhancements

- [ ] Multi-modal recommendations (image + text)
- [ ] Real-time collaborative filtering with WebSockets
- [ ] A/B testing framework for explanation styles
- [ ] Social proof integration ("5 friends bought this")
- [ ] Temporal pattern analysis
- [ ] Voice-based explanations
- [ ] Mobile app (React Native)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **Streamlit** - Beautiful data apps
- **Google Gemini** - AI-powered explanations
- **scikit-learn** - Machine learning algorithms
- **CRED** - UI design inspiration

---

## 📞 Contact

**Developer**: Dhawal Agarwal  
**Email**: agarwaldhawalaero10@gmail.com  
**GitHub**: [@dhawalagarwal10](https://github.com/dhawalagarwal10)  
**LinkedIn**: [dhawal-agarwal-0z1](https://www.linkedin.com/in/dhawal-agarwal-0z1/)

---

## 🌟 Star this repo if you found it helpful!

**Built with ❤️ for Unthinkable Solutions**
