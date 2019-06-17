HOST=$(jq '.host' -r /.secrets/.secret.json)
PORT=$(jq '.port' -r /.secrets/.secret.json)
DB_NAME=$(jq '.db_name' -r /.secrets/.secret.json)
USERNAME=$(jq '.username' -r /.secrets/.secret.json)
PASSWORD=$(jq '.password' -r /.secrets/.secret.json)
SSL_MODE=$(jq '.ssl_mode' -r /.secrets/.secret.json)

PG="host=$HOST port=$PORT dbname=$DB_NAME user=$USERNAME password=$PASSWORD sslmode=$SSL_MODE"
echo "Inserting into $HOST"

ogr2ogr -f PostgreSQL "PG:$PG" /data/static_data.gdb -overwrite -progress --config PG_USE_COPY YES -overwrite -progress --config PG_USE_COPY YES

# Potentially working:
# ogr2ogr -f PostgreSQL PG:'host=ukmap-server.postgres.database.azure.com port=5432 dbname=ukmap_db user=atiadmin_ukmap@ukmap-server password=QgE3OYG{qMe$XpYi sslmode=require' /data/static_data.gdb -overwrite -progress --config PG_USE_COPY YES