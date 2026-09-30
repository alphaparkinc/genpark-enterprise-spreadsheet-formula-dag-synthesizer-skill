"""MCP Server for Enterprise Spreadsheet Formula DAG Synthesizer."""
import sys
import json
import time
from client import EnterpriseSpreadsheetFormulaDAGSynthesizer

synthesizer = EnterpriseSpreadsheetFormulaDAGSynthesizer()

def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})
    if name != "synthesize_spreadsheet_formula_dag":
        raise ValueError(f"Unknown tool: {name}")

    action = args.get("action", "compile_spreadsheet_model")
    if action == "compile_spreadsheet_model":
        return synthesizer.compile_spreadsheet_model(
            model_name=args.get("model_name", "Q3_Model"),
            cell_definitions=args.get("cell_definitions", {}),
            tab_name=args.get("tab_name", "Summary")
        )
    elif action == "detect_circular_references":
        return synthesizer.detect_circular_references(
            cell_defs=args.get("cell_definitions", {})
        )
    elif action == "evaluate_cell_dag":
        return synthesizer.evaluate_cell_dag(
            cell_defs=args.get("cell_definitions", {})
        )
    else:
        raise ValueError(f"Invalid action: {action}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running self-test...")
        cells = {"A1": 100, "A2": 250, "A3": "=A1+A2", "A4": "=A3*1.1"}
        model = synthesizer.compile_spreadsheet_model("Test", cells)
        assert model["export_ready"] is True
        assert model["evaluated_preview"]["A3"] == 350.0
        assert model["evaluated_preview"]["A4"] == 385.0
        print("Self-test PASSED!")
        sys.exit(0)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            msg_id = req.get("id")
            method = req.get("method")
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "EnterpriseSpreadsheetFormulaDAGSynthesizer", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [{
                            "name": "synthesize_spreadsheet_formula_dag",
                            "description": "Enterprise goal-to-spreadsheet synthesis: define multi-tab models, compile formula dependency DAGs, detect circular reference deadlocks, and evaluate deterministic cell value matrices.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["compile_spreadsheet_model", "detect_circular_references", "evaluate_cell_dag"]},
                                    "model_name": {"type": "string"},
                                    "cell_definitions": {"type": "object"},
                                    "tab_name": {"type": "string"}
                                },
                                "required": ["action"]
                            }
                        }]
                    }
                }
            elif method == "tools/call":
                res = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
