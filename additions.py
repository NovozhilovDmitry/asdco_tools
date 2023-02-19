import os
import sys
import json
import subprocess
import time
from myLogging import logger

VERSION = '1.3.3'
MAIN_WINDOW_TITLE = 'AsdcoTools'
AUTHOR = r'РЦР Екатеринбург'
TEMP_DIRECTORY = r'temp'
RELEASE_NOTES_FILENAME = 'README.md'


# Чтение конфигурации из файла
def load_config(file_json):
    try:
        if os.path.isfile(file_json):
            logger.info(f'Load config file={file_json}')
            with open(file_json, 'r') as file:
                config = json.load(file)
            logger.info(f'Load configuration from file={file_json} successfully.')
            return config
    except Exception as error:
        logger.error(f'{file_json} contain wrong format: {error}!')
        sys.exit(1)


# Запись конфигурации в файл
def dump_config(config, file_json):
    try:
        with open(file_json, 'w') as file:
            json.dump(config, file, sort_keys=True, indent=4)
        logger.info(f'Save configuration to file={file_json} successfully.')
    except Exception as error:
        logger.error(f'{file_json} contain wrong format: {error}!')
        sys.exit(1)


# Возвращает имя файла с проверкой, т.е. если он существует
def get_real_file_name(file_name, enabled=1):
    return file_name if not enabled or os.path.isfile(file_name) else ''


# Создание временного файла sql-скрипта для выполнения команд sqlplus
def create_script_file(script):
    directory_name = os.path.join(os.getcwd(), TEMP_DIRECTORY)
    file_name = os.path.join(os.getcwd(), TEMP_DIRECTORY, f"script_{time.time_ns()}.sql")
    try:
        if not os.path.isdir(directory_name):
            os.makedirs(directory_name)
            logger.info(f'Create temporary directory={directory_name}.')
        with open(file_name, 'w') as file:
            file.write(script)
        logger.info(f'Create temporary file={file_name}.')
    except Exception as error:
        logger.error(f'Cannot create temporary file={file_name} {error}!')
        sys.exit(1)
    return file_name


# Проверка и создание внешнего каталога для монтирования внутреннего каталога
# файловой системы докер-контейнера
def check_external_volume(external_volume_directory):
    try:
        if not os.path.isdir(external_volume_directory):
            os.makedirs(external_volume_directory)
            logger.info(f'Create external_volume_directory={external_volume_directory}.')
    except Exception as error:
        logger.error(f'Cannot create external_volume_directory={external_volume_directory} {error}!')
        return False
    return True


# Удаление временного файла sql-скрипта
def delete_script_file(file_name):
    try:
        if os.path.isfile(file_name):
            os.remove(file_name)
            logger.info(f'Delete temporary file={file_name}.')
        else:
            logger.info(f'Cannot delete temporary file={file_name} not exists.')
    except Exception as error:
        logger.error(f'Cannot delete temporary file={file_name} {error}!')
    return True


# Чтение конфигурации из файла
def load_release_notes():
    text = f"{MAIN_WINDOW_TITLE} {VERSION}\n{AUTHOR}\n\n"
    try:
        if os.path.isfile(RELEASE_NOTES_FILENAME):
            logger.info(f'Load release notes file={RELEASE_NOTES_FILENAME}')
            with open(RELEASE_NOTES_FILENAME, 'r', encoding='utf-8') as file:
                text = text + file.read().encode('utf-8', errors='replace').decode('utf-8')
            logger.info(f'Load release notes file={RELEASE_NOTES_FILENAME} successfully.')
        return text
    except Exception as error:
        logger.error(f'Error in load_release_notes(): {error}!')
        sys.exit(1)


# Запуск команды в отдельном процессе
def run_cmd(cmd, cmd_mask_password="", script="", encoding='windows-1251', shell=True):
    if cmd_mask_password:
        logger.info(f"cmd={cmd_mask_password}")
    else:
        logger.info(f"cmd={cmd}")
    if script:
        logger.info(f"script={script}")
    process = subprocess.Popen(cmd,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               encoding=encoding,
                               shell=shell)
    if script:
        stdout, stderr = process.communicate(input=script)
    else:
        stdout, stderr = process.communicate()
    if stdout:
        logger.info(f'stdout={stdout}')
    if stderr:
        logger.info(f'stderr={stderr}')
    return process.returncode, stdout, stderr


if __name__ == '__main__':
    pass
