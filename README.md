# HireMind
### Multi-Agent AI Interview Simulator

Built with **Python • Streamlit • Groq API • LLaMA 3.1**

---

## 📌 Overview

HireMind is a **Multi-Agent AI system** that simulates a complete job interview pipeline.

Three specialized AI agents:
- Interviewer
- Evaluator
- Feedback Coach  

They work together to:
- Generate questions  
- Evaluate answers  
- Provide personalized coaching  

All in real-time through a clean web interface.

This is designed for:
- Students  
- Job seekers  
- Placement training programs  

---

## 🚀 Features

- Multi-agent pipeline (Interviewer, Evaluator, Feedback Coach)
- 6-dimension scoring rubric with weighted score
- Adaptive difficulty system
- Domains:
  - Technical
  - HR / Behavioural
  - System Design
- Supported roles:
  - Software Engineer
  - Data Scientist
  - Product Manager
  - Machine Learning Engineer
  - Web Developer
  - DevOps Engineer
- Performance dashboard (Improvement Journey)
- Model answers after each response
- Practice resource recommendations
- Local JSON-based history tracking

---

## 🛠 Tech Stack

| Layer        | Technology            | Purpose |
|-------------|---------------------|--------|
| Frontend    | Streamlit           | Web UI |
| LLM Backend | Groq API            | Fast inference |
| AI Model    | LLaMA 3.1 8B Instant| Q&A + Evaluation |
| Language    | Python 3.10+        | Core logic |
| Storage     | JSON (local)        | History |

---


## 🎯 How to Use
- Start Interview
- Select Job Role
- Select Domain
- Choose Difficulty
- Click New Question
- Answer the question
- Click Submit Answer

---

## 📊 Results Breakdown

### After submission:

- Overall score (0–10)
- Dimension-wise scores
- Improvement strategy
- Model answer
- Practice recommendations
---
### 🔄 Adaptive Difficulty
- Score Range	Action
 - 8.0 – 10	Difficulty increases
 - 5.0 – 7.9	Stays same
 - 0.0 – 4.9	Difficulty decreases
---
### 📐 Scoring Rubric
- Dimension	Weight
- Technical Accuracy	25%
- Clarity	20%
- Completeness	20%
- Communication	15%
- Use of Examples	10%
- Relevance	10%
---
## 🤖 How the Agents Work
 - Generates questions
 - Avoids repetition
 - Scores answers across 6 dimensions
 - Uses structured output
 - Improvement strategy
 - Model answer
 - Learning resources
