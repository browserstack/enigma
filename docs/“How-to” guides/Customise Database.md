Enigma allows to integrate database either with sqlite3 or mysql database engine.

## Using sqlite3 database
- The database engine can be configured in the `config.json` using the  `"database"` key.
- For sqlite database set as follows:
  ```json
  {
    ...
    "database": {
      "enigne": "sqlite3"
    }
    ...
  }
  ```
- This will autogenerate `db.sqlite3` file in `/db` path inside the docker container which is mounted to `/mounts/db` folder.

## Using docker mysql database
- Configure the enviroment variables which are used by the mysql docker image in `secrets/ops_mysql_dev.env` file.
- After which configure the `"database"` key in `config.json` file to be as follows:
  ```json
  {
    ...
    "database":{
      "engine": "mysql",
      "dbname": "<database name set in the env variables, default value is enigma>",
      "username": "root",
      "password": "<password of root user set in the env variables>",
      "host": "db",
      "port": 3306
    }
    ...
  }
  ```
  Note here that `host` is set to `db` because the mysql container in `docker-compose.yml` file is identified by `db` with port `3306` expose hence `port` is set to `3306`.
- The mysql file in the container is mounted to `mounts/mysql`.

## Using self hosted mysql database
- Also allows to configure self hosted mysql database.
- Configure the `"database"` key in `config.json` file as follows:
  ```json
  {
    ...
    "database": {
      "engine": "mysql",
      "dbname": "<database name that is used by Enigma in self hosted database>",
      "username": "<username used by Enigma to perform migrations, write and reads>",
      "password": "<password to the user with the username provided>",
      "host": "<Host url through which Enimga can access database>",
      "port": "<Port self hosted database is running on>"
    }
    ...
  }
  ```
  Note: Make sure that the user provide has root access.
