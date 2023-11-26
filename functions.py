import time
import sys
import shutil
import pathlib
import requests
import re
from myLogging import logger


TEMP_DIRECTORY = r'temp'
DATA_PUMP_DIR = r'DATA_PUMP_DIR'


def create_script_file(script):
    """
    :param script: sql скрипт из функций
    :return: создает временный файл с sql запросом
    """
    directory_name = pathlib.Path.cwd().joinpath(TEMP_DIRECTORY)
    file_name = directory_name.joinpath(f'script_{time.time_ns()}.sql')
    try:
        if not pathlib.Path.exists(pathlib.Path.cwd().joinpath(directory_name)):
            pathlib.Path.cwd().joinpath(directory_name).mkdir(parents=True, exist_ok=True)
            logger.info(f'Создана директория {directory_name} для временного размещения скриптов')
        with open(file_name, 'w') as file:
            file.write(script)
        logger.info(f'Создан временный файл скрипта {file_name}')
    except Exception as error:
        logger.error(f'Временный файл скрипта {file_name} не может быть создан по причине {error}!')
        sys.exit(1)
    return file_name


def create_file_for_pdb(filename):
    """
    :filename: имя создаваемого файла
    :return: создать файл, в который будут записаны результаты для PDB
    """
    directory_name = pathlib.Path.cwd().joinpath(TEMP_DIRECTORY)
    file_name = directory_name.joinpath(filename)
    with open(file_name, 'w'):
        pass
    return file_name


def delete_temp_directory():
    """
    :return: при штатном выходе из программы удаляется врменный каталог temp
    """
    cwd_temp_path = pathlib.Path.cwd().joinpath(TEMP_DIRECTORY)
    if pathlib.Path.exists(cwd_temp_path):
        try:
            shutil.rmtree(cwd_temp_path)
            logger.info(f'Директория {TEMP_DIRECTORY} удалена')
        except FileNotFoundError as error:
            logger.error(f'Невозможно удалить директорию {TEMP_DIRECTORY} по причине {error}')


def get_sql_filenames(directory_path):
    """
    :param directory_path: указывается путь, где будет начало поиска файлов
    :return: выводится список файлов в директории, соответствующий формату .sql
    """
    path = pathlib.Path(directory_path).glob('*.sql')
    files = [x.name for x in path if x.is_file()]
    return files


def filter_function(nested_list, regular_expression_pattern):
    """
    :param nested_list: вложенный список, полученный из бд
    :param regular_expression_pattern: регуляорное выражение, по которому идет фильтрация
    :return: отфильтрованный список
    """
    if regular_expression_pattern == '':
        return nested_list
    else:
        exit_list = []
        re_pattern = re.compile(regular_expression_pattern)
        for i in nested_list:
            if re_pattern.search(i[0]):
                exit_list.append(i)
        return exit_list


