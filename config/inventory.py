from pathlib import Path
import json


def get_ip_from_terraform(tf_output_path: Path) -> str:
    with open(tf_output_path, "r") as json_file:
        data = json.load(json_file)
        return data


terraform_output = Path(__file__).parent / ".." / "data" / "ducklake_postgres_ip.json"
postgres = [get_ip_from_terraform(terraform_output.resolve())]
