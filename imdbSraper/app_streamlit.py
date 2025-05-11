import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from database.mongo import get_all_movies
from io import BytesIO
import base64
import re
import requests
from textblob import TextBlob

st.set_page_config(page_title="IMDb Top 250 Dashboard", layout="wide")

# Chargement des données depuis MongoDB
movies = get_all_movies()
df = pd.DataFrame(movies)

if df.empty:
    st.warning("Aucune donnée trouvée dans la base MongoDB.")
    st.stop()

def parse_duration(d):
    if pd.isnull(d):
        return None
    if isinstance(d, (int, float)):
        return int(d)
    match = re.match(r"(?:(\d+)h)?\s*(\d+)?m?", str(d).strip())
    if match:
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        return hours * 60 + minutes
    return None

def get_poster_url(title, year=None):
    api_key = "demo"  # Remplacez par votre clé OMDb si vous en avez une
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    if year:
        url += f"&y={year}"
    try:
        r = requests.get(url)
        data = r.json()
        if data.get('Poster') and data['Poster'] != 'N/A':
            return data['Poster']
    except Exception:
        pass
    return "https://via.placeholder.com/200x300?text=No+Poster"

def get_youtube_trailer_url(title, year=None):
    query = f"{title} trailer"
    if year:
        query += f" {year}"
    return f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"

def sentiment_synopsis(s):
    if not isinstance(s, str) or not s.strip():
        return 0
    return TextBlob(s).sentiment.polarity

def get_similar_movies(selected_film, df, n=5):
    if 'genres' not in selected_film or 'genres' not in df.columns:
        return pd.DataFrame()
    genres = set(str(selected_film['genres']).split(','))
    sim = df[df['title'] != selected_film['title']].copy()
    sim['common_genres'] = sim['genres'].apply(lambda g: len(genres & set(str(g).split(','))))
    return sim.sort_values(['common_genres','rating'], ascending=[False,False]).head(n)

def plot_wordcloud(text, title):
    wc = WordCloud(width=800, height=300, background_color='white').generate(' '.join(text))
    fig, ax = plt.subplots(figsize=(8,3))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)
    st.caption(title)

# Nettoyage des colonnes principales
if 'rating' in df.columns:
    df = df[df['rating'].notnull() & (df['rating'] != 'N/A')]
    df['rating'] = df['rating'].astype(float)
if 'duration' in df.columns:
    df['duration'] = df['duration'].apply(parse_duration)
    df = df[df['duration'].notnull()]
    df['duration'] = df['duration'].astype(int)
if 'year' in df.columns:
    df = df[df['year'].notnull() & (df['year'] != 'N/A')]
    df['year'] = df['year'].astype(int)

# --- Favoris (stockés en session Streamlit) ---
if 'favoris' not in st.session_state:
    st.session_state['favoris'] = set()

# --- UI ---
st.title("🎬 IMDb Top 250 - Dashboard interactif avancé")

# Bande déroulante (marquee) avec tous les titres de films
titres = df['title'].dropna().unique()
marquee_html = f"""
<div style='background:#22223b;color:#f2e9e4;padding:8px 0;font-size:18px;white-space:nowrap;overflow:hidden;'>
  <marquee behavior='scroll' direction='left' scrollamount='7'>
    {' | '.join(titres)}
  </marquee>
</div>
"""
st.markdown(marquee_html, unsafe_allow_html=True)

# Sélection d'un film (dropdown)
st.subheader("Sélectionnez un film pour voir ses caractéristiques")
selected_title = st.selectbox("Choisissez un film", titres)
film = df[df['title']==selected_title].iloc[0]

# Affichage des caractéristiques du film
colA, colB = st.columns([1,2])
with colA:
    poster_url = get_poster_url(film['title'], film['year'])
    st.image(poster_url, width=200, caption="Affiche du film")
    if st.button("⭐ Ajouter/Retirer des favoris"):
        if film['title'] in st.session_state['favoris']:
            st.session_state['favoris'].remove(film['title'])
        else:
            st.session_state['favoris'].add(film['title'])
    if film['title'] in st.session_state['favoris']:
        st.success("Ce film est dans vos favoris !")
with colB:
    st.markdown(f"**Titre :** {film['title']}")
    st.markdown(f"**Année :** {film['year']}")
    st.markdown(f"**Note :** {film['rating']}")
    if 'genres' in film:
        st.markdown(f"**Genres :** {film['genres']}")
    if 'director' in film:
        st.markdown(f"**Réalisateur :** {film['director']}")
    if 'duration' in film:
        st.markdown(f"**Durée :** {film['duration']} min")
    if 'synopsis' in film:
        st.markdown(f"**Synopsis :** {film['synopsis']}")
        sentiment = sentiment_synopsis(film['synopsis'])
        st.markdown(f"**Sentiment du synopsis :** {'😊' if sentiment>0.2 else '😐' if sentiment>-0.2 else '😞'} (score : {sentiment:.2f})")
    if 'imdb_link' in film:
        st.markdown(f"[Lien IMDb]({film['imdb_link']})")
    trailer_url = get_youtube_trailer_url(film['title'], film['year'])
    st.markdown(f"[Voir la bande-annonce sur YouTube]({trailer_url})")

