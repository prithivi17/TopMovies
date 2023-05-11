from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ.get("API_KEY")
URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_IMG_URL = "https://image.tmdb.org/t/p/w500/"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=True, unique=True)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(80), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(20), nullable=True)
    img_url = db.Column(db.String(80), nullable=True)


with app.app_context():
    db.create_all()


class UpdateForm(FlaskForm):
    new_rating = StringField("Your rating out of 10 e.g 7.5")
    new_review = StringField("Your review")
    submit = SubmitField("Done")


class AddForm(FlaskForm):
    movie_title = StringField("Movie Title", validators=[DataRequired()])
    add = SubmitField("Add Movie")


@app.route("/", methods=['POST', 'GET'])
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['POST', 'GET'])
def edit():
    form = UpdateForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.new_rating.data)
        movie.review = form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['POST', 'GET'])
def add():
    form = AddForm()
    if request.method == "POST":
        if form.validate_on_submit():
            title = form.movie_title.data
            parameters = {
                "api_key": API_KEY,
                "query": title
            }
            response = requests.get(url=URL, params=parameters)
            result = response.json()["results"]
            return render_template('select.html', option=result)

    return render_template('add.html', form=form)


@app.route('/find')
def find():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_INFO_URL}/{movie_api_id}"
        parameters = {
            "api_key": API_KEY,
            "language": "en-US"
        }
        response = requests.get(url=movie_api_url, params=parameters)
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_IMG_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
