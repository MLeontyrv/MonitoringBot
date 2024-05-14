import re
import dotenv
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, ContextTypes
from bot_logger import logger
from init_db import init_db
import query_db as qdb
import monitoring_linux as ml

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}! \nДоступные команды: /help')


def help_command(update: Update, context):
    update.message.reply_text("""
Доступные команды:
/help - Справка о доступных командах
/find_email - Поиск Email адреса
/find_phone_number - Поиск номера телефона
/get_emails - Показать сохранённые Email адреса
/get_phone_numbers - Показать сохранённые номера телефонов
/verify_password - Проверка пароля на сложность

Мониторинг Linux-системы
/get_release - О релизе
/get_uname - Об архитектуры процессора, имени хоста системы и версии ядра 
/get_uptime - О времени работы
/get_df - Сбор информации о состоянии файловой системы
/get_free - Сбор информации о состоянии оперативной памяти
/get_mpstat - Сбор информации о производительности системы
/get_w - Сбор информации о работающих в данной системе пользователях
/get_auths - Последние 10 входов в систему
/get_critical - Последние 5 критических события
/get_ps - Сбор информации о запущенных процессах
/get_ss - Сбор информации об используемых портах
/get_apt_list <пакет> - Сбор информации об установленных пакетах, если <пакет> не указан, будут выведены все пакеты
/get_services - Сбор информации о запущенных сервисах
/get_repl_logs - Вывод логов о репликации базы данных""")


# Поиск почтовых адресов в тексте
def find_email_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска почтовых адресов: ')
    return 'find_email'


def find_email(update: Update, context):
    user_input = update.message.text  # Получаем текст
    email_regex = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')  # Регулярка для email
    email_list = email_regex.findall(user_input)  # Ищем email

    if not email_list:  # Обрабатываем случай, когда адресов нет
        update.message.reply_text('Почтовые адреса не найдены')
        return ConversationHandler.END  # Завершаем выполнение функции

    context.user_data["emails"] = email_list
    emails = ''  # Создаем строку, в которую будем записывать email-ы
    for i in range(len(email_list)):
        emails += f'{i + 1}. {email_list[i]}\n'  # Записываем очереднeю почту

    update.message.reply_text(emails)  # Отправляем сообщение пользователю
    update.message.reply_text("Сохранить запись? (Да/нет)")
    return 'save_email'


# Сохранение почтовых адресов в бд
def save_email(update: Update, context):
    user_input = update.message.text

    if user_input.lower() == "да":
        emails = context.user_data["emails"]
        qdb.save_emails(emails)
        update.message.reply_text("Данные сохранены")
    elif user_input.lower() == "нет":
        update.message.reply_text("Данные не будут сохранены")
    else:
        update.message.reply_text("Формат ответа: да/нет")
        return "save_email"

    context.user_data["emails"] = None
    return ConversationHandler.END


# Поиск телефонных номеров в тексте
def find_phone_number_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'find_phone_number'


def find_phone_number(update: Update, context):
    user_input = update.message.text  # Получаем текст
    phone_num_regex = re.compile(r'(?:(?:8|\+7)[\- ]?)?(?:\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}')  # Регулярка для номера
    phone_number_list = phone_num_regex.findall(user_input)  # Ищем номера телефонов

    if not phone_number_list:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END  # Завершаем выполнение функции

    context.user_data["phones"] = phone_number_list
    phone_numbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phone_number_list)):
        phone_numbers += f'{i + 1}. {phone_number_list[i]}\n'  # Записываем очередной номер

    update.message.reply_text(phone_numbers)  # Отправляем сообщение пользователю
    update.message.reply_text("Сохранить запись? (Да/нет)")
    return "save_phone"


# Сохранение номеров в бд
def save_phone(update: Update, context):
    user_input = update.message.text

    if user_input.lower() == "да":
        phones = context.user_data["phones"]
        qdb.save_phone_numbers(phones)
        update.message.reply_text("Данные сохранены")
    elif user_input.lower() == "нет":
        update.message.reply_text("Данные не будут сохранены")
    else:
        update.message.reply_text("Формат ответа: да/нет")
        return "save_phone"

    context.user_data["phones"] = None
    return ConversationHandler.END


#  Проверка пароля на сложность
def verify_password_command(update: Update, context):
    update.message.reply_text('Введите пароль для проверки на сложность: ')
    return 'verify_password'


def verify_password(update: Update, context):
    user_input = update.message.text  # Получаем текст
    # Регулярка для пароля
    password_regex = re.compile(r'(?=.*[0-9])(?=.*[!@#$%^&*()])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*()]{8,}')
    mo = password_regex.search(user_input)  # Проверяем пароль
    if mo:
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text("Пароль простой")
    return ConversationHandler.END  # Завершаем работу обработчика диалога


