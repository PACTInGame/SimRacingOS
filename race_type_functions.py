import time

import keyboard
import pyautogui
import pygame


def start_hotlap_blackwood(ui_manager):
    ui_manager.draw_starting()
    pygame.display.flip()
    pygame.display.update()
    lfs_interface = ui_manager.os.lfs_interface

    lfs_interface.send_commands_to_lfs([b"/track BL1"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/weather 1"])
    time.sleep(2)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/car FZ5", b"/join"])
    lfs_interface.send_commands_to_lfs([b"/setup BL1_HL_120830"])
    ui_manager.close_screen()
    time.sleep(1)
    pyautogui.click(1539, 1372)
    time.sleep(0.2)
    pyautogui.click(3606, 760)
    time.sleep(0.2)
    lfs_interface.send_commands_to_lfs([b"/ready"])
    time.sleep(1)
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("HotlapBL1")


def start_practice_blackwood(ui_manager):
    ui_manager.draw_starting()
    pygame.display.flip()
    pygame.display.update()
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL1"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/weather 1"])
    time.sleep(2)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/car FZ5", b"/join"])
    lfs_interface.send_commands_to_lfs([b"/setup BL1_HL_120830TC"])
    time.sleep(0.1)
    lfs_interface.send_commands_to_lfs([b"/laps 3"])
    time.sleep(0.2)
    ui_manager.close_screen()
    lfs_interface.send_commands_to_lfs([b"/ready"])
    time.sleep(1)
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("PracticeBL1")


def start_hotlap_westhill(ui_manager):
    ui_manager.draw_starting()
    pygame.display.flip()
    pygame.display.update()
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track WE2"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/weather 1"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/car FZ5", b"/join"])
    lfs_interface.send_commands_to_lfs([b"/setup WE2R_Q_Final"])
    ui_manager.close_screen()
    time.sleep(1)
    pyautogui.click(1539, 1372)
    time.sleep(0.2)
    pyautogui.click(3606, 760)
    time.sleep(0.2)
    lfs_interface.send_commands_to_lfs([b"/ready"])
    time.sleep(1)

    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("HotlapWE2")


def start_practice_westhill(ui_manager):
    ui_manager.draw_starting()
    pygame.display.flip()
    pygame.display.update()
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track WE2"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/weather 1"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/car FZ5", b"/join"])
    lfs_interface.send_commands_to_lfs([b"/setup WE2R_Q_Final_TC"])
    time.sleep(0.2)
    ui_manager.close_screen()
    lfs_interface.send_commands_to_lfs([b"/ready"])
    time.sleep(1)
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("PracticeWE2")


def start_b1_uebung(ui_manager, uebung):

    ui_manager.current_explain = uebung
    ui_manager.current_screen = "explain"
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL4"])
    time.sleep(1)
    time.sleep(1)
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/weather 1"])
    time.sleep(1)
    load_layout = f"/axload {uebung}"
    load_layout = load_layout.encode()
    lfs_interface.send_commands_to_lfs([load_layout])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(0.2)
    lfs_interface.send_commands_to_lfs([b"/car FZ5"])
    time.sleep(0.4)
    lfs_interface.send_commands_to_lfs([b"/join"])
    if uebung in ["Lenkradhaltung", "Notbremsung", "Notbremsung_Ausweichen", "Ausweichen", "Schnelles_Ausweichen"]:
        lfs_interface.send_commands_to_lfs([b"/setup BL1_HL_120830TC"])
    else:
        lfs_interface.send_commands_to_lfs([b"/setup BL1_HL_120830"])
    ui_manager.current_explain = f"{uebung}-enter"
    keyboard.wait("enter")
    time.sleep(0.2)
    lfs_interface.send_commands_to_lfs([b"/ready"])
    ui_manager.ready_for_start = uebung


def start_driften(ui_manager):
    ui_manager.draw_starting()
    pygame.display.flip()
    pygame.display.update()
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track LA1"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/weather 3"])
    time.sleep(0.7)
    lfs_interface.send_commands_to_lfs([b"/axload Driften"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(0.2)
    lfs_interface.send_commands_to_lfs([b"/car FZ5"])
    time.sleep(0.4)
    lfs_interface.send_commands_to_lfs([b"/join"])
    lfs_interface.send_commands_to_lfs([b"/setup BL1_HL_120830"])
    time.sleep(0.2)
    ui_manager.close_screen()
    lfs_interface.send_commands_to_lfs([b"/ready"])
    time.sleep(1)
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("Driften")
