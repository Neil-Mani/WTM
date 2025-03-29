import subprocess
import time
import pywinctl
import pyautogui
import keyboard

# Store window objects
windows = []

def get_mouse_region():
    """Determine which quadrant of the screen the mouse is in."""
    screen_width, screen_height = pyautogui.size()
    mouse_x, mouse_y = pyautogui.position()
    
    # Define quadrants (top-left, top-right, bottom-left, bottom-right)
    if mouse_x < screen_width // 2 and mouse_y < screen_height // 2:
        return "top-left"
    elif mouse_x >= screen_width // 2 and mouse_y < screen_height // 2:
        return "top-right"
    elif mouse_x < screen_width // 2 and mouse_y >= screen_height // 2:
        return "bottom-left"
    else:
        return "bottom-right"

def find_window_at_mouse_position():
    """Find which window is under the mouse cursor."""
    mouse_x, mouse_y = pyautogui.position()
    
    for window in windows:
        if (window.left <= mouse_x <= window.left + window.width and 
            window.top <= mouse_y <= window.top + window.height):
            return window
    
    return None  # No window found at mouse position

def find_adjacent_windows(closed_window):
    """Find windows that are adjacent to the closed window."""
    adjacent = []
    
    # Get the closed window's position and size
    x, y, w, h = closed_window.left, closed_window.top, closed_window.width, closed_window.height
    
    for window in windows:
        # Check if window is adjacent horizontally
        horizontal_adjacent = (
            (abs(window.left + window.width - x) < 5) or  # Window is to the left of closed window
            (abs(window.left - (x + w)) < 5)              # Window is to the right of closed window
        ) and (
            (y < window.top + window.height) and (y + h > window.top)  # Vertical overlap
        )
        
        # Check if window is adjacent vertically
        vertical_adjacent = (
            (abs(window.top + window.height - y) < 5) or  # Window is above closed window
            (abs(window.top - (y + h)) < 5)               # Window is below closed window
        ) and (
            (x < window.left + window.width) and (x + w > window.left)  # Horizontal overlap
        )
        
        if horizontal_adjacent or vertical_adjacent:
            adjacent.append(window)
    
    return adjacent

