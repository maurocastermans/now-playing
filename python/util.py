import logging

logger = logging.getLogger("now_playing_logger")


class Util:
    @staticmethod
    def parse_coordinates(geo_coordinates: str) -> tuple[float, float]:
        try:
            lat, lon = map(lambda x: float(x.strip()), geo_coordinates.split(','))
            return lat, lon
        except ValueError:
            logger.error("Invalid geo_coordinates format. Expected 'lat,lon' with numeric values.")
            raise ValueError("Invalid geo_coordinates format. Expected 'lat,lon' with numeric values.")
