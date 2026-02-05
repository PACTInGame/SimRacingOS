import mouse

def on_left_click():
    x, y = mouse.get_position()
    print(f"Left click at: ({x}, {y})")

mouse.on_button(on_left_click, buttons=("left",), types=("down",))

# keep the program running
mouse.wait()