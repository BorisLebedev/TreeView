"""Модуль для заполнения БД данными по-умолчанию"""

from os import path

from pandas import read_excel

from STC.config.config import CONFIG
from STC.gui.splash_screen import SplashScreen


def add_default_data(engine) -> None:
    """
    Проходит по таблицам БД и вызывает функцию,
    заполняющую таблицы данными по-умолчанию
    """

    directory = CONFIG.data['db']['ini_data_folder']
    file = CONFIG.data['db']['ini_data_name']
    type_table_file = path.join(directory, file)

    tables = [{'sheet_name': 'document_type',
               'index_label': 'id_type',
               'first_row': 0},

              {'sheet_name': 'product_type',
               'index_label': 'id_type',
               'first_row': 0},

              {'sheet_name': 'product_kind',
               'index_label': 'id_kind',
               'first_row': 0},

              {'sheet_name': 'document_stage',
               'index_label': 'id_document_stage',
               'first_row': 0},

              {'sheet_name': 'document_real',
               'index_label': 'id_document_real',
               'first_row': 0},

              {'sheet_name': 'workplace',
               'index_label': 'id_workplace',
               'first_row': 0},

              {'sheet_name': 'area',
               'index_label': 'id_area',
               'first_row': 0},

              {'sheet_name': 'operation',
               'index_label': 'id_operation',
               'first_row': 1},

              {'sheet_name': 'setting',
               'index_label': 'id_setting',
               'first_row': 1},

              {'sheet_name': 'sentence',
               'index_label': 'id_sentence',
               'first_row': 1},

              {'sheet_name': 'setting_def',
               'index_label': 'id_setting_def',
               'first_row': 1},

              {'sheet_name': 'rig',
               'index_label': 'id_rig',
               'first_row': 0},

              {'sheet_name': 'rig_def',
               'index_label': 'id_rig_def',
               'first_row': 1},

              {'sheet_name': 'doc_def',
               'index_label': 'id_doc_def',
               'first_row': 1},

              {'sheet_name': 'equipment',
               'index_label': 'id_equipment',
               'first_row': 0},

              {'sheet_name': 'equipment_def',
               'index_label': 'id_equipment_def',
               'first_row': 1},

              {'sheet_name': 'material',
               'index_label': 'id_material',
               'first_row': 0},

              {'sheet_name': 'material_def',
               'index_label': 'id_material_def',
               'first_row': 1},

              {'sheet_name': 'iot',
               'index_label': 'id_iot',
               'first_row': 0},

              {'sheet_name': 'iot_def',
               'index_label': 'id_iot_def',
               'first_row': 1},

              {'sheet_name': 'profession',
               'index_label': 'id_profession',
               'first_row': 0},

              {'sheet_name': 'operation_def',
               'index_label': 'id_operation_def',
               'first_row': 1},
              ]

    for table in tables:
        insert_data(sheet_name=table['sheet_name'],
                    index_label=table['index_label'],
                    first_row=table['first_row'],
                    type_table_file=type_table_file,
                    engine=engine)


def insert_data(sheet_name, index_label, first_row, type_table_file, engine):
    """Заполняет функцию данными по-умолчанию из файла excel"""

    default = 'Заполнение значений по умолчанию для'
    SplashScreen().newMessage(message=f'{default} {sheet_name}',
                              hide_pb=True)
    type_table = read_excel(type_table_file, sheet_name=sheet_name)
    type_table[first_row:].to_sql(sheet_name,
                                  con=engine,
                                  if_exists='append',
                                  index_label=index_label)
