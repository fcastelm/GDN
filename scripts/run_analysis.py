from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gdn.pipeline import run_analysis


def main() -> int:
    result = run_analysis(PROJECT_ROOT)
    processed = result["processed"]
    skipped = result["skipped"]

    if not processed:
        print("No complete networks were processed.")
        if skipped:
            for network_name, issues in skipped.items():
                print(f"- {network_name}: {', '.join(issues)}")
        return 1

    print("GDN analysis completed.")
    for item in processed:
        print(
            f"- {item['network']}: {item['n_nodes']} nodes, {item['n_edges']} edges, "
            f"{item['n_samples']} samples -> {item['results_dir']}"
        )

    if skipped:
        print("Skipped networks:")
        for network_name, issues in skipped.items():
            print(f"- {network_name}: {', '.join(issues)}")

    print(f"Processed {len(processed)} network(s); skipped {len(skipped)} network(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
