from tkinter import *
from tkinter import messagebox
import asyncio
import os
import sys
import argparse

from myLogging import logger

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
from additions import load_config

INTERVAL = 0.1
CONFIG_DIR = r'settings'
config_file_menu = os.path.join(os.getcwd(), CONFIG_DIR, r'menu.json')
config_file_oracle_remote = os.path.join(os.getcwd(), CONFIG_DIR, r'oracle_remote.json')


def parser_command_line_arguments():
    parser = argparse.ArgumentParser(description='AsdcoTools')
    parser.add_argument('--reset-admin-password',
                        dest='reset_admin_password',
                        default=False,
                        action='store_true',
                        help='Reset all admins passwords in files config')
    return parser


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


def create_menu(root):
    config_menu = load_config(config_file_menu)
    main_menu = Menu(root)
    root.config(menu=main_menu)
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
    if config_menu['oracle_remote_menu']:
        main_menu.add_cascade(label='Oracle (remote)', menu=oracle_remote_menu)
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
        logger.info("All tasks cancelling done.")
        root.destroy()


if __name__ == '__main__':
    logger.info(f'Start {__file__}')
    try:
        parser = parser_command_line_arguments()
        namespace = parser.parse_args()
        RESET_ADMIN_PASSWORD = namespace.reset_admin_password
    except TypeError:
        logger.error('Command line arguments are not specified correctly!')
        sys.exit()
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    root = Tk()
    menu = create_menu(root)
    root.update_task = loop.create_task(tkinter_update(root, loop))
    root.protocol("WM_DELETE_WINDOW", lambda: close_window(root))
    window = WindowMain(root, loop, menu)
    try:
        logger.info('Is loop opened...')
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    logger.info('... is loop closed.')
