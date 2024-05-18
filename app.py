import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import dotenv_values
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

env_vars = dotenv_values(".env")

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=env_vars["SPOTIFY_CLIENT_ID"],
        client_secret=env_vars["SPOTIFY_CLIENT_SECRET"],
        redirect_uri="http://localhost:3000",
        scope="user-library-read",
    )
)

likedTracks = sp.current_user_saved_tracks()
spotifySongs = []

for item in likedTracks["items"]:
    track = item["track"]
    print(track["name"], "-", track["artists"][0]["name"])
    spotifySongs.append(track["name"] + " " + track["artists"][0]["name"])


credentials_file = "youtube_credentials.json"
if os.path.exists(credentials_file):
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file, scopes=["https://www.googleapis.com/auth/youtube"]
    )
    credentials = flow.run_local_server()
    with open(credentials_file, "w") as f:
        f.write(credentials.to_json())
else:
    credentials = os.environ.get("YOUTUBE_OAUTH2_CREDENTIALS")
    if credentials:
        credentials = json.loads(credentials)
    else:
        print(
            "Please provide the path to your YouTube OAuth2 credentials file or set the 'YOUTUBE_OAUTH2_CREDENTIALS' environment variable."
        )
        exit(1)


youtube = build("youtube", "v3", credentials=credentials)

playlistTitle = "Liked Songs"
playlistDesc = "Playlist of liked songs from Spotify"


try:
    playlist = (
        youtube.playlists()
        .insert(
            part="snippet,status",
            body=dict(
                snippet=dict(title=playlistTitle, description=playlistDesc),
                status=dict(
                    privacyStatus="private"  # Change this to 'public' if you want the playlist to be public
                ),
            ),
        )
        .execute()
    )

    playlist_id = playlist["id"]
    print(f'Playlist "{playlistTitle}" created successfully with ID: {playlist_id}')

    for song in spotifySongs:
        searchResponse = (
            youtube.search().list(q=song, part="id", type="video").execute()
        )

        if searchResponse["items"]:
            videoId = searchResponse["items"][0]["id"]["videoId"]
            youtube.playlistItems().insert(
                part="snippet",
                body=dict(
                    snippet=dict(
                        playlistId=playlist_id,
                        resourceId=dict(kind="youtube#video", videoId=videoId),
                    )
                ),
            ).execute()
            print(f'Song "{song}" added to the playlist.')
        else:
            print(f'Song "{song}" not found on YouTube.')
except HttpError as e:
    print(f"An HTTP error occurred: {e}")
