"""
Entrypoint for scoot modelling.
"""

from cleanair.scoot import ScootView
from cleanair.parsers import ScootForecastFeatureArgumentParser as Parser


def main():
    """Main function for creating scoot views."""
    parser = Parser(sources=[], end="2020-02-18T00:00:00")
    args = parser.parse_args()

    # create views
    scoot_view = ScootView(secretfile=args.secretfile)
    scoot_view.create_detector_road_view()


if __name__ == "__main__":
    main()
