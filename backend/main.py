import glob
import json
from datetime import datetime

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

sys_default_config = {}

sys_setting = {
    "ASSISTANT_NAME": "Adam",
    "WORK_PATH": "../../WORK",
    "TEMP_PATH": "../../TEMP",
    "prj01": "http://192.168.1.234:35200",
    "prj02": "http://192.168.1.234:35300",
    "prj03": "http://192.168.1.234:35400",
}
sys_config = {}

sys_employees = {}

tasks: dict[str, str] = {}

# 假设我们有一个会话或数据库来存储对话历史
user_conversations = {}


def log(message):
    # 獲取當前日期和時間
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 如果訊息是字串，直接打印
    if isinstance(message, str):
        print(f"{current_time}\t{message}")
    else:
        # 如果不是字串，使用 repr() 來轉換對象為字串
        print(f"{current_time}")
        print(repr(message))


def read_json_file(file_path):
    try:
        # 打開並讀取 JSON 檔案
        with open(file_path, 'r', encoding='utf-8') as file:
            # 解析 JSON 內容為 Python 字典
            data = json.load(file)

        log(f"成功讀取和載入 {file_path}")
        return data

    except json.JSONDecodeError:
        print(f"Error decoding JSON in file {file_path}")
    except IOError:
        print(f"Error reading file {file_path}")

    return None


def load_setting():
    global sys_setting
    sys_setting = read_json_file(Constant.CONFIG_SETTING_FILE)


def load_default_config():
    global sys_default_config
    sys_default_config = read_json_file(Constant.CONFIG_DEFAULT_CONFIG_FILE)


def load_employees():
    root_dir = Constant.CONFIG_EMPLOYEE_PATH
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    for subdir in subdirs:
        sub_dir_path = os.path.join(root_dir, subdir)
        prompt_file_path = os.path.join(sub_dir_path, Constant.EMPLOYEE_FILE)
        if os.path.exists(prompt_file_path):
            prompt_data = read_json_file(prompt_file_path)
            if prompt_data:
                sys_employees[subdir] = prompt_data
            else:
                log(f'載入 {subdir} Employee 失敗: ')

    log(f"總共載入 {str(len(sys_employees))} AI 員工")


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
)


@app.get("/")
def read_root():
    return {"message": "Hello API Server ! Cross-Domain is enabled"}


@app.get("/info")
def read_info(current_user: models.User = Depends(auth.get_current_user)):
    user_config = sys_config['users'][current_user.username]
    return {"name": ASSISTANT_NAME, "setting": sys_setting, "config": user_config}


@app.get('/employees')
def employees():
    return JSONResponse(content=sys_employees)


@app.get("/employees/{employee_id}")
def get_employee(employee_id: str):
    if employee_id in sys_employees:
        return JSONResponse(content=sys_employees[employee_id])
    return JSONResponse(content={"error": "Employee not found"}, status_code=404)


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
    log(sys_config.keys())
    log('user name :' + user.username)
    if (user.username not in sys_config.keys()):
        sys_config[user.username] = sys_default_config.copy()

    sys_config[user.username][Constant.USER_CFG_EMPLOYEE_KEY] = form_data.employee
    log(sys_config)

    return {'access_token': access_token, 'token_type': 'bearer'}


@app.post("/conversations")
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


@app.get("/conversations", response_model=List[schemas.ConversationResponse])
def get_conversation(current_user: models.User = Depends(auth.get_current_user),
                     db: Session = Depends(database.get_db)):
    user_config = sys_config[current_user.username]
    log(user_config)
    emp_id = user_config[Constant.USER_CFG_EMPLOYEE_KEY]
    log(emp_id)
    employee = sys_employees[emp_id]
    employee_id = employee[Constant.EMP_KEY_EMP_ID]
    conversations = (db.query(models.Conversation).
                     filter(models.Conversation.user_id == current_user.id,
                            models.Conversation.employee_id == employee_id).all())
    return conversations