# Сбор информации о системе
# О релизе
def get_release_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о релизе...')
    result = ml.get_release()
    update.message.reply_text(result)


# Об архитектуры процессора, имени хоста системы и версии ядра.
def get_uname_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о системе...')
    result = ml.get_uname()
    update.message.reply_text(result)


# О времени работы
def get_uptime_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о времени работы системы...')
    result = ml.get_uptime()
    update.message.reply_text(result)


# Сбор информации о состоянии файловой системы
def get_df_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о состоянии файловой системы...')
    result = ml.get_df()
    update.message.reply_text(result)


# Сбор информации о состоянии оперативной памяти
def get_free_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о состоянии оперативной памяти...')
    result = ml.get_free()
    update.message.reply_text(result)


# Сбор информации о производительности системы
def get_mpstat_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о производительности системы...')
    result = ml.get_mpstat()
    update.message.reply_text(result)


# Сбор информации о работающих в данной системе пользователях
def get_w_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о работающих пользователях...')
    result = ml.get_w()
    update.message.reply_text(result)


# Сбор логов
# Последние 10 входов в систему
def get_auths_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о последних 10 входах в систему...')
    result = ml.get_auths()
    update.message.reply_text(result)


# Последние 5 критических событий #
def get_critical_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о последних 5 критических событиях...')
    result = ml.get_critical()
    if result == "":
        update.message.reply_text("Критических событий нет")
    else:
        critical = result.strip().split('\n')
        for line in critical:
            update.message.reply_text(line)


# Сбор информации о запущенных процессах
def get_ps_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о запущенных процессах...')
    result = ml.get_ps()
    update.message.reply_text(result)


# Сбор информации об используемых портах
def get_ss_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации об используемых портах...')
    result = ml.get_ss()
    update.message.reply_text(result)


# Сбор информации об установленных пакетах
def get_apt_list_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации об установленных пакетах...')
    package_name = ""
    try:
        package_name = context.args[0]
    except:
        pass

    result = ml.get_apt_list(package_name)
    update.message.reply_text(result)


# Сбор информации информации о запущенных сервисах
def get_services_command(update: Update, context) -> None:
    update.message.reply_text('Получение информации о запущенных сервисах...')
    services = ml.get_services()
    result = services.strip().split('\n')
    for line in result:
        update.message.reply_text(line)


# Вывод логов о репликации бд
def get_repl_logs_command(update: Update, context) -> None:
    update.message.reply_text('Получение логов репликации...')
    repl_logs = ml.get_repl_logs()
    repl_logs_lines = repl_logs.strip().split('\n')
    for line in repl_logs_lines:
        update.message.reply_text(line)


# Вывод email адресов из бд
def get_emails_command(update: Update, context) -> None:
    result = qdb.get_emails()
    update.message.reply_text(result)


# Вывод телефонных номеров из бд
def get_phone_numbers_command(update: Update, context) -> None:
    result = qdb.get_phone_numbers()
    update.message.reply_text(result)


def main():
    logger.info("Starting bot setup")
    init_db()  # Создание бд, если она не существует
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher  # Получаем диспетчер для регистрации обработчиков

    # Обработчики диалога
    conv_handler_find_phone_number = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_number_command)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
            'save_phone': [MessageHandler(Filters.text & ~Filters.command, save_phone)],
        },
        fallbacks=[]
    )

    conv_handler_find_emails = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_email_command)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'save_email': [MessageHandler(Filters.text & ~Filters.command, save_email)],
        },
        fallbacks=[]
    )

    conv_handler_verify_password = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password_command)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(conv_handler_find_phone_number)
    dp.add_handler(conv_handler_find_emails)
    dp.add_handler(conv_handler_verify_password)
    dp.add_handler(CommandHandler("get_release", get_release_command))
    dp.add_handler(CommandHandler("get_uname", get_uname_command))
    dp.add_handler(CommandHandler("get_uptime", get_uptime_command))
    dp.add_handler(CommandHandler("get_df", get_df_command))
    dp.add_handler(CommandHandler("get_free", get_free_command))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat_command))
    dp.add_handler(CommandHandler("get_w", get_w_command))
    dp.add_handler(CommandHandler("get_auths", get_auths_command))
    dp.add_handler(CommandHandler("get_critical", get_critical_command))
    dp.add_handler(CommandHandler("get_ps", get_ps_command))
    dp.add_handler(CommandHandler("get_ss", get_ss_command))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list_command))
    dp.add_handler(CommandHandler("get_services", get_services_command))
    dp.add_handler(CommandHandler("get_emails", get_emails_command))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers_command))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs_command))

    # Запускаем бота
    logger.info("Setup complete, launching bot")
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
