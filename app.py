import streamlit as st
import re
from groq import Groq
import json
import os

HISTORY_FILE = "performance_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_to_history(question, overall_score, role, difficulty, domain):
    history = load_history()
    history.append({
        "question": question, 
        "score": overall_score, 
        "role": role, 
        "difficulty": difficulty,
        "domain": domain
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

st.set_page_config(page_title="HireMind", layout="wide")

# Initialize session states
if "history" not in st.session_state:
    st.session_state.history = []
if "current_question" not in st.session_state:
    st.session_state.current_question = ""
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Medium"
if "evaluation_text" not in st.session_state:
    st.session_state.evaluation_text = ""
if "feedback_text" not in st.session_state:
    st.session_state.feedback_text = ""
if "overall_score" not in st.session_state:
    st.session_state.overall_score = None
if "dimension_scores" not in st.session_state:
    st.session_state.dimension_scores = {}
if "answer_input_box" not in st.session_state:
    st.session_state.answer_input_box = ""

def get_client():
    return Groq(api_key="")

def interviewer_agent(role, domain, difficulty, history):
    history_text = ", ".join(history) if history else "None"
    
    messages = [
        {
            "role": "system",
            "content": "You are an expert interviewer. Return ONLY the question text. Do not include any numbering, intro, or extra text."
        },
        {
            "role": "user",
            "content": f"Generate a SINGLE interview question for a {role} candidate focusing on the {domain} domain.\nThe difficulty level should be {difficulty}.\nDo NOT repeat any of these previously asked questions: {history_text}."
        }
    ]
    
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def evaluator_agent(question, answer):
    messages = [
        {
            "role": "system",
            "content": "You are an expert interviewer evaluating a candidate's answer."
        },
        {
            "role": "user",
            "content": f"Question: {question}\nCandidate Answer: {answer}\n\nEvaluate the answer and return EXACTLY this format, replacing the bracketed parts with your scores (0-10) and one-line reasons.\nTechnical Accuracy: <score>/10 | <one-line reason>\nClarity: <score>/10 | <one-line reason>\nCompleteness: <score>/10 | <one-line reason>\nCommunication: <score>/10 | <one-line reason>\nUse of Examples: <score>/10 | <one-line reason>\nRelevance: <score>/10 | <one-line reason>\nOverall: <score>/10"
        }
    ]
    
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()

def feedback_agent(question, answer, evaluation_text, domain):
    domain_instruction = "\nIMPORTANT: Since this is a Technical interview, you MUST include specific, clickable website urls/links (like LeetCode, MDN, GeeksForGeeks, AWS Docs, etc.) within the Practice Recommendations." if domain == "Technical" else ""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful interview coach."
        },
        {
            "role": "user",
            "content": f"Question: {question}\nCandidate Answer: {answer}\nEvaluation: {evaluation_text}\n\nProvide feedback EXACTLY in this format:\n\nIMPROVEMENT STRATEGY:\n1. [First specific area to improve]\n2. [Second specific area to improve]\n3. [Third specific area to improve]\n\nMODEL ANSWER (example of a strong response):\n[Write a 3-5 sentence model answer]\n\nPRACTICE RECOMMENDATIONS:\n- [Resource or exercise 1]\n- [Resource or exercise 2]\n- [Resource or exercise 3]{domain_instruction}"
        }
    ]
    
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.7,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

def parse_scores(evaluation_text):
    dimensions = ["Technical Accuracy", "Clarity", "Completeness", "Communication", "Use of Examples", "Relevance"]
    scores = {}
    overall = 0.0
    
    for line in evaluation_text.split('\n'):
        line = line.strip()
        if not line: continue
        for dim in dimensions:
            if line.startswith(dim) and "|" in line:
                try:
                    parts = line.split("|")
                    score_part = parts[0].split(":")[1].strip()
                    score_val = float(score_part.split("/")[0].strip())
                    reason = parts[1].strip()
                    scores[dim] = {"score": score_val, "reason": reason}
                except:
                    pass
        if line.startswith("Overall:"):
            try:
                score_part = line.split(":")[1].strip()
                overall = float(score_part.split("/")[0].strip())
            except:
                pass
                
    if len(scores) == 6:
        weights = {
            "Technical Accuracy": 0.25,
            "Clarity": 0.20,
            "Completeness": 0.20,
            "Communication": 0.15,
            "Use of Examples": 0.10,
            "Relevance": 0.10
        }
        computed_overall = sum(scores[dim]["score"] * weights[dim] for dim in dimensions)
        overall = round(computed_overall, 1)
        
    return scores, overall

