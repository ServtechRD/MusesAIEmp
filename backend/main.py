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
    db_user = auth.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail='用户名已被注册')
    hashed_password = utils.get_password_hash(user.password)
    new_user = models.User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = auth.create_access_token(data={'sub': new_user.username})
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail='用户名或密码错误')
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


def do_modify_code(
        filename,
        username,
        task_id,
        conversation_id,
        user_input,
        db
):
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + username
    desc_file = f"{UPLOAD_DIR}/{filename}_desc.txt"
    code_file = f"{UPLOAD_DIR}/{filename}_code.txt"
    file_location = f"{UPLOAD_DIR}/{filename}"

    img_desc = read_text_file(desc_file)
    code_base = read_text_file(code_file)

    if code_base is None:
        code_base = ""

    user_config = globals.sys_config[username]
    log("取得CONFIG")
    # log(user_config)
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    log("查詢工程師")
    # log(employee)
    llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
    log("查詢模型")

    llm_code_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_CODE]
    llm_code_prompt_model = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
    llm_code_prompt_messages = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

    messages = []

    globals.tasks[task_id] = f"修改程式中"

    json_str = json.dumps(llm_code_prompt_messages)
    modify_json_str = json_str.replace(Constant.LLM_MSG_USER_INPUT, user_input)
    pass_message = json.loads(modify_json_str)
    for prompt_message in pass_message:
        messages.append(prompt_message)

    for idx, description in enumerate([img_desc]):
        messages.append({
            'role': 'user',
            'content': f'图片{idx + 1}的描述：{description}',
        })

    messages.append({
        'role': 'user',
        'content': f'請以下面程式為基礎進行修改:{code_base}'
    })

    assistant_reply = generate_program(file_location, llm_code_prompt_model, llm_mode, messages, globals.sys_config,
                                       sys_setting, task_id, username)

    globals.tasks[task_id] = assistant_reply

    # 保存对话记录到数据库
    new_message = models.Message(
        conversation_id=conversation_id,
        message="修改程式:" + filename,
        response=assistant_reply,
    )
    db.add(new_message)
    db.commit()

    globals.tasks[task_id] = "@@END@@處理完畢"


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
    UPLOAD_DIR = globals.sys_setting['TEMP_PATH'] + "/uploads/" + username
    desc_file = f"{UPLOAD_DIR}/{filename}_desc.txt"
    file_location = f"{UPLOAD_DIR}/{filename}"

    img_desc = read_text_file(desc_file)

    user_config = globals.sys_config[username]
    log("取得CONFIG")
    # log(user_config)
    employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    log("查詢工程師")
    # log(employee)
    llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
    log("查詢模型")

    llm_code_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_CODE]
    llm_code_prompt_model = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
    llm_code_prompt_messages = llm_code_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

    messages = []

    globals.tasks[task_id] = f"重新生成程式中"

    json_str = json.dumps(llm_code_prompt_messages)
    modify_json_str = json_str.replace(Constant.LLM_MSG_USER_INPUT, user_input)
    pass_message = json.loads(modify_json_str)
    for prompt_message in pass_message:
        messages.append(prompt_message)

    for idx, description in enumerate([img_desc]):
        messages.append({
            'role': 'user',
            'content': f'图片{idx + 1}的描述：{description}',
        })

    assistant_reply = generate_program(file_location, llm_code_prompt_model, llm_mode, messages, globals.sys_config,
                                       sys_setting, task_id, username)

    globals.tasks[task_id] = assistant_reply

    # 保存对话记录到数据库
    new_message = models.Message(
        conversation_id=conversation_id,
        message="重新寫一次程式:" + filename,
        response=assistant_reply,
    )
    db.add(new_message)
    db.commit()

    globals.tasks[task_id] = "@@END@@處理完畢"


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


