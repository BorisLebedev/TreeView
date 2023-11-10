"""Модуль для классов конфигурации"""
from __future__ import annotations
from dataclasses import dataclass
import configparser


class Config:
    """ Родительский класс, который хранит методы
        общие для других классов конфигурации"""
    # pylint: disable = too-few-public-methods

    def __init__(self) -> None:
        self.readConfigData()

    def readConfigData(self):
        """Чтение settings.ini"""

        self.data = configparser.ConfigParser()
        try:
            self.data.read('settings.ini', encoding='utf-8')
        except configparser.MissingSectionHeaderError:
            self.data.read('settings.ini', encoding='utf-8-sig')
        except UnicodeDecodeError:
            self.data.read('settings.ini', encoding='cp1251')


class ConfigMain(Config):
    """ Отдельные параметры конфигурации, которые не
        выделить в специализированные классы"""

    def __init__(self):
        super().__init__()
        self.color_style = self.initColorStyle()
        self.fonts = self.initFontsStyle()
        self.icons = self.initIconsStyle()
        self.style = None

    def initColorStyle(self):
        """ Инициализация параметров цветовой схемы приложения"""

        cfg = 'main_settings'
        return CfgStyle(
            color_style_current=self.data[cfg]['color_style_current'],
            color_style_list=list(self.data[cfg]['color_style_list'].split(', '))
        )

    def initFontsStyle(self):
        """ Инициализация параметров шрифтов """

        cfg = 'fonts'
        return CfgFonts(
            font=self.data[cfg]['font'],
            font_size=int(self.data[cfg]['font_size']),
            font_size_big=int(self.data[cfg]['font_size_big']),
            font_size_toolbar=int(self.data[cfg]['font_size_toolbar']),
        )

    def initIconsStyle(self):
        """ Инициализация параметров шрифтов """

        cfg = 'gui'
        return CfgIcons(
            icons_white=self.data[cfg]['icons_white'],
            icons_black=self.data[cfg]['icons_black'],
        )

    def setCurrentStyle(self, style_name: str) -> None:
        """ Запись выбранного стиля приложения в файл конфигов """

        self.data['main_settings']['color_style_current'] = style_name
        with open('settings.ini', 'w', encoding='utf-8') as configfile:
            self.data.write(configfile)


