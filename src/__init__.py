"""
GPA Calculator Package
A PyQt6-based application for calculating and tracking course grades and GPA.
"""

from src.course import Course
from src.grade_category import GradeCategory
from src.main import GPACalculator

__version__ = '1.0.0'
__author__ = 'Christian Ratcliff'

# Export the main classes
__all__ = [
    'Course',
    'GradeCategory',
    'GPACalculator'
]