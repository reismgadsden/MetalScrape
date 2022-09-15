import json
import time
from os.path import exists
import numpy
import pandas
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
import urllib.parse

class MetalWrangle:
    _df = None
    _cid = ""
    _scid = ""
    _spotify = ""

    def __init__(self, filename, cid, scid, letter):
        scraped = ""

        try:
            with open(filename, "r") as file:
                scraped = json.load(file)
        except FileNotFoundError:
            print("The json does not exist.")
            exit()

        self._cid = cid
        self._scid = scid

        self.authorize_spotify()

        if exists("spotify_artists_by_" + letter + ".csv"):
            self._df = pandas.read_csv("spotify_artists_by_" + letter + ".csv", index_col=0)
        else:
            self.build_df(scraped)
            self.append_country_codes()
            self.spotify_artist_search()
            self._df.to_csv("spotify_artists_by_" + letter + ".csv")

        if exists("compiled_artists_by_" + letter + ".csv"):
            self.df = pandas.read_csv("compiled_artists_by_" + letter + ".csv", index_col=0)
        else:
            self.get_top_tracks()
            self._df.to_csv("compiled_artists_by_" + letter + ".csv")

    def build_df(self, json_info):
        data = {
            "Band name": [],
            "Country of origin": [],
            "Location": [],
            "Status": [],
            "Formed in": [],
            "Years active": [],
            "Genre": [],
            "Lyrical themes": [],
            "Current/Last label": [],
            "Discography": []
        }

        for x in json_info:
            for y in json_info[x]:
                if y != "Discography" and y!= "Genre":
                    if json_info[x][y] == "N/A":
                        data[y].append(None)
                        continue
                    data[y].append(json_info[x][y])
                elif y == "Genre":
                    split = json_info[x][y].split("/")
                    if split == [""]:
                        data[y].append(None)
                    else:
                        data[y].append(", ".join(split))
                else:
                    disco = []
                    for z in json_info[x][y]:
                        disco.append(z["Name"])
                    data[y].append(disco)

        self._df = pandas.DataFrame(data=data)

    # ADD COUNTRY CODE
    def append_country_codes(self):
        country_codes_csv = open("is03166Codes.csv", "r")
        country_codes = dict()
        for line in country_codes_csv:
            col = line.split(",")
            if col[0] == "Name":
                continue
            country_codes[col[0]] = col[1].strip()

        codes = []
        for index, row in self._df.iterrows():
            if row["Country of origin"] in country_codes:
                codes.append(country_codes[row["Country of origin"]])
            else:
                codes.append(None)

        self._df["Country code"] = codes

    # stuff
    def authorize_spotify(self):
        client_credentials_manager = SpotifyClientCredentials(client_id=self._cid, client_secret=self._scid)
        self._spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    # more stuff
    def spotify_artist_search(self):
        spotify_id = []
        for index, row in self._df.iterrows():
            print(index)
            skip_album = False
            skip_genre = False
            if pandas.isnull(row["Discography"]):
                skip_album = True
            if pandas.isnull(row["Genre"]):
                skip_genre = False
            error = False
            try:
                time.sleep(1)
                artists = self._spotify.search(urllib.parse.quote(row["Band name"]), limit=20, offset=0, type='artist', market=row["Country code"])
            except SpotifyException as e:
                # print(e)
                # print("Value: " + row["Country code"] + "; Type: " + str(type(row["Country code"])))
                # exit()
                error = True
            if error or artists["artists"]["total"] == 0 or pandas.isnull(row["Country code"]):
                if not pandas.isnull(row["Country code"]):
                    time.sleep(1)
                    artists = self._spotify.search(urllib.parse.quote(row["Band name"]), limit=20, offset=0, type='artist', market=None)

                if artists["artists"]["total"] == 0:
                    spotify_id.append(None)
                    continue

            if skip_genre and skip_album and artists["artists"]["total"] == 1:
                spotify_id.append(artists["artists"]["items"][0]["id"])
                continue
            else:
                found = False
                for item in artists["artists"]["items"]:
                    artist_id = item["id"]

                    if not skip_album:
                        time.sleep(1)
                        albums = self._spotify.artist_albums(artist_id, album_type=None, country=None, limit=15, offset=0)
                        for album in albums["items"]:
                            if album["name"] in row["Discography"]:
                                found = True
                                spotify_id.append(artist_id)
                                break
                    elif not skip_genre:
                        for genres in item["genres"]:
                            if genres.lower() in row["Genre"].lower().split("/"):
                                found = True
                                spotify_id.append(spotify_id)
                                break

                    if found:
                        for genres in item["genres"]:
                            if pandas.isnull(row["Genre"]) and (genres.lower() not in row["Genre"].lower().split("/")):
                                row["Genre"] += ", " + genres
                            elif pandas.isnull(row["Genre"]):
                                row["Genre"] = genres
                        break

                if not found:
                    spotify_id.append(None)

        self._df["Spotify ID"] = spotify_id

    def get_top_tracks(self):
        top_tracks = list()
        top_track_ids = list()
        top_tracks_features = list()

        for index, row in self._df.iterrows():
            print(index)
            if not pandas.isnull(row["Spotify ID"]):
                time.sleep(2)
                artist_top_tracks = self._spotify.artist_top_tracks(artist_id=row["Spotify ID"])
                if not artist_top_tracks["tracks"]:
                    top_tracks.append(None)
                    top_track_ids.append(None)
                    top_tracks_features.append(None)
                    continue
                top = []
                top_ids = []
                for item in artist_top_tracks["tracks"]:
                    top.append(item["name"])
                    top_ids.append(item["id"])

                top_features = []
                time.sleep(2)
                audio_features = self._spotify.audio_features(top_ids)
                for i in range(0, len(audio_features)):
                    try:
                        song_features = {
                            "danceability" : audio_features[i]["danceability"],
                            "energy": audio_features[i]["energy"],
                            "key": audio_features[i]["key"],
                            "loudness": audio_features[i]["loudness"],
                            "mode": audio_features[i]["mode"],
                            "speechiness": audio_features[i]["speechiness"],
                            "acousticness": audio_features[i]["acousticness"],
                            "instrumentalness": audio_features[i]["instrumentalness"],
                            "liveness": audio_features[i]["liveness"],
                            "valence": audio_features[i]["valence"],
                            "tempo": audio_features[i]["tempo"]
                        }
                        top_features.append(song_features)
                    except TypeError as e:
                        top[i] = None
                        top_ids[i] = None

                top = [t for t in top if not pandas.isnull(t)]
                top_ids = [i for i in top_ids if not pandas.isnull(i)]

                top_tracks.append(", ".join(top))
                top_track_ids.append(", ".join(top_ids))
                top_tracks_features.append(top_features)
                continue

            top_tracks.append(None)
            top_track_ids.append(None)
            top_tracks_features.append(None)

        self._df["Top tracks"] = top_tracks
        self._df["Top track IDs"] = top_track_ids
        self._df["Top track features"] = top_tracks_features

    def get_df(self):
        return self._df.copy(deep=True)


def get_wrangle(client=None, secret=None, csv=None, json=None):
    if csv is None and json is None:
        print("Must either provide a .csv or .json.")
        exit(-1)
    if json is not None and (client is None and secret is not None):
        print("Must provide credientials.")
        exit(-1)

    if exists(csv):
        return pandas.read_csv(csv, index_col=0)
    else:
        print(".csv is not readable.")
        exit(-1)

    mw = MetalWrangle(filename=json, cid=client, scid=secret)
    return mw.get_df()


# execute this stuff if the file is being executed directly and not imported
if __name__ == "__main__":

    # needed credentials for spotify api
    client_id = ""
    client_secret = ""

    # json file from MetalScrape.py
    filename = "metal-scrape-reis-gadsden_by_R.json"
    letter = 'R'

    # create our new MetalWrangle object
    mw = MetalWrangle(filename=filename, cid=client_id, scid=client_secret, letter=letter)