class ConfigXLHierarchy(Config):
    """ Параметры для импорта и экспорта
        иерархических составов в Excel"""

    def __init__(self):
        super().__init__()
        self.xl_h_ntd = self.initExcelHierarchyNTD()
        self.xl_h_nrm = self.initExcelHierarchyNorm()
        self.xl_h_doc = self.initExcelHierarchyForDocuments()

    def initExcelHierarchyNTD(self):
        """ Инициализация параметров для экспорта данных иерархических составов
            в форму Excel для оценки трудоемкости сервисного обслуживания"""

        cfg = 'excel_table_ntd'
        return CfgXLHierarchyNTD(
            export_file_path=self.data[cfg]['export_file_path'],
            folder=self.data[cfg]['folder'],
            sheet_name=self.data[cfg]['sheet_name'],
            template_folder=self.data[cfg]['template_folder'],
            template_file=self.data[cfg]['template_file'],
            temp_folder=self.data[cfg]['temp_folder'],
            file_name_prefix=self.data[cfg]['file_name_prefix'],
            file_name_postfix=self.data[cfg]['file_name_postfix'],
            file_name_extension=self.data[cfg]['file_name_extension']
        )

    def initExcelHierarchyForDocuments(self):
        """ Инициализация параметров для импорта/экспорта данных
            иерархических составов из/в Excel"""

        cfg = 'excel_table'
        return CfgXLHierarchyForDocuments(
            folder=str(self.data[cfg]['folder']),
            deno_col=int(self.data[cfg]['deno_col']),
            name_col=int(self.data[cfg]['name_col']),
            type_col=int(self.data[cfg]['type_col']),
            index_col=int(self.data[cfg]['index_col']),
            sheet_name=str(self.data[cfg]['sheet_name']),
            ilgach_dep=str(self.data[cfg]['ilgach_dep']).replace(' ', '').split(','),
            temp_folder=str(self.data[cfg]['temp_folder']),
            doc_td_deno=int(self.data[cfg]['doc_td_deno']),
            mk_type_col=int(self.data[cfg]['mk_type_col']),
            mk_code_col=int(self.data[cfg]['mk_code_col']),
            doc_type_row=int(self.data[cfg]['doc_type_row']),
            doc_last_col=int(self.data[cfg]['doc_last_col']),
            upd_date_col=int(self.data[cfg]['upd_date_col']),
            mk_place_col=int(self.data[cfg]['mk_place_col']),
            quantity_col=int(self.data[cfg]['quantity_col']),
            template_file=str(self.data[cfg]['template_file']),
            doc_first_col=int(self.data[cfg]['doc_first_col']),
            purchased_col=int(self.data[cfg]['purchased_col']),
            template_folder=str(self.data[cfg]['template_folder']),
            doc_td_org_type=int(self.data[cfg]['doc_td_org_type']),
            export_file_path=str(self.data[cfg]['export_file_path']),
            doc_type_col_fin=int(self.data[cfg]['doc_type_col_fin']),
            file_name_prefix=str(self.data[cfg]['file_name_prefix']),
            file_name_postfix=str(self.data[cfg]['file_name_postfix']),
            doc_type_col_start=int(self.data[cfg]['doc_type_col_start']),
            file_name_extension=str(self.data[cfg]['file_name_extension']),
            primary_application_col=int(self.data[cfg]['primary_application_col']),
            product_type_exceptions=str(self.data[cfg]['product_type_exceptions']).split(', ')
        )

    def initExcelHierarchyNorm(self):
        """ Инициализация параметров для экспорта данных иерархических составов
            в форму Excel для оценки трудоемкости изготовления изделия"""

        cfg = 'excel_table_norm'
        return CfgXLHierarchyNorm(
            folder=self.data[cfg]['folder'],
            sheet_name=self.data[cfg]['sheet_name'],
            temp_folder=self.data[cfg]['temp_folder'],
            template_file=self.data[cfg]['template_file'],
            template_folder=self.data[cfg]['template_folder'],
            export_file_path=self.data[cfg]['export_file_path'],
            file_name_prefix=self.data[cfg]['file_name_prefix'],
            file_name_postfix=self.data[cfg]['file_name_postfix'],
            file_name_extension=self.data[cfg]['file_name_extension']
        )


class ConfigXLTechDocDb(Config):
    """ Содержит параметры для импорта реквизитов технологических
        документов из таблицы с данными их регистрации"""

    def __init__(self):
        super().__init__()
        self.xl_td = self.initExcelTechDocDb()

    def initExcelTechDocDb(self):
        """ Инициализация параметров для экспорта данных иерархических составов
            в форму Excel для оценки трудоемкости сервисного обслуживания"""

        cfg = 'dbtd'
        return CfgXLTechDocDb(
            folder=str(self.data[cfg]['folder']),
            col_name=int(self.data[cfg]['col_name']),
            file_name=str(self.data[cfg]['file_name']),
            start_row=int(self.data[cfg]['start_row']),
            col_stage=int(self.data[cfg]['col_stage']),
            sheet_name=str(self.data[cfg]['sheet_name']),
            col_deno_td=int(self.data[cfg]['col_deno_td']),
            col_deno_kd=int(self.data[cfg]['col_deno_kd']),
            col_reg_fio=int(self.data[cfg]['col_reg_fio']),
            col_dev_fio=int(self.data[cfg]['col_dev_fio']),
            col_complex=int(self.data[cfg]['col_complex']),
            col_reg_date=int(self.data[cfg]['col_reg_date']),
            col_dev_date=int(self.data[cfg]['col_dev_date']),
            col_canceled=int(self.data[cfg]['col_canceled']),
            col_norm_num=int(self.data[cfg]['col_norm_num']),
            col_first_app=int(self.data[cfg]['col_first_app']),
            col_norm_date=int(self.data[cfg]['col_norm_date']),
            col_archive_num=int(self.data[cfg]['col_archive_num']),
            col_canceled_date=int(self.data[cfg]['col_canceled_date'])
        )


