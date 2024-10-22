import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QMessageBox, QGridLayout)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt
from cnc_calculator.presentation.viewmodels.cnc_calculator_viewmodel import CNCCalculatorViewModel
from cnc_calculator.domain.models.cutting_parameters import CuttingParameters
from cnc_calculator.domain.models.material import Material
from cnc_calculator.domain.models.cutting_style import CuttingStyle
from cnc_calculator.domain.value_objects.measurements import RPM, Feedrate, Distance

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
        self.rpm_combo.addItems([str(rpm) for rpm in [11000, 13500, 18250, 24500, 29250, 31000]])
        self.rpm_combo.setCurrentText("18250")
        self.rpm_combo.currentTextChanged.connect(self.on_rpm_changed)
        layout.addWidget(self.rpm_combo, row, 1)

        # Add material combo box
        row += 1
        layout.addWidget(QLabel("Material type:"), row, 0)
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Soft plastics", "Soft wood & hard plastics", "Hard wood & aluminium"])
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        layout.addWidget(self.material_combo, row, 1)

        # Add cutting style combo box
        row += 1
        layout.addWidget(QLabel("Cutting style:"), row, 0)
        self.cutting_style_combo = QComboBox()
        self.cutting_style_combo.addItems(["Wide and Shallow", "Narrow and Deep"])
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
        except ValueError as e:
            self.show_error(str(e))

    def on_rpm_changed(self, value):
        try:
            self.view_model.update_parameter('rpm', value)
            self.update_chipload_suggestion()
        except ValueError as e:
            self.show_error(str(e))

    def on_material_changed(self, value):
        self.view_model.update_parameter('material', value)
        self.update_chipload_suggestion()

    def on_cutting_style_changed(self, value):
        self.view_model.update_parameter('cutting_style', value)

    def update_model_from_inputs(self):
        for field_id, input_field in self.inputs.items():
            self.view_model.update_parameter(field_id, input_field.text())

    def update_chipload_suggestion(self):
        try:
            lower, upper = self.view_model.calculator.suggest_chipload(self.view_model.parameters.tool_diameter)
            flutes = float(self.inputs['flutes'].text())
            suggestion_text = (
                f"Suggested chipload range:\n"
                f"{lower:.4f} to {upper:.4f} mm per flute\n"
                f"{lower * flutes:.4f} to {upper * flutes:.4f} mm total"
            )
            self.chipload_suggestion.setText(suggestion_text)
        except (ValueError):
            self.chipload_suggestion.setText("Invalid input for chipload calculation")

    def calculate(self):
        try:
            self.update_model_from_inputs()
            results = self.view_model.calculate_results()

            self.results['feedrate'].setText(f"{results['feedrate']:.0f}")
            self.results['woc_guideline'].setText(f"{results['woc_range'][0]:.2f} to {results['woc_range'][1]:.2f}")
            self.results['doc_guideline'].setText(f"{results['doc_range'][0]:.2f} to {results['doc_range'][1]:.2f}")
            self.results['plunge_rate'].setText(f"{results['plunge_rate'][0]:.2f} to {results['plunge_rate'][1]:.2f}")

            if results['warning']:
                self.warning_label.setText("Warning: Calculated feedrate exceeds 6000 mm/min")
            else:
                self.warning_label.setText("")

        except ValueError as e:
            self.show_error(str(e))

    def maximize_feedrate(self):
        try:
            self.update_model_from_inputs()
            max_feedrate, max_chipload = self.view_model.maximize_feedrate(6000, 0.0001)

            if max_feedrate == 0:
                self.show_error("Unable to find a valid feedrate. Please check your inputs.")
                return

            self.inputs['chipload'].setText(f"{max_chipload:.4f}")
            self.calculate()

            # Check if we should suggest increasing RPM
            lower_chipload, upper_chipload = self.view_model.calculator.suggest_chipload(self.view_model.parameters.tool_diameter)
            if abs(max_chipload - upper_chipload) < 0.0001:
                self.suggest_rpm_increase(max_feedrate)

        except ValueError as e:
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
            next_rpm = self.get_next_rpm(current_rpm)

            if next_rpm:
                self.rpm_combo.setCurrentText(str(next_rpm))
                self.maximize_feedrate()
            else:
                QMessageBox.information(self, "RPM Limit", "Already at maximum RPM.")

    def get_next_rpm(self, current_rpm):
        rpm_steps = [11000, 13500, 18250, 24500, 29250, 31000]
        try:
            current_index = rpm_steps.index(current_rpm)
            if current_index < len(rpm_steps) - 1:
                return rpm_steps[current_index + 1]
        except ValueError:
            pass
        return None

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    window = CNCCalculatorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
