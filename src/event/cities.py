from enum import Enum


class GermanCity(str, Enum):
    berlin = "berlin"
    munich = "munich"
    hamburg = "hamburg"
    cologne = "cologne"
    frankfurt = "frankfurt"
    stuttgart = "stuttgart"
    dusseldorf = "dusseldorf"
    leipzig = "leipzig"
    dresden = "dresden"
    nuremberg = "nuremberg"
    bremen = "bremen"
    hannover = "hannover"
    dortmund = "dortmund"
    essen = "essen"
    mannheim = "mannheim"


# slug -> (display_name, latitude, longitude)
CITY_COORDINATES: dict[GermanCity, tuple[str, float, float]] = {
    GermanCity.berlin: ("Berlin", 52.5200, 13.4050),
    GermanCity.munich: ("Munich", 48.1351, 11.5820),
    GermanCity.hamburg: ("Hamburg", 53.5511, 9.9937),
    GermanCity.cologne: ("Cologne", 50.9375, 6.9603),
    GermanCity.frankfurt: ("Frankfurt", 50.1109, 8.6821),
    GermanCity.stuttgart: ("Stuttgart", 48.7758, 9.1829),
    GermanCity.dusseldorf: ("Dusseldorf", 51.2277, 6.7735),
    GermanCity.leipzig: ("Leipzig", 51.3397, 12.3731),
    GermanCity.dresden: ("Dresden", 51.0504, 13.7373),
    GermanCity.nuremberg: ("Nuremberg", 49.4521, 11.0767),
    GermanCity.bremen: ("Bremen", 53.0793, 8.8017),
    GermanCity.hannover: ("Hannover", 52.3759, 9.7320),
    GermanCity.dortmund: ("Dortmund", 51.5136, 7.4653),
    GermanCity.essen: ("Essen", 51.4556, 7.0116),
    GermanCity.mannheim: ("Mannheim", 49.4875, 8.4660),
}


def city_display_name(city: GermanCity) -> str:
    return CITY_COORDINATES[city][0]
