""" Классы ORM модели и функции для работы с БД """
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy import delete
from sqlalchemy import event
from sqlalchemy import exc
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.orm import Query
from sqlalchemy.orm import aliased
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy.sql import and_
from sqlalchemy.sql import or_
from sqlalchemy.sql.expression import literal
from sqlalchemy_utils import database_exists

from STC.config.config import CFG_DB
from STC.database.create import add_default_data
from STC.functions.func import null_cleaner, add_missing_keys, upd_attrs
from STC.gui.splash_screen import SplashScreen
from STC.gui.splash_screen import show_dialog

if TYPE_CHECKING:
    from STC.product.product import DocumentType
    from STC.product.product import Operation
    from STC.product.product import Sentence


Base = declarative_base()


class DbConnection:
    """ Агрегирует методы работы с БД """

    session = None
    file_path = ''
    file_name = ''
    sub_status_bar_max_stage = 10

    @classmethod
    def initSession(cls, file_path: str, file_name: str):
        """ Возвращает сессию для работы с БД """
        cls.file_path = file_path
        cls.file_name = file_name
        engine = cls.getEngine()
        cls.createDatabaseIfNotExist(engine=engine)
        SplashScreen().newMessage(message='База данных найдена',
                                  log=True,
                                  logging_level='INFO')
        session_cls = sessionmaker(engine,
                                   autoflush=False,
                                   future=True,
                                   expire_on_commit=False)
        # engine.execution_options(stream_results=True)
        with session_cls() as cls.session:
            cls.session = session_cls()

    @classmethod
    def getEngine(cls):
        """ Возвращает engine согласно типу в файле конфигурации"""
        match CFG_DB.main.db_type:
            case 'SQLite':
                prefix = 'sqlite:///'
                engine_path = prefix + cls.file_path + cls.file_name
                return create_engine(engine_path,
                                     connect_args={'timeout': CFG_DB.sqlite.timeout},
                                     echo=False)
            case 'PostgreSQL':
                return create_engine('postgresql+psycopg2://postgres:stc123@localhost:5432/STC_DB')

    @classmethod
    def createDatabaseIfNotExist(cls, engine):
        """ Создает БД согласно классам ORM модели """
        inspection = inspect(engine)
        product_table_not_exist = 'product' not in inspection.get_table_names()
        if not database_exists(engine.url) or product_table_not_exist:
            SplashScreen().newMessage(message='База данных не найдена.\n'
                                              'Создание новой базы данных',
                                      log=True,
                                      logging_level='INFO')
            Base.metadata.create_all(engine)
            add_default_data(engine=engine)

    @classmethod
    def reconnection(cls, error: BaseException | None):
        """ Переподключается к БД при потере соединения
            и обновляет кэшированные данные """
        cls.session.close()
        SplashScreen().closeWithWindow()
        error_msg = f'{error}\n' if error is not None else ''
        show_dialog(f'Не удалось внести данные.\n{error_msg}Попробовать еще раз?')
        cls.initSession(file_path=cls.file_path,
                        file_name=cls.file_name)
        cls.updAllData()
        SplashScreen().closeWithWindow()

    @classmethod
    def updAllData(cls) -> None:
        """ Обновляет кэшированные данные """
        cls.resetData()
        DbProduct.updData()
        DbUsers.updData()
        DbProductType.updData()
        DbProductKind.updData()
        DbPrimaryApplication.updData()
        DbDocumentStage.updData()
        DbDocumentType.updData()
        # DbProduct.updAllProductKinds()

    @classmethod
    def resetData(cls) -> None:
        """ Сбрасывает хранимые данные """
        cls.resetMainData()
        cls.resetMkData()

    @staticmethod
    def resetMainData() -> None:
        """ Сбрасывает хранимые данные для формирования главной таблицы иерархии """
        DbProduct.data = {}
        DbUsers.data = {}
        DbProductType.data = {}
        DbProductKind.data = {}
        DbHierarchy.data = {}
        DbDocumentReal.data = {}
        DbDocument.data = {}
        DbPrimaryApplication.data = {}
        DbDocumentStage.data = {}
        DbDocumentType.data = {}
        DbDocumentTdComplex.data = {}
        DbDocumentSignature.data = {}

    @staticmethod
    def resetMkData() -> None:
        """ Сбрасывает хранимые данные для формирования маршрутных карт """
        DbArea.data = {}
        DbWorkplace.data = {}
        DbOperation.data = {}
        DbSetting.data = {}
        DbSentence.data = {}
        DbOperationDoc.data = {}
        DbSentenceDoc.data = {}
        DbMaterial.data = {}
        DbMaterialDef.data = {}
        DbMaterialDoc.data = {}
        DbRig.data = {}
        DbRigDef.data = {}
        DbRigDoc.data = {}
        DbIOT.data = {}
        DbIOTDef.data = {}
        DbIOTDoc.data = {}

    @classmethod
    def executeStatement(cls, statement, one=False):
        """ Метод выполняет sql запрос, учитывая случаи
            различных ошибок выполнения"""
        try:
            try:
                if one:
                    try:
                        data = cls.session.execute(statement).one()
                        result = data
                    except MultipleResultsFound:
                        result = DbConnection.executeStatement(statement)[0]
                    # data = DbConnection.session.execute(statement).one()
                    # result = data
                else:
                    data = DbConnection.session.execute(statement)
                    try:
                        result = tuple(data)
                    except ResourceClosedError:
                        result = None
            except NoResultFound:
                result = ()
        except OperationalError as err:
            DbConnection.reconnection(error=err)
            result = DbConnection.executeStatement(statement, one)
        return result

    @classmethod
    def sessionCommit(cls):
        """ Стандартный коммит, но gui выполнения """
        SplashScreen().writeToDB()
        cls.session.commit()
        SplashScreen().close()


