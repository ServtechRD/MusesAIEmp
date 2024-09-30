import json

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
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

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)

# 获取环境变量
SECRET_KEY = os.getenv('SECRET_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_NAME = os.getenv('ASSISTANT_NAME', 'ASSISTANT')

client = OpenAI(api_key=OPENAI_API_KEY)

print("KEY:" + SECRET_KEY)
print("OPENAI KEY:" + OPENAI_API_KEY)

# 数据
data = {"sub": "user_id"}

setting = {
    "ASSISTANT_NAME": "Adam",
    "WORK_PATH": "../../WORK",
    "TEMP_PATH": "../../TEMP",
    "prj01": "http://192.168.1.234:35200",
    "prj02": "http://192.168.1.234:35300",
    "prj03": "http://192.168.1.234:35400",
}

config = {
    "users": {
        "aa": {
            "PROJ_ID": "prj01",
            "PROJ_DESC": "測試專案",
            "APP_DESC": "報表",
            "APP_NAME": "01_Report",
            "FUNC_DESC": "查詢子報表",
            "FUNC_FILE": "query1.html",
            "PROJ_MODE": 1,
        }
    }
}

tasks: dict[str, str] = {}

# 生成 JWT
try:
    token = jwt.encode(data, SECRET_KEY, algorithm="HS256")
    print(f"Generated token: {token}")
except JWTError as e:
    print(f"Error encoding token: {e}")

# 解码 JWT
try:
    decoded_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print(f"Decoded data: {decoded_data}")
except JWTError as e:
    print(f"Error decoding token: {e}")

# 假设我们有一个会话或数据库来存储对话历史
user_conversations = {}


@app.get("/")
def read_root():
    return {"message": "Hello API Server ! Cross-Domain is enabled"}


@app.get("/info")
def read_info(current_user: models.User = Depends(auth.get_current_user)):
    user_config = config['users'][current_user.username]
    return {"name": ASSISTANT_NAME, "setting": setting, "config": user_config}


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
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.post('/upload')
async def upload_images(
        images: List[UploadFile] = File(...),
        descriptions: List[str] = Form(None),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    if len(images) > 5:
        raise HTTPException(status_code=400, detail='最多只能上传5张图片')

    image_paths = []
    image_desc = []
    for idx, image in enumerate(images):
        filename = f"{uuid.uuid4()}_{image.filename}"
        file_location = f"uploads/{filename}"
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
                # print("base64")
                # print(encode_image)
                response = client.chat.completions.create(
                    # files=[file_object],
                    messages=[
                        {"role": "system", "content": "You are an image analyst."},
                        {"role": "user",
                         "content":
                             [
                                 {"type": "text", "text": "Please analyze this image, include content, color and size"},
                                 {"type": "image_url",
                                  "image_url": {"url": f"data:image/{file_type};base64,{encode_image}"}},
                             ]
                         },
                    ],
                    model="gpt-4o")
                print(response.choices[0].message.content)
                image_desc.append(response.choices[0].message.content)
            except Exception as ce:
                print(str(ce))
                image_desc.append("NOTHING " + str(ce))

        # 保存到数据库
        new_image = models.Image(
            user_id=current_user.id,
            image_path=file_location,
            description=descriptions[idx] if descriptions else '',
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        image_paths.append(file_location)

    # 与 OpenAI GPT 交互

    messages = [
        {
            'role': 'system',
            'content': '你是一个擅長web畫面生成代码的助手。',
        },
    ]

    for idx, description in enumerate(image_desc):
        messages.append({
            'role': 'user',
            'content': f'图片{idx + 1}的描述：{description}',
        })

    messages.append({'role': 'user', 'content': 'write only program,no any description or explain, no markdown tag'})
    messages.append({'role': 'user', 'content': descriptions[0]})

    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=messages,
        )
        generated_code = response.choices[0].message.content.strip()

        output_path = f"../prj01/public/index.html"
        lines = generated_code.splitlines(True)
        with open(output_path, "w") as out_f:
            out_f.writelines(lines[1:-1])


    except Exception as e:
        raise HTTPException(status_code=500, detail='与 OpenAI GPT 交互失败 [' + str(e) + ']')

    # 返回生成的代码
    return {'code': generated_code}


@app.post('/message')
async def send_message(
        message: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),

):
    user_id = current_user.id
    user_input = message  # .text
    task_id = str(uuid.uuid4())

    if len(user_input) > 0:
        if (user_input.startswith("/SETTING")):
            return JSONResponse(content={"message": json.dumps(setting)},
                                status_code=200)
        elif (user_input.startswith("/CONFIG")):
            user_config = config['users'][current_user.username]
            input_items = user_input.split()
            print("parser items :"+str(len(input_items)))
            if (len(input_items) > 1):
                if (input_items[1].upper() == "SET"):
                    if (len(input_items) > 3):
                        config_key = input_items[2]
                        config_value = input_items[3]
                        user_config[config_key] = config_value


            return JSONResponse(content={"message": json.dumps(user_config)},
                                status_code=200)
        elif (user_input.startswith("/COMMAND")):
            return JSONResponse(content={"message": "命令結果"},
                                status_code=200)
        else:
            tasks[task_id] = "分析中"
            background_tasks.add_task(general_rep, user_input, user_id, task_id, current_user.username)
            return JSONResponse(content={"task_id": task_id, "message": "分析中"},
                                status_code=200)
    else:
        return JSONResponse(content={"message": "無輸入"},
                            status_code=200)


@app.post('/message_images')
async def send_message(
        message: str = Form(...),
        images: List[UploadFile] = File(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),

):
    user_id = current_user.id
    user_input = message  # .text

    task_id = str(uuid.uuid4())

    UPLOAD_DIR = setting['TEMP_PATH'] + "/uploads/" + current_user.username

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
                              current_user.username, task_id)
    return JSONResponse(content={"task_id": task_id, "message": "資料已上傳,進行分析中"},
                        status_code=200)

    # return assistant_reply