# Suggestions de films similaires
st.markdown("**Suggestions de films similaires :**")
sim = get_similar_movies(film, df)
if not sim.empty:
    st.dataframe(sim[['title','year','rating','genres']].head(5))
else:
    st.info("Aucune suggestion disponible.")

# Affichage des favoris
if st.session_state['favoris']:
    st.subheader("⭐ Vos films favoris")
    favs = df[df['title'].isin(st.session_state['favoris'])]
    st.dataframe(favs[['title','year','rating','genres','director','duration']] if 'genres' in favs.columns and 'director' in favs.columns else favs)

# --- PAGE ANALYSES ---
st.markdown("---")
st.header("📊 Analyses et visualisations avancées")

# Statistiques globales
col1, col2, col3 = st.columns(3)
col1.metric("Note moyenne", round(df['rating'].mean(), 2))
col2.metric("Durée moyenne (min)", int(df['duration'].mean()) if 'duration' in df else '-')
col3.metric("Année médiane", int(df['year'].median()) if 'year' in df else '-')

# Genres et réalisateurs les plus fréquents
st.subheader("Genres et réalisateurs les plus fréquents")
if 'genres' in df.columns:
    all_genres = df['genres'].dropna().str.split(',').explode().str.strip()
    top_genres = all_genres.value_counts().head(10)
    fig_genres = px.bar(top_genres, x=top_genres.index, y=top_genres.values, labels={'x':'Genre','y':'Nombre'})
    st.plotly_chart(fig_genres, use_container_width=True)
if 'director' in df.columns:
    top_directors = df['director'].value_counts().head(10)
    fig_directors = px.bar(top_directors, x=top_directors.index, y=top_directors.values, labels={'x':'Réalisateur','y':'Nombre'})
    st.plotly_chart(fig_directors, use_container_width=True)

