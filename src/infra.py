"""Defines classes and functions for managing player data."""

import os
import re
from typing import Dict, List, Optional, Tuple, Type

import bs4
import numpy
from bs4 import BeautifulSoup, Tag

import settings
import util

DATA_DIR_PATH: str = os.path.join(os.path.dirname(__file__), "..", "data")


class Player:
    def __init__(
        self, name: str, position: Optional[str] = None, team: Optional[str] = None
    ) -> None:
        self.name = name
        self.position = position
        self.team = team
        self.rank_map: Dict[str, int] = {}
        self.position_rank_map: Dict[str, int] = {}
        self.projected_ppg_map: Dict[str, float] = {}

    def set_rank(self, source: str, rank: int) -> None:
        self.rank_map[source] = rank

    def set_position_rank(self, source: str, position_rank: int) -> None:
        self.position_rank_map[source] = position_rank

    def set_projected_ppg(self, source: str, projected_ppg: float) -> None:
        self.projected_ppg_map[source] = projected_ppg

    def get_rank(self, source: str) -> Optional[int]:
        return self.rank_map.get(source)

    def get_position_rank(self, source: str) -> Optional[int]:
        return self.position_rank_map.get(source)

    def get_projected_ppg(self, source: str) -> Optional[float]:
        return self.projected_ppg_map.get(source)

    def get_average_projected_ppg(self) -> float:
        return numpy.mean(list(self.projected_ppg_map.values()))

    def merge(self, other: "Player") -> None:
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

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(\n"
            f"	name = {self.name}, \n"
            f"	position = {self.position}, \n"
            f"	team = {self.team}, \n"
            f"	rank = {self.rank_map}, \n"
            f"	position rank = {self.position_rank_map}, \n"
            f"	projected ppg = {self.projected_ppg_map}\n"
            ")"
        )

    def similarity(self, other: "Player") -> float:
        def simplify(name: str) -> str:
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

        simplified_self: str = simplify(self.name)
        simplified_other: str = simplify(other.name)

        if simplified_self == other.name or simplified_other == self.name:
            return 1.0
        if simplified_self == simplified_other:
            return 2.0

        return float("inf")

    def find_match(self, players: List["Player"]) -> Optional["Player"]:
        if not players:
            return None

        similarities: List[Tuple["Player", float]] = [
            (other, self.similarity(other)) for other in players
        ]
        match: Tuple["Player", float] = min(similarities, key=lambda pair: pair[1])

        return match[0] if match[1] != float("inf") else None

    @classmethod
    def from_rankings_row(cls, row: Tag) -> "Player":
        raise NotImplementedError("Subclasses should override.")

    @classmethod
    def from_ppg_row(cls, row: Tag) -> "Player":
        raise NotImplementedError("Subclasses should override.")


class ESPNPlayer(Player):
    @classmethod
    def from_rankings_row(cls, row: Tag) -> "ESPNPlayer":
        cells: bs4.element.ResultSet[bs4.element.Tag] = row.find_all("td")
        rank_name: str = cells[0].get_text()
        rank: int = int(rank_name.split(".")[0])
        name: str = rank_name.split(". ", 1)[1]
        position: str = cells[1].get_text()
        team: str = cells[2].get_text()
        position_rank_text: str = cells[3].get_text()
        position_rank: int = int(re.search(r"[A-Z]+(\d+)", position_rank_text).group(1))

        player = cls(name, position, team)
        player.set_rank("ESPN", rank)
        player.set_position_rank("ESPN", position_rank)
        return player

    @classmethod
    def from_ppg_row(cls, row: Tag) -> "ESPNPlayer":
        try:
            cells: bs4.element.ResultSet[bs4.element.Tag] = row.find_all("td")
            name_text: str = util.aggressively_sanitize(cells[1].get_text())
            name: str = name_text.split(",")[0]
            projected_ppg: float = float(cells[-1].get_text())

            player = cls(name)
            player.set_projected_ppg("ESPN", projected_ppg)
            return player
        except (AttributeError, ValueError, IndexError) as e:
            if settings.VERBOSE:
                print(f"Skipping ppg row because of a parsing error: {e}")
            return None


