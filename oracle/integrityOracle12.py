import os
import time
from myLogging import logger
from additions import create_script_file, TEMP_DIRECTORY

CHECK_CONNECTION_SUCCESSFULLY_STRING = r'CHECK CONNECTION SUCCESSFULLY'
CHECK_DROP_USER_SUCCESSFULLY_STRING_RUS = r'ПОЛЬЗОВАТЕЛЬ УДАЛЕН.'
CHECK_DROP_USER_SUCCESSFULLY_STRING_ENG = r'USER DROPPED.'
CHECK_CREATE_USER_SUCCESSFULLY_STRING_RUS = r'ПОЛЬЗОВАТЕЛЬ СОЗДАН.'
CHECK_CREATE_USER_SUCCESSFULLY_STRING_ENG = r'USER CREATED.'
CHECK_CRANT_PRIVILEGE_SUCCESSFULLY_STRING_RUS = r'Привилегии предоставлены.'
CHECK_CRANT_PRIVILEGE_SUCCESSFULLY_STRING_ENG = r'GRANT SUCCEEDED.'

CHECK_ORACLE_ERROR_0 = r'ORA-0'
CHECK_ORACLE_ERROR_1 = r'ORA-1'
DATA_PUMP_DIR = r'DATA_PUMP_DIR'


def get_string_check_oracle_connection(connection_string, scheme_name, scheme_password, connection_as_sysdba=False):
    """
        sqlplus credit/credit@localhost/ASDCO.localdomain
        select 'CHECK_CONNECTION_SUCCESSFULLY_STRING' as result from dual;
    """
    script = f"select '{CHECK_CONNECTION_SUCCESSFULLY_STRING}' as result from dual;"
    logger.info(f"script={script}")
    script_file = create_script_file(script)
    if connection_as_sysdba:
        cmd = f'echo exit | sqlplus.exe {scheme_name}/{scheme_password}@{connection_string} as sysdba @{script_file}'
        cmd_mask_password = f'sqlplus.exe {scheme_name}/********@{connection_string} as sysdba @{script_file}'
    else:
        cmd = f'echo exit | sqlplus.exe {scheme_name}/{scheme_password}@{connection_string} @{script_file}'
        cmd_mask_password = f'sqlplus.exe {scheme_name}/********@{connection_string} @{script_file}'
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_success_result_check_oracle_connection(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_CONNECTION_SUCCESSFULLY_STRING)