class ConfigXLMk(Config):
    """ Содержит параметры для создания маршрутной карты """

    def __init__(self):
        super().__init__()
        self.main = self.initXLMkDocument()
        self.file = self.initXLMkDocFilePath()
        self.col = self.initXLMkDocTextCol()
        self.row = self.initXLMkDocTextRow()
        self.first_page = self.initXLMkDocTextFp()
        self.last_page = self.initXLMkDocTextLp()
        self.doc_details = self.initDocumentDetails()

    def initXLMkDocument(self) -> CfgXLMkDocument:
        """ Инициализация настроек маршрутной карты,
            которые по смыслу не структурировать в
            отдельные классы"""
        cfg = 'excel_document'
        return CfgXLMkDocument(
            excel_len=int(self.data[cfg]['excel_len']),
            ws_text_name=self.data[cfg]['ws_text_name'],
            excel_len_iot=int(self.data[cfg]['excel_len_iot']),
            subtype_names=self.data[cfg]['subtype_names'].split(','),
            word_exception=self.data[cfg]['word_exception'],
            free_space_crit=int(self.data[cfg]['free_space_crit']),
            rows_to_push_up=int(self.data[cfg]['rows_to_push_up']),
            ws_template_name=self.data[cfg]['ws_template_name'],
            default_operation=self.data[cfg]['default_operation'],
            related_documents=self.data[cfg]['related_documents'],
            free_space_crit_fp=int(self.data[cfg]['free_space_crit_fp']),
            ws_first_page_name=self.data[cfg]['ws_first_page_name'],
            additional_control_text=self.data[cfg]['additional_control_text'],
            product_type_exceptions=self.data[cfg]['product_type_exceptions'].split(', '),
            rows_between_operations=int(self.data[cfg]['rows_between_operations'])
        )

    def initXLMkDocTextCol(self) -> CfgXLMkDocTextCol:
        """ Инициализация столбцов для реквизитов
            и текста маршрутной карты """
        cfg = 'excel_document'
        return CfgXLMkDocTextCol(
            col_docs=int(self.data[cfg]['col_docs']),
            col_page=int(self.data[cfg]['col_page']),
            col_litera=int(self.data[cfg]['col_litera']),
            col_checker=int(self.data[cfg]['col_checker']),
            col_docs_fp=int(self.data[cfg]['col_docs_fp']),
            col_m_contr=int(self.data[cfg]['col_m_contr']),
            col_n_contr=int(self.data[cfg]['col_n_contr']),
            col_page_fp=int(self.data[cfg]['col_page_fp']),
            col_approver=int(self.data[cfg]['col_approver']),
            col_area_end=int(self.data[cfg]['col_area_end']),
            col_area_fst=int(self.data[cfg]['col_area_fst']),
            col_prof_end=int(self.data[cfg]['col_prof_end']),
            col_prof_fst=int(self.data[cfg]['col_prof_fst']),
            col_developer=int(self.data[cfg]['col_developer']),
            col_k_num_end=int(self.data[cfg]['col_k_num_end']),
            col_k_num_fst=int(self.data[cfg]['col_k_num_fst']),
            col_main_text=int(self.data[cfg]['col_main_text']),
            col_operation=int(self.data[cfg]['col_operation']),
            col_str_index=int(self.data[cfg]['col_str_index']),
            col_workplace=int(self.data[cfg]['col_workplace']),
            col_page_total=int(self.data[cfg]['col_page_total']),
            col_prof_end_fp=int(self.data[cfg]['col_prof_end_fp']),
            col_prof_fst_fp=int(self.data[cfg]['col_prof_fst_fp']),
            col_product_deno=int(self.data[cfg]['col_product_deno']),
            col_document_deno=int(self.data[cfg]['col_document_deno']),
            col_document_name=int(self.data[cfg]['col_document_name']),
            col_norm_code_end=int(self.data[cfg]['col_norm_code_end']),
            col_norm_code_fst=int(self.data[cfg]['col_norm_code_fst']),
            col_product_deno_fp=int(self.data[cfg]['col_product_deno_fp']),
            col_document_deno_fp=int(self.data[cfg]['col_document_deno_fp']),
            col_document_name_fp=int(self.data[cfg]['col_document_name_fp']),
            col_operation_number=int(self.data[cfg]['col_operation_number'])
        )

    def initXLMkDocTextRow(self) -> CfgXLMkDocTextRow:
        """ Инициализация номеров строк для реквизитов
            и текста маршрутной карты """
        cfg = 'excel_document'
        return CfgXLMkDocTextRow(
            row_page=int(self.data[cfg]['row_page']),
            row_start=int(self.data[cfg]['row_start']),
            row_total=int(self.data[cfg]['row_total']),
            row_litera=int(self.data[cfg]['row_litera']),
            row_checker=int(self.data[cfg]['row_checker']),
            row_m_contr=int(self.data[cfg]['row_m_contr']),
            row_n_contr=int(self.data[cfg]['row_n_contr']),
            row_approver=int(self.data[cfg]['row_approver']),
            row_start_fp=int(self.data[cfg]['row_start_fp']),
            row_total_fp=int(self.data[cfg]['row_total_fp']),
            row_developer=int(self.data[cfg]['row_developer']),
            text_row_last=int(self.data[cfg]['text_row_last']),
            text_row_first=int(self.data[cfg]['text_row_first']),
            row_product_deno=int(self.data[cfg]['row_product_deno']),
            row_document_deno=int(self.data[cfg]['row_document_deno']),
            row_document_name=int(self.data[cfg]['row_document_name']),
            fp_text_row_first=int(self.data[cfg]['fp_text_row_first']),
            row_document_name_fp=int(self.data[cfg]['row_document_name_fp']),
        )

    def initXLMkDocTextFp(self) -> CfgXLMkDocTextFp:
        """ Инициализация общего текста маршрутной карты """
        cfg = 'excel_document'
        return CfgXLMkDocTextFp(
            first_page_text_inst=self.data[cfg]['first_page_text_inst'],
            first_page_text_iots=self.data[cfg]['first_page_text_iots'],
            first_page_text_mat1=self.data[cfg]['first_page_text_mat1'],
            first_page_text_mat2=self.data[cfg]['first_page_text_mat2'],
            first_page_text_met1=self.data[cfg]['first_page_text_met1'],
            first_page_text_prof=self.data[cfg]['first_page_text_prof'],
            first_page_text_stat=self.data[cfg]['first_page_text_stat'],
            first_page_text_wkpl=self.data[cfg]['first_page_text_wkpl'],
            first_page_text_abbr_po=self.data[cfg]['first_page_text_abbr_po'],
            first_page_text_abbr_tu=self.data[cfg]['first_page_text_abbr_tu'],
            first_page_text_abbr_nku=self.data[cfg]['first_page_text_abbr_nku'],
            first_page_text_abbr_spo=self.data[cfg]['first_page_text_abbr_spo'],
            first_page_text_abbrlist=self.data[cfg]['first_page_text_abbrlist'],
            first_page_text_abbr_po_find=self.data[cfg]['first_page_text_abbr_po_find'],
            first_page_text_abbr_tu_find=self.data[cfg]['first_page_text_abbr_tu_find'],
            first_page_text_abbr_nku_find=self.data[cfg]['first_page_text_abbr_nku_find'],
            first_page_text_abbr_spo_find=self.data[cfg]['first_page_text_abbr_spo_find']
        )

    def initXLMkDocTextLp(self) -> CfgXLMkDocTextLp:
        """ Инициализация параметров текста иерархического
            раскрытия изделия маршрутной карты """
        cfg = 'excel_document'
        return CfgXLMkDocTextLp(
            by_document=self.data[cfg]['by_document'],
            in_document=self.data[cfg]['in_document'],
            document_not_found=self.data[cfg]['document_not_found'],
            ed_document_prefix=self.data[cfg]['ed_document_prefix'],
            ed_document_postfix=self.data[cfg]['ed_document_postfix'],
            ed_document_quantity=self.data[cfg]['ed_document_quantity'],
            last_page_start_text=self.data[cfg]['last_page_start_text'],
            first_page_text_iots=self.data[cfg]['first_page_text_iots'],
            first_page_text_prof=self.data[cfg]['first_page_text_prof'],
            first_page_text_wkpl=self.data[cfg]['first_page_text_wkpl'],
            first_page_text_mat1=self.data[cfg]['first_page_text_mat1'],
            first_page_text_mat2=self.data[cfg]['first_page_text_mat2'],
            first_page_text_met1=self.data[cfg]['first_page_text_met1'],
            first_page_text_inst=self.data[cfg]['first_page_text_inst'],
            first_page_text_stat=self.data[cfg]['first_page_text_stat'],
            first_page_text_abbr_tu=self.data[cfg]['first_page_text_abbr_tu'],
            first_page_text_abbr_po=self.data[cfg]['first_page_text_abbr_po'],
            first_page_text_abbr_spo=self.data[cfg]['first_page_text_abbr_spo'],
            first_page_text_abbr_nku=self.data[cfg]['first_page_text_abbr_nku'],
            first_page_text_abbr_tu_find=self.data[cfg]['first_page_text_abbr_tu_find'][1:][:-1],
            first_page_text_abbr_po_find=self.data[cfg]['first_page_text_abbr_po_find'][1:][:-1],
            first_page_text_abbr_spo_find=self.data[cfg]['first_page_text_abbr_spo_find'][1:][:-1],
            first_page_text_abbr_nku_find=self.data[cfg]['first_page_text_abbr_nku_find'][1:][:-1],
            first_page_text_abbrlist=self.data[cfg]['first_page_text_abbrlist'],
        )

    def initXLMkDocFilePath(self) -> CfgXLMkDocFilePath:
        """ Инициализация файловых путей при
            создании маршрутной карты """
        cfg = 'excel_document'
        return CfgXLMkDocFilePath(
            file_path=self.data[cfg]['file_path'],
            template_name=self.data[cfg]['template_name'],
            template_folder=self.data[cfg]['template_folder'],
            document_extension=self.data[cfg]['document_extension'],
        )

    def initDocumentDetails(self) -> CfgXLDocumentDetails:
        """ Инициализация реквизитов документа по-умолчанию """
        cfg = 'document_settings'
        return CfgXLDocumentDetails(
            litera=self.data[cfg]['litera'],
            stages=self.data[cfg]['stages'],
            checker=self.data[cfg]['checker'],
            n_contr=self.data[cfg]['n_contr'],
            m_contr=self.data[cfg]['m_contr'],
            approver=self.data[cfg]['approver'],
            developer=self.data[cfg]['developer'],
            name_checker=self.data[cfg]['name_checker'],
            name_n_contr=self.data[cfg]['name_n_contr'],
            name_m_contr=self.data[cfg]['name_m_contr'],
            name_approver=self.data[cfg]['name_approver'],
            name_developer=self.data[cfg]['name_developer'],
        )


