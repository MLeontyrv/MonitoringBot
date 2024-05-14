import dotenv
import os
import paramiko
import re

from bot_logger import logger

dotenv.load_dotenv()
HOST = os.getenv("RM_HOST")
PORT = os.getenv("RM_PORT")
USER = os.getenv("RM_USER")
PASS = os.getenv("RM_PASSWORD")


# Выполнение команды на удаленном хосте
def exec_command_on_remote_host(command: str) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        logger.info(f"Connecting to {USER}@{HOST}:{PORT}")
        client.connect(
            hostname=HOST,
            port=PORT,
            username=USER,
            password=PASS,
        )
    except:
        logger.error(f"Couldn't connect to {USER}@{HOST}:{PORT}")
        return "Не удалось подключиться к удаленному хосту"

    _, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    if len(data) > 4096:
        logger.warn("SSH output is too big")
        return data[:4092] + "\n..."
    else:
        return data


# Сбор информации о системе
# О релизе
def get_release() -> str:
    return exec_command_on_remote_host("cat /etc/os-release")


# Об архитектуры процессора, имени хоста системы и версии ядра.
def get_uname() -> str:
    return exec_command_on_remote_host('uname -a')


# О времени работы
def get_uptime() -> str:
    return exec_command_on_remote_host("uptime")


# Сбор информации о состоянии файловой системы
def get_df() -> str:
    return exec_command_on_remote_host("df -h")


# Сбор информации о состоянии оперативной памяти
def get_free() -> str:
    return exec_command_on_remote_host("free -h")


# Сбор информации о производительности системы
def get_mpstat() -> str:
    return exec_command_on_remote_host("mpstat")


# Сбор информации о работающих в данной системе пользователях
def get_w() -> str:
    return exec_command_on_remote_host("w")


# Сбор логов
# Последние 10 входов в систему
def get_auths() -> str:
    return exec_command_on_remote_host("tail /var/log/auth.log")


# Последние 5 критических событий
def get_critical() -> str:
    result = exec_command_on_remote_host("journalctl -p crit -n 5")
    if result == "":
        return "Критических событий нет"
    else:
        return result


# Сбор информации о запущенных процессах
def get_ps() -> str:
    return exec_command_on_remote_host("ps")


# Сбор информации об используемых порта
def get_ss() -> str:
    return exec_command_on_remote_host("ss -tuln")


# Сбор информации об установленных пакетах
def get_apt_list(package_name: str) -> str:
    # Против command injections
    special_chars = re.compile(r"[&|;\n`]|\$\(")
    if special_chars.search(package_name) is not None:
        logger.critical(f"Malicius payload detected {package_name}")
        return "Запрещенное имя пакета"
    else:
        return exec_command_on_remote_host(f"apt list {package_name}")


# Сбор информации информации о запущенных сервисах
def get_services() -> str:
    return exec_command_on_remote_host("systemctl list-units --type=service --state=running")


# Вывод логов о репликации бд
def get_repl_logs() -> str:
    repl_logs = exec_command_on_remote_host(
        'tail -n 20 /var/log/postgresql/postgresql-15-main.log ') # | grep -i "replication"
    return repl_logs