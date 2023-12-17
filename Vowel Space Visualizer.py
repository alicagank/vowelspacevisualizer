import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QComboBox, QFileDialog, QMessageBox, QCheckBox, QMenu, QMenuBar, QAction
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull


class ScatterplotVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create widgets
        self.create_widgets()

        # Set layout
        self.set_layout()

        # Set initial state
        self.data = pd.DataFrame(columns=["vowel", "F1", "F2", "source"])
        self.update_input_fields()
        self.setWindowTitle("Vowel Space Visualizer V.1.1")

        self.create_menu_bar()

    def create_menu_bar(self):
        menubar = QMenuBar(self)

        # File menu
        file_menu = menubar.addMenu('File')

        save_action = self.create_action('Save', self.save_scatterplot_auto, Qt.CTRL + Qt.Key_S)
        save_as_action = self.create_action('Save As...', self.save_scatterplot, Qt.CTRL + Qt.SHIFT + Qt.Key_S)
        save_data_action = self.create_action('Save Data As...', self.save_data_to_excel)
        import_data_action = self.create_action('Import Data from Excel', self.import_data_from_excel)

        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addAction(save_data_action)
        file_menu.addAction(import_data_action)

        # Edit menu
        edit_menu = menubar.addMenu('Edit')

        undo_action = self.create_action('Undo', self.undo_last_data, Qt.CTRL + Qt.Key_Z)
        edit_menu.addAction(undo_action)

        # Settings menu
        settings_menu = menubar.addMenu('Settings')

        # Visualization Settings submenu
        visualization_settings_menu = settings_menu.addMenu('Visualization Settings')

        # Connect Data with Polygons action
        self.connect_data_action = self.create_action('Connect Data with Polygons', self.update_scatterplot,
                                                      format='png', checkable=True)
        visualization_settings_menu.addAction(self.connect_data_action)

        self.layout().setMenuBar(menubar)

    def create_action(self, text, function, shortcut=None, format=None, checkable=False):
        action = QAction(text, self)
        action.triggered.connect(lambda: function(format) if format else function())
        action.setCheckable(checkable)
        if shortcut:
            action.setShortcut(shortcut)
        return action

    def create_widgets(self):
        self.label_mode = QLabel('Mode:')
        self.mode_combobox = QComboBox(self)
        self.mode_combobox.addItems(['Singular', 'Multiple'])
        self.mode_combobox.currentIndexChanged.connect(self.update_input_fields)

        self.label_vowel = QLabel('Vowel:')
        self.edit_vowel = QLineEdit()

        self.label_F1 = QLabel('F1 Value:')
        self.edit_F1 = QLineEdit()

        self.label_F2 = QLabel('F2 Value:')
        self.edit_F2 = QLineEdit()

        self.label_source = QLabel('Source:')
        self.edit_source = QLineEdit()

        self.label_title = QLabel('Add Title:')
        self.edit_title = QLineEdit()
        self.edit_title.textChanged.connect(self.update_title)

        self.button_add_data = self.create_button('Add Data', self.add_data, Qt.Key_Return)
        self.button_clear_data = self.create_button('Clear Data', self.clear_data)

        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)

    def set_layout(self):
        layout = QVBoxLayout()

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.label_mode)
        mode_layout.addWidget(self.mode_combobox)

        layout.addLayout(mode_layout)

        input_grid_layout = QGridLayout()
        input_grid_layout.addWidget(self.label_vowel, 0, 0)
        input_grid_layout.addWidget(self.edit_vowel, 0, 1)
        input_grid_layout.addWidget(self.label_F1, 1, 0)
        input_grid_layout.addWidget(self.edit_F1, 1, 1)
        input_grid_layout.addWidget(self.label_F2, 2, 0)
        input_grid_layout.addWidget(self.edit_F2, 2, 1)
        input_grid_layout.addWidget(self.label_source, 3, 0)
        input_grid_layout.addWidget(self.edit_source, 3, 1)

        layout.addLayout(input_grid_layout)

        title_layout = QHBoxLayout()
        title_layout.addWidget(self.label_title)
        title_layout.addWidget(self.edit_title)

        layout.addLayout(title_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.button_add_data)
        buttons_layout.addWidget(self.button_clear_data)

        layout.addLayout(buttons_layout)

        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def create_button(self, text, function, shortcut=None):
        button = QPushButton(text, self)
        button.clicked.connect(function)
        if shortcut:
            button.setShortcut(shortcut)
        return button

    def update_input_fields(self):
        mode = self.mode_combobox.currentText()
        self.label_source.setVisible(mode == 'Multiple')
        self.edit_source.setVisible(mode == 'Multiple')

    def add_data(self):
        if not self.validate_input_data():
            return

        mode = self.mode_combobox.currentText()
        vowel = self.edit_vowel.text()
        F1 = float(self.edit_F1.text())
        F2 = float(self.edit_F2.text())

        source = self.edit_source.text() if mode == 'Multiple' and self.edit_source.text() else ''

        new_data = pd.DataFrame({"vowel": [vowel], "F1": [F1], "F2": [F2], "source": [source]}) if source else \
                   pd.DataFrame({"vowel": [vowel], "F1": [F1], "F2": [F2]})

        self.data = pd.concat([self.data, new_data], ignore_index=True)

        self.clear_input_fields()

        self.edit_vowel.setFocus()
        self.update_scatterplot()

    def clear_input_fields(self):
        self.edit_vowel.clear()
        self.edit_F1.clear()
        self.edit_F2.clear()
        self.edit_source.clear()

    def validate_input_data(self):
        if not all([self.edit_vowel.text(), self.edit_F1.text(), self.edit_F2.text()]):
            self.show_error_message("Please fill in all the required fields.")
            return False

        try:
            F1 = float(self.edit_F1.text())
            F2 = float(self.edit_F2.text())
        except ValueError:
            self.show_error_message("Invalid numeric input for F1 or F2.")
            return False

        return True

    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Happy Accident!")
        msg_box.setText(message)
        msg_box.exec_()

    def undo_last_data(self):
        if not self.data.empty:
            self.data = self.data.iloc[:-1]
            self.update_scatterplot()

    def update_scatterplot(self, format=None):
        self.ax.clear()

        markers = ['o', 's', '^', 'v', '<', '>', '8', 'p', '*', 'h', '+', 'x', 'D']
        vowel_markers = {v: markers[i % len(markers)] for i, v in enumerate(self.data['vowel'].unique())}

        source_colors = {source: plt.cm.get_cmap('viridis')(i / len(self.data['source'].unique()))
                         for i, source in enumerate(self.data['source'].unique())}

        for v in self.data['vowel'].unique():
            subset = self.data[self.data['vowel'] == v]
            self.ax.scatter(
                subset["F2"], subset["F1"],
                marker=vowel_markers[v],
                c=[source_colors[s] for s in subset["source"]],
                label=v,
                alpha=0.8, edgecolors="w", linewidth=1
            )

            for index, row in subset.iterrows():
                self.ax.annotate(row["vowel"], (row["F2"], row["F1"]), textcoords="offset points", xytext=(0, 5),
                                 ha='center', va='bottom', fontsize=8)

        if self.connect_data_action.isChecked() and len(self.data) >= 3:
            for source, group in self.data.groupby("source"):
                points = np.array([group["F2"], group["F1"]]).T
                if len(points) >= 3:
                    hull = ConvexHull(points)
                    polygon = plt.Polygon(points[hull.vertices], closed=True, alpha=0.2, label=source,
                                          facecolor=source_colors[source])
                    self.ax.add_patch(polygon)

        self.ax.yaxis.tick_right()
        self.ax.xaxis.tick_top()

        plt.gca().invert_xaxis()
        plt.gca().invert_yaxis()

        custom_title = self.edit_title.text()
        if custom_title:
            self.ax.set_title(custom_title, pad=20)
        else:
            self.ax.set_title("Vowel Space(s)", pad=20)

        self.ax.set_xlabel("F2")
        self.ax.set_ylabel("F1")

        self.ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()

        self.ax.yaxis.set_label_position("right")
        self.ax.xaxis.set_label_position("top")
        self.ax.yaxis.set_ticks_position("right")
        self.ax.xaxis.set_ticks_position("top")

    def clear_data(self):
        self.data = pd.DataFrame(columns=["vowel", "F1", "F2", "source"])
        self.update_scatterplot()

    def save_scatterplot_auto(self):
        custom_title = self.edit_title.text() or "Vowel Spaces"
        file_name = f"{custom_title}.jpg"
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Scatterplot", file_name,
                                                   "JPEG Files (*.jpg *.jpeg);;All Files (*)")

        if file_name:
            try:
                self.figure.savefig(file_name, format='jpeg', dpi=800)
                QMessageBox.information(self, "Success", "Scatterplot saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving scatterplot: {str(e)}")

    def save_scatterplot(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Scatterplot", "",
                                                   "JPEG Files (*.jpg *.jpeg);;PNG Files (*.png);;All Files (*)",
                                                   options=options)

        if file_name:
            try:
                # Determine file format based on the selected file extension
                file_format = 'jpeg' if file_name.lower().endswith(('.jpg', '.jpeg')) else 'png'

                self.figure.savefig(file_name, format=file_format, dpi=800)
                QMessageBox.information(self, "Success", "Scatterplot saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving scatterplot: {str(e)}")

    def save_data_to_excel(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data as Excel", "",
                                                   "Excel Files (*.xls *.xlsx);;All Files (*)", options=options)

        if file_name:
            try:
                # Determine file format based on the selected file extension
                file_format = 'xls' if file_name.lower().endswith('.xls') else 'xlsx'

                self.data.to_excel(file_name, index=False, sheet_name='Sheet1', engine='openpyxl')
                QMessageBox.information(self, "Success", f"Data saved to {file_format} successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving data to {file_format}: {str(e)}")

    def import_data_from_excel(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Data from Excel", "",
                                                   "Excel Files (*.xls *.xlsx);;All Files (*)", options=options)

        if file_name:
            try:
                # Specify the sheet name if needed
                # sheet_name = 'Sheet1'  # Replace with the actual sheet name
                new_data = pd.read_excel(file_name, na_values=['', 'NaN', 'nan', 'N/A', 'NA', 'n/a'])

                # Convert 'F1' and 'F2' columns to numeric
                new_data['F1'] = pd.to_numeric(new_data['F1'], errors='coerce')
                new_data['F2'] = pd.to_numeric(new_data['F2'], errors='coerce')

                # Set 'source' column to an empty string if it doesn't exist
                if 'source' not in new_data.columns:
                    new_data['source'] = ''

                # Replace empty values in 'source' column with a space character
                new_data['source'] = new_data['source'].fillna('N/A')

                # Drop rows with missing values after conversion
                new_data = new_data.dropna()

                self.data = pd.concat([self.data, new_data], ignore_index=True)
                self.update_scatterplot()
                QMessageBox.information(self, "Success", "Data imported from Excel successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error importing data from Excel: {str(e)}")


    def update_title(self):
        custom_title = self.edit_title.text()
        self.ax.set_title(custom_title if custom_title else "Vowel Spaces", pad=20)
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_app = ScatterplotVisualizer()
    my_app.show()
    sys.exit(app.exec_())

    # Vowel Space Visualizer V.1.1
    # Ali Çağan Kaya, under the GPL-3.0 license.