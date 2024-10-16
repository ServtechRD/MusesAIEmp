from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime

import globals
from constant import Constant
from models import ImageFileVersion, AppFunctionVersion


def get_next_image_file_version(db, user_name: str, filename: str):
    # 查询最新的版本记录
    latest_version = db.query(ImageFileVersion).filter_by(
        user_name=user_name,
        filename=filename
    ).order_by(desc(ImageFileVersion.timestamp)).first()

    max_ver = globals.sys_setting[Constant.SET_VERSION_IMAGE_COUNT]

    new_ver = 0
    # 如果有最新版本，返回版本号+1
    if latest_version:
        new_ver = latest_version.version + 1

    if new_ver >= max_ver:
        new_ver = 0

    return new_ver


def get_next_app_function_version(db, user_name: str, proj_id: str, app_name: str, func_name: str):
    # 查询最新的版本记录
    latest_version = db.query(AppFunctionVersion).filter_by(
        user_name=user_name,
        proj_id=proj_id,
        app_name=app_name,
        func_name=func_name
    ).order_by(desc(AppFunctionVersion.timestamp)).first()

    max_ver = globals.sys_setting[Constant.SET_VERSION_FUNC_COUNT]

    new_ver = 0
    # 如果有最新版本，返回版本号+1
    if latest_version:
        new_ver = latest_version.version + 1

    if new_ver >= max_ver:
        new_ver = 0

    return new_ver


def upsert_image_file_version(db, user_name, filename, version):
    stmt = insert(ImageFileVersion).values(
        user_name=user_name,
        filename=filename,
        version=version,
        timestamp=datetime.utcnow()
    )

    # 如果主键冲突，则更新 timestamp
    stmt = stmt.on_duplicate_key_update(
        timestamp=datetime.utcnow()
    )

    db.execute(stmt)
    db.commit()


def upsert_app_function_version(db, user_name, proj_id, app_name, func_name, version):
    stmt = insert(AppFunctionVersion).values(
        user_name=user_name,
        proj_id=proj_id,
        app_name=app_name,
        func_name=func_name,
        version=version,
        timestamp=datetime.utcnow()
    )

    # 如果主键冲突，则更新 timestamp
    stmt = stmt.on_duplicate_key_update(
        timestamp=datetime.utcnow()
    )

    db.execute(stmt)
    db.commit()


def get_all_image_file_versions(db: Session, user_name: str, filename: str):
    # 查询所有版本号，并按时间戳升序排序
    versions = db.query(ImageFileVersion.version).filter_by(
        user_name=user_name,
        filename=filename
    ).order_by(asc(ImageFileVersion.timestamp)).all()

    # 将结果转换为版本号列表
    return [v.version for v in versions]


def get_all_app_function_versions(db: Session, user_name: str, proj_id: str, app_name: str, func_name: str):
    # 查询所有版本号，并按时间戳升序排序
    versions = db.query(AppFunctionVersion.version).filter_by(
        user_name=user_name,
        proj_id=proj_id,
        app_name=app_name,
        func_name=func_name
    ).order_by(asc(AppFunctionVersion.timestamp)).all()

    # 将结果转换为版本号列表
    return [v.version for v in versions]