def adjust_difficulty(score, current_diff):
    levels = ["Easy", "Medium", "Hard"]
    idx = levels.index(current_diff)
    if score >= 8.0:
        if idx < 2:
            return levels[idx+1], "Great answer! Difficulty increased."
    elif score <= 4.9:
        if idx > 0:
            return levels[idx-1], "Let's try a slightly easier question."
    return current_diff, ""

# Sidebar
st.sidebar.title("Settings")

role = st.sidebar.selectbox("Job Role", [
    "Software Engineer", "Data Scientist", "Product Manager", 
    "Machine Learning Engineer", "Web Developer", "DevOps Engineer"
])
domain = st.sidebar.selectbox("Domain", ["Technical", "HR / Behavioural", "System Design"])

# Handle dynamic difficulty properly without hitting key mutation errors
diff_options = ["Easy", "Medium", "Hard"]
st.session_state.difficulty = st.sidebar.selectbox(
    "Difficulty", 
    diff_options, 
    index=diff_options.index(st.session_state.difficulty)
)

# Main Page
st.title("HireMind")
st.subheader("Multi-Agent AI Interview Simulator")

if st.button("New Question"):
    with st.spinner("Interviewer Agent is generating a question..."):
        try:
            q = interviewer_agent(role, domain, st.session_state.difficulty, st.session_state.history)
            st.session_state.current_question = q
            st.session_state.evaluation_text = ""
            st.session_state.feedback_text = ""
            st.session_state.dimension_scores = {}
            st.session_state.overall_score = None
            st.session_state.answer_input_box = ""
        except Exception as e:
            st.error(f"Error generating question: {e}")

if st.session_state.current_question:
    st.info(st.session_state.current_question)

    user_answer = st.text_area("Your Answer", height=300, key="answer_input_box")
    
    if st.button("Submit Answer", type="primary"):
        if not user_answer.strip():
            st.warning("Please enter an answer before submitting.")
        else:
            with st.spinner("Evaluator Agent is scoring your answer..."):
                try:
                    eval_text = evaluator_agent(st.session_state.current_question, user_answer)
                    st.session_state.evaluation_text = eval_text
                    scores, overall = parse_scores(eval_text)
                    st.session_state.dimension_scores = scores
                    st.session_state.overall_score = overall
                except Exception as e:
                    st.error(f"Error evaluating answer: {e}")
                    st.stop()

            with st.spinner("Feedback Agent is generating tips..."):
                try:
                    feed_text = feedback_agent(st.session_state.current_question, user_answer, st.session_state.evaluation_text, domain)
                    st.session_state.feedback_text = feed_text
                except Exception as e:
                    st.error(f"Error generating feedback: {e}")
            
            st.session_state.history.append(st.session_state.current_question)
            
            if st.session_state.overall_score is not None:
                new_diff, msg = adjust_difficulty(st.session_state.overall_score, st.session_state.difficulty)
                if new_diff != st.session_state.difficulty:
                    st.session_state.difficulty = new_diff
                    if msg:
                        st.success(msg)
                
                # Persist the score so we can track improvement
                save_to_history(st.session_state.current_question, st.session_state.overall_score, role, st.session_state.difficulty, domain)

if st.session_state.overall_score is not None:
    st.markdown("---")
    st.header("Results")
    
    score = st.session_state.overall_score
    color = "green" if score >= 7.0 else "orange" if score >= 5.0 else "red"
    
    st.markdown(f"### Overall Score: :{color}[{score}/10]")
    
    with st.expander("Dimension Scores", expanded=True):
        if st.session_state.dimension_scores:
            for dim, data in st.session_state.dimension_scores.items():
                col1, col2 = st.columns([1, 4])
                dim_score = data['score']
                reason = data['reason']
                with col1:
                    st.write(f"**{dim}**")
                with col2:
                    val = max(0.0, min(1.0, dim_score / 10.0))
                    try:
                        st.progress(val, text=f"{dim_score}/10 - {reason}")
                    except TypeError:
                        st.progress(val)
                        st.write(f"{dim_score}/10 - {reason}")
        else:
            st.warning("Could not parse scores correctly. Raw Output:")
            st.code(st.session_state.evaluation_text)

    st.subheader("Your AI Interview Coach")
    
    feed_text = st.session_state.feedback_text
    sections = {"strategy": "", "model": "", "practice": ""}
    current_section = None
    
    for line in feed_text.split('\n'):
        if "IMPROVEMENT STRATEGY" in line.upper():
            current_section = "strategy"
        elif "MODEL ANSWER" in line.upper():
            current_section = "model"
        elif "PRACTICE RECOMMENDATIONS" in line.upper():
            current_section = "practice"
        elif current_section:
            sections[current_section] += line + '\n'

    with st.container():
        st.caption("Great job! Let's break down your performance. Here are some actionable tips and a model response.")
        
        if sections["strategy"].strip():
            st.markdown("#### Improvement Strategy")
            st.info(sections["strategy"].strip())
            
        if sections["model"].strip():
            st.markdown("#### Model Answer")
            st.success(sections["model"].strip())
            
        if sections["practice"].strip():
            st.markdown("#### Practice Recommendations")
            st.warning(sections["practice"].strip())
            
        # Fallback if the LLM didn't use the expected headings
        if not any(sections.values()):
            st.write(feed_text)

