import glob
import json
from datetime import datetime
from io import BytesIO

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker
from typing import List
import models, schemas, database, auth, utils
import shutil
import os
import uuid
from openai import OpenAI
import base64

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError

from constant import *
from llmengine import LLMEngine

from helper import *
from routers import bases
from services import user_service, version_service
from services.prompt_service import build_image_task_messages
from utils import log

from PIL import Image

from globals import *

load_dotenv()

models.Base.metadata.create_all(bind=database.engine)

# 获取环境变量
SECRET_KEY = os.getenv('SECRET_KEY')
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_NAME = os.getenv('ASSISTANT_NAME', 'ASSISTANT')

# client = OpenAI(api_key=OPENAI_API_KEY)

print("KEY:" + SECRET_KEY)
# print("OPENAI KEY:" + OPENAI_API_KEY)

# 数据
data = {"sub": "user_id"}

# 讀取設定檔
load_setting()
# 讀取預設值
load_default_config()
# 讀取員工
load_employees()

'''
log('setting')
log(sys_setting)
log('default config')
log(sys_default_config)
log('employees')
log(sys_employees)
'''

llm = LLMEngine()

# web

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# 将不同模块的路由器包含到主应用中
app.include_router(bases.router)


@app.get("/")
def read_root():
    return {"message": "Hello API Server ! Cross-Domain is enabled"}


