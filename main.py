import tkinter as tk
from tkinter import ttk, messagebox
import math

def calculate_feedrate(flutes, rpm, chipload, woc, tool_diameter):
    base_feedrate = rpm * chipload * flutes
    if woc > tool_diameter / 2:
        return base_feedrate
    else:
        return base_feedrate / math.sqrt(1 - (1 - 2 * woc / tool_diameter)**2)

def interpolate(x, x1, y1, x2, y2):
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

def suggest_chipload(flutes, tool_diameter, material_type):
    chiploads = {
        "Soft plastics": {
            1.5: (0.05, 0.075),
            3.175: (0.05, 0.13),
            6: (0.05, 0.254)
        },
        "Soft wood & hard plastics": {
            1.5: (0.025, 0.04),
            3.175: (0.025, 0.063),
            6: (0.025, 0.127)
        },
        "Hard wood & aluminium": {
            1.5: (0.013, 0.013),
            3.175: (0.013, 0.025),
            6: (0.025, 0.05)
        }
    }

    diameters = [1.5, 3.175, 6]
    material_data = chiploads[material_type]

    if tool_diameter <= 1.5:
        return material_data[1.5]
    elif tool_diameter >= 6:
        # Extrapolate for larger diameters
        lower_diameter, upper_diameter = 3.175, 6
        lower_range = material_data[lower_diameter]
        upper_range = material_data[upper_diameter]

        slope_lower = (upper_range[0] - lower_range[0]) / (upper_diameter - lower_diameter)
        slope_upper = (upper_range[1] - lower_range[1]) / (upper_diameter - lower_diameter)

        extrapolated_lower = upper_range[0] + slope_lower * (tool_diameter - upper_diameter)
        extrapolated_upper = upper_range[1] + slope_upper * (tool_diameter - upper_diameter)

        # Ensure the lower value doesn't go below the minimum for the material
        extrapolated_lower = max(extrapolated_lower, material_data[1.5][0])

        return (extrapolated_lower, extrapolated_upper)
    else:
        lower_diameter = max([d for d in diameters if d <= tool_diameter])
        upper_diameter = min([d for d in diameters if d >= tool_diameter])

        # If the tool diameter exactly matches a predefined diameter
        if lower_diameter == upper_diameter:
            return material_data[lower_diameter]

        lower_range = material_data[lower_diameter]
        upper_range = material_data[upper_diameter]

        interpolated_lower = interpolate(tool_diameter, lower_diameter, lower_range[0], upper_diameter, upper_range[0])
        interpolated_upper = interpolate(tool_diameter, lower_diameter, lower_range[1], upper_diameter, upper_range[1])

        return (interpolated_lower, interpolated_upper)


class CNCCalculatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("CNC Milling Calculator")
        self.create_widgets()

        # Update idletasks to ensure all widgets are drawn
        self.master.update_idletasks()

        # Get the required width and height
        width = self.master.winfo_reqwidth()
        height = self.master.winfo_reqheight()

        # Set the window size to the required dimensions
        self.master.geometry(f"{width}x{height}")

        # Prevent resizing smaller than the required size
        self.master.minsize(width, height)

    def create_widgets(self):
        input_frame = ttk.LabelFrame(self.master, text="Inputs")
        input_frame.pack(padx=10, pady=10, fill="x")
        for i in range(8):
            input_frame.grid_columnconfigure(i, weight=1)

        self.flutes = self.create_input(input_frame, "Number of endmill flutes:", 1, 0)
        self.tool_diameter = self.create_input(input_frame, "Endmill diameter (mm):", 6.35, 1)

        ttk.Label(input_frame, text="RPM:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.rpm_var = tk.StringVar(value="18250")
        rpm_values = ["11000", "13500", "18250", "24500", "29250", "31000"]
        self.rpm_combo = ttk.Combobox(input_frame, textvariable=self.rpm_var, values=rpm_values)
        self.rpm_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.rpm_combo.bind("<<ComboboxSelected>>", self.update_chipload_suggestion)

        self.woc = self.create_input(input_frame, "Width of cut (WOC) (mm):", 6.35, 3)
        self.doc = self.create_input(input_frame, "Depth of cut (DOC) (mm):", 0.254, 4)

        ttk.Label(input_frame, text="Material type:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.material_var = tk.StringVar(value="Soft plastics")
        material_combo = ttk.Combobox(input_frame, textvariable=self.material_var,
                                      values=["Soft plastics", "Soft wood & hard plastics", "Hard wood & aluminium"])
        material_combo.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        material_combo.bind("<<ComboboxSelected>>", self.update_chipload_suggestion)

        ttk.Label(input_frame, text="Cutting style:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.cutting_style_var = tk.StringVar(value="Wide and Shallow")
        cutting_style_combo = ttk.Combobox(input_frame, textvariable=self.cutting_style_var,
                                           values=["Wide and Shallow", "Narrow and Deep"])
        cutting_style_combo.grid(row=6, column=1, sticky="ew", padx=5, pady=5)

        self.chipload_suggestion = tk.StringVar()
        ttk.Label(input_frame, textvariable=self.chipload_suggestion).grid(row=7, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.chipload = self.create_input(input_frame, "Target total chipload (mm):", 0.0254, 8)

        ttk.Button(input_frame, text="Calculate", command=self.calculate).grid(row=9, column=0, pady=10)
        ttk.Button(input_frame, text="Maximize Feedrate", command=self.maximize_feedrate).grid(row=9, column=1, pady=10)

        results_frame = ttk.LabelFrame(self.master, text="Results")
        results_frame.pack(padx=10, pady=10, fill="x")

        self.feedrate_result = self.create_output(results_frame, "Required feedrate (mm/min):")
        self.woc_guideline = self.create_output(results_frame, "WOC guideline (mm):")
        self.doc_guideline = self.create_output(results_frame, "DOC guideline (mm):")
        self.plunge_rate_guideline = self.create_output(results_frame, "Plunge rate guideline (mm/min):")
        self.warning_label = ttk.Label(results_frame, text="", foreground="red")
        self.warning_label.pack(padx=5, pady=5)

        self.update_chipload_suggestion()

    def create_input(self, parent, label, default, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        var = tk.DoubleVar(value=default)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        entry.bind("<KeyRelease>", self.update_chipload_suggestion)
        return var

    def create_output(self, parent, label):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(frame, text=label).pack(side="left", padx=5)
        var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=var, state="readonly", width=20)
        entry.pack(side="right", padx=5)
        return var

    def update_chipload_suggestion(self, event=None):
        try:
            flutes = self.flutes.get()
            tool_diameter = self.tool_diameter.get()
            material = self.material_var.get()
            lower, upper = suggest_chipload(flutes, tool_diameter, material)
            per_flute = f"{lower:.4f} to {upper:.4f}"
            total = f"{lower*flutes:.4f} to {upper*flutes:.4f}"
            self.chipload_suggestion.set(f"Suggested chipload range:\n{per_flute} mm per flute\n{total} mm total")
        except tk.TclError:
            self.chipload_suggestion.set("Invalid input. Please enter valid numbers.")

    def calculate(self):
        try:
            flutes = self.flutes.get()
            tool_diameter = self.tool_diameter.get()
            rpm = float(self.rpm_var.get())
            woc = self.woc.get()
            doc = self.doc.get()
            chipload = self.chipload.get()

            feedrate = calculate_feedrate(flutes, rpm, chipload, woc, tool_diameter)
            self.feedrate_result.set(f"{feedrate:.0f}")

            if feedrate > 6000:
                self.warning_label.config(text="Warning: Calculated feedrate exceeds 6000 mm/min")
            else:
                self.warning_label.config(text="")

            self.update_guidelines(tool_diameter, feedrate)
        except tk.TclError:
            self.feedrate_result.set("Invalid input")

    def update_guidelines(self, tool_diameter, feedrate):
        cutting_style = self.cutting_style_var.get()
        material = self.material_var.get()

        if cutting_style == "Wide and Shallow":
            woc_range = f"{tool_diameter * 0.4:.2f} to {tool_diameter:.2f}"
            doc_range = f"{tool_diameter * 0.05:.2f} to {tool_diameter * 0.1:.2f}"
        else:  # Narrow and Deep
            woc_range = f"{tool_diameter * 0.1:.2f} to {tool_diameter * 0.25:.2f}"
            doc_range = f"{tool_diameter:.2f} to {tool_diameter * 3:.2f}"

        self.woc_guideline.set(woc_range)
        self.doc_guideline.set(doc_range)

        if material == "Hard wood & aluminium":
            plunge_rate = f"{feedrate * 0.1:.0f} to {feedrate * 0.3:.0f}"
        elif material == "Soft wood & hard plastics":
            plunge_rate = f"{feedrate * 0.3:.0f}"
        else:  # Soft plastics
            plunge_rate = f"{feedrate * 0.4:.0f} to {feedrate * 0.5:.0f}"

        self.plunge_rate_guideline.set(f"{plunge_rate} mm/min")

    def maximize_feedrate(self):
        try:
            flutes = self.flutes.get()
            tool_diameter = self.tool_diameter.get()
            rpm = float(self.rpm_var.get())
            woc = self.woc.get()
            material = self.material_var.get()

            lower_chipload, upper_chipload = suggest_chipload(flutes, tool_diameter, material)
            current_chipload = lower_chipload
            max_feedrate = 0
            max_chipload = current_chipload

            while current_chipload <= upper_chipload:
                feedrate = calculate_feedrate(flutes, rpm, current_chipload, woc, tool_diameter)
                if feedrate > max_feedrate and feedrate <= 6000:
                    max_feedrate = feedrate
                    max_chipload = current_chipload
                elif feedrate > 6000:
                    break
                current_chipload += 0.0001

            if max_feedrate == 0:
                messagebox.showinfo("Maximizer Result", "Unable to find a valid feedrate. Please check your inputs.")
                return

            self.chipload.set(f"{max_chipload:.4f}")
            self.feedrate_result.set(f"{max_feedrate:.0f}")
            self.update_guidelines(tool_diameter, max_feedrate)

            if max_feedrate < 6000 and max_chipload >= upper_chipload:
                response = messagebox.askyesno("Maximizer Result",
                                               f"Maximum feedrate of {max_feedrate:.0f} mm/min achieved at maximum suggested chipload.\n"
                                               f"Would you like to increase the RPM to the next step?")
                if response:
                    self.increase_rpm()

        except tk.TclError:
            messagebox.showerror("Error", "Invalid input. Please enter valid numbers.")

    def increase_rpm(self):
        rpm_values = self.rpm_combo['values']
        current_index = rpm_values.index(self.rpm_var.get())
        if current_index < len(rpm_values) - 1:
            self.rpm_var.set(rpm_values[current_index + 1])
            self.maximize_feedrate()
        else:
            messagebox.showinfo("RPM Limit", "Already at maximum RPM.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CNCCalculatorGUI(root)
    root.mainloop()