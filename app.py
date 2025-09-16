# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
from datetime import datetime
import babel
from collections import defaultdict
from flask import render_template, request, flash, redirect, url_for
import logging
from logging import Formatter, FileHandler
from sqlalchemy import text

# from flask_wtf import Form
from forms import VenueForm, ArtistForm, ShowForm
from models import Venue, Artist, Show, db, app


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    """Converts a datetime object or string to a formatted string"""
    if isinstance(value, str):
        # returns a datetime object from a str
        date = dateutil.parser.parse(value)
    else:
        # already datetime                                               #
        # ADJUSTED to allow datetime object
        date = value
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    # babel takes a datime object and returns a string
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Helper functions.
# ----------------------------------------------------------------------------#

def class_to_dict(cls):
    """
    Converts a SQLAlchemy model instance to a dictionary.
    Returns:
    Dict of key:value pairs from SQLAlchemy model instance.
    """
    return {c.key: getattr(cls, c.key) for c in cls.__table__.columns}


def show_details(show_id, image):
    """
    Converts a Show instance to a dictionary
    Args:
      show_id: int, id of the show to convert
      image: str, 'venue' or 'artist', determines which image and info to return
    Returns:
      Dict with keys artist_id, artist_name, artist_image_link, start_time.
    """
    selected_show = db.session.get(Show, show_id)
    start_time = selected_show.start_time
    artist_id = selected_show.artist_id
    artist = db.session.get(Artist, artist_id)
    artist_name = artist.name
    if image == 'venue':          # displays show details on artist page
        venue = db.session.get(Venue, selected_show.venue_id)
        venue_image_link = venue.image_link
        venue_name = venue.name
        return {
            "venue_image_link": venue_image_link,
            # allows to display the venue name in the show details on artist
            # page
            "venue_name": venue_name,
            "start_time": start_time,
            # allows to navigate to the venue page from the artist page by
            # clicking on a show venue name link
            "venue_id": selected_show.venue_id
        }
    else:  # image == 'artist':    # displays show details on venue page
        artist_image_link = artist.image_link
        return {
            # allows to navigate to the artist page from the venue page by
            # clicking on a show artist name link
            "artist_id": artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": start_time
        }


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')  # typical GET method
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
# GET method retrieves info from the back end and render it in the front end
# POST method sends info from the front end to the back end - can still involves returning a msg to the front end to confirm + the status code cf. abort(404)
# PUT method updates all request method info in the back end
# DELETE method deletes all request method info in the back end

@app.route('/venues')  # typical GET method
def venues():
    """
    Return all venues grouped by city and state with count of upcoming shows
    Returns:
      data[List[Dict[city, state, venues[List[Dict]]]]]
    """
    # get all venues
    all_venues = Venue.query.all()
    # group by (city, state) and serialize using class_to_dict
    grouped = defaultdict(list)
    for venue in all_venues:
        grouped[(venue.city, venue.state)].append(class_to_dict(venue))
    data = []
    # reformat into List[Dict[city, state, venues[List[Dict]]]]
    for city, state in grouped.keys():
        list_venues = grouped[city, state]
        # count upcoming shows for each venue
        for venue in list_venues:
            venue['num_upcoming_shows'] = Show.query.filter_by(
                venue_id=venue['id']).filter(
                Show.start_time > datetime.now()).count()
        data.append({"city": city, "state": state, "venues": list_venues})

    return render_template('pages/venues.html', areas=data)

#  search Venue
#  ----------------------------------------------------------------


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live
    # Music & Coffee"
    search_term = request.form.get('search_term', '')
    matches = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    matches = [{"id": match.id, "name": match.name, "num_upcoming_shows": Show.query.filter_by(
        venue_id=match.id).filter(Show.start_time >= datetime.now()).count()} for match in matches]
    response = {
        "count": len(matches),
        "data": matches
    }
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))

#  display Venue
#  ----------------------------------------------------------------


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """
    Return venue details with past and upcoming shows
    Returns:
      data[Dict[venue, past_shows[List[Dict]], upcoming_shows[List[Dict]], past_shows_count[int], upcoming_shows_count[int]]]
    """
    venue = db.session.get(Venue, venue_id)
    past_shows = Show.query.filter_by(
        venue_id=venue_id).filter(
        Show.start_time < datetime.now()).order_by(
            Show.start_time).all()
    upcoming_shows = Show.query.filter_by(
        venue_id=venue_id).filter(
        Show.start_time >= datetime.now()).order_by(
            Show.start_time).all()
    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)
    # extract artist details from shows
    if upcoming_shows:
        upcoming_shows = [show_details(show.id, 'artist')
                          for show in upcoming_shows]
    if past_shows:
        past_shows = [show_details(show.id, 'artist') for show in past_shows]

    data = class_to_dict(venue)
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = past_shows_count
    data['upcoming_shows_count'] = upcoming_shows_count
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    # called to display the form to create a new venue
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # called to create new venue in the db with the form data
    form = VenueForm()
    if form.validate_on_submit():
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                address=form.address.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website_link=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(new_venue)
            db.session.commit()
            flash(f'Venue {form.name.data} was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash(
                f'An error occurred. Venue {
                    form.name.data} could not be listed. Error: {
                    str(e)}')
        finally:
            db.session.close()
    else:
        flash(f"correct the following errors: {form.errors}")
    # on unsuccessful db insert, flash an error message.
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


