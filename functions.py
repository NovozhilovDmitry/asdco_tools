import os
import time
import sys
import shutil
import pathlib
import subprocess
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


def delete_temp_directory():
    cwd_temp_path = pathlib.Path.cwd().joinpath('temp')
    try:
        shutil.rmtree(cwd_temp_path)
        logger.info('директория temp удалена')
    except FileNotFoundError:
        pass


# получить имена баз данных
def get_string_show_pdbs(sysdba_name, sysdba_password, connection_string):
    script = f"""set feedback off 
set colsep "|"
set pagesize 1000
set linesize 1000
set heading off
column name format a25
set NUMWIDTH 11
set NUMFORMAT 99,999,999,999
select name, creation_time, open_mode, total_size 
from v$pdbs
order by name;
"""
    script_file = create_script_file(script)
    cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string}/ORCL @{script_file}'
    logger.info(f"Подключение к {connection_string} под пользователем {sysdba_name}")
    return cmd


def runnings_sqlplus_scripts_with_subprocess(cmd):  # переписать
    result = subprocess.run(cmd, stdout=subprocess.PIPE).stdout
    return result


def formating_sqlplus_results(result):  # на вход проверить и список и строку
    pdb_name_list = []
    new_list = [i.replace('\t', '').replace('\r', '').replace('\n', '').replace(' ', '').split('|') for i in result if
                i != '']
    for i in new_list:
        pdb_name_list.append(i[0])
    return pdb_name_list


# def check_failure_result_show_pdbs(log_string):
#     log_string = log_string.upper()
#     return log_string.startswith('ORA-0') or log_string.startswith('ORA-1')


def get_string_check_oracle_connection(connection_string, scheme_name, scheme_password, connection_as_sysdba=False):
    script = f"select 'СОЕДИНЕНИЕ ПРОВЕРЕНО УСПЕШНО' as result from dual;"
    script_file = create_script_file(script)
    if connection_as_sysdba:
        cmd = f'echo exit | sqlplus.exe {scheme_name}/{scheme_password}@{connection_string} as sysdba @{script_file}'
    else:
        cmd = f'echo exit | sqlplus.exe {scheme_name}/{scheme_password}@{connection_string} @{script_file}'
    return cmd
