import pygame
import sys
import re

import keyboard

def login_window():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.NOFRAME)
    pygame.display.set_caption("Login")

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (200, 200, 200)
    BLUE = (100, 150, 255)
    RED = (255, 100, 100)

    # Font
    font = pygame.font.Font(None, 50)
    error_font = pygame.font.Font(None, 40)

    # Input rectangles
    qnumber_rect = pygame.Rect(710, 300, 500, 50)
    name_rect = pygame.Rect(710, 400, 500, 50)
    pin_rect = pygame.Rect(710, 500, 500, 50)

    # Input texts
    qnumber_text = ""
    name_text = ""
    pin_text = ""
    error_message = ""
    show_error = False

    # Active input field
    active_qnumber = True
    active_name = False
    active_pin = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                active_qnumber = qnumber_rect.collidepoint(event.pos)
                active_name = name_rect.collidepoint(event.pos)
                active_pin = pin_rect.collidepoint(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    if active_qnumber:
                        active_qnumber = False
                        active_name = True
                    elif active_name:
                        active_name = False
                        active_pin = True
                    else:
                        active_pin = False
                        active_qnumber = True

                elif event.key == pygame.K_RETURN:
                    q_pattern = re.compile(r'^[qQ]\d{6}$')
                    print(qnumber_text)
                    print(len(name_text), len(pin_text), q_pattern.match(qnumber_text))
                    if (len(name_text) > 0 and len(pin_text) == 4 and
                        q_pattern.match(qnumber_text)):
                        if pin_text == "3578":
                            pygame.quit()
                            return name_text, qnumber_text
                        else:
                            error_message = "Wrong PIN! Please try again."
                            show_error = True
                            pin_text = ""
                    else:
                        error_message = "Invalid input! Please check all fields."
                        show_error = True

                elif event.key == pygame.K_BACKSPACE:
                    if active_qnumber:
                        qnumber_text = qnumber_text[:-1]
                    elif active_name:
                        name_text = name_text[:-1]
                    elif active_pin:
                        pin_text = pin_text[:-1]
                else:
                    if active_qnumber:
                        if len(qnumber_text) < 7:
                            if (len(qnumber_text) == 0 and event.unicode in 'qQ') or \
                               (len(qnumber_text) > 0 and event.unicode.isdigit()):
                                qnumber_text += event.unicode
                    elif active_name:
                        if len(event.unicode.strip()) > 0:
                            name_text += event.unicode
                    elif active_pin:
                        if event.unicode.isdigit() and len(pin_text) < 4:
                            pin_text += event.unicode
                            show_error = False

        # Fill screen
        screen.fill(WHITE)

        # Draw title
        title_surface = font.render("Login System", True, BLACK)
        screen.blit(title_surface, (860, 200))

        # Draw input boxes with rounded corners and shadows
        pygame.draw.rect(screen, (220, 220, 220), qnumber_rect.inflate(4, 4))
        pygame.draw.rect(screen, (220, 220, 220), name_rect.inflate(4, 4))
        pygame.draw.rect(screen, (220, 220, 220), pin_rect.inflate(4, 4))
        pygame.draw.rect(screen, WHITE, qnumber_rect)
        pygame.draw.rect(screen, WHITE, name_rect)
        pygame.draw.rect(screen, WHITE, pin_rect)
        pygame.draw.rect(screen, BLUE if active_qnumber else GRAY, qnumber_rect, 2)
        pygame.draw.rect(screen, BLUE if active_name else GRAY, name_rect, 2)
        pygame.draw.rect(screen, BLUE if active_pin else GRAY, pin_rect, 2)

        # Render texts
        qnumber_surface = font.render("Q-Number:", True, BLACK)
        name_surface = font.render("Full Name:", True, BLACK)
        pin_surface = font.render("PIN:", True, BLACK)
        input_qnumber_surface = font.render(qnumber_text, True, BLACK)
        input_name_surface = font.render(name_text, True, BLACK)
        input_pin_surface = font.render("*" * len(pin_text), True, BLACK)

        # Draw texts
        screen.blit(qnumber_surface, (500, 310))
        screen.blit(name_surface, (500, 410))
        screen.blit(pin_surface, (500, 510))
        screen.blit(input_qnumber_surface, (qnumber_rect.x + 5, qnumber_rect.y + 5))
        screen.blit(input_name_surface, (name_rect.x + 5, name_rect.y + 5))
        screen.blit(input_pin_surface, (pin_rect.x + 5, pin_rect.y + 5))

        # Draw error message
        if show_error:
            error_surface = error_font.render(error_message, True, RED)
            screen.blit(error_surface, (710, 570))

        # Draw helper text
        helper_surface = error_font.render("Press TAB to switch fields, ENTER to login", True, GRAY)
        screen.blit(helper_surface, (710, 630))

        pygame.display.flip()


if __name__ == "__main__":
    user_name, qnummer = login_window()
    print(f"Logged in as: {user_name}")