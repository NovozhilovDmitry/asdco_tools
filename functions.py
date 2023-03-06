import os
import time
import sys
from myLogging import logger


TEMP_DIRECTORY = r'temp'  # записать в настройки и дать возможность менять директорию по умолчанию


# создание файла sql-скрипта
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


# получить имена баз данных
def get_string_show_pdbs(sysdba_name, sysdba_password, connection_string):
    """
        sqlplus c##devop/123devop@ORCL
        ...
        select name, GUID, open_mode, total_size from v$pdbs;
    """
    script = f"""column name format a30;
column total_size format 99999999999999999999999999.99;
set linesize 1000;
select name, GUID, open_mode, total_size from v$pdbs;
"""  # выпилить GUID и добавить дату + изменить оформление запроса
    script_file = create_script_file(script)
    cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string} @{script_file}'
    logger.info(f"Подключение к {connection_string} под пользователем {sysdba_name}")
    return cmd


def check_failure_result_show_pdbs(log_string):
    log_string = log_string.upper()
    return log_string.startswith('ORA-0') or log_string.startswith('ORA-1')