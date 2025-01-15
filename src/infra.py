import os
import re
import bs4
import numpy
import settings
import util

DATA_DIR_PATH = os.path.join(os.path.dirname(__file__), "..", "data")


class Player:
    def __init__(self, name, position=None, team=None):
        self.name = name
        self.position = position
        self.team = team
        self.rank_map = {}
        self.position_rank_map = {}
        self.projected_ppg_map = {}

    def set_rank(self, source, rank):
        self.rank_map[source] = rank

    def set_position_rank(self, source, position_rank):
        self.position_rank_map[source] = position_rank

    def set_projected_ppg(self, source, projected_ppg):
        self.projected_ppg_map[source] = projected_ppg

    def get_rank(self, source):
        return self.rank_map.get(source)

    def get_position_rank(self, source):
        return self.position_rank_map.get(source)

    def get_projected_ppg(self, source):
        return self.projected_ppg_map.get(source)

    def get_average_projected_ppg(self):
        return numpy.mean(list(self.projected_ppg_map.values()))

    def merge(self, other):
        if settings.VERBOSE:
            print(f"Merging {self.name} and {other.name}")

        self.position = self.position or other.position
        self.team = self.team or other.team

        for source, rank in other.rank_map.items():
            self.set_rank(source, rank)
        for source, position_rank in other.position_rank_map.items():
            self.set_position_rank(source, position_rank)
        for source, projected_ppg in other.projected_ppg_map.items():
            self.set_projected_ppg(source, projected_ppg)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(\n"
            f"\tname = {self.name}, \n"
            f"\tposition = {self.position}, \n"
            f"\tteam = {self.team}, \n"
            f"\trank = {self.rank_map}, \n"
            f"\tposition rank = {self.position_rank_map}, \n"
            f"\tprojected ppg = {self.projected_ppg_map}\n"
            ")"
        )

    def similarity(self, other):
        def simplify(name):
            # General name simplifications
            name = re.sub(r" (Jr\.|Sr\.|II|III)$", "", name)
            # D/ST simplifications
            name = name.replace(" D/ST", "").replace(" D/STD/ST", "")
            # Team name simplifications
            for team_name in settings.TEAM_NAMES:
                name = name.replace(f"{team_name} ", "")
            return name

        if self.name == other.name:
            return 0.0
        
        simplified_self = simplify(self.name)
        simplified_other = simplify(other.name)

        if simplified_self == other.name or simplified_other == self.name:
            return 1.0
        if simplified_self == simplified_other:
            return 2.0
        
        return float("inf")

    def find_match(self, players):
        if not players:
            return None
        
        similarities = [(other, self.similarity(other)) for other in players]
        match = min(similarities, key=lambda pair: pair[1])
        
        return match[0] if match[1] != float("inf") else None

    @classmethod
    def from_rankings_row(cls, row):
        raise NotImplementedError("Subclasses should override.")

    @classmethod
    def from_ppg_row(cls, row):
        raise NotImplementedError("Subclasses should override.")


class ESPNPlayer(Player):
    @classmethod
    def from_rankings_row(cls, row):
        cells = row.find_all("td")
        rank_name = cells[0].get_text()
        rank = int(rank_name.split(".")[0])
        name = rank_name.split(". ", 1)[1]
        position = cells[1].get_text()
        team = cells[2].get_text()
        position_rank_text = cells[3].get_text()
        position_rank = int(re.search(r"[A-Z]+(\d+)", position_rank_text).group(1))
        
        player = cls(name, position, team)
        player.set_rank("ESPN", rank)
        player.set_position_rank("ESPN", position_rank)
        return player

    @classmethod
    def from_ppg_row(cls, row):
        cells = row.find_all("td")
        name_text = util.aggressively_sanitize(cells[1].get_text())
        name = name_text.split(",")[0]
        projected_ppg = float(cells[-1].get_text())
        
        player = cls(name)
        player.set_projected_ppg("ESPN", projected_ppg)
        return player


