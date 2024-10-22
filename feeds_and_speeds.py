#!/usr/bin/env python3

import sys
import math
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QMessageBox, QGridLayout)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

# Configuration Classes
class MaterialConfig:
    CONFIGS = {
        "Soft plastics": {
            "chiploads": {
                1.5: (0.05, 0.075),
                3.175: (0.05, 0.13),
                6: (0.05, 0.254)
            },
            "plunge_rate_range": (0.4, 0.5)
        },
        "Soft wood & hard plastics": {
            "chiploads": {
                1.5: (0.025, 0.04),
                3.175: (0.025, 0.063),
                6: (0.025, 0.127)
            },
            "plunge_rate_range": (0.3, 0.3)
        },
        "Hard wood & aluminium": {
            "chiploads": {
                1.5: (0.013, 0.013),
                3.175: (0.013, 0.025),
                6: (0.025, 0.05)
            },
            "plunge_rate_range": (0.1, 0.3)
        }
    }

class CuttingStyleConfig:
    CONFIGS = {
        "Wide and Shallow": {
            "woc_multiplier": (0.4, 1.0),
            "doc_multiplier": (0.05, 0.1)
        },
        "Narrow and Deep": {
            "woc_multiplier": (0.1, 0.25),
            "doc_multiplier": (1.0, 3.0)
        }
    }

# Exceptions and Utilities
class ValidationError(Exception):
    pass

class CNCSuggestionEngine:
    """Handles suggestions and optimization recommendations"""

    RPM_STEPS = [11000, 13500, 18250, 24500, 29250, 31000]

    @classmethod
    def get_next_rpm(cls, current_rpm):
        try:
            current_index = cls.RPM_STEPS.index(current_rpm)
            if current_index < len(cls.RPM_STEPS) - 1:
                return cls.RPM_STEPS[current_index + 1]
        except ValueError:
            pass
        return None

    @classmethod
    def format_range(cls, range_tuple):
        return f"{range_tuple[0]:.2f} to {range_tuple[1]:.2f}"

class InputValidator:
    """Centralized input validation"""

    @staticmethod
    def validate_positive_float(value, field_name):
        try:
            float_value = float(value)
            if float_value <= 0:
                raise ValidationError(f"{field_name} must be positive")
            return float_value
        except ValueError:
            raise ValidationError(f"{field_name} must be a valid number")

    @staticmethod
    def validate_rpm(value):
        try:
            rpm = float(value)
            if rpm not in CNCSuggestionEngine.RPM_STEPS:
                raise ValidationError("Invalid RPM value")
            return rpm
        except ValueError:
            raise ValidationError("RPM must be a valid number")

# Model Classes
class CNCParameters:
    def __init__(self):
        self.flutes = 1
        self.tool_diameter = 6.35
        self.rpm = 18250
        self.woc = 6.35
        self.doc = 0.254
        self.material = "Soft plastics"
        self.cutting_style = "Wide and Shallow"
        self.chipload = 0.0254

    @property
    def feedrate(self):
        return self.calculate_feedrate()

    def calculate_feedrate(self):
        base_feedrate = self.rpm * self.chipload * self.flutes
        if self.woc > self.tool_diameter / 2:
            return base_feedrate
        return base_feedrate / math.sqrt(1 - (1 - 2 * self.woc / self.tool_diameter) ** 2)

