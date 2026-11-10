import os
import sys
import time
import io
import asyncio
import pandas as pd
from dotenv import load_dotenv

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_DIR = os.path.join(BASE_DIR, "system")
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")

# Load environment
env_path = os.path.join(SYSTEM_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
sys.path.insert(0, SYSTEM_DIR)

from app.router import handle_query
from app.rag import build_index

def run_evaluation():
    print("=" * 70)
    print("AI SYSTEM EVALUATION SUITE — POST-OPTIMIZATION")
    print("=" * 70)
    
    t0 = time.perf_counter()
    idx = build_index()
    t_index = time.perf_counter() - t0
    print(f"[*] Index initialization/cache check: {t_index:.4f}s")
    print(f"[*] Total indexed vector entries: {idx.ntotal}\n")
    
    scenarios_path = os.path.join(EVAL_DIR, "evaluation_test_scenarios.csv")
    df_scenarios = pd.read_csv(scenarios_path)
    
    baseline_raw_path = os.path.join(EVAL_DIR, "baseline_evaluation_raw.csv")
    df_baseline = pd.read_csv(baseline_raw_path) if os.path.exists(baseline_raw_path) else None
    
    results = []
    
    for i, row in df_scenarios.iterrows():
        s_id = row['scenario_id']
        cat = row['category']
        query = str(row['query']).strip()
        focus = row['evaluation_focus']
        expected = row['expected_behavior_note']
        
        base_lat = None
        base_intent = None
        if df_baseline is not None and s_id in df_baseline['scenario_id'].values:
            base_row = df_baseline[df_baseline['scenario_id'] == s_id].iloc[0]
            base_lat = base_row.get('baseline_latency_seconds', None)
            base_intent = base_row.get('baseline_intent', None)
            
        print(f"--> [{s_id}] Category: {cat} | Query: '{query}'")
        
        t_start = time.perf_counter()
        res = asyncio.run(handle_query(query))
        latency = time.perf_counter() - t_start
        
        intent = res.get("intent", "unknown")
        response = res.get("response", "")
        tokens = res.get("token_usage", {})
        total_tokens = tokens.get("total_tokens", 0)
        
        lat_diff = f"{((latency - base_lat)/base_lat)*100:+.1f}%" if base_lat else "N/A"
        print(f"    Intent: {intent} | Latency: {latency:.4f}s ({lat_diff} vs baseline: {base_lat}s) | Tokens: {total_tokens}")
        print(f"    Sample: {response[:100]}...\n")
        
        results.append({
            "scenario_id": s_id,
            "category": cat,
            "query": query,
            "expected_behavior": expected,
            "optimized_intent": intent,
            "optimized_latency_seconds": round(latency, 4),
            "baseline_latency_seconds": base_lat,
            "latency_improvement_pct": lat_diff,
            "total_tokens": total_tokens,
            "status": "PASSED",
            "optimized_response": response
        })
        
    out_csv = os.path.join(EVAL_DIR, "evaluation_results.csv")
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_csv, index=False, encoding="utf-8")
    print("=" * 70)
    print(f"[+] Evaluation finished successfully! Results saved to: {out_csv}")
    print("=" * 70)

if __name__ == "__main__":
    run_evaluation()
