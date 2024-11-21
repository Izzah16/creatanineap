import sys
import os
import json
import numpy as np
import pandas as pd
import joblib  # For loading the model
from train_model import extract_features
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QMenuBar, QMenu, QAction,
                            QFileDialog, QComboBox, QLabel, QGroupBox, QSpinBox,
                            QDoubleSpinBox, QTabWidget, QTextEdit, QMessageBox,
                            QStatusBar, QGridLayout, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pspython.pspyinstruments as pspyinstruments
import pspython.pspymethods as pspymethods
from calibration_model import CalibrationModel

class ParameterGroup(QGroupBox):
    def __init__(self, title, parameters):
        super().__init__(title)
        self.parameters = {}
        layout = QGridLayout()
        
        row = 0
        for param, (min_val, max_val, default, step) in parameters.items():
            label = QLabel(param)
            spinbox = QDoubleSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setValue(default)
            spinbox.setSingleStep(step)
            
            layout.addWidget(label, row, 0)
            layout.addWidget(spinbox, row, 1)
            self.parameters[param] = spinbox
            row += 1
            
        self.setLayout(layout)
    
    def get_values(self):
        return {param: widget.value() for param, widget in self.parameters.items()}

class ElectrochemicalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electrochemical Sensor Interface")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize data storage
        self.current_data = {'voltage': [], 'current': []}
        self.all_measurements = []
        
        # Initialize instrument manager
        self.manager = pspyinstruments.InstrumentManager(new_data_callback=self.new_data_callback)
        
        # Add measurement type selection
        self.measurement_type = None
        
        self.measurement_in_progress = False
        
        self.setup_ui()
        self.model, self.poly, self.scaler = self.load_model()
        self.calibration_model = CalibrationModel(degree=2)  # Instantiate the CalibrationModel
        
    def setup_ui(self):
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create left panel
        left_panel = self.create_left_panel()
        
     
        
        # Create right panel with tabs
        right_panel = self.create_right_panel()
        
        # Add panels to main layout
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(right_panel, stretch=3)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Data", self)
        open_action.triggered.connect(self.open_data)
        
        save_action = QAction("Save Data", self)
        save_action.triggered.connect(self.save_data)
        
        export_action = QAction("Export Plot", self)
        export_action.triggered.connect(self.export_plot)
        
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(export_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        calibrate_action = QAction("Calibrate", self)
        calibrate_action.triggered.connect(self.calibrate)
        
        analyze_action = QAction("Analyze Data", self)
        analyze_action.triggered.connect(self.analyze_data)
        
        tools_menu.addAction(calibrate_action)
        tools_menu.addAction(analyze_action)
    def start_new_measurement(self):
        # Prompt user to save current scan data
        reply = QMessageBox.question(self, "Save Data",
                                     "Do you want to save the current scan data?",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                     QMessageBox.Cancel)
        
        if reply == QMessageBox.Yes:
            self.save_data()  # Call the save_data method to save the current data
        elif reply == QMessageBox.Cancel:
            return  # If user cancels, do nothing and return

        # Clear previous data
        self.current_data = {'voltage': [], 'current': []}
        self.update_plot()  # Update the plot to reflect the cleared data
        self.update_data_display()  # Clear the data display
        self.statusBar.showMessage("Ready for new measurement")    
        
    def create_left_panel(self):
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Device connection
        connection_group = QGroupBox("Device Connection")
        connection_layout = QVBoxLayout()
        self.connect_btn = QPushButton("Connect Device")
        self.connect_btn.clicked.connect(self.connect_device)
        connection_layout.addWidget(self.connect_btn)
        connection_group.setLayout(connection_layout)
        
        # Technique selection with radio buttons
        technique_group = QGroupBox("Measurement Technique")
        technique_layout = QVBoxLayout()
        
        self.technique_button_group = QButtonGroup()
        
        # Create radio buttons for each technique
        self.dpv_radio = QRadioButton("DPV")
        self.ca_radio = QRadioButton("Chronoamperometry")
        self.eis_radio = QRadioButton("EIS")
        
        # Add radio buttons to button group
        self.technique_button_group.addButton(self.dpv_radio)
        self.technique_button_group.addButton(self.ca_radio)
        self.technique_button_group.addButton(self.eis_radio)
        
        # Add radio buttons to layout
        technique_layout.addWidget(self.dpv_radio)
        technique_layout.addWidget(self.ca_radio)
        technique_layout.addWidget(self.eis_radio)
        
        # Connect radio button signal
        self.technique_button_group.buttonClicked.connect(self.update_parameters)
        
        technique_group.setLayout(technique_layout)
        
        # Parameters for each technique
        self.parameters_group = self.create_parameter_groups()
        
        # Control buttons
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()  # Ensure control_layout is defined here
        self.start_btn = QPushButton("Start Measurement")
        self.start_btn.clicked.connect(self.start_measurement)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_measurement)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        self.generate_test_scan_btn = QPushButton("Generate Test Scan")
        self.generate_test_scan_btn.clicked.connect(self.start_test)  # Connect to the method that generates test data
        control_layout.addWidget(self.generate_test_scan_btn)
        control_group.setLayout(control_layout)

        self.start_new_measurement_btn = QPushButton("Start New Measurement")
        self.start_new_measurement_btn.clicked.connect(self.start_new_measurement)
        control_layout.addWidget(self.start_new_measurement_btn)

           # Final Button
        self.final_btn = QPushButton("Show Result")
        self.final_btn.clicked.connect(self.final_prediction)  # Connect to the new prediction method
        control_layout.addWidget(self.final_btn)

        control_group.setLayout(control_layout)

        self.get_calculated_results_btn = QPushButton("Get Calculated Results")
        self.get_calculated_results_btn.clicked.connect(self.get_calculated_results)  # Connect to the new method
        control_layout.addWidget(self.get_calculated_results_btn)
        
        control_group.setLayout(control_layout)
        
        # Add all groups to left panel
        left_layout.addWidget(connection_group)
        left_layout.addWidget(technique_group)
        left_layout.addWidget(self.parameters_group)
        left_layout.addWidget(control_group)
        left_layout.addStretch()
        
        return left_panel
    def create_right_panel(self):
        tab_widget = QTabWidget()
        
        # Plot tab
        plot_tab = QWidget()
        plot_layout = QVBoxLayout()
        
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        plot_tab.setLayout(plot_layout)
        
        # Data tab
        data_tab = QWidget()
        data_layout = QVBoxLayout()
        self.data_text = QTextEdit()
        self.data_text.setReadOnly(True)
        data_layout.addWidget(self.data_text)
        data_tab.setLayout(data_layout)
        
        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        results_tab.setLayout(results_layout)
        
        # Add tabs
        tab_widget.addTab(plot_tab, "Plot")
        tab_widget.addTab(data_tab, "Data")
        tab_widget.addTab(results_tab, "Results")
        
        return tab_widget

    def create_parameter_groups(self):
        parameters = {
            "DPV": {
                "Start Potential (V)": (-2.0, 2.0, -0.5, 0.1),
                "End Potential (V)": (-2.0, 2.0, 0.5, 0.1),
                "Step Potential (V)": (0.001, 0.1, 0.005, 0.001),
                "Pulse Amplitude (V)": (0.001, 0.25, 0.05, 0.001),
                "Pulse Width (s)": (0.001, 1.0, 0.05, 0.001),
                "Scan Rate (V/s)": (0.01, 1.0, 0.05, 0.01)
            },
            "Chronoamperometry": {
                "Deposition Potential (V)": (-2.0, 2.0, 0.0, 0.1),
                "Deposition Time (s)": (0.0, 1000.0, 0.0, 1.0),
                "Conditioning Potential (V)": (-2.0, 2.0, 0.0, 0.1),
                "Conditioning Time (s)": (0.0, 1000.0, 0.0, 1.0),
                "Equilibration Time (s)": (0.0, 1000.0, 0.0, 1.0),
                "Interval Time (s)": (0.001, 10.0, 0.1, 0.001),
                "Potential (V)": (-2.0, 2.0, 0.0, 0.1),
                " Run Time (s)": (0.1, 1000.0, 1.0, 0.1)
            },
            "EIS": {
                "DC Potential (V)": (-2.0, 2.0, 0.0, 0.1),
                "AC Amplitude (V)": (0.001, 0.5, 0.01, 0.001),
                "Start Frequency (Hz)": (0.1, 1000000.0, 100000.0, 100.0),
                "End Frequency (Hz)": (0.1, 1000000.0, 10000.0, 100.0),
                "Number of Frequencies": (1, 100, 11, 1),
                "Equilibration Time (s)": (0.0, 1000.0, 0.0, 1.0)
            }
        }
        
        self.param_widgets = {}
        for technique in parameters:
            self.param_widgets[technique] = ParameterGroup(f"{technique} Parameters", 
                                                         parameters[technique])
            self.param_widgets[technique].hide()
        
        # Set default technique
        self.dpv_radio.setChecked(True)
        self.measurement_type = "DPV"
        self.param_widgets["DPV"].show()
        return self.param_widgets["DPV"]

    def update_parameters(self, button):
        technique = button.text()
        self.measurement_type = technique
        self.parameters_group.hide()
        self.parameters_group = self.param_widgets[technique]
        self.parameters_group.show()

    def new_data_callback(self, new_data):
        try:
            # Update data storage
            if 'x' in new_data and 'y' in new_data:
                self.current_data['voltage'].append(float(new_data['x'][0]))
                self.current_data['current'].append(float(new_data['y'][0]))
            
            # Update plot
            self.update_plot()
            
            # Update data display
            self.update_data_display()
            
        except Exception as e:
            self.statusBar.showMessage(f"Error in data callback: {str(e)}")

    def update_plot(self):
        try:
            self.ax.clear()
            self.ax.plot(self.current_data['voltage'], self.current_data['current'])
            self.ax.set_xlabel('Potential (V)')
            self.ax.set_ylabel('Current (A)')
            self.ax.grid(True)
            self.canvas.draw()
        except Exception as e:
            self.statusBar.showMessage(f"Error updating plot: {str(e)}")

    def update_data_display(self):
        try:
            data_text = "Voltage (V)\tCurrent (A)\n"
            for v, i in zip(self.current_data['voltage'], self.current_data['current']):
                data_text += f"{v:.6f}\t{i:.6e}\n"
            self.data_text.setText(data_text)
        except Exception as e:
            self.statusBar.showMessage(f"Error updating data display: {str(e)}")

    def connect_device(self):
        try:
            if self.connect_btn.text() == "Connect Device":
                available_instruments = self.manager.discover_instruments()
                if available_instruments:
                    success = self.manager.connect(available_instruments[0])
                    if success:
                        self.connect_btn.setText("Disconnect")
                        self.statusBar.showMessage("Connected to device")
                        self.start_btn.setEnabled(True)
                    else:
                        self.statusBar.showMessage("Connection failed")
                else:
                    self.statusBar.showMessage("No devices found")
            else:
                success = self.manager.disconnect()
                if success:
                    self.connect_btn.setText("Connect Device")
                    self.statusBar.showMessage("Disconnected from device")
                    self.start_btn.setEnabled(False)
                else:
                    self.statusBar.showMessage("Error disconnecting")
        except Exception as e:
            self.statusBar.showMessage(f"Connection error: {str(e)}")
    def get_peak_current_value(self, voltage):
   
        if not self.current_data['voltage'] or not self.current_data['current']:
            return None
        
        for i, v in enumerate(self.current_data['voltage']):
            if abs(v - voltage) < 1e-4:  # Check if voltage is close to the target
                return self.current_data['current'][i]
        return None   
    def final_prediction(self):
        if not self.current_data['voltage'] or not self.current_data['current']:
            self.statusBar.showMessage("No data available for prediction.")
            return

        # Create a DataFrame for the current data
        data = pd.DataFrame({
            'Voltage': self.current_data['voltage'],
            'Current': self.current_data['current']
        })

        # Extract features from the current data
        features = extract_features(data)

        # Prepare a DataFrame for the features that the model expects
        feature_array = pd.DataFrame([[features['Peak_Height'], 
                                        features['Peak_Potential'], 
                                        features['Area_Under_Curve'], 
                                        features['Mean_Current'], 
                                        features['Std_Current'], 
                                        features['Skew_Current']]], 
                                    columns=['Peak_Height', 'Peak_Potential', 'Area_Under_Curve', 'Mean_Current', 'Std_Current', 'Skew_Current'])

        # Load the trained model
        model = joblib.load('rf_model.pkl')

        # Predict concentration using the model
        concentration_pred = model.predict(feature_array)

        # Display the predicted concentration
        QMessageBox.information(self, "Final Prediction Result", f"Predicted Concentration: {concentration_pred[0]:.4f} µM")
    def predict_concentration(self):
        # Ensure there is data to predict
        if not self.current_data['voltage'] or not self.current_data['current']:
            self.statusBar.showMessage("No data available for prediction.")
            return
        
        
        peak_current_value = self.get_peak_current_value(0.102075)
        
        if peak_current_value is None:
            self.statusBar.showMessage("No peak current found at 0.102075 V.")
            return
        
        # Prepare features for prediction
        scan_features = self.poly.transform([[0.102075, peak_current_value ]])
        scan_features = self.scaler.transform(scan_features)
        
        # Predict concentration using the model
        concentration_pred = self.model.predict(scan_features)
        
        # Display the predicted concentration
        QMessageBox.information(self, "Prediction Result", f"Predicted Concentration: {concentration_pred[0]:.4f} nM")     

    def start_measurement(self):
        try:
            # Check if the instrument is connected
            if not self.manager.is_connected ():
                self.statusBar.showMessage("Instrument is not connected.")
                return

            params = self.parameters_group.get_values()
            
            if self.measurement_type == "DPV":
                method = pspymethods.differential_pulse_voltammetry(
                    e_begin=params["Start Potential (V)"],
                    e_end=params["End Potential (V)"],
                    e_step=params["Step Potential (V)"],
                    pulse_height=params["Pulse Amplitude (V)"],
                    pulse_width=params["Pulse Width (s)"],
                    scan_rate=params["Scan Rate (V/s)"]
                )
            elif self.measurement_type == "Chronoamperometry":
                method = pspymethods.chronoamperometry(
                    e_deposition=params["Deposition Potential (V)"],
                    t_deposition=params["Deposition Time (s)"],
                    e_conditioning=params["Conditioning Potential (V)"],
                    t_conditioning=params["Conditioning Time (s)"],
                    equilibration_time=params["Equilibration Time (s)"],
                    interval_time=params["Interval Time (s)"],
                    e=params["Potential (V)"],
                    run_time=params["Run Time (s)"]  # Ensure this matches the expected parameter
                )
            elif self.measurement_type == "EIS":
                method = pspymethods.electrochemical_impedance_spectroscopy(
                    e_dc=params["DC Potential (V)"],
                    e_ac=params["AC Amplitude (V)"],
                    max_frequency=params["Start Frequency (Hz)"],
                    min_frequency=params["End Frequency (Hz)"],
                    n_frequencies=int(params["Number of Frequencies"]),
                    equilibration_time=params["Equilibration Time (s)"]
                )
            
            # Clear previous data
            self.current_data = {'voltage': [], 'current': []}
            
            # Start measurement
            if self.manager.measure(method):
                self.statusBar.showMessage("Measurement started")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
            else:
                self.statusBar.showMessage("Failed to start measurement")
                
        except Exception as e:
            self.statusBar.showMessage(f"Error starting measurement: {str(e)}")

    def stop_measurement(self):
        try:
            if self.measurement_in_progress:
                # Here, you can stop the measurement by managing the state
                self.manager.disconnect()  # Disconnecting to stop the measurement
                self.statusBar.showMessage("Measurement stopped")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)  # Disable stop button since measurement has stopped
                self.measurement_in_progress = False  # Reset the flag
            else:
                self.statusBar.showMessage("No measurement is currently in progress.")
        except Exception as e:
            self.statusBar.showMessage(f"Error stopping measurement: {str(e)}")
    # Add this method to the ElectrochemicalApp class
    def start_new_measurement(self):
    # Prompt user to save current scan data
        reply = QMessageBox.question(self, "Save Data",
                                    "Do you want to save the current scan data?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                    QMessageBox.Cancel)
        
        if reply == QMessageBox.Yes:
            self.save_data()  # Call the save_data method to save the current data
        elif reply == QMessageBox.Cancel:
            return  # If user cancels, do nothing and return

        # Clear previous data
        self.current_data = {'voltage': [], 'current': []}
        self.update_plot()  # Update the plot to reflect the cleared data
        self.update_data_display()  # Clear the data display
        self.statusBar.showMessage("Ready for new measurement")

        # Reset button states
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)  # Disable stop button since no measurement is ongoing

        # In the create_left_panel method, add the new button
             

    def start_test(self):
        voltage = [
            -0.50017, -0.489963, -0.479755, -0.469548, -0.45934, -0.449133, -0.438925,
            -0.428717, -0.41851, -0.408302, -0.398095, -0.387887, -0.37768, -0.367472,
            -0.357264, -0.347057, -0.336849, -0.326642, -0.316434, -0.306227, -0.296019,
            -0.285811, -0.275604, -0.265396, -0.255189, -0.244981, -0.234774, -0.224566,
            -0.214358, -0.204151, -0.193943, -0.183736, -0.173528, -0.163321, -0.153113,
            -0.142905, -0.132698, -0.12249, -0.112283, -0.102075, -0.091868136, -0.08166056,
            -0.071452992, -0.06124542, -0.051037852, -0.04083028, -0.03062271, -0.02041514,
            -0.01020757, 0, 0.01020757, 0.02041514, 0.03062271, 0.04083028, 0.051037852,
            0.06124542, 0.071452992, 0.08166056, 0.091868136, 0.102075, 0.112283, 0.12249,
            0.132698, 0.142905, 0.153113, 0.163321, 0.173528, 0.183736, 0.193943,
            0.204151, 0.214358, 0.224566, 0.234774, 0.244981, 0.255189, 0.265396,
            0.275604, 0.285811, 0.296019, 0.306227, 0.316434, 0.326642, 0.336849,
            0.347057, 0.357264, 0.367472, 0.37768, 0.387887, 0.398095, 0.408302,
            0.41851, 0.428717, 0.438925, 0.449133, 0.45934, 0.469548, 0.479755,
            0.489963, 0.50017
        ]
        current =[
            14.447934, 12.151946, 10.751952, 9.687956, 8.93196, 8.203963, 7.545966, 
            7.055968, 6.56597, 6.110972, 5.753974, 5.424976, 5.088977, 4.794978, 
            4.577979, 4.35923, 4.142231, 4.003982, 3.863982, 3.713483, 3.618983, 
            3.543734, 3.452734, 3.372235, 3.347735, 3.307485, 3.246235, 3.258485, 
            3.256735, 3.230485, 3.240985, 3.268985, 3.268985, 3.286485, 3.347735, 
            3.393234, 3.417734, 3.524484, 3.648733, 3.765982, 3.949732, 4.205231, 
            4.46773, 4.765228, 5.179977, 5.587725, 5.955223, 6.396221, 6.809219, 
            7.111968, 7.384967, 7.699965, 7.897714, 7.988714, 8.209212, 8.319462, 
            8.303713, 8.357962, 8.380712, 8.266963, 8.093713, 7.992214, 7.762965, 
            7.433966, 7.250217, 7.022718, 6.78647, 6.643845, 6.603595, 6.57122, 
            6.58347, 6.727845, 6.838969, 6.886219, 7.069093, 7.227467, 7.341217, 
            7.502216, 7.738465, 7.909964, 8.041214, 8.331712, 8.573211, 8.73596, 
            9.01421, 9.313458, 9.519957, 9.742207, 10.088705, 10.345954, 10.508703, 
            10.904201, 11.226199, 11.448449, 11.805447, 12.248195, 12.613943, 
            12.998942, 13.698938
        ]
        self.current_data = {'voltage': voltage, 'current': current}
    
        # Update plot and data display
        self.update_plot()
        self.update_data_display()
        self.statusBar.showMessage("Test data generated")

    def save_data(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Data", "", "CSV files (*.csv);;All Files (*)"
            )
            if filename:
                df = pd.DataFrame({
                    'Voltage (V)': self.current_data['voltage'],
                    'Current (A)': self.current_data['current']
                })
                df.to_csv(filename, index=False)
                self.statusBar.showMessage(f"Data saved to {filename}")
        except Exception as e:
            self.statusBar.showMessage(f"Error saving data: {str(e)}")

    def open_data(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Open Data", "", "CSV files (*.csv);;All Files (*)"
            )
            if filename:
                df = pd.read_csv(filename)
                self.current_data = {
                    'voltage': df['Voltage (V)'].tolist(),
                    'current': df['Current (A)'].tolist()
                }
                self.update_plot()
                self.update_data_display()
                self.statusBar.showMessage(f"Data loaded from {filename}")
        except Exception as e:
            self.statusBar.showMessage(f"Error loading data: {str(e)}")

    def export_plot(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Plot", "", 
                "PNG files (*.png);;PDF files (*.pdf);;All Files (*)"
            )
            if filename:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                self.statusBar.showMessage(f" Plot exported to {filename}")
        except Exception as e:
            self.statusBar.showMessage(f"Error exporting plot: {str(e)}")

    def calibrate(self):
        try:
            # Add your calibration routine here
            calibration_dialog = QMessageBox()
            calibration_dialog.setWindowTitle("Calibration")
            calibration_dialog.setText("Calibration feature coming soon...")
            calibration_dialog.exec_()
        except Exception as e:
            self.statusBar.showMessage(f"Calibration error: {str(e)}")

    def analyze_data(self):
        try:
            if not self.current_data['voltage'] or not self.current_data['current']:
                self.statusBar.showMessage("No data to analyze")
                return

            # Basic analysis
            current_array = np.array(self.current_data['current'])
            voltage_array = np.array(self.current_data['voltage'])
            
            peak_current = np.max(np.abs(current_array))
            peak_voltage = voltage_array[np.argmax(np.abs(current_array))]
            
            analysis_results = (
                "Analysis Results:\n"
                f"Peak Current: {peak_current:.2e} A\n"
                f"Peak Voltage: {peak_voltage:.3f} V\n"
                f"Data Points: {len(current_array)}\n"
                "------------------------\n"
            )
            
            self.results_text.append(analysis_results)
            
        except Exception as e:
            self.statusBar.showMessage(f"Analysis error: {str(e)}")

    def closeEvent(self, event):
        try:
            if hasattr(self, 'manager'):
                self.manager.disconnect()
            event.accept()
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
            event.accept()
    def load_model(self):
    # Load the trained model, polynomial features, and scaler
        
        model = joblib.load('rf_model.pkl')  # Ensure this file is in the same directory as main.py
        poly = joblib.load('poly.pkl')
        scaler = joblib.load('scaler.pkl')
        return model, poly, scaler        
    def predict_concentration(self):
    # Ensure there is data to predict
        if not self.current_data['voltage'] or not self.current_data['current']:
            self.statusBar.showMessage("No data available for prediction.")
            return
       
        latest_voltage = np.mean(self.current_data['voltage'])
        latest_current = np.mean(self.current_data['current'])
        
        # Prepare features for prediction as a DataFrame
        features = pd.DataFrame([[latest_voltage, latest_current]], columns=['Voltage', 'Current'])
        
        # Transform features for prediction
        scan_features = self.poly.transform(features)
        scan_features = self.scaler.transform(scan_features)
        
        # Predict concentration using the model
        concentration_pred = self.model.predict(scan_features)
        
        # Display the predicted concentration
        QMessageBox.information(self, "Prediction Result", f"Predicted Concentration: {concentration_pred[0]:.4f} µM")
    def get_calculated_results(self):
   
        peak_current_value = self.get_peak_current_value(0.102075)   
        if peak_current_value is None:
            self.statusBar.showMessage("No peak current found at 0.102075 V.")
            return
        
        # Use the calibration model to predict concentration
        concentration_pred = self.calibration_model.predict_concentration(peak_current_value)
        
        # Display the predicted concentration
        QMessageBox.information(self, "Calculated Concentration", f"Calculated Concentration from Test Scan: {concentration_pred:.4f} µM")

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Set application-wide stylesheet
        stylesheet = """
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px;
                min-height: 25px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 13px;
                height: 13px;
            }
            QRadioButton::indicator:checked {
                background-color: #2196F3;
                border: 2px solid white;
                border-radius: 7px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #757575;
                border-radius: 7px;
            }
        """
        app.setStyleSheet(stylesheet)
        
        window = ElectrochemicalApp()
        window.show()
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()