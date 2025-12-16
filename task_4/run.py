# run.py
"""
Запуск: python run.py --config config.json --output output
"""

import argparse
from io_utils import load_config, save_policy
from dp_core import solve

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="config.json", help="path to config.json")
    parser.add_argument("--output", "-o", default="output", help="output folder")
    parser.add_argument("--cap", type=int, default=2000, help="cap reachable states per time (предотвращение blow-up)")
    args = parser.parse_args()

    config = load_config(args.config)
    initial_state, V, policy = solve(config, cap_per_t=args.cap)
    csv_path, results_path = save_policy(policy, V, args.output)
    print("Done. Results:")
    with open(results_path, 'r', encoding='utf-8') as f:
        print(f.read())
    print(f"Full policy saved to {csv_path}")

if __name__ == "__main__":
    main()
