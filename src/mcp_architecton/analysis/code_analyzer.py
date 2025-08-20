"""Enhanced code analyzer for intelligent refactoring.

This module provides sophisticated analysis of existing code structure
to enable intelligent refactoring suggestions rather than blind pattern
appending. It identifies existing patterns, code structure, and
refactoring opportunities.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..detectors import registry as detector_registry
from .ast_utils import analyze_code_for_patterns, astroid_summary


@dataclass
class CodeStructure:
    """Represents the structural analysis of a code file."""
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    complexity_indicators: Dict[str, Any] = field(default_factory=dict)
    refactoring_opportunities: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RefactoringContext:
    """Context information for intelligent refactoring."""
    target_pattern: str
    existing_structure: CodeStructure
    transformation_plan: List[Dict[str, Any]] = field(default_factory=list)
    integration_points: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


def analyze_code_structure(source: str) -> CodeStructure:
    """Analyze code structure to understand existing patterns and components."""
    structure = CodeStructure()
    
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return structure
    
    # Extract basic structure
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            structure.classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            structure.functions.append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    structure.imports.append(alias.name)
            else:
                module = node.module or ""
                for alias in node.names:
                    structure.imports.append(f"{module}.{alias.name}")
    
    # Analyze existing patterns
    structure.patterns = analyze_code_for_patterns(source, detector_registry)
    
    # Get additional context from astroid
    ast_summary = astroid_summary(source)
    if "error" not in ast_summary:
        # Merge astroid insights
        structure.functions.extend([f for f in ast_summary.get("functions", []) 
                                   if f not in structure.functions])
    
    # Analyze complexity indicators
    structure.complexity_indicators = _analyze_complexity(tree, source)
    
    # Identify refactoring opportunities
    structure.refactoring_opportunities = _identify_opportunities(tree, source, structure)
    
    return structure


def _analyze_complexity(tree: ast.AST, source: str) -> Dict[str, Any]:
    """Analyze code complexity indicators."""
    indicators = {
        "cyclomatic_complexity": 0,
        "nesting_depth": 0,
        "function_length": {},
        "class_size": {},
        "parameter_count": {}
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Function length (lines)
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                indicators["function_length"][node.name] = length
            
            # Parameter count
            indicators["parameter_count"][node.name] = len(node.args.args)
            
            # Cyclomatic complexity (simplified)
            complexity = _calculate_cyclomatic_complexity(node)
            indicators["cyclomatic_complexity"] = max(
                indicators["cyclomatic_complexity"], complexity
            )
        
        elif isinstance(node, ast.ClassDef):
            # Class size (number of methods)
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            indicators["class_size"][node.name] = len(methods)
    
    return indicators


def _calculate_cyclomatic_complexity(node: ast.FunctionDef) -> int:
    """Calculate simplified cyclomatic complexity for a function."""
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.Try):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.With):
            complexity += 1
    
    return complexity


def _identify_opportunities(tree: ast.AST, source: str, structure: CodeStructure) -> List[Dict[str, Any]]:
    """Identify specific refactoring opportunities in the code."""
    opportunities = []
    
    # Look for long parameter lists (potential for parameter object pattern)
    for func_name, param_count in structure.complexity_indicators.get("parameter_count", {}).items():
        if param_count > 4:
            opportunities.append({
                "type": "parameter_object",
                "target": func_name,
                "reason": f"Function has {param_count} parameters, consider parameter object pattern",
                "confidence": 0.7
            })
    
    # Look for large classes (potential for decomposition)
    for class_name, method_count in structure.complexity_indicators.get("class_size", {}).items():
        if method_count > 10:
            opportunities.append({
                "type": "class_decomposition", 
                "target": class_name,
                "reason": f"Class has {method_count} methods, consider splitting responsibilities",
                "confidence": 0.6
            })
    
    # Look for complex functions (potential for strategy pattern)
    for func_name, length in structure.complexity_indicators.get("function_length", {}).items():
        if length > 20:
            opportunities.append({
                "type": "function_decomposition",
                "target": func_name,
                "reason": f"Function is {length} lines long, consider extracting strategies",
                "confidence": 0.5
            })
    
    # Look for repeated patterns that could benefit from specific design patterns
    _identify_pattern_opportunities(tree, opportunities)
    
    return opportunities


def _identify_pattern_opportunities(tree: ast.AST, opportunities: List[Dict[str, Any]]) -> None:
    """Identify opportunities for specific design patterns."""
    # Look for factory method opportunities (multiple constructors)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            static_methods = [n for n in node.body 
                            if isinstance(n, ast.FunctionDef) and 
                            any(isinstance(d, ast.Name) and d.id == "staticmethod" 
                                for d in n.decorator_list)]
            
            if len(static_methods) > 2:
                opportunities.append({
                    "type": "factory_method",
                    "target": node.name,
                    "reason": f"Class has {len(static_methods)} static methods, consider factory pattern",
                    "confidence": 0.6
                })
    
    # Look for observer pattern opportunities (callback patterns)
    callback_patterns = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Look for callback-style parameters
            for arg in node.args.args:
                if "callback" in arg.arg.lower() or "handler" in arg.arg.lower():
                    callback_patterns += 1
    
    if callback_patterns > 2:
        opportunities.append({
            "type": "observer",
            "target": "module",
            "reason": f"Found {callback_patterns} callback patterns, consider observer pattern",
            "confidence": 0.5
        })


def create_refactoring_context(source: str, target_pattern: str) -> RefactoringContext:
    """Create comprehensive refactoring context for intelligent transformation."""
    structure = analyze_code_structure(source)
    context = RefactoringContext(
        target_pattern=target_pattern,
        existing_structure=structure
    )
    
    # Generate transformation plan
    context.transformation_plan = _generate_transformation_plan(structure, target_pattern)
    
    # Identify integration points
    context.integration_points = _identify_integration_points(structure, target_pattern)
    
    # Assess risks
    context.risks = _assess_refactoring_risks(structure, target_pattern)
    
    return context


def _generate_transformation_plan(structure: CodeStructure, target_pattern: str) -> List[Dict[str, Any]]:
    """Generate step-by-step transformation plan for the target pattern."""
    plan = []
    canonical_pattern = target_pattern.lower().strip()
    
    if canonical_pattern == "singleton":
        if structure.classes:
            # Transform existing class to singleton
            primary_class = structure.classes[0]
            plan.append({
                "step": 1,
                "action": "modify_class",
                "target": primary_class,
                "description": f"Add singleton behavior to existing class {primary_class}",
                "details": "Add _instance class variable and modify __new__ method"
            })
        else:
            plan.append({
                "step": 1,
                "action": "create_class",
                "target": "Singleton", 
                "description": "Create new singleton class",
                "details": "Add complete singleton implementation"
            })
    
    elif canonical_pattern == "strategy":
        if structure.classes:
            # Look for classes that could become strategies
            plan.append({
                "step": 1,
                "action": "extract_interface",
                "target": "Strategy",
                "description": "Extract common strategy interface",
                "details": "Create abstract Strategy base class"
            })
            
            for i, class_name in enumerate(structure.classes[:3]):  # Limit to first 3
                plan.append({
                    "step": i + 2,
                    "action": "convert_to_strategy",
                    "target": class_name,
                    "description": f"Convert {class_name} to implement Strategy",
                    "details": f"Make {class_name} inherit from Strategy and implement execute method"
                })
        
        plan.append({
            "step": len(plan) + 1,
            "action": "create_context",
            "target": "Context",
            "description": "Create context class to use strategies",
            "details": "Add Context class with strategy composition"
        })
    
    elif canonical_pattern == "observer":
        plan.append({
            "step": 1,
            "action": "create_subject",
            "target": "Observable",
            "description": "Create observable subject class",
            "details": "Add subscription and notification methods"
        })
        
        if structure.classes:
            plan.append({
                "step": 2,
                "action": "modify_existing",
                "target": structure.classes[0],
                "description": f"Integrate {structure.classes[0]} with observer pattern",
                "details": "Add observer notification to existing class methods"
            })
    
    return plan


def _identify_integration_points(structure: CodeStructure, target_pattern: str) -> List[Dict[str, Any]]:
    """Identify where the new pattern should integrate with existing code."""
    integration_points = []
    canonical_pattern = target_pattern.lower().strip()
    
    # Find existing methods that should trigger pattern behavior
    if canonical_pattern == "observer" and structure.functions:
        for func in structure.functions:
            if any(keyword in func.lower() for keyword in ["update", "change", "set", "modify"]):
                integration_points.append({
                    "type": "notification_point",
                    "target": func,
                    "description": f"Add observer notification to {func}",
                    "reason": "Method name suggests state change"
                })
    
    elif canonical_pattern == "strategy" and structure.functions:
        for func in structure.functions:
            if any(keyword in func.lower() for keyword in ["process", "execute", "handle", "calculate"]):
                integration_points.append({
                    "type": "strategy_point",
                    "target": func,
                    "description": f"Replace {func} with strategy pattern",
                    "reason": "Method suggests algorithmic behavior"
                })
    
    return integration_points


def _assess_refactoring_risks(structure: CodeStructure, target_pattern: str) -> List[str]:
    """Assess potential risks of the refactoring."""
    risks = []
    
    if len(structure.classes) == 0 and len(structure.functions) == 0:
        risks.append("Empty or minimal code - pattern introduction may be premature")
    
    if len(structure.classes) > 5:
        risks.append("Complex class hierarchy - pattern introduction may increase complexity")
    
    complex_funcs = [name for name, length in 
                    structure.complexity_indicators.get("function_length", {}).items() 
                    if length > 30]
    if complex_funcs:
        risks.append(f"Complex functions detected: {', '.join(complex_funcs)} - may need refactoring first")
    
    if len(structure.patterns) > 3:
        risks.append("Multiple patterns already detected - adding more may create over-engineering")
    
    return risks


def generate_refactoring_instructions(context: RefactoringContext) -> Dict[str, Any]:
    """Generate detailed, step-by-step refactoring instructions for LLMs."""
    instructions = {
        "pattern": context.target_pattern,
        "analysis": {
            "existing_structure": {
                "classes": context.existing_structure.classes,
                "functions": context.existing_structure.functions,
                "detected_patterns": [p.get("name", "") for p in context.existing_structure.patterns]
            },
            "opportunities": context.existing_structure.refactoring_opportunities,
            "complexity": context.existing_structure.complexity_indicators
        },
        "transformation_plan": context.transformation_plan,
        "integration_points": context.integration_points,
        "step_by_step_instructions": [],
        "risks_and_considerations": context.risks,
        "validation_steps": []
    }
    
    # Generate detailed step-by-step instructions
    for i, step in enumerate(context.transformation_plan, 1):
        instruction = {
            "step": i,
            "action": step["action"],
            "description": step["description"],
            "code_changes": _generate_code_changes(step, context),
            "validation": f"Verify {step['target']} works correctly after changes"
        }
        instructions["step_by_step_instructions"].append(instruction)
    
    # Add validation steps
    instructions["validation_steps"] = [
        "Run existing tests to ensure no regression",
        f"Verify {context.target_pattern} pattern is correctly implemented",
        "Check that existing functionality is preserved",
        "Validate that new pattern integrates smoothly with existing code"
    ]
    
    return instructions


def _generate_code_changes(step: Dict[str, Any], context: RefactoringContext) -> Dict[str, str]:
    """Generate specific code changes for a transformation step."""
    changes = {}
    
    action = step["action"]
    target = step["target"]
    
    if action == "modify_class" and context.target_pattern.lower() == "singleton":
        changes["before"] = f"class {target}:"
        changes["after"] = f"""class {target}:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance"""
        changes["description"] = "Add singleton behavior to existing class"
    
    elif action == "create_class":
        changes["before"] = "# No class exists"
        changes["after"] = f"class {target}:\n    pass  # TODO: Implement pattern"
        changes["description"] = f"Create new {target} class"
    
    elif action == "extract_interface":
        changes["before"] = "# No common interface"
        changes["after"] = """from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def execute(self, data):
        raise NotImplementedError"""
        changes["description"] = "Extract common strategy interface"
    
    return changes


__all__ = [
    "CodeStructure",
    "RefactoringContext", 
    "analyze_code_structure",
    "create_refactoring_context",
    "generate_refactoring_instructions"
]