# Visualisations interactives
st.subheader("Visualisations interactives")
fig_hist = px.histogram(df, x='rating', nbins=20, title='Répartition des notes')
st.plotly_chart(fig_hist, use_container_width=True)
if 'year' in df.columns:
    df['decade'] = (df['year']//10)*10
    fig_decade = px.bar(df['decade'].value_counts().sort_index(), labels={'value':'Nombre de films','index':'Décennie'}, title='Répartition par décennie')
    st.plotly_chart(fig_decade, use_container_width=True)
if 'genres' in df.columns:
    genre_ratings = df[['genres','rating']].dropna().copy()
    genre_ratings = genre_ratings.assign(genre=genre_ratings['genres'].str.split(',')).explode('genre')
    genre_ratings['genre'] = genre_ratings['genre'].str.strip()
    fig_box = px.box(genre_ratings, x='genre', y='rating', title='Boxplot des notes par genre')
    st.plotly_chart(fig_box, use_container_width=True)
if 'genres' in df.columns and 'duration' in df.columns:
    genre_duration = df[['genres','duration']].dropna().copy()
    genre_duration = genre_duration.assign(genre=genre_duration['genres'].str.split(',')).explode('genre')
    genre_duration['genre'] = genre_duration['genre'].str.strip()
    mean_duration = genre_duration.groupby('genre')['duration'].mean().sort_values(ascending=False).head(10)
    fig_dur = px.bar(mean_duration, x=mean_duration.index, y=mean_duration.values, labels={'x':'Genre','y':'Durée moyenne'}, title='Durée moyenne par genre')
    st.plotly_chart(fig_dur, use_container_width=True)

# Analyses avancées
st.subheader("Analyses avancées")
if 'director' in df.columns:
    top5_dir = df.groupby('director')['rating'].mean().sort_values(ascending=False).head(5)
    st.write("**Top 5 réalisateurs par note moyenne**")
    st.bar_chart(top5_dir)
    st.dataframe(df[df['director'].isin(top5_dir.index)][['title','director','rating']].sort_values('rating',ascending=False))
if 'genres' in df.columns:
    st.write("**Films les plus populaires par genre**")
    for genre in all_genres.value_counts().head(3).index:
        st.write(f"*{genre}*")
        st.dataframe(df[df['genres'].str.contains(genre)][['title','rating','year','director']].sort_values('rating',ascending=False).head(5))
if 'genres' in df.columns:
    st.write("**Nuage de mots des genres**")
    plot_wordcloud(all_genres, "Genres les plus présents")
if 'director' in df.columns:
    st.subheader("Nuage de mots des réalisateurs")
    plot_wordcloud(df['director'].dropna().astype(str), "Réalisateurs les plus présents")
if 'actors' in df.columns:
    st.subheader("Nuage de mots des acteurs")
    actors = df['actors'].dropna().str.split(',').explode().str.strip()
    plot_wordcloud(actors, "Acteurs les plus présents")

# Heatmap de corrélation
st.subheader("Heatmap de corrélation")
if {'rating','duration','year'}.issubset(df.columns):
    corr = df[['rating','duration','year']].corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
    st.pyplot(fig)

# Comparateur de films
st.subheader("Comparateur de films")
if 'title' in df.columns:
    films = df['title'].unique()
    film1 = st.selectbox("Film 1", films, key='film1')
    film2 = st.selectbox("Film 2", films, key='film2')
    if film1 and film2:
        comp = df[df['title'].isin([film1, film2])][['title','year','rating','genres','director','duration'] if 'genres' in df.columns and 'director' in df.columns else ['title','year','rating','duration']]
        st.dataframe(comp)

# Analyse qualitative des synopsis
st.subheader("Analyse qualitative des synopsis")
if 'synopsis' in df.columns:
    df['synopsis_length'] = df['synopsis'].str.len()
    st.write(f"Longueur moyenne des synopsis : {int(df['synopsis_length'].mean())} caractères")
    longest = df.loc[df['synopsis_length'].idxmax()]
    st.write("**Synopsis le plus long :**")
    st.write(f"*{longest['title']}* ({longest['year']}) - {longest['synopsis_length']} caractères")
    st.info(longest['synopsis'])

# --- ANALYSES AVANCÉES ET ORIGINALES ---
st.markdown("---")
st.header("🔎 Analyses avancées et originales")

# 1. Évolution de la note moyenne et du nombre de films par décennie
if 'year' in df.columns:
    st.subheader("Évolution de la note moyenne et du nombre de films par décennie")
    df['decade'] = (df['year']//10)*10
    decade_stats = df.groupby('decade').agg({'rating':'mean','title':'count'}).rename(columns={'rating':'Note moyenne','title':'Nombre de films'})
    fig1 = px.line(decade_stats, y='Note moyenne', labels={'index':'Décennie'}, title='Note moyenne par décennie')
    fig2 = px.bar(decade_stats, y='Nombre de films', labels={'index':'Décennie'}, title='Nombre de films par décennie')
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)

# 2. Distribution de la durée des films
if 'duration' in df.columns:
    st.subheader("Distribution de la durée des films")
    fig3 = px.histogram(df, x='duration', nbins=20, title='Histogramme des durées')
    st.plotly_chart(fig3, use_container_width=True)
    fig4 = px.box(df, y='duration', title='Boxplot des durées')
    st.plotly_chart(fig4, use_container_width=True)

# 3. Top films par genre et par décennie
if 'genres' in df.columns and 'decade' in df.columns:
    st.subheader("Top films par genre et par décennie")
    genres = df['genres'].dropna().str.split(',').explode().str.strip().unique()
    decades = sorted(df['decade'].unique())
    genre_select = st.selectbox("Choisissez un genre", genres, key='genre_decade')
    decade_select = st.selectbox("Choisissez une décennie", decades, key='decade_genre')
    top_films = df[df['genres'].str.contains(genre_select, na=False) & (df['decade']==decade_select)].sort_values('rating', ascending=False).head(5)
    st.dataframe(top_films[['title','year','rating','director','duration']])

# 4. Diversité des genres (mono/multi-genre)
if 'genres' in df.columns:
    st.subheader("Diversité des genres : mono-genre vs multi-genre")
    df['nb_genres'] = df['genres'].apply(lambda g: len(str(g).split(',')) if pd.notnull(g) else 0)
    mono = df[df['nb_genres']==1]['rating']
    multi = df[df['nb_genres']>1]['rating']
    st.write(f"Films mono-genre : {len(mono)} | Films multi-genre : {len(multi)}")
    fig5 = px.box(df, x='nb_genres', y='rating', labels={'nb_genres':'Nombre de genres','rating':'Note'}, title='Note selon le nombre de genres')
    st.plotly_chart(fig5, use_container_width=True)

# 5. Corrélation élargie
st.subheader("Corrélation entre note, durée, année")
if {'rating','duration','year'}.issubset(df.columns):
    corr = df[['rating','duration','year']].corr()
    fig6, ax = plt.subplots()
    sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
    st.pyplot(fig6)

# 6. Durée optimale pour un film bien noté
if 'duration' in df.columns:
    st.subheader("Existe-t-il une durée idéale pour un film bien noté ?")
    fig7 = px.scatter(df, x='duration', y='rating', trendline='ols', title='Note vs Durée')
    st.plotly_chart(fig7, use_container_width=True)

# 7. Acteurs/actrices les plus présents
if 'actors' in df.columns:
    st.subheader("Acteurs/actrices les plus présents dans le Top 250")
    actors = df['actors'].dropna().str.split(',').explode().str.strip()
    top_actors = actors.value_counts().head(10)
    fig8 = px.bar(top_actors, x=top_actors.index, y=top_actors.values, labels={'x':'Acteur/Actrice','y':'Présence'}, title='Top acteurs/actrices')
    st.plotly_chart(fig8, use_container_width=True)

# 8. Répartition des films par langue/pays (si dispo)
if 'language' in df.columns:
    st.subheader("Répartition des films par langue")
    top_lang = df['language'].dropna().str.split(',').explode().str.strip().value_counts().head(10)
    fig9 = px.pie(values=top_lang.values, names=top_lang.index, title='Langues les plus représentées')
    st.plotly_chart(fig9, use_container_width=True)
if 'country' in df.columns:
    st.subheader("Répartition des films par pays")
    top_country = df['country'].dropna().str.split(',').explode().str.strip().value_counts().head(10)
    fig10 = px.pie(values=top_country.values, names=top_country.index, title='Pays les plus représentés')
    st.plotly_chart(fig10, use_container_width=True)

# 9. Prime à l’ancienneté et à la nouveauté
if 'year' in df.columns:
    st.subheader("Prime à l’ancienneté ou à la nouveauté ?")
    old = df[df['year']<1980]['rating']
    new = df[df['year']>=1980]['rating']
    st.write(f"Films avant 1980 : {len(old)} | Films après 1980 : {len(new)}")
    fig11 = px.box(df, x=df['year']<1980, y='rating', labels={'x':'Avant 1980','rating':'Note'}, title='Note : anciens vs récents')
    st.plotly_chart(fig11, use_container_width=True)

# 10. Diversité linguistique
if 'language' in df.columns:
    st.subheader("Diversité linguistique")
    n_lang = df['language'].dropna().str.split(',').explode().str.strip().nunique()
    st.write(f"Nombre de langues différentes dans le Top 250 : {n_lang}")

# 11. Analyse de la “starification” réalisateurs
if 'director' in df.columns:
    st.subheader("Réalisateurs ayant le plus de films dans le Top 250")
    top_dir = df['director'].value_counts().head(10)
    st.dataframe(top_dir)

# 12. Analyse de la “starification” acteurs
if 'actors' in df.columns:
    st.subheader("Acteurs ayant le plus de films dans le Top 250")
    top_act = actors.value_counts().head(10)
    st.dataframe(top_act)

# Filtres dynamiques
st.sidebar.header("Filtres dynamiques")
min_year, max_year = int(df['year'].min()), int(df['year'].max())
year_range = st.sidebar.slider("Année", min_year, max_year, (min_year, max_year))
min_rating, max_rating = float(df['rating'].min()), float(df['rating'].max())
rating_range = st.sidebar.slider("Note", min_rating, max_rating, (min_rating, max_rating))
genres_list = sorted(all_genres.unique()) if 'genres' in df.columns else []
genre_filter = st.sidebar.multiselect("Genre", genres_list)
title_search = st.sidebar.text_input("Recherche par titre")

filtered = df[(df['year']>=year_range[0]) & (df['year']<=year_range[1]) &
              (df['rating']>=rating_range[0]) & (df['rating']<=rating_range[1])]
if genre_filter:
    filtered = filtered[filtered['genres'].apply(lambda g: any(gen in g for gen in genre_filter) if isinstance(g, str) else False)]
if title_search:
    filtered = filtered[filtered['title'].str.contains(title_search, case=False, na=False)]

st.subheader("Tableau des films filtrés")
colonnes_possibles = ['title','year','rating','genres','director','duration']
colonnes_affichees = [col for col in colonnes_possibles if col in filtered.columns]
st.dataframe(filtered[colonnes_affichees].sort_values('rating',ascending=False))

# Export CSV
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("Exporter les données filtrées en CSV", csv, "imdb_top250_filtre.csv", "text/csv")

# Export Excel
excel_buffer = BytesIO()
filtered.to_excel(excel_buffer, index=False)
st.download_button("Exporter en Excel", excel_buffer.getvalue(), "imdb_top250_filtre.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.sidebar.markdown("---")
st.sidebar.write("🌗 Pour le mode sombre/clair, utilisez les options de Streamlit dans le menu principal (en haut à droite)")

st.success("Dashboard ultra-complet prêt à l'emploi ! Pour toute fonctionnalité avancée supplémentaire, demandez-moi.")