class BaseMethods:
    """ Агрегирует общие методы, к которым обращаются все ORM классы.
        Позволяет избежать множественного и избыточного наследования
        Не выносить как модуль из-за циклических импортов """

    @staticmethod
    def updData(db_cls, title: str) -> None:
        """ Запрашивает данные таблицы БД и формирует словарь,
            согласно методу ORM класса """
        SplashScreen().basicReceive(title)
        statement = select(db_cls)
        _data = DbConnection.executeStatement(statement)
        _data_tuple = tuple(_data)
        amount = len(_data_tuple)
        SplashScreen().basicProceed(title)
        SplashScreen().changeSubProgressBar(stage=0,
                                            stages=amount)
        SplashScreen().changeSubProgressBar()
        for count, item in enumerate(_data_tuple):
            db_cls.addData(item=item[0])
            SplashScreen().changeSubProgressBar(stage=count,
                                                stages=amount)
        SplashScreen().changeSubProgressBar(stage=0,
                                            stages=0)
        SplashScreen().basicCompletion(title)

    @staticmethod
    def uniqueData(db_cls) -> list:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        db_cls.updCheck()
        return list(set(db_cls.data.values()))

    @staticmethod
    def updCheck(db_cls) -> None:
        """ Проверяет кэшированы ли данные для определенного
            класса ORM модели. Кэширует если нет """
        if not db_cls.data:
            db_cls.updData()

    @staticmethod
    def getData(db_cls,
                attr: tuple | str | int,
                in_cache: bool = False):
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД
            attr -> составной ключ из addData переданного класса
            in_cache -> поиск только в кэше, когда кэширование сделано
            непосредственно перед операциями с БД """
        item = None
        if attr:
            item = db_cls.getDataFromDict(attr=attr)
            if item is None and not in_cache:
                item = db_cls.getDataFromDb(attr=attr)
        return item

    @staticmethod
    def getDataFromDb(db_cls, statement):
        """ Возвращает экземпляр указанного класса из БД.
            Если в БД имеется несколько значений, то возвращается первое.
            Если ничего не найдено, то возвращается None """
        try:
            db_item = DbConnection.executeStatement(statement, one=True)[0]
            db_cls.addData(item=db_item)
        except IndexError:
            db_item = None
        return db_item

    @staticmethod
    def getDataFromDict(db_cls, attr: tuple | str | int) -> DbProduct | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return db_cls.data.get(attr, None)


# pylint: disable=unused-argument
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    """ Настройки SQlite """
    if CFG_DB.main.db_type == 'SQLite':
        cursor = dbapi_connection.cursor()
        cursor.execute(f"PRAGMA synchronous = {CFG_DB.sqlite.pragma_synchronous}")
        cursor.execute(f"PRAGMA journal_mode = {CFG_DB.sqlite.pragma_journal_mode}")
        cursor.close()


class DbProductKind(Base):
    """SqlAlchemy класс описания таблицы product_kind в БД"""

    __tablename__ = 'product_kind'
    id_kind = Column('id_kind', Integer, primary_key=True)
    name = Column('name', String)
    name_short = Column('name_short', String)
    imenitelnyy = Column('imenitelnyy', String)
    roditelnyy = Column('roditelnyy', String)
    datelnyy = Column('datelnyy', String)
    tvoritelnyy = Column('tvoritelnyy', String)
    predlozhnyy = Column('predlozhnyy', String)
    product = relationship("DbProduct", back_populates="kind")
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка видов изделий'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbProductKind) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.name_short] = item
        cls.data[item.id_kind] = item

    @classmethod
    def uniqueData(cls) -> list[DbProductKind]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: str | int) -> DbProductKind | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: str | int) -> DbProductKind | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.name_short == attr,
                                          cls.id_kind == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str | int) -> DbProductKind | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def getDefaultProductKind(cls, db_product: DbProduct) -> DbProductKind:
        """ Возвращает вид изделия, исходя из аттрибутов изделия """
        default_kind = DbProductKind.data['неизвестно']
        deno = str(db_product.deno)
        name = str(db_product.name)
        if db_product.purchased:
            return DbProductKind.data['ПКИ']
        if re.fullmatch(r'\w{4}[.]\d{5}-\d{2}', deno):
            return DbProductKind.data['СПО']
        if deno == name:
            re_str = r'винт|шуруп|штифт|гайка|шайба|шплинт|заклепка|заклёпка|саморез'
            if re.search(rf'{re_str}', deno, re.IGNORECASE):
                return DbProductKind.data['крепеж']
            return DbProductKind.data['ПКИ']
        if db_product.parents:
            for db_hierarchy in db_product.parents:
                if db_hierarchy.product_type.type_name == 'деталь':
                    return DbProductKind.data['деталь']
        if re.fullmatch(r'\w{4}[.]68\d{4}[.].*', deno) is not None \
                and re.search(r'кабель|жгут|провод', name, re.IGNORECASE) is not None:
            return DbProductKind.data['кабель']
        if re.search(r'ЗИП', name, re.IGNORECASE) is not None:
            return DbProductKind.data['ЗИП']
        if re.search(r'КМЧ|комплект монтажных частей', name, re.IGNORECASE) is not None:
            return DbProductKind.data['КМЧ']
        if re.search(r'упаковка|комплект*упаковки', name, re.IGNORECASE) is not None:
            return DbProductKind.data['упаковка']
        if re.search(r'комплект', name, re.IGNORECASE) is not None:
            return DbProductKind.data['комплект']
        if re.search(r'чехол', name, re.IGNORECASE) is not None:
            return DbProductKind.data['чехол']
        if re.search(r'АРМ', name) is not None:
            return DbProductKind.data['АРМ']
        if db_product.documents:
            doc_types = [doc.document_real.id_type for doc in db_product.documents]
            if cls.doc_type_tu_id not in doc_types:
                if cls.doc_type_sb_id in doc_types:
                    if cls.doc_type_e4_id not in doc_types and cls.doc_type_e3_id not in doc_types:
                        # Нет ТУ есть СБ нет Э4, Э3
                        if db_product.children:
                            return DbProductKind.data['мех. сборка']
                        return DbProductKind.data['мех. узел']
                    else:
                        if re.search(r'плата', db_product.name, re.IGNORECASE) is not None:
                            return DbProductKind.data['плата']
                        if db_product.children:
                            return DbProductKind.data['эл. сборка']
                        return DbProductKind.data['эл. узел']
                else:
                    if cls.doc_type_e4_id in doc_types and cls.doc_type_e3_id in doc_types:
                        return DbProductKind.data['комплекс']
            else:
                # Есть ТУ нет СБ
                return DbProductKind.data['комплекс']
        return default_kind

    @classmethod
    def getDefaultIdKinds(cls):
        """ Определяет типовые виды документов для использования
            в методах определения вида изделия """
        cls.doc_type_tu_id = DbDocumentType. \
            getData(class_name='КД',
                    subtype_name='Технические условия').id_type
        cls.doc_type_sb_id = DbDocumentType. \
            getData(class_name='КД',
                    subtype_name='Сборочный чертеж').id_type
        cls.doc_type_e4_id = DbDocumentType. \
            getData(class_name='КД',
                    subtype_name='Схема электрическая соединений').id_type
        cls.doc_type_e3_id = DbDocumentType. \
            getData(class_name='КД',
                    subtype_name='Схема электрическая принципиальная (полная)').id_type


class DbProduct(Base):
    """SqlAlchemy класс описания таблицы product в БД"""

    __tablename__ = 'product'
    id_product = Column('id_product', Integer, primary_key=True)
    name = Column('name', String)
    deno = Column('deno', String)
    id_kind = Column('id_kind', ForeignKey("product_kind.id_kind"))
    purchased = Column('purchased', String)
    date_check = Column('date_check', DateTime)
    name_check = Column('name_check', String)
    kind = relationship("DbProductKind",
                        lazy='joined',
                        foreign_keys=[id_kind],
                        back_populates="product")
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка данных об изделиях'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbProduct) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.deno] = item

    @classmethod
    def uniqueData(cls) -> list[DbProduct]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, deno: str, in_cache: bool = False) -> DbProduct | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr=deno, in_cache=in_cache)

    @classmethod
    def getDataFromDb(cls, attr: str) -> DbProduct | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.deno == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str) -> DbProduct | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return BaseMethods.getDataFromDict(cls, attr)

    @classmethod
    def getProductWithoutPrimaryApplication(cls) -> list[DbProduct]:
        """ Возвращает список изделий без первичной применяемости """
        cls.updCheck()
        DbPrimaryApplication.updCheck()
        SplashScreen().basicProceed('Поиск изделий без первичной применяемости')
        statement = select(cls). \
            outerjoin(DbPrimaryApplication, cls.id_product == DbPrimaryApplication.id_child). \
            outerjoin(DbHierarchy, cls.id_product == DbHierarchy.id_child). \
            outerjoin(DbProductType, DbHierarchy.id_type == DbProductType.id_type). \
            filter(DbPrimaryApplication.id_parent.is_(None)). \
            filter(cls.deno != cls.name).\
            filter(DbProductType.type_name != 'деталь')
        result = DbConnection.executeStatement(statement)
        return [item[0] for item in result]

    @classmethod
    # pylint: disable=too-many-arguments
    def addDbProduct(cls, deno: str,
                     name: str = 'Неизвестно',
                     id_kind: int | None = None,
                     purchased: str = '',
                     date_check: datetime | None = None,
                     name_check: str | None = None,
                     commit_later: bool = False,
                     upd: bool = True,
                     in_cache: bool = False,
                     generated_name: bool = False) -> DbProduct | None:
        """ Проверяет наличие экземпляра класса по предоставленным аттрибутам.
            Создает новый или обновляет существующий экземпляр класса.
            Вносит изменения в БД если не сказано обратное (commit_later) """
        product = None
        if not name:
            name = 'Неизвестно'
        if deno:
            product = cls.getData(deno, in_cache)
            if product:
                if upd or product.name == 'Неизвестно':
                    product.updDbProduct(name=name,
                                         id_kind=id_kind,
                                         purchased=purchased,
                                         date_check=date_check,
                                         name_check=name_check,
                                         generated_name=generated_name)
            else:
                product = cls(name=name,
                              deno=deno,
                              id_kind=id_kind,
                              purchased=purchased,
                              date_check=date_check,
                              name_check=name_check)
                DbConnection.session.add(product)

            if not commit_later:
                try:
                    SplashScreen().newMessage(message=f'Попытка внести {name} {deno} в базу данных',
                                              log=True,
                                              upd_bar=False,
                                              logging_level='INFO')
                    DbConnection.sessionCommit()
                    cls.addData(item=product)
                    DbConnection.session.refresh(product)
                    SplashScreen().close()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось внести {name} {deno}. Повторная попытка\n{err}')
                    DbConnection.session.rollback()
                    cls.addDbProduct(deno=deno,
                                     name=name,
                                     id_kind=id_kind,
                                     date_check=date_check,
                                     name_check=name_check,
                                     commit_later=False,
                                     upd=True)
                except InvalidRequestError as err:
                    DbConnection.reconnection(error=err)
        return product

    @classmethod
    def addDbProducts(cls, products: dict[str, dict[str, str | datetime | bool]],
                      in_cache: bool = False) \
            -> dict[str, dict[str, str | datetime | bool | DbProduct]]:
        """ Проверяет наличие экземпляров класса по предоставленным аттрибутам.
            Создает новые и обновляет существующие экземпляры класса.
            Вносит изменения за один коммит """
        already_added = {}
        all_keys = ['name',
                    'deno',
                    'id_kind',
                    'purchased',
                    'date_check',
                    'name_check',
                    'upd',
                    'generated_name']
        SplashScreen().basicMsg('Подготовка к записи изделий')
        for key in products.keys():
            product = add_missing_keys(dictionary=products[key],
                                       keys=all_keys)
            if key in already_added:
                db_product = already_added[key]
            else:
                db_product = cls.addDbProduct(deno=product['deno'],
                                              name=product['name'],
                                              id_kind=product['id_kind'],
                                              purchased=product['purchased'],
                                              date_check=product['date_check'],
                                              name_check=product['name_check'],
                                              upd=product['upd'],
                                              generated_name=product['generated_name'],
                                              in_cache=in_cache,
                                              commit_later=True)
                already_added[key] = db_product
            product['db_product'] = db_product
        try:
            DbConnection.sessionCommit()
            # DbConnection.session_commit()
            for product in products.values():
                if product is not None:
                    cls.data[product['deno']] = product['db_product']
        except (IntegrityError, OperationalError, NameError) as err:
            show_dialog(f'Не удалось внести изделия. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addDbProducts(products=products)
        return products

    @classmethod
    def updAllProductKinds(cls):
        """ Определяет каждому изделию его вид """
        DbProductKind.getDefaultIdKinds()
        for db_product in cls.data.values():
            db_product.id_kind = DbProductKind.getDefaultProductKind(db_product=db_product).id_kind
        DbConnection.sessionCommit()

    # pylint: disable=too-many-arguments
    def updDbProduct(self,
                     name: str,
                     id_kind: int,
                     purchased: str,
                     date_check: datetime,
                     name_check: str,
                     generated_name: bool = False):
        """ Изменяет данные существующего изделия """
        if date_check is not None:
            try:
                new = date_check >= self.date_check
            except TypeError:
                new = False
        else:
            new = True
        if id_kind is not None:
            self.id_kind = id_kind
        if purchased or self.purchased is None:
            self.purchased = purchased
        if new or self.date_check is None:
            if name and name != 'Неизвестно' and not generated_name:
                self.name = name
            if date_check:
                self.date_check = date_check
            if name_check:
                self.name_check = name_check

    def getDbDocuments(self) -> list[DbDocument]:
        """ Возвращает список документов """
        try:
            return self.documents
        except DetachedInstanceError as err:
            logging.debug(err)
            self.__class__.updData()
            return self.getDbDocuments()


class DbPrimaryApplication(Base):
    """SqlAlchemy класс описания таблицы первичных применяемостей в БД"""

    __tablename__ = 'primary_application'
    id_primary_application = Column('id_primary_application', Integer, primary_key=True)
    id_child = Column('id_child', ForeignKey("product.id_product"), unique=True)
    id_parent = Column('id_parent', ForeignKey("product.id_product"))
    parent = relationship('DbProduct', lazy='joined',
                          foreign_keys=[id_parent], backref='primary_children')
    child = relationship('DbProduct', lazy='joined',
                         foreign_keys=[id_child], backref='primary_parent')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка связей изделий по первичной применяемости'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbPrimaryApplication) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_child] = item

    @classmethod
    def uniqueData(cls) -> list[DbPrimaryApplication]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, product: DbProduct) -> DbPrimaryApplication | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, product.id_product)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbPrimaryApplication | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_child == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbPrimaryApplication | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def addDbPrimaryApplication(cls, parent: DbProduct, child: DbProduct,
                                commit_later: bool = False) -> DbPrimaryApplication:
        """ Проверяет наличие экземпляра класса по предоставленным аттрибутам.
            Создает новый или обновляет существующий экземпляр класса.
            Вносит изменения в БД если не сказано обратное (commit_later) """
        primary_application = None
        if child and parent:
            primary_application = cls.getData(child)
            if primary_application:
                primary_application.updDbPrimaryApplication(parent=parent,
                                                            child=child)
            else:
                primary_application = cls(id_child=child.id_product,
                                          id_parent=parent.id_product)
                DbConnection.session.add(primary_application)
                cls.data[primary_application.id_child] = primary_application
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    DbConnection.session.refresh(primary_application)
                    DbConnection.session.refresh(child)
                    DbConnection.session.refresh(parent)
                    cls.data[primary_application.id_child] = primary_application
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось внести первичную применяемость. '
                                f'Повторная попытка\n{err}')
                    DbConnection.session.rollback()
                    cls.addDbPrimaryApplication(parent=parent,
                                                child=child,
                                                commit_later=commit_later)
                except InvalidRequestError as err:
                    DbConnection.reconnection(error=err)
        return primary_application

    @classmethod
    # pylint: disable=line-too-long
    def addDbPrimaryApplications(cls, products: dict[str, dict[str, DbPrimaryApplication | str | datetime | bool]])\
            -> dict[str, dict[str, DbPrimaryApplication | str | datetime | bool]]:
        """ Проверяет наличие экземпляров класса по предоставленным аттрибутам.
            Создает новые и обновляет существующие экземпляры класса.
            Вносит изменения за один коммит """
        already_added = {}
        all_keys = ['parent', 'child']
        SplashScreen().basicMsg('Подготовка к записи первичных применяемостей')
        for key in products.keys():
            product = add_missing_keys(dictionary=products[key],
                                       keys=all_keys)
            if key in already_added:
                db_primary_application = already_added[key]
            else:
                db_primary_application = cls.addDbPrimaryApplication(parent=product['parent'],
                                                                     child=product['child'],
                                                                     commit_later=True)
                already_added[key] = db_primary_application
            product['db_primary_application'] = db_primary_application
        try:
            DbConnection.sessionCommit()
            for product in products.values():
                if product['db_primary_application'] is not None:
                    cls.addData(product['db_primary_application'])
        except (IntegrityError, OperationalError) as err:
            logging.debug(err)
            DbConnection.session.rollback()
            cls.addDbPrimaryApplications(products=products)
        return products

    def updDbPrimaryApplication(self, parent: DbProduct, child: DbProduct) -> None:
        """ Изменяет данные о первичной применяемости в БД """
        if self.id_parent != parent.id_product:
            statement = update(DbPrimaryApplication)\
                       .where(DbPrimaryApplication.id_child == child.id_product) \
                       .values(id_parent=parent.id_product)
            DbConnection.executeStatement(statement)


class DbHierarchy(Base):
    """SqlAlchemy класс описания таблицы hierarchy в БД"""

    __tablename__ = 'hierarchy'
    pk_hierarchy = Column('pk_hierarchy', Integer, primary_key=True)
    id_child = Column('id_child', ForeignKey("product.id_product"))
    id_parent = Column('id_parent', ForeignKey("product.id_product"))
    id_type = Column('id_type', ForeignKey("product_type.id_type"))
    quantity = Column('quantity', Integer)
    unit = Column('unit', String)
    product_type = relationship("DbProductType", lazy='joined',
                                foreign_keys=[id_type], back_populates="hierarchy")
    parent = relationship('DbProduct', lazy='joined',
                          foreign_keys=[id_parent], backref='children')
    child = relationship('DbProduct', lazy='joined',
                         foreign_keys=[id_child], backref='parents')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка иерархических связей изделий'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbHierarchy) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[(item.id_child, item.id_parent)] = item

    @classmethod
    def uniqueData(cls) -> list[DbHierarchy]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def setChildren(cls,
                    parent: DbProduct,
                    products: list[dict[str, DbProduct, int]],
                    commit_later: bool = False) -> list[DbHierarchy]:
        """ Обновить или удалить старые зависимости
            products = [
                {'product': Изделие №1.1 (DbProduct),
                 'id_type': id типа по СП (int),
                 'quantity': количество по СП (int)},
                {'product': Изделие №1.2 (DbProduct),
                 'id_type': id типа по СП (int),
                 'quantity': количество по СП (int)}
                        ]"""

        if parent:
            old_hierarchies = cls.getByParent(parent)

            new_children, outdated_hierarchies, refresh_hierarchies = \
                cls.updOld(old_hierarchies=old_hierarchies,
                           children=products)
            cls.addNew(parent=parent,
                       children=new_children)
            cls.delOutdated(outdated_hierarchies=outdated_hierarchies)
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    for hierarchy in refresh_hierarchies:
                        DbConnection.session.refresh(hierarchy)
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось внести связи изделий. Повторная попытка\n{err}')
                    DbConnection.session.rollback()
                    cls.setChildren(parent=parent,
                                    products=products,
                                    commit_later=commit_later)
            return refresh_hierarchies

    @classmethod
    def addNew(cls, parent: DbProduct,
               children: list[dict[str, DbProduct, int]]) -> None:
        """ Вносит в БД новую запись parent-child """

        for child in children:
            hierarchy = cls(id_parent=parent.id_product,
                            id_child=child['product'].id_product,
                            id_type=child['id_type'],
                            quantity=child.get('quantity', 0),
                            unit=child.get('unit', 'шт'))
            DbConnection.session.add(hierarchy)

    @classmethod
    def delOutdated(cls, outdated_hierarchies: list[DbHierarchy]) -> None:
        """ Удаляет записи из таблицы иерархий """
        for hierarchy in outdated_hierarchies:
            statement = delete(cls).where(and_(cls.id_parent == hierarchy.id_parent,
                                               cls.id_child == hierarchy.id_child))
            DbConnection.executeStatement(statement)

    @classmethod
    def getByParent(cls, parent: DbProduct) -> list[DbHierarchy]:
        """ Возвращает все записи, где родитель с определенным id """
        statement = select(cls).where(
            cls.id_parent == parent.id_product)
        hierarchies = [hierarchy[0] for hierarchy in DbConnection.executeStatement(statement)]
        for hierarchy in hierarchies:
            DbProduct.data[hierarchy.child.deno] = hierarchy.child
            DbConnection.session.refresh(hierarchy.child)
        return hierarchies

    @classmethod
    # pylint: disable=too-many-locals
    def getHierarchy(cls, product: DbProduct, reverse=False)\
            -> list[dict[str, None | int | DbHierarchy | bool | list[DbDocument]]]:
        """ Возвращает список словарей, содержащий данные об иерархическом составе изделия """

        # Запрос древа изделий
        title = f'Запрос иерархии для {product.name} {product.deno}'
        SplashScreen().basicReceive(title)
        result = DbConnection.executeStatement(cls.hierarchicalQuery(product, reverse))
        SplashScreen().basicProceed(title)

        # Словарь {первичный ключ hierarchy: значение уровня}
        pk_to_level_dict = {}
        ids_parent = []
        ids_child = []
        for level, pk_hierarchy, id_child, id_parent in result:
            pk_to_level_dict.update({pk_hierarchy: level})
            ids_parent.append(id_parent)
            ids_child.append(id_child)

        # ORM иерархии, с изделиями и типом изделия по спецификации
        title = f'Запрос изделий для {product.name} {product.deno}'
        SplashScreen().basicReceive(title)
        db_hierarchies = cls.getDbHierarchies(ids_parent=ids_parent,
                                              ids_child=ids_child,
                                              reverse=reverse)
        SplashScreen().basicProceed(title)

        # Формирование списка документов для изделий из найденной иерархии
        title = f'Запрос документов для дочерних изделий {product.name} {product.deno}'
        SplashScreen().basicReceive(title)
        db_documents_dict = cls.getDbDocuments(ids_child=ids_child)
        SplashScreen().basicProceed(title)

        # Список словарей с уровнем и ORM иерархией для построения древа
        title = f'Запрос документов для {product.name} {product.deno}'
        SplashScreen().basicReceive(title)
        root_documents = cls.getDbDocumentsForRoot(root_product_id=product.id_product)
        SplashScreen().basicProceed(title)

        # Сопоставление изделий иерархии и их документов
        SplashScreen().newMessage(message='Привязка документов к изделиям...',
                                  log=True,
                                  logging_level='DEBUG')

        hierarchy = [{'level': 0,
                      'root': True,
                      'db_hierarchy': None,
                      'db_documents': root_documents
                      }]
        for count, db_hierarchy in enumerate(db_hierarchies):
            product = db_hierarchy.parent if reverse else db_hierarchy.child
            hierarchy.append({'level': pk_to_level_dict[db_hierarchy.pk_hierarchy],
                              'root': False,
                              'db_hierarchy': db_hierarchy,
                              'db_documents': db_documents_dict.get(product.id_product, [])
                              })
            SplashScreen().changeSubProgressBar(stage=count,
                                                stages=len(db_hierarchies))
        SplashScreen().changeSubProgressBar(stage=0, stages=0)
        return hierarchy

    @classmethod
    def getDbHierarchies(cls, ids_parent: list[int], ids_child: list[int],
                         reverse: bool) -> list[DbHierarchy]:
        """ Возвращает список экземпляров OMR класса, соответствующих условиям
            построения иерархического древа вниз или же вверх """
        if reverse:
            statement = select(cls).options(joinedload(cls.child)). \
                                    options(joinedload(cls.product_type)). \
                                    filter(cls.id_child.in_(ids_child))
        else:
            statement = select(cls).options(joinedload(cls.parent)).\
                                    options(joinedload(cls.product_type)).\
                                    filter(cls.id_parent.in_(ids_parent))
        result = DbConnection.executeStatement(statement)
        return [item[0] for item in result]

    @classmethod
    def getDbDocuments(cls, ids_child: list[int]) -> dict[int, list[DbDocument]]:
        """ Возвращает словарь, содержащий списки документов,
            соответствующих определенному изделию """
        statement = select(DbDocument).options(joinedload(DbDocument.product)). \
            options(joinedload(DbDocument.document_real).
                    joinedload(DbDocumentReal.stage)). \
            options(joinedload(DbDocument.document_real).
                    joinedload(DbDocumentReal.document_type)). \
            filter(DbDocument.id_product.in_(ids_child))
        result = DbConnection.executeStatement(statement)
        db_documents_dict = {}
        for item in result:
            db_document = item[0]
            if db_document.product.id_product in db_documents_dict:
                db_documents_dict[db_document.product.id_product].append(db_document)
            else:
                db_documents_dict[db_document.product.id_product] = [db_document]
        return db_documents_dict

    @classmethod
    def getDbDocumentsForRoot(cls, root_product_id):
        """ Возвращает документы относящиеся к изделию - вершине иерархии"""
        statement = select(DbDocument).options(joinedload(DbDocument.product)). \
            options(joinedload(DbDocument.document_real).
                    joinedload(DbDocumentReal.stage)). \
            options(joinedload(DbDocument.document_real).
                    joinedload(DbDocumentReal.document_type)). \
            filter(DbDocument.id_product == root_product_id)
        result = DbConnection.executeStatement(statement)
        return [item[0] for item in result]

    @classmethod
    def hierarchicalQuery(cls, product: DbProduct, reverse) -> Query:
        """ Возвращает запрос к БД на получение """
        record = ''
        if not reverse:
            record = select(literal(0).label('level'),
                            literal(0).label("pk_hierarchy"),
                            literal(product.id_product).label("id_product"),
                            literal(0).label("id_parent")
                            ).cte(recursive=True)
            ralias = aliased(record, name="R")
            lalias = aliased(cls, name="L")
            record = record.union_all(
                DbConnection.session.query(ralias.c.level + 1,
                                           lalias.pk_hierarchy,
                                           lalias.id_child,
                                           lalias.id_parent)
                .join(ralias, ralias.c.id_product == lalias.id_parent)
                .filter(ralias.c.level < 20))
        if reverse:
            record = select(literal(0).label('level'),
                            literal(0).label("pk_hierarchy"),
                            literal(product.id_product).label("id_product"),
                            literal(0).label("id_parent"),
                            ).cte(recursive=True)
            ralias = aliased(record, name="R")
            lalias = aliased(cls, name="L")
            record = record.union_all(
                DbConnection.session.query(ralias.c.level + 1,
                                           lalias.pk_hierarchy,
                                           lalias.id_parent,
                                           lalias.id_child)
                .join(ralias, ralias.c.id_product == lalias.id_child)
                .suffix_with('ORDER BY 1 DESC')
                .filter(ralias.c.level < 20))
        return DbConnection.session.query(record)

    @classmethod
    def addDbHierarchies(cls,
                         hierarchies: dict[DbProduct,
                                           dict[str, list[dict[str, DbProduct, int]]]],
                         parent: DbProduct | None = None) -> None:
        """ Изменяет данные об иерархических связях в БД
            hierarchies = {
                Изделие №1 (DbProduct): {
                    'parent': Изделие №1 (DbProduct),
                    'products': [{'product': Изделие №1.1 (DbProduct),
                                  'id_type': id типа по СП (int),
                                  'quantity': количество по СП (int)},
                                 {'product': Изделие №1.2 (DbProduct),
                                  'id_type': id типа по СП (int),
                                  'quantity': количество по СП (int)},]
                                        },
                Изделие №2 (DbProduct): {
                    'parent': Изделие №2 (DbProduct),
                    'products': [{'product': Изделие №2.1 (DbProduct),
                                  'id_type': id типа по СП (int),
                                  'quantity': количество по СП (int)},
                                 {'product': Изделие №2.2 (DbProduct),
                                  'id_type': id типа по СП (int),
                                  'quantity': количество по СП (int)},]
                                        },
                           }
        """

        all_keys = ['parent', 'products']
        refresh_hierarchies = []
        if hierarchies:
            for key in hierarchies.keys():
                hierarchy = add_missing_keys(dictionary=hierarchies[key],
                                             keys=all_keys)
                refresh_hierarchies = cls.setChildren(parent=hierarchy['parent'],
                                                      products=hierarchy['products'],
                                                      commit_later=True)
        else:
            refresh_hierarchies = cls.setChildren(parent=parent,
                                                  products=[],
                                                  commit_later=True)
        try:
            SplashScreen().newMessage(message='Попытка внести связи изделий в базу данных',
                                      log=True,
                                      upd_bar=False,
                                      logging_level='INFO')
            DbConnection.sessionCommit()
            for hierarchy in refresh_hierarchies:
                DbConnection.session.refresh(hierarchy)

        except (IntegrityError, OperationalError) as err:
            logging.debug(err)
            SplashScreen().newMessage(message='Не удалось внести связи изделий. Повторная попытка',
                                      log=True,
                                      upd_bar=False,
                                      logging_level='INFO')
            DbConnection.session.rollback()
            DbHierarchy.addDbHierarchies(hierarchies)
        except InvalidRequestError as err:
            DbConnection.reconnection(error=err)

    @staticmethod
    def updOld(old_hierarchies: list[DbHierarchy],
               children: list[dict[str, DbProduct, int]]) -> \
            tuple[list[dict[str, DbProduct, int]], list[DbHierarchy], list[DbHierarchy]]:
        """ Сравнивает имеющиеся иерархические данные для родителя
            со списком новых входящих в его состав изделий и
            определяет какие изделия больше не входят в состав изделия.
            Возвращает:
            1. Список изделий которые нужно внести;
            2. Список зависимостей для удаления;
            3. Список зависимостей для изменения """
        refresh_hierarchies = []
        new_children = children.copy()
        outdated_hierarchies = old_hierarchies.copy()
        for hierarchy in old_hierarchies:
            for child in children:
                if hierarchy.id_child == child['product'].id_product:
                    hierarchy.id_type = child['id_type']
                    hierarchy.quantity = child.get('quantity', 0)
                    hierarchy.unit = child.get('unit', 'шт')
                    new_children.remove(child)
                    outdated_hierarchies.remove(hierarchy)
                    refresh_hierarchies.append(hierarchy)
        return new_children, outdated_hierarchies, refresh_hierarchies


class DbProductType(Base):
    """SqlAlchemy класс описания таблицы product_type в БД"""

    __tablename__ = 'product_type'
    id_type = Column('id_type', Integer, primary_key=True)
    type_name = Column('type_name', String)
    hierarchy = relationship("DbHierarchy", back_populates="product_type")
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка типов изделий'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def uniqueData(cls) -> list[DbProductType]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def addData(cls, item: DbProductType) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.type_name] = item
        cls.data[item.id_type] = item

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, product_type: str) -> DbProductType | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = str(product_type).lower()
        return BaseMethods.getData(cls, attr=attr)

    @classmethod
    def getDataFromDb(cls, attr: str) -> DbProductType | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.type_name == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str) -> DbProductType | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return BaseMethods.getDataFromDict(cls, attr)


class DbDocument(Base):
    """SqlAlchemy класс описания таблицы document в БД"""

    __tablename__ = 'document'
    id_document = Column('id_document', Integer, primary_key=True)
    id_product = Column('id_product', ForeignKey("product.id_product"))
    id_document_real = Column('id_document_real', ForeignKey("document_real.id_document_real"))

    product = relationship('DbProduct', lazy='joined',
                           foreign_keys=[id_product], backref='documents')

    document_real = relationship('DbDocumentReal', lazy='joined',
                                 foreign_keys=[id_document_real], backref='documents')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка связей документов с изделиями'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocument) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[(item.id_document_real,
                  item.id_product)] = item

    @classmethod
    def uniqueData(cls) -> list[DbDocument]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, document_real: DbDocumentReal,
                product: DbProduct,
                in_cache: bool = False) -> DbDocument | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (document_real.id_document_real,
                product.id_product)
        return BaseMethods.getData(cls, attr=attr, in_cache=in_cache)

    @classmethod
    def getDataFromDb(cls, attr: tuple[int]) -> DbDocument | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(and_(cls.id_document_real == attr[0],
                                           cls.id_product == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple[int]) -> DbDocument | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def getDbDocumentsByProductIds(cls, product_ids: list[int]) -> list[DbDocument]:
        """ Возвращает список документов для списка изделий """
        statement = select(cls).options(joinedload(cls.product))\
                               .options(joinedload(cls.document_type))\
                               .filter(cls.id_product.in_(product_ids))
        documents = DbConnection.executeStatement(statement)
        documents = [document[0] for document in documents]
        return documents

    @classmethod
    def getErrorTTP(cls) -> dict[DbProduct: list[DbDocument]]:
        """ Возвращает словарь {изделие: список документов} для тех
            изделий где одному изделию соответствуют больше одного
            типового технологического процесса"""
        SplashScreen().newMessage(message='Загрузка данных о некорректно присвоенных КТТП',
                                  stage=0,
                                  stages=0,
                                  log=True,
                                  logging_level='INFO')
        SplashScreen().changeSubProgressBar(0, 0)
        sub_statement = select(DbDocumentReal.id_document_real)\
            .join(DbDocumentType)\
            .filter(DbDocumentType.sign == 'КТТП')
        statement = select(DbDocument).options(joinedload(DbDocument.product))\
                                      .filter(DbDocument.id_document_real.in_(sub_statement))
        documents = DbConnection.executeStatement(statement)
        documents = list(map(lambda x: x[0], documents))
        product_dict = {}
        for document in documents:
            document_list = product_dict.get(document.product, [])
            document_list.append(document)
            product_dict[document.product] = document_list
        SplashScreen().close()
        result = {}
        for product, document_list in product_dict.items():
            if len(document_list) > 1:
                result[product] = document_list
        return result

    @classmethod
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    def addDbDocument(cls, product: DbProduct,
                      document_deno: str | None = None,
                      document_type: DocumentType | None = None,
                      document_name: str | None = None,
                      document_stage: str = 'Неизвестно',
                      file_name: str = None,
                      link: str = None,
                      date_created: datetime | None = None,
                      name_created: str | None = None,
                      date_changed: datetime | None = None,
                      name_changed: str | None = None,
                      document_real: DbDocumentReal | None = None,
                      in_cache: bool = False,
                      commit_later: bool = False) -> DbDocument:
        """ Проверяет наличие экземпляра класса по предоставленным аттрибутам.
            Создает новый или обновляет существующий экземпляр класса.
            Вносит изменения в БД если не сказано обратное (commit_later) """
        if not document_real:
            document_real = DbDocumentReal.addDbDocument(document_type=document_type,
                                                         document_deno=document_deno,
                                                         document_name=document_name,
                                                         document_stage=document_stage,
                                                         file_name=file_name,
                                                         link=link,
                                                         date_created=date_created,
                                                         name_created=name_created,
                                                         date_changed=date_changed,
                                                         name_changed=name_changed,
                                                         commit_later=commit_later)
        document = cls.getData(document_real=document_real,
                               product=product,
                               in_cache=in_cache)
        if not document:
            document = cls(id_product=product.id_product,
                           id_document_real=document_real.id_document_real)
            DbConnection.session.add(document)

        if not commit_later:
            try:
                DbConnection.sessionCommit()
                DbConnection.session.refresh(document)
                DbConnection.session.refresh(document.document_real)
                DbDocumentReal.data[(document_real.deno, document_real.id_type)] = document_real
                cls.data[(document.id_document_real, document.id_product)] = document
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести {product.name} {document_deno}.'
                            f'Повторная попытка\n{err}')
                DbConnection.session.rollback()
                cls.addDbDocument(product=product,
                                  document_deno=document_deno,
                                  document_type=document_type,
                                  document_name=document_name,
                                  document_stage=document_stage,
                                  file_name=file_name,
                                  link=link,
                                  date_created=date_created,
                                  name_created=name_created,
                                  date_changed=date_changed,
                                  name_changed=name_changed,
                                  document_real=document_real,
                                  commit_later=commit_later)
            except InvalidRequestError as err:
                DbConnection.reconnection(error=err)
        return document

    @classmethod
    def delDbDocument(cls, product: DbProduct,
                      document_real: DbDocumentReal,
                      commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        document = cls.getData(document_real=document_real,
                               product=product)
        del cls.data[document.id_document_real, document.id_product]
        DbConnection.session.delete(document)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                DbConnection.session.refresh(document.document_real)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить {product.name} {document_real.deno}. '
                            f'Повторная попытка\n{err}')
                DbConnection.session.rollback()
                cls.delDbDocument(product=product, document_real=document_real)

    @classmethod
    # pylint: disable=line-too-long
    def addDbDocuments(cls, documents: dict[str, dict[str, str | bool | datetime | DbProduct | DbDocumentReal]],
                       in_cache: bool = False) \
            -> dict[str, dict[str, str | bool | datetime | DbProduct | DbDocumentReal | DbDocument]]:
        """ Проверяет наличие экземпляров класса по предоставленным аттрибутам.
            Создает новые и обновляет существующие экземпляры класса.
            Вносит изменения за один коммит """
        already_added = {}
        all_keys = ['product',
                    'document_type',
                    'document_deno',
                    'document_name',
                    'document_stage',
                    'file_name',
                    'link',
                    'date_created',
                    'name_created',
                    'date_changed',
                    'name_changed',
                    'document_real',
                    'delete']
        SplashScreen().basicMsg('Подготовка к записи связей изделий и документов')
        for key in documents.keys():
            document = add_missing_keys(dictionary=documents[key],
                                        keys=all_keys)
            if key in already_added:
                db_document = already_added[key]
            else:
                if not bool(document['delete']):
                    db_document = cls.addDbDocument(product=document['product'],
                                                    document_type=document['document_type'],
                                                    document_deno=document['document_deno'],
                                                    document_name=document['document_name'],
                                                    document_stage=document['document_stage'],
                                                    file_name=document['file_name'],
                                                    link=document['link'],
                                                    date_created=document['date_created'],
                                                    name_created=document['name_created'],
                                                    date_changed=document['date_changed'],
                                                    name_changed=document['name_changed'],
                                                    document_real=document['document_real'],
                                                    in_cache=in_cache,
                                                    commit_later=True)
                else:
                    cls.delDbDocument(product=document['product'],
                                      document_real=document['document_real'],
                                      commit_later=True)
                    db_document = None
                already_added[key] = db_document
            document['db_document'] = db_document
        try:
            DbConnection.sessionCommit()
            SplashScreen().newMessage(message='Обновление документов...',
                                      upd_bar=False)
            for num, document in enumerate(documents.values()):
                SplashScreen().changeSubProgressBar(stage=num,
                                                    stages=len(documents))
                db_document = document['db_document']
                if db_document is not None:
                    DbConnection.session.refresh(db_document)
                    DbConnection.session.refresh(db_document.document_real)
                    DbDocumentReal.data[
                        (db_document.document_real.deno,
                         db_document.document_real.id_type)] = db_document.document_real
                    cls.data[(db_document.id_document_real, db_document.id_product)] = db_document
            SplashScreen().close()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести документы. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addDbDocuments(documents=documents)
        except InvalidRequestError as err:
            DbConnection.reconnection(error=err)
        return documents


class DbDocumentType(Base):

    """ SqlAlchemy класс для хранения информации о типах документов """

    __tablename__ = 'document_type'

    id_type = Column('id_type', Integer, primary_key=True)
    class_name = Column('class_name', String)
    subclass_name = Column('subclass_name', String)
    type_name = Column('type_name', String)
    subtype_name = Column('subtype_name', String)
    sign = Column('sign', String)
    description = Column('description', String)
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка типов документов'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocumentType) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_type] = item
        cls.data[(item.class_name,
                  item.sign)] = item
        cls.data[(item.class_name,
                  item.subtype_name)] = item

    @classmethod
    def uniqueData(cls) -> list[DbDocumentType]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls):
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, class_name: str, subtype_name: str) -> DbDocumentType | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (class_name, subtype_name)
        return BaseMethods.getData(cls, attr=attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple[str]) -> DbDocumentType | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(and_(cls.class_name == attr[0],
                                           cls.subtype_name == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple[str]) -> DbDocumentType | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    # pylint: disable=too-many-arguments
    def updDocumentType(cls, id_type: int,
                        class_name: str,
                        subclass_name: str,
                        type_name: str,
                        subtype_name: str,
                        sign: str,
                        description: str,
                        commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_type not in cls.data:
            cls.addNewDocumentType(class_name=class_name,
                                   subclass_name=subclass_name,
                                   type_name=type_name,
                                   subtype_name=subtype_name,
                                   sign=sign,
                                   description=description)
        else:
            db_type = cls.data[id_type]
            db_type.class_name = class_name
            db_type.subclass_name = subclass_name
            db_type.type_name = type_name
            db_type.subtype_name = subtype_name
            db_type.sign = sign
            db_type.description = description
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить вид документа\n{err}\nПовторная попытка')
                    DbConnection.session.rollback()
                    cls.updDocumentType(id_type=id_type,
                                        class_name=class_name,
                                        subclass_name=subclass_name,
                                        type_name=type_name,
                                        subtype_name=subtype_name,
                                        sign=sign,
                                        description=description)

    @classmethod
    # pylint: disable=too-many-arguments
    def addNewDocumentType(cls, class_name: str,
                           subclass_name: str,
                           type_name: str,
                           subtype_name: str,
                           sign: str,
                           description: str,
                           commit_later: bool = False):
        """ Внесение нового типа документа """
        db_type = DbDocumentType(class_name=class_name,
                                 subclass_name=subclass_name,
                                 type_name=type_name,
                                 subtype_name=subtype_name,
                                 sign=sign,
                                 description=description)
        DbConnection.session.add(db_type)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
                # cls.addData(item=db_iot)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести вид документа\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewDocumentType(class_name=class_name,
                                       subclass_name=subclass_name,
                                       type_name=type_name,
                                       subtype_name=subtype_name,
                                       sign=sign,
                                       description=description)
        return db_type


class DbDocumentReal(Base):
    """SqlAlchemy класс описания таблицы document_real в БД"""
    # pylint: disable=too-many-instance-attributes
    __tablename__ = 'document_real'
    id_document_real = Column('id_document_real', Integer, primary_key=True)
    id_document_stage = Column('id_document_stage', ForeignKey("document_stage.id_document_stage"))
    id_type = Column('id_type', ForeignKey("document_type.id_type"))
    name = Column('name', String)
    deno = Column('deno', String)
    file_name = Column('file_name', String)
    link = Column('link', String)
    date_created = Column('date_created', DateTime)
    name_created = Column('name_created', String)
    date_changed = Column('date_changed', DateTime)
    name_changed = Column('name_changed', String)

    stage = relationship('DbDocumentStage', lazy='joined',
                         foreign_keys=[id_document_stage], backref='document_real')
    document_type = relationship('DbDocumentType', lazy='joined',
                                 foreign_keys=[id_type], backref='documents')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка документов'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocumentType) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[(item.deno,
                  item.id_type)] = item

    @classmethod
    def uniqueData(cls) -> list[DbDocumentReal]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, document_deno: str, document_type: DocumentType,
                in_cache: bool = False) -> DbDocumentReal | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (document_deno, document_type.id_type)
        return BaseMethods.getData(cls, attr, in_cache=in_cache)

    @classmethod
    def getDataFromDb(cls, attr: tuple[str, int]) -> DbDocumentReal | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(and_(cls.deno == attr[0],
                                           cls.id_type == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple[str, int]) -> DbDocumentReal | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def getDbDocumentRealByCode(cls, code: str) -> list[DbDocumentReal]:
        """ Возвращает документы с децимальным номером
            содержащим определенную строку """
        statement = select(cls).where(cls.deno.like(f'%{code}%'))
        _data = DbConnection.executeStatement(statement)
        return _data

    @classmethod
    def getAllDocumentsRealByType(cls, id_type: int) -> list[DbDocumentReal]:
        """ Возвращает список документов запрошенного типа """
        statement = select(cls).where(cls.id_type == id_type)
        data = DbConnection.executeStatement(statement)
        result = []
        for item in data:
            result.append(item[0])
        return result

    @classmethod
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    def addDbDocument(cls,
                      document_type: DocumentType,
                      document_deno: str,
                      document_name: str | None = None,
                      document_stage: str = 'Неизвестно',
                      file_name: str | None = None,
                      link: str | None = None,
                      date_created: datetime | None = None,
                      name_created: str | None = None,
                      date_changed: datetime | None = None,
                      name_changed: str | None = None,
                      in_cache: bool = False,
                      commit_later: bool = False) -> DbDocumentReal:
        """ Проверяет наличие экземпляра класса по предоставленным аттрибутам.
            Создает новый или обновляет существующий экземпляр класса.
            Вносит изменения в БД если не сказано обратное (commit_later) """

        document = None
        if document_deno and document_type.document_type:
            document = cls.getData(document_deno=document_deno,
                                   document_type=document_type,
                                   in_cache=in_cache)
            db_document_stage = DbDocumentStage.addDbDocumentStage(document_stage)
            date_created = null_cleaner(date_created)
            date_changed = null_cleaner(date_changed)

            if document:
                document.updDocumentReal(db_document_stage=db_document_stage,
                                         document_name=document_name,
                                         file_name=file_name,
                                         link=link,
                                         date_created=date_created,
                                         name_created=name_created,
                                         date_changed=date_changed,
                                         name_changed=name_changed)
            else:
                document = cls(deno=document_deno,
                               id_document_stage=db_document_stage.id_document_stage,
                               id_type=document_type.id_type,
                               name=document_name,
                               file_name=file_name,
                               link=link,
                               date_created=date_created,
                               name_created=name_created,
                               date_changed=date_changed,
                               name_changed=name_changed)
                DbConnection.session.add(document)
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    DbConnection.session.refresh(document)
                    DbDocumentReal.data[(document.deno, document.id_type)] = document
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось внести {document_name} {document_deno}. '
                                f'Повторная попытка\n{err}')
                    DbConnection.session.rollback()
                    DbDocumentReal.addDbDocument(document_type=document_type,
                                                 document_deno=document_deno,
                                                 document_name=document_name,
                                                 document_stage=document_stage,
                                                 file_name=file_name,
                                                 link=link,
                                                 date_created=date_created,
                                                 name_created=name_created,
                                                 date_changed=date_changed,
                                                 name_changed=name_changed,
                                                 commit_later=commit_later)
        return document

    @classmethod
    def addDbDocuments(cls, documents: dict[str, dict[str, str | datetime | DocumentType]],
                       in_cache: bool = False)\
            -> dict[str, dict[str, str | datetime | DocumentType | DbDocumentReal]]:
        """ Проверяет наличие экземпляров класса по предоставленным аттрибутам.
            Создает новые и обновляет существующие экземпляры класса.
            Вносит изменения за один коммит """
        already_added = {}
        all_keys = ['document_type',
                    'document_deno',
                    'document_name',
                    'document_stage',
                    'file_name',
                    'link',
                    'date_created',
                    'name_created',
                    'date_changed',
                    'name_changed']
        SplashScreen().basicMsg('Подготовка к записи реквизитов документов')
        for key in documents.keys():
            document = add_missing_keys(dictionary=documents[key],
                                        keys=all_keys)
            if key in already_added:
                db_document = already_added[key]
            else:
                db_document = cls.addDbDocument(document_type=document['document_type'],
                                                document_deno=document['document_deno'],
                                                document_name=document['document_name'],
                                                document_stage=document['document_stage'],
                                                file_name=document['file_name'],
                                                link=document['link'],
                                                date_created=document['date_created'],
                                                name_created=document['name_created'],
                                                date_changed=document['date_changed'],
                                                name_changed=document['name_changed'],
                                                in_cache=in_cache,
                                                commit_later=True)
                already_added[key] = db_document
            document['document_real'] = db_document
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести документы. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addDbDocuments(documents)
        except InvalidRequestError as err:
            DbConnection.reconnection(error=err)
        return documents

    # pylint: disable=too-many-arguments
    def updDocumentReal(self, db_document_stage: DbDocumentStage,
                        document_name: str | None = None,
                        file_name: str | None = None,
                        link: str | None = None,
                        date_created: datetime | None = None,
                        name_created: str | None = None,
                        date_changed: datetime | None = None,
                        name_changed: str | None = None) -> None:
        """ Изменение реквизитов документа """
        if document_name and document_name != self.name:
            self.name = document_name
        try:
            if db_document_stage and db_document_stage != self.stage.id_document_stage:
                self.id_document_stage = db_document_stage.id_document_stage
                self.stage = db_document_stage
        except AttributeError:
            msg = f'Этап разработки документа {self.deno} не изменен'
            logging.warning(msg)
        if file_name and file_name != self.file_name:
            self.file_name = file_name
        if link and link != self.link:
            self.link = link
        if date_created and date_created != self.date_created:
            self.date_created = date_created
        if name_created and name_created != self.name_created:
            self.name_created = name_created
        if date_changed and date_changed != self.date_changed:
            self.date_changed = date_changed
        if name_changed and name_changed != self.name_changed:
            self.name_changed = name_changed


class DbDocumentStage(Base):
    """SqlAlchemy класс описания таблицы document_real в БД"""

    __tablename__ = 'document_stage'
    id_document_stage = Column('id_document_stage', Integer, primary_key=True)
    stage = Column('stage', String)
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка этапов разработки документа'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocumentStage) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.stage] = item
        cls.data[item.id_document_stage] = item

    @classmethod
    def uniqueData(cls) -> list[DbDocumentStage]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getDocumentStage(cls, stage_name: str = 'Неизвестно') -> DbDocumentStage | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr=stage_name)

    @classmethod
    def getDataFromDb(cls, attr: str) -> DbDocumentStage | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.stage == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str) -> DbDocumentStage | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def addDbDocumentStage(cls, stage_name='Неизвестно', commit_later=False) -> DbDocumentStage:
        """ Проверяет наличие экземпляра класса по предоставленным аттрибутам.
            Создает новый или обновляет существующий экземпляр класса.
            Вносит изменения в БД если не сказано обратное (commit_later) """
        if not stage_name:
            stage_name = 'Неизвестно'
        db_document_stage = cls.getDocumentStage(stage_name)
        if not db_document_stage:
            db_document_stage = cls(stage=stage_name)
            DbConnection.session.add(db_document_stage)
            cls.data[db_document_stage.stage] = db_document_stage
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось внести этап {stage_name}. Повторная попытка\n{err}')
                    DbConnection.session.rollback()
                    cls.addDbDocumentStage(stage_name=stage_name,
                                           commit_later=False)
                except InvalidRequestError as err:
                    DbConnection.reconnection(err)
        return db_document_stage


class DbDocumentSignature(Base):
    """SqlAlchemy класс описания таблицы document_minor_data в БД"""

    __tablename__ = 'document_signature'
    id_document_signature = Column('id_document_signature', Integer, primary_key=True)
    id_document_real = Column('id_document_real', ForeignKey("document_real.id_document_real"))
    signature_position = Column('signature_position', String)
    signature_surname = Column('signature_surname', String)
    signature_signdate = Column('signature_signdate', DateTime)
    document = relationship('DbDocumentReal', foreign_keys=[id_document_real], backref='signatures')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка подписей документов...'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocumentSignature) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        key = (item.id_document_real,
               item.signature_position)
        cls.data[key] = item

    @classmethod
    def uniqueData(cls) -> list[DbDocumentSignature]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_document_real: int, signature_position: str) -> DbDocumentSignature | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (id_document_real, signature_position)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple[int, str]) -> DbDocumentSignature | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.id_document_real == attr[0],
                                          cls.signature_position == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple[int, str]) -> DbDocumentSignature | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    # pylint: disable=too-many-arguments
    def updDocumentSignature(cls, id_document_real: int,
                             signature_position: str,
                             signature_surname: str,
                             signature_signdate: datetime | None = None,
                             commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        key = (id_document_real, signature_position)
        if key not in cls.uniqueData():
            cls.addNewDocumentSignature(id_document_real=id_document_real,
                                        signature_position=signature_position,
                                        signature_surname=signature_surname,
                                        signature_signdate=signature_signdate)
        else:
            changed = False
            db_signature_position = cls.data[key]
            if db_signature_position.signature_surname != signature_surname:
                db_signature_position.signature_surname = signature_surname
                changed = True
            if signature_signdate:
                if db_signature_position.signature_signdate != signature_signdate:
                    db_signature_position.signature_signdate = signature_signdate
                    changed = True
            if not commit_later and changed:
                try:
                    DbConnection.sessionCommit()
                    DbConnection.session.refresh(db_signature_position)
                    cls.addData(item=db_signature_position)
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить данные {err}. Повторная попытка')
                    DbConnection.session.rollback()
                    cls.updDocumentSignature(id_document_real=id_document_real,
                                             signature_position=signature_position,
                                             signature_surname=signature_surname,
                                             signature_signdate=signature_signdate)

    @classmethod
    # pylint: disable=too-many-arguments
    def addNewDocumentSignature(cls, id_document_real: int,
                                signature_position: str,
                                signature_surname: str,
                                signature_signdate: datetime | None = None,
                                commit_later: bool = False) -> DbDocumentSignature:
        """ Внесение новых данных в БД """
        db_document_signature = DbDocumentSignature(id_document_real=id_document_real,
                                                    signature_position=signature_position,
                                                    signature_surname=signature_surname,
                                                    signature_signdate=signature_signdate)
        DbConnection.session.add(db_document_signature)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.addData(db_document_signature)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewDocumentSignature(id_document_real=id_document_real,
                                            signature_position=signature_position,
                                            signature_surname=signature_surname,
                                            signature_signdate=signature_signdate)
            except InvalidRequestError as err:
                DbConnection.reconnection(error=err)
        return db_document_signature


class DbDocumentTdComplex(Base):
    """SqlAlchemy класс описания таблицы document_td_complex в БД"""

    __tablename__ = 'document_td_complex'
    pk_document_td_complex = Column('pk_document_td_complex', Integer, primary_key=True)
    id_document_real = Column('id_document_real', ForeignKey("document_real.id_document_real"))
    id_product = Column('id_product', ForeignKey("product.id_product"))
    product = relationship('DbProduct',
                           foreign_keys=[id_product],
                           backref='products_in_complex_documents')
    document = relationship('DbDocumentReal',
                            foreign_keys=[id_document_real],
                            backref='products_in_complex_documents')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка составных документов'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocumentTdComplex) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        if item.id_document_real in cls.data:
            cls.data[item.id_document_real][item.id_product] = item
        else:
            cls.data[item.id_document_real] = {item.id_product: item}

    @classmethod
    def uniqueData(cls) -> list[DbDocumentTdComplex]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, document_real: DbDocumentReal,
                product: DbProduct) -> DbDocumentTdComplex | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (document_real.id_document_real,
                product.id_product)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple[int]) -> DbDocumentTdComplex | None:
        """ Возвращает экземпляр ORM класса по совпадению полей в БД """
        statement = select(cls).where(and_(cls.id_document_real == attr[0],
                                           cls.id_product == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple[int]) -> DbDocumentTdComplex | None:
        """ Возвращает экземпляр ORM класса из кэша """
        id_document_real = attr[0]
        id_product = attr[1]
        return cls.data.get(id_document_real, {}).get(id_product, None)

    @classmethod
    def clearDocumentTdComplex(cls):
        """ Полная очистка данных об изделиях в составных документах.
            Применяется при импорте данных из таблицы регистрации
            децимальных номеров Excel """
        statement = delete(cls)
        DbConnection.executeStatement(statement)
        try:
            DbConnection.sessionCommit()
            cls.data = {}
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось очистить записи о составных документах. '
                        f'Повторная попытка\n{err}')
            cls.clearDocumentTdComplex()

    @ classmethod
    def addDbDocumentTdComplex(cls, document_real: DbDocumentReal,
                               product: DbProduct,
                               commit_later: bool = False) -> DbDocumentTdComplex:
        """ Проверяет наличие экземпляра класса по предоставленным аттрибутам.
            Создает новый или обновляет существующий экземпляр класса.
            Вносит изменения в БД если не сказано обратное (commit_later) """
        record = cls.getData(document_real=document_real, product=product)
        if record is None:
            statement = select(cls).\
                where(and_(cls.id_document_real == document_real.id_document_real,
                           cls.id_product == product.id_product))
            try:
                record = DbConnection.executeStatement(statement, one=True)[0]
            except IndexError:
                record = cls(id_product=product.id_product,
                             id_document_real=document_real.id_document_real)
                DbConnection.session.add(record)
                if record.id_document_real in cls.data:
                    cls.data[record.id_document_real][record.id_product] = record
                else:
                    cls.data[record.id_document_real] = {record.id_product: record}
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось внести составные части документа. '
                                    f'Повторная попытка\n{err}')
                        DbConnection.session.rollback()
                        cls.addDbDocumentTdComplex(document_real=document_real,
                                                   product=product,
                                                   commit_later=commit_later)
        return record

    @classmethod
    def addDbDocumentsTdComplex(cls, documents: dict[str,
                                                     dict[str,
                                                          DbDocumentReal | list[DbProduct]]]):
        """ Проверяет наличие экземпляров класса по предоставленным аттрибутам.
            Создает новые и обновляет существующие экземпляры класса.
            Вносит изменения за один коммит """
        all_keys = ['document_real',
                    'sub_products',
                    'db_document_complex']
        SplashScreen().basicMsg('Подготовка к записи связей изделий в составных документах')
        for key in documents.keys():
            document = add_missing_keys(dictionary=documents[key],
                                        keys=all_keys)

            # if key not in already_added:
            document['db_document_complex'] = []
            for sub_product in document['sub_products']:
                db_document = cls.addDbDocumentTdComplex(document_real=document['document_real'],
                                                         product=sub_product,
                                                         commit_later=True)
                document['db_document_complex'].append(db_document)
        try:
            DbConnection.sessionCommit()
            for document in documents.values():
                for db_document in document['db_document_complex']:
                    if db_document.id_document_real in cls.data:
                        cls.data[db_document.id_document_real][db_document.id_product] = db_document
                    else:
                        cls.data[db_document.id_document_real] = \
                            {db_document.id_product: db_document}
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести запись о составном документе. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addDbDocumentsTdComplex(documents)

    @classmethod
    def updDbDocumentsTdComplex(cls, document: dict[str, DbDocumentReal | list[DbProduct]]):
        """ Обновление списка изделий для составных документов """
        cls.delDbDocumentsTdComplex(document)
        cls.addDbDocumentsTdComplex({'dict': document})

    @classmethod
    def delDbDocumentsTdComplex(cls, document: dict[str, DbDocumentReal | list[DbProduct]]):
        """ Удаление данных из БД """
        db_document = document['document_real']
        statement = delete(cls).where(cls.id_document_real == db_document.id_document_real)
        DbConnection.executeStatement(statement)
        try:
            DbConnection.sessionCommit()
            if cls.data.get(db_document.id_document_real, None) is not None:
                del cls.data[db_document.id_document_real]
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось удалить запись. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.delDbDocumentsTdComplex(document)


class DbExcelProject(Base):
    """SqlAlchemy класс описания таблицы excel_project в БД"""

    __tablename__ = 'excel_project'
    id_project = Column('id_project', Integer, primary_key=True)
    project_name = Column('project_name', String)
    id_product = Column('id_product', ForeignKey("product.id_product"))

    product = relationship('DbProduct', lazy='joined', foreign_keys=[id_product], backref='project')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка проектов'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbProductKind) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.project_name] = item

    @classmethod
    def uniqueData(cls) -> list[DbExcelProject]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, project_name: str) -> DbExcelProject | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, project_name)

    @classmethod
    def getDataFromDict(cls, attr: str) -> DbExcelProject | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def getDataFromDb(cls, attr: str) -> DbExcelProject | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.project_name == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def updDbProject(cls, project: DbExcelProject, product: DbProduct) -> None:
        """ Изменение привязки изделия и проекта """
        if project.product != product:
            project.id_product = product.id_product

    @classmethod
    def addDbProject(cls, project_name: str,
                     product: DbProduct,
                     commit_later: bool = False) -> DbExcelProject:
        """ Проверяет наличие экземпляра класса по предоставленным аттрибутам.
            Создает новый или обновляет существующий экземпляр класса.
            Вносит изменения в БД если не сказано обратное (commit_later) """
        db_project = cls.getData(project_name=project_name)
        if not db_project:
            db_project = cls(project_name=project_name, id_product=product.id_product)
            DbConnection.session.add(db_project)
        else:
            cls.updDbProject(project=db_project, product=product)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                DbConnection.session.refresh(db_project)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести проект: {project_name}. Повторная попытка\n{err}')
                DbConnection.session.rollback()
                cls.addDbProject(project_name=project_name,
                                 product=product,
                                 commit_later=commit_later)
        return db_project

    @classmethod
    def addDbProjects(cls, projects: dict[str, dict[str, DbProduct]])\
            -> dict[str, dict[str, str | DbExcelProject]]:
        """ Проверяет наличие экземпляров класса по предоставленным аттрибутам.
            Создает новые и обновляет существующие экземпляры класса.
            Вносит изменения за один коммит """
        already_added = {}
        all_keys = ['project_name',
                    'product']
        for key in projects.keys():
            project = add_missing_keys(dictionary=projects[key],
                                       keys=all_keys)
            if key in already_added:
                db_project = already_added[key]
            else:
                db_project = cls.addDbProject(project_name=project['project_name'],
                                              product=project['product'],
                                              commit_later=True)
                already_added[key] = db_project
            project['db_project'] = db_project
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести проект. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addDbProjects(projects=projects)
        return projects


class DbExcelInterconnection(Base):
    """ SqlAlchemy класс описания таблицы excel_project_product в БД
        Не используется в проекте.
        Нужен был для отслеживания применения изделий
        в выгрузках иерархий в Excel."""

    __tablename__ = 'excel_interconnection'
    pk_pp = Column('pk_pp', Integer, primary_key=True)
    id_product = Column('id_product', ForeignKey("product.id_product"))
    id_project = Column('id_project', ForeignKey("excel_project.id_project"))
    id_document = Column('id_document', ForeignKey("document.id_document"))

    product = relationship('DbProduct', lazy='joined',
                           foreign_keys=[id_product], backref='projects')
    project = relationship('DbExcelProject', lazy='joined',
                           foreign_keys=[id_project], backref='product_ids')
    document = relationship('DbDocument', lazy='joined',
                            foreign_keys=[id_document], backref='projects')

    @classmethod
    def getInterconnection(cls, product: DbProduct,
                           project: DbExcelProject,
                           document: DbDocument) -> DbExcelInterconnection | None:
        """ Возвращает экземпляр DbExcelInterconnection по аттрибутам """
        id_document = None if document is None else document.id_document
        statement = select(cls).where(and_(cls.id_product == product.id_product,
                                           cls.id_document == id_document,
                                           cls.id_project == project.id_project))
        try:
            return DbConnection.executeStatement(statement, one=True)[0]
        except exc.NoResultFound:
            return None

    @classmethod
    def addInterconnection(cls, product: DbProduct,
                           project: DbExcelProject,
                           document: DbDocument,
                           commit_later: bool = False) -> DbExcelInterconnection:
        """ Добавляет в БД информацию о том, каким документом
            закрыто изделие в определенном проекте Excel """
        db_record = cls.getInterconnection(product=product,
                                           project=project,
                                           document=document)

        if not db_record:
            id_document = None if document is None else document.id_document
            db_record = cls(id_product=product.id_product,
                            id_document=id_document,
                            id_project=project.id_project)
            DbConnection.session.add(db_record)
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    DbConnection.session.refresh(db_record)
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось внести проект. Повторная попытка\n{err}')
                    DbConnection.session.rollback()
                    cls.addInterconnection(product=product,
                                           project=project,
                                           document=document,
                                           commit_later=commit_later)
        return db_record

    @classmethod
    def addInterconnections(cls, interconnections: dict[str, dict[str, str]])\
            -> dict[str, dict[str, str | DbExcelInterconnection]]:
        """ Добавляет в БД информацию о том, каким документом
            закрыто изделие в определенном проекте Excel для
            многих изделий за один коммит """
        already_added = {}
        all_keys = ['project_name']
        for key in interconnections.keys():
            interconnection = add_missing_keys(dictionary=interconnections[key],
                                               keys=all_keys)
            if key in already_added:
                db_interconnection = already_added[key]
            else:
                db_interconnection = cls.addInterconnection(product=interconnection['product'],
                                                            project=interconnection['project'],
                                                            document=interconnection['document'],
                                                            commit_later=True)
                already_added[key] = db_interconnection
            interconnection['db_interconnection'] = db_interconnection
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести проект. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addInterconnections(interconnections=interconnections)
        return interconnections


class DbArea(Base):

    """SqlAlchemy класс описания таблицы участков и их свойств в БД"""

    __tablename__ = 'area'
    id_area = Column('id_area', Integer, primary_key=True)
    name = Column('name', String)
    name_short = Column('name_short', String)
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка участков'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbArea) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.name] = item
        cls.data[item.id_area] = item

    @classmethod
    def uniqueData(cls) -> list[DbArea]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: str | int) -> DbArea | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: str | int) -> DbArea | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.name == attr,
                                          cls.id_area == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str | int) -> DbArea | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def updArea(cls, id_area: int, name: str, name_short: str, commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_area not in cls.data:
            cls.addNewArea(name=name, name_short=name_short)
        else:
            db_area = cls.data[id_area]
            db_area.name = name
            db_area.name_short = name_short
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    DbConnection.session.refresh(db_area)
                    cls.addData(db_area)
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить участок {err}. Повторная попытка')
                    DbConnection.session.rollback()
                    cls.updArea(id_area=id_area, name=name, name_short=name_short)

    @classmethod
    def addNewArea(cls, name: str, name_short: str, commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_area = DbArea(name=name, name_short=name_short)
        DbConnection.session.add(db_area)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести участок {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewArea(name=name, name_short=name_short)
        return db_area


class DbWorkplace(Base):
    """SqlAlchemy класс описания таблицы рабочих мест в БД"""

    __tablename__ = 'workplace'
    id_workplace = Column('id_workplace', Integer, primary_key=True)
    name = Column('name', String)
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка рабочих мест'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbWorkplace) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.name] = item
        cls.data[item.id_workplace] = item

    @classmethod
    def uniqueData(cls) -> list[DbWorkplace]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: str | int) -> DbWorkplace | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: str | int) -> DbWorkplace | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.name == attr,
                                          cls.id_workplace == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str | int) -> DbWorkplace | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def updWorkplace(cls, id_workplace: int, name: str, commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_workplace not in cls.data:
            cls.addNewWorkplace(name=name)
        else:
            db_workplace = cls.data[id_workplace]
            db_workplace.name = name
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.data[db_workplace.name] = db_workplace
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить операцию {err}. Повторная попытка')
                    DbConnection.session.rollback()
                    cls.updWorkplace(id_workplace=id_workplace, name=name)

    @classmethod
    def addNewWorkplace(cls, name: str, commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_workplace = DbWorkplace(name=name)
        DbConnection.session.add(db_workplace)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести операцию {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewWorkplace(name=name)
        return db_workplace


class DbOperation(Base):
    """SqlAlchemy класс описания таблицы базовых операции и их свойств в БД"""

    __tablename__ = 'operation'
    id_operation = Column('id_operation', Integer, primary_key=True)
    name = Column('name', String)

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка базовых операций'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbOperation) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.name] = item
        cls.data[item.id_operation] = item

    @classmethod
    def uniqueData(cls) -> list[DbOperation]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: str | int) -> DbOperation | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: str | int) -> DbOperation | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.name == attr,
                                          cls.id_operation == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str | int) -> DbOperation | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def updOperation(cls, id_operation: int, new_name: str, commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_operation not in cls.data:
            cls.addNewOperation(name=new_name)
        else:
            db_operation = cls.data[id_operation]
            db_operation.name = new_name
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить операцию {err}. Повторная попытка')
                    DbConnection.session.rollback()
                    cls.updOperation(id_operation=id_operation, new_name=new_name)

    @classmethod
    def addNewOperation(cls, name: str, commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_operation = DbOperation(name=name)
        DbConnection.session.add(db_operation)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести операцию {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewOperation(name=name)
        return db_operation

    @classmethod
    def delOperation(cls, id_operation: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_operation = cls.data[id_operation]
        DbConnection.session.delete(db_operation)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                del cls.data[db_operation.name]
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить операцию {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delOperation(id_operation=id_operation)


class DbSetting(Base):
    """SqlAlchemy класс описания таблицы типов выполняемых работ и их привязки к операциям"""

    __tablename__ = 'setting'
    id_setting = Column('id_setting', Integer, primary_key=True)
    id_operation = Column('id_operation', ForeignKey("operation.id_operation"))
    text = Column('text', String)

    operation = relationship('DbOperation', lazy='joined',
                             foreign_keys=[id_operation], backref='setting')

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка типов выполняемых работ'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbSetting) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_setting] = item
        cls.data[(item.operation.name, item.text)] = item

    @classmethod
    def uniqueData(cls) -> list[DbSetting]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_setting: int | None = None,
                operation_name: str | None = None,
                operation_text: str | None = None) -> DbSetting | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        if id_setting is not None:
            attr = id_setting
        else:
            attr = (operation_name, operation_text)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple | int) -> DbSetting | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        if isinstance(attr, tuple):
            statement = select(cls).join(DbOperation).where(and_(DbOperation.name == attr[0],
                                                                 cls.text == attr[1]))
        else:
            statement = select(cls).where(cls.id_setting == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple | int) -> DbSetting | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def updSetting(cls, id_setting: int,
                   id_operation: int,
                   text: str,
                   commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_setting not in cls.data:
            cls.addNewSetting(id_operation=id_operation, text=text)
        else:
            db_settings = cls.data[id_setting]
            db_settings.id_operation = id_operation
            db_settings.text = text
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    DbConnection.session.refresh(db_settings)
                    cls.addData(db_settings)
                    # cls.data[db_settings.id_setting] = db_settings
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить свойство {err}. Повторная попытка')
                    DbConnection.session.rollback()
                    cls.updOperation(id_setting=id_setting, id_operation=id_operation, text=text)

    @classmethod
    def addNewSetting(cls, id_operation: int, text: str, commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_settings = DbSetting(id_operation=id_operation, text=text)
        DbConnection.session.add(db_settings)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести свойство {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewSetting(id_operation=id_operation, text=text)
        return db_settings


class DbSettingDoc(Base):
    """ SqlAlchemy класс описания таблицы типов выполняемых
        работ и их привязки к операциям в документам"""

    __tablename__ = 'setting_doc'
    id_setting_doc = Column('id_setting_doc', Integer, primary_key=True)
    id_operation_doc = Column('id_operation_doc', ForeignKey("operation_doc.id_operation_doc"))
    id_setting = Column('id_setting', ForeignKey("setting.id_setting"))

    operation = relationship('DbOperationDoc', lazy='joined',
                             foreign_keys=[id_operation_doc], backref='setting_doc')
    setting = relationship('DbSetting', lazy='joined',
                           foreign_keys=[id_setting], backref='setting_doc')

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка типов выполняемых работ в документах'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbSettingDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[(item.id_setting,
                  item.id_operation_doc)] = item

    @classmethod
    def uniqueData(cls) -> list[DbSettingDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_setting: int, id_operation_doc: int) -> DbSettingDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (id_setting, id_operation_doc)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple) -> DbSettingDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(and_(cls.id_setting == attr[0],
                                           cls.id_operation_doc == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple) -> DbSettingDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def delOutdatedSettings(cls, settings: list) -> None:
        """ Удаление данных из БД """
        keys_for_del = set()
        settings_ids = [setting.default_setting_id for setting in settings if setting.activated]
        for setting in settings:
            for key in cls.data:
                if key[1] == setting.operation.db_operation_doc.id_operation_doc:
                    if key[0] not in settings_ids:
                        keys_for_del.add(key)
        for key in keys_for_del:
            DbConnection.session.delete(cls.data[key])
            del cls.data[key]
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести данные. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.delOutdatedSettings(settings)

    @classmethod
    def newSetting(cls, setting: Setting) -> None:
        """ Создание нового экземпляра ORM класса """
        id_setting = setting.default_setting_id
        id_operation_doc = setting.operation.db_operation_doc.id_operation_doc
        db_setting_doc = cls(id_operation_doc=id_operation_doc,
                             id_setting=id_setting)
        DbConnection.session.add(db_setting_doc)
        key = (id_setting, id_operation_doc)
        cls.data[key] = db_setting_doc

    @classmethod
    def addSetting(cls, setting: Setting, commit_later: bool = False) -> None:
        """ Внесение данных в БД """
        setting_doc = setting.db_setting_doc
        if setting_doc is None and setting.activated:
            cls.newSetting(setting=setting)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные. Повторная попытка\n{err}')
                DbConnection.session.rollback()
                cls.addSetting(setting=setting,
                               commit_later=False)


class DbSettingDef(Base):
    """SqlAlchemy класс описания таблицы переходов и их связь с типами выполняемых работ"""

    __tablename__ = 'setting_def'
    id_setting_def = Column('id_setting_def', Integer, primary_key=True)
    id_setting = Column('id_setting', ForeignKey("setting.id_setting"))
    id_sentence = Column('id_sentence', ForeignKey("sentence.id_sentence"))
    sentence_order = Column('sentence_order', Integer)

    setting = relationship('DbSetting', lazy='joined',
                           foreign_keys=[id_setting], backref='setting_def')
    sentence = relationship('DbSentence', lazy='joined',
                            foreign_keys=[id_sentence], backref='setting_def')

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка cвязей базовых переходов с типами выполняемых работ'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbSettingDef) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        key = (item.id_setting, item.sentence_order)
        cls.data[key] = item
        cls.data[item.id_setting_def] = item

    @classmethod
    def uniqueData(cls) -> list[DbSettingDef]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_setting: int | None = None,
                sentence_order: int | None = None,
                id_setting_def: int | None = None) -> DbSettingDef | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        if id_setting_def is not None:
            attr = id_setting_def
        else:
            attr = (id_setting, sentence_order)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple | int) -> DbSettingDef | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        if isinstance(attr, tuple):
            statement = select(cls).where(and_(cls.id_setting == attr[0],
                                               cls.sentence_order == attr[1]))
        else:
            statement = select(cls).where(cls.id_setting_def == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple | int) -> DbSettingDef | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    # pylint: disable=too-many-arguments
    def updSettingDef(cls, id_setting_def: int,
                      id_setting: int,
                      id_sentence: int,
                      sentence_order: int,
                      commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_setting_def not in cls.data:
            cls.addNewSettingDef(id_setting=id_setting,
                                 id_sentence=id_sentence,
                                 sentence_order=sentence_order)
        else:
            db_settings_def = cls.data[id_setting_def]
            if db_settings_def.id_setting != id_setting \
                    or db_settings_def.id_sentence != id_sentence \
                    or db_settings_def.sentence_order != sentence_order:
                db_settings_def.id_setting = id_setting
                db_settings_def.id_sentence = id_sentence
                db_settings_def.sentence_order = sentence_order
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                        DbConnection.session.refresh(db_settings_def)
                        cls.addData(item=db_settings_def)
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось изменить данные {err}. Повторная попытка')
                        DbConnection.session.rollback()
                        cls.updOperation(id_setting_def=id_setting_def,
                                         id_setting=id_setting,
                                         id_sentence=id_sentence,
                                         sentence_order=sentence_order)

    @classmethod
    def addNewSettingDef(cls, id_setting: int, id_sentence: int, sentence_order: int,
                         commit_later: bool = False) -> DbSettingDef:
        """ Внесение новых данных в БД """
        db_settings_def = DbSettingDef(id_setting=id_setting,
                                       id_sentence=id_sentence,
                                       sentence_order=sentence_order)
        DbConnection.session.add(db_settings_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewSettingDef(id_setting=id_setting,
                                     id_sentence=id_sentence,
                                     sentence_order=sentence_order)
        return db_settings_def

    @classmethod
    def delSettingDef(cls, id_setting_def: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_setting_def = cls.data[id_setting_def]
        DbConnection.session.delete(db_setting_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
                # cls.delData(item=db_setting_def)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delSettingDef(id_setting_def=id_setting_def)


class DbSentence(Base):
    """SqlAlchemy класс описания таблицы переходов и их связь с типами выполняемых работ"""

    __tablename__ = 'sentence'
    id_sentence = Column('id_sentence', Integer, primary_key=True)
    text = Column('text', String)
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка переходов и их связей с типами выполняемых работ'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbSentence) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_sentence] = item
        cls.data[item.text] = item

    @classmethod
    def uniqueData(cls) -> list[DbSentence]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: int | str) -> DbSentence | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: int | str) -> DbSentence | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.id_sentence == attr, cls.text == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int | str) -> DbSentence | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def updSentence(cls, id_sentence: int, text: str, commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_sentence not in cls.data:
            cls.addNewSentence(text=text)
        else:
            db_sentence = cls.data[id_sentence]
            db_sentence.text = text
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    DbConnection.session.refresh(db_sentence)
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить свойство {err}. Повторная попытка')
                    DbConnection.session.rollback()
                    cls.updOperation(id_sentence=id_sentence, text=text)

    @classmethod
    def addNewSentence(cls, text: str, commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_sentence = DbSentence(text=text)
        DbConnection.session.add(db_sentence)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести свойство {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewSentence(text=text)
        return db_sentence


class DbOperationDoc(Base):
    """SqlAlchemy класс описания таблицы типов выполняемых работ и их привязки к операциям"""

    __tablename__ = 'operation_doc'
    id_operation_doc = Column('id_operation_doc', Integer, primary_key=True)
    id_document_real = Column('id_document_real', ForeignKey("document_real.id_document_real"))
    id_operation = Column('id_operation', ForeignKey("operation.id_operation"))
    operation_order = Column('operation_order', Integer)
    id_area = Column('id_area', ForeignKey("area.id_area"))
    id_workplace = Column('id_workplace', ForeignKey("workplace.id_workplace"))
    id_profession = Column('id_profession', ForeignKey("profession.id_profession"))

    area = relationship('DbArea', lazy='joined',
                        foreign_keys=[id_area], backref='operations_doc')
    workplace = relationship('DbWorkplace', lazy='joined',
                             foreign_keys=[id_workplace], backref='operations_doc')
    profession = relationship('DbProfession', lazy='joined',
                              foreign_keys=[id_profession], backref='operations_doc')
    operation = relationship('DbOperation', lazy='joined',
                             foreign_keys=[id_operation], backref='operations_doc')
    document_real = relationship('DbDocumentReal', lazy='joined',
                                 foreign_keys=[id_document_real], backref='operations_doc')

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка операций в документах'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbOperationDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        key = (item.id_document_real,
               item.id_operation,
               item.operation_order)
        cls.data[key] = item

    @classmethod
    def delData(cls, item):
        """ Удаляет из кэша экземпляр класса """
        key = (item.id_document_real,
               item.id_operation,
               item.operation_order)
        del cls.data[key]

    @classmethod
    def uniqueData(cls) -> list[DbOperationDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_operation: int,
                id_document_real: int,
                operation_order: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (id_document_real,
                id_operation,
                operation_order)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(and_(cls.id_document_real == attr[0],
                                           cls.id_operation == attr[1],
                                           cls.operation_order == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def delOutdatedOperations(cls, operations: dict[int, Operation]) -> None:
        """ Удаление данных из БД """
        keys_for_del = set()
        db_operations = [operation.db_operation_doc for operation in operations.values()]
        for operation in operations.values():
            for key, db_operation_doc in cls.data.items():
                try:
                    id_document_real = key[0]
                    if id_document_real == operation.document_main.id_document_real:
                        if db_operation_doc not in db_operations:
                            keys_for_del.add(key)
                except TypeError:
                    pass
        for key in keys_for_del:
            DbConnection.session.delete(cls.data[key])
            del cls.data[key]
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            logging.debug(err)
            DbConnection.session.rollback()
            cls.delOutdatedOperations(operations)

    @classmethod
    def newOperation(cls, operation: Operation) -> None:
        """ Внесение новой операции """
        db_operation_doc = cls(id_document_real=operation.document_main.id_document_real,
                               id_operation=operation.id_operation_def,
                               id_area=operation.area.id,
                               id_workplace=operation.workplace.id,
                               id_profession=operation.profession.id,
                               operation_order=operation.order)
        DbConnection.session.add(db_operation_doc)
        operation.db_operation_doc = db_operation_doc
        key = (operation.document_main.id_document_real,
               operation.id_operation_def,
               operation.order)
        cls.data[key] = db_operation_doc

    @classmethod
    def updOperation(cls, operation: Operation) -> None:
        """ Изменение аттрибутов экземпляра класса """
        operation_doc = operation.db_operation_doc
        operation_doc.id_area = operation.area.id
        operation_doc.id_workplace = operation.workplace.id
        operation_doc.id_profession = operation.profession.id
        operation_doc.operation_order = operation.order

    @classmethod
    def addOperation(cls, operation: Operation, commit_later: bool = False) -> None:
        """ Внесение/Обновление данных """
        operation_doc = operation.db_operation_doc
        if operation_doc is not None:
            cls.updOperation(operation=operation)
        elif operation_doc is None:
            cls.newOperation(operation=operation)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести {operation.num} {operation.name}. '
                            f'Повторная попытка\n{err}')
                DbConnection.session.rollback()
                cls.addOperation(operation=operation,
                                 commit_later=False)


class DbSentenceDoc(Base):
    """ SqlAlchemy класс описания таблицы связей
        базовых переходов с реальными операциями в документах"""

    __tablename__ = 'sentence_doc'
    id_sentence_doc = Column('id_sentence_doc', Integer, primary_key=True)
    id_operation_doc = Column('id_operation_doc', ForeignKey("operation_doc.id_operation_doc"))
    id_sentence = Column('id_sentence', ForeignKey("sentence.id_sentence"))
    id_setting = Column('id_setting', ForeignKey("setting.id_setting"))
    sentence_order = Column('sentence_order', Integer)
    custom_text = Column('custom_text', String)

    operation = relationship('DbOperationDoc', lazy='joined',
                             foreign_keys=[id_operation_doc], backref='sentence')
    sentence = relationship('DbSentence', lazy='joined',
                            foreign_keys=[id_sentence], backref='sentence_doc')
    setting = relationship('DbSetting', lazy='joined',
                           foreign_keys=[id_setting], backref='sentence_doc')

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка связей базовых переходов с реальными операциями'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbSentenceDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        key = (item.id_operation_doc,
               item.sentence_order)
        cls.data[key] = item
        cls.data[item.id_sentence_doc] = item

    @classmethod
    def uniqueData(cls) -> list[DbSentenceDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_sentence_doc: int | None = None,
                id_operation_doc: int | None = None,
                sentence_order: int | None = None) -> DbSentenceDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        if id_sentence_doc is not None:
            attr = id_sentence_doc
        else:
            attr = (id_operation_doc, sentence_order)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple | int) -> DbSentenceDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        if isinstance(attr, tuple):
            statement = select(cls).where(and_(cls.id_operation_doc == attr[0],
                                               cls.sentence_order == attr[1]))
        else:
            statement = select(cls).where(cls.id_sentence_doc == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple | int) -> DbSentenceDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def delSentences(cls, sentences: list[Sentence]) -> None:
        """ Вызов метода удаления данных для нескольких переходов """
        for sentence in sentences:
            if sentence.id_sentence_doc is not None:
                cls.delSentence(sentence)

    @classmethod
    def delSentence(cls, sentence: Sentence) -> None:
        """ Удаление данных из БД """
        db_sentence_doc = cls.data[sentence.id_sentence_doc]

        del cls.data[sentence.id_sentence_doc]
        del cls.data[(db_sentence_doc.id_operation_doc,
                      db_sentence_doc.sentence_order)]
        DbConnection.session.delete(db_sentence_doc)

    @classmethod
    def updSentence(cls, sentence: Sentence, order: int) -> None:
        """ Изменение перехода, привязанного к документу """
        db_sentence_doc = cls.data[sentence.id_sentence_doc]
        if db_sentence_doc.sentence_order != order:
            db_sentence_doc.sentence_order = order
        if sentence.id_def_sentence is None:
            db_sentence_doc.custom_text = sentence.text
            db_sentence_doc.id_sentence = None
        if sentence.id_operation != db_sentence_doc.id_operation_doc:
            db_sentence_doc.id_operation_doc = sentence.id_operation
        return db_sentence_doc

    @classmethod
    def addSentence(cls, sentence: Sentence, order: int) -> DbSentenceDoc:
        """ Внесение данных в БД """
        id_setting = None
        if sentence.setting is not None:
            id_setting = sentence.setting.default_setting_id
        db_sentence_doc = cls(id_operation_doc=sentence.id_operation,
                              id_sentence=sentence.id_def_sentence,
                              id_setting=id_setting,
                              sentence_order=order,
                              custom_text=sentence.custom_text)
        sentence.db_sentence_doc = db_sentence_doc
        DbConnection.session.add(db_sentence_doc)
        key = (db_sentence_doc.id_operation_doc,
               db_sentence_doc.sentence_order)
        cls.data[key] = db_sentence_doc
        return db_sentence_doc

    @classmethod
    def addSentences(cls, sentences: dict[int, Sentence]) -> None:
        """ Внесение нескольких переходов в БД за один коммит """
        all_sentences = []
        for order, sentence in sentences.items():
            if sentence.id_sentence_doc is None:
                all_sentences.append(cls.addSentence(sentence=sentence, order=order))
            else:
                if sentence.id_sentence_doc in cls.data:
                    all_sentences.append(cls.updSentence(sentence=sentence, order=order))
        try:
            DbConnection.sessionCommit()
            for db_sentence_doc in all_sentences:
                cls.data[db_sentence_doc.id_sentence_doc] = db_sentence_doc
                cls.data[(db_sentence_doc.id_operation_doc,
                          db_sentence_doc.sentence_order)] = db_sentence_doc
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести переходы. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addSentences(sentences=sentences)


class DbMaterial(Base):
    """SqlAlchemy класс описания таблицы материалов и их свойств"""

    __tablename__ = 'material'
    id_material = Column('id_material', Integer, primary_key=True)
    name = Column('name', String)
    mat_type = Column('type', String)
    name_short = Column('name_short', String)
    document = Column('document', String)
    kind = Column('kind', String)

    data = {}
    all_types = set()
    all_kinds = set()

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка материалов и их свойств'
        cls.data = {}
        cls.all_types = set()
        cls.all_kinds = set()
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbMaterial) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_material] = item
        cls.data[item.name] = item
        cls.all_types.update([item.mat_type])
        cls.all_kinds.update([item.kind])

    @classmethod
    def uniqueData(cls) -> list[DbMaterial]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: str | int) -> DbMaterial | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: str | int) -> DbMaterial | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.name == attr,
                                          cls.id_material == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str | int) -> DbMaterial | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def allTypes(cls) -> set[str]:
        """ Возвращает список типов материалов """
        cls.updCheck()
        return cls.all_types

    @classmethod
    def allKinds(cls) -> set[str]:
        """ Возвращает список видов материалов """
        cls.updCheck()
        return cls.all_kinds

    @classmethod
    # pylint: disable=too-many-arguments
    def updMat(cls, id_material: int,
               name: str,
               mat_type: str,
               name_short: str,
               document: str,
               kind: str,
               commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_material not in cls.data:
            cls.addNewMat(name=name,
                          mat_type=mat_type,
                          name_short=name_short,
                          document=document,
                          kind=kind)
        else:
            db_material = cls.data[id_material]
            db_material.name = name
            db_material.mat_type = mat_type
            db_material.name_short = name_short
            db_material.document = document
            db_material.kind = kind
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить ИОТ\n{err}\nПовторная попытка')
                    DbConnection.session.rollback()
                    cls.updMat(id_material=id_material,
                               name=name,
                               mat_type=mat_type,
                               name_short=name_short,
                               document=document,
                               kind=kind)

    @classmethod
    # pylint: disable=too-many-arguments
    def addNewMat(cls, name: str,
                  mat_type: str,
                  name_short: str,
                  document: str,
                  kind: str,
                  commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_material = DbMaterial(name=name,
                                 mat_type=mat_type,
                                 name_short=name_short,
                                 document=document, kind=kind)
        DbConnection.session.add(db_material)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести ИОТ\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewMat(name=name,
                              mat_type=mat_type,
                              name_short=name_short,
                              document=document,
                              kind=kind)
        return db_material


class DbMaterialDef(Base):
    """SqlAlchemy класс описания таблицы материалов в переходах по умолчанию"""

    __tablename__ = 'material_def'
    id_material_def = Column('id_material_def', Integer, primary_key=True)
    id_sentence = Column('id_sentence', ForeignKey("sentence.id_sentence"))
    id_material = Column('id_material', ForeignKey("material.id_material"))

    sentence = relationship('DbSentence', lazy='joined',
                            foreign_keys=[id_sentence], backref='material_def')
    material = relationship('DbMaterial', lazy='joined',
                            foreign_keys=[id_material], backref='material_def')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка материалов в переходах по умолчанию'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbMaterialDef) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_material_def] = item
        if item.id_sentence in cls.data:
            cls.data[item.id_sentence].append(item)
        else:
            cls.data[item.id_sentence] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbMaterialDef]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_material_def: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_material_def)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_material_def == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def updMatDef(cls, id_material_def: int,
                  id_sentence: int,
                  id_material: int,
                  commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_material_def not in cls.items:
            cls.addNewMatDef(id_sentence=id_sentence, id_material=id_material)
        else:
            db_mat_def = cls.items[id_material_def]
            if db_mat_def.id_sentence != id_sentence or db_mat_def.id_material != id_material:
                db_mat_def.id_sentence = id_sentence
                db_mat_def.id_material = id_material
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                        DbConnection.session.refresh(db_mat_def)
                        cls.addData(item=db_mat_def)
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось изменить данные {err}. Повторная попытка')
                        DbConnection.session.rollback()
                        cls.updMatDef(id_material_def=id_material_def,
                                      id_sentence=id_sentence,
                                      id_material=id_material)

    @classmethod
    def addNewMatDef(cls, id_sentence: int,
                     id_material: int,
                     commit_later: bool = False) -> DbIOTDef:
        """ Внесение новых данных в БД """
        db_mat_def = DbMaterialDef(id_sentence=id_sentence, id_material=id_material)
        DbConnection.session.add(db_mat_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewMatDef(id_sentence=id_sentence, id_material=id_material)
        return db_mat_def

    @classmethod
    def delMatDef(cls, id_material_def: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_material_def = cls.items[id_material_def]
        DbConnection.session.delete(db_material_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
                # cls.delData(item=db_material_def)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delMatDef(id_material_def=id_material_def)


class DbMaterialDoc(Base):

    """SqlAlchemy класс описания таблицы материалов в пользовательских переходах"""

    __tablename__ = 'material_doc'
    id_material_doc = Column('id_material_doc', Integer, primary_key=True)
    id_sentence_doc = Column('id_sentence_doc', ForeignKey("sentence_doc.id_sentence_doc"))
    id_material = Column('id_material', ForeignKey("material.id_material"))

    sentence = relationship('DbSentenceDoc', lazy='joined',
                            foreign_keys=[id_sentence_doc], backref='material_doc')
    material = relationship('DbMaterial', lazy='joined',
                            foreign_keys=[id_material], backref='material_doc')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка материалов в пользовательских переходах'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbMaterialDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_material_doc] = item
        if item.id_sentence_doc in cls.data:
            cls.data[item.id_sentence_doc].append(item)
        else:
            cls.data[item.id_sentence_doc] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbMaterialDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_material_doc: int) -> DbMaterialDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_material_doc)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbMaterialDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_material_doc == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbMaterialDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def delMats(cls, sentence: Sentence) -> None:
        """ Удаление данных из БД """
        if sentence.id_sentence_doc in cls.data:
            for mat_doc in cls.data[sentence.id_sentence_doc]:
                if mat_doc.material.name not in sentence.mat:
                    cls.data[sentence.id_sentence_doc].remove(mat_doc)
                    DbConnection.session.delete(mat_doc)

    @classmethod
    def addMats(cls, sentence: Sentence) -> None:
        """ Добавление материалов к переходу """
        db_mats_in_doc = []
        if sentence.id_sentence_doc in cls.data:
            db_mats_in_doc = [mat_doc.material for mat_doc in cls.data[sentence.id_sentence_doc]]
        for mat in sentence.mat.values():
            if mat.db_mat not in db_mats_in_doc:
                db_mat_doc = cls(id_sentence_doc=sentence.id_sentence_doc,
                                 id_material=mat.db_mat.id_material)
                DbConnection.session.add(db_mat_doc)
                if sentence.id_sentence_doc in cls.data:
                    cls.data[sentence.id_sentence_doc].append(db_mat_doc)
                else:
                    cls.data[sentence.id_sentence_doc] = [db_mat_doc]

    @classmethod
    def updMats(cls, sentences: dict[int, Sentence]) -> None:
        """ Изменение данных списка привязанных к переходу материалов """
        for sentence in sentences.values():
            if sentence.id_def_sentence is None:
                cls.delMats(sentence)
                cls.addMats(sentence)
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести материалы. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.updMats(sentences=sentences)


class DbRig(Base):
    """SqlAlchemy класс описания таблицы оснастки и ее свойств"""

    __tablename__ = 'rig'
    id_rig = Column('id_rig', Integer, primary_key=True)
    name = Column('name', String)
    rig_type = Column('type', String)
    name_short = Column('name_short', String)
    document = Column('document', String)
    kind = Column('kind', String)

    data = {}
    all_name_short = set()
    all_types = set()

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка оснастки и ее свойств'
        cls.data = {}
        cls.all_name_short = set()
        cls.all_types = set()
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbRig) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_rig] = item
        cls.data[item.name] = item
        cls.all_name_short.update([item.name_short])
        cls.all_types.update([item.rig_type])

    @classmethod
    def uniqueData(cls) -> list[DbRig]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: int | str) -> DbRig | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: int | str) -> DbRig | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.id_rig == attr,
                                          cls.name == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int | str) -> DbRig | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def allTypes(cls) -> set[str]:
        """ Возвращает уникальные типы оснастки """
        cls.updCheck()
        return cls.all_types

    @classmethod
    # pylint: disable=too-many-arguments
    def updRig(cls, id_rig: int,
               name: str,
               rig_type: str,
               name_short: str,
               document: str,
               kind: str,
               commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_rig not in cls.data:
            cls.addNewRig(name=name,
                          rig_type=rig_type,
                          name_short=name_short,
                          document=document,
                          kind=kind)
        else:
            db_rig = cls.data[id_rig]
            db_rig.name = name
            db_rig.rig_type = rig_type
            db_rig.name_short = name_short
            db_rig.document = document
            db_rig.kind = kind
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить ИОТ\n{err}\nПовторная попытка')
                    DbConnection.session.rollback()
                    cls.updRig(id_rig=id_rig,
                               name=name,
                               rig_type=rig_type,
                               name_short=name_short,
                               document=document,
                               kind=kind)

    @classmethod
    # pylint: disable=too-many-arguments
    def addNewRig(cls, name: str,
                  rig_type: str,
                  name_short: str,
                  document: str,
                  kind: str,
                  commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_rig = DbRig(name=name,
                       rig_type=rig_type,
                       name_short=name_short,
                       document=document,
                       kind=kind)
        DbConnection.session.add(db_rig)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести ИОТ\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewRig(name=name,
                              rig_type=rig_type,
                              name_short=name_short,
                              document=document,
                              kind=kind)
        return db_rig


class DbRigDef(Base):
    """SqlAlchemy класс описания таблицы использования оснастки по умолчанию в базовых переходах """

    __tablename__ = 'rig_def'
    id_rig_def = Column('id_rig_def', Integer, primary_key=True)
    id_sentence = Column('id_sentence', ForeignKey("sentence.id_sentence"))
    id_rig = Column('id_rig', ForeignKey("rig.id_rig"))

    sentence = relationship('DbSentence', lazy='joined',
                            foreign_keys=[id_sentence], backref='rig_def')
    rig = relationship('DbRig', lazy='joined',
                       foreign_keys=[id_rig], backref='rig_def')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка использования оснастки по умолчанию в базовых переходах'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbRigDef) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_rig_def] = item
        if item.id_sentence in cls.data:
            cls.data[item.id_sentence].append(item)
        else:
            cls.data[item.id_sentence] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbRigDef]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_rig_def: int) -> DbRigDef | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_rig_def)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbRigDef | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_rig_def == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbRigDef | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def updRigDef(cls, id_rig_def: int,
                  id_sentence: int,
                  id_rig: int,
                  commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_rig_def not in cls.items:
            cls.addNewRigDef(id_sentence=id_sentence, id_rig=id_rig)
        else:
            db_rig_def = cls.items[id_rig_def]
            if db_rig_def.id_sentence != id_sentence or db_rig_def.id_rig != id_rig:
                db_rig_def.id_sentence = id_sentence
                db_rig_def.id_rig = id_rig
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                        DbConnection.session.refresh(db_rig_def)
                        cls.addData(item=db_rig_def)
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось изменить данные {err}. Повторная попытка')
                        DbConnection.session.rollback()
                        cls.updRigDef(id_rig_def=id_rig_def, id_sentence=id_sentence, id_rig=id_rig)

    @classmethod
    def addNewRigDef(cls, id_sentence: int, id_rig: int, commit_later: bool = False) -> DbIOTDef:
        """ Внесение новых данных в БД """
        db_rig_def = DbRigDef(id_sentence=id_sentence, id_rig=id_rig)
        DbConnection.session.add(db_rig_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewRigDef(id_sentence=id_sentence, id_rig=id_rig)
        return db_rig_def

    @classmethod
    def delRigDef(cls, id_rig_def: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_rig_def = cls.items[id_rig_def]
        DbConnection.session.delete(db_rig_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delRigDef(id_rig_def=id_rig_def)


class DbRigDoc(Base):
    """ SqlAlchemy класс описания таблицы использования
        оснастки в реальных переходах определенных документов"""

    __tablename__ = 'rig_doc'
    id_rig_doc = Column('id_rig_doc', Integer, primary_key=True)
    id_sentence_doc = Column('id_sentence_doc', ForeignKey("sentence_doc.id_sentence_doc"))
    id_rig = Column('id_rig', ForeignKey("rig.id_rig"))

    sentence = relationship('DbSentenceDoc', lazy='joined',
                            foreign_keys=[id_sentence_doc], backref='rig')
    rig = relationship('DbRig', lazy='joined',
                       foreign_keys=[id_rig], backref='rig_doc')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка оснастки в реальных переходах определенных документов'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbRigDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_rig_doc] = item
        if item.id_sentence_doc in cls.data:
            cls.data[item.id_sentence_doc].append(item)
        else:
            cls.data[item.id_sentence_doc] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbRigDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_rig_doc: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_rig_doc)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_rig_doc == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def delRigs(cls, sentence: Sentence) -> None:
        """ Удаление данных из БД """
        if sentence.id_sentence_doc in cls.data:
            for rig_doc in cls.data[sentence.id_sentence_doc]:
                if rig_doc.rig.name not in sentence.rig:
                    cls.data[sentence.id_sentence_doc].remove(rig_doc)
                    DbConnection.session.delete(rig_doc)

    @classmethod
    def addRigs(cls, sentence: Sentence) -> None:
        """ Добавление оснастки к переходам """
        db_rigs_in_doc = []
        if sentence.id_sentence_doc in cls.data:
            db_rigs_in_doc = [rig_doc.rig for rig_doc in cls.data[sentence.id_sentence_doc]]
        for rig in sentence.rig.values():
            if rig.db_rig not in db_rigs_in_doc:
                db_rig_doc = cls(id_sentence_doc=sentence.id_sentence_doc,
                                 id_rig=rig.db_rig.id_rig)
                DbConnection.session.add(db_rig_doc)
                if sentence.id_sentence_doc in cls.data:
                    cls.data[sentence.id_sentence_doc].append(db_rig_doc)
                else:
                    cls.data[sentence.id_sentence_doc] = [db_rig_doc]

    @classmethod
    def updRigs(cls, sentences: dict[int, Sentence]) -> None:
        """ Изменение оснастки привязанной к определенному переходу """
        for sentence in sentences.values():
            if sentence.id_def_sentence is None:
                cls.delRigs(sentence)
                cls.addRigs(sentence)
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести оснастку. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.updRigs(sentences=sentences)


class DbEquipment(Base):
    """SqlAlchemy класс описания таблицы оборудования и его свойств"""

    __tablename__ = 'equipment'
    id_equipment = Column('id_equipment', Integer, primary_key=True)
    name = Column('name', String)
    name_short = Column('name_short', String)
    type = Column('type', String)

    data = {}
    all_name_short = set()

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка оборудования и его свойств'
        cls.data = {}
        cls.all_name_short = set()
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbEquipment) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_equipment] = item
        cls.data[item.name] = item
        cls.all_name_short.update([item.name_short])

    @classmethod
    def uniqueData(cls) -> list[DbEquipment]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: int | str) -> DbEquipment | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: int | str) -> DbEquipment | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.id_equipment == attr,
                                          cls.name == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int | str) -> DbEquipment | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def allShortNames(cls) -> set[str]:
        """ Возвращает названия оборудования """
        cls.updCheck()
        return cls.all_name_short

    @classmethod
    # pylint: disable=too-many-arguments
    def updEquipment(cls, id_equipment: int,
                     name: str,
                     name_short: str,
                     type_name: str,
                     commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_equipment not in cls.data:
            cls.addNewEquipment(name=name, name_short=name_short, type_name=type_name)
        else:
            db_equipment = cls.data[id_equipment]
            db_equipment.name = name
            db_equipment.name_short = name_short
            db_equipment.type = type_name
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить оборудование\n{err}\nПовторная попытка')
                    DbConnection.session.rollback()
                    cls.updEquipment(id_equipment=id_equipment,
                                     name=name,
                                     name_short=name_short,
                                     type_name=type_name)

    @classmethod
    def addNewEquipment(cls, name: str,
                        name_short: str,
                        type_name: str,
                        commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_equipment = DbEquipment(name=name,
                                   name_short=name_short,
                                   type=type_name)
        DbConnection.session.add(db_equipment)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести оборудование\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewEquipment(name=name,
                                    name_short=name_short,
                                    type_name=type_name)
        return db_equipment


class DbEquipmentDef(Base):

    """ SqlAlchemy класс описания таблицы использования
        оборудования по умолчанию в базовых переходах """

    __tablename__ = 'equipment_def'
    id_equipment_def = Column('id_equipment_def', Integer, primary_key=True)
    id_sentence = Column('id_sentence', ForeignKey("sentence.id_sentence"))
    id_equipment = Column('id_equipment', ForeignKey("equipment.id_equipment"))

    sentence = relationship('DbSentence', lazy='joined',
                            foreign_keys=[id_sentence], backref='equipment_def')
    equipment = relationship('DbEquipment', lazy='joined',
                             foreign_keys=[id_equipment], backref='equipment_def')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка использования оборудования по умолчанию в базовых переходах'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbEquipmentDef) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_equipment_def] = item
        if item.id_sentence in cls.data:
            cls.data[item.id_sentence].append(item)
        else:
            cls.data[item.id_sentence] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbEquipmentDef]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_equipment_def: int) -> DbEquipmentDef | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_equipment_def)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbEquipmentDef | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_equipment_def == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbEquipmentDef | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def updEqtDef(cls, id_equipment_def: int,
                  id_sentence: int,
                  id_equipment: int,
                  commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_equipment_def not in cls.items:
            cls.addNewEqtDef(id_sentence=id_sentence, id_equipment=id_equipment)
        else:
            db_eqt_def = cls.items[id_equipment_def]
            if db_eqt_def.id_sentence != id_sentence or db_eqt_def.id_equipment != id_equipment:
                db_eqt_def.id_sentence = id_sentence
                db_eqt_def.id_equipment = id_equipment
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                        DbConnection.session.refresh(db_eqt_def)
                        cls.addData(item=db_eqt_def)
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось изменить данные {err}. Повторная попытка')
                        DbConnection.session.rollback()
                        cls.updEqtDef(id_equipment_def=id_equipment_def,
                                      id_sentence=id_sentence,
                                      id_equipment=id_equipment)

    @classmethod
    def addNewEqtDef(cls, id_sentence: int,
                     id_equipment: int,
                     commit_later: bool = False) -> updEqtDef:
        """ Внесение новых данных в БД """
        db_eqt_def = DbEquipmentDef(id_sentence=id_sentence,
                                    id_equipment=id_equipment)
        DbConnection.session.add(db_eqt_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewRigDef(id_sentence=id_sentence,
                                 id_equipment=id_equipment)
        return db_eqt_def

    @classmethod
    def delEqtDef(cls, id_equipment_def: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_equipment_def = cls.items[id_equipment_def]
        DbConnection.session.delete(db_equipment_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
                # cls.delData(item=db_equipment_def)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delEqtDef(id_equipment_def=id_equipment_def)


class DbEquipmentDoc(Base):
    """ SqlAlchemy класс описания таблицы использования
        оборудования в реальных переходах определенных документов"""

    __tablename__ = 'equipment_doc'
    id_equipment_doc = Column('id_equipment_doc', Integer, primary_key=True)
    id_sentence_doc = Column('id_sentence_doc', ForeignKey("sentence_doc.id_sentence_doc"))
    id_equipment = Column('id_equipment', ForeignKey("equipment.id_equipment"))

    sentence = relationship('DbSentenceDoc', lazy='joined',
                            foreign_keys=[id_sentence_doc], backref='equipment')
    equipment = relationship('DbEquipment', lazy='joined',
                             foreign_keys=[id_equipment], backref='equipment_doc')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка оборудования в реальных переходах определенных документов'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbEquipmentDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_equipment_doc] = item
        if item.id_sentence_doc in cls.data:
            cls.data[item.id_sentence_doc].append(item)
        else:
            cls.data[item.id_sentence_doc] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbEquipmentDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_equipment_doc: int) -> DbEquipmentDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_equipment_doc)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbEquipmentDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_equipment_doc == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbEquipmentDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def delEquipments(cls, sentence: Sentence) -> None:
        """ Удаление данных из БД """
        if sentence.id_sentence_doc in cls.data:
            for equipment_doc in cls.data[sentence.id_sentence_doc]:
                if equipment_doc.equipment.name not in sentence.equipment:
                    cls.data[sentence.id_sentence_doc].remove(equipment_doc)
                    DbConnection.session.delete(equipment_doc)

    @classmethod
    def addEquipments(cls, sentence: Sentence) -> None:
        """ Добавление оборудования к переходу """
        db_equipments_in_doc = []
        if sentence.id_sentence_doc in cls.data:
            for equipment_doc in cls.data[sentence.id_sentence_doc]:
                db_equipments_in_doc.append(equipment_doc.equipment)
        for equipment in sentence.equipment.values():
            if equipment.db_equipment not in db_equipments_in_doc:
                db_equipment_doc = cls(id_sentence_doc=sentence.id_sentence_doc,
                                       id_equipment=equipment.db_equipment.id_equipment)
                DbConnection.session.add(db_equipment_doc)
                if sentence.id_sentence_doc in cls.data:
                    cls.data[sentence.id_sentence_doc].append(db_equipment_doc)
                else:
                    cls.data[sentence.id_sentence_doc] = [db_equipment_doc]

    @classmethod
    def updEquipments(cls, sentences: dict[int, Sentence]) -> None:
        """ Изменение данных в БД """
        for sentence in sentences.values():
            if sentence.id_def_sentence is None:
                cls.delEquipments(sentence)
                cls.addEquipments(sentence)
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести оборудование. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.updEquipments(sentences=sentences)


class DbIOT(Base):
    """SqlAlchemy класс описания таблицы ИОТ и их реквизитов"""

    __tablename__ = 'iot'
    id_iot = Column('id_iot', Integer, primary_key=True)
    deno = Column('deno', String)
    name = Column('name', String)
    name_short = Column('name_short', String)
    type = Column('type', String)
    type_short = Column('type_short', String)

    data = {}
    all_type_short = set()

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка ИОТ и их реквизитов'
        cls.data = {}
        cls.all_type_short = set()
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbIOT) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_iot] = item
        cls.data[item.deno] = item
        cls.data[item.name_short] = item
        cls.all_type_short.update([item.type_short])

    @classmethod
    def uniqueData(cls) -> list[DbIOT]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, attr: int | str) -> DbIOT | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: int | str) -> DbIOT | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(or_(cls.id_iot == attr,
                                          cls.deno == attr,
                                          cls.name_short == attr))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int | str) -> DbIOT | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def allTypeShort(cls) -> set[str]:
        """ Возвращает уникальные названия типов """
        cls.updCheck()
        return cls.all_type_short

    @classmethod
    # pylint: disable=too-many-arguments
    def updIOT(cls, id_iot: int,
               type_name: str,
               type_short: str,
               deno: str,
               name: str,
               name_short: str,
               commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_iot not in cls.data:
            cls.addNewIOT(type_name=type_name,
                          type_short=type_short,
                          deno=deno,
                          name=name,
                          name_short=name_short)
        else:
            db_iot = cls.data[id_iot]
            db_iot.type_long = type_name
            db_iot.type_short = type_short
            db_iot.deno = deno
            db_iot.name = name
            db_iot.name_short = name_short
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить ИОТ\n{err}\nПовторная попытка')
                    DbConnection.session.rollback()
                    cls.updIOT(id_iot=id_iot,
                               type_name=type_name,
                               type_short=type_short,
                               deno=deno,
                               name=name,
                               name_short=name_short)

    @classmethod
    # pylint: disable=too-many-arguments
    def addNewIOT(cls, type_name: str,
                  type_short: str,
                  deno: str,
                  name: str,
                  name_short: str,
                  commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_iot = DbIOT(type=type_name,
                       type_short=type_short,
                       deno=deno,
                       name=name,
                       name_short=name_short)
        DbConnection.session.add(db_iot)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести ИОТ\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewIOT(type_name=type_name,
                              type_short=type_short,
                              deno=deno,
                              name=name,
                              name_short=name_short)
        return db_iot


class DbIOTDef(Base):
    """SqlAlchemy класс описания таблицы ИОТ по умолчанию в базовых переходах """

    __tablename__ = 'iot_def'
    id_iot_def = Column('id_iot_def', Integer, primary_key=True)
    id_sentence = Column('id_sentence', ForeignKey("sentence.id_sentence"))
    id_iot = Column('id_iot', ForeignKey("iot.id_iot"))

    sentence = relationship('DbSentence', lazy='joined',
                            foreign_keys=[id_sentence], backref='iot_def')
    iot = relationship('DbIOT', lazy='joined',
                       foreign_keys=[id_iot], backref='iot_def')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка ИОТ по умолчанию в базовых переходах'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbIOTDef) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_iot_def] = item
        if item.id_sentence in cls.data:
            cls.data[item.id_sentence].append(item)
        else:
            cls.data[item.id_sentence] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbIOTDef]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls):
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_iot_def: int) -> DbIOTDef | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_iot_def)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbIOTDef | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_iot_def == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbIOTDef | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def updIOTDef(cls, id_iot_def: int,
                  id_sentence: int,
                  id_iot: int,
                  commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_iot_def not in cls.items:
            cls.addNewIOTDef(id_sentence=id_sentence, id_iot=id_iot)
        else:
            db_iot_def = cls.items[id_iot_def]
            if db_iot_def.id_sentence != id_sentence or db_iot_def.id_iot != id_iot:
                db_iot_def.id_sentence = id_sentence
                db_iot_def.id_iot = id_iot
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                        DbConnection.session.refresh(db_iot_def)
                        cls.addData(item=db_iot_def)
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось изменить данные {err}. Повторная попытка')
                        DbConnection.session.rollback()
                        cls.updIOTDef(id_iot_def=id_iot_def, id_sentence=id_sentence, id_iot=id_iot)

    @classmethod
    def addNewIOTDef(cls, id_sentence: int,
                     id_iot: int,
                     commit_later: bool = False) -> DbIOTDef:
        """ Внесение новых данных в БД """
        db_iot_def = DbIOTDef(id_sentence=id_sentence,
                              id_iot=id_iot)
        DbConnection.session.add(db_iot_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewIOTDef(id_sentence=id_sentence,
                                 id_iot=id_iot)
        return db_iot_def

    @classmethod
    def delIOTDef(cls, id_iot_def: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_iot_def = cls.items[id_iot_def]
        DbConnection.session.delete(db_iot_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
                # cls.delData(item=db_iot_def)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delIOTDef(id_iot_def=id_iot_def)


class DbIOTDoc(Base):
    """SqlAlchemy класс описания таблицы ИОТ в пользовательских переходах """

    __tablename__ = 'iot_doc'
    id_iot_doc = Column('id_iot_doc', Integer, primary_key=True)
    id_sentence_doc = Column('id_sentence_doc', ForeignKey("sentence_doc.id_sentence_doc"))
    id_iot = Column('id_iot', ForeignKey("iot.id_iot"))

    sentence = relationship('DbSentenceDoc', lazy='joined',
                            foreign_keys=[id_sentence_doc], backref='iot_doc')
    iot = relationship('DbIOT', lazy='joined',
                       foreign_keys=[id_iot], backref='iot_doc')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка ИОТ по умолчанию в пользовательских переходах'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbIOTDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_iot_doc] = item
        if item.id_sentence_doc in cls.data:
            cls.data[item.id_sentence_doc].append(item)
        else:
            cls.data[item.id_sentence_doc] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbIOTDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_iot_doc: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_iot_doc)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_iot_doc == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbOperationDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def delIots(cls, sentence: Sentence) -> None:
        """ Удаление данных из БД """
        if sentence.id_sentence_doc in cls.data:
            for iot_doc in cls.data[sentence.id_sentence_doc]:
                if iot_doc.iot.deno not in sentence.iot:
                    cls.data[sentence.id_sentence_doc].remove(iot_doc)
                    DbConnection.session.delete(iot_doc)

    @classmethod
    def addIots(cls, sentence: Sentence) -> None:
        """ Добавление ИОТ к переходу """
        db_iots_in_doc = []
        if sentence.id_sentence_doc in cls.data:
            db_iots_in_doc = [iot_doc.iot for iot_doc in cls.data[sentence.id_sentence_doc]]
        for iot in sentence.iot.values():
            if iot.db_iot not in db_iots_in_doc:
                db_iot_doc = cls(id_sentence_doc=sentence.id_sentence_doc,
                                 id_iot=iot.db_iot.id_iot)
                DbConnection.session.add(db_iot_doc)
                if sentence.id_sentence_doc in cls.data:
                    cls.data[sentence.id_sentence_doc].append(db_iot_doc)
                else:
                    cls.data[sentence.id_sentence_doc] = [db_iot_doc]

    @classmethod
    def updIots(cls, sentences: dict[int, Sentence]):
        """ Изменение ИОТ, привязанных к определенному переходу """
        for sentence in sentences.values():
            if sentence.id_def_sentence is None:
                cls.delIots(sentence)
                cls.addIots(sentence)
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести ИОТ. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.updIots(sentences=sentences)


class DbDocDef(Base):
    """SqlAlchemy класс описания таблицы типов документов по умолчанию в базовых переходах """

    __tablename__ = 'doc_def'
    id_doc_def = Column('id_doc_def', Integer, primary_key=True)
    id_sentence = Column('id_sentence', ForeignKey("sentence.id_sentence"))
    id_type = Column('id_type', ForeignKey("document_type.id_type"))

    sentence = relationship('DbSentence', lazy='joined',
                            foreign_keys=[id_sentence], backref='doc_def')
    document_type = relationship('DbDocumentType', lazy='joined',
                                 foreign_keys=[id_type], backref='doc_def')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка типов документов по умолчанию в базовых переходах'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocDef) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_doc_def] = item
        if item.id_sentence in cls.data:
            cls.data[item.id_sentence].append(item)
        else:
            cls.data[item.id_sentence] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbDocDef]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_doc_def: int) -> DbDocDef | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_doc_def)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbDocDef | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_doc_def == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbDocDef | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def updDocDef(cls, id_doc_def: int,
                  id_sentence: int,
                  id_type: int,
                  commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_doc_def not in cls.items:
            cls.addNewDocDef(id_sentence=id_sentence, id_type=id_type)
        else:
            db_doc_def = cls.items[id_doc_def]
            if db_doc_def.id_sentence != id_sentence or db_doc_def.id_type != id_type:
                db_doc_def.id_sentence = id_sentence
                db_doc_def.id_type = id_type
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                        DbConnection.session.refresh(db_doc_def)
                        cls.addData(item=db_doc_def)
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось изменить данные {err}. Повторная попытка')
                        DbConnection.session.rollback()
                        cls.updDocDef(id_doc_def=id_doc_def,
                                      id_sentence=id_sentence,
                                      id_type=id_type)

    @classmethod
    def addNewDocDef(cls, id_sentence: int,
                     id_type: int,
                     commit_later: bool = False) -> DbDocDef:
        """ Внесение новых данных в БД """
        db_doc_def = DbDocDef(id_sentence=id_sentence,
                              id_type=id_type)
        DbConnection.session.add(db_doc_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.addNewDocDef(id_sentence=id_sentence,
                                 id_type=id_type)
        return db_doc_def

    @classmethod
    def delDocDef(cls, id_doc_def: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_doc_def = cls.items[id_doc_def]
        DbConnection.session.delete(db_doc_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
                # cls.delData(item=db_iot_def)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delDocDef(id_doc_def=id_doc_def)


class DbDocDoc(Base):
    """SqlAlchemy класс описания таблицы документов в пользовательских переходах """

    __tablename__ = 'doc_doc'
    id_doc_doc = Column('id_doc_doc', Integer, primary_key=True)
    id_sentence_doc = Column('id_sentence_doc', ForeignKey("sentence_doc.id_sentence_doc"))
    id_document_real = Column('id_document_real', ForeignKey("document_real.id_document_real"))

    sentence = relationship('DbSentenceDoc', lazy='joined',
                            foreign_keys=[id_sentence_doc], backref='doc_doc')
    document_real = relationship('DbDocumentReal', lazy='joined',
                                 foreign_keys=[id_document_real], backref='doc_doc')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка документов в пользовательских переходах'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbDocDoc) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_doc_doc] = item
        if item.id_sentence_doc in cls.data:
            cls.data[item.id_sentence_doc].append(item)
        else:
            cls.data[item.id_sentence_doc] = [item]

    @classmethod
    def uniqueData(cls) -> list[DbDocDoc]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_doc_doc: int) -> DbDocDoc | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_doc_doc)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbDocDoc | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_doc_doc == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbDocDoc | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def delDocs(cls, sentence: Sentence):
        """ Удаление данных из БД """
        if sentence.id_sentence_doc in cls.data:
            for doc_doc in cls.data[sentence.id_sentence_doc]:
                if doc_doc.id_document_real not in sentence.doc_ids:
                    cls.data[sentence.id_sentence_doc].remove(doc_doc)
                    DbConnection.session.delete(doc_doc)

    @classmethod
    def addDocs(cls, sentence: Sentence):
        """ Добавление документов к переходу """
        id_documents = []
        if sentence.id_sentence_doc in cls.data:
            id_documents = [doc.id_document_real for doc in cls.data[sentence.id_sentence_doc]]
        for doc in sentence.doc.values():
            if doc.id_document_real not in id_documents:
                doc_doc = cls(id_sentence_doc=sentence.id_sentence_doc,
                              id_document_real=doc.id_document_real)
                DbConnection.session.add(doc_doc)
                if sentence.id_sentence_doc in cls.data:
                    cls.data[sentence.id_sentence_doc].append(doc_doc)
                else:
                    cls.data[sentence.id_sentence_doc] = [doc_doc]

    @classmethod
    def updDocs(cls, sentences: dict[int, Sentence]):
        """ Изменение типов документов привязанных к определенному переходу """
        for sentence in sentences.values():
            if sentence.id_def_sentence is None:
                cls.delDocs(sentence)
                cls.addDocs(sentence)
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести документы в МК. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.updDocs(sentences=sentences)


class DbProfession(Base):
    """SqlAlchemy класс описания таблицы профессий"""

    __tablename__ = 'profession'
    id_profession = Column('id_profession', Integer, primary_key=True)
    name = Column('name', String)
    code = Column('code', String)

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка профессий'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbProfession) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.name] = item

    @classmethod
    def uniqueData(cls) -> list[DbProfession]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, name: str) -> DbProfession | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, name)

    @classmethod
    def getDataFromDb(cls, attr: str) -> DbProfession | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.name == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str) -> DbProfession | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def updProfession(cls, id_profession: int,
                      name: str,
                      code: str,
                      commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_profession not in cls.data:
            cls.addNewProfession(name=name, code=code)
        else:
            db_profession = cls.data[id_profession]
            db_profession.name = name
            db_profession.code = code
            if not commit_later:
                try:
                    DbConnection.sessionCommit()
                    cls.updData()
                except (IntegrityError, OperationalError) as err:
                    show_dialog(f'Не удалось изменить профессию\n{err}\nПовторная попытка')
                    DbConnection.session.rollback()
                    cls.updProfession(id_profession=id_profession,
                                      name=name,
                                      code=code)

    @classmethod
    def addNewProfession(cls, name: str,
                         code: str,
                         commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_profession = DbProfession(name=name, code=code)
        DbConnection.session.add(db_profession)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести профессию\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewProfession(name=name, code=code)
        return db_profession


class DbOperationDef(Base):
    """SqlAlchemy класс описания таблицы связи вида изделия с операциями, местом изготовления"""

    __tablename__ = 'operation_def'
    id_operation_def = Column('id_operation_def', Integer, primary_key=True)
    id_operation = Column('id_operation', ForeignKey("operation.id_operation"))
    id_area = Column('id_area', ForeignKey("area.id_area"))
    id_workplace = Column('id_workplace', ForeignKey("workplace.id_workplace"))
    id_profession = Column('id_profession', ForeignKey("profession.id_profession"))
    id_kind = Column('id_kind', ForeignKey("product_kind.id_kind"))

    operation = relationship('DbOperation', lazy='joined',
                             foreign_keys=[id_operation], backref='operation_def')
    area = relationship('DbArea', lazy='joined',
                        foreign_keys=[id_area], backref='operation_def')
    workplace = relationship('DbWorkplace', lazy='joined',
                             foreign_keys=[id_workplace], backref='operation_def')
    profession = relationship('DbProfession', lazy='joined',
                              foreign_keys=[id_profession], backref='operation_def')
    kind = relationship('DbProductKind', lazy='joined',
                        foreign_keys=[id_kind], backref='operation_def')

    data = {}
    items = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка связи вида изделия с операциями, местом изготовления'
        cls.data = {}
        cls.items = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbOperationDef) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.items[item.id_operation_def] = item
        if item.kind.name == 'неизвестно':
            for id_kind in DbProductKind.data:
                cls.updDataValues(id_kind=id_kind, db_operation_def=item)
        else:
            cls.updDataValues(id_kind=item.id_kind, db_operation_def=item)

    @classmethod
    def uniqueData(cls) -> list[DbOperationDef]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        # return BaseMethods.uniqueData(cls)
        cls.updCheck()
        return cls.items.values()

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_operation_def: int) -> DbOperationDef | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_operation_def)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbOperationDef | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_operation_def == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbOperationDef | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.items.get(attr, None)

    @classmethod
    def updDataValues(cls, id_kind: int | Column, db_operation_def: DbOperationDef) -> None:
        """ Метод обновления кэша """
        if id_kind in cls.data:
            operation_list = cls.data[id_kind]
            operation_list.append(db_operation_def)
            operation_list = list(set(operation_list))
            cls.data[id_kind] = operation_list
        else:
            cls.data[id_kind] = [db_operation_def]

    @classmethod
    # pylint: disable=too-many-arguments
    def updOperationDef(cls, id_operation_def: int,
                        id_operation: int,
                        id_area: int,
                        id_workplace: int,
                        id_profession: int,
                        id_kind: int,
                        commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        if id_operation_def not in cls.items:
            cls.addNewOperationDef(id_operation=id_operation,
                                   id_area=id_area,
                                   id_workplace=id_workplace,
                                   id_profession=id_profession,
                                   id_kind=id_kind)
        else:
            db_operation_def = cls.items[id_operation_def]
            if db_operation_def.id_operation != id_operation \
                    or db_operation_def.id_operation != id_operation \
                    or db_operation_def.id_area != id_area \
                    or db_operation_def.id_workplace != id_workplace \
                    or db_operation_def.id_profession != id_profession \
                    or db_operation_def.id_kind != id_kind:

                db_operation_def.id_operation = id_operation
                db_operation_def.id_area = id_area
                db_operation_def.id_workplace = id_workplace
                db_operation_def.id_profession = id_profession
                db_operation_def.id_kind = id_kind
                if not commit_later:
                    try:
                        DbConnection.sessionCommit()
                        DbConnection.session.refresh(db_operation_def)
                        cls.addData(item=db_operation_def)
                    except (IntegrityError, OperationalError) as err:
                        show_dialog(f'Не удалось изменить данные\n{err}\nПовторная попытка')
                        DbConnection.session.rollback()
                        cls.updOperationDef(id_operation_def=id_operation_def,
                                            id_operation=id_operation,
                                            id_area=id_area,
                                            id_workplace=id_workplace,
                                            id_profession=id_profession,
                                            id_kind=id_kind)

    @classmethod
    # pylint: disable=too-many-arguments
    def addNewOperationDef(cls, id_operation: int,
                           id_area: int,
                           id_workplace: int,
                           id_profession: int,
                           id_kind: int,
                           commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_operation_def = DbOperationDef(id_operation=id_operation,
                                          id_area=id_area,
                                          id_workplace=id_workplace,
                                          id_profession=id_profession,
                                          id_kind=id_kind)
        DbConnection.session.add(db_operation_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести данные\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewOperationDef(id_operation=id_operation,
                                       id_area=id_area,
                                       id_workplace=id_workplace,
                                       id_profession=id_profession,
                                       id_kind=id_kind)
        return db_operation_def

    @classmethod
    def delOperationDef(cls, id_operation_def: int, commit_later: bool = False) -> None:
        """ Удаление данных из БД """
        db_operation_def = cls.items[id_operation_def]
        DbConnection.session.delete(db_operation_def)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
                # cls.delData(item=db_operation_def)
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось удалить данные {err}. Повторная попытка')
                DbConnection.session.rollback()
                cls.delOperationDef(id_operation_def=id_operation_def)


class DbMkExcel(Base):

    """SqlAlchemy класс описания таблицы общих данных о мк в excel"""

    __tablename__ = 'mk_excel'
    id_mk_excel = Column('id_mk_excel', Integer, primary_key=True)
    id_document_real = Column('id_document_real', ForeignKey("document_real.id_document_real"))
    code = Column('code', Integer)
    kind = Column('kind', Integer)
    area = Column('area', Integer)

    document_real = relationship('DbDocumentReal', lazy='joined',
                                 foreign_keys=[id_document_real], backref='excel_mk')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка данных общих данных о маршрутных карт в excel'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbMkExcel) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.id_document_real] = item

    @classmethod
    def uniqueData(cls) -> list[DbMkExcel]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_document_real: int) -> DbMkExcel | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, id_document_real)

    @classmethod
    def getDataFromDb(cls, attr: int) -> DbMkExcel | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.id_document_real == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: int) -> DbMkExcel | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    def getMkExcel(cls, id_document_real) -> DbMkExcel | None:
        """ Возвращает данные о мк (excel), сохраненные после импорта,
            для экспорта в новый состав excel """
        statement = select(cls).where(cls.id_document_real == id_document_real)
        try:
            data = DbConnection.executeStatement(statement, one=True)[0]
        except IndexError:
            data = None
        return data

    @classmethod
    # pylint: disable=too-many-arguments
    def addMkExcel(cls, code, kind, area, id_document_real, commit_later=True):
        """ Добавление импортированных данных о мк из excel """
        db_mk_excel = cls.getMkExcel(id_document_real)
        if db_mk_excel is not None:
            db_mk_excel.updMkExcel(code=code,
                                   kind=kind,
                                   area=area)
        else:
            db_mk_excel = DbMkExcel(id_document_real=id_document_real,
                                    code=code,
                                    kind=kind,
                                    area=area)
        DbConnection.session.add(db_mk_excel)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                DbConnection.session.refresh(db_mk_excel)
            except (IntegrityError, OperationalError) as err:
                logging.debug(err)
                DbConnection.session.rollback()
                cls.addMkExcel(code=code,
                               kind=kind,
                               area=area,
                               id_document_real=id_document_real,
                               commit_later=commit_later)
        return db_mk_excel

    @classmethod
    def addMkExcelMultiple(cls, data):
        """ Добавление многих записей за один коммит """
        already_added = {}
        all_keys = ['id_document_real',
                    'code',
                    'kind',
                    'area',
                    'sentences']
        for key in data.keys():
            item = add_missing_keys(dictionary=data[key],
                                    keys=all_keys)
            if key in already_added:
                db_mk_excel = already_added[key]
            else:
                db_mk_excel = cls.addMkExcel(id_document_real=item['id_document_real'],
                                             code=item['code'],
                                             kind=item['kind'],
                                             area=item['area'],
                                             commit_later=True)
                already_added[key] = db_mk_excel
            item['db_mk_excel'] = db_mk_excel
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            show_dialog(f'Не удалось внести данные МК. Повторная попытка\n{err}')
            DbConnection.session.rollback()
            cls.addMkExcelMultiple(data=data)
        return data

    def updMkExcel(self, code, kind, area):
        """ Обновление кода операций """
        if code and code != self.code:
            self.code = code
        if kind and kind != self.kind:
            self.kind = kind
        if area and area != self.area:
            self.area = area


class DbMkExcelSentences(Base):
    """SqlAlchemy класс описания таблицы переходов мк из excel"""

    __tablename__ = 'mk_excel_sentences'
    id_mk_excel_sentences = Column('id_mk_excel_sentences', Integer, primary_key=True)
    id_mk_excel = Column('id_mk_excel', ForeignKey("mk_excel.id_mk_excel"))
    number = Column('number', Integer)
    code = Column('code', Integer)
    text = Column('text', Integer)

    mk_excel = relationship('DbMkExcel', lazy='joined',
                            foreign_keys=[id_mk_excel], backref='mk_excel_sentences')
    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных """
        title = 'Загрузка данных переходов маршрутных карт из excel'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbMkExcelSentences) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[(item.id_mk_excel, item.number)] = item

    @classmethod
    def uniqueData(cls) -> list[DbMkExcelSentences]:
        """ Возвращает список уникальных экземпляров класса из
            словаря кэшированных данных """
        return BaseMethods.uniqueData(cls)

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, id_mk_excel: int, number: int) -> DbMkExcelSentences | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        attr = (id_mk_excel, number)
        return BaseMethods.getData(cls, attr)

    @classmethod
    def getDataFromDb(cls, attr: tuple) -> DbMkExcelSentences | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(and_(cls.id_mk_excel == attr[0],
                                           cls.number == attr[1]))
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: tuple) -> DbMkExcelSentences | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    # pylint: disable=too-many-arguments
    def addMkExcelSentence(cls, id_mk_excel: int,
                           number: int,
                           code: str,
                           text: str,
                           commit_later: bool = True) -> DbMkExcelSentences:
        """ Добавляет в БД данные о тексте для определенной операции
            из данных экспортированных из составов Excel"""
        db_mk_excel_sentence = cls.getData(id_mk_excel=id_mk_excel,
                                           number=number)
        if db_mk_excel_sentence is not None:
            db_mk_excel_sentence.updMkExcelSentence(code, text)
        else:
            db_mk_excel_sentence = DbMkExcelSentences(id_mk_excel=id_mk_excel,
                                                      number=number,
                                                      code=code,
                                                      text=text)
            DbConnection.session.add(db_mk_excel_sentence)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                DbConnection.session.refresh(db_mk_excel_sentence)
            except (IntegrityError, OperationalError) as err:
                logging.debug(err)
                DbConnection.session.rollback()
                cls.addMkExcelSentence(id_mk_excel=id_mk_excel,
                                       number=number,
                                       code=code,
                                       text=text,
                                       commit_later=commit_later)
        return db_mk_excel_sentence

    @classmethod
    def addMkExcelSentencesMultiple(cls, data: dict[str, dict[str, int | str]])\
            -> dict[str, dict[str, int | str | DbMkExcelSentences]]:
        """ Внесение нескольких записей за один коммит """
        already_added = {}
        all_keys = ['id_mk_excel',
                    'number',
                    'code',
                    'text']
        for key in data.keys():
            item = add_missing_keys(dictionary=data[key],
                                    keys=all_keys)
            if key in already_added:
                db_mk_excel_sentences = already_added[key]
            else:
                db_mk_excel_sentences = cls.addMkExcelSentence(id_mk_excel=item['id_mk_excel'],
                                                               number=item['number'],
                                                               code=item['code'],
                                                               text=item['text'],
                                                               commit_later=True)
                already_added[key] = db_mk_excel_sentences
            item['db_mk_excel_sentences'] = db_mk_excel_sentences
        try:
            DbConnection.sessionCommit()
        except (IntegrityError, OperationalError) as err:
            logging.debug(err)
            DbConnection.session.rollback()
            cls.addMkExcelSentencesMultiple(data=data)
        return data

    def updMkExcelSentence(self, code, text):
        """ Обновление привязки кода операции и переходов из Excel """
        if code and code != self.code:
            self.code = code
        if text and text != self.text:
            self.text = text


