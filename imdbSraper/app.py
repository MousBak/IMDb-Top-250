from flask import Flask, render_template
from database.mongo import get_all_movies

app = Flask(__name__)

@app.route('/')
def index():
    # Récupérer tous les films depuis MongoDB
    movies = get_all_movies()
    nb_movies = len(movies)
    # Exemple d'analyse : note moyenne
    ratings = [float(m['rating']) for m in movies if m.get('rating') not in (None, '', 'N/A')]
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
    else:
        avg_rating = 0
    return render_template('index.html', nb_movies=nb_movies, avg_rating=avg_rating)

if __name__ == '__main__':
    app.run(debug=True)
