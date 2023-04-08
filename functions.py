import os
import time
import sys
import shutil
import pathlib
import subprocess
from myLogging import logger


TEMP_DIRECTORY = r'temp'  # записать в настройки и дать возможность менять директорию по умолчанию


def create_script_file(script):
    """
    :param script: sql скрипт из функций
    :return: создает временный файл с sql запросом
    """
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
    """
    :return: при выходе из программы удаляется врменный каталог temp
    """
    cwd_temp_path = pathlib.Path.cwd().joinpath('temp')
    try:
        shutil.rmtree(cwd_temp_path)
        logger.info('директория temp удалена')
    except FileNotFoundError:
        pass


def runnings_sqlplus_scripts_with_subprocess(cmd, return_split_result=False):
    """
    функция для запуска sql скриптов с помощью модуля subprocess и метода run
    :param cmd: передается строка подключения и sql скрипт
    :param return_split_result: если true - возвращает дополнительно список разбитый по разделителю конца строки
    :return:
    """
    result = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('1251')
    if return_split_result:
        return result, result.split('\r\n')
    else:
        return result


def get_string_show_pdbs(sysdba_name, sysdba_password, connection_string):
    """
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :return: собирается строка подключения и sql запрос для отправки в subprocess
    """
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
exit;
    """
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/ORCL @{script_file}'
    logger.info(f"Подключение к {connection_string}/ORCL под пользователем {sysdba_name}")
    return cmd


def formating_sqlplus_results_and_return_pdb_names(result):
    """
    :param result: результат, полученный из subprocess
    :return: форматирует аргумент и выводит имена pdb из базы данных
    """
    pdb_name_list = []
    new_list = [i.replace('\t', '').replace('\r', '').replace('\n', '').replace(' ', '').split('|') for i in result if
                i != '']
    for i in new_list:
        pdb_name_list.append(i[0])
    return pdb_name_list


def format_list_result(result):
    """
    :param result: результат, полученный из subprocess
    :return: форматирует аргумент и выводит список списков
    """
    new_list = [i.replace('\t', '').replace('\r', '').replace('\n', '').replace(' ', '').split('|') for i in result if
                i != '']
    return new_list


def get_string_clone_pdb(connection_string, sysdba_name, sysdba_password, pdb_name, pdb_name_cloned):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param pdb_name: имя pdb, с которой клонируемся
    :param pdb_name_cloned: новое имя pdb
    :return: собирается строка подключения и sql запрос для отправки в subprocess
    """
    script = f"""set echo on;
set serveroutput on size unlimited;
execute pdb.clone_pdb('{pdb_name}', '{pdb_name_cloned}');
exit;
"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/ORCL @{script_file}'
    logger.info(f"Клонирование базы данных начато. Имя клонируемой PDB {pdb_name}, имя новой PDB {pdb_name_cloned}")
    return cmd


def get_string_make_pdb_writable(connection_string, sysdba_name, sysdba_password, pdb_name):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param pdb_name: имя pdb, у которой убираем режим только для чтения
    :return:
    """
    script = f"""set echo on;
set serveroutput on size unlimited;
execute pdb.make_read_write('{pdb_name}');
exit;
"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/ORCL @{script_file}'
    logger.info(f"Сделать клонируемую PDB {pdb_name} доступной для записи")
    return cmd


def get_string_delete_pdb(connection_string, sysdba_name, sysdba_password, pdb_name):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param pdb_name: имя удаляемой pdb
    :return:
    """
    script = f"""set echo on;
set serveroutput on size unlimited;
execute pdb.remove('{pdb_name}');
exit;
"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/ORCL @{script_file}'
    logger.info(f"Удаление PDB {pdb_name}")
    return cmd


def get_string_check_oracle_connection(connection_string,
                                       sysdba_name,
                                       sysdba_password):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :return:
    """
    script = f"select 'CONNECTION SUCCESS' as result from dual exit;"
    sql = script.encode()
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/ORCL'
    return cmd, sql


def runnings_check_connect(cmd, sql):
    """
    функция запускает скрипт проверки подключения (и только)
    :param cmd: строка подключения из функции
    :param sql: sql скрипт
    :return:
    """
    result = subprocess.run(cmd, input=sql, stdout=subprocess.PIPE).stdout.decode('1251')
    return result


if __name__ == '__main__':
    pass
