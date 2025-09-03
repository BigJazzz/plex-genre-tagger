import os
import sys
import time
from plexapi.server import PlexServer
from tmdbv3api import TMDb, Movie, TV, Search

# --- Configuration ---
# Plex connection details (replace with your own or use environment variables)
PLEX_URL = os.environ.get('PLEX_URL', 'http://plex:32400')
PLEX_TOKEN = os.environ.get('PLEX_TOKEN', '')

# TMDB API Key (replace with your own or use an environment variable)
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')

# Sync mode ('update' or 'full-sync')
# 'update': Only adds genres to items that have none.
# 'full-sync': Overwrites existing genres with fresh data from TMDB.
SYNC_MODE = os.environ.get('SYNC_MODE', 'update').lower()

# --- Initialize APIs ---
try:
    tmdb = TMDb()
    tmdb.api_key = TMDB_API_KEY
    tmdb.language = 'en'
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
except Exception as e:
    print(f"Error initializing APIs: {e}")
    sys.exit(1)

def get_tmdb_genres(item, item_type):
    """
    Fetches genres for a given media item from TMDB.
    """
    try:
        search = Search()
        tmdb_movie = Movie()
        tmdb_tv = TV()

        if item_type == 'movie':
            results = search.movies(f"{item.title} {item.year}")
            if results:
                details = tmdb_movie.details(results[0].id)
                return [genre['name'] for genre in details.genres]
        elif item_type == 'show':
            # Adding year to the search query often improves accuracy for shows with remakes
            results = search.tv_shows(f"{item.title} {item.year}")
            if not results: # Fallback to title only if no results with year
                results = search.tv_shows(item.title)
            if results:
                details = tmdb_tv.details(results[0].id)
                return [genre['name'] for genre in details.genres]
    except Exception as e:
        print(f"  - Could not fetch TMDB genres for '{item.title}': {e}")
    return []

def update_plex_genres():
    """
    Scans Plex libraries and updates genres based on the SYNC_MODE.
    """
    print(f"Starting genre tagger in '{SYNC_MODE}' mode.")
    try:
        print("Fetching all libraries from Plex server...")
        all_libraries = plex.library.sections()
        
        for library in all_libraries:
            if library.type not in ['movie', 'show']:
                print(f"\nSkipping library '{library.title}' (type: {library.type}).")
                continue

            print(f"\nConnecting to Plex library: '{library.title}'...")
            item_type = 'movie' if library.type == 'movie' else 'show'

            print(f"Scanning {len(library.all())} items...")
            for item in library.all():
                print(f"\nProcessing: {item.title} ({getattr(item, 'year', 'N/A')})")

                existing_genres = [genre.tag for genre in item.genres]

                # In 'update' mode, skip items that already have genres.
                if SYNC_MODE == 'update' and existing_genres:
                    print(f"  - Item already has genres. Skipping in 'update' mode.")
                    continue

                tmdb_genres = get_tmdb_genres(item, item_type)

                if not tmdb_genres:
                    print(f"  - No genres found on TMDB for '{item.title}'. Skipping.")
                    continue

                # In 'full-sync' mode, skip if genres are already identical.
                if SYNC_MODE == 'full-sync' and set(existing_genres) == set(tmdb_genres):
                    print(f"  - Genres are already up-to-date for '{item.title}'.")
                    continue

                if SYNC_MODE == 'full-sync':
                    print(f"  - [Full Sync] Overwriting genres.")
                    print(f"  - Existing Genres: {existing_genres}")
                    print(f"  - New TMDB Genres: {tmdb_genres}")
                    # Clear existing genres and add the new ones
                    item.edit(**{'genre.locked': 0, 'genre.clear': 1})
                    item.reload()
                    item.addGenre(tmdb_genres, locked=False)
                    item.reload()
                    print(f"  - Successfully updated genres for '{item.title}'.")
                else: # This is 'update' mode for an item with no genres
                    print(f"  - [Update] Adding new genres.")
                    print(f"  - Found TMDB Genres: {tmdb_genres}")
                    item.addGenre(tmdb_genres, locked=False)
                    item.reload()
                    print(f"  - Successfully added genres for '{item.title}'.")
                
                time.sleep(1) # Be nice to the API

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == '__main__':
    if not PLEX_URL or not PLEX_TOKEN or not TMDB_API_KEY:
        print("Error: Missing one or more required environment variables:")
        print("PLEX_URL, PLEX_TOKEN, TMDB_API_KEY")
        sys.exit(1)
        
    update_plex_genres()
    print("\nGenre tagging process completed!")

