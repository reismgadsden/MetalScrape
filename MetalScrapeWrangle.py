"""
Takes data scraped from MetalScrape.py and gathers Spotify information
on any artists that can be found on there.

author: Reis Gadsden 2022-09-09
modified: 2022-09-16
git: https://github.com/reismgadsden/MetalScrape
"""

"""
IMPORTS
"""
import json
import time
from os.path import exists
import numpy
import pandas
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
import urllib.parse


"""
Class that contains all our methods and values for the wrangle.
"""
class MetalWrangle:
    # dataframe
    _df = None

    # client id
    _cid = ""

    # secret client id
    _scid = ""

    # will hold the spotipy object
    _spotify = ""

    """
    Constructor for a MetalScrapeWrangle object.
    
    param:
        filename - json file to be loaded
        cid - client id
        scid - secret client id
        letter - the letter that was scraped for naming purposes
    """
    def __init__(self, filename, cid, scid, letter):

        # will hold our json data if it can be loaded
        scraped = ""

        # attempt to load the json, abort if we cant
        try:
            with open(filename, "r") as file:
                scraped = json.load(file)
        except FileNotFoundError:
            print("The json does not exist.")
            exit()

        # set our private client id fields
        self._cid = cid
        self._scid = scid

        # authenticate our spotify api account
        self.authorize_spotify()

        # will attempt to load an existing csv first
        if exists("spotify_artists_by_" + letter + ".csv"):
            self._df = pandas.read_csv("spotify_artists_by_" + letter + ".csv", index_col=0)
        else:
            self.build_df(scraped)
            self.append_country_codes()
            self.spotify_artist_search()
            self._df.to_csv("spotify_artists_by_" + letter + ".csv")

        # will attempt to load an existing first
        if exists("compiled_artists_by_" + letter + ".csv"):
            self.df = pandas.read_csv("compiled_artists_by_" + letter + ".csv", index_col=0)
        else:
            self.get_top_tracks()
            self._df.to_csv("compiled_artists_by_" + letter + ".csv")

    """
    Build a pandas DataFrame with data from MetalScrape.py
    
    param:
        json_info - our dictionary from loading a json
    """
    def build_df(self, json_info):

        # create a dict with our column names and empty containers for data
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

        # loop over each object in the json object
        for x in json_info:

            # access the fields in the json object
            for y in json_info[x]:

                # discography and genres will need to be treated differently
                if y != "Discography" and y!= "Genre":

                    # if it is "N/A"
                    if json_info[x][y] == "N/A":
                        data[y].append(None)
                        continue
                    data[y].append(json_info[x][y])

                # condition for genre
                elif y == "Genre":
                    # sometimes multiple genres are listed
                    # ex: genre1/genre2
                    # we need to split these so they can be formatted
                    # genre1, genre2, ..., genreN
                    split = json_info[x][y].split("/")

                    # if our split is empty we do not have a genre
                    if split == [""]:
                        data[y].append(None)

                    # otherwise join each element into a single string
                    else:
                        data[y].append(", ".join(split))

                # condition for discography
                else:

                    # we want to hold this in a list so that we can
                    # iterate over it
                    disco = []

                    # for each object in the discography only grab its name
                    for z in json_info[x][y]:
                        disco.append(z["Name"])
                    data[y].append(disco)

        # construct a pandas DataFrame with our data
        self._df = pandas.DataFrame(data=data)

    """
    Appends a ISO-3166 country code to each artist where
    location data was given. We do this because we want to
    narrow the scope of our spotify search since multiple
    artists can use the same name.
    """
    def append_country_codes(self):
        # open our csv and construct a dictionary where
        # the key is the full name and the value is the code
        country_codes_csv = open("is03166Codes.csv", "r")
        country_codes = dict()
        for line in country_codes_csv:
            col = line.split(",")
            if col[0] == "Name":   # skips the line if it is the header line
                continue
            country_codes[col[0]] = col[1].strip()

        # list to store our column data in
        codes = []

        # iterate over each row, get the country of origin
        # if they have one, and get its country code
        for index, row in self._df.iterrows():

            # condition if country of origin is in the dict
            if row["Country of origin"] in country_codes:
                codes.append(country_codes[row["Country of origin"]])

            # condtion if country of origin isnt in the dict or is empty
            else:
                codes.append(None)

        # add the new column
        self._df["Country code"] = codes

    """
    Authorizes our API calls
    """
    def authorize_spotify(self):
        client_credentials_manager = SpotifyClientCredentials(client_id=self._cid, client_secret=self._scid)
        self._spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    """
    This method will attempt to find the artist on spotify using 3 different methods.
        1. If the result only returns one item and our row has no discography or genres
           assume that item is the artist.
        2. If the row has a discography and we get > 1 result returned, compare discographies
           of the results and see if we have matches.
        3. Finally if we have no albums but several matches attempt the same comparison accept with
           genres. This method will be the most inaccurate.
    """
    def spotify_artist_search(self):

        # empty to list to hold our artist ids
        spotify_id = []

        # loop over each row of the dataframe
        for index, row in self._df.iterrows():

            # print the index to show progress
            print(index)

            # boolean values for comparison methods
            skip_album = False
            skip_genre = False

            # set skip_album (this is bad coding)
            if pandas.isnull(row["Discography"]):
                skip_album = True
            if pandas.isnull(row["Genre"]):
                skip_genre = True
            """
            the above values should have been set like so if I was good
            
            skip_album = pandas.isnull(row["Discography"])
            skip_genre = pandas.isnull(row["Genre"])
            
            alternatively instead of creating these values here we could
            have just used pandas.isnull(row[xxx]) in each spot where we
            used one the skip_xxx variables
            """

            # boolean value that lets us now if our first query returns an error
            # this happens because not every ISO-3166 code is registered in spotify
            # as a valid market.
            error = False
            try:

                # sleep to avoid 429 error (too many requests)
                time.sleep(1)

                # attempt to grab the 20 artists matching our band's name based of market
                # throws SpotifyException if the country code is an invalid market
                artists = self._spotify.search(urllib.parse.quote(row["Band name"]), limit=20, offset=0, type='artist', market=row["Country code"])
            except SpotifyException as e:
                # print(e)
                # print("Value: " + row["Country code"] + "; Type: " + str(type(row["Country code"])))
                # exit()
                error = True

            # this will reattempt to find the artist by not limiting the market
            if error or artists["artists"]["total"] == 0 or pandas.isnull(row["Country code"]):
                if not pandas.isnull(row["Country code"]):

                    # sleep to avoid 429 error (too many requests)
                    time.sleep(1)

                    # make a API call with the spotipy wrapper object
                    artists = self._spotify.search(urllib.parse.quote(row["Band name"]), limit=20, offset=0, type='artist', market=None)

                # if this result returns no artists we append None and start at the next row
                if artists["artists"]["total"] == 0:
                    spotify_id.append(None)
                    continue

            # condition 1
            if skip_genre and skip_album and artists["artists"]["total"] == 1:

                # appends the id from the first (and only) item returned
                spotify_id.append(artists["artists"]["items"][0]["id"])

                # restart the loop on the next row
                continue
            else:

                # boolean value that will tell whether we found the artist or not
                found = False

                # gets the spotify ids for each artist returned by API
                for item in artists["artists"]["items"]:
                    artist_id = item["id"]

                    # condtion 2
                    # if the row has discography, query the api for at most 15 albums from each artist
                    # this only gets the albums for one artist at a time so we dont end up making
                    # unnecessary calls
                    if not skip_album:

                        # sleep to avoid 429 error (too many requests)
                        time.sleep(1)

                        # gets up to 15 albums from an artist from an artist id
                        albums = self._spotify.artist_albums(artist_id, album_type=None, country=None, limit=15, offset=0)

                        # loop over each item in the returned result and see if the
                        # name of an album is present within or discography list
                        for album in albums["items"]:

                            # if there is a match we set our found value to true
                            # and break out of the loop as we do not need to make sure
                            # all things match
                            if album["name"] in row["Discography"]:
                                found = True
                                spotify_id.append(artist_id)
                                break

                    # condition 3
                    elif not skip_genre:

                        # loop over each item in the genres and compare
                        for genres in item["genres"]:
                            if genres.lower() in row["Genre"].lower().split("/"):
                                found = True
                                spotify_id.append(spotify_id)
                                break

                    # stuff to do only if we found a match
                    if found:

                        # loop over each genre in the returned result
                        for genres in item["genres"]:

                            # append genre with comma and space before if we have no data in the genre
                            # column or the genre is not already present in said column
                            # we dont need to split on a / anymore but it does not break functionality
                            if pandas.isnull(row["Genre"]) and (genres.lower() not in row["Genre"].lower().split("/")):
                                row["Genre"] += ", " + genres

                            # if the column value is empty we just set it to the first genre
                            elif pandas.isnull(row["Genre"]):
                                row["Genre"] = genres

                        # start the loop over on the next row
                        break

                # if we got results back but did not find a match we need to append None
                # so that the dataframe has an empty value for that row
                if not found:
                    spotify_id.append(None)

        # set the row equal to our now populated list
        self._df["Spotify ID"] = spotify_id

    """
    Gets the top (at most 10) tracks for each artist that we were able to find,
    and gets the names, ids, and audio features for each one.
    """
    def get_top_tracks(self):

        # lists to hold our new column(s) data
        top_tracks = list()
        top_track_ids = list()
        top_tracks_features = list()

        # loop over each row of the dataframe
        for index, row in self._df.iterrows():

            # print the index to show progress
            print(index)

            # we want to skip over rows where there is no artist id
            if not pandas.isnull(row["Spotify ID"]):

                # sleep to avoid 429 error (too many requests)
                time.sleep(2)

                # query the api for an artists top tracks
                artist_top_tracks = self._spotify.artist_top_tracks(artist_id=row["Spotify ID"])

                # if the returned result is empty
                if not artist_top_tracks["tracks"]:

                    # since the result is empty we just want have an empty cell for these values
                    # so we append a None
                    top_tracks.append(None)
                    top_track_ids.append(None)
                    top_tracks_features.append(None)

                    # start the loop over on the next row
                    continue

                # two lists to hold values for track name
                # and track id
                top = []
                top_ids = []

                # loop over the each track in the returned result and
                # append the names and ids of each track
                for item in artist_top_tracks["tracks"]:
                    top.append(item["name"])
                    top_ids.append(item["id"])

                # empty list to hold the audio features for each track
                top_features = []

                # sleep to avoid 429 error (too many requests)
                time.sleep(2)

                # API call to get the audio features for a track
                audio_features = self._spotify.audio_features(top_ids)

                # loop over the each element in the returned result
                # we do this by index so that if we get  bad result we
                # can change values at the index in our two lists that
                # hold track name and id
                for i in range(0, len(audio_features)):

                    # attempt to construct a dictionary with values from the result
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

                        # appends this dictionary to our list
                        top_features.append(song_features)

                    # sometimes a result will be none for a track
                    # im not sure why this happens as a valid track id
                    # will return None
                    except TypeError as e:

                        # set values at that index to none, we dont need to worry
                        # about appending a None to our audio features as these two
                        # lists will end up becoming single strings with each value
                        # that is not None being seperated by commas
                        top[i] = None
                        top_ids[i] = None

                # remove any none values in this list with list comprehension
                top = [t for t in top if not pandas.isnull(t)]
                top_ids = [i for i in top_ids if not pandas.isnull(i)]

                # create strings from our lists
                top_tracks.append(", ".join(top))
                top_track_ids.append(", ".join(top_ids))

                # append the entire list to the master list
                # our final list will look like:
                # list(list(dict(), dict(), ...), list(dict(), dict(), ...), ...)
                top_tracks_features.append(top_features)

                # start the loop over on the next row
                continue

            # if we do not have an id for an artist we just append None as
            # we want an empty value in that column for that row
            top_tracks.append(None)
            top_track_ids.append(None)
            top_tracks_features.append(None)

        # create new columns for each of our 3 lists
        self._df["Top tracks"] = top_tracks
        self._df["Top track IDs"] = top_track_ids
        self._df["Top track features"] = top_tracks_features

    """
    This simply returns a deep copy of our DataFrame object.
    """
    def get_df(self) -> pandas.DataFrame:
        return self._df.copy(deep=True)


"""
This public method will attempt allows us to get a complete DataFrame in another file
without having to create an instance of the class in that file. It also allows us to
pass in a csv to be loaded so if we already have a csv from running this file once
we do not have to collect the same data twice.

params:
    client - the client id (DEFAULT=None)
    secret - the secret client id (DEFAULT=None)
    csv - the name of our csv file (DEFAULT=None)
    json - the name of our json file (DEFAULT=None)
"""
def get_wrangle(client=None, secret=None, csv=None, json=None) -> pandas.DataFrame:

    # we either need a csv or json to have any data at all
    # so we abort if either of these values are empty
    if csv is None and json is None:
        print("Must either provide a .csv or .json.")
        exit(-1)

    # if we are given a json we will need to use the spotify api so
    # we need to make sure that we are given both needed client ids
    # if we arent we abort
    if json is not None and (client is None or secret is None):
        print("Must provide credientials.")
        exit(-1)

    # check if the csv given exists and if not abort
    if exists(csv):
        return pandas.read_csv(csv, index_col=0)
    else:
        print(".csv is not readable.")
        exit(-1)

    # if we are not given a csv but given the other three values
    # we will run our MetalWrangle and return the resulting DataFrame
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