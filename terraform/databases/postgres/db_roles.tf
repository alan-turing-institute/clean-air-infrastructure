# CREATE ROLE GROUPS


# Role to read all schemas
resource "postgresql_role" "read_all" {
  name     = "read_all"
}

# Role to read  and write all schemas
resource "postgresql_role" "read_write" {
  name     = "read_write"
}

# Role to read only API relevant tables
resource "postgresql_role" "read_write_api" {
  name     = "read_write_api"
}
