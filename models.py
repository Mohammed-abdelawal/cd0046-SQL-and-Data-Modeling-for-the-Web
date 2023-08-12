from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import ARRAY

db = SQLAlchemy()


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    genres = db.Column(ARRAY(db.String(255), dimensions=1))
    # genres = db.Column(MutableList.as_mutable(ARRAY(db.String(255))), default=[])
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy="joined")


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    genres = db.Column(ARRAY(db.String(255), dimensions=1))
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy="joined")


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(timezone=True))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
