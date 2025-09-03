# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# We will install them directly here for simplicity
RUN pip install --no-cache-dir plexapi tmdbv3api

# Define environment variables (can be overridden at runtime)
ENV PLEX_URL=""
ENV PLEX_TOKEN=""
ENV TMDB_API_KEY=""
ENV SYNC_MODE="update"

# Run plex_genre_tagger.py when the container launches
CMD ["python", "plex_genre_tagger.py"]