class FantasyProsPlayer(Player):
    @classmethod
    def from_rankings_row(cls, row):
        cells = row.find_all("td")
        rank = int(cells[0].get_text())
        player_label = cells[1]
        name = player_label.find("span", class_="full-name").get_text()
        position = re.search(r"([A-Z]+)\d+", cells[3].get_text()).group(1)
        team_tag = player_label.find("small", class_="grey")
        team = team_tag.get_text() if team_tag else None
        position_rank = int(re.search(r"[A-Z]+(\d+)", cells[3].get_text()).group(1))
        
        player = cls(name, position, team)
        player.set_rank("FantasyPros", rank)
        player.set_position_rank("FantasyPros", position_rank)
        return player

    @classmethod
    def from_ppg_row(cls, row):
        player_label = row.find("td", class_="player-label")
        name = player_label.find("a").get_text()
        ppg = float(row.find_all("td")[-1].get_text())
        
        player = cls(name)
        player.set_projected_ppg("FantasyPros", ppg)
        return player


class FantasyDataSource:
    def __init__(self):
        self.dir_path = os.path.join(DATA_DIR_PATH, self.__class__.__name__)

    def __repr__(self):
        return self.__class__.__name__

    def parse_rankings(self):
        html_file_path = os.path.join(self.dir_path, "Rankings.htm")
        with open(html_file_path, "r", encoding="utf-8") as f:
            html = f.read()
        soup = bs4.BeautifulSoup(html, "html5lib")
        return self._parse_rankings(soup)

    def _parse_rankings(self, soup):
        raise NotImplementedError("Subclasses should override.")

    def parse_ppg(self):
        players = []
        projections_path = os.path.join(self.dir_path, "Projections")
        for filename in os.listdir(projections_path):
            if filename.endswith((".html", ".htm")):
                html_file_path = os.path.join(projections_path, filename)
                with open(html_file_path, "r", encoding="utf-8") as f:
                    html = f.read()
                soup = bs4.BeautifulSoup(html, "html5lib")
                players.extend(self._parse_ppg(soup))
        return players

    def _parse_ppg(self, soup):
        raise NotImplementedError("Subclasses should override.")


class ESPN(FantasyDataSource):
    def _parse_rankings(self, soup):
        players = []
        table = soup.find_all("table", class_="inline-table")[1]
        for row in table.find_all("tr")[1:]:
            player = ESPNPlayer.from_rankings_row(row)
            players.append(player)
        return players

    def _parse_ppg(self, soup):
        players = []
        table = soup.find("table", class_="playerTableTable tableBody")
        for row in table.find_all("tr")[2:]:
            player = ESPNPlayer.from_ppg_row(row)
            players.append(player)
        return players


class FantasyPros(FantasyDataSource):
    def _parse_rankings(self, soup):
        players = []
        table = soup.find("table", class_="table-bordered")
        for row in table.find_all("tr")[2:]:
            if "Tier" not in row.get_text() and len(row.find_all("td")) == 11:
                player = FantasyProsPlayer.from_rankings_row(row)
                players.append(player)
        return players

    def _parse_ppg(self, soup):
        players = []
        table = soup.find("table", class_="table-bordered")
        should_ignore = True
        for row in table.find_all("tr")[1:]:
            if should_ignore:
                if "Player" in row.get_text():
                    should_ignore = False
            else:
                player = FantasyProsPlayer.from_ppg_row(row)
                players.append(player)
        return players


SOURCES = [ESPN, FantasyPros]


def load_players():
    players = []
    for source_class in SOURCES:
        source = source_class()
        for player in source.parse_rankings() + source.parse_ppg():
            old_player = player.find_match(players)
            if old_player:
                old_player.merge(player)
            else:
                players.append(player)
    return players


def main():
    for player in load_players():
        print(player)
        print()


if __name__ == "__main__":
    main()