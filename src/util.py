from logger import Logger
import logging

class Util:
    logger: logging.Logger = Logger().get_logger()

    @staticmethod
    def parse_coordinates(geo_coordinates: str) -> tuple[float, float]:
        try:
            lat, lon = map(lambda x: float(x.strip()), geo_coordinates.split(','))
            return lat, lon
        except ValueError:
            Util.logger.error("Invalid geo_coordinates format. Expected 'lat,lon' with numeric values.")
            raise ValueError("Invalid geo_coordinates format. Expected 'lat,lon' with numeric values.")