def general_rep(user_input, user_id, task_id,
                user_name
                ):
    # 获取用户的对话历史，如果没有则初始化
    conversation = user_conversations.get(user_id, [])
    if not conversation:
        conversation.append({
            'role': 'system',
            'content': '你是一个智能助手，帮助用户回答问题。',
        })

    conversation.append({"role": "user",
                         "content": user_input})

    # 与 OpenAI GPT 交互
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=conversation,
        )
        assistant_reply = response.choices[0].message.content.strip()
    except Exception as e:
        assistant_reply = '与 OpenAI GPT 交互失败 ::[' + str(e) + ']'

    print(assistant_reply)
    tasks[task_id] = "@@END@@" + assistant_reply
    # 将助手的回复添加到对话历史
    conversation.append({'role': 'assistant', 'content': assistant_reply})

    # 更新用户的对话历史
    user_conversations[user_id] = conversation

    # 保存对话记录到数据库
    # new_message = models.Conversation(
    #    user_id=user_id,
    #    message=user_input,
    #    response=assistant_reply,
    # )
    # db.add(new_message)
    # db.commit()

    # tasks[task_id] = "@@END@@處理完畢"


def analyze_image(images_b64: [str],
                  images_type: [str],
                  user_input,
                  user_id,
                  username,
                  task_id,

                  db: Session = Depends(database.get_db)
                  ):
    try:
        tasks[task_id] = f"分析圖片中"
        image_desc = []
        for idx, encode_image in enumerate(images_b64):
            file_type = images_type[idx]
            try:
                response = client.chat.completions.create(
                    # files=[file_object],
                    messages=[
                        {"role": "system", "content": "You are an image analyst."},
                        {"role": "user",
                         "content":
                             [
                                 {"type": "text", "text": "Please analyze this image, include content, color and size"},
                                 {"type": "text", "text": user_input},
                                 {"type": "image_url",
                                  "image_url": {"url": f"data:image/{file_type};base64,{encode_image}"}},
                             ]
                         },
                    ],
                    model="gpt-4o")
                print(response.choices[0].message.content)
                image_desc.append(response.choices[0].message.content)
            except Exception as imge:
                print(str(imge))
                tasks[task_id] = f"圖片分析錯誤:{str(idx) + ' => ' + str(imge)}"

        tasks[task_id] = "解析完成"

        print(str(tasks[task_id]))

        # 获取用户的对话历史，如果没有则初始化
        conversation = user_conversations.get(user_id, [])
        # 添加用户的消息到对话历史
        conversation.append({'role': 'user', 'content': user_input})

        messages = [
            {
                'role': 'system',
                'content': '你是一個資深的前端工程師, 擅長javascript , css, html , 可以根據畫面描述, 撰寫Web前端程式。',
            },
        ]

        for idx, description in enumerate(image_desc):
            messages.append({
                'role': 'user',
                'content': f'图片{idx + 1}的描述：{description}',
            })

        messages.append(
            {'role': 'user', 'content': 'write only program,no any description or explain, no markdown tag , output full html code embedd css and javascript'})
      #  messages.append({'role': 'user', 'content': user_input})

        try:
            tasks[task_id] = "生成程式碼"

            print(str(tasks[task_id]))

            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=messages,
            )

            print(response)

            assistant_reply = response.choices[0].message.content.strip()

            print(assistant_reply)

            WORK_PATH = setting['WORK_PATH']

            print(WORK_PATH)

            user_config = config['users'][username]

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
        conversation.append({'role': 'assistant', 'content': assistant_reply})

        # 更新用户的对话历史
        user_conversations[user_id] = conversation

        # 保存对话记录到数据库
        # new_message = models.Conversation(
        #    user_id=current_user.id,
        #    message=user_input,
        #    response=assistant_reply,
        # )
        # db.add(new_message)
        # db.commit()

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


@app.post('/upload_code')
async def upload_code_file(
        code_file: UploadFile = File(...),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db),
):
    # 验证文件类型
    allowed_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.txt']
    filename, file_extension = os.path.splitext(code_file.filename)
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail='不支持的文件类型')

    # 读取文件内容
    file_content = await code_file.read()
    code_text = file_content.decode('utf-8')

    # 准备与 OpenAI GPT 的对话
    messages = [
        {
            'role': 'system',
            'content': '你是一个经验丰富的程序员，帮助用户分析和改进代码。',
        },
        {
            'role': 'user',
            'content': f'请分析以下代码并提出修改建议，提供修改后的代码：\n\n{code_text}',
        },
    ]

    try:
        response = client.chat.completions.create(model='gpt-3.5-turbo',
                                                  messages=messages)
        modified_code = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail='与 OpenAI GPT 交互失败')

    # 返回修改后的代码
    return {'modified_code': modified_code}
