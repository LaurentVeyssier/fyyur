from models import db, Venue, Artist, Show, app
import json


# Load JSON data
with open("venues.json") as f:
    venues_data = json.load(f)

with open("artists.json") as f:
    artists_data = json.load(f)

with open("shows.json") as f:
    shows_data = json.load(f)

with app.app_context():
    for v in venues_data:
        # Check if venue already exists (by name + city + state)
        existing = Venue.query.filter_by(
            name=v.get("name"),
            city=v.get("city"),
            state=v.get("state")
        ).first()

        if existing:
            print(f"Skipping existing venue: {v.get('name')} ({v.get('city')}, {v.get('state')})")
            continue

        # Parse capacity if numeric
        capacity_val = None
        if v.get("capacity"):
            to_process = v.get("capacity").split(" ")
            numbers = [''.join(filter(str.isdigit, str(i))) for i in to_process]
            if numbers:
                capacity_val = max(numbers)
            else:
                capacity_val = None

        # Create and add new venue
        venue = Venue(
            name=v.get("name"),
            city=v.get("city"),
            state=v.get("state"),
            address=v.get("address"),
            phone=v.get("phone"),
            image_link=v.get("image_link"),
            website_link=v.get("website"),
            facebook_link=v.get("facebook_link",None),
            #description=v.get("description","") + "\n\nCapacity: " + v.get("capacity","n.a."),
            #capacity= capacity_val,
            seeking_talent=v.get("seeking_talent",False),
            seeking_description=v.get("seeking_description",None),
            genres=v.get("genres",None),

        )
        db.session.add(venue)

    for a in artists_data:
        # Check if artist already exists (by name + city + state)
        existing = Artist.query.filter_by(
            name=a.get("name"),
            city=a.get("city"),
            state=a.get("state")
        ).first()

        if existing:
            print(f"Skipping existing artist: {a.get('name')} ({a.get('city')}, {a.get('state')})")
            continue
    
        # Create and add new artist
        artist = Artist(
            name=a.get("name"),
            city=a.get("city"),
            state=a.get("state"),
            phone=a.get("phone"),
            image_link=a.get("image_link"),
            facebook_link=a.get("facebook_link",None),
            #description=a.get("description"),
            seeking_venue=a.get("seeking_venue",False),
            seeking_description=a.get("seeking_description",None),
            genres=a.get("genres",None),
            website_link=a.get("website",None),
        )
        db.session.add(artist)


    for s in shows_data:
        existing = Show.query.filter_by(
            venue_id=s.get("venue_id"),
            artist_id=s.get("artist_id"),
            start_time=s.get("start_time")
        ).first()

        if existing:
            print(f"Skipping existing show: {s.get('venue_id')} ({s.get('artist_id')}, {s.get('start_time')})")
            continue

        show = Show(
            venue_id=s.get("venue_id"),
            artist_id=s.get("artist_id"),
            start_time=s.get("start_time"),
        )
        db.session.add(show)

    db.session.commit()

    print("Database populated successfully!")