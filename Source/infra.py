import os
import sys
import re
import bs4
import ntpath

import numpy

import ashlib.util.file_
import ashlib.util.dir_
import ashlib.util.str_

import util
import settings

# ESPN rankings link: http://www.espn.com/fantasy/football/story/_/page/18RanksPreseason300nonPPR/2018-fantasy-football-non-ppr-rankings-top-300
# ESPN projected ppg link: http://games.espn.com/ffl/tools/projections?leagueId=1160162
# FantasyPros rankings link: https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php
# FantasyPros projected ppg link: https://www.fantasypros.com/nfl/projections/qb.php?week=draft

DATA_DIR_PATH = os.path.join("..", "Data")

class Player(object):
    
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
        if source in self.rank_map: return self.rank_map[source]
        else: return None
        
    def get_position_rank(self, source):
        if source in self.position_rank_map: return self.position_rank_map[source]
        else: return None
        
    def get_projected_ppg(self, source):
        if source in self.projected_ppg_map: return self.projected_ppg_map[source] 
        else: return None
    
    def get_average_projected_ppg(self):
        return sum(self.projected_ppg_map.values()) / len(self.projected_ppg_map)
        
    def merge(self, other):
        if settings.VERBOSE:
            print "Merging %s and %s" % (self.name, other.name)
        
        self.position = self.position or other.position
        self.team = self.team or other.team 
        
        for source in other.rank_map:
            self.set_rank(source, other.get_rank(source))
        for source in other.position_rank_map:
            self.set_position_rank(source, other.get_position_rank(source))
        for source in other.projected_ppg_map:
            self.set_projected_ppg(source, other.get_projected_ppg(source))
        
    def __repr__(self):
        return "%s(\n\tname = %s, \n\tposition = %s, \n\tteam = %s, \n\trank = %s, \n\tposition rank =% s, \n\tprojected ppg = %s\n)"% (self.__class__.__name__, self.name, self.position, self.team, self.rank_map, self.position_rank_map, self.projected_ppg_map)
    
    def similarity(self, other):
        def simplify(name):
            name = name.replace(" Jr.", "")
            name = name.replace(" sr.", "")
            name = name.replace(" II", "")
            name = name.replace(" III", "")
            name = name.replace(" D/STD/ST", "")
            name = name.replace(" D/ST", "")
            
            name = name.replace("Jacksonville ", "")
            name = name.replace("Minnesota ", "")
            name = name.replace("Philadelphia ", "")
            name = name.replace("Houston ", "")
            name = name.replace("Los Angeles ", "")
            name = name.replace("Baltimore ", "")
            name = name.replace("Denver ", "")
            name = name.replace("Seattle ", "")
            name = name.replace("New England ", "")
            name = name.replace("Carolina ", "")
            name = name.replace("Pittsburgh ", "")
            name = name.replace("Carolina ", "")
            name = name.replace("Kansas City ", "")
            name = name.replace("Chicago ", "")
            name = name.replace("Atlanta ", "")
            name = name.replace("Arizona ", "")
            name = name.replace("Green Bay ", "")
            name = name.replace("New York ", "")
            name = name.replace("Tennessee ", "")
            name = name.replace("Detroit ", "")
            name = name.replace("Buffalo ", "")
            name = name.replace("New Orleans ", "")
            name = name.replace("San Francisco ", "")
            name = name.replace("Washington ", "")
            name = name.replace("Cleveland ", "")
            name = name.replace("Cincinnati ", "")
            name = name.replace("Dallas ", "")
            name = name.replace("Houston ", "")
            name = name.replace("Indianapolis ", "")
            name = name.replace("Miami ", "")
            name = name.replace("Oakland ", "")
            name = name.replace("Tampa Bay ", "")
            
            return name

        if self.name == other.name: return 0.0
        elif simplify(self.name) == other.name: return 1.0
        elif simplify(other.name) == self.name: return 1.0
        elif simplify(other.name) == simplify(self.name): return 2.0
        else: return float("inf")
        
    def find_match(self, players):
        if len(players) > 0:
            similarities = [(other, self.similarity(other)) for other in players]
            match = min(similarities, key=lambda pair: pair[1])
            if match[1] < float("inf"):
                return match[0]
        return None
        
    @classmethod
    def from_rankings_row(cls, row):
        raise NotImplementedError("Subclasses should override.")
        
    @classmethod
    def from_ppg_row(cls, row):
        raise NotImplementedError("Subclasses should override.")
        