@app.get("/conversations/{conversion_id}/messages")
def get_conversation_message(conversion_id: int, current_user: models.User = Depends(auth.get_current_user),
                             db: Session = Depends(database.get_db)):
    messages = db.query(models.Message).filter(models.Message.conversation_id == conversion_id).all()
    result = []
    user_config = sys_config[current_user.username]
    employee = sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
    for msg in messages:
        result.append({'sender': 'user', 'text': msg.message, 'name': current_user.username})
        result.append({'sender': 'assistant', 'text': msg.response, 'name': employee[Constant.EMP_KEY_EMP_NAME]})
    return result


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
    user_id = current_user.id
    user_input = message  # .text
    task_id = str(uuid.uuid4())

    if len(user_input) > 0:
        if (user_input.startswith("/SETTING")):
            return JSONResponse(content={"message": json.dumps(sys_setting)},
                                status_code=200)
        elif (user_input.startswith("/CONFIG")):
            user_config = sys_config['users'][current_user.username]
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

            return JSONResponse(content={"message": json.dumps(user_config)},
                                status_code=200)
        elif (user_input.startswith("/COMMAND")):
            return JSONResponse(content={"message": "命令結果"},
                                status_code=200)
        else:
            tasks[task_id] = "分析中"
            background_tasks.add_task(general_rep, user_input, user_id, task_id, current_user.username,
                                      conversation_id,
                                      database.SessionLocal())
            return JSONResponse(content={"task_id": task_id, "message": "分析中"},
                                status_code=200)
    else:
        return JSONResponse(content={"message": "無輸入"},
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

    UPLOAD_DIR = sys_setting['TEMP_PATH'] + "/uploads/" + current_user.username

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

    background_tasks.add_task(analyze_image, image_b64s, image_types, user_input, user_id,
                              current_user.username, task_id, conversation_id, database.SessionLocal())
    return JSONResponse(content={"task_id": task_id, "message": "資料已上傳,進行分析中"},
                        status_code=200)

    # return assistant_reply


def general_rep(user_input, user_id, task_id,
                user_name, conversation_id, db
                ):
    user_config = sys_config[user_name]
    employee = sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
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
    tasks[task_id] = "@@END@@" + assistant_reply
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
                  user_id,
                  username,
                  task_id,
                  conversation_id,
                  db
                  ):
    try:
        tasks[task_id] = f"分析圖片中"
        image_desc = []

        user_config = sys_config[username]
        employee = sys_employees[user_config[Constant.USER_CFG_EMPLOYEE_KEY]]
        llm_mode = employee[Constant.EMP_KEY_LLM_ENGINE]
        llm_img_prompt = employee[Constant.EMP_KEY_LLM_PROMPT][Constant.EMP_KEY_EMP_IMAGE]
        llm_img_prompt_model = llm_img_prompt[Constant.EMP_KEY_LLM_PROMPT_MODEL]
        llm_img_prompt_messages = llm_img_prompt[Constant.EMP_KEY_LLM_PROMPT_MESSAGES]

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

                rep = llm.askllm(llm_mode, llm_img_prompt_model, messages)
                image_desc.append(rep)
            except Exception as imge:
                print(str(imge))
                tasks[task_id] = f"圖片分析錯誤:{str(idx) + ' => ' + str(imge)}"

        tasks[task_id] = "解析完成"

        print(str(tasks[task_id]))

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

        try:
            tasks[task_id] = "生成程式碼"

            print(str(tasks[task_id]))

            assistant_reply = llm.askllm(llm_mode, llm_code_prompt_model, messages)

            print(assistant_reply)

            WORK_PATH = sys_setting['WORK_PATH']

            print(WORK_PATH)

            user_config = sys_config['users'][username]

            print(user_config)

            prj_id = user_config['PROJ_ID']
            print(prj_id)

            app_desc = user_config['APP_DESC']
            app_name = user_config['APP_NAME']
            func_desc = user_config['FUNC_DESC']

            func_file = user_config['FUNC_FILE']
            print(func_file)

            output_folder = f"{WORK_PATH}/{prj_id}/public/{app_name}"
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
            else:
                print("write program")
                with open(output_path, "w") as out_f:
                    out_f.write(assistant_reply)

            # 更新路由
            print("開始更新路由")
            tasks[task_id] = "更新路由"
            route_path = f"{WORK_PATH}/{prj_id}/route.json"
            with open(route_path, "r") as route_f:
                original_route = route_f.read()

            route_js = json.loads(original_route)

            new_route = {"APP_DESC": app_desc, "FUNC_DESC": func_desc, "FUNC_NAME": f"/{app_name}/{func_file}"}
            found = False
            for route_item in route_js:
                if (route_item["APP_DESC"] == new_route["APP_DESC"] and
                        route_item["FUNC_DESC"] == new_route["FUNC_DESC"]):
                    found = True
                    route_item["FUNC_NAME"] = new_route["FUNC_NAME"]

            if not found:
                route_js.append(new_route)

            with open(route_path, "w") as route_f:
                route_f.write(json.dumps(route_js, indent=4))

            print("結束更新路由")
            # lines = generated_code.splitlines(True)
            # with open(output_path,"w") as out_f:
            #    out_f.writelines(lines[1:-1])

            tasks[task_id] = "完成程式碼寫入"

            print(str(tasks[task_id]))

        except Exception as gee:
            # raise HTTPException(status_code=500, detail='与 OpenAI GPT 交互失败 ['+str(e)+']')
            tasks[task_id] = "生成程式碼失敗-[" + str(gee) + "]"
            print(str(tasks[task_id]))

        tasks[task_id] = assistant_reply

        # 将助手的回复添加到对话历史
        # conversation.append({'role': 'assistant', 'content': assistant_reply})

        # 更新用户的对话历史
        # user_conversations[user_id] = conversation

        in_msg = user_input

        if len(image_desc) > 0:
            in_msg = in_msg + "\n" + (image_desc[0])

        # 保存对话记录到数据库
        new_message = models.Message(
            user_id=user_id,
            converation_id=conversation_id,
            message=in_msg,
            response=assistant_reply,
        )
        db.add(new_message)
        db.commit()

        tasks[task_id] = "@@END@@處理完畢"

        print(str(tasks[task_id]))

    except Exception as e:
        tasks[task_id] = f"錯誤發生: {str(e)}"


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
    status = tasks.get(task_id, "Task not found")
    return JSONResponse(content={"task_id": task_id, "status": status}, status_code=200)
