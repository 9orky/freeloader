import json
import re
from dataclasses import dataclass
from pathlib import Path
from subprocess import run, CalledProcessError
from typing import Union, List, Dict


class CliCommandFailed(Exception):
    def __init__(self, cmd: str, error: str, raw_output: str):
        if isinstance(error, bytes):
            error = error.decode(errors='replace')

        self.cmd = cmd
        self.error = error
        self.command_output = CommandOutput(raw_output)


@dataclass(frozen=True)
class CommandOutput:
    raw: str

    def extract_json_within(self):
        string = self.raw

        try:
            first_value = string.index("{")
            last_value = len(string) - string[::-1].index("}")
            string = string[first_value:last_value]
            return json.loads(string)
        except ValueError:
            return {}

    def extract_jsons(self):
        pattern = r'{.*?}'
        json_list = re.findall(pattern, self.raw)

        extracted_jsons = []
        for json_str in json_list:
            try:
                json_data = json.loads(json_str)
                extracted_jsons.append(json_data)
            except json.JSONDecodeError:
                extracted_jsons.append({})

        return extracted_jsons

    @property
    def json(self) -> Union[List, Dict]:
        return self.extract_json_within()


def run_cli(command: str | list[str], chdir: Path | None = None) -> CommandOutput:
    if chdir is not None and not chdir.is_dir():
        raise ValueError(f"Invalid directory: {chdir}")
    
    try:
        result = run(command, capture_output=True, text=True, check=True, cwd=chdir)
        return CommandOutput(result.stdout)
    except CalledProcessError as e:
        raise CliCommandFailed(cmd=command, error=e.stderr, raw_output=e.output)

