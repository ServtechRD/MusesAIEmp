import os

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

import auth
import models
from constant import Constant
from helper import write_json_file
from utils import log,get_password_hash
from models import User
from schemas import UserCreate, UserLogin, Token
from database import get_db
from utils import get_password_hash
from auth import create_access_token, authenticate_user, get_user
from globals import *



def register_user(user: UserCreate, db: Session):
    db_user = auth.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail='帳號已被註冊')
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = auth.create_access_token(data={'sub': new_user.username})
    return {'access_token': access_token, 'token_type': 'bearer'}


def login_user(form_data: UserLogin, db: Session):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail='帳號或密码错误')
    access_token = auth.create_access_token(data={'sub': user.username})
    log('sys_config keys')
    log(globals.sys_config.keys())
    log('user name :' + user.username)
    if (user.username not in globals.sys_config.keys()):
        globals.sys_config[user.username] = globals.sys_default_config.copy()

    globals.sys_config[user.username][Constant.USER_CFG_EMPLOYEE_KEY] = form_data.employee
    log(globals.sys_config)

    emp = globals.sys_employees[form_data.employee]
    idx = int(emp[Constant.EMP_KEY_WORK_MODE])

    if idx == 0:
        log("emp mode is 0")
        root_path = globals.sys_setting[Constant.SET_WORK_PATH]
        work_mode_path = globals.sys_setting[Constant.SET_WORK_MODE_PATH][idx]
        user_path = os.path.join(root_path, work_mode_path, "public", "users", form_data.username)
        if not os.path.exists(user_path):
            log("create user folder :" + user_path)
            os.makedirs(user_path)

        prj_route_json = os.path.join(user_path, "route.json")
        if not os.path.exists(prj_route_json):
            log("create user route.json :" + prj_route_json)
            write_json_file(prj_route_json, {})

    return {'access_token': access_token, 'token_type': 'bearer'}