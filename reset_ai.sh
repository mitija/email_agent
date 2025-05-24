# This script will connect to the sqlite database and
# - empty the thread_summary
# - empty the knowledge field on contacts

SQLITE_DB="./db.sqlite3"

sqlite3 $SQLITE_DB <<EOF
DELETE FROM  core_threadsummary;
UPDATE core_contact SET knowledge = null;
EOF
