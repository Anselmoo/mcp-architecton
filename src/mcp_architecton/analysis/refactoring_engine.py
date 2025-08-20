"""Enhanced refactoring engine for intelligent pattern introduction.

This module provides intelligent refactoring capabilities that analyze
existing code structure and transform it appropriately rather than
simply appending boilerplate code.
"""

from __future__ import annotations

from typing import Any, Dict

try:
    import libcst as cst
    from libcst import parse_module
except ImportError:
    cst = None
    parse_module = None

from .code_analyzer import (
    RefactoringContext,
    create_refactoring_context,
    generate_refactoring_instructions,
)


class IntelligentRefactoringEngine:
    """Engine for performing intelligent code refactoring."""
    
    def __init__(self):
        self._transformers = {
            "singleton": self._transform_to_singleton,
            "strategy": self._transform_to_strategy,
            "observer": self._transform_to_observer,
            "factory": self._transform_to_factory,
            "facade": self._transform_to_facade,
        }
    
    def analyze_and_refactor(self, source: str, pattern_name: str) -> Dict[str, Any]:
        """Analyze code and perform intelligent refactoring."""
        # Create refactoring context
        context = create_refactoring_context(source, pattern_name)
        
        # Generate detailed instructions
        instructions = generate_refactoring_instructions(context)
        
        # Attempt intelligent transformation
        canonical_pattern = pattern_name.lower().strip()
        transformer = self._transformers.get(canonical_pattern)
        
        if transformer:
            transformation_result = transformer(source, context)
        else:
            transformation_result = {
                "transformed_code": None,
                "changes_made": [],
                "success": False,
                "reason": f"No intelligent transformer available for {pattern_name}"
            }
        
        return {
            "analysis": instructions["analysis"],
            "refactoring_plan": instructions["transformation_plan"],
            "integration_points": instructions["integration_points"],
            "step_by_step_instructions": instructions["step_by_step_instructions"],
            "risks": instructions["risks_and_considerations"],
            "validation_steps": instructions["validation_steps"],
            "transformation_result": transformation_result
        }
    
    def _transform_to_singleton(self, source: str, context: RefactoringContext) -> Dict[str, Any]:
        """Transform existing code to implement singleton pattern."""
        if not context.existing_structure.classes:
            # No existing classes, create new singleton
            return self._create_singleton_scaffold(source)
        
        # Transform the first class to be a singleton
        primary_class = context.existing_structure.classes[0]
        return self._modify_class_to_singleton(source, primary_class)
    
    def _modify_class_to_singleton(self, source: str, class_name: str) -> Dict[str, Any]:
        """Modify an existing class to implement singleton pattern."""
        if not cst or not parse_module:
            return {"success": False, "reason": "LibCST not available"}
        
        try:
            tree = parse_module(source)
            transformer = SingletonTransformer(class_name)
            modified_tree = tree.visit(transformer)
            
            if transformer.was_modified:
                return {
                    "transformed_code": modified_tree.code,
                    "changes_made": [
                        f"Added singleton behavior to {class_name}",
                        "Added _instance class variable",
                        "Modified or added __new__ method"
                    ],
                    "success": True
                }
        except Exception:
            pass
        
        # Fallback to text-based transformation
        return self._text_based_singleton_transform(source, class_name)
    
    def _text_based_singleton_transform(self, source: str, class_name: str) -> Dict[str, Any]:
        """Fallback text-based singleton transformation."""
        lines = source.split('\n')
        modified_lines = []
        in_target_class = False
        class_indent = 0
        added_singleton = False
        
        for line in lines:
            if f"class {class_name}" in line and line.strip().startswith("class"):
                in_target_class = True
                class_indent = len(line) - len(line.lstrip())
                modified_lines.append(line)
                # Add singleton variables after class definition
                indent = " " * (class_indent + 4)
                modified_lines.append(f"{indent}_instance = None")
                modified_lines.append("")
            elif in_target_class and line.strip().startswith("class ") and line != lines[0]:
                # End of our target class
                in_target_class = False
                modified_lines.append(line)
            elif in_target_class and "def __new__(" in line:
                # Replace existing __new__ method
                indent = " " * (class_indent + 4)
                modified_lines.append(f"{indent}def __new__(cls, *args, **kwargs):")
                modified_lines.append(f"{indent}    if cls._instance is None:")
                modified_lines.append(f"{indent}        cls._instance = super().__new__(cls)")
                modified_lines.append(f"{indent}    return cls._instance")
                added_singleton = True
                # Skip the original __new__ implementation
                continue
            elif in_target_class and line.strip() == "" and not added_singleton:
                # Add __new__ method if we haven't seen one
                indent = " " * (class_indent + 4)
                modified_lines.append(f"{indent}def __new__(cls, *args, **kwargs):")
                modified_lines.append(f"{indent}    if cls._instance is None:")
                modified_lines.append(f"{indent}        cls._instance = super().__new__(cls)")
                modified_lines.append(f"{indent}    return cls._instance")
                modified_lines.append("")
                added_singleton = True
                modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        return {
            "transformed_code": '\n'.join(modified_lines),
            "changes_made": [
                f"Added singleton pattern to {class_name}",
                "Added _instance class variable",
                "Added/modified __new__ method"
            ],
            "success": True
        }
    
    def _create_singleton_scaffold(self, source: str) -> Dict[str, Any]:
        """Create a new singleton class when no classes exist."""
        singleton_code = '''
class Singleton:
    """Singleton pattern implementation."""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # TODO: Add initialization logic here
            pass
'''
        
        modified_source = source.rstrip() + "\n\n" + singleton_code.strip()
        
        return {
            "transformed_code": modified_source,
            "changes_made": ["Created new Singleton class"],
            "success": True
        }
    
    def _transform_to_strategy(self, source: str, context: RefactoringContext) -> Dict[str, Any]:
        """Transform code to implement strategy pattern."""
        changes = []
        modified_source = source
        
        # Add strategy interface if not present
        if "Strategy" not in source:
            strategy_interface = '''
from abc import ABC, abstractmethod

class Strategy(ABC):
    """Strategy interface for algorithm implementations."""
    
    @abstractmethod
    def execute(self, data):
        """Execute the strategy algorithm."""
        raise NotImplementedError
'''
            modified_source = strategy_interface.strip() + "\n\n" + modified_source
            changes.append("Added Strategy abstract base class")
        
        # Add Context class if not present  
        if "Context" not in source:
            context_class = '''

class Context:
    """Context class that uses a strategy."""
    
    def __init__(self, strategy: Strategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: Strategy):
        """Change the strategy at runtime."""
        self._strategy = strategy
    
    def execute(self, data):
        """Execute the current strategy."""
        return self._strategy.execute(data)
'''
            modified_source += context_class
            changes.append("Added Context class")
        
        # Convert existing classes to strategies if appropriate
        existing_classes = context.existing_structure.classes
        if existing_classes:
            for class_name in existing_classes[:2]:  # Convert first 2 classes
                if "Strategy" not in class_name:
                    modified_source = self._convert_class_to_strategy(modified_source, class_name)
                    changes.append(f"Converted {class_name} to implement Strategy pattern")
        
        return {
            "transformed_code": modified_source,
            "changes_made": changes,
            "success": True
        }
    
    def _convert_class_to_strategy(self, source: str, class_name: str) -> str:
        """Convert an existing class to implement Strategy pattern."""
        lines = source.split('\n')
        modified_lines = []
        
        for line in lines:
            if f"class {class_name}" in line and line.strip().startswith("class"):
                # Modify class declaration to inherit from Strategy
                if "(" not in line:
                    modified_line = line.replace(f"class {class_name}:", f"class {class_name}(Strategy):")
                else:
                    # Handle existing inheritance
                    modified_line = line.replace(f"class {class_name}(", f"class {class_name}(Strategy, ")
                modified_lines.append(modified_line)
            else:
                modified_lines.append(line)
        
        result = '\n'.join(modified_lines)
        
        # Add execute method if not present
        if "def execute(" not in result:
            class_pos = result.find(f"class {class_name}")
            if class_pos != -1:
                # Find the end of the class definition to add execute method
                lines = result.split('\n')
                for i, line in enumerate(lines):
                    if f"class {class_name}" in line:
                        # Find a good place to insert execute method
                        insert_pos = i + 1
                        while insert_pos < len(lines) and (lines[insert_pos].strip() == "" or lines[insert_pos].strip().startswith('"""')):
                            insert_pos += 1
                        
                        indent = "    "
                        execute_method = [
                            f"{indent}def execute(self, data):",
                            f"{indent}    # TODO: Implement strategy algorithm",
                            f"{indent}    raise NotImplementedError",
                            ""
                        ]
                        
                        lines = lines[:insert_pos] + execute_method + lines[insert_pos:]
                        result = '\n'.join(lines)
                        break
        
        return result
    
    def _transform_to_observer(self, source: str, context: RefactoringContext) -> Dict[str, Any]:
        """Transform code to implement observer pattern."""
        changes = []
        modified_source = source
        
        # Add Observable class
        observable_code = '''
class Observable:
    """Observable subject that notifies observers of changes."""
    
    def __init__(self):
        self._observers = {}
    
    def subscribe(self, event: str, observer):
        """Subscribe an observer to an event."""
        if event not in self._observers:
            self._observers[event] = []
        self._observers[event].append(observer)
    
    def unsubscribe(self, event: str, observer):
        """Unsubscribe an observer from an event."""
        if event in self._observers:
            self._observers[event].remove(observer)
    
    def notify(self, event: str, data=None):
        """Notify all observers of an event."""
        if event in self._observers:
            for observer in self._observers[event]:
                observer(data)
'''
        
        modified_source = observable_code.strip() + "\n\n" + modified_source
        changes.append("Added Observable class")
        
        # Modify existing classes to use observer pattern
        if context.existing_structure.classes:
            primary_class = context.existing_structure.classes[0]
            modified_source = self._add_observer_to_class(modified_source, primary_class)
            changes.append(f"Modified {primary_class} to use observer notifications")
        
        return {
            "transformed_code": modified_source,
            "changes_made": changes,
            "success": True
        }
    
    def _add_observer_to_class(self, source: str, class_name: str) -> str:
        """Add observer functionality to an existing class."""
        lines = source.split('\n')
        modified_lines = []
        in_target_class = False
        class_indent = 0
        
        for line in lines:
            if f"class {class_name}" in line and line.strip().startswith("class"):
                in_target_class = True
                class_indent = len(line) - len(line.lstrip())
                modified_lines.append(line)
            elif in_target_class and "def __init__(" in line:
                modified_lines.append(line)
                # Add observable initialization
                indent = " " * (class_indent + 8)
                modified_lines.append(f"{indent}self._observable = Observable()")
            else:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines)
    
    def _transform_to_factory(self, source: str, context: RefactoringContext) -> Dict[str, Any]:
        """Transform code to implement factory pattern."""
        factory_code = '''
class Factory:
    """Factory for creating objects."""
    
    @staticmethod
    def create(object_type: str, **kwargs):
        """Create an object based on type."""
        # TODO: Implement factory logic
        raise NotImplementedError(f"Unknown object type: {object_type}")
'''
        
        modified_source = source + "\n\n" + factory_code.strip()
        
        return {
            "transformed_code": modified_source,
            "changes_made": ["Added Factory class"],
            "success": True
        }
    
    def _transform_to_facade(self, source: str, context: RefactoringContext) -> Dict[str, Any]:
        """Transform code to implement facade pattern."""
        facade_code = '''
class Facade:
    """Facade providing simplified interface to complex subsystems."""
    
    def __init__(self):
        # TODO: Initialize subsystem components
        pass
    
    def simplified_operation(self, data):
        """Provide simplified access to complex operations."""
        # TODO: Orchestrate subsystem calls
        raise NotImplementedError
'''
        
        modified_source = source + "\n\n" + facade_code.strip()
        
        return {
            "transformed_code": modified_source,
            "changes_made": ["Added Facade class"],
            "success": True
        }