class CNCCalculator:
    MAX_FEEDRATE = 6000
    CHIPLOAD_INCREMENT = 0.0001

    def __init__(self):
        self.parameters = CNCParameters()
        self._chipload_cache = {}

    def suggest_chipload(self):
        cache_key = (self.parameters.tool_diameter, self.parameters.material)
        if cache_key in self._chipload_cache:
            return self._chipload_cache[cache_key]

        material_config = MaterialConfig.CONFIGS[self.parameters.material]
        result = self._interpolate_chipload(material_config["chiploads"])
        self._chipload_cache[cache_key] = result
        return result

    def _interpolate_chipload(self, chipload_data):
        diameters = sorted(chipload_data.keys())
        tool_diameter = self.parameters.tool_diameter

        if tool_diameter <= diameters[0]:
            return chipload_data[diameters[0]]
        if tool_diameter >= diameters[-1]:
            return self._extrapolate_chipload(chipload_data, diameters[-2:])

        for i in range(len(diameters) - 1):
            if diameters[i] <= tool_diameter <= diameters[i + 1]:
                return self._interpolate(
                    tool_diameter,
                    diameters[i], chipload_data[diameters[i]],
                    diameters[i + 1], chipload_data[diameters[i + 1]]
                )

        return chipload_data[diameters[0]]  # fallback

    def _interpolate(self, x, x1, y1, x2, y2):
        """Linear interpolation helper"""
        if isinstance(y1, tuple) and isinstance(y2, tuple):
            return (
                y1[0] + (x - x1) * (y2[0] - y1[0]) / (x2 - x1),
                y1[1] + (x - x1) * (y2[1] - y1[1]) / (x2 - x1)
            )
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

    def _extrapolate_chipload(self, chipload_data, last_two_diameters):
        """Extrapolate chipload for larger tool diameters"""
        d1, d2 = last_two_diameters
        v1, v2 = chipload_data[d1], chipload_data[d2]

        return self._interpolate(
            self.parameters.tool_diameter,
            d1, v1,
            d2, v2
        )

    def _calculate_range(self, base_value, multiplier_tuple):
        return (
            base_value * multiplier_tuple[0],
            base_value * multiplier_tuple[1]
        )

    def calculate_guidelines(self):
        cutting_config = CuttingStyleConfig.CONFIGS[self.parameters.cutting_style]
        material_config = MaterialConfig.CONFIGS[self.parameters.material]

        woc_range = self._calculate_range(
            self.parameters.tool_diameter,
            cutting_config["woc_multiplier"]
        )

        doc_range = self._calculate_range(
            self.parameters.tool_diameter,
            cutting_config["doc_multiplier"]
        )

        plunge_rate = self._calculate_range(
            self.parameters.feedrate,
            material_config["plunge_rate_range"]
        )

        return woc_range, doc_range, plunge_rate

    def maximize_feedrate(self):
        lower_chipload, upper_chipload = self.suggest_chipload()
        current_chipload = lower_chipload
        max_feedrate = 0
        max_chipload = current_chipload

        # Binary search implementation for optimization
        while abs(upper_chipload - lower_chipload) > self.CHIPLOAD_INCREMENT:
            mid_chipload = (lower_chipload + upper_chipload) / 2
            self.parameters.chipload = mid_chipload
            feedrate = self.parameters.feedrate

            if feedrate <= self.MAX_FEEDRATE:
                max_feedrate = feedrate
                max_chipload = mid_chipload
                lower_chipload = mid_chipload
            else:
                upper_chipload = mid_chipload

        return max_feedrate, max_chipload

# View Model
class CNCCalculatorViewModel:
    def __init__(self):
        self.calculator = CNCCalculator()
        self.validators = {
            'flutes': lambda x: x > 0,
            'tool_diameter': lambda x: x > 0,
            'woc': lambda x: x > 0,
            'doc': lambda x: x > 0,
            'chipload': lambda x: x > 0
        }

    def validate_input(self, parameter, value):
        try:
            float_value = float(value)
            validator = self.validators.get(parameter)
            if validator and not validator(float_value):
                raise ValidationError(f"Invalid {parameter} value")
            return float_value
        except ValueError as e:
            raise ValidationError(f"Invalid input for {parameter}: {str(e)}")

    def update_parameter(self, parameter, value):
        validated_value = self.validate_input(parameter, value)
        setattr(self.calculator.parameters, parameter, validated_value)

    def calculate_results(self):
        feedrate = self.calculator.parameters.feedrate
        woc_range, doc_range, plunge_rate = self.calculator.calculate_guidelines()

        return {
            'feedrate': feedrate,
            'woc_range': woc_range,
            'doc_range': doc_range,
            'plunge_rate': plunge_rate,
            'warning': feedrate > CNCCalculator.MAX_FEEDRATE
        }

