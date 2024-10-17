from typing import List

from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
import models, schemas, database, auth, utils
import globals
from constant import Constant
from utils import log
from helper import *

router = APIRouter()


@router.get("/info")
def read_info(current_user: models.User = Depends(auth.get_current_user)):
    user_config = globals.sys_config[current_user.username]
    empkey = user_config[Constant.USER_CFG_EMPLOYEE_KEY]
    employee = globals.sys_employees[empkey]
    return {"name": employee[Constant.EMP_KEY_EMP_NAME], "setting": globals.sys_setting, "config": user_config}


@router.get('/employees')
def employees():
    return JSONResponse(content=globals.sys_employees)


@router.post('/reload_employees')
def reload_employees(current_user: models.User = Depends(auth.get_current_user)
                     ):
    load_employees()
    return JSONResponse(content=globals.sys_employees)


@router.get("/employees/{employee_id}")
def get_employee(employee_id: str):
    if employee_id in globals.sys_employees:
        return JSONResponse(content=globals.sys_employees[employee_id])
    return JSONResponse(content={"error": "Employee not found"}, status_code=404)


@router.get('/projects')
def get_projects(
        current_user: models.User = Depends(auth.get_current_user)
):
    user_name = current_user.username
    user_config = globals.sys_config[user_name]

    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]

    mode = int(employee[Constant.EMP_KEY_WORK_MODE])

    log(f"get projects by mode = {mode}")

    allprjs, _, _ = read_projects_by_user(mode, user_name)

    log(allprjs)

    result_prjs = []
    for prjid in allprjs.keys():
        result_prjs.append(prjid + '|' + allprjs[prjid])

    return JSONResponse(content={"projects": json.dumps(result_prjs)},
                        status_code=200)


@router.get('/getcode')
def get_code(current_user: models.User = Depends(auth.get_current_user)
             ):
    user_name = current_user.username
    user_config = globals.sys_config[user_name]
    code_file_path = get_code_file_path(user_config, user_name)

    if not os.path.exists(code_file_path):
        raise HTTPException(status_code=404, detail="Code file not found")

    code_text = read_text_file(code_file_path)

    # 返回 JSON 响应
    return JSONResponse(content={
        "codeText": code_text
    })


def get_code_file_path(user_config, user_name):
    mode = int(user_config[Constant.USER_CFG_PROJ_MODE])
    prj_id = user_config[Constant.USER_CFG_PROJ_ID]
    app_name = user_config[Constant.USER_CFG_APP_NAME]
    func_file = user_config[Constant.USER_CFG_FUNC_FILE]
    work_root_path = globals.sys_setting[Constant.SET_WORK_PATH]
    work_mode_paths = globals.sys_setting[Constant.SET_WORK_MODE_PATH]
    work_mode_path = work_mode_paths[int(mode)]
    code_root_path = os.path.join(work_root_path, work_mode_path, "public", "users", user_name)
    code_file_path = os.path.join(code_root_path, prj_id, app_name, func_file)
    return code_file_path


@router.get('/download_code')
def download_code(current_user: models.User = Depends(auth.get_current_user)
                  ):
    user_name = current_user.username
    user_config = globals.sys_config[user_name]
    code_file_path = get_code_file_path(user_config, user_name)
    filename = user_config[Constant.USER_CFG_FUNC_FILE]
    if not os.path.exists(code_file_path):
        raise HTTPException(status_code=404, detail="Code file not found")

    log("down code :" + filename)

    return FileResponse(code_file_path, media_type='application/octet-stream', filename=filename)


@router.get('/workurl')
def get_work_url(
        current_user: models.User = Depends(auth.get_current_user)
):
    user_name = current_user.username
    user_config = globals.sys_config[user_name]
    mode = int(user_config[Constant.USER_CFG_PROJ_MODE])
    prj_id = user_config[Constant.USER_CFG_PROJ_ID]
    app_name = user_config[Constant.USER_CFG_APP_NAME]
    func_file = user_config[Constant.USER_CFG_FUNC_FILE]

    work_root_urls = globals.sys_setting[Constant.SET_WORK_MODE_URL]
    work_root_url = work_root_urls[int(mode)]

    url = f"{work_root_url}"
    if mode == 0:
        url = f"{work_root_url}#show@{user_name}@{prj_id}@{app_name}@{func_file}"

    return url


