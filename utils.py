import pygame

def load_image(path):
    return pygame.image.load(path).convert_alpha()

def draw_text(surface, text, font, color, position):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)