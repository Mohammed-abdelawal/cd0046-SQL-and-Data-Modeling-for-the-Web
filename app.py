import logging
import sys
from logging import Formatter, FileHandler

from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    abort,
)
from flask_migrate import Migrate
from flask_moment import Moment
from sqlalchemy import func
from utils import format_datetime
from forms import *
from models import db, Venue, Artist, Show
from flask_wtf.csrf import CSRFProtect

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
csrf = CSRFProtect(app)

db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#
app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues', methods=['GET'])
def venues():
    # data = Venue.query.group_by('venue.city', 'venue.state').all()
    data = Venue.query \
        .with_entities(Venue.city, Venue.state, Venue.name, Venue.id, func.count(Venue.id)) \
        .group_by(Venue.city, Venue.state, Venue.name, Venue.id).all()
    areas = list(set([(d.city, d.state) for d in data]))
    data = [
        {
            'city': area[0],
            'state': area[1],
            'venues': [{
                'id': d.id,
                'name': d.name,
                'num_upcoming_shows': d[4]
            } for d in data if d.city == area[0] and d.state == area[1]]
        } for area in areas
    ]

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    data = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).with_entities(Venue.id, Venue.name).all()
    # select fields in db scope better than in python scope
    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)

    past_shows = []
    upcoming_shows = []

    for show in venue.shows:
        temp_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    # object class to dict
    data = vars(venue)

    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    obj_id = 0
    if not form.validate_on_submit():
        flash(form.errors, 'error')
        return render_template('forms/new_venue.html', form=form)
    form_data = form.data.copy()
    form_data.pop('csrf_token', None)
    try:
        obj = Venue(**form_data)
        db.session.add(obj)
        db.session.commit()
        flash(f'Venue {obj.name}  was successfully listed!')
        obj_id = obj.id

    except:
        db.session.rollback()
        print(sys.exc_info())
        # on successful db insert, flash success
        flash('An error occurred. Venue could not be listed.', 'error')

    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=obj_id))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    name = str(venue.name)
    try:
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue {name} was successfully deleted!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(f'An error occurred. Venue {name} could not be deleted.', 'error')
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    data = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)

    past_shows = []
    upcoming_shows = []

    for show in artist.shows:
        temp_show = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    # object class to dict
    data = vars(artist)

    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    form = ArtistForm(formdata=request.form, obj=artist)
    if not form.validate_on_submit():
        flash(form.errors, category='error')
        return render_template('forms/edit_artist.html', form=form, artist=artist)
    try:
        form.populate_obj(artist)
        db.session.add(artist)
        db.session.commit()
        flash(f'Artist {artist.name} was successfully updated!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(f'An error occurred. Artist {artist.name} could not be updated.', 'error')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(formdata=request.form)
    if not form.validate_on_submit():
        flash(form.errors, category='error')
        return render_template('forms/edit_venue.html', form=form, venue=venue)
    try:
        form.populate_obj(venue)
        db.session.commit()
        flash(f'Venue {venue.name} was successfully updated!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(f'An error occurred. Venue {venue.name} could not be updated.', 'error')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(formdata=request.form)
    obj_id = 0
    name = ''
    if not form.validate_on_submit():
        flash(form.errors, category='error')
        return render_template('forms/new_artist.html', form=form)
    form_data = form.data.copy()
    form_data.pop('csrf_token', None)
    try:
        artist = Artist(**form_data)
        db.session.add(artist)
        db.session.commit()
        flash(f'Artist {name} was successfully listed!')
        obj_id = artist.id
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(f'An error occurred. Artist {name} could not be listed.', 'error')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=obj_id))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = Show.query.join(Artist).join(Venue).with_entities(
        Show.venue_id, Venue.name.label('venue_name'), Show.artist_id, Artist.name.label('artist_name'),
        Artist.image_link.label('artist_image_link'), Show.start_time).all()

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create', methods=['GET'])
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(formdata=request.form)
    obj_id = 0
    if not form.validate_on_submit():
        flash(form.errors, category='error')
        return render_template('forms/new_show.html', form=form)
    form_data = form.data.copy()
    form_data.pop('csrf_token', None)
    try:
        show = Show(**form_data)
        db.session.add(show)
        db.session.commit()
        flash(f'Show was successfully listed!')
        obj_id = show.id
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(f'An error occurred. Show could not be listed.', 'error')
    finally:
        db.session.close()
    return redirect(url_for('shows'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
