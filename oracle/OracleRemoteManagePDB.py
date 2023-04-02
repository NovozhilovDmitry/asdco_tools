# зачем? мб для создания дампов
# def create_pdb_directory(self):
#     connection_string = self.connection_cdb_string_gui_suit.field_connection_string.get()
#     remote_system_data_pump_dir = self.connection_cdb_string_gui_suit.remote_system_data_pump_dir.get()
#     sysdba_name = self.sysdba_user_string_gui_suit.field_sysdba_name_string.get()
#     sysdba_password = self.sysdba_user_string_gui_suit.field_sysdba_password_string.get()
#
#     oracle_string, oracle_string_mask_password = get_string_create_data_pump_dir(sysdba_name,
#                                                                                  sysdba_password,
#                                                                                  connection_string,
#                                                                                  remote_system_data_pump_dir)
#     self.loop.create_task(self.run_async_cmd_with_check_and_run_next_functions(oracle_string,
#                                                                                oracle_string_mask_password,
#                                                                                check_failure_result_create_data_pump_dir,
#                                                                                check_failure=True))
