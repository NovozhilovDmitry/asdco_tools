from tkinter import *
from tkinter import messagebox
import asyncio
import os
import sys
import argparse

from myLogging import logger
# from docker.Docker import Docker
# from docker.DockerVolumeChoice import DockerVolumeChoice

from oracle.OracleDelete import OracleDelete
from oracle.OracleCreate import OracleCreate
from oracle.OracleImport import OracleImport
from oracle.OracleExport import OracleExport
from oracle.OracleImpdp import OracleImpdp
from oracle.OracleExpdp import OracleExpdp
from oracle.OracleRemoteManagePDB import OracleRemoteManagePDB
from oracle.OracleRemoteDeletePDB import OracleRemoteDeletePDB
from oracle.OracleRemoteExpdp import OracleRemoteExpdp
from oracle.OracleRemoteImpdp import OracleRemoteImpdp
from StartWindow import WindowMain
# from asdco.AsdcoCreateRelease import AsdcoCreateRelease
from asdco.AsdcoSettings import AsdcoSettings
from myhelp.ShowReleaseNotes import ShowReleaseNotes
from additions import load_config, dump_config

# Optimal refresh loop interval (in seconds)
INTERVAL = 0.1

CONFIG_DIR = r'settings'
config_file_menu = os.path.join(os.getcwd(), CONFIG_DIR, r'menu.json')
config_file_oracle_local = os.path.join(os.getcwd(), CONFIG_DIR, r'oracle_local.json')
config_file_oracle_remote = os.path.join(os.getcwd(), CONFIG_DIR, r'oracle_remote.json')
config_file_docker = os.path.join(os.getcwd(), CONFIG_DIR, r'docker.json')
config_file_asdco = os.path.join(os.getcwd(), CONFIG_DIR, r'asdco.json')


# Парсер для аргументов командной строки
def parser_command_line_arguments():
    parser = argparse.ArgumentParser(description='AsdcoTools')
    parser.add_argument('--reset-admin-password',
                        dest='reset_admin_password',
                        default=False,
                        action='store_true',
                        help='Reset all admins passwords in files config'
                        )
    return parser


# def choice_menu_docker_volume(config_file):
#     logger.info('choice_menu_docker_volume')
#     child = Toplevel(master=None)
#     window = DockerVolumeChoice(child, loop, config_file)


# def choice_menu_docker(config_file):
#     logger.info('choice_menu_docker')
#     child = Toplevel(master=None)
#     window = Docker(child, loop, config_file)


def choice_menu_delete_schemes(config_file):
    logger.info('choice_menu_delete_schemes')
    child = Toplevel(master=None)
    window = OracleDelete(child, loop, config_file)


def choice_menu_create_schemes(config_file):
    logger.info('choice_menu_delete_schemes')
    child = Toplevel(master=None)
    window = OracleCreate(child, loop, config_file)


def choice_menu_import_schemes(config_file):
    logger.info('choice_menu_import_schemes')
    child = Toplevel(master=None)
    window = OracleImport(child, loop, config_file)


def choice_menu_export_schemes(config_file):
    logger.info('choice_menu_export_schemes')
    child = Toplevel(master=None)
    window = OracleExport(child, loop, config_file)


def choice_menu_import_data_pump_schemes(config_file):
    logger.info('choice_menu_import_data_pump_schemes')
    child = Toplevel(master=None)
    window = OracleImpdp(child, loop, config_file)


def choice_menu_export_data_pump_schemes(config_file):
    logger.info('choice_menu_export_data_pump_schemes')
    child = Toplevel(master=None)
    window = OracleExpdp(child, loop, config_file)


def choice_menu_manage_pdb(config_file):
    logger.info('choice_menu_manage_pdbs')
    child = Toplevel(master=None)
    window = OracleRemoteManagePDB(child, loop, config_file)


def choice_menu_delete_pdb(config_file):
    logger.info('choice_menu_delete_pdb')
    child = Toplevel(master=None)
    window = OracleRemoteDeletePDB(child, loop, config_file)


def choice_menu_remote_export_data_pump_schemes(config_file):
    logger.info('choice_menu_remote_export_data_pump_schemes')
    child = Toplevel(master=None)
    window = OracleRemoteExpdp(child, loop, config_file)


def choice_menu_remote_import_data_pump_schemes(config_file):
    logger.info('choice_menu_remote_import_data_pump_schemes')
    child = Toplevel(master=None)
    window = OracleRemoteImpdp(child, loop, config_file)


def choice_menu_asdco_set_configuration(config_file):
    logger.info('choice_menu_asdco_set_configuration')
    child = Toplevel(master=None)
    window = AsdcoSettings(child, loop, config_file)


# def choice_menu_asdco_create_release(config_file):
#     logger.info('choice_menu_asdco_create_release')
#     child = Toplevel(master=None)
#     window = AsdcoCreateRelease(child, loop, config_file)


def choice_menu_about_program():
    logger.info('choice_menu_about_program')
    child = Toplevel(master=None)
    window = ShowReleaseNotes(child, loop)


