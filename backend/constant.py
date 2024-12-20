import os


class Constant:
    CONFIG_PATH = "./config"
    CONFIG_SETTING_FILE = CONFIG_PATH + "/setting.json"
    CONFIG_DEFAULT_CONFIG_FILE = CONFIG_PATH + "/default.json"
    CONFIG_EMPLOYEE_PATH = CONFIG_PATH + "/employees"
    EMPLOYEE_FILE = "prompt.json"

    SET_WORK_PATH = "WORK_PATH"
    SET_WORK_MODE_PATH = "WORK_MODE_PATH"
    SET_WORK_MODE_URL = "WORK_MODE_URL"

    SET_VERSION_IMAGE_COUNT = "IMAGE_CODE_VERSION_COUNT"
    SET_VERSION_FUNC_COUNT = "APP_CODE_VERSION_COUNT"

    USER_CFG_PROJ_ID = "PROJ_ID"
    USER_CFG_PROJ_DESC = "PROJ_DESC"
    USER_CFG_APP_DESC = "APP_DESC"
    USER_CFG_APP_NAME = "APP_NAME"
    USER_CFG_FUNC_DESC = "FUNC_DESC"
    USER_CFG_FUNC_FILE = "FUNC_FILE"
    USER_CFG_PROJ_MODE = "PROJ_MODE"
    USER_CFG_EMPLOYEE_KEY = "EMP_ID"

    EMP_KEY_EMP_ID = "EMP_ID"
    EMP_KEY_EMP_NAME = "EMP_NAME"
    EMP_KEY_EMP_IMAGE = "EMP_IMAGE"
    EMP_KEY_EMP_SKILL = "EMP_SKILL"
    EMP_KEY_EMP_DESC = "EMP_DESC"
    EMP_KEY_EMP_HELLO = "EMP_HELLO"
    EMP_KEY_EMP_HELP = "EMP_HELP"
    EMP_KEY_WORK_MODE = "WORK_MODE"
    EMP_KEY_LLM_ENGINE = "LLM_ENGINE"
    EMP_KEY_LLM_PROMPT = "LLM_PROMPT"

    EMP_KEY_LLM_PROMPT_GENERAL = "GENERAL"
    EMP_KEY_LLM_PROMPT_IMAGE = "IMAGE"
    EMP_KEY_LLM_PROMPT_CODE = "CODE"

    EMP_KEY_LLM_PROMPT_MODEL = "MODEL"
    EMP_KEY_LLM_PROMPT_MESSAGES = "MESSAGES"

    LLM_MSG_USER_INPUT = "%USER_INPUT%"
    LLM_MSG_FILE_TYPE = "%FILE_TYPE%"
    LLM_MSG_ENCODE_IMAGE = "%ENCODE_IMAGE%"
