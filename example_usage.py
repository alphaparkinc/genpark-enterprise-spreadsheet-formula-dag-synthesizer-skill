"""Example usage for EnterpriseSpreadsheetFormulaDAGSynthesizer."""
import json
from client import EnterpriseSpreadsheetFormulaDAGSynthesizer

def main():
    print("=== Enterprise Spreadsheet Financial Model DAG Synthesizer (WorkBuddy Goal-to-Excel) ===")
    synthesizer = EnterpriseSpreadsheetFormulaDAGSynthesizer()

    # 1. Define financial modeling cells with dependency cascade
    cells = {
        "B1": 500000,          # Base Q1 Revenue
        "B2": "=B1*1.15",      # Q2 Revenue (+15%)
        "B3": "=B2*1.20",      # Q3 Revenue (+20%)
        "B4": "=B1+B2+B3",     # 9-Month Trailing Gross Revenue
        "C1": 150000,          # Fixed COGS
        "C2": "=C1*1.05",      # Inflation adjusted COGS
        "D4": "=B4-(C1+C2)"    # Gross Margin
    }

    print("\n--- Compiling Spreadsheet Model & Evaluating Cell DAG ---")
    model = synthesizer.compile_spreadsheet_model(
        model_name="Corporate_Gross_Margin_Forecast",
        cell_definitions=cells,
        tab_name="Executive_Summary"
    )
    print(f"Model: {model['model_name']} (Circular Ref Error: {model['circular_reference_check']['has_circular_reference']})")
    print("\nEvaluated Cell Values Preview:")
    for k, v in model["evaluated_preview"].items():
        print(f"  {k} = {v}")

    # 2. Test Circular Reference Detection
    print("\n--- Circular Reference Deadlock Detection Test ---")
    bad_cells = {
        "A1": "=A2+10",
        "A2": "=A1*2" # Circular loop!
    }
    circ = synthesizer.detect_circular_references(bad_cells)
    print(f"Has Circular Loop: {circ['has_circular_reference']}")
    print(f"Detected Cycles: {circ['cycles']}")

if __name__ == "__main__":
    main()
