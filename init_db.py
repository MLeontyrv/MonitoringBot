import dotenv
import os
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from bot_logger import logger


def init_db():
    logger.info("Trying to initialize database")
    connection = None
    cursor = None
    dotenv.load_dotenv()
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    USER = os.getenv("DB_USER")
    PASS = os.getenv("DB_PASSWORD")
    DATABASE = os.getenv("DB_DATABASE")

    try:
        connection = psycopg2.connect(user=USER, password=PASS, host=HOST, port=PORT)
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()

        # Проверка существование бд
        cursor.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname = '{DATABASE}';")
        data = cursor.fetchall()
        # Не создавать бд, если он существует
        if len(data) != 0:
            logger.info(f"Database '{DATABASE}' already exists")
            return

        # Создание бд
        cursor.execute(f"CREATE DATABASE {DATABASE}")
        cursor.close()
        connection.close()

        # Подключение к бд и добавление тестовых данных
        connection = psycopg2.connect(user=USER, password=PASS, host=HOST, port=PORT, database=DATABASE)
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE emails (
                       email_id INT PRIMARY KEY,
                       email VARCHAR(255)         
        );""")
        cursor.execute("CREATE SEQUENCE email_id_seq OWNED BY emails.email_id")
        cursor.execute("ALTER TABLE emails ALTER COLUMN email_id SET DEFAULT nextval('email_id_seq')")

        cursor.execute("""CREATE TABLE phones (
                       phone_id INT PRIMARY KEY,
                       phone VARCHAR(24)
        );""")
        cursor.execute("CREATE SEQUENCE phone_id_seq OWNED BY phones.phone_id")
        cursor.execute("ALTER TABLE phones ALTER COLUMN phone_id SET DEFAULT nextval('phone_id_seq')")

        cursor.execute(
            "INSERT INTO emails (email_id, email) "
            "VALUES (DEFAULT, 'pt@pt.com'), (DEFAULT, 'mirea@edu.mirea.ru'), (DEFAULT, 'gsdfg@egff.ru')")
        cursor.execute(
            "INSERT INTO phones (phone_id, phone) "
            "VALUES (DEFAULT, '8 999 332 11 23'), (DEFAULT, '+79115678467'), (DEFAULT, '8(911)567-84-67')")
        connection.commit()
    except (Exception, Error) as error:
        logger.error("PostgreSQL initialize error: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


if __name__ == '__main__':
    init_db()