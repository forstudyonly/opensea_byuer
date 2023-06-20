from mysql.connector import connect, Error

from core.settings import settings

host, user, password, database = settings.host.host_value, settings.user.user_value, settings.password.pass_value, settings.database.database_value


def bd_add_link(name, min_price, max_price):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `name` FROM `collections` WHERE `name` = '{name}'")
                result = cursor.fetchall()
                print(result)
                if not result:
                    cursor.execute(f"INSERT INTO `collections` (name, min_price, max_price, ignored) VALUES (%s, %s, "
                                   f"%s, %s)", (name, min_price, max_price, 0))
                    cursor.fetchall()
                    connection.commit()
                    return "suc"
                return result[0][0]

    except Error as e:
        print(e)


def bd_delete_link(name):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `name` FROM `collections` WHERE `name` = '{name}'")
                result = cursor.fetchall()
                print(result)
                if result:
                    cursor.execute(f"DELETE FROM `collections` WHERE `name` = '{name}'")
                    result = cursor.fetchall()
                    connection.commit()
                    return "suc"
                return "no"

    except Error as e:
        print(e)


def bd_get_links():
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `name`, `min_price`, `max_price`, `ignored` FROM `collections`")
                result = cursor.fetchall()
                print(result)
                if not result:
                    return ""
                return result

    except Error as e:
        print(e)


def bd_get_range(name):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `name`, `min_price`, `max_price`, `ignored` FROM `collections` WHERE `name` = '{name}'")
                result = cursor.fetchall()
                print(result)
                if not result:
                    return ""
                return result

    except Error as e:
        print(e)


def bd_update_range(name, min_price, max_price):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE `collections` SET `min_price` = '{min_price}', `max_price` = '{max_price}' "
                               f"WHERE `name` = '{name}'")
                cursor.fetchall()
                connection.commit()
                return "suc"

    except Error as e:
        print(e)


def bd_get_percent():
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `percent` FROM `settings` WHERE `id` = 1")
                result = cursor.fetchall()
                # print(result)
                if not result:
                    return ""
                return result[0][0]

    except Error as e:
        print(e)


def bd_edit_percent(percent):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE `settings` SET `percent` = '{percent}' WHERE `id` = 1")
                cursor.fetchall()
                connection.commit()
                return "suc"

    except Error as e:
        print(e)


def bd_all_collections():
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `collections`")
                result = cursor.fetchall()
                # print(result)
                if not result:
                    return ""
                return result

    except Error as e:
        print(e)


def bd_check_user(chat_id):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `users` WHERE `tg_id` = '{chat_id}'")
                result = cursor.fetchall()
                print(result)
                if not result:
                    return ""
                return result

    except Error as e:
        print(e)


def bd_add_ignored(name, time_expired):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE `collections` SET `ignored` = 1,`date_expired` = '{time_expired}' WHERE `name` = '{name}'")
                result = cursor.fetchall()
                connection.commit()
                return "suc"

    except Error as e:
        print(e)


def bd_off_ignored(name):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE `collections` SET `ignored` = 0,`date_expired` = '' WHERE `name` = '{name}'")
                result = cursor.fetchall()
                connection.commit()
                return "suc"

    except Error as e:
        print(e)


def bd_get_ignored(link):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `time_expired` FROM `ignored` WHERE `link` = '{link}'")
                result = cursor.fetchall()
                print(result)
                if not result:
                    return ""
                return result[0][0]

    except Error as e:
        print(e)


def bd_get_all_ignored():
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `name`, `date_expired` FROM `collections` WHERE `ignored` = 1")
                result = cursor.fetchall()
                print(result)
                if not result:
                    return ""
                return result

    except Error as e:
        print(e)


def bd_delete_ignored(link):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `link` FROM `ignored` WHERE `link` = '{link}'")
                result = cursor.fetchall()
                print(result)
                if result:
                    cursor.execute(f"DELETE FROM `ignored` WHERE `link` = '{link}'")
                    result = cursor.fetchall()
                    connection.commit()
                    return "suc"
                return "no"

    except Error as e:
        print(e)


def bd_get_col_by_slug(slug):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `collections` WHERE `name` = '{slug}'")
                result = cursor.fetchall()
                if not result:
                    return ""
                return result[0]

    except Error as e:
        print(e)


def bd_get_gas_x():
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT `gas_price` FROM `settings` WHERE `id`=1")
                result = cursor.fetchall()
                print(result)
                if not result:
                    return ""
                return result[0][0]

    except Error as e:
        print(e)


def bd_update_gas_x(value):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE `settings` SET `gas_price` = '{value}' WHERE `id` =1")
                result = cursor.fetchall()
                connection.commit()
                return "suc"

    except Error as e:
        print(e)