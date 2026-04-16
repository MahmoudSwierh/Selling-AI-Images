import os
import json
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import json
import shutil
from pathlib import Path


script_dir = Path(__file__).resolve().parent
base_dir = script_dir.parent

image_dir = base_dir / fr"Scored-To Review"
toupscale_dir = base_dir / fr"Reviewed"

# List all images in the folder
imagesNames = os.listdir(image_dir)

# Filter and process image names
image_floats = []
for file_name in imagesNames:
    # Extract the part of the name before the file extension
    base_name, ext = os.path.splitext(file_name)
    # Try converting the base name to a float
    try:
        value = int(base_name)
        if len(str(abs(value))) == 5:
            value = value * 100.1
            newName = str(value) + ext
            os.rename(fr"{image_dir}\{file_name}", fr"{image_dir}\{newName}")

        image_floats.append((value, file_name))  # Store the float and the original name
    except ValueError:
        continue

# Sort the list by the float values in descending order
image_floats.sort(reverse=True, key=lambda x: x[0])

# Extract the sorted file names
sorted_images = [file_name for _, file_name in image_floats]

current_index = 0
current_image_path = None

# Create the main window
root = tk.Tk()
root.title("Image Review App")
root.geometry("800x600")  # Initial window size

reviewedImages = []

# Temporary directory to hold last moved image
redo_dir = base_dir / fr"Scored-To Review\To Delete"
if not os.path.exists(redo_dir):
    os.makedirs(redo_dir)

last_moved_image = None
last_action = None  # Track whether the last action was 'delete' or 'keep'
action_delay = 0.2  # delay between actions in seconds

redo_stack = []

def redo_image(event=None):
    global current_index

    if not redo_stack:
        return

    last_moved_image, last_action = redo_stack.pop()

    if last_action == 'delete':
        shutil.move(last_moved_image, image_dir)
    elif last_action == 'keep':
        shutil.move(last_moved_image, image_dir)

    current_index -= 1
    show_image()

    if not redo_stack:
        redo_button.config(state='disabled')

# Fullscreen toggle
def toggle_fullscreen(event=None):
    is_fullscreen = root.attributes("-fullscreen")
    root.attributes("-fullscreen", not is_fullscreen)

root.bind('<Control_L>', toggle_fullscreen) 
root.bind('<Escape>', toggle_fullscreen)

last_width, last_height = root.winfo_width(), root.winfo_height()

def on_resize(event):
    global last_width, last_height

    if event.width != last_width or event.height != last_height:
        show_image()

        last_width, last_height = event.width, event.height

root.bind("<Configure>", on_resize)

screen_height = root.winfo_screenheight()
button_height = int(screen_height * 0.035)

del_allowed = True
keep_allowed = True

canvas = tk.Canvas(root, bg='#141414', highlightthickness=0,borderwidth=0)
canvas.pack(fill='both', expand=True)

root.update_idletasks()

def show_image():
    global current_image_path, current_index
    if current_index >= len(sorted_images):
        tk.messagebox.showinfo("End", "No more images to review.")
        root.destroy()
        return

    image_file = sorted_images[current_index]
    current_image_path = os.path.join(image_dir, image_file)
    try:
        img = Image.open(current_image_path)
    except:
        print(f"Image not found")
        reviewedImages.append(image_file)

        current_index += 1
        show_image()
        return
        
    img_aspect_ratio = img.width / img.height

    root.update_idletasks()
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height() - button_height

    if canvas_width / canvas_height > img_aspect_ratio:
        img = img.resize((int(canvas_height * img_aspect_ratio), canvas_height), Image.Resampling.LANCZOS)
    else:
        img = img.resize((canvas_width, int(canvas_width / img_aspect_ratio)), Image.Resampling.LANCZOS)

    img_tk = ImageTk.PhotoImage(img)
    canvas.create_image(canvas_width // 2, canvas_height // 2, anchor='center', image=img_tk)
    canvas.image = img_tk

    # Display current image score
    score, _ = os.path.splitext(image_file)
    
    score = int(score) * 0.00001
    root.title(f"Image Review App - {image_file} (Score: {score:.2f})")

def delete_image(event=None):
    global current_index, del_allowed

    if not del_allowed:
        return
    del_allowed = False
    root.after(int(action_delay * 1000), lambda: enable_del_action())

    if current_image_path:
        # Move image to redo folder instead of deleting immediately
        name = os.path.basename(current_image_path)
        temp_path = os.path.join(redo_dir, name)
        shutil.move(current_image_path, temp_path)
        redo_stack.append((temp_path, 'delete'))
        redo_button.config(state='normal')
        print(f"Deleted")
        reviewedImages.append(name)
        
    current_index += 1
    show_image()

def keep_image(event=None):
    global keep_allowed, current_index

    if not keep_allowed:
        return
    keep_allowed = False
    root.after(int(action_delay * 1000), lambda: enable_keep_action())

    if current_image_path:
        # Transfer the image to the kept images folder
        name = os.path.basename(current_image_path)
        destination_path = os.path.join(toupscale_dir, name)
        shutil.move(current_image_path, destination_path)
        redo_stack.append((destination_path, 'keep'))
        redo_button.config(state='normal')
        print(f"Kept and moved (keep): {destination_path}")
        reviewedImages.append(name)

    current_index += 1
    show_image()

def enable_del_action():
    global del_allowed
    del_allowed = True

def enable_keep_action():
    global keep_allowed
    keep_allowed = True

root.bind('<Delete>', delete_image)
root.bind('<space>', keep_image)
root.bind('<BackSpace>', redo_image)  # Bind Backspace for redo

def button_keep():
    keep_image()

def button_del():
    delete_image()

# Create buttons
delete_button = tk.Button(root, text="Delete", bg="red", fg="white", command=button_del)
keep_button = tk.Button(root, text="Good", bg="green", fg="white", command=button_keep)

redo_button = tk.Button(root, text="Redo", bg="green", fg="red", command=lambda: redo_image(), state='disabled')
redo_button.place(relx=1.0, rely=0.0, anchor='ne')

delete_button.place(relx=0.0, rely=1.0, anchor='sw', relwidth=0.5, height=button_height)
keep_button.place(relx=1.0, rely=1.0, anchor='se', relwidth=0.5, height=button_height)

def on_close():

    # Delete images in the redo folder
    for f in os.listdir(redo_dir):
        p = os.path.join(redo_dir, f)
        if os.path.isfile(p) and p.lower().endswith(('png', 'jpg', 'jpeg')):
            os.remove(p)

    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