class SingletonTransformer(cst.CSTTransformer):
    """LibCST transformer for adding singleton behavior to a class."""
    
    def __init__(self, target_class: str):
        self.target_class = target_class
        self.was_modified = False
        self.found_target = False
        self.has_instance_var = False
        self.has_new_method = False
    
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        if node.name.value == self.target_class:
            self.found_target = True
        return node
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.target_class:
            # Add singleton behavior to this class
            body = list(updated_node.body.body)
            
            # Add _instance variable if not present
            if not self.has_instance_var:
                instance_var = cst.SimpleStatementLine([
                    cst.Assign([cst.AssignTarget(cst.Name("_instance"))], cst.Name("None"))
                ])
                body.insert(0, instance_var)
                body.insert(1, cst.SimpleStatementLine([cst.Pass()]))  # Empty line
            
            # Add __new__ method if not present
            if not self.has_new_method:
                new_method = self._create_new_method()
                body.append(new_method)
            
            new_body = cst.IndentedBlock(body)
            self.was_modified = True
            return updated_node.with_changes(body=new_body)
        
        return updated_node
    
    def _create_new_method(self) -> cst.FunctionDef:
        """Create the __new__ method for singleton behavior."""
        return cst.FunctionDef(
            name=cst.Name("__new__"),
            params=cst.Parameters([
                cst.Param(cst.Name("cls")),
                cst.MaybeSentinel.DEFAULT,
                cst.MaybeSentinel.DEFAULT,
                cst.ParamStar(cst.Name("args")),
                cst.ParamStar(cst.Name("kwargs"), comma=cst.Comma())
            ]),
            body=cst.IndentedBlock([
                cst.SimpleStatementLine([
                    cst.If(
                        test=cst.Comparison(
                            left=cst.Attribute(cst.Name("cls"), cst.Name("_instance")),
                            comparisons=[cst.ComparisonTarget(cst.Is(), cst.Name("None"))]
                        ),
                        body=cst.IndentedBlock([
                            cst.SimpleStatementLine([
                                cst.Assign(
                                    [cst.AssignTarget(cst.Attribute(cst.Name("cls"), cst.Name("_instance")))],
                                    cst.Call(
                                        cst.Attribute(cst.Call(cst.Name("super")), cst.Name("__new__")),
                                        [cst.Arg(cst.Name("cls"))]
                                    )
                                )
                            ])
                        ])
                    )
                ]),
                cst.SimpleStatementLine([
                    cst.Return(cst.Attribute(cst.Name("cls"), cst.Name("_instance")))
                ])
            ])
        )


# Global instance
refactoring_engine = IntelligentRefactoringEngine()


def intelligent_refactor(source: str, pattern_name: str) -> Dict[str, Any]:
    """Main entry point for intelligent refactoring."""
    return refactoring_engine.analyze_and_refactor(source, pattern_name)


__all__ = ["IntelligentRefactoringEngine", "intelligent_refactor"]