def get_string_show_pdbs(connection_string, sysdba_name, sysdba_password):
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
select name, to_char(creation_time, 'dd.mm.yyyy') as creation_time, open_mode, total_size
from v$pdbs
where name not in ('ASDCOEMPTY_ETALON', 'PDB$SEED')
order by name;
exit;
    """
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string} @{script_file}'
    logger.info(f'Подключение к {connection_string} под пользователем {sysdba_name}')
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
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string} @{script_file}'
    return cmd


def get_string_make_pdb_writable(connection_string, sysdba_name, sysdba_password, pdb_name):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param pdb_name: имя pdb, у которой убираем режим только для чтения
    :return: база данных переводится из режима только для чтения в режим записи
    """
    script = f"""set echo on;
set serveroutput on size unlimited;
execute pdb.make_read_write('{pdb_name}');
exit;
"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string} @{script_file}'
    return cmd


def get_string_delete_pdb(connection_string, sysdba_name, sysdba_password, pdb_name):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param pdb_name: имя удаляемой pdb
    :return: база данных удалена
    """
    script = f"""set echo on;
set serveroutput on size unlimited;
execute pdb.remove('{pdb_name}');
exit;
"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string} @{script_file}'
    return cmd


def get_string_check_oracle_connection(connection_string, sysdba_name, sysdba_password):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :return: проверяется возможность подключения к pdb
    """
    script = f"""set heading off
select 'CONNECTION SUCCESS' from dual;
exit;"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string} as sysdba @{script_file}'
    return cmd


def get_string_create_oracle_schema(connection_string, sysdba_name, sysdba_password, schema_name, schema_password, pdb_name):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param schema_name: имя новой схемы
    :param schema_password: пароль для схемы
    :param pdb_name: имя pdb, в которой будет создана схема
    :return: создана схема
    """
    script = f"""create user {schema_name} identified by {schema_password} default tablespace USERS temporary tablespace TEMP;
grant CONNECT, RESOURCE, SELECT_ALL to {schema_name};
grant FLASHBACK ANY TABLE,UNLIMITED TABLESPACE, CREATE ANY DIRECTORY, ALTER SESSION, SELECT ANY DICTIONARY to {schema_name};
grant SELECT on V_$SESSION to {schema_name};
grant SELECT on V_$LOCKED_OBJECT to {schema_name};
grant SELECT on V_$SQL to {schema_name};
grant SELECT on GV_$SESSION to {schema_name};
grant SELECT on GV_$TRANSACTION to {schema_name};
grant SELECT on DBA_OBJECTS to {schema_name};
grant SELECT on DBA_HIST_SNAPSHOT to {schema_name};
grant SELECT on DBA_ADVISOR_TASKS to {schema_name};
grant EXECUTE on DBMS_ADVISOR to {schema_name};
grant EXECUTE on CHECKHISTORYINTEGRITY_UPD to {schema_name};
grant EXECUTE on CHECKCOMPLETEHISTINTEGRITY_DEL to {schema_name};
grant EXECUTE on CHECKHISTORYINTEGRITY_DEL to {schema_name};
grant EXECUTE on CHECKHISTORYINTEGRITY_INS to {schema_name};
grant EXECUTE on CHECKCOMPLETEHISTINTEGRITY_INS to {schema_name};
grant EXECUTE on CHECKCOMPLETEHISTINTEGRITY_UPD to {schema_name};
grant EXECUTE on CheckASDCOtoAPOuniqueness to {schema_name};
grant execute on add_DateField to {schema_name};
grant execute on formatPrecision to {schema_name};
grant read, write on directory {DATA_PUMP_DIR} to {schema_name};
exit;"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/{pdb_name} as sysdba @{script_file}'
    return cmd


def get_string_show_oracle_users(connection_string, sysdba_name, sysdba_password, pdb_name):
    """
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param pdb_name: имя pdb, в которой создана схема
    :return: показывает созданные схемы
    """
    script = f"""column USERNAME format A40;
alter session set NLS_DATE_FORMAT = 'YYYY.MM.DD HH24:MI:SS';
set heading off
set linesize 60;
select USERNAME, CREATED from dba_users where COMMON='NO';
exit;
"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/{pdb_name} as sysdba @{script_file}'
    return cmd