class FantasyProsPlayer(Player):
    @classmethod
    def from_rankings_row(cls, row: Tag) -> "FantasyProsPlayer":
        try:
            cells: bs4.element.ResultSet[bs4.element.Tag] = row.find_all("td")
            rank: int = int(cells[0].get_text())
            player_label: Tag = cells[1]
            name: str = player_label.find("span", class_="full-name").get_text()
            position: str = re.search(r"([A-Z]+)\d+", cells[3].get_text()).group(1)
            team_tag: Tag = player_label.find("small", class_="grey")
            team: Optional[str] = team_tag.get_text() if team_tag else None
            position_rank: int = int(
                re.search(r"[A-Z]+(\d+)", cells[3].get_text()).group(1)
            )

            player = cls(name, position, team)
            player.set_rank("FantasyPros", rank)
            player.set_position_rank("FantasyPros", position_rank)
            return player
        except (AttributeError, ValueError, IndexError) as e:
            if settings.VERBOSE:
                print(f"Skipping rankings row because of a parsing error: {e}")
            return None

    @classmethod
    def from_ppg_row(cls, row: Tag) -> "FantasyProsPlayer":
        try:
            player_label: Tag = row.find("td", class_="player-label")
            name: str = player_label.find("a").get_text()
            ppg: float = float(row.find_all("td")[-1].get_text())

            player = cls(name)
            player.set_projected_ppg("FantasyPros", ppg)
            return player
        except (AttributeError, ValueError) as e:
            if settings.VERBOSE:
                print(f"Skipping ppg row because of a parsing error: {e}")
            return None


class FantasyDataSource:
    def __init__(self) -> None:
        self.dir_path: str = os.path.join(DATA_DIR_PATH, self.__class__.__name__)

    def __repr__(self) -> str:
        return self.__class__.__name__

    def parse_rankings(self) -> List[Player]:
        html_file_path: str = os.path.join(self.dir_path, "Rankings.htm")
        try:
            with open(html_file_path, "r", encoding="utf-8") as f:
                html: str = f.read()
        except FileNotFoundError:
            print(f"Skipping {self} rankings because file was not found")
            return []
        soup: BeautifulSoup = bs4.BeautifulSoup(html, "html5lib")
        return self._parse_rankings(soup)

    def _parse_rankings(self, soup: BeautifulSoup) -> List[Player]:
        raise NotImplementedError("Subclasses should override.")

    def parse_ppg(self) -> List[Player]:
        players: List[Player] = []
        projections_path: str = os.path.join(self.dir_path, "Projections")
        for filename in os.listdir(projections_path):
            if filename.endswith((".html", ".htm")):
                html_file_path: str = os.path.join(projections_path, filename)
                with open(html_file_path, "r", encoding="utf-8") as f:
                    html: str = f.read()
                soup: BeautifulSoup = bs4.BeautifulSoup(html, "html5lib")
                players.extend(self._parse_ppg(soup))
        return players

    def _parse_ppg(self, soup: BeautifulSoup) -> List[Player]:
        raise NotImplementedError("Subclasses should override.")


class ESPN(FantasyDataSource):
    def _parse_rankings(self, soup: BeautifulSoup) -> List[Player]:
        players: List[Player] = []
        table: Tag = soup.find_all("table", class_="inline-table")[1]
        for row in table.find_all("tr")[1:]:
            player: Player = ESPNPlayer.from_rankings_row(row)
            players.append(player)
        return players

    def _parse_ppg(self, soup: BeautifulSoup) -> List[Player]:
        players: List[Player] = []
        try:
            table: Tag = soup.find("table", class_="playerTableTable tableBody")
            for row in table.find_all("tr")[2:]:
                player: Player = ESPNPlayer.from_ppg_row(row)
                if player:
                    players.append(player)
        except AttributeError:
            if settings.VERBOSE:
                print("Skipping ppg because the table was not found")
        return players


class FantasyPros(FantasyDataSource):
    def _parse_rankings(self, soup: BeautifulSoup) -> List[Player]:
        players: List[Player] = []
        try:
            table: Tag = soup.find("table", class_="table-bordered")
            for row in table.find_all("tr")[2:]:
                if "Tier" not in row.get_text() and len(row.find_all("td")) == 11:
                    player: Player = FantasyProsPlayer.from_rankings_row(row)
                    if player:
                        players.append(player)
        except AttributeError:
            if settings.VERBOSE:
                print("Skipping rankings because the table was not found")
        return players

    def _parse_ppg(self, soup: BeautifulSoup) -> List[Player]:
        players: List[Player] = []
        try:
            table: Tag = soup.find("table", class_="table-bordered")
            should_ignore: bool = True
            for row in table.find_all("tr")[1:]:
                if should_ignore:
                    if "Player" in row.get_text():
                        should_ignore = False
                else:
                    player: Player = FantasyProsPlayer.from_ppg_row(row)
                    if player:
                        players.append(player)
        except AttributeError:
            if settings.VERBOSE:
                print("Skipping ppg because the table was not found")
        return players


SOURCES: List[Type[FantasyDataSource]] = [ESPN, FantasyPros]


def load_players() -> List[Player]:
    players: List[Player] = []
    for source_class in SOURCES:
        source: FantasyDataSource = source_class()
        for player in source.parse_rankings() + source.parse_ppg():
            old_player: Optional[Player] = player.find_match(players)
            if old_player:
                old_player.merge(player)
            else:
                players.append(player)
    return players


def main() -> None:
    for player in load_players():
        print(player)
        print()


if __name__ == "__main__":
    main()