#  Update Venue
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # called with GET request to load the form with the current venue data
    form = VenueForm()
    venue = db.session.get(Venue, venue_id)
    if venue is None:
        flash('An error occurred. Venue not found.')
        abort(404)
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # called with POST request to update a venue's data with the form data
    form = VenueForm()
    if form.validate_on_submit():
        try:
            venue = db.session.get(Venue, venue_id)
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.genres = form.genres.data
            venue.facebook_link = form.facebook_link.data
            venue.image_link = form.image_link.data
            venue.website_link = form.website_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            db.session.commit()
            flash('Venue ' + venue.name + ' was successfully updated!')
        except BaseException:
            flash(
                'An error occurred. Venue ' +
                form.name.data +
                ' could not be updated.')
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash(f"correct the following errors: {form.errors}")
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Delete Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # called with DELETE request to delete a venue
    try:
        venue = db.session.get(Venue, venue_id)
        if venue is None:
            flash('An error occurred. Venue not found.')
            abort(404)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully deleted!')
    except BaseException:
        db.session.rollback()
        flash(
            'An error occurred. Venue ' +
            venue.name +
            ' could not be deleted.')
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the
    # homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)

#  search Artist
#  ----------------------------------------------------------------


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    matches = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    matches = [{"id": match.id, "name": match.name, "num_upcoming_shows": Show.query.filter_by(
        artist_id=match.id).filter(Show.start_time >= datetime.now()).count()} for match in matches]

    response = {
        "count": len(matches),
        "data": matches
    }

    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


#  display Artist
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """
    Return artist details with past and upcoming shows
    Returns:
      data[Dict[artist, past_shows[List[Dict]], upcoming_shows[List[Dict]], past_shows_count[int], upcoming_shows_count[int]]]
    """
    artist = db.session.get(Artist, artist_id)
    past_shows = Show.query.filter_by(
        artist_id=artist_id).filter(
        Show.start_time < datetime.now()).order_by(
            Show.start_time).all()
    upcoming_shows = Show.query.filter_by(
        artist_id=artist_id).filter(
        Show.start_time >= datetime.now()).order_by(
            Show.start_time).all()
    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)
    # extract artist details from shows
    if upcoming_shows:
        upcoming_shows = [show_details(show.id, 'venue')
                          for show in upcoming_shows]
    if past_shows:
        past_shows = [show_details(show.id, 'venue') for show in past_shows]

    data = class_to_dict(artist)
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = past_shows_count
    data['upcoming_shows_count'] = upcoming_shows_count

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    # called with GET request to load the form with the current artist data
    form = ArtistForm()
    artist = db.session.get(Artist, artist_id)
    if artist is None:
        flash('An error occurred. Artist not found.')
        abort(404)
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # called with POST request to update a artist's data with the form data
    form = ArtistForm()
    if form.validate_on_submit():
        try:
            artist = db.session.get(Artist, artist_id)
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.genres = form.genres.data
            artist.facebook_link = form.facebook_link.data
            artist.image_link = form.image_link.data
            artist.website_link = form.website_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            db.session.commit()
            flash('Artist ' + artist.name + ' was successfully updated!')
        except BaseException:
            flash(
                'An error occurred. Artist ' +
                form.name.data +
                ' could not be updated.')
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash(f"correct the following errors: {form.errors}")
    return redirect(url_for('show_artist', artist_id=artist_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    form = ArtistForm()
    if form.validate_on_submit():
        try:
            new_artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website_link=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(new_artist)
            db.session.commit()
            flash('Artist ' + form.name.data + ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash(
                f'An error occurred. Artist {
                    form.name.data} could not be listed. Error: {
                    str(e)}')
        finally:
            db.session.close()
    else:
        flash(f"correct the following errors: {form.errors}")
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows = Show.query.order_by(Show.start_time).all()
    shows = [class_to_dict(show) for show in shows]
    data = []
    for show in shows:

        # option 1: cleanest one-liner
        show['venue_name'] = db.session.get(Venue, show['venue_id']).name

        # option 2 : significantly more complicated
        """show['venue_name'] = (
    db.session.query(Venue.name)
    .join(Show, Show.venue_id == Venue.id)
    .filter(Show.id == show.id)
    .scalar()
    )"""

        '''# option 3 : raw sql style using sql text
    sql = text("""
    SELECT v.name
    FROM "Venue" v
    JOIN "Show" s ON s.venue_id = v.id
    WHERE s.id = :show_id
    """)
    show['venue_name'] = db.session.execute(sql, {"show_id": show['id']}).fetchone()'''

        del show['id']
        show['artist_name'] = db.session.get(Artist, show['artist_id']).name
        show['artist_image_link'] = db.session.get(
            Artist, show['artist_id']).image_link
        data.append(show)

    return render_template('pages/shows.html', shows=data)

#  Create Show
#  ----------------------------------------------------------------


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing
    # form
    form = ShowForm()  # request.form
    if form.validate_on_submit():
        try:
            new_show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data
            )
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash(
                f'An error occurred. Show could not be listed. Error: {
                    str(e)}')
        finally:
            db.session.close()
    else:
        flash(f"correct the following errors: {form.errors}")
    return render_template('pages/home.html')


#  Error handlers
#  ----------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()  # running in debug mode from the config file

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