def analyze_image(images_b64: [str],
                  images_type: [str],
                  user_input,
                  file_location,
                  username,
                  task_id,
                  conversation_id,
                  db
                  ):
    # global sys_setting, sys_employees, sys_config
    try:
        globals.tasks[task_id] = f"分析圖片中"
        image_desc = []

        log("開始分析圖片中")
        # log(sys_config)
        user_config = globals.sys_config[username]
        log("取得CONFIG")
        # log(user_config)
        employee = globals.sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
        log("查詢工程師")
        # log(employee)
        llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
        log("查詢模型")
        # log(llm_mode)
        llm_img_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_LLM_PROMPT_IMAGE]
        llm_img_prompt_model = llm_img_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
        llm_img_prompt_messages = llm_img_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

        log("開始看圖")
        for idx, encode_image in enumerate(images_b64):
            file_type = images_type[idx]
            try:

                messages = []

                json_str = json.dumps(llm_img_prompt_messages)
                modify_json_str = json_str.replace(Constant.LLM_MSG_USER_INPUT, user_input)
                modify_json_str = modify_json_str.replace(Constant.LLM_MSG_FILE_TYPE, file_type)
                modify_json_str = modify_json_str.replace(Constant.LLM_MSG_ENCODE_IMAGE, encode_image)
                pass_message = json.loads(modify_json_str)

                for prompt_message in pass_message:
                    messages.append(prompt_message)

                log("詢問訊息:")
                # log(messages)
                rep = llm.askllm(llm_mode, llm_img_prompt_model, messages)
                image_desc.append(rep)

                desc_loc = file_location + "_desc.txt"
                with open(desc_loc, "w", encoding="UTF-8") as f:
                    f.write(rep)

            except Exception as imge:
                print(str(imge))
                globals.tasks[task_id] = f"圖片分析錯誤:{str(idx) + ' => ' + str(imge)}"

        globals.tasks[task_id] = "解析完成"

        print(str(globals.tasks[task_id]))

        # 获取用户的对话历史，如果没有则初始化
        # conversation = user_conversations.get(user_id, [])

        # 获取用户的对话历史，如果没有则初始化
        originalMessage = db.query(models.Message).filter(models.Message.conversation_id == conversation_id).all()

        conversation = []
        if not originalMessage:
            conversation = originalMessage

        # 添加用户的消息到对话历史
        # conversation.append({'role': 'user', 'content': user_input})

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
                'content': f'图片{idx + 1}的描述：{description}',
            })

        assistant_reply = generate_program(file_location, llm_code_prompt_model, llm_mode, messages, globals.sys_config,
                                           sys_setting, task_id, username)

        globals.tasks[task_id] = assistant_reply

        # 将助手的回复添加到对话历史
        # conversation.append({'role': 'assistant', 'content': assistant_reply})

        # 更新用户的对话历史
        # user_conversations[user_id] = conversation

        in_msg = user_input

        if len(image_desc) > 0:
            in_msg = in_msg + "\n" + (image_desc[0])

        # 保存对话记录到数据库
        new_message = models.Message(
            conversation_id=conversation_id,
            message=in_msg,
            response=assistant_reply,
        )
        db.add(new_message)
        db.commit()

        globals.tasks[task_id] = "@@END@@處理完畢"

        print(str(globals.tasks[task_id]))

    except Exception as e:
        globals.tasks[task_id] = f"錯誤發生: {str(e)}"


def generate_program(file_location, llm_code_prompt_model, llm_mode, messages, sys_config, sys_setting, task_id,
                     username):
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

        # 3. 分析結果包含程式碼時，進行檔案寫入
        if "```" in assistant_reply:
            print("remove markdown and write")
            code_blocks = extract_code_blocks(assistant_reply)
            with open(output_path, "w") as out_f:
                out_f.writelines(code_blocks)
            code_loc = file_location + "_code.txt"
            with open(code_loc, "w") as out_f:
                out_f.writelines(code_blocks)

        else:
            print("write program")
            with open(output_path, "w") as out_f:
                out_f.write(assistant_reply)
            code_loc = file_location + "_code.txt"
            with open(code_loc, "w") as out_f:
                out_f.writelines(assistant_reply)

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