st.markdown("---")

st.subheader("Your Improvement Journey")
historical_data = load_history()
if len(historical_data) > 0:
    filtered_data = historical_data
    
    if len(filtered_data) > 0:
        all_possible_roles = [
            "Software Engineer", "Data Scientist", "Product Manager", 
            "Machine Learning Engineer", "Web Developer", "DevOps Engineer"
        ]
        
        selected_role = st.radio("Filter Improvement Journey by Role:", ["Overall"] + all_possible_roles, horizontal=True)
        
        if selected_role != "Overall":
            role_filtered_data = [item for item in filtered_data if item.get("role") == selected_role]
        else:
            role_filtered_data = filtered_data
            
        total = len(role_filtered_data)
        total_score = sum(float(item["score"]) for item in role_filtered_data if "score" in item)
        avg_score = (total_score / total) if total > 0 else 0
        avg_pct = int((avg_score / 10.0) * 100)
        roles_counts = {r: 0 for r in all_possible_roles}
        for item in filtered_data:
            r = item.get("role")
            if r in roles_counts:
                roles_counts[r] += 1
            
        ROLES_COLORS = {
            "Software Engineer": "#00b8a3",
            "Data Scientist": "#ffc01e",
            "Product Manager": "#ff375f",
            "Machine Learning Engineer": "#3b82f6",
            "Web Developer": "#8b5cf6",
            "DevOps Engineer": "#f97316"
        }

        pie_total = sum(roles_counts.values())
        gradient_parts = []
        current_deg = 0
        if pie_total > 0:
            for r, count in roles_counts.items():
                if count > 0:
                    deg = (count / pie_total) * 360
                    color = ROLES_COLORS.get(r, "#888")
                    gradient_parts.append(f"{color} {current_deg}deg {current_deg + deg}deg")
                    current_deg += deg
        else:
            gradient_parts.append("#333 0deg 360deg")
            
        gradient_str = ", ".join(gradient_parts)
        
        boxes_html = ""
        for r in all_possible_roles:
            count = roles_counts[r]
            color = ROLES_COLORS.get(r, "#888")
            bg_color = "rgba(255, 255, 255, 0.15)" if selected_role == r else "rgba(255, 255, 255, 0.05)"
            boxes_html += f'<div style="background: {bg_color}; padding: 8px 12px; border-radius: 8px; text-align: center;"><span style="color: {color}; font-weight: 600; font-size: 12px;">{r}</span><br><span style="color: white; font-weight: bold; font-size: 16px;">{count}</span></div>'
            
        html = f'''
        <div style="display: flex; gap: 50px; align-items: center; justify-content: center; background: #1e1e24; padding: 30px; border-radius: 15px; border: 1px solid #333; margin-top: 10px;">
           <div style="position: relative; width: 160px; height: 160px; border-radius: 50%; background: conic-gradient({gradient_str}); flex-shrink: 0;">
               <div style="position: absolute; top: 12px; left: 12px; width: 136px; height: 136px; border-radius: 50%; background: #1e1e24; display: flex; justify-content: center; align-items: center; flex-direction: column;">
                   <span style="font-size: 38px; font-weight: bold; color: white; line-height: 1;">{avg_pct}%</span>
                   <span style="font-size: 13px; color: #a0a0a0; margin-top: 4px;">Avg. Score</span>
               </div>
           </div>
           <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
               {boxes_html}
           </div>
        </div>
        '''
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No data recorded for this role yet.")
else:
    st.write("Finish a question to start plotting your improvement graph!")
