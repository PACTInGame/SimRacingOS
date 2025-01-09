import time

import keyboard
import pyautogui
import pygame


def start_hotlap_blackwood(ui_manager):
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL1"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/car FZ5", b"/join"])
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


def start_hotlap_westhill(ui_manager):
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL1"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/spec"])
    time.sleep(1)
    lfs_interface.send_commands_to_lfs([b"/car FZ5", b"/join"])
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


def start_b1_lenken(ui_manager):
    ui_manager.draw_explanation("Lenkradhaltung")
    pygame.display.flip()
    pygame.display.update()
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL4"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/axload Lenkradhaltung"])
    time.sleep(0.7)
    lfs_interface.send_commands_to_lfs([b"/spec", b"/car FZ5"])
    time.sleep(0.4)
    lfs_interface.send_commands_to_lfs([b"/join"])
    ui_manager.draw_explanation("Lenkradhaltung-enter") # TODO Refactor all to be one function
    pygame.display.flip()
    pygame.display.update()
    keyboard.wait("enter")
    time.sleep(0.2)
    lfs_interface.send_commands_to_lfs([b"/ready"])
    ui_manager.close_screen()
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("Lenkradhaltung")


def start_b1_notbremsung(ui_manager):
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL4"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/axload Notbremsung"])
    time.sleep(0.7)
    lfs_interface.send_commands_to_lfs([b"/spec", b"/car FZ5"])
    time.sleep(0.4)
    lfs_interface.send_commands_to_lfs([b"/join"])
    time.sleep(0.3)
    lfs_interface.send_commands_to_lfs([b"/ready"])
    ui_manager.close_screen()
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("Notbremsung")


def start_b1_notbremsung_ausweichen(ui_manager):
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL4"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/axload Notbremsung_Ausweichen"])
    time.sleep(0.7)
    lfs_interface.send_commands_to_lfs([b"/spec", b"/car FZ5"])
    time.sleep(0.4)
    lfs_interface.send_commands_to_lfs([b"/join"])
    time.sleep(0.3)
    lfs_interface.send_commands_to_lfs([b"/ready"])
    ui_manager.close_screen()
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("Notbremsung_Ausweichen")

def start_b1_ausweichen(ui_manager):
    lfs_interface = ui_manager.os.lfs_interface
    lfs_interface.send_commands_to_lfs([b"/track BL4"])
    time.sleep(3)
    lfs_interface.send_commands_to_lfs([b"/axload Ausweichen"])
    time.sleep(0.7)
    lfs_interface.send_commands_to_lfs([b"/spec", b"/car FZ5"])
    time.sleep(0.4)
    lfs_interface.send_commands_to_lfs([b"/join"])
    time.sleep(0.3)
    lfs_interface.send_commands_to_lfs([b"/ready"])
    ui_manager.close_screen()
    ui_manager.draw_buttons()
    ui_manager.os.lfs_interface.track_uebung("Ausweichen")
