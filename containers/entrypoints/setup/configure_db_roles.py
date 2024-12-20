"""Configure database roles"""

from cleanair_data.loggers import initialise_logging
from cleanair_data.databases import DBConfig
from cleanair_data.parsers import DataBaseRoleParser


def main():
    "Confure database roles"
    parser = DataBaseRoleParser()
    args = parser.parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    default_logger.warning(
        "This will create roles on the database."
        "It will not revoke them. Any removals from the config.yaml must be manually removed from the database"
    )

    db_config = DBConfig(
        config_file=args.config_file,
        secretfile=args.secretfile,
        secret_dict=args.secret_dict,
    )
    db_config.ensure_database_exists()
    db_config.ensure_extensions()
    db_config.configure_all_roles()


if __name__ == "__main__":
    main()