class DbUsers(Base):
    """SqlAlchemy класс описания таблицы пользователей"""

    __tablename__ = 'users'
    id_user = Column('id_user', Integer, primary_key=True)
    name = Column('name', String)
    surname = Column('surname', String)
    patronymic = Column('patronymic', String)
    user_name = Column('user_name', String)
    password = Column('password', String)
    id_product_last = Column('id_product_last', ForeignKey("product.id_product"))

    product = relationship('DbProduct', lazy='joined',
                           foreign_keys=[id_product_last], backref='last_users')

    data = {}

    @classmethod
    def updData(cls) -> None:
        """ Кэширование данных пользователей """
        title = 'Загрузка данных пользователей'
        cls.data = {}
        BaseMethods.updData(cls, title)

    @classmethod
    def addData(cls, item: DbUsers) -> None:
        """ Кэширует данные. Добавляет экземпляр класса ORM модели
            в словарь, хранящийся в классе, используя определенные
            аттрибуты экземпляра в качестве ключей словаря """
        cls.data[item.user_name] = item

    @classmethod
    def updCheck(cls) -> None:
        """ Проверяет кэшированы ли данные. Кэширует если нет """
        BaseMethods.updCheck(cls)

    @classmethod
    def getData(cls, user_name: str) -> DbUsers | None:
        """ Возвращает экземпляр ORM класса. Проверяет наличие в кэше,
            и если отсутствует, то запрашивает в БД """
        return BaseMethods.getData(cls, user_name)

    @classmethod
    def getDataFromDb(cls, attr: str) -> DbUsers | None:
        """ Возвращает экземпляр ORM класса по совпадению одного из полей в БД """
        statement = select(cls).where(cls.user_name == attr)
        return BaseMethods.getDataFromDb(cls, statement)

    @classmethod
    def getDataFromDict(cls, attr: str) -> DbUsers | None:
        """ Возвращает экземпляр ORM класса из кэша """
        return cls.data.get(attr, None)

    @classmethod
    # pylint: disable=too-many-arguments
    def addNewUser(cls,
                   user_name: str,
                   name: str | None = None,
                   surname: str | None = None,
                   patronymic: str | None = None,
                   password: str | None = None,
                   id_product_last: int | None = None,
                   commit_later: bool = False):
        """ Внесение новых данных в БД """
        db_user = DbUsers(user_name=user_name,
                          name=name,
                          surname=surname,
                          patronymic=patronymic,
                          password=password,
                          id_product_last=id_product_last)
        DbConnection.session.add(db_user)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось внести пользователя\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.addNewUser(user_name=user_name,
                               name=name,
                               surname=surname,
                               patronymic=patronymic,
                               password=password,
                               id_product_last=id_product_last)
        return db_user

    @classmethod
    # pylint: disable=too-many-arguments
    def updUser(cls, user_name: str,
                name: str | None = None,
                surname: str | None = None,
                patronymic: str | None = None,
                password: str | None = None,
                id_product_last: int | None = None,
                commit_later: bool = False) -> None:
        """ Изменение данных в БД """
        db_user = cls.getData(user_name=user_name)
        if db_user is None:
            cls.addNewUser(user_name=user_name,
                           name=name,
                           surname=surname,
                           patronymic=patronymic,
                           password=password,
                           id_product_last=id_product_last,
                           commit_later=commit_later)
        else:
            upd_attrs(obj=db_user,
                      name=name,
                      surname=surname,
                      patronymic=patronymic,
                      password=password,
                      id_product_last=id_product_last)
        if not commit_later:
            try:
                DbConnection.sessionCommit()
                cls.updData()
            except (IntegrityError, OperationalError) as err:
                show_dialog(f'Не удалось изменить данные пользователя\n{err}\nПовторная попытка')
                DbConnection.session.rollback()
                cls.updNewUser(user_name=user_name,
                               name=name,
                               surname=surname,
                               patronymic=patronymic,
                               password=password,
                               id_product_last=id_product_last,
                               commit_later=commit_later)

    @staticmethod
    def updAttr(db_item, attr_dict):
        """ Добавляет отсутствующие аттрибуты.
            НЕ ИСПОЛЬЗУЕТСЯ """
        for attr, value in attr_dict.items():
            if value is not None:
                setattr(db_item, attr, value)
        return db_item
