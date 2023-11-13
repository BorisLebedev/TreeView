""" Функции для нестандартного изменения БД """
import logging
import sqlite3
import sys


class SizeMsg:
    """ Определяет размер данных и сохраняет в глобальную переменную
        сумму размеров поступивших данных """
    total_size_of_data = 0

    def __init__(self, result, show: bool = True, reset: bool = False):
        self.__class__.resetTotalSize(reset=reset)
        self.result_size = self.measure(result=result)
        self.showMsg(show)

    @classmethod
    def resetTotalSize(cls, reset: bool):
        """ Обнуляет сумму поступивших данных """
        if reset:
            cls.total_size_of_data = 0

    @staticmethod
    def measure(result):
        """ Определяет размер поступивших данных """
        return int(sys.getsizeof(result) / 8)

    def showMsg(self, show: bool):
        """ Выводит сообщение в лог """
        if show:
            msg = f'{self.result_size / 1000} kB всего ' \
                  f'{self.__class__.total_size_of_data / 1000} kB'
            logging.debug(msg)


def alter_table_sqlite(db_name: str, text: str) -> None:
    """Подключение к БД SQLite и изменение БД"""

    logging.debug('Connecting to db')
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    sql_text = text
    cur.execute(f"{sql_text}")
    conn.commit()


def modify_database(file_path: str, name: str) -> None:
    """ Функция через которую можно исполнить SQL выражение"""

    alter_table_sqlite(db_name=file_path + name,
                       text='UPDATE product SET id_kind = 9 '
                            'WHERE purchased IS NOT NULL AND purchased <> ""')

    alter_table_sqlite(db_name=file_path + name,
                       text='ALTER TABLE product_type ADD id_kind INTEGER')

    alter_table_sqlite(db_name=file_path + name,
                       text='ALTER TABLE excel_project ADD id_product INTEGER')

    alter_table_sqlite(db_name=file_path + name,
                       text="""CREATE TABLE excel_project_1 (
                               id_project INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                               project_name TEXT NOT NULL,
                               id_product INTEGER,
                               FOREIGN KEY (id_product) REFERENCES product(id_product)
                               )""")

    alter_table_sqlite(db_name=file_path + name,
                       text='PRAGMA foreign_keys = OFF')

    alter_table_sqlite(db_name=file_path + name,
                       text="""INSERT INTO excel_project_1(id_project, project_name)
                        SELECT id_project, project_name FROM excel_project""")

    alter_table_sqlite(db_name=file_path + name,
                       text="""DROP TABLE excel_project""")

    alter_table_sqlite(db_name=file_path + name,
                       text="""ALTER TABLE excel_project_1 RENAME TO excel_project""")

    alter_table_sqlite(db_name=file_path + name,
                       text="""INSERT INTO excel_project_1(id_project, project_name)
                        SELECT id_project, project_name FROM excel_project
                        WHERE id_project NOT IN (SELECT id_project FROM excel_project_1)""")

    alter_table_sqlite(db_name=file_path + name,
                       text='PRAGMA foreign_keys = OFF')

    alter_table_sqlite(db_name=file_path + name,
                       text="""DROP TABLE excel_project""")

    alter_table_sqlite(db_name=file_path + name,
                       text='PRAGMA foreign_keys = ON')

    alter_table_sqlite(db_name=file_path + name,
                       text="""CREATE TABLE users (
                        id_user INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        surname TEXT,
                        patronymic TEXT,
                        user_name TEXT,
                        password TEXT,
                        id_product_last INTEGER,
                        FOREIGN KEY (id_product_last) REFERENCES product(id_product)
                        )""")

    alter_table_sqlite(db_name=file_path + name,
                       text="""ALTER TABLE hierarchy ADD COLUMN unit TEXT""")

    alter_table_sqlite(db_name=file_path + name,
                       text="""UPDATE hierarchy SET unit='шт' WHERE quantity <> ''""")


def repair_floats(session, hierarchy) -> None:
    hierarchy.updData()
    for item in hierarchy.data.values():
        try:
            item.quantity = float(item.quantity)
        except ValueError:
            if "," in item.quantity:
                item.quantity = float(str(item.quantity).replace(",", "."))
    session.commit()
