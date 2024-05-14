import dotenv
import os
import psycopg2
from psycopg2 import Error
from bot_logger import logger


def query_database(query: str, no_return=False) -> str | list:
    logger.info("Trying to connect database")
    connection = None
    cursor = None
    dotenv.load_dotenv()
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    USER = os.getenv("DB_USER")
    PASS = os.getenv("DB_PASSWORD")
    DATABASE = os.getenv("DB_DATABASE")

    try:
        connection = psycopg2.connect(user=USER, password=PASS, host=HOST, port=PORT, database=DATABASE)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        if no_return:
            return ""
        else:
            return cursor.fetchall()

    except (Exception, Error) as error:
        logger.error("PostgreSQL query error: %s", error)

    finally:
        if connection is not None:
            cursor.close()
            connection.close()


def get_emails() -> str:
    result_string = ""
    row_list = query_database("SELECT * FROM emails;")

    for row in row_list:
        email_id, email = row
        result_string += f"{email_id}: {email}\n"

    return result_string


def get_phone_numbers() -> str:
    result_string = ""
    rowList = query_database("SELECT * FROM phones;")

    for row in rowList:
        phone_id, phone = row
        result_string += f"{phone_id}: {phone}\n"

    return result_string


def list_to_string(list_d: list[str]):
    values = ""
    for string in list_d:
        values += f"(DEFAULT ,'{string}'),"
    return values[:-1]


def save_emails(emails_list: list[str]):
    values = list_to_string(emails_list)
    query_database(f"INSERT INTO emails (email_id, email) VALUES {values};", True)


def save_phone_numbers(numbers_list: list[str]):
    values = list_to_string(numbers_list)
    query_database(f"INSERT INTO phones (phone_id, phone) VALUES {values};", True)
