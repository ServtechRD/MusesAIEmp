import base64
import json
import os
from datetime import datetime
from http.client import HTTPException
from io import BytesIO

from PIL import Image

import globals
from constant import Constant

from utils import log



def write_json_file(file_path, json_obj):
    try:
        with open(file_path, "w", encoding='utf-8') as file:
            file.write(json.dumps(json_obj, indent=4))
    except IOError:
        print(f"Error reading file {file}")


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
    globals.sys_setting = read_json_file(Constant.CONFIG_SETTING_FILE)


def load_default_config():
    globals.sys_default_config = read_json_file(Constant.CONFIG_DEFAULT_CONFIG_FILE)


def load_employees():
    root_dir = Constant.CONFIG_EMPLOYEE_PATH
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    for subdir in subdirs:
        sub_dir_path = os.path.join(root_dir, subdir)
        prompt_file_path = os.path.join(sub_dir_path, Constant.EMPLOYEE_FILE)
        if os.path.exists(prompt_file_path):
            prompt_data = read_json_file(prompt_file_path)
            if prompt_data:
                globals.sys_employees[subdir] = prompt_data
            else:
                log(f'載入 {subdir} Employee 失敗: ')

    log(f"總共載入 {str(len(globals.sys_employees))} AI 員工")


def read_projects_by_user(prj_mode, user_name):
    work_path = globals.sys_setting[Constant.SET_WORK_PATH]
    work_mode_path = globals.sys_setting[Constant.SET_WORK_MODE_PATH]
    user_root_path = os.path.join(work_path, work_mode_path[prj_mode], "public", "users",
                                  user_name)
    # update proj route json
    all_prjs = {}
    prj_route_json = os.path.join(user_root_path, "route.json")

    log(f"user_root_path :{user_root_path}")
    log(f"prj_route_path :{prj_route_json}")

    if os.path.exists(prj_route_json):
        all_prjs = read_json_file(prj_route_json)
    return all_prjs, prj_route_json, user_root_path


def image_to_base64(file_location: str) -> str:
    """
    从文件路径读取影像，并将其转为 base64 字符串
    """
    try:
        with open(file_location, "rb") as image_file:
            # 读取二进制数据
            image_data = image_file.read()
            # 将二进制数据编码为 Base64
            base64_encoded_data = base64.b64encode(image_data).decode('utf-8')
            return base64_encoded_data
    except FileNotFoundError:
        raise Exception(f"File {file_location} not found")

# 生成 Base64 编码的图片数据
def get_image_base64(image_path):
    try:
        with Image.open(image_path) as img:
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


# 读取文本文件的内容
def read_text_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found or error reading file: {str(e)}")



# 获取目录下所有图片文件的名字
def get_image_files(directory):
    return [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]


# 生成缩略图并返回 Base64 编码
def generate_thumbnail_base64(image_path, size=(100, 100)):
    with Image.open(image_path) as img:
        img.thumbnail(size)
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        # 将图像内容编码为 Base64
        thumbnail_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return thumbnail_base64