def get_string_import_oracle_scheme(connection_string, scheme_name, scheme_password, scheme_name_in_dump, scheme_dump_file):
    """
        imp deposit/deposit@localhost:1521/ASDCO.localdomain FILE='.\dmp\88350_deposit.dmp'
            FROMUSER=deposit TOUSER=deposit GRANTS=N COMMIT=Y BUFFER=8192000 STATISTICS=RECALCULATE
            LOG='.\log\imp_deposit.log'
    """
    log_file_with_full_path = os.path.join(os.getcwd(), TEMP_DIRECTORY, f"import_{scheme_name}_{time.time_ns()}.log")
    cmd = f"imp.exe {scheme_name}/{scheme_password}@{connection_string} FILE='{scheme_dump_file}' FROMUSER={scheme_name_in_dump} TOUSER={scheme_name} GRANTS=N COMMIT=Y BUFFER=8192000 STATISTICS=RECALCULATE LOG='{log_file_with_full_path}'"
    cmd_mask_password = f"imp.exe {scheme_name}/********@{connection_string} FILE='{scheme_dump_file}' FROMUSER={scheme_name_in_dump} TOUSER={scheme_name} GRANTS=N COMMIT=Y BUFFER=8192000 STATISTICS=RECALCULATE LOG='{log_file_with_full_path}'"
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_result_import_oracle_scheme(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


def get_string_export_oracle_scheme(connection_string, scheme_name, scheme_password, scheme_dump_file):
    """
        exp deposit/deposit@localhost:1521/ASDCO.localdomain FILE='.\dmp\88350_deposit.dmp'
            CONSISTENT=Y COMPRESS=N GRANTS=N INDEXES=Y ROWS=Y CONSTRAINTS=Y RECORDLENGTH=8192 BUFFER=8192000
            DIRECT=N FULL=N RECORD=N STATISTICS=NONE LOG='.\log\imp_deposit.log'
    """
    log_file_with_full_path = os.path.join(os.getcwd(), TEMP_DIRECTORY, f"export_{scheme_name}_{time.time_ns()}.log")
    cmd = f"exp.exe {scheme_name}/{scheme_password}@{connection_string} FILE='{scheme_dump_file}' CONSISTENT=Y COMPRESS=N GRANTS=N INDEXES=Y ROWS=Y CONSTRAINTS=Y RECORDLENGTH=8192 BUFFER=8192000 DIRECT=N FULL=N RECORD=N STATISTICS=NONE LOG='{log_file_with_full_path}'"
    cmd_mask_password = f"exp.exe {scheme_name}/********@{connection_string} FILE='{scheme_dump_file}' CONSISTENT=Y COMPRESS=N GRANTS=N INDEXES=Y ROWS=Y CONSTRAINTS=Y RECORDLENGTH=8192 BUFFER=8192000 DIRECT=N FULL=N RECORD=N STATISTICS=NONE LOG='{log_file_with_full_path}'"
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_result_export_oracle_scheme(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


def get_string_impdp_oracle_scheme(connection_string, sysdba_name, sysdba_password, scheme_name, scheme_dump_file):
    """
       impdp c##devop/123devop@localhost/ASDCO.localdomain SCHEMAS=credit directory=DATA_PUMP_DIR dumpfile=1111.dmp logfile=importdmp.log
    """
    log_file = f"import_{scheme_name}_{time.time_ns()}.log"
    cmd = f"impdp {sysdba_name}/{sysdba_password}@{connection_string} SCHEMAS={scheme_name} directory={DATA_PUMP_DIR} dumpfile={scheme_dump_file} logfile={log_file}"
    cmd_mask_password = f"impdp {sysdba_name}/********@{connection_string} SCHEMAS={scheme_name} directory={DATA_PUMP_DIR} dumpfile={scheme_dump_file} logfile={log_file}"
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_result_impdp_oracle_scheme(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


def get_string_expdp_oracle_scheme(connection_string, sysdba_name, sysdba_password, scheme_name, scheme_dump_file):
    """
        expdp c##devop/123devop@localhost/ASDCO.localdomain SCHEMAS=credit directory=DATA_PUMP_DIR dumpfile=1111.dmp logfile=exportdmp3.log reuse_dumpfiles=Y
    """
    log_file = f"export_{scheme_name}_{time.time_ns()}.log"
    cmd = f"expdp {sysdba_name}/{sysdba_password}@{connection_string} SCHEMAS={scheme_name} directory={DATA_PUMP_DIR} dumpfile={scheme_dump_file} logfile={log_file} reuse_dumpfiles=Y"
    cmd_mask_password = f"expdp {sysdba_name}/********@{connection_string} SCHEMAS={scheme_name} directory={DATA_PUMP_DIR} dumpfile={scheme_dump_file} logfile={log_file} reuse_dumpfiles=Y"
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_result_expdp_oracle_scheme(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


# удаление схемы
def get_string_delete_oracle_scheme(sysdba_name, sysdba_password, connection_string, scheme_name):
    """
        sqlplus c##devop/123devop@localhost/ASDCO.localdomain as sysdba
        drop user credit cascade;
    """
    script = f"drop user {scheme_name} cascade;"
    logger.info(f"script={script}")  # запись в лог
    script_file = create_script_file(script)  # создание sql файла
    cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string} as sysdba @{script_file}'
    cmd_mask_password = f'sqlplus.exe {sysdba_name}/********@{connection_string} as sysdba @{script_file}'
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_success_result_delete_oracle_scheme(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_DROP_USER_SUCCESSFULLY_STRING_ENG) or log_string.startswith(
        CHECK_DROP_USER_SUCCESSFULLY_STRING_RUS)


def get_string_create_oracle_scheme(sysdba_name, sysdba_password, connection_string, scheme_name, scheme_password):
    """
        sqlplus c##devop/123devop@localhost/ASDCO.localdomain as sysdba
        create user {scheme_name} identified by {scheme_password} default tablespace USERS temporary tablespace TEMP;
    """
    script = f"create user {scheme_name} identified by {scheme_password} default tablespace USERS temporary tablespace TEMP;"
    logger.info(f"script={script}")
    script_file = create_script_file(script)
    cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string} as sysdba @{script_file}'
    cmd_mask_password = f'sqlplus.exe {sysdba_name}/********@{connection_string} as sysdba @{script_file}'
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_success_result_create_oracle_scheme(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_CREATE_USER_SUCCESSFULLY_STRING_ENG) or log_string.startswith(
        CHECK_CREATE_USER_SUCCESSFULLY_STRING_RUS)


def get_string_grant_oracle_privilege(sysdba_name, sysdba_password, connection_string, scheme_name):
    """
        sqlplus c##devop/123devop@localhost/ASDCO.localdomain as sysdba
        grant CONNECT, RESOURCE, SELECT_ALL to {scheme_name};
        ...
        grant read,write on directory DATA_PUMP_DIR to {scheme_name};
    """
    script = f"""grant CONNECT, RESOURCE, SELECT_ALL to {scheme_name};
grant DBA to {scheme_name};
grant FLASHBACK ANY TABLE,UNLIMITED TABLESPACE, CREATE ANY DIRECTORY, ALTER SESSION, SELECT ANY DICTIONARY to {scheme_name};
grant SELECT on V_$SESSION to {scheme_name};
grant SELECT on V_$LOCKED_OBJECT to {scheme_name};
grant SELECT on V_$SQL to {scheme_name};
grant SELECT on GV_$SESSION to {scheme_name};
grant SELECT on GV_$TRANSACTION to {scheme_name};
grant SELECT on DBA_OBJECTS to {scheme_name};
grant SELECT on DBA_HIST_SNAPSHOT to {scheme_name};
grant SELECT on DBA_ADVISOR_TASKS to {scheme_name};
grant EXECUTE on DBMS_ADVISOR to {scheme_name};
grant EXECUTE on CHECKHISTORYINTEGRITY_UPD to {scheme_name};
grant EXECUTE on CHECKCOMPLETEHISTINTEGRITY_DEL to {scheme_name};
grant EXECUTE on CHECKHISTORYINTEGRITY_DEL to {scheme_name};
grant EXECUTE on CHECKHISTORYINTEGRITY_INS to {scheme_name};
grant EXECUTE on CHECKCOMPLETEHISTINTEGRITY_INS to {scheme_name};
grant EXECUTE on CHECKCOMPLETEHISTINTEGRITY_UPD to {scheme_name};
grant EXECUTE on CheckASDCOtoAPOuniqueness to {scheme_name};
grant execute on add_DateField to {scheme_name};
grant execute on formatPrecision to {scheme_name};
grant read,write on directory {DATA_PUMP_DIR} to {scheme_name};
"""
    logger.info(f"script={script}")
    script_file = create_script_file(script)
    cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string} as sysdba @{script_file}'
    cmd_mask_password = f'sqlplus.exe {sysdba_name}/********@{connection_string} as sysdba @{script_file}'
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_result_grant_oracle_privilege(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


def get_string_show_oracle_users(sysdba_name, sysdba_password, connection_string):
    """
        sqlplus credit/credit@localhost/ASDCO.localdomain
        alter session set NLS_DATE_FORMAT = 'YYYY.MM.DD HH24:MI:SS';
        column USERNAME format A40;
        set linesize 60;
        select USERNAME, CREATED from dba_users where COMMON='NO';
    """
    script = f"""column USERNAME format A40;
alter session set NLS_DATE_FORMAT = 'YYYY.MM.DD HH24:MI:SS';
set linesize 60;
select USERNAME, CREATED from dba_users where COMMON='NO';
"""
    logger.info(f"script={script}")
    script_file = create_script_file(script)
    cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string} @{script_file}'
    cmd_mask_password = f'sqlplus.exe {sysdba_name}/********@{connection_string} @{script_file}'
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_result_show_oracle_users(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


def get_string_enabled_oracle_asdco_options(connection_string, scheme_name, scheme_password):
    script = f"""-- включение row movement
begin
for c in (SELECT table_name FROM user_tables WHERE status = 'VALID' AND temporary = 'N' AND dropped = 'NO' AND table_name != '{scheme_name}' AND row_movement != 'ENABLED' AND table_name NOT LIKE 'SYS\_%%')
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
for c in (SELECT table_name, column_name FROM dba_tab_cols WHERE owner = UPPER('{scheme_name}') AND data_type LIKE '%LOB' AND table_name = ANY(SELECT table_name FROM all_lobs WHERE owner = UPPER('{scheme_name}') AND table_name IN (SELECT object_name FROM dba_objects WHERE owner = UPPER('{scheme_name}') AND temporary = 'N' AND object_type = 'TABLE') AND (PCTVERSION < 50 OR PCTVERSION IS NULL)))
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
"""
    logger.info(f"script={script}")
    script_file = create_script_file(script)
    cmd = f'echo exit | sqlplus.exe {scheme_name}/{scheme_password}@{connection_string} @{script_file}'
    cmd_mask_password = f'sqlplus.exe {scheme_name}/********@{connection_string} @{script_file}'
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_enabled_oracle_asdco_options(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


def get_string_create_data_pump_dir(sysdba_name, sysdba_password, connection_string, system_data_pump_dir):
    """
        sqlplus c##devop/123devop@ORCL as sysdba
        create or replace directory DATA_PUMP_DIR '/u01/app/oracle/admin/orcl/dpdump/asdco';
        GRANT read, write ON DIRECTORY DATA_PUMP_DIR TO c##devop;
    """
    script = f"""create or replace directory {DATA_PUMP_DIR} as '{system_data_pump_dir}';
GRANT read, write ON DIRECTORY {DATA_PUMP_DIR} TO {sysdba_name};
"""
    logger.info(f"script={script}")
    script_file = create_script_file(script)
    cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string} as sysdba @{script_file}'
    cmd_mask_password = f'sqlplus.exe {sysdba_name}/********@{connection_string} as sysdba @{script_file}'
    logger.info(f"cmd={cmd_mask_password}")
    return cmd, cmd_mask_password


def check_failure_result_create_data_pump_dir(log_string):
    log_string = log_string.upper()
    return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


# Показать базы данных
# def get_string_show_pdbs(sysdba_name, sysdba_password, connection_string):
#     """
#         sqlplus c##devop/123devop@ORCL
#         ...
#         select name, GUID, open_mode, total_size from v$pdbs;
#     """
#     script = f"""column name format a30;
# column total_size format 99999999999999999999999999.99;
# set linesize 1000;
# select name, GUID, open_mode, total_size from v$pdbs;
# """
#     script_file = create_script_file(script)
#     cmd = f'echo exit | sqlplus.exe {sysdba_name}/{sysdba_password}@{connection_string} @{script_file}'
#     logger.info(f"Подключение к {connection_string} под пользователем {sysdba_name}")
#     return cmd


# def check_failure_result_show_pdbs(log_string):
#     log_string = log_string.upper()
#     return log_string.startswith(CHECK_ORACLE_ERROR_0) or log_string.startswith(CHECK_ORACLE_ERROR_1)


# if __name__ == '__main__':
#     connection_string = r"localhost/ASDCO.localdomain"
#     scheme_name = scheme_password = r'credit'
#     print(get_string_check_oracle_connection(connection_string, scheme_name, scheme_password))
