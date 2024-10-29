#!/usr/bin/env python3

import sys
import math
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QMessageBox, QGridLayout)
from PyQt6.QtGui import QDoubleValidator, QFont
from PyQt6.QtCore import Qt

MAXIMUM_FEEDRATE = 10_000

def calculate_feedrate(flutes, rpm, chipload_per_flute, woc, tool_diameter):
    base_feedrate = rpm * chipload_per_flute * flutes
    if woc > tool_diameter / 2:
        return base_feedrate
    else:
        return base_feedrate / math.sqrt(1 - (1 - 2 * woc / tool_diameter) ** 2)


def interpolate(x, x1, y1, x2, y2):
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)


def suggest_chipload(tool_diameter, material_type):
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
        lower_diameter, upper_diameter = 3.175, 6
        lower_range = material_data[lower_diameter]
        upper_range = material_data[upper_diameter]

        slope_lower = (upper_range[0] - lower_range[0]) / (upper_diameter - lower_diameter)
        slope_upper = (upper_range[1] - lower_range[1]) / (upper_diameter - lower_diameter)

        extrapolated_lower = upper_range[0] + slope_lower * (tool_diameter - upper_diameter)
        extrapolated_upper = upper_range[1] + slope_upper * (tool_diameter - upper_diameter)

        extrapolated_lower = max(extrapolated_lower, material_data[1.5][0])

        return extrapolated_lower, extrapolated_upper
    else:
        lower_diameter = max([d for d in diameters if d <= tool_diameter])
        upper_diameter = min([d for d in diameters if d >= tool_diameter])

        if lower_diameter == upper_diameter:
            return material_data[lower_diameter]

        lower_range = material_data[lower_diameter]
        upper_range = material_data[upper_diameter]

        interpolated_lower = interpolate(tool_diameter, lower_diameter, lower_range[0], upper_diameter, upper_range[0])
        interpolated_upper = interpolate(tool_diameter, lower_diameter, lower_range[1], upper_diameter, upper_range[1])

        return interpolated_lower, interpolated_upper


class CNCCalculatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Milling Calculator")
        self.setGeometry(200, 200, 600, 400)  # Increased window size

        # Set a larger base font for the entire application
        app = QApplication.instance()
        font = app.font()
        font.setPointSize(16)  # Increased font size
        app.setFont(font)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        input_group = QGroupBox("Inputs")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        self.flutes = self.create_input(input_layout, "Number of endmill flutes:", 1, 0, 0)
        self.tool_diameter = self.create_input(input_layout, "Endmill diameter (mm):", 6.35, 1, 0)

        self.rpm_label = QLabel("RPM:")
        input_layout.addWidget(self.rpm_label, 2, 0)
        self.rpm_combo = QComboBox()
        self.rpm_combo.addItems(["10000", "14000", "18000", "23000", "27000", "32000"])
        self.rpm_combo.setCurrentText("18000")
        self.rpm_combo.currentTextChanged.connect(self.update_chipload_suggestion)
        self.rpm_combo.setMinimumHeight(30)  # Increased height
        input_layout.addWidget(self.rpm_combo, 2, 1)

        self.woc = self.create_input(input_layout, "Width of cut (WOC) (mm):", 6.35, 3, 0)
        self.doc = self.create_input(input_layout, "Depth of cut (DOC) (mm):", 0.254, 4, 0)

        self.material_label = QLabel("Material type:")
        input_layout.addWidget(self.material_label, 5, 0)
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Soft plastics", "Soft wood & hard plastics", "Hard wood & aluminium"])
        self.material_combo.currentTextChanged.connect(self.update_chipload_suggestion)
        self.material_combo.setMinimumHeight(30)  # Increased height
        input_layout.addWidget(self.material_combo, 5, 1)

        self.cutting_style_label = QLabel("Cutting style:")
        input_layout.addWidget(self.cutting_style_label, 6, 0)
        self.cutting_style_combo = QComboBox()
        self.cutting_style_combo.addItems(["Wide and Shallow", "Narrow and Deep"])
        self.cutting_style_combo.setMinimumHeight(30)  # Increased height
        input_layout.addWidget(self.cutting_style_combo, 6, 1)

        self.chipload_suggestion = QLabel()
        self.chipload_suggestion.setWordWrap(True)  # Allow text wrapping
        input_layout.addWidget(self.chipload_suggestion, 7, 0, 1, 2)

        self.chipload = self.create_input(input_layout, "Target total chipload (mm):", 0.0254, 8, 0)

        button_layout = QHBoxLayout()
        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculate)
        calculate_button.setMinimumHeight(35)  # Increased height
        button_layout.addWidget(calculate_button)

        maximize_button = QPushButton("Maximize Feedrate")
        maximize_button.clicked.connect(self.maximize_feedrate)
        maximize_button.setMinimumHeight(35)  # Increased height
        button_layout.addWidget(maximize_button)

        input_layout.addLayout(button_layout, 9, 0, 1, 2)

        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        self.feedrate_result = self.create_output(results_layout, "Required feedrate (mm/min):")
        self.woc_guideline = self.create_output(results_layout, "WOC guideline (mm):")
        self.doc_guideline = self.create_output(results_layout, "DOC guideline (mm):")
        self.plunge_rate_guideline = self.create_output(results_layout, "Plunge rate guideline (mm/min):")
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        self.warning_label.setWordWrap(True)  # Allow text wrapping
        results_layout.addWidget(self.warning_label)

        self.update_chipload_suggestion()

    def create_input(self, layout, label, default, row, col):
        label_widget = QLabel(label)
        layout.addWidget(label_widget, row, col)
        input_widget = QLineEdit(str(default))
        input_widget.setValidator(QDoubleValidator())
        input_widget.textChanged.connect(self.update_chipload_suggestion)
        input_widget.setMinimumHeight(30)  # Increased height
        layout.addWidget(input_widget, row, col + 1)
        return input_widget

    def create_output(self, layout, label):
        output_layout = QHBoxLayout()
        label_widget = QLabel(label)
        output_layout.addWidget(label_widget)
        output_widget = QLineEdit()
        output_widget.setReadOnly(True)
        output_widget.setMinimumHeight(30)  # Increased height
        output_layout.addWidget(output_widget)
        layout.addLayout(output_layout)
        return output_widget

    def update_chipload_suggestion(self):
        try:
            flutes = float(self.flutes.text())
            tool_diameter = float(self.tool_diameter.text())
            material = self.material_combo.currentText()
            lower, upper = suggest_chipload(tool_diameter, material)
            per_flute = f"{lower:.4f} to {upper:.4f}"
            total = f"{lower * flutes:.4f} to {upper * flutes:.4f}"
            self.chipload_suggestion.setText(f"Suggested chipload range:\n{per_flute} mm per flute\n{total} mm total")
        except ValueError:
            self.chipload_suggestion.setText("Invalid input. Please enter valid numbers.")

    def calculate(self):
        try:
            flutes = float(self.flutes.text())
            tool_diameter = float(self.tool_diameter.text())
            rpm = float(self.rpm_combo.currentText())
            woc = float(self.woc.text())
            float(self.doc.text())
            total_chipload = float(self.chipload.text())

            # Convert total chipload to per-flute chipload
            chipload_per_flute = total_chipload / flutes

            feedrate = calculate_feedrate(flutes, rpm, chipload_per_flute, woc, tool_diameter)
            self.feedrate_result.setText(f"{feedrate:.0f}")

            if feedrate > MAXIMUM_FEEDRATE:
                self.warning_label.setText(f"Warning: Calculated feedrate exceeds {MAXIMUM_FEEDRATE} mm/min")
            else:
                self.warning_label.setText("")

            self.update_guidelines(tool_diameter, feedrate)
        except ValueError:
            self.feedrate_result.setText("Invalid input")

    def update_guidelines(self, tool_diameter, feedrate):
        cutting_style = self.cutting_style_combo.currentText()
        material = self.material_combo.currentText()

        if cutting_style == "Wide and Shallow":
            woc_range = f"{tool_diameter * 0.4:.2f} to {tool_diameter:.2f}"
            doc_range = f"{tool_diameter * 0.05:.2f} to {tool_diameter * 0.1:.2f}"
        else:  # Narrow and Deep
            woc_range = f"{tool_diameter * 0.1:.2f} to {tool_diameter * 0.25:.2f}"
            doc_range = f"{tool_diameter:.2f} to {tool_diameter * 3:.2f}"

        self.woc_guideline.setText(woc_range)
        self.doc_guideline.setText(doc_range)

        if material == "Hard wood & aluminium":
            plunge_rate = f"{feedrate * 0.1:.0f} to {feedrate * 0.3:.0f}"
        elif material == "Soft wood & hard plastics":
            plunge_rate = f"{feedrate * 0.3:.0f}"
        else:  # Soft plastics
            plunge_rate = f"{feedrate * 0.4:.0f} to {feedrate * 0.5:.0f}"

        self.plunge_rate_guideline.setText(f"{plunge_rate} mm/min")

    def maximize_feedrate(self):
        try:
            flutes = float(self.flutes.text())
            tool_diameter = float(self.tool_diameter.text())
            rpm = float(self.rpm_combo.currentText())
            woc = float(self.woc.text())
            material = self.material_combo.currentText()

            # Get per-flute chipload range
            lower_chipload, upper_chipload = suggest_chipload(tool_diameter, material)

            # Convert to total chipload range
            lower_total_chipload = lower_chipload * flutes
            upper_total_chipload = upper_chipload * flutes

            current_total_chipload = lower_total_chipload
            max_feedrate = 0
            max_total_chipload = current_total_chipload

            while current_total_chipload <= upper_total_chipload:
                # Convert total chipload back to per-flute for feedrate calculation
                per_flute_chipload = current_total_chipload / flutes
                feedrate = calculate_feedrate(flutes, rpm, per_flute_chipload, woc, tool_diameter)

                if max_feedrate < feedrate <= MAXIMUM_FEEDRATE:
                    max_feedrate = feedrate
                    max_total_chipload = current_total_chipload
                elif feedrate > MAXIMUM_FEEDRATE:
                    break
                current_total_chipload += 0.0001

            if max_feedrate == 0:
                QMessageBox.information(self, "Maximizer Result",
                                        "Unable to find a valid feedrate. Please check your inputs.")
                return

            self.chipload.setText(f"{max_total_chipload:.4f}")
            self.feedrate_result.setText(f"{max_feedrate:.0f}")
            self.update_guidelines(tool_diameter, max_feedrate)

            # Check if we've reached the maximum suggested total chipload
            if abs(max_total_chipload - upper_total_chipload) < 0.0001:
                response = QMessageBox.question(self, "Maximizer Result",
                                                f"Maximum feedrate of {max_feedrate:.0f} mm/min achieved at maximum suggested chipload.\n"
                                                f"Would you like to increase the RPM to the next step?",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if response == QMessageBox.StandardButton.Yes:
                    self.increase_rpm()
            else:
                QMessageBox.information(self, "Maximizer Result",
                                        f"Maximum feedrate of {max_feedrate:.0f} mm/min achieved.")

        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid input. Please enter valid numbers.")

        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid input. Please enter valid numbers.")

    def increase_rpm(self):
        current_index = self.rpm_combo.currentIndex()
        if current_index < self.rpm_combo.count() - 1:
            self.rpm_combo.setCurrentIndex(current_index + 1)
            self.maximize_feedrate()
        else:
            QMessageBox.information(self, "RPM Limit", "Already at maximum RPM.")


def main():
    app = QApplication(sys.argv)
    window = CNCCalculatorGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