@app.post('/register', response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    return user_service.register_user(user, db)


@app.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    return user_service.login_user(form_data, db)


@app.post("/versions/image")
async def get_version_image(
        filename: str = Form(...),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    versions = version_service.get_all_image_file_versions(db, current_user.username, filename)
    return JSONResponse(content={"versions": json.dumps(versions)},
                        status_code=200)


@app.post("/versions/func")
async def get_version_func(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    user_config = sys_config[current_user.username]

    prj_id = user_config[Constant.USER_CFG_PROJ_ID]
    app_name = user_config[Constant.USER_CFG_APP_NAME]
    func_file = user_config[Constant.USER_CFG_FUNC_FILE]

    versions = version_service.get_all_app_function_versions(db, current_user.username, prj_id, app_name, func_file)
    log(f"proj:{prj_id} / app:{app_name} / func :{func_file}")

    return JSONResponse(content={"versions": json.dumps(versions)}, status_code=200)



@app.post("/version/image/switch")
async def switch_version_image(
        version: int = Form(...),
        filename: str = Form(...),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    username = current_user.username
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + username
    code_file = f"{UPLOAD_DIR}/{filename}_code.txt"
    code_file_ver = f"{UPLOAD_DIR}/{filename}_code.txt.{version}"

    # copy file
    with open(code_file, "w") as out_f:
        shutil.copyfileobj(code_file_ver, out_f)

    return JSONResponse(content={"message": "影像程式版本切換到成功"}, status_code=200)


@app.post("/version/func/switch")
async def switch_version_func(
        version: int = Form(...),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    username = current_user.username

    user_config = sys_config[current_user.username]
    idx = int(user_config[Constant.USER_CFG_PROJ_MODE])

    work_path = globals.sys_setting[Constant.SET_WORK_PATH]
    work_mode_path = globals.sys_setting[Constant.SET_WORK_MODE_PATH]
    user_root_path = os.path.join(work_path, work_mode_path[idx], "public", "users", username)

    prj_id = user_config[Constant.USER_CFG_PROJ_ID]
    app_name = user_config[Constant.USER_CFG_APP_NAME]
    func_file = user_config[Constant.USER_CFG_FUNC_FILE]

    log(user_root_path)

    output_folder = f"{user_root_path}/{prj_id}/{app_name}"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_path = f"{output_folder}/{func_file}"
    output_path_ver = output_path + f".{version}"

    # copy file
    with open(output_path, "w") as out_f:
        shutil.copyfileobj(output_path_ver, out_f)

    return JSONResponse(content={"message": "應用程式版本切換到成功"}, status_code=200)


@app.get('/messages')
def get_messages(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    messages = db.query(models.Conversation).filter(models.Conversation.user_id == current_user.id).all()
    result = []
    for msg in messages:
        result.append({'sender': 'user', 'text': msg.message})
        result.append({'sender': 'assistant', 'text': msg.response})
    return result


@app.post('/message')
async def send_message(
        message: str = Form(...),
        conversation_id: int = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),

):
    user_name = current_user.username
    user_id = current_user.id
    user_input = message  # .text
    task_id = str(uuid.uuid4())

    if len(user_input) > 0:
        if (user_input.startswith("/SETTING")):
            return JSONResponse(content={"message": json.dumps(globals.sys_setting)},
                                status_code=200)
        elif (user_input.startswith("/CONFIG")):
            user_config = globals.sys_config[current_user.username]
            input_items = user_input.split()
            print("parser items :" + str(len(input_items)))
            if (len(input_items) > 1):
                print("config have action")
                if (input_items[1].upper() == "SET"):
                    print("config setting")
                    if (len(input_items) > 3):
                        config_key = input_items[2]
                        config_value = input_items[3]
                        user_config[config_key] = config_value
                        print(f"update {config_key} = {config_value}")

                        # setting prj_mode, trigger action
                        if config_key == Constant.USER_CFG_PROJ_MODE:
                            if config_value == "0":  # mode 0
                                idx = int(config_value)
                                # get prj path
                                all_prjs, prj_route_json, user_root_path = read_projects_by_user(idx, user_name)

                                all_prjs[user_config[Constant.USER_CFG_PROJ_ID]] = user_config[
                                    Constant.USER_CFG_PROJ_DESC]

                                write_json_file(prj_route_json, all_prjs)

                                # update app route.json
                                user_prj_path = os.path.join(user_root_path, user_config[Constant.USER_CFG_PROJ_ID])
                                app_route_json = os.path.join(user_prj_path, "route.json")

                                if not os.path.exists(user_prj_path):
                                    os.makedirs(user_prj_path)
                                    write_json_file(app_route_json, [])

            return JSONResponse(content={"message": json.dumps(user_config)},
                                status_code=200)
        elif (user_input.startswith("/COMMAND")):
            return JSONResponse(content={"message": "命令結果"},
                                status_code=200)
        else:
            globals.tasks[task_id] = "分析中"
            background_tasks.add_task(general_rep, user_input, user_id, task_id, current_user.username,
                                      conversation_id,
                                      database.SessionLocal())
            return JSONResponse(content={"task_id": task_id, "message": "分析中"},
                                status_code=200)
    else:
        return JSONResponse(content={"message": "無輸入"},
                            status_code=200)


@app.post('/redo/modifycode')
async def modify_code(
        filename: str = Form(...),
        conversation_id: int = Form(...),
        message: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        current_user: models.User = Depends(auth.get_current_user),
):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(do_modify_code, filename,
                              current_user.username, task_id, conversation_id, message, database.SessionLocal())
    return JSONResponse(content={"task_id": task_id, "message": "修改程式中"},
                        status_code=200)


def process_code_task(
        filename: str,
        username: str,
        task_id: str,
        conversation_id: int,
        user_input: str,
        db: Session,
        mode: str
):
    """
    通用代码任务处理函数
    :param filename: 文件名
    :param username: 用户名
    :param task_id: 任务ID
    :param conversation_id: 会话ID
    :param user_input: 用户输入
    :param db: 数据库会话
    :param mode: 任务模式 "modify" 或 "rewrite"
    """
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + username
    desc_file = f"{UPLOAD_DIR}/{filename}_desc.txt"
    code_file = f"{UPLOAD_DIR}/{filename}_code.txt" if mode == "modify" else None
    file_location = f"{UPLOAD_DIR}/{filename}"

    img_desc = read_text_file(desc_file)
    code_base = read_text_file(code_file) if code_file else None

    if code_base is None:
        code_base = ""

    user_config = globals.sys_config[username]
    log("取得CONFIG")
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    log("查詢工程師")

    llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
    llm_code_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_CODE]
    llm_code_prompt_model = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
    llm_code_prompt_messages = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

    messages = []

    globals.tasks[task_id] = f"{mode.capitalize()}程式中"

    json_str = json.dumps(llm_code_prompt_messages)
    modify_json_str = json_str.replace(Constant.LLM_MSG_USER_INPUT, user_input)
    pass_message = json.loads(modify_json_str)
    for prompt_message in pass_message:
        messages.append(prompt_message)

    for idx, description in enumerate([img_desc]):
        messages.append({
            'role': 'user',
            'content': f'圖片{idx + 1}的描述：{description}',
        })

    if mode == "modify":
        messages.append({
            'role': 'user',
            'content': f'請以下面程式為基礎進行修改:{code_base}'
        })

    assistant_reply = generate_program(file_location, llm_code_prompt_model, llm_mode, messages, globals.sys_config,
                                       sys_setting, task_id, username, db)

    globals.tasks[task_id] = assistant_reply

    # 保存对话记录到数据库
    new_message = models.Message(
        conversation_id=conversation_id,
        message=f"{mode.capitalize()}程式:" + filename,
        response=assistant_reply,
    )
    db.add(new_message)
    db.commit()

    globals.tasks[task_id] = "@@END@@處理完畢"


def do_modify_code(
        filename,
        username,
        task_id,
        conversation_id,
        user_input,
        db
):
    process_code_task(filename, username, task_id, conversation_id, user_input, db, mode="modify")


@app.post('/redo/copycode')
async def copy_code(
        filename: str = Form(...),
        conversation_id: int = Form(...),
        message: str = Form(...),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    username = current_user.username
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + current_user.username
    src_file = f"{UPLOAD_DIR}/{filename}_code.txt"
    user_config = globals.sys_config[username]
    idx = int(user_config[Constant.USER_CFG_PROJ_MODE])

    work_path = globals.sys_setting[Constant.SET_WORK_PATH]
    work_mode_path = globals.sys_setting[Constant.SET_WORK_MODE_PATH]
    user_root_path = os.path.join(work_path, work_mode_path[idx], "public", "users", username)

    log(user_root_path)

    prj_id = user_config[Constant.USER_CFG_PROJ_ID]
    app_desc = user_config[Constant.USER_CFG_APP_DESC]
    app_name = user_config[Constant.USER_CFG_APP_NAME]
    func_desc = user_config[Constant.USER_CFG_FUNC_DESC]
    func_file = user_config[Constant.USER_CFG_FUNC_FILE]

    output_folder = f"{user_root_path}/{prj_id}/{app_name}"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_path = f"{output_folder}/{func_file}"

    print("prog path :" + output_path)
    with open(output_path, "w") as out_f:
        shutil.copyfileobj(src_file, out_f)

    # 保存对话记录到数据库
    new_message = models.Message(
        conversation_id=conversation_id,
        message="複製程式碼:" + filename,
        response="複製成功",
    )
    db.add(new_message)
    db.commit()

    return JSONResponse(content={"message": "程式已複製完成"},
                        status_code=200)


@app.post('/redo/rewrite')
async def rewrite_code(
        filename: str = Form(...),
        conversation_id: int = Form(...),
        message: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        current_user: models.User = Depends(auth.get_current_user),
):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(do_rewrite_code, filename,
                              current_user.username, task_id, conversation_id, message, database.SessionLocal())
    return JSONResponse(content={"task_id": task_id, "message": "重新生成程式中"},
                        status_code=200)


def do_rewrite_code(
        filename,
        username,
        task_id,
        conversation_id,
        user_input,
        db
):
    process_code_task(filename, username, task_id, conversation_id, user_input, db, mode="rewrite")


@app.post('/redo/reseeandwrite')
async def re_see_and_write(filename: str = Form(...),
                           conversation_id: int = Form(...),
                           background_tasks: BackgroundTasks = BackgroundTasks(),
                           current_user: models.User = Depends(auth.get_current_user)):
    username = current_user.username
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + username
    file_location = f"{UPLOAD_DIR}/{filename}"

    task_id = str(uuid.uuid4())
    image_b64s = []
    image_types = []

    img_b64 = image_to_base64(file_location)
    image_b64s.append(img_b64)

    _, file_extension = os.path.splitext(filename)
    image_types.append(file_extension[1:])

    background_tasks.add_task(analyze_image, image_b64s, image_types, "", file_location,
                              current_user.username, task_id, conversation_id, database.SessionLocal())
    return JSONResponse(content={"task_id": task_id, "message": "已取得圖片,重新進行分析中"},
                        status_code=200)


@app.post('/message_images')
async def send_message(
        message: str = Form(...),
        conversation_id: int = Form(...),
        images: List[UploadFile] = File(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),

):
    user_id = current_user.id
    user_input = message  # .text

    task_id = str(uuid.uuid4())

    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + current_user.username

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    image_paths = []
    image_b64s = []
    image_types = []

    if len(images) > 5:
        raise HTTPException(status_code=400, detail='最多只能上传5张图片')

    for idx, image in enumerate(images):
        filename = f"{task_id}_{image.filename}"
        file_location = f"{UPLOAD_DIR}/{filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        img_content = await image.read()
        with open(file_location, "wb+") as file_object:
            image.file.seek(0)  # restore point for copy
            shutil.copyfileobj(image.file, file_object)
            try:
                # img_content = await image.read()
                # print("content")
                # print(img_content)
                file_type = image.content_type.split("/")[1]
                print("file_type:" + file_type)
                encode_image = base64.b64encode(img_content).decode('utf-8')
                image_b64s.append(encode_image)
                image_types.append(file_type)
                # print("base64")
                # print(encode_image)

            except Exception as ce:
                print(str(ce))

        # 保存到数据库
        new_image = models.Image(
            user_id=current_user.id,
            image_path=file_location,
            description=user_input,
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        image_paths.append(file_location)

    background_tasks.add_task(analyze_image, image_b64s, image_types, user_input, file_location,
                              current_user.username, task_id, conversation_id, database.SessionLocal())
    return JSONResponse(content={"task_id": task_id, "message": "資料已上傳,進行分析中"},
                        status_code=200)

    # return assistant_reply


def general_rep(user_input, user_id, task_id,
                user_name, conversation_id, db
                ):
    user_config = globals.sys_config[user_name]
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
    llm_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_GENERAL]
    llm_prompt_model = llm_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
    llm_prompt_messages = llm_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

    db.query(models.Message)

    # 获取用户的对话历史，如果没有则初始化
    originalMessage = db.query(models.Message).filter(models.Message.conversation_id == conversation_id).all()

    conversation = []
    if not originalMessage:
        conversation = originalMessage

    if not conversation:
        # conversation.append({
        #    'role': 'system',
        #    'content': '你是一个智能助手，帮助用户回答问题。',
        # })

        conversation.append(llm_prompt_messages[0])

    # conversation.append({"role": "user",
    #                     "content": user_input})

    json_str = json.dumps(llm_prompt_messages)
    modify_json_str = json_str.replace(Constant.LLM_MSG_USER_INPUT, user_input)
    pass_message = json.loads(modify_json_str)
    for i in range(1, len(pass_message)):
        msg = pass_message[i]
        conversation.append(msg)

    # 与 OpenAI GPT 交互
    try:
        assistant_reply = llm.askllm(llm_mode, llm_prompt_model, conversation)
    except Exception as e:
        assistant_reply = '與LLM 交互失败 ::[' + str(e) + ']'

    print(assistant_reply)
    globals.tasks[task_id] = "@@END@@" + assistant_reply
    # 将助手的回复添加到对话历史
    conversation.append({'role': 'assistant', 'content': assistant_reply})

    # 更新用户的对话历史
    # user_conversations[user_id] = conversation

    # 获取用户的对话历史，如果没有则初始化
    originalMessage = db.query(models.Message).filter(models.Message.conversation_id == conversation_id).all()

    # 保存对话记录到数据库
    new_message = models.Message(
        conversation_id=conversation_id,
        message=user_input,
        response=assistant_reply,
    )
    db.add(new_message)
    db.commit()

    # tasks[task_id] = "@@END@@處理完畢"


def analyze_images_from_llm(images_b64: [str], images_type: [str], user_input: str, task_id: str, username: str,
                            file_location: str):
    """与 LLM 模型交互分析图像"""
    image_desc = []
    log("開始分析圖片")

    user_config = globals.sys_config[username]
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
    llm_img_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_IMAGE]
    llm_img_prompt_model = llm_img_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
    llm_img_prompt_messages = llm_img_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

    for idx, encode_image in enumerate(images_b64):
        file_type = images_type[idx]

        try:
            messages = build_image_task_messages(encode_image, file_type, user_input, llm_img_prompt_messages)
            log(f"發送圖像分析需求：{messages}")
            response = llm.askllm(llm_mode, llm_img_prompt_model, messages)
            image_desc.append(response)

            desc_loc = f"{file_location}_desc.txt"
            with open(desc_loc, "w", encoding="UTF-8") as f:
                f.write(response)

        except Exception as imge:
            log(f"圖片分析錯誤：{str(imge)}")
            globals.tasks[task_id] = f"圖片分析錯誤: {str(imge)}"

    return image_desc


def process_code_task_from_analyze(
        filename: str,
        username: str,
        task_id: str,
        conversation_id: int,
        user_input: str,
        db: Session,
        messages: list,
        file_location: str):
    """用于处理从图像分析中生成代码的任务"""
    user_config = globals.sys_config[username]
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
    llm_code_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_CODE]
    llm_code_prompt_model = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]

    # 调用 process_code_task 生成代码
    assistant_reply = generate_program(file_location, llm_code_prompt_model, llm_mode, messages, globals.sys_config,
                                       sys_setting, task_id, username, db)

    globals.tasks[task_id] = assistant_reply

    # 保存对话记录到数据库
    new_message = models.Message(
        conversation_id=conversation_id,
        message=f"圖像分析後生成程式: {user_input}",
        response=assistant_reply,
    )
    db.add(new_message)
    db.commit()

    globals.tasks[task_id] = "@@END@@處理完畢"


def build_code_task_messages(image_desc: list, user_input: str, username: str):
    """构建用于代码生成任务的消息"""
    user_config = globals.sys_config[username]
    log("取得CONFIG")
    # log(user_config)
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    log("查詢工程師")
    # log(employee)
    llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
    llm_code_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_CODE]
    llm_code_prompt_model = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
    llm_code_prompt_messages = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

    messages = []

    json_str = json.dumps(llm_code_prompt_messages)
    modify_json_str = json_str.replace(Constant.LLM_MSG_USER_INPUT, user_input)
    pass_message = json.loads(modify_json_str)
    for prompt_message in pass_message:
        messages.append(prompt_message)

    for idx, description in enumerate(image_desc):
        messages.append({
            'role': 'user',
            'content': f'圖片{idx + 1}的描述：{description}',
        })

    return messages


def analyze_image(images_b64: [str],
                  images_type: [str],
                  user_input,
                  file_location,
                  username,
                  task_id,
                  conversation_id,
                  db
                  ):
    try:
        globals.tasks[task_id] = f"分析圖片中"
        image_desc = analyze_images_from_llm(images_b64, images_type, user_input, task_id, username, file_location)

        globals.tasks[task_id] = "解析完成"
        log(f"圖片分析结果：{image_desc}")

        # 处理代码生成任务
        code_task_messages = build_code_task_messages(image_desc, user_input, username)
        process_code_task_from_analyze(
            filename=None,
            username=username,
            task_id=task_id,
            conversation_id=conversation_id,
            user_input=user_input,
            db=db,
            messages=code_task_messages,
            file_location=file_location
        )

    except Exception as e:
        globals.tasks[task_id] = f"錯誤發生: {str(e)}"
        log(f"图片分析发生错误: {str(e)}")


def generate_program(file_location, llm_code_prompt_model, llm_mode, messages, sys_config, sys_setting, task_id,
                     username, db):
    try:
        globals.tasks[task_id] = "生成程式碼"
        log(globals.tasks[task_id])
        assistant_reply = llm.askllm(llm_mode, llm_code_prompt_model, messages)
        log(assistant_reply)

        user_config = sys_config[username]
        idx = int(user_config[Constant.USER_CFG_PROJ_MODE])

        work_path = globals.sys_setting[Constant.SET_WORK_PATH]
        work_mode_path = globals.sys_setting[Constant.SET_WORK_MODE_PATH]
        user_root_path = os.path.join(work_path, work_mode_path[idx], "public", "users", username)

        log(user_root_path)

        prj_id = user_config[Constant.USER_CFG_PROJ_ID]
        app_desc = user_config[Constant.USER_CFG_APP_DESC]
        app_name = user_config[Constant.USER_CFG_APP_NAME]
        func_desc = user_config[Constant.USER_CFG_FUNC_DESC]
        func_file = user_config[Constant.USER_CFG_FUNC_FILE]

        output_folder = f"{user_root_path}/{prj_id}/{app_name}"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_path = f"{output_folder}/{func_file}"

        print("prog path :" + output_path)

        code_blocks = assistant_reply
        # 3. 分析結果包含程式碼時，進行檔案寫入
        if "```" in assistant_reply:
            print("remove markdown and write")
            code_blocks = extract_code_blocks(assistant_reply)

        with open(output_path, "w") as out_f:
            out_f.writelines(code_blocks)
        code_loc = file_location + "_code.txt"
        with open(code_loc, "w") as out_f:
            out_f.writelines(code_blocks)

        filename = os.path.basename(file_location)
        code_ver = version_service.get_next_image_file_version(db, username, filename)
        func_ver = version_service.get_next_app_function_version(db, username, prj_id, app_name, func_file)

        # write version program
        code_loc_ver = code_loc + f".{code_ver}"
        with open(code_loc_ver, "w") as out_f:
            out_f.writelines(code_blocks)

        output_path_ver = output_path + f".{func_ver}"
        with open(output_path_ver, "w") as out_f:
            out_f.writelines(code_blocks)

        version_service.upsert_image_file_version(db, username, filename, code_ver)
        version_service.upsert_app_function_version(db, username, prj_id, app_name, func_file, func_ver)

        # 更新路由
        print("開始更新路由")
        globals.tasks[task_id] = "更新路由"

        route_path = f"{user_root_path}/{prj_id}/route.json"

        if not os.path.exists(route_path):
            write_json_file(route_path, [])

        route_js = read_json_file(route_path)

        new_route = {Constant.USER_CFG_APP_NAME: app_name, Constant.USER_CFG_APP_DESC: app_desc,
                     Constant.USER_CFG_FUNC_DESC: func_desc, Constant.USER_CFG_FUNC_FILE: f"{func_file}"}
        found = False
        for route_item in route_js:
            if (route_item[Constant.USER_CFG_APP_DESC] == new_route[Constant.USER_CFG_APP_DESC] and
                    route_item[Constant.USER_CFG_FUNC_DESC] == new_route[Constant.USER_CFG_FUNC_DESC]):
                found = True
                route_item[Constant.USER_CFG_FUNC_FILE] = new_route[Constant.USER_CFG_FUNC_FILE]

        if not found:
            route_js.append(new_route)

        write_json_file(route_path, route_js)

        log("結束更新路由")
        # lines = generated_code.splitlines(True)
        # with open(output_path,"w") as out_f:
        #    out_f.writelines(lines[1:-1])

        globals.tasks[task_id] = "完成程式碼寫入"

        log(str(globals.tasks[task_id]))

    except Exception as gee:
        # raise HTTPException(status_code=500, detail='与 OpenAI GPT 交互失败 ['+str(e)+']')
        globals.tasks[task_id] = "生成程式碼失敗-[" + str(gee) + "]"
        log(str(globals.tasks[task_id]))
    return assistant_reply


# 擷取程式碼區塊
def extract_code_blocks(text):
    code_blocks = []
    in_code_block = False
    current_block = []

    for line in text.split('\n'):
        if line.startswith("```"):
            if in_code_block:
                # 結束程式碼區塊
                in_code_block = False
                code_blocks.append('\n'.join(current_block))
                current_block = []
            else:
                # 開始程式碼區塊
                in_code_block = True
        elif in_code_block:
            current_block.append(line)

    return code_blocks


# 5. 查詢工作狀態
@app.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    status = globals.tasks.get(task_id, "Task not found")
    return JSONResponse(content={"task_id": task_id, "status": status}, status_code=200)