@router.post("/conversations")
def create_conversation(conversation: schemas.ConversationCreate,
                        current_user: models.User = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_conversation = models.Conversation(**conversation.dict())
    db_conversation.user_id = current_user.id
    db_conversation.employee_id = conversation.employee_id
    db_conversation.title = conversation.title
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.get("/conversations", response_model=List[schemas.ConversationResponse])
def get_conversation(current_user: models.User = Depends(auth.get_current_user),
                     db: Session = Depends(database.get_db)):
    user_config = globals.sys_config[current_user.username]
    log(user_config)
    emp_id = user_config[Constant.USER_CFG_EMPLOYEE_KEY]
    log(emp_id)
    employee = globals.sys_employees[emp_id]
    employee_id = employee[Constant.EMP_KEY_EMP_ID]
    conversations = (db.query(models.Conversation).
                     filter(models.Conversation.user_id == current_user.id,
                            models.Conversation.employee_id == employee_id).all())
    return conversations


@router.get("/conversations/{conversion_id}/messages")
def get_conversation_message(conversion_id: int, current_user: models.User = Depends(auth.get_current_user),
                             db: Session = Depends(database.get_db)):
    messages = db.query(models.Message).filter(models.Message.conversation_id == conversion_id).all()
    result = []
    user_config = globals.sys_config[current_user.username]
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    for msg in messages:
        result.append({'sender': 'user', 'text': msg.message, 'name': current_user.username})
        result.append({'sender': 'assistant', 'text': msg.response, 'name': employee[Constant.EMP_KEY_EMP_NAME]})
    return result


@router.get("/thumbnails/")
async def get_all_thumbnails(current_user: models.User = Depends(auth.get_current_user)):
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + current_user.username

    # 获取图片文件名列表
    files = get_image_files(UPLOAD_DIR)

    if not files:
        raise HTTPException(status_code=404, detail="No images found")

    thumbnails = []
    for file_name in files:
        image_path = os.path.join(UPLOAD_DIR, file_name)
        # 生成缩略图并编码为 Base64
        thumbnail_base64 = generate_thumbnail_base64(image_path)
        thumbnails.append({
            "filename": file_name,
            "thumbnail": thumbnail_base64
        })

    return JSONResponse(content=thumbnails)


@router.post("/history")
async def read_history_file(filename: str = Form(...),
                            current_user: models.User = Depends(auth.get_current_user)):
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + current_user.username

    # 构造文件路径
    image_path = os.path.join(UPLOAD_DIR, f"{filename}")
    desc_path = os.path.join(UPLOAD_DIR, f"{filename}_desc.txt")
    code_path = os.path.join(UPLOAD_DIR, f"{filename}_code.txt")

    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    if not os.path.exists(desc_path):
        raise HTTPException(status_code=404, detail="Description file not found")
    if not os.path.exists(code_path):
        raise HTTPException(status_code=404, detail="Code file not found")

    # 获取图片的 Base64 编码
    image_base64 = get_image_base64(image_path)

    # 读取描述文件和代码文件的内容
    markdown_text = read_text_file(desc_path)
    code_text = read_text_file(code_path)

    # 返回 JSON 响应
    return JSONResponse(content={
        "image": image_base64,
        "markdownText": markdown_text,
        "codeText": code_text
    })


@router.post("/functions")
def get_all_functions_by_user_and_proj(
        prj_id: str = Form(...),
        current_user: models.User = Depends(auth.get_current_user)
):
    username = current_user.username
    user_config = globals.sys_config[username]
    idx = int(user_config[Constant.USER_CFG_PROJ_MODE])

    work_path = globals.sys_setting[Constant.SET_WORK_PATH]
    work_mode_path = globals.sys_setting[Constant.SET_WORK_MODE_PATH]
    user_root_path = os.path.join(work_path, work_mode_path[idx], "public", "users", username)

    log(user_root_path)

    route_path = f"{user_root_path}/{prj_id}/route.json"

    if not os.path.exists(route_path):
        write_json_file(route_path, [])

    route_js = read_json_file(route_path)

    # 返回 JSON 响应
    return JSONResponse(content={
        "functions": route_js
    })
