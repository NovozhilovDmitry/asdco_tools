def add_exit_to_script(sql_text_script):
    if str(sql_text_script).endswith(';'):
        new_sql_script = sql_text_script + '\n exit;'
    else:
        new_sql_script = sql_text_script + ';\n exit;'
    return new_sql_script


def convert_from_utf8_to_cp1251(sql_text_scripts):
    sql_encode = sql_text_scripts.encode('cp1251')
    sql_decode = sql_encode.decode('cp1251')
    return sql_decode


sql_add_curs_to_next_day = "insert into exchangerates (idcurrency, i_scale, d_exchangedate, f_rate, nv_pr_ecu) select idcurrency, i_scale, d_exchangedate+1, f_rate+0.0001, nv_pr_ecu from exchangerates where d_exchangedate=(select MAX(d_exchangedate) from exchangerates); commit;"
remove_schedule_for_users = "update quantity_hist set NV_VALUE='Нет' where NV_NAME='scheduleUserOnRole'; commit;"
reset_password_to_one = "update users set nv_password=21207185601386731906 where enabled=1; commit;"
off_archive_bd = "delete from PvvsoperationOnDocType where idOperation = 40; commit;"
off_crypto = "update systemparameter set nv_parametervalue='false' where idsystemparameter in(50089, 1, 11); commit;"
remove_changepass_date = "update users set d_changepassdate=to_date('30.12.9999','dd.mm.yyyy') where enabled=1; commit;"
watch_max_curs = """set linesize 1000
set feedback off
select * from exchangerates where d_exchangedate in (select MAX(d_exchangedate) from exchangerates);"""
set_password_unlimited = "alter profile default limit password_life_time unlimited;"
nsi_db_link = """CREATE OR REPLACE PACKAGE nci_create_package
AUTHID CURRENT_USER
is
    PROCEDURE recreateUser         (l_userName  in NVARCHAR2,l_password   in NVARCHAR2);
    PROCEDURE createTable          (l_tableName in NVARCHAR2,l_textSql    in NVARCHAR2);
    PROCEDURE createGrantSelect    (l_cxemaNSIinEXD  in NVARCHAR2,l_tableName  in NVARCHAR2,l_cxemaTUZinEXD in nvarchar2); 
end;
/

CREATE OR REPLACE PACKAGE BODY nci_create_package
is
    PROCEDURE recreateUser(l_userName in NVARCHAR2, l_password in NVARCHAR2)
    is
    l_sql varchar2(100);
    begin
          BEGIN
                 l_sql:='DROP USER ' || l_userName || ' cascade';
                 EXECUTE IMMEDIATE l_sql;
                DBMS_OUTPUT.PUT_LINE('Deleted schema ' || l_userName );
          EXCEPTION
          WHEN OTHERS
          THEN
             DBMS_OUTPUT.PUT_LINE('Schema ' || l_userName || ' is not delete: ' );
             DBMS_OUTPUT.PUT_LINE(dbms_utility.format_error_stack||dbms_utility.format_error_backtrace);
          END;
          
          l_sql:='CREATE USER ' || l_userName || ' IDENTIFIED BY '|| l_password;
          EXECUTE IMMEDIATE l_sql;
          DBMS_OUTPUT.PUT_LINE('Created schema ' || l_userName );
          l_sql:='GRANT resource      TO  '|| l_userName;
          EXECUTE IMMEDIATE l_sql;
          l_sql:='GRANT connect       TO  '|| l_userName;
          EXECUTE IMMEDIATE l_sql;
          l_sql:='GRANT alter session TO '|| l_userName;
          EXECUTE IMMEDIATE l_sql;
           l_sql:='GRANT create database link TO '|| l_userName;
          EXECUTE IMMEDIATE l_sql;
    end recreateUser;
   
    PROCEDURE createTable(l_tableName in NVARCHAR2, l_textSql in NVARCHAR2)
    is
    l_sql varchar2(500);
    begin
          l_sql:=l_textSql;
          EXECUTE IMMEDIATE l_sql;
          DBMS_OUTPUT.PUT_LINE('Created table ' || l_tableName);
    end createTable;
    
    PROCEDURE createGrantSelect(l_cxemaNSIinEXD in NVARCHAR2,l_tableName in NVARCHAR2,l_cxemaTUZinEXD in nvarchar2)
    is
     l_sql varchar2(500);
    begin
          l_sql:='grant select on ' || l_cxemaNSIinEXD || '.' || l_tableName || ' to ' || l_cxemaTUZinEXD;
          EXECUTE IMMEDIATE l_sql;
          DBMS_OUTPUT.PUT_LINE('Grant select on ' || l_cxemaNSIinEXD || '.' || l_tableName || ' to ' || l_cxemaTUZinEXD );
    end createGrantSelect; 
end;
/

set serverout on
declare
l_url nvarchar2(40):='192.168.65.136:1521/EHD';
l_cxemaTUZinASDCO nvarchar2(30):='asdco_ehd_dbl_prom';
l_TUZinASDCOPass nvarchar2(30):='asdco_ehd_dbl_prom';
l_cxemaTUZinEXD nvarchar2(30):='prom_ehd_tuz';
l_TUZinEXDPass nvarchar2(30):='prom_ehd_tuz';
l_dblinkName nvarchar2(30):='NEW_LINK_FROM_ASDCO_TO_EHD';
l_strDblink varchar2(500);

procedure createDBlink(l_dblinkName in varchar2, l_strDblink in varchar2)
is
l_s varchar2(200);
str_current_user varchar2(100);
begin
   begin
        l_s:='drop public database link ' || l_dblinkName;
         execute immediate l_s;
    EXCEPTION
          WHEN OTHERS
          THEN
                    null; 
   end;             
   DBMS_OUTPUT.PUT_LINE(l_strDblink); 
   execute immediate l_strDblink;
   DBMS_OUTPUT.PUT_LINE('Создан dblink');
end;

begin
     -- Создание ТУЗов
     nci_create_package.recreateUser(l_cxemaTUZinASDCO,l_TUZinASDCOPass);
     l_strDblink:='create public database link ' || l_dblinkName || ' connect to ' || l_cxemaTUZinEXD || ' identified by ' || l_TUZinEXDPass || ' using ''' || l_url || '''';     
     createDBlink(l_dblinkName,l_strDblink);
     commit work;
end;
/
drop package nci_create_package;"""
nsi_systemparameter = "update systemparameter set NV_PARAMETERVALUE='USER=asdco_ehd_dbl_prom; PASSWORD=asdco_ehd_dbl_prom; URL=jdbc:oracle:thin:@{CONNECTION_WITH_PDB}; DBLINK_NAME2=NEW_LINK_FROM_ASDCO_TO_EHD;  SIT_DM_RCO_OUT=ZPE_DM_RCO_OUT' where IDSYSTEMPARAMETER = 81500; \n" \
                      "update quantity_hist set nv_value = 'ПРОМ' where getoperdate between d_from and d_to and idquantity = 160;\n commit;"


sql_dict = {
    'Просмотр максимального курса валют': add_exit_to_script(watch_max_curs),
    'Убрать требования к сроку паролей для схем': add_exit_to_script(set_password_unlimited),
    'Добавить DBLink для подключения к EHD': add_exit_to_script(nsi_db_link),
    'Сброс паролей всех активных пользователей на 1': add_exit_to_script(reset_password_to_one),
    'Отключение криптозащиты': add_exit_to_script(off_crypto),
    'Продление периода действия всех активных пользователей': add_exit_to_script(remove_changepass_date),
    'Копирование курсов валют': add_exit_to_script(sql_add_curs_to_next_day),
    'Отключение работы с архивной БД': add_exit_to_script(off_archive_bd),
}

cyrillic_sql_dict = {
    'Установить подключение в настройках': convert_from_utf8_to_cp1251(add_exit_to_script(nsi_systemparameter)),
    'Убрать график смен': convert_from_utf8_to_cp1251(add_exit_to_script(remove_schedule_for_users))
}


def get_sql_dict():
    merged_dictionary = {**sql_dict, **cyrillic_sql_dict}
    return merged_dictionary


if __name__ == '__main__':
    pass
