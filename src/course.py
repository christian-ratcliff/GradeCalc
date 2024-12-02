from typing import Dict, List
from .grade_category import GradeCategory

class Course:
    def __init__(self, name: str, credit_hours: float = 3.0):
        self.name = name
        self.credit_hours = float(credit_hours)
        self.categories: Dict[str, GradeCategory] = {}
        self.grade_boundaries: Dict[float, float] = {}
        self.semester = ""  # Initialize empty semester
        self.final_policy = "No Replacement"
        
    def to_dict(self) -> dict:
        """Convert course to dictionary for saving"""
        return {
            'name': self.name,
            'credit_hours': float(self.credit_hours),
            'semester': self.semester,  # Include semester in serialization
            'categories': {name: cat.to_dict() for name, cat in self.categories.items()},
            'grade_boundaries': {float(k): float(v) for k, v in self.grade_boundaries.items()},
            'final_policy': self.final_policy
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Course':
        """Create course from dictionary data"""
        course = cls(
            name=data['name'],
            credit_hours=float(data['credit_hours'])
        )
        course.semester = data['semester']  # Set semester from loaded data
        course.grade_boundaries = {float(k): float(v) for k, v in data['grade_boundaries'].items()}
        course.final_policy = data['final_policy']
        
        # Restore categories
        for name, cat_data in data['categories'].items():
            course.categories[name] = GradeCategory.from_dict(cat_data)
            
        return course
        
    def calculate_category_average(self, category_name: str) -> float:
        """Calculate the average for a specific category considering drops"""
        category = self.categories.get(category_name)
        if not category or not category.grades:
            return 0.0
            
        grades = [float(g) for g in sorted(category.grades)]  # Ensure float
        
        # Apply drops
        if category.drops > 0:
            grades = grades[category.drops:]
            
        # Handle final exam replacement if applicable
        if (category_name == "Test" and "Final" in self.categories and 
            self.final_policy != "No Replacement"):
            final_grades = [float(g) for g in self.categories["Final"].grades]  # Ensure float
            if final_grades:
                final_grade = final_grades[0]
                
                if self.final_policy == "Replace Lowest Test":
                    if grades and final_grade > grades[0]:
                        grades[0] = final_grade
                elif self.final_policy == "Average with Lowest Test":
                    if grades:
                        grades[0] = (grades[0] + final_grade) / 2
                        
        return sum(grades) / len(grades) if grades else 0.0
        
    def calculate_current_grade(self) -> float:
        """Calculate the current weighted grade for the course"""
        total_weighted_score = 0.0
        total_weight_used = 0.0
        
        for name, category in self.categories.items():
            if category.grades:
                average = float(self.calculate_category_average(name))
                weight = float(category.weight) / 100.0
                total_weighted_score += average * weight
                total_weight_used += weight
                
        if total_weight_used > 0:
            return total_weighted_score / total_weight_used
        return 0.0
        
    def get_gpa_points(self, percentage: float) -> float:
        """Convert percentage grade to GPA points based on boundaries"""
        if not self.grade_boundaries:
            return 0.0
            
        percentage = float(percentage)  # Ensure float
        for gpa, minimum in sorted(
            ((float(k), float(v)) for k, v in self.grade_boundaries.items()),
            reverse=True
        ):
            if percentage >= minimum:
                return float(gpa)
        return 0.0