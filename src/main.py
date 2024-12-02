import sys
import os
import json
from src.course import Course
from src.grade_category import GradeCategory
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QTableWidget, QTableWidgetItem, 
                            QFileDialog, QMessageBox, QTabWidget, 
                            QScrollArea, QFrame, QHeaderView, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from scipy.optimize import minimize
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtWidgets import QSizePolicy


class GPACalculator(QMainWindow):
    def init_input_fields(self):
        """Initialize all input fields"""
        # Course details inputs
        self.course_title_input = QLineEdit()
        self.credit_hours_input = QLineEdit()
        
        # Category inputs
        self.category_name_input = QLineEdit()
        self.category_weight_input = QLineEdit()
        self.total_assignments_input = QLineEdit()
        self.drops_input = QLineEdit()
        self.drops_input.setPlaceholderText("0")
        
        # Grade inputs
        self.grade_category_combo = QComboBox()
        self.grade_input = QLineEdit()
        
        # Tables
        self.categories_table = QTableWidget()
        self.grades_table = QTableWidget()
        self.gpa_table = QTableWidget()
        
        # Labels
        self.total_weight_label = QLabel("Total Weight: 0%")
        self.current_grade_label = QLabel("Current Grade: N/A")
        self.category_averages_text = QLabel()
        self.required_grades_text = QLabel()
        self.semester_gpa_label = QLabel("Semester GPA: N/A")
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPA Calculator")
        self.setMinimumSize(1200, 800)
        
        # Initialize state
        self.courses = {}
        self.current_course = None
        
        # Initialize all input fields
        self.init_input_fields()
        
        # Setup UI
        self.setup_ui()
        
        # Apply styling
        self.apply_styling()
        
    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def load_default_json(self):
        """Load the default JSON file from the app bundle"""
        try:
            # First try to load from the app bundle
            json_path = os.path.join(os.path.dirname(sys.executable), 
                                   '../Resources/courses_data.json')
            if not os.path.exists(json_path):
                # Fall back to the development path
                json_path = self.get_resource_path('resources/courses_data.json')
            
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading default JSON: {str(e)}")
            return None

    def setup_menu(self):
        """Set up the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # New Semester action
        new_semester = file_menu.addAction('New Semester')
        new_semester.triggered.connect(self.new_semester)
        
        # Sample Data action
        sample_action = file_menu.addAction('Load Sample Data')
        sample_action.triggered.connect(self.load_sample_data)
        
        file_menu.addSeparator()
        
        # Save/Load actions
        save_action = file_menu.addAction('Save All')
        save_action.triggered.connect(self.save_all_data)
        
        load_action = file_menu.addAction('Load All')
        load_action.triggered.connect(self.load_all_data)
        
        export_action = file_menu.addAction('Export Grades')
        export_action.triggered.connect(self.export_current_grades)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)

    def load_sample_data(self):
        """Load the sample data included with the app"""
        reply = QMessageBox.question(
            self,
            "Load Sample Data",
            "This will replace any existing data. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            data = self.load_default_json()
            if data:
                self.courses.clear()
                self.course_combo.clear()
                self.semester_combo.clear()
                
                for name, course_data in data['courses'].items():
                    self.courses[name] = Course.from_dict(course_data)
                
                self.update_semester_dropdown()
                self.update_gpa()
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Sample data loaded successfully!"
                )
        
    def apply_styling(self):
        """Apply consistent styling with visible text"""
        self.setStyleSheet("""
            QMainWindow, QWidget#course_content, QScrollArea {
                background-color: #e0e0e0;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 80px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f5f5f5;
                color: black;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: black;
                padding: 5px;
                border: 1px solid #ddd;
            }
            QLabel {
                color: black;
                font-weight: bold;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #aaa;
                border-radius: 4px;
                margin-top: 14px;
                background-color: #f0f0f0;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 3px;
                background-color: #f0f0f0;
                color: black;
            }
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: black;
                selection-background-color: #2196F3;
                selection-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid black;
                margin-right: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
            }
            QHeaderView::section:checked {
                background-color: #e0e0e0;
            }
        """)
    
    
    def setup_ui(self):
        """Set up the main UI structure"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create main tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create and add tabs
        self.courses_tab = QWidget()
        self.gpa_tab = QWidget()
        
        self.tab_widget.addTab(self.courses_tab, "Courses")
        self.tab_widget.addTab(self.gpa_tab, "GPA")
        
        # Set up individual tabs
        self.setup_courses_tab()
        self.setup_gpa_tab()
        
        # Add global save/load buttons
        self.setup_global_controls(main_layout)
        
    def setup_global_controls(self, layout: QVBoxLayout):
        """Set up global save/load controls"""
        controls_layout = QHBoxLayout()
        
        save_all_button = QPushButton("Save Grades to File")
        load_all_button = QPushButton("Load Grades from File")
        
        save_all_button.clicked.connect(self.save_all_data)
        load_all_button.clicked.connect(self.load_all_data)
        
        controls_layout.addWidget(save_all_button)
        controls_layout.addWidget(load_all_button)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
    
    
    def setup_boundaries_section(self):
        """Set up the grade boundaries section with compact layout"""
        bounds_group = QGroupBox("Grade Boundaries")
        bounds_layout = QHBoxLayout()  # Changed to horizontal layout
        
        self.boundary_inputs = {}
        gpa_points = [4.0, 3.5, 3.0, 2.5, 2.0]
        
        # Create a sub-layout for each GPA point and its input
        for gpa in gpa_points:
            point_layout = QHBoxLayout()
            label = QLabel(f"{gpa:.1f}:")
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Min %")
            input_field.setFixedWidth(60)  # Made input fields narrower
            self.boundary_inputs[gpa] = input_field
            point_layout.addWidget(label)
            point_layout.addWidget(input_field)
            point_layout.addSpacing(10)  # Add some space between pairs
            bounds_layout.addLayout(point_layout)
        
        save_bounds_button = QPushButton("Save")
        save_bounds_button.setFixedWidth(60)  # Made button narrower
        save_bounds_button.clicked.connect(self.save_boundaries)
        bounds_layout.addWidget(save_bounds_button)
        bounds_layout.addStretch()
        
        bounds_group.setLayout(bounds_layout)
        bounds_group.setMaximumHeight(100)  # Limit the height of the boundaries section
        self.course_layout.addWidget(bounds_group)

                

    def setup_courses_tab(self):
        """Set up the courses tab with proper spacing"""
        layout = QVBoxLayout(self.courses_tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Course selection area
        selection_group = QGroupBox("Course Selection")
        selection_layout = QHBoxLayout()
        selection_layout.setContentsMargins(10, 15, 10, 10)
        
        # Semester dropdown (moved before course dropdown)
        semester_label = QLabel("Select Semester:")
        self.semester_combo = QComboBox()
        self.semester_combo.setFixedWidth(200)
        self.semester_combo.currentTextChanged.connect(self.change_current_semester)
        selection_layout.addWidget(semester_label)
        selection_layout.addWidget(self.semester_combo)
        
        # Course dropdown
        course_label = QLabel("Select Course:")
        self.course_combo = QComboBox()
        self.course_combo.setFixedWidth(200)
        self.course_combo.currentTextChanged.connect(self.change_current_course)
        selection_layout.addWidget(course_label)
        selection_layout.addWidget(self.course_combo)
        
        # Course management buttons
        add_course_button = QPushButton("Add Course")
        delete_course_button = QPushButton("Delete Course")
        
        add_course_button.clicked.connect(self.add_new_course)
        delete_course_button.clicked.connect(self.delete_current_course)
        
        selection_layout.addWidget(add_course_button)
        selection_layout.addWidget(delete_course_button)
        selection_layout.addStretch()
        
        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)
        
        # Rest of the setup code remains the same...
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.course_content = QWidget()
        self.course_content.setObjectName("course_content")
        self.course_layout = QVBoxLayout(self.course_content)
        self.course_layout.setSpacing(10)
        self.course_layout.setContentsMargins(10, 10, 10, 10)
        
        self.setup_course_details()
        self.setup_boundaries_section()
        self.setup_final_policy_section()
        self.setup_categories_section()
        self.setup_grades_section()
        self.setup_analysis_section()
        
        scroll.setWidget(self.course_content)
        layout.addWidget(scroll)

    def setup_course_details(self):
        """Set up course details with proper spacing"""
        details_group = QGroupBox("Course Details")
        layout = QHBoxLayout()  # Change back to HBoxLayout
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Course title
        title_label = QLabel("Course Title:")
        self.course_title_input = QLineEdit()
        layout.addWidget(title_label)
        layout.addWidget(self.course_title_input)
        
        # Credit hours
        hours_label = QLabel("Credit Hours:")
        self.credit_hours_input = QLineEdit()
        self.credit_hours_input.setFixedWidth(60)
        layout.addWidget(hours_label)
        layout.addWidget(self.credit_hours_input)
        
        # Semester - make sure it's editable
        semester_label = QLabel("Semester:")
        self.semester_input = QLineEdit()
        self.semester_input.setPlaceholderText("e.g., Fall 2024")
        self.semester_input.editingFinished.connect(self.on_semester_input_change)
        layout.addWidget(semester_label)
        layout.addWidget(self.semester_input)
        
        layout.addStretch()
        details_group.setLayout(layout)
        self.course_layout.addWidget(details_group)
    def on_semester_input_change(self):
        """Handle semester input changes"""
        if not self.current_course:
            return
        
        new_semester = self.semester_input.text().strip()
        if new_semester:
            # Update the course's semester
            self.current_course.semester = new_semester
            
            # Update semester dropdown
            if self.semester_combo.findText(new_semester) == -1:
                self.semester_combo.addItem(new_semester)
                # Sort the semesters
                semesters = [self.semester_combo.itemText(i) 
                            for i in range(self.semester_combo.count())]
                sorted_semesters = self.sort_semesters(semesters)
                
                # Repopulate dropdown
                self.semester_combo.clear()
                self.semester_combo.addItems(sorted_semesters)
            
            # Set the current semester in dropdown
            self.semester_combo.setCurrentText(new_semester)


    def setup_categories_section(self):
        """Set up categories with proper spacing"""
        categories_group = QGroupBox("Grade Categories")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)  # Increased top margin
        layout.setSpacing(10)
        
        # Form layout for inputs
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(10)
        
        labels = ["Category Name:", "Weight (%):", "Total Assignments:", "Number of Drops:"]
        widgets = [self.category_name_input, self.category_weight_input,
                self.total_assignments_input, self.drops_input]
        
        for i, (label, widget) in enumerate(zip(labels, widgets)):
            form_layout.addWidget(QLabel(label), i // 2, (i % 2) * 2)
            form_layout.addWidget(widget, i // 2, (i % 2) * 2 + 1)
        
        layout.addLayout(form_layout)
        
        # Add category button
        add_button = QPushButton("Add Category")
        add_button.clicked.connect(self.add_category)
        layout.addWidget(add_button)
        
        # Categories table
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(5)
        self.categories_table.setHorizontalHeaderLabels([
            "Category", "Weight (%)", "Total Assignments", "Drops", "Actions"
        ])
        self.categories_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.categories_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.categories_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.categories_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.categories_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.categories_table.setMaximumHeight(200)
        layout.addWidget(self.categories_table)
        
        # Weight validation
        self.total_weight_label = QLabel("Total Weight: 0%")
        layout.addWidget(self.total_weight_label)
        
        categories_group.setLayout(layout)
        self.course_layout.addWidget(categories_group)

    def setup_final_policy_section(self):
        """Set up final exam policy with proper spacing"""
        final_group = QGroupBox("Final Exam Policy")
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)  # Increased top margin
        
        self.final_policy_combo = QComboBox()
        self.final_policy_combo.addItems([
            "No Replacement",
            "Replace Lowest Test (Experimental, use at own risk)",
            "Average with Lowest Test (Experimental, use at own risk)"
        ])
        self.final_policy_combo.currentTextChanged.connect(self.update_final_policy)
        
        layout.addWidget(QLabel("Final Exam Policy:"))
        layout.addWidget(self.final_policy_combo)
        layout.addStretch()
        
        final_group.setLayout(layout)
        self.course_layout.addWidget(final_group)

    def setup_grades_section(self):
        """Set up grades section with proper spacing"""
        grades_group = QGroupBox("Grades")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)  # Increased top margin
        layout.setSpacing(10)
        
        # Grade entry form
        entry_layout = QHBoxLayout()
        self.grade_category_combo = QComboBox()
        self.grade_input = QLineEdit()
        self.grade_input.setFixedWidth(60)
        self.grade_input.setPlaceholderText("0-100")
        
        entry_layout.addWidget(QLabel("Category:"))
        entry_layout.addWidget(self.grade_category_combo)
        entry_layout.addWidget(QLabel("Grade:"))
        entry_layout.addWidget(self.grade_input)
        
        add_button = QPushButton("Add Grade")
        add_button.clicked.connect(self.add_grade)
        entry_layout.addWidget(add_button)
        entry_layout.addStretch()
        
        layout.addLayout(entry_layout)
        
        # Grades table
        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(3)
        self.grades_table.setHorizontalHeaderLabels(["Category", "Grade", "Actions"])
        self.grades_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.grades_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.grades_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.grades_table.setMaximumHeight(200)
        layout.addWidget(self.grades_table)
        
        grades_group.setLayout(layout)
        self.course_layout.addWidget(grades_group)

    def setup_analysis_section(self):
        """Set up analysis section with proper spacing"""
        analysis_group = QGroupBox("Grade Analysis")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)  # Increased top margin
        layout.setSpacing(10)
        
        self.current_grade_label = QLabel("Current Grade: N/A")
        # self.current_grade_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.current_grade_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(self.current_grade_label)
        
        self.category_averages_text = QLabel()
        self.category_averages_text.setWordWrap(True)
        layout.addWidget(self.category_averages_text)
        
        self.required_grades_text = QLabel()
        self.required_grades_text.setWordWrap(True)
        layout.addWidget(self.required_grades_text)
        
        calc_button = QPushButton("Calculate Required Grades")
        calc_button.clicked.connect(self.calculate_required_grades)
        layout.addWidget(calc_button)
        
        analysis_group.setLayout(layout)
        self.course_layout.addWidget(analysis_group)
    
 
    

    

    

    def add_new_course(self):
        """Add a new course to the calculator"""
        course_name, ok = QInputDialog.getText(self, "Add Course", "Enter course name:")
        if ok and course_name:
            if course_name in self.courses:
                QMessageBox.warning(self, "Error", "Course already exists")
                return
                
            credit_hours, ok = QInputDialog.getDouble(
                self, "Credit Hours",
                "Enter credit hours:",
                value=3.0, min=0.0, max=6.0, decimals=1
            )
            if ok:
                # Create new course and set its semester
                new_course = Course(course_name, credit_hours)
                current_semester = self.semester_combo.currentText()
                if current_semester:
                    new_course.semester = current_semester
                
                self.courses[course_name] = new_course
                
                # Update course combo only if it's in the current semester
                if current_semester == new_course.semester:
                    self.course_combo.addItem(course_name)
                    self.course_combo.setCurrentText(course_name)
                
                self.update_gpa()

    def delete_current_course(self):
        """Delete the currently selected course"""
        course_name = self.course_combo.currentText()
        if course_name:
            reply = QMessageBox.question(
                self, "Delete Course",
                f"Are you sure you want to delete {course_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.course_combo.removeItem(self.course_combo.currentIndex())
                del self.courses[course_name]
                self.current_course = None
                self.update_course_display()
                self.update_gpa()

    def change_current_course(self, course_name: str):
        """Switch to a different course"""
        if course_name in self.courses:
            self.current_course = self.courses[course_name]
            self.update_course_display()
            self.update_grade_category_combo()
            
            # Update semester input when changing courses
            if self.current_course.semester:
                self.semester_input.setText(self.current_course.semester)

    def populate_course_combo(self, semester: str):
        """Populate course combo box with courses from the selected semester"""
        self.course_combo.clear()
        semester_courses = []
        for name, course in self.courses.items():
            if hasattr(course, 'semester') and course.semester == semester:
                semester_courses.append(name)
        self.course_combo.addItems(sorted(semester_courses))

    def update_course_display(self):
        """Update all UI elements to reflect the current course"""
        if not self.current_course:
            self.clear_course_display()
            return
                
        # Update basic info
        self.course_title_input.setText(self.current_course.name)
        self.credit_hours_input.setText(str(self.current_course.credit_hours))
        self.semester_input.setText(self.current_course.semester)  # Update semester display
        
        # Rest of the update code...
        for gpa, input_field in self.boundary_inputs.items():
            if gpa in self.current_course.grade_boundaries:
                input_field.setText(str(self.current_course.grade_boundaries[gpa]))
            else:
                input_field.clear()
        
        index = self.final_policy_combo.findText(self.current_course.final_policy)
        if index >= 0:
            self.final_policy_combo.setCurrentIndex(index)
        
        self.update_categories_table()
        self.update_grades_table()
        self.update_analysis()
        
    def clear_course_display(self):
        """Clear all course-related displays when no course is selected"""
        self.course_title_input.clear()
        self.credit_hours_input.clear()
        
        for input_field in self.boundary_inputs.values():
            input_field.clear()
        
        self.final_policy_combo.setCurrentIndex(0)
        self.categories_table.setRowCount(0)
        self.grades_table.setRowCount(0)
        self.grade_category_combo.clear()
        self.current_grade_label.setText("Current Grade: N/A")
        self.category_averages_text.clear()
        self.required_grades_text.clear()
        
    def add_category(self):
        """Add a new category to the current course"""
        if not self.current_course:
            QMessageBox.warning(self, "Error", "No course selected")
            return
            
        name = self.category_name_input.text().strip()
        weight_text = self.category_weight_input.text().strip()
        assignments_text = self.total_assignments_input.text().strip()
        drops_text = self.drops_input.text().strip()
        
        if not all([name, weight_text, assignments_text]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields")
            return
            
        try:
            weight = float(weight_text)
            total_assignments = int(assignments_text)
            drops = int(drops_text) if drops_text else 0
            
            if weight < 0 or weight > 100:
                raise ValueError("Weight must be between 0 and 100")
            if total_assignments < 0:
                raise ValueError("Total assignments must be positive")
            if drops < 0 or drops >= total_assignments:
                raise ValueError("Drops must be less than total assignments")
                
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return
            
        if name in self.current_course.categories:
            QMessageBox.warning(self, "Error", "Category already exists")
            return
            
        # Add category
        self.current_course.categories[name] = GradeCategory(
            name, weight, total_assignments, drops)
        
        # Update UI
        self.update_categories_table()
        self.update_grade_category_combo()
        
        # Clear inputs
        self.category_name_input.clear()
        self.category_weight_input.clear()
        self.total_assignments_input.clear()
        self.drops_input.clear()
        
        self.update_total_weight()
        self.update_analysis()

    def update_categories_table(self):
        """Update the categories display table"""
        self.categories_table.setRowCount(0)
        if not self.current_course:
            return
            
        for name, category in self.current_course.categories.items():
            row = self.categories_table.rowCount()
            self.categories_table.insertRow(row)
            
            self.categories_table.setItem(row, 0, QTableWidgetItem(name))
            self.categories_table.setItem(row, 1, QTableWidgetItem(f"{category.weight}"))
            self.categories_table.setItem(row, 2, QTableWidgetItem(f"{category.total_assignments}"))
            self.categories_table.setItem(row, 3, QTableWidgetItem(f"{category.drops}"))
            
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, n=name: self.delete_category(n))
            self.categories_table.setCellWidget(row, 4, delete_button)

    def update_grade_category_combo(self):
        """Update the category selection combo box"""
        self.grade_category_combo.clear()
        if self.current_course:
            self.grade_category_combo.addItems(sorted(self.current_course.categories.keys()))

    def update_total_weight(self):
        """Update the total weight display"""
        if not self.current_course:
            self.total_weight_label.setText("Total Weight: 0%")
            return
            
        total = sum(cat.weight for cat in self.current_course.categories.values())
        self.total_weight_label.setText(f"Total Weight: {total}%")
        
        if abs(total - 100) > 0.01:  # Allow for small floating point differences
            self.total_weight_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.total_weight_label.setStyleSheet("color: green; font-weight: bold;")

    def delete_category(self, name: str):
        """Delete a category from the current course"""
        if not self.current_course:
            return
            
        if name in self.current_course.categories:
            reply = QMessageBox.question(
                self, "Delete Category",
                f"Are you sure you want to delete the {name} category?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.current_course.categories[name]
                self.update_categories_table()
                self.update_grade_category_combo()
                self.update_total_weight()
                self.update_grades_table()
                self.update_analysis()

    def add_grade(self):
        """Add a new grade to the selected category"""
        if not self.current_course:
            QMessageBox.warning(self, "Error", "No course selected")
            return
            
        category = self.grade_category_combo.currentText()
        grade_text = self.grade_input.text().strip()
        
        if not category:
            QMessageBox.warning(self, "Error", "Please select a category")
            return
            
        if not grade_text:
            QMessageBox.warning(self, "Error", "Please enter a grade")
            return
            
        try:
            grade = float(grade_text)
            if grade < 0 or grade > 100:
                raise ValueError("Grade must be between 0 and 100")
                
            category_obj = self.current_course.categories[category]
            if len(category_obj.grades) >= category_obj.total_assignments:
                raise ValueError(
                    f"Cannot add more grades than total assignments ({category_obj.total_assignments})"
                )
                
            category_obj.grades.append(grade)
            self.update_grades_table()
            self.grade_input.clear()
            self.update_analysis()
                
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def update_grades_table(self):
        """Update the grades display table"""
        self.grades_table.setRowCount(0)
        if not self.current_course:
            return
            
        for category_name, category in self.current_course.categories.items():
            for i, grade in enumerate(category.grades):
                row = self.grades_table.rowCount()
                self.grades_table.insertRow(row)
                
                self.grades_table.setItem(row, 0, QTableWidgetItem(category_name))
                self.grades_table.setItem(row, 1, QTableWidgetItem(f"{grade:.2f}"))
                
                delete_button = QPushButton("Delete")
                delete_button.clicked.connect(
                    lambda _, c=category_name, g=grade, r=row: 
                    self.delete_grade(c, g, r))
                self.grades_table.setCellWidget(row, 2, delete_button)

    def delete_grade(self, category_name: str, grade: float, row: int):
        """Delete a grade from a category"""
        if not self.current_course:
            return
            
        if category_name in self.current_course.categories:
            try:
                self.current_course.categories[category_name].grades.remove(grade)
                self.grades_table.removeRow(row)
                self.update_analysis()
            except ValueError:
                QMessageBox.warning(self, "Error", "Error removing grade")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error: {str(e)}")

    def update_analysis(self):
        """Update the grade analysis display"""
        if not self.current_course:
            self.clear_analysis()
            return
            
        # Update current grade
        current_grade = self.current_course.calculate_current_grade()
        gpa_points = self.current_course.get_gpa_points(current_grade)
        
        # Convert values to float before formatting
        try:
            current_grade = float(current_grade)
            gpa_points = float(gpa_points)
            self.current_grade_label.setText(
                f"Current Grade: {current_grade:.2f}% ({gpa_points:.1f} GPA points)"
            )
        except (ValueError, TypeError):
            self.current_grade_label.setText("Current Grade: N/A")
        
        # Update category averages
        category_text = []
        for name, category in self.current_course.categories.items():
            if category.grades:
                try:
                    average = float(self.current_course.calculate_category_average(name))
                    category_text.append(
                        f"{name}: {average:.2f}% "
                        f"({len(category.grades)}/{category.total_assignments} assignments)"
                    )
                except (ValueError, TypeError):
                    continue
        
        self.category_averages_text.setText("\n".join(category_text))
        
        # Trigger GPA tab update
        self.update_gpa()

    def clear_analysis(self):
        """Clear all analysis displays"""
        self.current_grade_label.setText("Current Grade: N/A")
        self.category_averages_text.clear()
        self.required_grades_text.clear()

    def calculate_required_grades(self):
        """Main driver function - exact port of original calculate_all_required_grades"""
        if not self.current_course or not self.current_course.grade_boundaries:
            self.show_error("Please set grade boundaries first")
            return
                
        try:
            # Format current data for the optimizer
            current_grades = {}
            weights = {}
            total_assignments = {}
            
            # Collect data from categories
            for name, category in self.current_course.categories.items():
                current_grades[name] = category.grades.copy()
                weights[name] = category.weight / 100  # Convert to decimal
                total_assignments[name] = category.total_assignments
            
            results_text = []
            policy = self.final_policy_combo.currentText()
            
            # Get lowest current test grade if it exists
            lowest_test_grade = None
            if "Test" in current_grades and current_grades["Test"]:
                lowest_test_grade = min(current_grades["Test"])
            
            # Calculate for each grade boundary
            for gpa, boundary in sorted(self.current_course.grade_boundaries.items(), reverse=True):
                results_text.append(f"\n{gpa:.1f} ({boundary}%) Requirements:")
                
                try:
                    # First try with replacement/averaging
                    if policy != "No Replacement" and "Test" in current_grades and lowest_test_grade is not None:
                        required_grades = self.find_minimum_balanced_grades(
                            current_grades,
                            weights,
                            total_assignments,
                            float(boundary),
                            apply_final_policy=True
                        )
                        
                        # Check if the final exam grade is higher than the lowest test grade
                        # if "Final" in required_grades:
                        #     final_grade = required_grades["Final"][0]
                        #     if final_grade > lowest_test_grade:
                        #         # Use these results
                        #         results_text.append(f"  Using {policy} - final grade ({final_grade:.1f}%) would be higher than lowest test ({lowest_test_grade:.1f}%)")
                        #     else:
                        #         # Recalculate without replacement
                        #         required_grades = self.find_minimum_balanced_grades(
                        #             current_grades,
                        #             weights,
                        #             total_assignments,
                        #             float(boundary),
                        #             apply_final_policy=False
                        #         )
                        #         results_text.append(f"  Not using {policy} - required final grade ({final_grade:.1f}%) would not be higher than lowest test ({lowest_test_grade:.1f}%)")
                        # else:
                        #     results_text.append(f"  Not using {policy} - no final exam grade found")
                    else:
                        # Calculate normally without replacement
                        required_grades = self.find_minimum_balanced_grades(
                            current_grades,
                            weights,
                            total_assignments,
                            float(boundary),
                            apply_final_policy=False
                        )
                    
                    if not required_grades:  # No remaining assignments
                        results_text.append("  No remaining assignments")
                        continue
                    
                    # Display results
                    for category, grades in required_grades.items():
                        avg_needed = np.mean(grades)
                        num_grades = len(grades)
                        results_text.append(
                            f"  {category}: Need {avg_needed:.1f}% on remaining {num_grades} assignment(s)"
                        )
                
                except ValueError as e:
                    results_text.append(f"  Cannot achieve this grade: {str(e)}")
            
            self.required_grades_text.setText("\n".join(results_text))
            
        except Exception as e:
            self.show_error(f"Error calculating required grades: {str(e)}")

    def find_minimum_balanced_grades(self, current_grades, weights, total_assignments, target_grade, apply_final_policy=False):
        """Exact port of original optimization function"""
        # Process drops first
        processed_grades = {}
        for category, grades in current_grades.items():
            if grades:
                sorted_grades = sorted(grades)
                drops = self.current_course.categories[category].drops
                if drops > 0 and len(sorted_grades) > drops:
                    sorted_grades = sorted_grades[drops:]
                processed_grades[category] = sorted_grades
            else:
                processed_grades[category] = []

        # Calculate current contribution
        current_contribution = 0
        total_weight_used = 0
        
        for category in processed_grades:
            if processed_grades[category]:
                avg = np.mean(processed_grades[category])
                effective_total = total_assignments[category] - self.current_course.categories[category].drops
                completed_weight = weights[category] * (len(processed_grades[category]) / effective_total)
                current_contribution += avg * completed_weight
                total_weight_used += completed_weight

        if total_weight_used > 0:
            current_contribution = (current_contribution / total_weight_used) * total_weight_used
        
        # Calculate remaining assignments needed
        all_remaining_grades = []
        
        for category in weights:
            effective_total = total_assignments[category] - self.current_course.categories[category].drops
            current_count = len(processed_grades[category])
            remaining = max(0, effective_total - current_count)

            if remaining > 0:
                if category == "Test" and apply_final_policy:
                    # Add remaining tests with regular weight
                    weight_per = weights[category] / effective_total
                    all_remaining_grades.extend([(category, weight_per) for _ in range(remaining - 1)])  # Subtract 1 for final exam
                elif category == "Final" and apply_final_policy:
                    # Add final with appropriate weight based on policy
                    final_weight = weights[category] / effective_total
                    if self.final_policy_combo.currentText() == "Replace Lowest Test":
                        if "Test" in weights and "Test" in total_assignments:
                            test_weight = weights["Test"] / total_assignments["Test"]
                            all_remaining_grades.append(("Final", final_weight + test_weight))
                        else:
                            all_remaining_grades.append(("Final", final_weight))
                    elif self.final_policy_combo.currentText() == "Average with Lowest Test":
                        if "Test" in weights and "Test" in total_assignments:
                            test_weight = weights["Test"] / total_assignments["Test"]
                            all_remaining_grades.append(("Final", final_weight))
                            all_remaining_grades.append(("Test", test_weight / 2))  # Add half test weight
                        else:
                            all_remaining_grades.append(("Final", final_weight))
                    else:
                        all_remaining_grades.append(("Final", final_weight))
                else:
                    # Handle other categories normally
                    weight_per = weights[category] / effective_total
                    all_remaining_grades.extend([(category, weight_per) for _ in range(remaining)])

        if not all_remaining_grades:
            return {}

        # Check if only the Final is remaining
        if len(all_remaining_grades) == 1 and all_remaining_grades[0][0] == "Final":
            final_weight = all_remaining_grades[0][1]
            needed_grade = (target_grade - current_contribution) / final_weight
            if 0 <= needed_grade <= 100:
                return {"Final": [needed_grade]}
            else:
                raise ValueError("Cannot achieve the target grade with the remaining Final")
            
        # Group by category
        categories_needing_grades = []
        remaining_weights = []
        num_remaining = []
        
        # Group by category and collect weights
        current_category = None
        count = 0
        
        for category, weight in all_remaining_grades:
            if category != current_category:
                if current_category is not None:
                    categories_needing_grades.append(current_category)
                    num_remaining.append(count)
                current_category = category
                count = 1
            else:
                count += 1
            remaining_weights.append(weight)
            
        # Add the last category
        if current_category is not None:
            categories_needing_grades.append(current_category)
            num_remaining.append(count)

        remaining_weights = np.array(remaining_weights)
        print("\nCategories needing grades:", categories_needing_grades)
        print("Number of grades needed per category:", num_remaining)
        print("Remaining weights:", remaining_weights)
        print("Applying final policy:", apply_final_policy)

        # Set up optimization
        def objective(grades):
            category_penalties = []
            final_grade_index = None
            final_grade_penalty = 0
            for i, (category, _) in enumerate(all_remaining_grades):
                if category == "Final":
                    final_grade_index = i
                    break

            if final_grade_index is not None:
                final_grade = grades[final_grade_index]
                non_final_grades = np.delete(grades, final_grade_index)
                mean_non_final_grade = np.mean(non_final_grades)
                final_grade_penalty = 5 * (final_grade - mean_non_final_grade) ** 2
            for i, (category, weight) in enumerate(all_remaining_grades):
                grade = grades[i]
                penalty = np.sqrt((1 / weight) * (grade))
                category_penalties.append(penalty)

            variance = np.sum((grades - np.mean(grades)) ** 2)
            magnitude = np.mean(grades) * 10
            category_penalty = np.sum(category_penalties)

            return variance + magnitude + category_penalty + final_grade_penalty

        def constraint(grades):
            weighted_new = np.sum(grades * remaining_weights)
            needed = target_grade - current_contribution
            return weighted_new - needed

        # Optimize
        n_grades = len(remaining_weights)
        initial_guess = np.ones(n_grades) * target_grade
        bounds = [(0, 100)] * n_grades
        constraint_dict = {'type': 'eq', 'fun': constraint}
        
        result = minimize(
            objective,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraint_dict,
            options={'ftol': 1e-8, 'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError("Could not find a valid solution")
        
        grades = np.round(result.x, 2)
        if np.any(grades < 0) or np.any(grades > 100):
            raise ValueError("Required grades would be outside possible range")
        
        # Format results
        results = {}
        idx = 0
        for cat, num in zip(categories_needing_grades, num_remaining):
            results[cat] = list(grades[idx:idx+num])
            idx += num
        
        return results

    def save_boundaries(self):
        """Save grade boundaries for the current course"""
        if not self.current_course:
            QMessageBox.warning(self, "Error", "No course selected")
            return
            
        try:
            new_boundaries = {}
            for gpa, input_field in self.boundary_inputs.items():
                if not input_field.text().strip():
                    raise ValueError(f"Please enter a boundary for {gpa:.1f} GPA")
                    
                value = float(input_field.text())
                if value < 0 or value > 100:
                    raise ValueError(f"Grade boundary for {gpa:.1f} must be between 0 and 100")
                new_boundaries[gpa] = value
            
            # Verify boundaries are in descending order
            prev_value = 101
            for gpa in sorted(new_boundaries.keys(), reverse=True):
                if new_boundaries[gpa] >= prev_value:
                    raise ValueError("Grade boundaries must be in descending order")
                prev_value = new_boundaries[gpa]
            
            self.current_course.grade_boundaries = new_boundaries
            self.update_analysis()
            QMessageBox.information(self, "Success", "Grade boundaries saved")
            
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Invalid grade boundaries: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving grade boundaries: {str(e)}")

    def update_course_info(self):
        """Update course title, credit hours, and semester"""
        if not self.current_course:
            return
        
        # Update title
        new_title = self.course_title_input.text().strip()
        if new_title and new_title != self.current_course.name:
            old_name = self.current_course.name
            self.current_course.name = new_title
            
            # Update course combo
            index = self.course_combo.findText(old_name)
            if index >= 0:
                self.course_combo.setItemText(index, new_title)
                self.courses[new_title] = self.courses.pop(old_name)
        
        # Update credit hours
        try:
            hours_text = self.credit_hours_input.text().strip()
            if hours_text:
                hours = float(hours_text)
                if hours <= 0:
                    raise ValueError("Credit hours must be positive")
                self.current_course.credit_hours = hours
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        
        # Update semester
        new_semester = self.semester_input.text().strip()
        if new_semester and new_semester != self.current_course.semester:
            old_semester = self.current_course.semester
            self.current_course.semester = new_semester
            
            # Update semester dropdown if needed
            if self.semester_combo.findText(new_semester) == -1:
                self.semester_combo.addItem(new_semester)
                
                # Resort semesters
                semesters = [self.semester_combo.itemText(i) 
                            for i in range(self.semester_combo.count())]
                sorted_semesters = self.sort_semesters(semesters)
                
                self.semester_combo.clear()
                self.semester_combo.addItems(sorted_semesters)
            
            self.semester_combo.setCurrentText(new_semester)
        
        self.update_gpa()

    def update_final_policy(self, policy: str):
        """Update final exam policy for current course"""
        if self.current_course:
            self.current_course.final_policy = policy
            self.update_analysis()
            
    def setup_gpa_tab(self):
        """Set up the GPA calculation tab"""
        layout = QVBoxLayout(self.gpa_tab)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing
        
        # GPA Summary table
        self.gpa_table = QTableWidget()
        self.gpa_table.setColumnCount(5)
        self.gpa_table.setHorizontalHeaderLabels([
            "", "Course", "Credit Hours", "Current Grade", "GPA Points"
        ])
        
        # Make table stretch to fill window
        self.gpa_table.horizontalHeader().setStretchLastSection(True)
        self.gpa_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set proportional column widths
        header = self.gpa_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Indent column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Course name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Credit hours
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Current grade
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # GPA points
        
        # Set fixed column widths for non-stretching columns
        self.gpa_table.setColumnWidth(0, 50)  # Indent
        self.gpa_table.setColumnWidth(2, 100)  # Credit hours
        self.gpa_table.setColumnWidth(3, 100)  # Current grade
        self.gpa_table.setColumnWidth(4, 100)  # GPA points
        
        # Style the table
        self.gpa_table.setShowGrid(False)
        self.gpa_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QHeaderView::section {
                background-color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #666666;
            }
            QTableCornerButton::section {
                background-color: white;
                border: none;
            }
        """)
        
        # Hide the vertical header (row numbers)
        self.gpa_table.verticalHeader().setVisible(False)
        
        # Make the table read-only
        self.gpa_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.gpa_table)

    def update_gpa(self):
        """Update GPA display with semester grouping and GPAs"""
        self.gpa_table.setRowCount(0)
        semester_data = {}
        total_points = 0.0
        total_hours = 0.0

        # First, collect and sort all courses by semester
        for course_name, course in self.courses.items():
            semester = course.semester
            if semester not in semester_data:
                semester_data[semester] = {
                    'courses': [],
                    'total_points': 0.0,
                    'total_hours': 0.0
                }
            
            current_grade = course.calculate_current_grade()
            gpa_points = course.get_gpa_points(current_grade)
            
            semester_data[semester]['courses'].append({
                'name': course_name,
                'credit_hours': course.credit_hours,
                'current_grade': current_grade,
                'gpa_points': gpa_points
            })
            
            semester_data[semester]['total_points'] += gpa_points * course.credit_hours
            semester_data[semester]['total_hours'] += course.credit_hours
            
            total_points += gpa_points * course.credit_hours
            total_hours += course.credit_hours

        # Sort semesters chronologically
        sorted_semesters = self.sort_semesters(list(semester_data.keys()))

        # Create the display with semester grouping
        for semester in sorted_semesters:
            # Add semester header row with styling
            header_row = self.gpa_table.rowCount()
            self.gpa_table.insertRow(header_row)
            header_item = QTableWidgetItem(f"{semester}")
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Center semester header
            header_item.setBackground(QColor("#f8f9fa"))
            font = header_item.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            header_item.setFont(font)
            header_item.setForeground(QColor("#2196F3"))
            self.gpa_table.setItem(header_row, 0, header_item)
            
            # Merge cells for semester header
            self.gpa_table.setSpan(header_row, 0, 1, 5)
            self.gpa_table.setRowHeight(header_row, 50)

            # Add courses for this semester
            for course in semester_data[semester]['courses']:
                course_row = self.gpa_table.rowCount()
                self.gpa_table.insertRow(course_row)
                
                # Create items with centered alignment
                items = [
                    QTableWidgetItem(""),  # Empty first column for indentation
                    QTableWidgetItem(course['name']),
                    QTableWidgetItem(f"{course['credit_hours']:.1f}"),
                    QTableWidgetItem(f"{course['current_grade']:.2f}%"),
                    QTableWidgetItem(f"{course['gpa_points']:.2f}")
                ]
                
                # Center all items except course name (index 1)
                for col, item in enumerate(items):
                    if col != 1:  # Skip course name column
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    item.setBackground(QColor("white"))
                    self.gpa_table.setItem(course_row, col, item)

            # Add semester GPA
            if semester_data[semester]['total_hours'] > 0:
                semester_gpa = semester_data[semester]['total_points'] / semester_data[semester]['total_hours']
                
                spacing_row = self.gpa_table.rowCount()
                self.gpa_table.insertRow(spacing_row)
                self.gpa_table.setRowHeight(spacing_row, 20)
                
                gpa_row = self.gpa_table.rowCount()
                self.gpa_table.insertRow(gpa_row)
                
                gpa_item = QTableWidgetItem(f"Semester GPA: {semester_gpa:.2f}")
                gpa_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Center GPA
                gpa_item.setForeground(QColor("#1976D2"))
                font = gpa_item.font()
                font.setBold(True)
                font.setPointSize(font.pointSize() + 1)
                gpa_item.setFont(font)
                gpa_item.setBackground(QColor("#f8f9fa"))
                
                self.gpa_table.setItem(gpa_row, 0, gpa_item)
                self.gpa_table.setSpan(gpa_row, 0, 1, 5)
                self.gpa_table.setRowHeight(gpa_row, 40)
                
                if semester != sorted_semesters[-1]:
                    end_spacing_row = self.gpa_table.rowCount()
                    self.gpa_table.insertRow(end_spacing_row)
                    self.gpa_table.setRowHeight(end_spacing_row, 30)

        # Add overall GPA
        if total_hours > 0:
            overall_gpa = total_points / total_hours
            
            spacing_row = self.gpa_table.rowCount()
            self.gpa_table.insertRow(spacing_row)
            self.gpa_table.setRowHeight(spacing_row, 40)
            
            overall_row = self.gpa_table.rowCount()
            self.gpa_table.insertRow(overall_row)
            
            overall_item = QTableWidgetItem(f"Overall GPA: {overall_gpa:.2f}")
            overall_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Center overall GPA
            overall_item.setForeground(QColor("#1565C0"))
            overall_item.setBackground(QColor("#e3f2fd"))
            font = overall_item.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 2)
            overall_item.setFont(font)
            
            self.gpa_table.setItem(overall_row, 0, overall_item)
            self.gpa_table.setSpan(overall_row, 0, 1, 5)
            self.gpa_table.setRowHeight(overall_row, 50)

    def save_all_data(self):
        """Save all course and semester data"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save All Data", "courses_data.json", "JSON Files (*.json)")
        if filename:
            try:
                data = {
                    'semester': self.semester_input.text(),
                    'courses': {
                        name: course.to_dict() 
                        for name, course in self.courses.items()
                    }
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                QMessageBox.information(
                    self, "Success", 
                    f"All data saved to {filename}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Error saving data: {str(e)}"
                )

    def load_all_data(self):
        """Load all course and semester data"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load All Data", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Clear current data
                self.courses.clear()
                self.course_combo.clear()
                self.semester_combo.clear()
                self.current_course = None
                
                # Load courses
                for name, course_data in data['courses'].items():
                    self.courses[name] = Course.from_dict(course_data)
                
                # Collect all unique semesters
                semesters = set()
                for course in self.courses.values():
                    if hasattr(course, 'semester') and course.semester:
                        semesters.add(course.semester)
                
                # Sort and populate semester dropdown
                sorted_semesters = self.sort_semesters(list(semesters))
                self.semester_combo.addItems(sorted_semesters)
                
                # Set to latest semester
                if sorted_semesters:
                    latest_semester = sorted_semesters[-1]
                    self.semester_combo.setCurrentText(latest_semester)
                    self.populate_course_combo(latest_semester)
                    
                    # Select first course if available
                    if self.course_combo.count() > 0:
                        first_course = self.course_combo.itemText(0)
                        self.course_combo.setCurrentText(first_course)
                        self.change_current_course(first_course)
                
                self.update_gpa()
                
                # QMessageBox.information(
                #     self, "Success", 
                #     f"Data loaded from {filename}"
                # )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Error loading data: {str(e)}\n\n"
                    "Please ensure the file is a valid JSON format."
                )


    def sort_semesters(self, semesters):
        """Sort semesters chronologically"""
        def semester_key(sem):
            try:
                season, year = sem.split()
                # Assign numeric values to seasons for proper sorting
                season_values = {
                    'Winter': 0,
                    'Spring': 1,
                    'Summer': 2,
                    'Fall': 3
                }
                return int(year), season_values.get(season, 4)
            except:
                return (0, 0)  # Default value for invalid format
        
        return sorted(semesters, key=semester_key)

    def change_current_semester(self, semester: str):
        """Handle semester selection change"""
        if semester:
            # Update the semester input text box
            self.semester_input.setText(semester)
            
            # Update the course combo box
            self.populate_course_combo(semester)
            
            # Update current course if possible
            if self.course_combo.count() > 0:
                first_course = self.course_combo.itemText(0)
                self.course_combo.setCurrentText(first_course)
                self.change_current_course(first_course)

    def export_current_grades(self):
        """Export current grades to CSV"""
        if not self.courses:
            QMessageBox.warning(self, "Error", "No courses to export")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Grades", "current_grades.csv", "CSV Files (*.csv)")
        if filename:
            try:
                data = []
                for course_name, course in self.courses.items():
                    current_grade = course.calculate_current_grade()
                    gpa_points = course.get_gpa_points(current_grade)
                    
                    row = {
                        'Course': course_name,
                        'Credit_Hours': course.credit_hours,
                        'Current_Grade': f"{current_grade:.2f}%",
                        'GPA_Points': gpa_points
                    }
                    
                    # Add category grades
                    for cat_name, category in course.categories.items():
                        if category.grades:
                            avg = course.calculate_category_average(cat_name)
                            row[f"{cat_name}_Average"] = f"{avg:.2f}%"
                            row[f"{cat_name}_Completed"] = f"{len(category.grades)}/{category.total_assignments}"
                    
                    data.append(row)
                
                df = pd.DataFrame(data)
                df.to_csv(filename, index=False)
                
                QMessageBox.information(
                    self, "Success", 
                    f"Grades exported to {filename}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Error exporting grades: {str(e)}"
                )

    def show_error(self, message: str):
        """Show an error message to the user"""
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """Handle application closing"""
        reply = QMessageBox.question(
            self, "Save Data",
            "Would you like to save your data before closing?",
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No | 
            QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.save_all_data()
            event.accept()
        elif reply == QMessageBox.StandardButton.No:
            event.accept()
        else:
            event.ignore()
            
    def update_gpa_table(self, df: pd.DataFrame):
        """Update GPA table from loaded data"""
        self.gpa_table.setRowCount(0)
        
        total_points = 0.0
        total_hours = 0.0
        
        for _, row in df.iterrows():
            table_row = self.gpa_table.rowCount()
            self.gpa_table.insertRow(table_row)
            
            self.gpa_table.setItem(table_row, 0, QTableWidgetItem(row['Course']))
            self.gpa_table.setItem(table_row, 1, QTableWidgetItem(f"{row['Credit_Hours']:.1f}"))
            self.gpa_table.setItem(table_row, 2, QTableWidgetItem(f"{row['Grade']:.2f}%"))
            self.gpa_table.setItem(table_row, 3, QTableWidgetItem(f"{row['GPA_Points']:.2f}"))
            
            total_points += row['GPA_Points'] * row['Credit_Hours']
            total_hours += row['Credit_Hours']
        
        if total_hours > 0:
            semester_gpa = total_points / total_hours
            self.semester_gpa_label.setText(f"Semester GPA: {semester_gpa:.2f}")
        else:
            self.semester_gpa_label.setText("Semester GPA: N/A")

    def validate_course_setup(self) -> bool:
        """Validate that the current course is properly set up"""
        if not self.current_course:
            self.show_error("No course selected")
            return False
            
        if not self.current_course.grade_boundaries:
            self.show_error("Please set up grade boundaries first")
            return False
            
        if not self.current_course.categories:
            self.show_error("Please add at least one category first")
            return False
            
        total_weight = sum(cat.weight for cat in self.current_course.categories.values())
        if abs(total_weight - 100) > 0.01:
            self.show_error("Category weights must sum to 100%")
            return False
            
        return True

    def get_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_semester = file_menu.addAction('New Semester')
        new_semester.triggered.connect(self.new_semester)
        
        save_action = file_menu.addAction('Save All')
        save_action.triggered.connect(self.save_all_data)
        
        load_action = file_menu.addAction('Load All')
        load_action.triggered.connect(self.load_all_data)
        
        export_action = file_menu.addAction('Export Grades')
        export_action.triggered.connect(self.export_current_grades)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        
        return menubar

    def new_semester(self):
        """Start a new semester"""
        if self.courses:
            reply = QMessageBox.question(
                self, "New Semester",
                "This will clear all current courses. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.courses.clear()
        self.course_combo.clear()
        self.current_course = None
        self.semester_input.clear()
        self.clear_course_display()
        self.update_gpa()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About GPA Calculator",
            "GPA Calculator v1.0\n\n"
            "A comprehensive tool for tracking course grades "
            "and calculating semester GPA.\n\n"
            "Features:\n"
            "- Multiple course management\n"
            "- Weighted grade categories\n"
            "- Grade dropping\n"
            "- Final exam policies\n"
            "- GPA calculation\n"
            "- Data import/export"
        )
        
def main():
    app = QApplication(sys.argv)
    window = GPACalculator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()