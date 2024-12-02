from typing import List

class GradeCategory:
    def __init__(self, name: str, weight: float, total_assignments: int = 0, drops: int = 0):
        self.name = name
        self.weight = float(weight)  # Ensure float
        self.total_assignments = int(total_assignments)  # Ensure int
        self.drops = int(drops)  # Ensure int
        self.grades: List[float] = []
        
    def to_dict(self) -> dict:
        """Convert category to dictionary for saving"""
        return {
            'name': self.name,
            'weight': float(self.weight),  # Ensure float
            'total_assignments': int(self.total_assignments),  # Ensure int
            'drops': int(self.drops),  # Ensure int
            'grades': [float(g) for g in self.grades]  # Ensure float
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GradeCategory':
        """Create category from dictionary data"""
        category = cls(
            name=data['name'],
            weight=float(data['weight']),  # Ensure float
            total_assignments=int(data['total_assignments']),  # Ensure int
            drops=int(data['drops'])  # Ensure int
        )
        category.grades = [float(g) for g in data['grades']]  # Ensure float
        return category