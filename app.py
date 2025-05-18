import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
import ast
from streamlit_carousel import carousel
import requests
import time

###

movies = [
    {"title": "The Shawshank Redemption", "img": "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg"},
    {"title": "The Godfather", "img": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg"},
    {"title": "The Dark Knight", "img": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"},
    {"title": "12 Angry Men", "img": "https://image.tmdb.org/t/p/w500/7sf9CgJz30aXDvrg7DYYUQ2U91T.jpg"},
    {"title": "Schindler's List", "img": "https://image.tmdb.org/t/p/w500/c8Ass7acuOe4za6DhSattE359gr.jpg"},
    {"title": "The Lord of the Rings: The Return of the King", "img": "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg"},
    {"title": "Pulp Fiction", "img": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg"},
    {"title": "Forrest Gump", "img": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg"},
    {"title": "Fight Club", "img": "https://image.tmdb.org/t/p/w500/bptfVGEQuv6vDTIMVCHjJ9Dz8PX.jpg"},
    {"title": "Inception", "img": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg"},
    {"title": "Mad Max: Fury Road", "img": "https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg"},
    {"title": "John Wick", "img": "https://image.tmdb.org/t/p/w500/ziEuG1essDuWuC5lpWUaw1uXY2O.jpg"},
    {"title": "The Matrix", "img": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg"},
    {"title": "Avengers: Endgame", "img": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg"},
    
]


images_html = "".join(
    f'<img src="{m["img"]}" alt="{m["title"]}" title="{m["title"]}"/>' for m in movies
)
images_html += images_html  # duplicate for infinite scroll effect

html_code = f"""
<style>
.scroll-wrapper {{
  width: 100%;
  overflow: hidden;
  background-color: #000;
  border-radius: 10px;
  padding: 10px 0;
}}

.scroll-content {{
  display: flex;
  width: max-content;
  animation: scroll-left 40s linear infinite;
  gap: 12px;
}}

.scroll-content img {{
  height: 160px;
  border-radius: 8px;
  user-select: none;
  flex-shrink: 0;
  pointer-events: none; /* disables clicking */
}}

@keyframes scroll-left {{
  0% {{
    transform: translateX(0);
  }}
  100% {{
    transform: translateX(-50%);
  }}
}}
</style>

<div class="scroll-wrapper">
  <div class="scroll-content">
    {images_html}
  </div>
</div>
"""

st.markdown(html_code, unsafe_allow_html=True)


###

# Load data
df = pd.read_csv('ratings_partial_upd.csv')

# Normalize 'type' and 'mood' columns to consistent formatting
df['type'] = df['type'].astype(str).str.strip().str.title()

def clean_mood_value(val):
    try:
        if isinstance(val, str) and val.startswith('[') and val.endswith(']'):
            mood_list = ast.literal_eval(val)
            if isinstance(mood_list, list) and len(mood_list) > 0:
                return mood_list[0].strip().title()  # clean and title case first mood
    except Exception:
        pass
    return val.strip().title() if isinstance(val, str) else val

df['mood'] = df['mood'].apply(clean_mood_value)

st.title('What should I watch?')
st.write('Find the perfect Netflix content based on your mood and available time!')

# Mood and time inputs
mood = st.selectbox("Pick your mood:", sorted(df['mood'].dropna().unique()), key="mood_selectbox")
time = st.slider("How much time do you have? (in minutes)", 10, 300, 90)

# Recommendation mode selection
recommendation_mode = st.selectbox("Choose Recommendation Mode:", [
    "Recommended for you", 
    "Smart recommendation (AI Based)",
    "Top-rated on IMDb"
], key="recommendation_mode_select")

# Number of items to show initially and per click
movies_per_page = 10

# Initialize session state counters for each mode
if 'rec_you_count' not in st.session_state:
    st.session_state.rec_you_count = movies_per_page
if 'smart_rec_count' not in st.session_state:
    st.session_state.smart_rec_count = movies_per_page
if 'top_rated_count' not in st.session_state:
    st.session_state.top_rated_count = movies_per_page

if 'last_mode' not in st.session_state:
    st.session_state.last_mode = recommendation_mode

if st.session_state.last_mode != recommendation_mode:
    st.session_state.rec_you_count = movies_per_page
    st.session_state.smart_rec_count = movies_per_page
    st.session_state.top_rated_count = movies_per_page
    st.session_state.last_mode = recommendation_mode

def show_movies(df_movies, count):
    for _, row in df_movies.head(count).iterrows():
        st.markdown(f"### {row['title']} ({row['type']})")
        if 'rating_score' in row:
            st.markdown(f"⭐ IMDb Rating: {row['rating_score']}")
        st.markdown(f"⏱️ Duration: {row['duration_cleaned']} min")
        st.markdown(f"🎭 Genres: {row['genres_list']}")
        st.markdown(f"<u>Description</u>: <br/>{row['description']}", unsafe_allow_html=True)
        st.markdown("---")

# Mode 1: Regular Recommendations
if recommendation_mode == "Recommended for you":
    st.subheader("-> Recommendations for you:")
    
    filtered = df[
        (df['mood'] == mood) & 
        (df['duration_cleaned'] <= time)
    ]

    if not filtered.empty:
        show_movies(filtered, st.session_state.rec_you_count)
        if st.session_state.rec_you_count < len(filtered):
            if st.button("Show more movies", key="rec_you_show_more"):
                st.session_state.rec_you_count += movies_per_page
    else:
        st.write("No matches found. Try adjusting your mood and time.")

# Mode 2: AI-Based Recommendations
elif recommendation_mode == "Smart recommendation (AI Based)":
    st.subheader("Smart recommendations: (AI Based)")

    required_columns = ['duration_cleaned', 'mood', 'rating_score']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    df['rating_score'] = df['rating_score'].fillna(0)
    df_clean = df.dropna(subset=['duration_cleaned', 'mood']).copy()

    le = LabelEncoder()
    df_clean['mood_encoded'] = le.fit_transform(df_clean['mood'])

    features = df_clean[['duration_cleaned', 'mood_encoded', 'rating_score']]
    kmeans = KMeans(n_clusters=4, random_state=42)
    df_clean['cluster'] = kmeans.fit_predict(features)

    input_vector = [[time, le.transform([mood])[0], 5.0]]  # neutral 5.0 rating
    predicted_cluster = kmeans.predict(input_vector)[0]

    smart_recommendations = df_clean[
        (df_clean['cluster'] == predicted_cluster) &
        (df_clean['mood'] == mood) &
        (df_clean['duration_cleaned'] <= time)
    ].sort_values(by='rating_score', ascending=False)

    if not smart_recommendations.empty:
        st.markdown("##### Based on your mood, time and IMDb score")
        st.markdown("---")
        show_movies(smart_recommendations, st.session_state.smart_rec_count)
        if st.session_state.smart_rec_count < len(smart_recommendations):
            if st.button("Show more movies", key="smart_rec_show_more"):
                st.session_state.smart_rec_count += movies_per_page
    else:
        st.write("No smart suggestions found. Try adjusting your mood or time.")

# Mode 3: Top-rated IMDb movies
elif recommendation_mode == "Top-rated on IMDb":
    st.subheader(f"Top-rated Netflix Titles for mood '{mood}' (within {time} min)")
    st.markdown("---")

    df_rated = df[
        (df['mood'] == mood) &
        (df['duration_cleaned'] <= time) & 
        (df['rating_score'].notna())
    ]

    top_rated = df_rated.sort_values(by='rating_score', ascending=False)

    if not top_rated.empty:
        show_movies(top_rated, st.session_state.top_rated_count)
        if st.session_state.top_rated_count < len(top_rated):
            if st.button("Show more movies", key="top_rated_show_more"):
                st.session_state.top_rated_count += movies_per_page
    else:
        st.write("No top-rated shows found for your mood and time selection.")
