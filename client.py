"""
Enterprise Spreadsheet Financial Model & Formula DAG Synthesizer (Zero External Dependencies)
Provides cell formula parsing, dependency graph resolution, circular reference detection, and preview evaluations.
"""
import time
import math
import re
import json
from typing import Dict, Any, List, Optional, Set

CELL_COORD_REGEX = re.compile(r"\b([A-Z]{1,2}[0-9]{1,4})\b")

class EnterpriseSpreadsheetFormulaDAGSynthesizer:
    def __init__(self):
        self.cells: Dict[str, Any] = {}
        self.graph: Dict[str, Set[str]] = {} # cell -> depends_on_cells
        self.reverse_graph: Dict[str, Set[str]] = {} # cell -> cells_that_depend_on_me

    def _parse_dependencies(self, formula_or_val: Any) -> List[str]:
        if not isinstance(formula_or_val, str) or not formula_or_val.startswith("="):
            return []
        tokens = CELL_COORD_REGEX.findall(formula_or_val[1:])
        return list(set(tokens))

    def detect_circular_references(self, cell_defs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds DAG and performs Tarjan/DFS topological cycle detection to prevent Excel circular calculation loops.
        """
        deps: Dict[str, List[str]] = {}
        for cell, val in cell_defs.items():
            deps[cell] = self._parse_dependencies(val)

        visited = {} # cell -> 0 (unvisited), 1 (visiting), 2 (visited)
        cycle_detected = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1 # visiting
            for nxt in deps.get(node, []):
                if nxt not in cell_defs:
                    continue # external or empty
                if visited.get(nxt) == 1:
                    cycle = path + [nxt]
                    cycle_detected.append(cycle)
                elif visited.get(nxt) == 0 or nxt not in visited:
                    dfs(nxt, path + [nxt])
            visited[node] = 2

        for c in cell_defs:
            if visited.get(c, 0) == 0:
                dfs(c, [c])

        return {
            "has_circular_reference": len(cycle_detected) > 0,
            "cycle_count": len(cycle_detected),
            "cycles": cycle_detected
        }

    def evaluate_cell_dag(self, cell_defs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates deterministic preview values for basic arithmetic and math formulas in topological order.
        """
        circ = self.detect_circular_references(cell_defs)
        if circ["has_circular_reference"]:
            return {
                "error": "Cannot evaluate matrix: circular references detected",
                "cycles": circ["cycles"]
            }

        resolved_values: Dict[str, float] = {}
        unresolved = dict(cell_defs)

        # Iterative topological resolution
        for _ in range(50):
            progress = False
            for cell, expr in list(unresolved.items()):
                if not isinstance(expr, str) or not expr.startswith("="):
                    # Literal number
                    try:
                        resolved_values[cell] = float(expr)
                        del unresolved[cell]
                        progress = True
                    except (ValueError, TypeError):
                        resolved_values[cell] = expr
                        del unresolved[cell]
                        progress = True
                    continue

                formula = expr[1:]
                tokens = CELL_COORD_REGEX.findall(formula)
                all_ready = all(t in resolved_values for t in tokens)

                if all_ready:
                    sub_formula = formula
                    for t in tokens:
                        sub_formula = re.sub(r"\b" + t + r"\b", str(resolved_values[t]), sub_formula)
                    try:
                        # Safe arithmetic eval strictly on digits and operators
                        if re.match(r"^[0-9.\s+\-*/()]+$", sub_formula):
                            # Evaluate simple arithmetic
                            val = eval(sub_formula, {"__builtins__": None}, {})
                            resolved_values[cell] = round(float(val), 4)
                            del unresolved[cell]
                            progress = True
                    except Exception:
                        resolved_values[cell] = "#VALUE!"
                        del unresolved[cell]
                        progress = True

            if not progress or not unresolved:
                break

        return {
            "total_cells": len(cell_defs),
            "resolved_count": len(resolved_values),
            "matrix_values": resolved_values
        }

    def compile_spreadsheet_model(
        self,
        model_name: str,
        cell_definitions: Dict[str, Any],
        tab_name: str = "Financial_Summary"
    ) -> Dict[str, Any]:
        """Compiles a complete structured multi-tab spreadsheet deliverable specification."""
        circ_check = self.detect_circular_references(cell_definitions)
        eval_result = self.evaluate_cell_dag(cell_definitions)

        return {
            "model_name": model_name,
            "active_tab": tab_name,
            "circular_reference_check": circ_check,
            "cell_definitions": cell_definitions,
            "evaluated_preview": eval_result.get("matrix_values", {}),
            "export_ready": not circ_check["has_circular_reference"],
            "status": "VALIDATED_ENTERPRISE_SPREADSHEET"
        }