def redistribute_layout():
    """Redistribute the entire layout based on the number of remaining windows."""
    screen_width, screen_height = pyautogui.size()
    num_windows = len(windows)
    
    if num_windows == 0:
        return  # No windows to manage
    
    if num_windows == 1:
        # One window takes up the whole screen
        windows[0].moveTo(0, 0)
        windows[0].resizeTo(screen_width, screen_height)
        return
        
    # For 2 windows, split the screen in half
    if num_windows == 2:
        # Split horizontally if screen is wider than tall
        if screen_width >= screen_height:
            windows[0].moveTo(0, 0)
            windows[0].resizeTo(screen_width // 2, screen_height)
            windows[1].moveTo(screen_width // 2, 0)
            windows[1].resizeTo(screen_width // 2, screen_height)
        else:
            windows[0].moveTo(0, 0)
            windows[0].resizeTo(screen_width, screen_height // 2)
            windows[1].moveTo(0, screen_height // 2)
            windows[1].resizeTo(screen_width, screen_height // 2)
        return
    
    # For 3 or 4 windows, use quadrants
    if num_windows <= 4:
        half_width = screen_width // 2
        half_height = screen_height // 2
        
        # Arrange in quadrants
        positions = [
            (0, 0, half_width, half_height),                   # top-left
            (half_width, 0, half_width, half_height),          # top-right
            (0, half_height, half_width, half_height),         # bottom-left
            (half_width, half_height, half_width, half_height) # bottom-right
        ]
        
        for i, window in enumerate(windows):
            if i < len(positions):
                x, y, w, h = positions[i]
                window.moveTo(x, y)
                window.resizeTo(w, h)
        return
    
    # For more windows, create a more complex tiling pattern
    cols = min(3, num_windows)
    rows = (num_windows + cols - 1) // cols
    
    cell_width = screen_width // cols
    cell_height = screen_height // rows
    
    for i, window in enumerate(windows):
        row = i // cols
        col = i % cols
        
        x = col * cell_width
        y = row * cell_height
        
        # Last row might need special handling for fewer windows
        if row == rows - 1 and col == num_windows % cols - 1 and num_windows % cols != 0:
            # Last window in a partially filled row, make it wider
            w = cell_width * (cols - (num_windows % cols) + 1)
        else:
            w = cell_width
            
        window.moveTo(x, y)
        window.resizeTo(w, cell_height)

def resize_and_place_windows():
    """Rearrange windows based on where the mouse is currently positioned."""
    if not windows:
        return  # No windows to manage
        
    if len(windows) == 1:
        # One window takes up the whole screen
        screen_width, screen_height = pyautogui.size()
        windows[0].moveTo(0, 0)
        windows[0].resizeTo(screen_width, screen_height)
        return
    
    # Find which existing window the mouse is over
    target_window = find_window_at_mouse_position()
    
    # If mouse isn't over any window, use the last active window
    if not target_window and len(windows) >= 2:
        target_window = windows[-2]  # Second last window
    elif not target_window:
        target_window = windows[0]  # Fallback to first window
    
    new_window = windows[-1]  # Most recent window
    
    # Get the current mouse position to determine placement
    region = get_mouse_region()
    
    # Get target window dimensions
    x, y, w, h = target_window.left, target_window.top, target_window.width, target_window.height
    
    # Determine split based on quadrant
    if region == "top-left":
        # Split horizontally and place on top if window is tall enough
        if h > w:
            target_window.moveTo(x, y + h // 2)
            target_window.resizeTo(w, h // 2)
            new_window.moveTo(x, y)
            new_window.resizeTo(w, h // 2)
        # Otherwise split vertically and place on left
        else:
            target_window.moveTo(x + w // 2, y)
            target_window.resizeTo(w // 2, h)
            new_window.moveTo(x, y)
            new_window.resizeTo(w // 2, h)
            
    elif region == "top-right":
        # Split horizontally and place on top if window is tall enough
        if h > w:
            target_window.moveTo(x, y + h // 2)
            target_window.resizeTo(w, h // 2)
            new_window.moveTo(x, y)
            new_window.resizeTo(w, h // 2)
        # Otherwise split vertically and place on right
        else:
            target_window.resizeTo(w // 2, h)
            new_window.moveTo(x + w // 2, y)
            new_window.resizeTo(w // 2, h)
            
    elif region == "bottom-left":
        # Split horizontally and place on bottom if window is tall enough
        if h > w:
            target_window.resizeTo(w, h // 2)
            new_window.moveTo(x, y + h // 2)
            new_window.resizeTo(w, h // 2)
        # Otherwise split vertically and place on left
        else:
            target_window.moveTo(x + w // 2, y)
            target_window.resizeTo(w // 2, h)
            new_window.moveTo(x, y)
            new_window.resizeTo(w // 2, h)
            
    else:  # bottom-right
        # Split horizontally and place on bottom if window is tall enough
        if h > w:
            target_window.resizeTo(w, h // 2)
            new_window.moveTo(x, y + h // 2)
            new_window.resizeTo(w, h // 2)
        # Otherwise split vertically and place on right
        else:
            target_window.resizeTo(w // 2, h)
            new_window.moveTo(x + w // 2, y)
            new_window.resizeTo(w // 2, h)

def open_and_tile_window():
    """Open a new window and tile it dynamically."""
    print("Hotkey pressed! Opening a new window...")

    process = subprocess.Popen("notepad.exe")  # Change to desired program
    time.sleep(1)  # Give time for the window to appear

    window = pywinctl.getActiveWindow()
    if not window:
        print("No active window found.")
        return

    windows.append(window)
    resize_and_place_windows()

def close_window_under_mouse():
    """Close the window that the mouse is currently hovering over."""
    # Find which window the mouse is over
    window_to_close = find_window_at_mouse_position()
    
    if not window_to_close:
        print("No window under mouse cursor to close.")
        return
    
    # Store the window's position and size before closing
    closed_window_info = {
        'left': window_to_close.left,
        'top': window_to_close.top,
        'width': window_to_close.width,
        'height': window_to_close.height
    }
    
    # Remove the window from our list
    windows.remove(window_to_close)
    
    # Close the window
    window_to_close.close()
    time.sleep(0.5)  # Give time for closing before rearranging
    
    # Redistribute the layout
    redistribute_layout()

# Bind hotkeys
keyboard.add_hotkey("ctrl+alt+x", open_and_tile_window)
keyboard.add_hotkey("ctrl+alt+c", close_window_under_mouse)  # Changed function

print("Press Ctrl + Alt + X to open a new window.")
print("Press Ctrl + Alt + C to close the window under the mouse cursor.")
keyboard.wait()  # Keep script running