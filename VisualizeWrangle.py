from datetime import datetime
import ast
import MetalScrapeWrangle as msw
import numpy
import pandas
import matplotlib.pyplot as plt
from matplotlib import patches
import seaborn
import json
import math
import random

class VisualizeWrangle:
    _df = ""
    _genres = dict()
    _colors = [
        "b",
        "g",
        "r",
        "c",
        "m",
        "y",
        "tab:purple",
        "tab:orange",
        "tab:pink",
        "tab:olive",
        "lightcoral",
        "maroon",
        "salmon",
        "coral",
        "chocolate",
        "tan",
        "goldenrod",
        "darkkhaki",
        "chartreuse",
        "palegreen",
        "lime",
        "forestgreen",
        "seagreen",
        "springgreen",
        "aquamarine",
        "lightseagreen",
        "teal",
        "lightblue",
        "steelblue",
        "midnightblue",
        "mediumpurple",
        "indigo",
        "darkorchid",
        "plum",
        "violet",
        "orchid",
        "deeppink",
        "peru"
    ]

    def __init__(self, csv=None, json_file=None, cid=None, scid=None, genres=None):
        self._df = msw.get_wrangle(csv=csv, json=json_file, client=cid, secret=scid)
        self.clean_df()

        self.build_genres()
        self.calc_genres()

        # used to get the top 10 genres by count
        # for each in self._genres:
        #     if self._genres[each]["total"] > 130:
        #         print(each + ": " + str(self._genres[each]["total"]))
        #exit()

        self.build_corr_heatmap()
        plt.clf()

        self.plot_genres_tempo_v_energy()
        plt.clf()

        self.plot_genres_danceability_v_energy()
        plt.clf()

        self.plot_genres_tempo_v_danceability()
        plt.clf()

        self.plot_acousticness_v_energy()
        plt.clf()

        self.plot_loudness_v_energy()
        plt.clf()

        self.plot_valence_v_danceability()
        plt.clf()

        if genres is not None and type(genres) is list:
            self.plot_genres_danceability_v_energy(genres)
            plt.clf()

            self.plot_genres_tempo_v_danceability(genres)
            plt.clf()

            self.plot_genres_tempo_v_energy(genres)
            plt.clf()

            self.plot_acousticness_v_energy(genres)
            plt.clf()

            self.plot_loudness_v_energy(genres)
            plt.clf()

            self.plot_valence_v_danceability(genres)
            plt.clf()

    def clean_df(self):
        self._df = self._df.loc[~self._df["Spotify ID"].isnull()]

    def build_genres(self):
        for index, row in self._df.iterrows():
            if not pandas.isnull(row["Genre"]) and not pandas.isnull(row["Top track features"]):
                for genre in row["Genre"].split(", "):
                    items = genre.lower().replace(" (early)", "").replace(" (later)", "").replace("metal", "").split(";")
                    convert_string = ast.literal_eval(row["Top track features"])
                    danceability = []
                    energy = []
                    key = []
                    loudness = []
                    mode = []
                    speechiness = []
                    acousticness = []
                    instrumentalness = []
                    liveness = []
                    valence = []
                    tempo = []
                    for i in items:
                        item = i.strip()
                        for song in convert_string:
                            danceability.append(song["danceability"])
                            energy.append(song["energy"])
                            key.append(song["key"])
                            loudness.append(song["loudness"])
                            mode.append(song["mode"])
                            speechiness.append(song["speechiness"])
                            acousticness.append(song["acousticness"])
                            instrumentalness.append(song["instrumentalness"])
                            liveness.append(song["liveness"])
                            valence.append(song["valence"])
                            tempo.append(song["tempo"])

                        if item in self._genres:
                            self._genres[item]["danceability"] += danceability
                            self._genres[item]["energy"] += energy
                            self._genres[item]["key"] += key
                            self._genres[item]["loudness"] += loudness
                            self._genres[item]["mode"] += mode
                            self._genres[item]["speechiness"] += speechiness
                            self._genres[item]["acousticness"] += acousticness
                            self._genres[item]["instrumentalness"] += instrumentalness
                            self._genres[item]["liveness"] += liveness
                            self._genres[item]["valence"] += valence
                            self._genres[item]["tempo"] += tempo
                        else:
                            new = {
                                "danceability": danceability,
                                "energy": energy,
                                "key": key,
                                "loudness": loudness,
                                "mode": mode,
                                "speechiness": speechiness,
                                "acousticness": acousticness,
                                "instrumentalness": instrumentalness,
                                "liveness": liveness,
                                "valence": valence,
                                "tempo": tempo,
                            }

                            self._genres[item] = new

    def calc_genres(self):
        for genre in self._genres:
            for each in self._genres[genre].copy():
                    self._genres[genre]["total"] = len(self._genres[genre]["mode"])
                    self._genres[genre][each + "_mean"] = sum(self._genres[genre][each]) / self._genres[genre]["total"]
                    self._genres[genre][each + "_sd"] = math.sqrt(sum([abs(x - self._genres[genre][each + "_mean"]) for x in self._genres[genre][each]]) / self._genres[genre]["total"])

    def plot_genres_tempo_v_energy(self, map_genres=None):
        show_legend = False
        if map_genres is None:
            map_genres = list(self._genres.keys())
        if len(map_genres) <= 10:
            show_legend = True
        fig, ax = plt.subplots()

        labels = []

        all_tempo = []
        tempo_means = []
        tempo_sds = []
        max_tempo = 0
        min_tempo = 1000

        all_energy = []
        energy_means = []
        energy_sds = []
        max_energy = 0
        for genre in self._genres:
            if genre.strip() in map_genres:
                labels.append(genre)
                all_tempo += self._genres[genre]["tempo"]
                tempo_means.append(self._genres[genre]["tempo_mean"])
                tempo_sds.append(self._genres[genre]["tempo_sd"])
                local_max_tempo = self._genres[genre]["tempo_mean"] + self._genres[genre]["tempo_sd"]
                if max_tempo < local_max_tempo:
                    max_tempo = local_max_tempo + self._genres[genre]["tempo_sd"]
                if min_tempo > local_max_tempo:
                    min_tempo = self._genres[genre]["tempo_mean"] - self._genres[genre]["tempo_sd"]

                all_energy += self._genres[genre]["energy"]
                energy_means.append(self._genres[genre]["energy_mean"])
                energy_sds.append(self._genres[genre]["energy_sd"])
                local_max_energy = self._genres[genre]["energy_mean"] + self._genres[genre]["energy_sd"]
                if max_energy < local_max_energy:
                    max_energy = local_max_energy

        ax.set_xlim(min_tempo, math.ceil(max_tempo))
        ax.set_ylim(0, max_energy)
        ax.set_ylabel("Energy")
        ax.set_xlabel("Tempo")
        plt.suptitle("Distribution of genres and tracks by tempo and energy", fontsize=12)
        plt.title("(Radii of circles is one standard deviation)", fontsize=8)
        circles = []
        for i in range(0, len(labels)):
            circ_color = random.choice(self._colors)
            circle = patches.Ellipse((tempo_means[i], energy_means[i]), tempo_sds[i], energy_sds[i], alpha=(1 / 3), facecolor=circ_color, edgecolor='k')
            circles.append(circle)
            ax.add_patch(circle)

        coef = numpy.polyfit(all_tempo, all_energy, 1)
        line = numpy.poly1d(coef)
        ax.plot(all_tempo, all_energy, "k.", all_tempo, line(all_tempo), "--b", markersize=2.5)

        if show_legend:
            ax.legend(circles, labels)

        # plt.show()
        current_date = str(datetime.today()).strip().replace(" ", "_").replace("-", "_").replace(":", "_")

        top = ""
        if show_legend:
            top = "top_" + str(len(map_genres)) + "_"
        plt.tight_layout()
        fig.savefig("./img_dump/genres_tempo_v_energy_" + top + current_date[0: current_date.index(".")] + ".png")

    def plot_genres_danceability_v_energy(self, map_genres=None):
        show_legend = False
        if map_genres is None:
            map_genres = list(self._genres.keys())
        if len(map_genres) <= 10:
            show_legend = True

        fig, ax = plt.subplots()

        labels = []

        all_danceability = []
        danceability_means = []
        danceability_sds = []
        max_danceability = 0

        all_energy = []
        energy_means = []
        energy_sds = []
        max_energy = 0
        for genre in self._genres:
            if genre in map_genres:
                labels.append(genre)

                all_danceability += self._genres[genre]["danceability"]
                danceability_means.append(self._genres[genre]["danceability_mean"])
                danceability_sds.append(self._genres[genre]["danceability_sd"])
                local_max_danceability = self._genres[genre]["danceability_mean"] + self._genres[genre]["danceability_sd"]
                if max_danceability < local_max_danceability:
                    max_danceability = local_max_danceability

                all_energy += self._genres[genre]["energy"]
                energy_means.append(self._genres[genre]["energy_mean"])
                energy_sds.append(self._genres[genre]["energy_sd"])
                local_max_energy = self._genres[genre]["energy_mean"] + self._genres[genre]["energy_sd"]
                if max_energy < local_max_energy:
                    max_energy = local_max_energy

        ax.set_xlim(0, max_danceability)
        ax.set_ylim(0, max_energy)
        ax.set_ylabel("Energy")
        ax.set_xlabel("Danceability")
        plt.suptitle("Distribution of genres and tracks by danceability and energy", fontsize=12)
        plt.title("(Radii of circles is one standard deviation)", fontsize=8)

        circles = []
        for i in range(0, len(labels)):
            circ_color = random.choice(self._colors)
            circle = patches.Ellipse((danceability_means[i], energy_means[i]), danceability_sds[i], energy_sds[i], alpha=(1 / 3), facecolor=circ_color, edgecolor='k')
            circles.append(circle)
            ax.add_patch(circle)

        if show_legend:
            ax.legend(circles, labels)

        coef = numpy.polyfit(all_danceability, all_energy, 1)
        line = numpy.poly1d(coef)
        ax.plot(all_danceability, all_energy, "k.", all_danceability, line(all_danceability), "--b", markersize=2.5)

        # plt.show()
        current_date = str(datetime.today()).strip().replace(" ", "_").replace("-", "_").replace(":", "_")

        top = ""
        if show_legend:
            top = "top_" + str(len(map_genres)) + "_"

        plt.tight_layout()
        fig.savefig("./img_dump/genres_danceability_v_energy_" + top + current_date[0: current_date.index(".")] + ".png")

    def plot_genres_tempo_v_danceability(self, map_genres=None):
        show_legend = False
        if map_genres is None:
            map_genres = list(self._genres.keys())
        if len(map_genres) <= 10:
            show_legend = True

        fig, ax = plt.subplots()

        labels = []

        all_tempo = []
        tempo_means = []
        tempo_sds = []
        max_tempo = 0
        min_tempo = 1000

        all_danceability = []
        danceability_means = []
        danceability_sds = []
        max_danceability = 0
        for genre in self._genres:
            if genre in map_genres:
                labels.append(genre)

                all_tempo += self._genres[genre]["tempo"]
                tempo_means.append(self._genres[genre]["tempo_mean"])
                tempo_sds.append(self._genres[genre]["tempo_sd"])
                local_max_tempo = self._genres[genre]["tempo_mean"] + self._genres[genre]["tempo_sd"]
                if max_tempo < local_max_tempo:
                    max_tempo = local_max_tempo
                if min_tempo > local_max_tempo:
                    min_tempo = self._genres[genre]["tempo_mean"] - self._genres[genre]["tempo_sd"]

                all_danceability += self._genres[genre]["danceability"]
                danceability_means.append(self._genres[genre]["danceability_mean"])
                danceability_sds.append(self._genres[genre]["danceability_sd"])
                local_max_danceability = self._genres[genre]["danceability_mean"] + self._genres[genre]["danceability_sd"]
                if max_danceability < local_max_danceability:
                    max_danceability = local_max_danceability

        ax.set_xlim(min_tempo, math.ceil(max_tempo))
        ax.set_ylim(0, max_danceability)
        ax.set_ylabel("Danceability")
        ax.set_xlabel("Tempo")
        plt.suptitle("Distribution of genres and tracks by tempo and danceability", fontsize=12)
        plt.title("(Radii of circles is one standard deviation)", fontsize=8)

        circles = []
        for i in range(0, len(labels)):
            circ_color = random.choice(self._colors)
            circle = patches.Ellipse((tempo_means[i], danceability_means[i]), tempo_sds[i], danceability_sds[i], alpha=(1 / 3), facecolor=circ_color, edgecolor='k')
            circles.append(circle)
            ax.add_patch(circle)

        if show_legend:
            ax.legend(circles, labels)

        coef = numpy.polyfit(all_tempo, all_danceability, 1)
        line = numpy.poly1d(coef)
        ax.plot(all_tempo, all_danceability, "k.", all_tempo, line(all_tempo), "--b", markersize=2.5)

        # plt.show()
        current_date = str(datetime.today()).strip().replace(" ", "_").replace("-", "_").replace(":", "_")

        top = ""
        if show_legend:
            top = "top_" + str(len(map_genres)) + "_"

        fig.savefig("./img_dump/genres_tempo_v_danceability_" + top + current_date[0: current_date.index(".")] + ".png")

    def plot_acousticness_v_energy(self, map_genres=None):
        show_legend = False
        if map_genres is None:
            map_genres = list(self._genres.keys())
        if len(map_genres) <= 10:
            show_legend = True

        fig, ax = plt.subplots()

        labels = []

        all_acousticness = []
        acousticness_means = []
        acousticness_sds = []
        max_acousticness = 0

        all_energy = []
        energy_means = []
        energy_sds = []
        max_energy = 0
        for genre in self._genres:
            if genre in map_genres:
                labels.append(genre)

                all_acousticness += self._genres[genre]["acousticness"]
                acousticness_means.append(self._genres[genre]["acousticness_mean"])
                acousticness_sds.append(self._genres[genre]["acousticness_sd"])
                local_max_acousticness = self._genres[genre]["acousticness_mean"] + self._genres[genre]["acousticness_sd"]
                if max_acousticness < local_max_acousticness:
                    max_acousticness = local_max_acousticness

                all_energy += self._genres[genre]["energy"]
                energy_means.append(self._genres[genre]["energy_mean"])
                energy_sds.append(self._genres[genre]["energy_sd"])
                local_max_energy = self._genres[genre]["energy_mean"] + self._genres[genre]["energy_sd"]
                if max_energy < local_max_energy:
                    max_energy = local_max_energy

        ax.set_xlim(0, max_acousticness)
        ax.set_ylim(0, max_energy)
        ax.set_ylabel("Energy")
        ax.set_xlabel("Acousticness")
        plt.suptitle("Distribution of genres and tracks by acousticness and energy", fontsize=12)
        plt.title("(Radii of circles is one standard deviation)", fontsize=8)

        circles = []
        for i in range(0, len(labels)):
            circ_color = random.choice(self._colors)
            circle = patches.Ellipse((acousticness_means[i], energy_means[i]), acousticness_sds[i], energy_sds[i],
                                     alpha=(1 / 3), facecolor=circ_color, edgecolor='k')
            circles.append(circle)
            ax.add_patch(circle)


        if show_legend:
            ax.legend(circles, labels)

        coef = numpy.polyfit(all_acousticness, all_energy, 1)
        line = numpy.poly1d(coef)
        ax.plot(all_acousticness, all_energy, "k.", all_acousticness, line(all_acousticness), "--b", markersize=2.5)

        # plt.show()
        current_date = str(datetime.today()).strip().replace(" ", "_").replace("-", "_").replace(":", "_")

        top = ""
        if show_legend:
            top = "top_" + str(len(map_genres)) + "_"

        plt.tight_layout()
        fig.savefig("./img_dump/genres_acousticness_v_energy_" + top + current_date[0: current_date.index(".")] + ".png")

    def plot_loudness_v_energy(self, map_genres=None):
        show_legend = False
        if map_genres is None:
            map_genres = list(self._genres.keys())
        if len(map_genres) <= 10:
            show_legend = True

        fig, ax = plt.subplots()

        labels = []

        all_loudness = []
        loudness_means = []
        loudness_sds = []
        max_loudness = 0

        all_energy = []
        energy_means = []
        energy_sds = []
        max_energy = 0
        for genre in self._genres:
            if genre in map_genres:
                labels.append(genre)

                all_loudness += self._genres[genre]["loudness"]
                loudness_means.append(self._genres[genre]["loudness_mean"])
                loudness_sds.append(self._genres[genre]["loudness_sd"])
                local_max_loudness = self._genres[genre]["loudness_mean"] - self._genres[genre]["loudness_sd"]
                if max_loudness > local_max_loudness:
                    max_loudness = local_max_loudness

                all_energy += self._genres[genre]["energy"]
                energy_means.append(self._genres[genre]["energy_mean"])
                energy_sds.append(self._genres[genre]["energy_sd"])
                local_max_energy = self._genres[genre]["energy_mean"] + self._genres[genre]["energy_sd"]
                if max_energy < local_max_energy:
                    max_energy = local_max_energy

        ax.set_xlim(max_loudness, 0)
        ax.set_ylim(0, max_energy)
        ax.set_ylabel("Energy")
        ax.set_xlabel("Loudness")
        plt.suptitle("Distribution of genres and tracks by loudness and energy", fontsize=12)
        plt.title("(Radii of circles is one standard deviation)", fontsize=8)

        circles = []
        for i in range(0, len(labels)):
            circ_color = random.choice(self._colors)
            circle = patches.Ellipse((loudness_means[i], energy_means[i]), loudness_sds[i], energy_sds[i],
                                     alpha=(1 / 3), facecolor=circ_color, edgecolor='k')
            circles.append(circle)
            ax.add_patch(circle)

        if show_legend:
            ax.legend(circles, labels)

        coef = numpy.polyfit(all_loudness, all_energy, 1)
        line = numpy.poly1d(coef)
        ax.plot(all_loudness, all_energy, "k.", all_loudness, line(all_loudness), "--b", markersize=2.5)

        # plt.show()
        current_date = str(datetime.today()).strip().replace(" ", "_").replace("-", "_").replace(":", "_")

        top = ""
        if show_legend:
            top = "top_" + str(len(map_genres)) + "_"

        plt.tight_layout()
        fig.savefig("./img_dump/loudness_v_energy_" + top + current_date[0: current_date.index(".")] + ".png")

    def plot_valence_v_danceability(self, map_genres=None):
        show_legend = False
        if map_genres is None:
            map_genres = list(self._genres.keys())
        if len(map_genres) <= 10:
            show_legend = True

        fig, ax = plt.subplots()

        labels = []

        all_danceability = []
        danceability_means = []
        danceability_sds = []
        max_danceability = 0

        all_valence = []
        valence_means = []
        valence_sds = []
        max_valence = 0
        for genre in self._genres:
            if genre in map_genres:
                labels.append(genre)

                all_danceability += self._genres[genre]["danceability"]
                danceability_means.append(self._genres[genre]["danceability_mean"])
                danceability_sds.append(self._genres[genre]["danceability_sd"])
                local_max_danceability = self._genres[genre]["danceability_mean"] + self._genres[genre][
                    "danceability_sd"]
                if max_danceability < local_max_danceability:
                    max_danceability = local_max_danceability

                all_valence += self._genres[genre]["valence"]
                valence_means.append(self._genres[genre]["valence_mean"])
                valence_sds.append(self._genres[genre]["valence_sd"])
                local_max_valence = self._genres[genre]["valence_mean"] + self._genres[genre]["valence_sd"]
                if max_valence < local_max_valence:
                    max_valence = local_max_valence

        ax.set_xlim(0, max_danceability)
        ax.set_ylim(0, max_valence)
        ax.set_ylabel("Valence")
        ax.set_xlabel("Danceability")
        plt.suptitle("Distribution of genres and tracks by danceability and valence", fontsize=12)
        plt.title("(Radii of circles is one standard deviation)", fontsize=8)

        circles = []
        for i in range(0, len(labels)):
            circ_color = random.choice(self._colors)
            circle = patches.Ellipse((danceability_means[i], valence_means[i]), danceability_sds[i], valence_sds[i],
                                     alpha=(1 / 3), facecolor=circ_color, edgecolor='k')
            circles.append(circle)
            ax.add_patch(circle)

        if show_legend:
            ax.legend(circles, labels)

        coef = numpy.polyfit(all_valence, all_danceability, 1)
        line = numpy.poly1d(coef)
        ax.plot(all_valence, all_danceability, "k.", all_valence, line(all_valence), "--b", markersize=2.5)

        # plt.show()
        current_date = str(datetime.today()).strip().replace(" ", "_").replace("-", "_").replace(":", "_")

        top = ""
        if show_legend:
            top = "top_" + str(len(map_genres)) + "_"

        plt.tight_layout()
        fig.savefig("./img_dump/genres_danceability_v_valence_" + top + current_date[0: current_date.index(".")] + ".png")

    def build_corr_heatmap(self):
        danceability = []
        energy = []
        key = []
        loudness = []
        mode = []
        speechiness = []
        acousticness = []
        instrumentalness = []
        liveness = []
        valence = []
        tempo = []

        for genre in self._genres:
            danceability += self._genres[genre]["danceability"]
            energy += self._genres[genre]["energy"]
            key += self._genres[genre]["key"]
            loudness += self._genres[genre]["loudness"]
            mode += self._genres[genre]["mode"]
            speechiness += self._genres[genre]["speechiness"]
            acousticness += self._genres[genre]["acousticness"]
            instrumentalness += self._genres[genre]["instrumentalness"]
            liveness += self._genres[genre]["liveness"]
            valence += self._genres[genre]["valence"]
            tempo += self._genres[genre]["tempo"]

        data = {
            "danceability": danceability,
            "energy": energy,
            "key": key,
            "loudness": loudness,
            "mode": mode,
            "speechiness": speechiness,
            "acousticness": acousticness,
            "instrumentalness": instrumentalness,
            "liveness": liveness,
            "valence": valence,
            "tempo": tempo
        }

        corr_df = pandas.DataFrame(data=data)
        corr_matrix = corr_df.corr()
        mask_mat = numpy.triu(corr_matrix)

        seaborn.heatmap(corr_matrix, mask=mask_mat)
        plt.tight_layout()
        current_date = str(datetime.today()).strip().replace(" ", "_").replace("-", "_").replace(":", "_")
        plt.savefig("./img_dump/corr_heatmap_" + current_date[0: current_date.index(".")] + ".png")
        # plt.show()


if __name__ == "__main__":

    # top 10 genres by total
    genres = [
        "groove",
        "hard rock",
        "death",
        "doom",
        "thrash",
        "heavy",
        "black",
        "power",
        "speed",
        "melodic death"
    ]
    vw = VisualizeWrangle(csv="./compiled_artists_by_R.csv", genres=genres)