class ConfigDb(Config):
    """ Параметры конфигурации для работы с БД """

    def __init__(self):
        super().__init__()
        self.main = self.initDbMain()
        self.sqlite = self.initDbSQLite()
        self.pstgr = self.initDbPostgreSQL()

    def initDbMain(self):
        """ Общие параметры для различных БД """
        cfg = 'db'
        return CfgDbMain(
            db_type=self.data[cfg]['db_type'],
            folder=self.data[cfg]['folder'],
            file_name=self.data[cfg]['file_name'],
        )

    def initDbSQLite(self):
        """ Параметры SQLite """
        cfg = 'SQLite'
        return CfgDbSQLite(
            timeout=int(self.data[cfg]['timeout']),
            pragma_synchronous=self.data[cfg]['pragma_synchronous'],
            pragma_journal_mode=self.data[cfg]['pragma_journal_mode'],
        )

    def initDbPostgreSQL(self):
        """ Параметры PostgreSQL """
        cfg = 'PostgreSQL'
        return CfgDbPostgreSQL(
            placeholder=self.data[cfg]['placeholder'],
        )


class ConfigPLM(Config):
    """ Параметры конфигурации для работы с PLM системой """

    def __init__(self):
        super().__init__()
        self.main = self.initMain()

    def initMain(self):
        """ Основные параметры для работы с PLM системой """

        cfg = 'PLM'
        return CfgPLM(
            folder_kd=self.data[cfg]['folder_kd'],
            folder_td=self.data[cfg]['folder_td'],
        )