# GUI Implementation
class CNCCalculatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.view_model = CNCCalculatorViewModel()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("CNC Milling Calculator")
        self.setGeometry(200, 200, 800, 600)

        # Set up main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Create and add input group
        input_group = self.create_input_group()
        main_layout.addWidget(input_group)

        # Create and add results group
        results_group = self.create_results_group()
        main_layout.addWidget(results_group)

        # Initialize suggestions
        self.update_chipload_suggestion()

    def create_input_group(self):
        group = QGroupBox("Inputs")
        layout = QGridLayout()
        group.setLayout(layout)

        # Create input fields with labels
        self.inputs = {}
        input_fields = [
            ("flutes", "Number of endmill flutes:", "1"),
            ("tool_diameter", "Endmill diameter (mm):", "6.35"),
            ("woc", "Width of cut (WOC) (mm):", "6.35"),
            ("doc", "Depth of cut (DOC) (mm):", "0.254"),
            ("chipload", "Target total chipload (mm):", "0.0254")
        ]

        for row, (field_id, label_text, default_value) in enumerate(input_fields):
            self.inputs[field_id] = self.create_input_field(layout, label_text, default_value, row)

        # Add RPM combo box
        row = len(input_fields)
        layout.addWidget(QLabel("RPM:"), row, 0)
        self.rpm_combo = QComboBox()
        self.rpm_combo.addItems([str(rpm) for rpm in CNCSuggestionEngine.RPM_STEPS])
        self.rpm_combo.setCurrentText("18250")
        self.rpm_combo.currentTextChanged.connect(self.on_rpm_changed)
        layout.addWidget(self.rpm_combo, row, 1)

        # Add material combo box
        row += 1
        layout.addWidget(QLabel("Material type:"), row, 0)
        self.material_combo = QComboBox()
        self.material_combo.addItems(MaterialConfig.CONFIGS.keys())
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        layout.addWidget(self.material_combo, row, 1)

        # Add cutting style combo box
        row += 1
        layout.addWidget(QLabel("Cutting style:"), row, 0)
        self.cutting_style_combo = QComboBox()
        self.cutting_style_combo.addItems(CuttingStyleConfig.CONFIGS.keys())
        self.cutting_style_combo.currentTextChanged.connect(self.on_cutting_style_changed)
        layout.addWidget(self.cutting_style_combo, row, 1)

        # Add chipload suggestion label
        self.chipload_suggestion = QLabel()
        self.chipload_suggestion.setWordWrap(True)
        layout.addWidget(self.chipload_suggestion, row + 1, 0, 1, 2)

        # Add buttons
        button_layout = QHBoxLayout()
        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculate)
        maximize_button = QPushButton("Maximize Feedrate")
        maximize_button.clicked.connect(self.maximize_feedrate)

        button_layout.addWidget(calculate_button)
        button_layout.addWidget(maximize_button)
        layout.addLayout(button_layout, row + 2, 0, 1, 2)

        return group

    def create_results_group(self):
        group = QGroupBox("Results")
        layout = QVBoxLayout()
        group.setLayout(layout)

        self.results = {}
        result_fields = [
            ("feedrate", "Required feedrate (mm/min):"),
            ("woc_guideline", "WOC guideline (mm):"),
            ("doc_guideline", "DOC guideline (mm):"),
            ("plunge_rate", "Plunge rate guideline (mm/min):")
        ]

        for field_id, label_text in result_fields:
            self.results[field_id] = self.create_result_field(layout, label_text)

        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

        return group

    def create_input_field(self, layout, label, default_value, row):
        layout.addWidget(QLabel(label), row, 0)
        input_field = QLineEdit(default_value)
        input_field.setValidator(QDoubleValidator())
        input_field.textChanged.connect(self.on_input_changed)
        layout.addWidget(input_field, row, 1)
        return input_field

    def create_result_field(self, layout, label):
        result_layout = QHBoxLayout()
        result_layout.addWidget(QLabel(label))
        result_field = QLineEdit()
        result_field.setReadOnly(True)
        result_layout.addWidget(result_field)
        layout.addLayout(result_layout)
        return result_field

    def on_input_changed(self):
        try:
            self.update_model_from_inputs()
            self.update_chipload_suggestion()
        except ValidationError as e:
            self.show_error(str(e))

    def on_rpm_changed(self, value):
        try:
            self.view_model.update_parameter('rpm', value)
            self.update_chipload_suggestion()
        except ValidationError as e:
            self.show_error(str(e))

    def on_material_changed(self, value):
        self.view_model.calculator.parameters.material = value
        self.update_chipload_suggestion()

    def on_cutting_style_changed(self, value):
        self.view_model.calculator.parameters.cutting_style = value

    def update_model_from_inputs(self):
        for field_id, input_field in self.inputs.items():
            self.view_model.update_parameter(field_id, input_field.text())

    def update_chipload_suggestion(self):
        try:
            lower, upper = self.view_model.calculator.suggest_chipload()
            flutes = float(self.inputs['flutes'].text())
            suggestion_text = (
                f"Suggested chipload range:\n"
                f"{lower:.4f} to {upper:.4f} mm per flute\n"
                f"{lower * flutes:.4f} to {upper * flutes:.4f} mm total"
            )
            self.chipload_suggestion.setText(suggestion_text)
        except (ValidationError, ValueError):
            self.chipload_suggestion.setText("Invalid input for chipload calculation")

    def calculate(self):
        try:
            self.update_model_from_inputs()
            results = self.view_model.calculate_results()

            self.results['feedrate'].setText(f"{results['feedrate']:.0f}")
            self.results['woc_guideline'].setText(CNCSuggestionEngine.format_range(results['woc_range']))
            self.results['doc_guideline'].setText(CNCSuggestionEngine.format_range(results['doc_range']))
            self.results['plunge_rate'].setText(CNCSuggestionEngine.format_range(results['plunge_rate']))

            if results['warning']:
                self.warning_label.setText("Warning: Calculated feedrate exceeds 6000 mm/min")
            else:
                self.warning_label.setText("")

        except ValidationError as e:
            self.show_error(str(e))

    def maximize_feedrate(self):
        try:
            self.update_model_from_inputs()
            max_feedrate, max_chipload = self.view_model.calculator.maximize_feedrate()

            if max_feedrate == 0:
                self.show_error("Unable to find a valid feedrate. Please check your inputs.")
                return

            self.inputs['chipload'].setText(f"{max_chipload:.4f}")
            self.calculate()

            # Check if we should suggest increasing RPM
            lower_chipload, upper_chipload = self.view_model.calculator.suggest_chipload()
            if abs(max_chipload - upper_chipload) < CNCCalculator.CHIPLOAD_INCREMENT:
                self.suggest_rpm_increase(max_feedrate)

        except ValidationError as e:
            self.show_error(str(e))

    def suggest_rpm_increase(self, current_feedrate):
        response = QMessageBox.question(
            self,
            "Maximizer Result",
            f"Maximum feedrate of {current_feedrate:.0f} mm/min achieved at maximum suggested chipload.\n"
            "Would you like to increase the RPM to the next step?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if response == QMessageBox.StandardButton.Yes:
            current_rpm = float(self.rpm_combo.currentText())
            next_rpm = CNCSuggestionEngine.get_next_rpm(current_rpm)

            if next_rpm:
                self.rpm_combo.setCurrentText(str(next_rpm))
                self.maximize_feedrate()
            else:
                QMessageBox.information(self, "RPM Limit", "Already at maximum RPM.")

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    window = CNCCalculatorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()