class ESPNPlayer(Player):
    
    @classmethod
    def from_rankings_row(cls, row):
        rank_name = row.find_all("td")[0].get_text()
        rank = int(rank_name.split(".")[0])
        name = rank_name[rank_name.find(".") + 2:]
        position = row.find_all("td")[1].get_text()
        team = abbreviation=row.find_all("td")[2].get_text()
        position_rank = int(re.search("[A-Z]+(\d+)", row.find_all("td")[3].get_text()).groups()[0])
        player = cls(name, position, team)
        player.set_rank(ESPN, rank)
        player.set_position_rank(ESPN, position_rank)
        return player
    
    @classmethod
    def from_ppg_row(cls, row):
        name = ashlib.util.str_.aggressivelySanitize(row.find_all("td")[1].get_text()).split(",")[0]
        projected_ppg = float(row.find_all("td")[-1].get_text())
        player = cls(name)
        player.set_projected_ppg(ESPN, projected_ppg)
        return player
    
class FantasyProsPlayer(Player):
    
    @classmethod
    def from_rankings_row(cls, row):
        rank = int(row.find_all("td")[0].get_text())
        name = row.find("td", class_="player-label").find("span", class_="full-name").get_text()
        position = re.search("([A-Z]+)\d+", row.find_all("td")[3].get_text()).groups()[0]
        team_tag = row.find("td", class_="player-label").find("small", class_="grey")
        if team_tag is None:
            team = None
        else:
            team = row.find("td", class_="player-label").find("small", class_="grey").get_text()
        position_rank = int(re.search("[A-Z]+(\d+)", row.find_all("td")[3].get_text()).groups()[0])
        player = cls(name, position, team)
        player.set_rank(FantasyPros, rank)
        player.set_position_rank(FantasyPros, position_rank)
        return player
    
    @classmethod
    def from_ppg_row(cls, row):
        name = row.find("td", class_="player-label").find("a").get_text()
        ppg = float(row.find_all("td")[-1].get_text())
        player = cls(name)
        player.set_projected_ppg(FantasyPros, ppg)
        return player

class FantasyDataSource(object):
    
    def __init__(self):
        self.dir_path = os.path.join(DATA_DIR_PATH, self.__class__.__name__)
        
    def __repr__(self):
        return self.__class__.__name__
    
    def parse_rankings(self):
        html_file_path = os.path.join(self.dir_path, "Rankings.htm")
        html = ashlib.util.file_.read(html_file_path)
        soup = bs4.BeautifulSoup(html, "html5lib")
        return self._parse_rankings(soup)
        
    def _parse_rankings(self, soup):
        raise NotImplementedError("Subclasses should override.")
        
    def parse_ppg(self):
        players = []
        for html_file_path in ashlib.util.dir_.listStdDir(os.path.join(self.dir_path, "Projections")):
            if html_file_path.endswith(".html") or html_file_path.endswith(".htm"):
                html = ashlib.util.file_.read(html_file_path)
                soup = bs4.BeautifulSoup(html, "html5lib")
                players.extend(self._parse_ppg(soup))
        return players
    
    def _parse_ppg(self, soup):
        raise NotImplementedError("Subclasses should override.")
    
class ESPN(FantasyDataSource):
    
    def _parse_rankings(self, soup):
        players = []
        for row in soup.find_all("table", class_="inline-table")[1].find_all("tr")[1:]:
            player = ESPNPlayer.from_rankings_row(row)
            players.append(player)
        return players
    
    def _parse_ppg(self, soup):
        players = []
        for row in soup.find("table", class_="playerTableTable tableBody").find_all("tr")[2:]:
            player = ESPNPlayer.from_ppg_row(row)
            players.append(player)
        return players
    
class FantasyPros(FantasyDataSource):
    
    def _parse_rankings(self, soup):
        players = []
        for row in soup.find("table", class_="table table-bordered table-striped player-table table-hover pad-below tablesorter").find_all("tr")[2:]:
            if not row.get_text().startswith("Tier") and len(row.find_all("td")) == 11:
                player = FantasyProsPlayer.from_rankings_row(row)
                players.append(player)
        return players
    
    def _parse_ppg(self, soup):
        players = []
        should_ignore = True
        for row in soup.find("table", class_="table table-bordered table-striped table-hover tablesorter").find_all("tr")[1:]:
            if should_ignore:
                if "Player" in row.get_text():
                    should_ignore = False
            else:
                player = FantasyProsPlayer.from_ppg_row(row)
                players.append(player)
        return players
        
SOURCES = [
    ESPN,
    FantasyPros
]

def load_players():
    players = []

    count = 0
    for source_class in SOURCES:
        source = source_class()
        for player in source.parse_rankings() + source.parse_ppg():
            count += 1
            old_player = player.find_match(players)
            if old_player is not None:
                old_player.merge(player)
            else:
                players.append(player)

    return players

def main():
    for player in load_players():
        print player
        print

if __name__ == "__main__":
    main()