@dataclass
class CfgStyle:
    """ Параметры стиля приложения """

    color_style_current: str
    color_style_list: list[str]


@dataclass
class CfgFonts:
    """ Параметры шрифтов """

    font: str
    font_size: int
    font_size_big: int
    font_size_toolbar: int


@dataclass
class CfgIcons:
    """ Параметры иконок """

    icons_white: str
    icons_black: str


@dataclass
class CfgXLHierarchyForDocuments:
    """ Параметры для импорта/экспорта данных
        иерархических составов из/в Excel"""

    # pylint: disable=too-many-instance-attributes

    folder: str
    deno_col: int
    name_col: int
    type_col: int
    index_col: int
    sheet_name: str
    ilgach_dep: list[str]
    temp_folder: str
    doc_td_deno: int
    mk_type_col: int
    mk_code_col: int
    doc_type_row: int
    doc_last_col: int
    upd_date_col: int
    mk_place_col: int
    quantity_col: int
    template_file: str
    doc_first_col: int
    purchased_col: int
    template_folder: str
    doc_td_org_type: int
    export_file_path: str
    doc_type_col_fin: int
    file_name_prefix: str
    file_name_postfix: str
    doc_type_col_start: int
    file_name_extension: str
    primary_application_col: int
    product_type_exceptions: list[str]


