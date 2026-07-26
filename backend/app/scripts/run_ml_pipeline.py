import sys
import os
import json
import traceback
import pandas as pd
import dataclasses

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.ml.pipeline import run_pipeline

def main():
    if len(sys.argv) < 5:
        print(json.dumps({"success": False, "message": "Invalid arguments", "steps": []}))
        sys.exit(1)
        
    csv_path = sys.argv[1]
    processed_dir = sys.argv[2]
    model_dir = sys.argv[3]
    contamination = float(sys.argv[4])
    
    try:
        df_raw = pd.read_csv(csv_path)
        result = run_pipeline(
            df_raw=df_raw,
            processed_dir=processed_dir,
            model_dir=model_dir,
            contamination=contamination
        )
        # Convert dataclass to dict
        result_dict = dataclasses.asdict(result)
        print(json.dumps(result_dict))
    except Exception as exc:
        err_msg = str(exc)
        trace = traceback.format_exc()
        print(json.dumps({
            "success": False, 
            "message": f"ML pipeline failed: {err_msg}", 
            "details": trace,
            "steps": []
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