def get_string_import_oracle_schema(connection_string, pdb_name, schema_name, schema_password, schema_name_in_dump, schema_dump_file):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param pdb_name: имя pdb, к которой подключаемся для импорта
    :param schema_name: имя схемы
    :param schema_password: пароль от схемы
    :param schema_name_in_dump: имя схемы в дампе
    :param schema_dump_file: путь к дампу
    :return: импорт схем из дампа
    """
    cmd = f"imp.exe {schema_name}/{schema_password}@{connection_string}/{pdb_name} FILE='{schema_dump_file}' FROMUSER={schema_name_in_dump} TOUSER={schema_name} GRANTS=N COMMIT=Y BUFFER=8192000"
    return cmd


def get_string_enabled_oracle_asdco_options(connection_string, pdb_name, schema_name, schema_password):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param pdb_name: имя pdb, к которой подключаемся
    :param schema_name: имя схемы
    :param schema_password: пароль от схемы
    :return: обновление триггеров, функций и процедур
    """
    script = f"""-- включение row movement
begin
for c in (SELECT table_name FROM user_tables WHERE status = 'VALID' AND temporary = 'N' AND dropped = 'NO' AND table_name != '{schema_name}' AND row_movement != 'ENABLED' AND table_name NOT LIKE 'SYS\_%%')
Loop
begin
execute immediate
'ALTER TABLE ' || c.table_name || ' ENABLE ROW MOVEMENT';
end;
end loop;
end;
/
-- установка pctversionbegin
begin
for c in (SELECT table_name, column_name FROM dba_tab_cols WHERE owner = UPPER('{schema_name}') AND data_type LIKE '%LOB' AND table_name = ANY(SELECT table_name FROM all_lobs WHERE owner = UPPER('{schema_name}') AND table_name IN (SELECT object_name FROM dba_objects WHERE owner = UPPER('{schema_name}') AND temporary = 'N' AND object_type = 'TABLE') AND (PCTVERSION < 50 OR PCTVERSION IS NULL)))
Loop
begin
execute immediate
'ALTER TABLE ' || c.table_name || ' MODIFY LOB(' || c.column_name || ') (PCTVERSION 50)';
end;
end loop;
end;
/
-- перекомпиляция view
begin
for c in (SELECT object_name name FROM user_objects WHERE object_type = 'VIEW' AND status='INVALID')
Loop
begin
execute immediate
'ALTER VIEW ' || c.name || ' compile';
end;
end loop;
end;
/
-- перекомпиляция функций и процедур
begin
for c in (SELECT object_type type,object_name name FROM user_objects WHERE object_type in ('FUNCTION','PROCEDURE') AND status = 'INVALID')
Loop
begin
execute immediate
'ALTER ' || c.type || ' ' || c.name || ' compile';
exception when others then null;
end;
end loop;
end;
/
-- перекомпиляция триггеров
begin
for c in (SELECT object_type type, object_name name FROM user_objects WHERE object_type = 'TRIGGER' AND status = 'INVALID')
Loop
begin
execute immediate
'alter ' || c.type || ' ' || c.name || ' compile';
end;
end loop;
end;
/
-- перекомпиляция пакетов
begin
for c in (SELECT object_type type, object_name name from user_objects WHERE object_type IN ('PACKAGE','PACKAGE BODY') AND status='INVALID')
Loop
begin
if (c.type='PACKAGE') then
execute immediate
'ALTER PACKAGE ' || c.name || ' compile PACKAGE';
else
execute immediate
'ALTER PACKAGE ' || c.name || ' compile BODY';
end if;
end;
end loop;
end;
/
exit;
"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {schema_name}/{schema_password}@{connection_string}/{pdb_name} @{script_file}'
    return cmd


def get_string_export_oracle_scheme(connection_string, pdb_name, scheme_name, scheme_password, scheme_dump_file):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param pdb_name: имя pdb, к которой подключаемся для импорта
    :param scheme_name: имя схемы
    :param scheme_password: пароль от схемы
    :param scheme_dump_file: путь, где будет создаваться дамп
    :return: экспорт схемы в дамп
    """
    cmd = f"exp.exe {scheme_name}/{scheme_password}@{connection_string}/{pdb_name} FILE='{scheme_dump_file}' CONSISTENT=Y COMPRESS=N GRANTS=N INDEXES=Y ROWS=Y CONSTRAINTS=Y RECORDLENGTH=8192 BUFFER=8192000 DIRECT=N FULL=N RECORD=N STATISTICS=NONE"
    return cmd


def get_string_delete_oracle_scheme(connection_string, sysdba_name, sysdba_password, pdb_name, schema_name):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param pdb_name: имя pdb, к которой подключаемся
    :param schema_name: имя схемы, которая будет удалена
    :return: удаленная схема
    """
    script = f"""drop user {schema_name} cascade;
exit;"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/{pdb_name} as sysdba @{script_file}'
    return cmd


def get_last_login_to_common_schemas(connection_string, sysdba_name, sysdba_password, pdb_name):
    """
    :param connection_string: строка подключения к базе данных - только ip и порт (сокет)
    :param sysdba_name: логин пользователя SYSDBA
    :param sysdba_password: пароль пользователя SYSDBA
    :param pdb_name: имя pdb, к которой подключаемся
    :return: показывает последний вход пользователей
    """
    script = f"""set heading off
set feedback off
select USERNAME || '; ' || to_char(LAST_LOGIN, 'DD.MM.YYYY HH24:MI:SS') from dba_users where COMMON='NO' and LAST_LOGIN is not null;
exit;"""
    script_file = create_script_file(script)
    cmd = f'sqlplus.exe -s {sysdba_name}/{sysdba_password}@{connection_string}/{pdb_name} as sysdba @{script_file}'
    return cmd


def get_total_space_and_used_space_from_zabbix():
    headers = {'Content-Type': 'application/json'}
    data = requests.post('http://192.168.65.170/api_jsonrpc.php', headers=headers,
                         json={"jsonrpc": "2.0", "method": "history.get",
                               "params": {"history": 3, "hostids": ["11185"], "itemids": ["108285", "108288"],
                                          "output": "extend", "limit": 2, "sortfield": "clock", "sortorder": "DESC"},
                               "auth": "fe57381c8834819d9ca7f99f644c8dc30b3e9ec6956bdb2c57efa9af29127032", "id": 1})
    data_dict = data.json()
    line_for_print = data_dict['result']
    temp_dict = {'used_space': 0, 'total_space': 0}
    for i in line_for_print:
        if i['itemid'] == '108288':
            temp_dict['used_space'] = int(i['value'])
        elif i['itemid'] == '108285':
            temp_dict['total_space'] = int(i['value'])
    return temp_dict


if __name__ == '__main__':
    pass