@dataclass
class CfgXLTechDocDb:
    """ Параметры для экспорта данных маршрутной карты в Excel"""

    # pylint: disable=too-many-instance-attributes

    folder: str
    col_name: int
    file_name: str
    start_row: int
    col_stage: int
    sheet_name: str
    col_deno_td: int
    col_deno_kd: int
    col_reg_fio: int
    col_dev_fio: int
    col_complex: int
    col_reg_date: int
    col_dev_date: int
    col_canceled: int
    col_norm_num: int
    col_first_app: int
    col_norm_date: int
    col_archive_num: int
    col_canceled_date: int


@dataclass
class CfgXLHierarchyNorm:
    """ Параметры для экспорта данных иерархических составов
        в форму Excel для оценки трудоемкости изготовления изделия"""

    # pylint: disable=too-many-instance-attributes

    folder: str
    sheet_name: str
    temp_folder: str
    template_file: str
    template_folder: str
    export_file_path: str
    file_name_prefix: str
    file_name_postfix: str
    file_name_extension: str


@dataclass
class CfgXLHierarchyNTD:
    """ Параметры для экспорта данных иерархических составов
        в форму Excel для оценки трудоемкости сервисного обслуживания"""

    # pylint: disable=too-many-instance-attributes

    export_file_path: str
    folder: str
    sheet_name: str
    template_folder: str
    template_file: str
    temp_folder: str
    file_name_prefix: str
    file_name_postfix: str
    file_name_extension: str


@dataclass
class CfgXLMkDocument:
    """ Параметры для создания маршрутной карты  """

    # pylint: disable=too-many-instance-attributes

    excel_len: int
    ws_text_name: str
    excel_len_iot: int
    subtype_names: list[str]
    word_exception: str
    free_space_crit: int
    rows_to_push_up: int
    ws_template_name: str
    default_operation: str
    related_documents: str
    free_space_crit_fp: int
    ws_first_page_name: str
    additional_control_text: str
    product_type_exceptions: list[str]
    rows_between_operations: int


@dataclass
class CfgXLMkDocTextCol:
    """ Хранит данные о номерах столбцов
        для текста маршрутной карты"""

    # pylint: disable=too-many-instance-attributes

    col_docs: int
    col_page: int
    col_litera: int
    col_checker: int
    col_docs_fp: int
    col_m_contr: int
    col_n_contr: int
    col_page_fp: int
    col_approver: int
    col_area_end: int
    col_area_fst: int
    col_prof_end: int
    col_prof_fst: int
    col_developer: int
    col_k_num_end: int
    col_k_num_fst: int
    col_main_text: int
    col_operation: int
    col_str_index: int
    col_workplace: int
    col_page_total: int
    col_prof_end_fp: int
    col_prof_fst_fp: int
    col_product_deno: int
    col_document_deno: int
    col_document_name: int
    col_norm_code_end: int
    col_norm_code_fst: int
    col_product_deno_fp: int
    col_document_deno_fp: int
    col_document_name_fp: int
    col_operation_number: int