def create_menu(root):
    config_menu = load_config(config_file_menu)
    main_menu = Menu(root)
    root.config(menu=main_menu)
    # docker_menu = Menu(main_menu, tearoff=0)
    # docker_menu.add_command(label='Импорт data volume', command=lambda: choice_menu_docker_volume(config_file_docker))
    # docker_menu.add_separator()
    # docker_menu.add_command(label='Запуск/остановка контейнера', command=lambda: choice_menu_docker(config_file_docker))

    oracle_menu = Menu(main_menu, tearoff=0)
    oracle_menu.add_command(label='Создание схем', command=lambda: choice_menu_create_schemes(config_file_oracle_local))
    oracle_menu.add_command(label='Удаление схем', command=lambda: choice_menu_delete_schemes(config_file_oracle_local))
    oracle_menu.add_separator()
    oracle_menu.add_command(label='Импорт схем', command=lambda: choice_menu_import_schemes(config_file_oracle_local))
    oracle_menu.add_command(label='Экспорт схем', command=lambda: choice_menu_export_schemes(config_file_oracle_local))
    oracle_menu.add_separator()
    oracle_menu.add_command(label='Импорт схем (data pump)', command=lambda: choice_menu_import_data_pump_schemes(config_file_oracle_local))
    oracle_menu.add_command(label='Экспорт схем (data pump)', command=lambda: choice_menu_export_data_pump_schemes(config_file_oracle_local))

    oracle_remote_menu = Menu(main_menu, tearoff=0)
    oracle_remote_menu.add_command(label='Управление PDB', command=lambda: choice_menu_manage_pdb(config_file_oracle_remote))
    oracle_remote_menu.add_separator()
    oracle_remote_menu.add_command(label='Создание схем', command=lambda: choice_menu_create_schemes(config_file_oracle_remote))
    oracle_remote_menu.add_command(label='Удаление схем', command=lambda: choice_menu_delete_schemes(config_file_oracle_remote))
    oracle_remote_menu.add_separator()
    oracle_remote_menu.add_command(label='Импорт схем', command=lambda: choice_menu_import_schemes(config_file_oracle_remote))
    oracle_remote_menu.add_command(label='Экспорт схем', command=lambda: choice_menu_export_schemes(config_file_oracle_remote))

    oracle_remote_menu.add_separator()
    oracle_remote_menu.add_command(label='Импорт схем (data pump)', command=lambda: choice_menu_remote_import_data_pump_schemes(config_file_oracle_remote))
    oracle_remote_menu.add_command(label='Экспорт схем (data pump)', command=lambda: choice_menu_remote_export_data_pump_schemes(config_file_oracle_remote))
    oracle_remote_menu.add_separator()
    oracle_remote_menu.add_command(label='Удаление PDB', command=lambda: choice_menu_delete_pdb(config_file_oracle_remote))

    asdco_menu = Menu(main_menu, tearoff=0)
    asdco_menu.add_command(label='Настройка конфигурации', command=lambda: choice_menu_asdco_set_configuration(config_file_asdco))
    asdco_menu.add_separator()
    # asdco_menu.add_command(label='Сборка релиза', command=lambda: choice_menu_asdco_create_release(config_file_asdco))
    asdco_menu.add_separator()
    asdco_menu.add_command(label='Выполнить тестирование', state=DISABLED)
    asdco_menu.add_command(label='Отправить в Пром', state=DISABLED)

    if config_menu['oracle_menu']:
        main_menu.add_cascade(label='Oracle (docker)', menu=oracle_menu)
    if config_menu['oracle_remote_menu']:
        main_menu.add_cascade(label='Oracle (remote)', menu=oracle_remote_menu)
    # if config_menu['docker_menu']:
    #     main_menu.add_cascade(label='Docker Desktop', menu=docker_menu)
    if config_menu['asdco_menu']:
        main_menu.add_cascade(label='АС ДКО', menu=asdco_menu)
    main_menu.add_command(label='Help', command=choice_menu_about_program)
    main_menu.add_command(label='Выход', command=lambda: close_window(root))
    return main_menu


async def tkinter_update(root, loop, interval=INTERVAL):
    logger.info(f'Start of async tkinter_update({interval})')
    logger.info('Start the loop.')
    try:
        while True:
            root.update()
            await asyncio.sleep(interval)
    except TclError as error:
        if "application has been destroyed" not in error.args[0]:
            raise
    except asyncio.CancelledError as error:
        logger.info(f'tkinter_update({interval}) Request to cancel tkinter_update_task received but may not be done. {error}')
        await asyncio.sleep(interval)
    loop.stop()
    logger.info("Stop the loop.")
    logger.info(f'End of async tkinter_update({interval})')


def close_window(root):
    if messagebox.askokcancel(title='Выход', message='Закрыть программу?'):
        for task in asyncio.Task.all_tasks():
            logger.info(f'Canceling task={task}')
            task.cancel()
        logger.info("All tasks cancelling done.")
        root.destroy()


def reset_admin_password():
    for config_file in [config_file_oracle_local, config_file_oracle_remote]:
        temp = load_config(config_file)
        if "sysdba_name_string" in temp:
            temp["sysdba_name_string"] = ""
        if "sysdba_password_string" in temp:
            temp["sysdba_password_string"] = ""
        if "connection_cdb_string" in temp:
            temp["connection_cdb_string"] = ""
        dump_config(temp, config_file)


if __name__ == '__main__':
    logger.info(f'Start {__file__}')

    try:
        parser = parser_command_line_arguments()
        namespace = parser.parse_args()
        RESET_ADMIN_PASSWORD = namespace.reset_admin_password
    except TypeError:
        logger.error('Command line arguments are not specified correctly!')
        sys.exit(1)
    if RESET_ADMIN_PASSWORD:
        reset_admin_password()
        logger.info('Reset all admins passwords in files config.')
        sys.exit(0)


    # loop = asyncio.get_event_loop()
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    root = Tk()
    menu = create_menu(root)

    root.update_task = loop.create_task(tkinter_update(root, loop))
    # Tell tkinter window instance what to do before it is destroyed.
    root.protocol("WM_DELETE_WINDOW", lambda: close_window(root))

    window = WindowMain(root, loop, menu)

    try:
        logger.info('Is loop opened...')
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    logger.info('... is loop closed.')

    # DO NOT IMPLEMENT; this is replaced by running tkinter's update() method in a asyncio loop called loop.
    # See tkinter_update() method and root.update_task.
    # root.mainloop()
