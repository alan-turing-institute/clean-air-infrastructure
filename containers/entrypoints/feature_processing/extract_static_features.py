"""
Run feature processing using OSHighway data
"""
import webbrowser
import tempfile
import time
from cleanair.features import FeatureExtractor, FEATURE_CONFIG
from cleanair.parsers.entrypoint_parsers import create_static_feature_parser

ALL_FEATURES = [
    val
    for sublist in [
        list(j.keys()) for j in [ftype["features"] for ftype in FEATURE_CONFIG.values()]
    ]
    for val in sublist
]


def check(args):
    """Check what data is available in the database"""

    # Set up feature extractor
    static_feature_extractor = FeatureExtractor(
        feature_source=args.feature_source,
        table=FEATURE_CONFIG[args.feature_source]["table"],
        features=FEATURE_CONFIG[args.feature_source]["features"],
        secretfile=args.secretfile,
        sources=args.sources,
    )

    if not args.feature_name:
        args.feature_name = list(FEATURE_CONFIG[args.feature_source]["features"].keys())

    if args.method == "all":
        exclude_missing = False
    else:
        exclude_missing = True

    # Set up features to check
    if args.web:
        # show in browser
        available_data = static_feature_extractor.get_static_feature_availability(
            args.feature_name, args.sources, exclude_missing, output_type="html"
        )

        with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmp:
            tmp.write(
                "<h1>Feature availability. Feature={}</h1>".format(args.feature_name)
            )
            tmp.write(available_data)
            tmp.write("<p>Where has_data = False there is missing data</p>")
            tmp.seek(0)
            webbrowser.open("file://" + tmp.name, new=2)
            time.sleep(1)
    else:
        available_data = static_feature_extractor.get_static_feature_availability(
            args.feature_name, args.sources, exclude_missing, output_type="tabulate",
        )

        print(available_data)


def fill(args):
    """Fill the database"""

    # Set up feature extractor
    static_feature_extractor = FeatureExtractor(
        feature_source=args.feature_source,
        table=FEATURE_CONFIG[args.feature_source]["table"],
        features=FEATURE_CONFIG[args.feature_source]["features"],
        secretfile=args.secretfile,
        sources=args.sources,
    )

    static_feature_extractor.update_remote_tables()


def main():
    """
    Extract static OSHighway features
    """

    # Parse and interpret command line arguments
    args = create_static_feature_parser(
        check, fill, FEATURE_CONFIG.keys(), ALL_FEATURES
    ).parse_args()

    # Execute program
    args.func(args)


if __name__ == "__main__":
    main()