@dataclass
class CfgXLMkDocTextRow:
    """ Хранит данные о номерах строк
        для текста маршрутной карты"""

    # pylint: disable=too-many-instance-attributes

    row_page: int
    row_start: int
    row_total: int
    row_litera: int
    row_checker: int
    row_m_contr: int
    row_n_contr: int
    row_approver: int
    row_start_fp: int
    row_total_fp: int
    row_developer: int
    text_row_last: int
    text_row_first: int
    row_product_deno: int
    row_document_deno: int
    row_document_name: int
    fp_text_row_first: int
    row_document_name_fp: int


@dataclass
class CfgXLMkDocTextFp:
    """ Хранит текст переходов для
        общих данных маршрутной карты"""

    # pylint: disable=too-many-instance-attributes

    first_page_text_inst: str
    first_page_text_iots: str
    first_page_text_mat1: str
    first_page_text_mat2: str
    first_page_text_met1: str
    first_page_text_prof: str
    first_page_text_stat: str
    first_page_text_wkpl: str
    first_page_text_abbr_po: str
    first_page_text_abbr_tu: str
    first_page_text_abbr_nku: str
    first_page_text_abbr_spo: str
    first_page_text_abbrlist: str
    first_page_text_abbr_po_find: str
    first_page_text_abbr_tu_find: str
    first_page_text_abbr_nku_find: str
    first_page_text_abbr_spo_find: str


@dataclass
class CfgXLMkDocFilePath:
    """ Хранит пути для создания маршрутной карты"""

    file_path: str
    template_name: str
    template_folder: str
    document_extension: str


@dataclass
class CfgXLMkDocTextLp:
    """ Хранит текст переходов для
        общих данных маршрутной карты"""

    # pylint: disable=too-many-instance-attributes

    by_document: str
    in_document: str
    document_not_found: str
    ed_document_prefix: str
    ed_document_postfix: str
    ed_document_quantity: str
    last_page_start_text: str
    first_page_text_iots: str
    first_page_text_prof: str
    first_page_text_wkpl: str
    first_page_text_mat1: str
    first_page_text_mat2: str
    first_page_text_met1: str
    first_page_text_inst: str
    first_page_text_stat: str
    first_page_text_abbr_tu: str
    first_page_text_abbr_po: str
    first_page_text_abbr_spo: str
    first_page_text_abbr_nku: str
    first_page_text_abbr_tu_find: str
    first_page_text_abbr_po_find: str
    first_page_text_abbr_spo_find: str
    first_page_text_abbr_nku_find: str
    first_page_text_abbrlist: str


@dataclass
class CfgXLDocumentDetails:
    """ Хранит текст переходов для
        общих данных маршрутной карты"""
    # pylint: disable=too-many-instance-attributes

    litera: str
    stages: str
    checker: str
    n_contr: str
    m_contr: str
    approver: str
    developer: str
    name_checker: str
    name_n_contr: str
    name_m_contr: str
    name_approver: str
    name_developer: str


@dataclass
class CfgDbMain:
    """ Общие параметры для различных БД """

    db_type: str
    folder: str
    file_name: str


@dataclass
class CfgDbSQLite:
    """ Параметры SQLite """

    timeout: int
    pragma_synchronous: str
    pragma_journal_mode: str


@dataclass
class CfgDbPostgreSQL:
    """ Параметры PostgreSQL """

    placeholder: str


@dataclass
class CfgPLM:
    """ Параметры конфигурации для работы с
        выгрузками из PLM системы """
    folder_kd: str
    folder_td: str


CONFIG = ConfigMain()
CFG_HR = ConfigXLHierarchy()
CFG_TD = ConfigXLTechDocDb()
CFG_MK = ConfigXLMk()
CFG_DB = ConfigDb()
CFG_PLM = ConfigPLM()
