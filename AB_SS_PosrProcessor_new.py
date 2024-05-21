import os
import time
import tkinter as tk
from tkinter import simpledialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def create_directory_structure():
    base_dir = 'D:/PP'
    fetch_dir = os.path.join(base_dir, 'Fetch')
    output_dir = os.path.join(base_dir, 'Output')

    os.makedirs(fetch_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    return fetch_dir, output_dir

def generate_cnc_hmi_file(input_gcode_path, output_file_path, feed_rate, num_loops):
    # Read the input G-code
    with open(input_gcode_path, 'r') as file:
        gcode_lines = file.readlines()

    # Initialize the output lines list
    output_lines = []
    g54_found = False
    while_started = False
    first_g00_found = False

    # Add the header information and the G54 command, comment everything before G54
    output_lines.append("; (Postprocessor Exp)\n")
    output_lines.append("; Dr. Bohrer Lasertec GmbH\n")
    output_lines.append("; Custom Post Processor\n")
    output_lines.append(f"; File location: {input_gcode_path}\n")
    output_lines.append(f"; Output Time: {os.path.getmtime(input_gcode_path)}\n")
    output_lines.append("; (Exported by FreeCAD)\n")
    output_lines.append("; (Post Processor: KineticNCBeamicon2_post)\n")
    output_lines.append(f"; (Output Time:{os.path.getmtime(input_gcode_path)})\n")
    output_lines.append("; (begin preamble)\n")
    output_lines.append("; %\n")
    output_lines.append("G54\n")
    output_lines.append(f"F{feed_rate:.3f} * 60\n")  # Write 'feed_rate * 60' as a string in the G-code

    # Add the while loop to repeat the operations
    output_lines.append(f"P1 = {num_loops}\n")
    output_lines.append("$WHILE P1 > 0\n")  # Remove the colon

    # Extract and process only G0 and G1 lines
    in_operation = False
    laser_on = False
    for i, line in enumerate(gcode_lines):
        if 'G54' in line:
            g54_found = True
        
        if not g54_found:
            line = ';' + line  # Comment out lines before G54 is found
        
        if line.startswith('(begin operation:'):
            in_operation = True
            continue
        elif line.startswith('(finish operation:'):
            in_operation = False
            continue
        
        if in_operation:
            if not first_g00_found and line.startswith('G0'):
                first_g00_found = True

            if first_g00_found:
                if line.startswith('G0'):
                    if laser_on:
                        output_lines.append("M62\n")  # Laser off
                        laser_on = False
                    output_lines.append(line.replace('G0', 'G00').replace('X', 'A').replace('Y', 'B').split('Z', 1)[0] + '\n')
                elif line.startswith('G1'):
                    if not laser_on:
                        output_lines.append("M61\n")  # Laser on
                        laser_on = True
                    output_lines.append(line.replace('G1', 'G01').replace('X', 'A').replace('Y', 'B').split('Z', 1)[0] + '\n')
                    if i + 1 < len(gcode_lines):
                        next_line = gcode_lines[i + 1]
                        if next_line.startswith('G0'):
                            output_lines.append("M62\n")  # Laser off
                            laser_on = False
                else:
                    parts = line.split()
                    new_parts = [part for part in parts if not part.startswith('Z') and not part.startswith('F')]
                    if new_parts:
                        output_lines.append("    " + " ".join(new_parts) + '\n')

    # Close the while loop and add postamble
    output_lines.append("    P1 = P1 - 1\n")
    output_lines.append("$ENDWHILE\n")
    output_lines.append("M30\n")  # Only keep M30 at the end

    # Write the output to the file
    with open(output_file_path, 'w') as file:
        file.writelines(output_lines)

# Define a function to prompt for user inputs using tkinter
def prompt_user_inputs():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    feed_rate = simpledialog.askfloat("Input", "Enter Feed Rate (mm/min):")
    num_loops = simpledialog.askinteger("Input", "Enter Number of Loops:")

    return feed_rate, num_loops

# Define a file system event handler
class NewFileHandler(FileSystemEventHandler):
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            feed_rate, num_loops = prompt_user_inputs()
            input_gcode_path = event.src_path
            output_file_name = os.path.basename(input_gcode_path).replace('.txt', '_output.txt')
            output_file_path = os.path.join(self.output_folder, output_file_name)
            generate_cnc_hmi_file(input_gcode_path, output_file_path, feed_rate, num_loops)

# Main function to run the script
def main():
    fetch_dir, output_dir = create_directory_structure()

    event_handler = NewFileHandler(fetch_dir, output_dir)
    observer = Observer()
    observer.schedule(event_handler, path=fetch_dir, recursive=False)
    observer.start()

    print(f"Watching folder: {fetch_dir} for new G-code files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
