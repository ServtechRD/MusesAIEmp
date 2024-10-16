import json

from constant import Constant
import globals

def build_code_task_messages(image_desc: list, user_input: str):
    """构建用于代码生成任务的消息"""
    messages = []
    for idx, description in enumerate(image_desc):
        messages.append({
            'role': 'user',
            'content': f'圖片{idx + 1}的描述：{description}',
        })

    return messages

def build_image_task_messages(encode_image: str, file_type: str, user_input: str, llm_img_prompt_messages: list):
    """构建用于图像任务的 LLM 消息"""
    messages = []
    json_str = json.dumps(llm_img_prompt_messages)
    modify_json_str = json_str.replace(Constant.LLM_MSG_USER_INPUT, user_input)
    modify_json_str = modify_json_str.replace(Constant.LLM_MSG_FILE_TYPE, file_type)
    modify_json_str = modify_json_str.replace(Constant.LLM_MSG_ENCODE_IMAGE, encode_image)
    pass_message = json.loads(modify_json_str)

    for prompt_message in pass_message:
        messages.append(prompt_message)

    return messages