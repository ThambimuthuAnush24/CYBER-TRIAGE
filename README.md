# Cybersecurity Incident Triage Expert System

A local, explainable assignment project with 32 observation definitions, 42 referenced production rules, forward chaining, backward chaining, a browser interface and automated tests. Classifications are suspected incidents, not forensic confirmation.

## Quick start on Windows

1. Install Python 3.10 or newer from https://www.python.org/downloads/ and enable the Python launcher / PATH option.
2. Extract this entire ZIP to a normal folder.
3. Double-click `start-windows.bat`, or open a terminal in this folder and run `py -3 server.py --engine python`.
4. Open **http://127.0.0.1:8000** in your browser. Keep the terminal running.
5. Choose a scenario, click **Analyze incident**, expand the forward trace, then use **Test a hypothesis**.
6. Press Ctrl+C in the terminal to stop.

macOS/Linux: `python3 server.py --engine python` or `./start.sh` after installing Python 3.10+.

No Python packages, API key, database or internet connection are needed at runtime. Python's standard library is sufficient.

## Preferred Prolog mode

Install a current stable SWI-Prolog release from https://www.swi-prolog.org/Download.html and ensure `swipl --version` works in a NEW terminal. Use:

```text
py -3 server.py --engine prolog
```

On macOS/Linux substitute `python3` for `py -3`. The server invokes `prolog/main.pl` for each consultation. Both inference directions run in Prolog; Python handles HTTP input validation and presentation assembly. `knowledge.json` is shared by both engines. Default `server.py` uses Prolog when it is available and otherwise uses the portable Python rule shell. The interface always shows the selected engine. A failing Prolog invocation is surfaced, not silently replaced with Python.

**Verification status:** Python engine/API: 22 automated tests passed, one Prolog parity test skipped in the build environment. SWI-Prolog was unavailable here. The Prolog engine is supplied but must be executed and its parity test passed on a machine with SWI-Prolog before claiming Prolog validation. UI assets and JavaScript syntax were checked; browser interactions and visual rendering were not executed because no browser binary was available.

## Tests

Run from this folder:

```text
py -3 -m unittest discover -s tests -v
```

`test_prolog_python_parity` automatically executes when `swipl` is on PATH. It compares both engines for all scenario/derived-goal combinations, including proof trees and rule traces. Do not present a skipped test as a pass. Existing observed results are in `docs/test-results.txt`; scenario-level expected/actual results are in `docs/scenario-results.json`.

## How to use

- **Yes:** positive observation supported by evidence.
- **No:** an explicitly established negative observation.
- **Unknown:** not investigated or not established. Never automatically treated as No.
- **Forward chaining:** derive all supported categories, priority facts and actions in rounds until no new rule fires.
- **Backward chaining:** select a hypothesis, recursively examine alternative rules, and show proven, unknown or not-supported paths.
- **Priority:** highest supported level wins: critical, high, medium. No supported priority yields unassessed, which does not mean safe.
- **Export:** explicitly downloads a JSON file containing observations, results and explanations. No case is saved automatically.
- Changing evidence invalidates displayed results. Re-analyze after edits.

## File map

- `knowledge.json`: authoritative fact definitions, rule definitions and source mappings.
- `prolog/main.pl`: Prolog forward engine and backward meta-interpreter.
- `engine.py`: portable Python production-rule shell and validation.
- `server.py`: local-only HTTP adapter; explicit Prolog/portable selection.
- `web/`: HTML, CSS and JavaScript user interface.
- `scenarios.json`: 12 fictional scenarios and independent expected outcomes.
- `examples/ransomware-full.json`: a fully instantiated 32-fact fictional consultation.
- `tests/`: engine, scenario, API and optional Prolog parity tests.
- `docs/`: observed test results, requirement map and demonstration guide.

## Editing the knowledge base

Add or edit rules in `knowledge.json`. Rule conditions are a conjunction; separate rules express alternatives. Conditions use only a known observation or derived fact and `yes`/`no`. Use negative values only for observations. Derived conclusions are positive atoms. Keep the dependency graph acyclic, attach a source and explain local policy assumptions. Restart the server and re-run tests after any edit. Add a case that exercises each changed rule. Existing rules have no numeric certainty factors; no output is a calibrated probability.

## Local operation and limits

The listener is bound to 127.0.0.1; it is a classroom/local prototype, not a production SOC platform. No login, persistent evidence repository, log ingestion, SIEM integration or automated containment is implemented. It does not open suspicious links or execute samples. All observations must describe the SAME incident and relevant time window. Hypotheses can overlap. An absent rule match cannot establish benign activity. Priorities and exact rule conjunctions are project policy, not NIST or CISA official rules.

## Troubleshooting

- `py` not found: install Python or use `python server.py` if that command starts Python 3.10+.
- `swipl` not found: add the SWI-Prolog `bin` directory to PATH, restart the terminal, and check `swipl --version`.
- Port busy: `py -3 server.py --port 8001`, then open http://127.0.0.1:8001.
- UI cannot connect: keep the server terminal open and use the local URL, not `web/index.html` directly.
- Prolog execution error: run the test suite, retain its stderr, and fix the failure before a Prolog demonstration. The Python mode remains available for comparison.

See the separate assignment report for the full knowledge engineering process, rule catalog, architecture diagram, user manual and references. Replace student details in the report before submission and follow your institution's rules on acknowledging assistance.
