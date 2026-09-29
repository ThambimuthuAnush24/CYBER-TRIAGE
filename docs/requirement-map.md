# Assignment requirement map

| Requirement | Implementation evidence |
|---|---|
| Clearly defined real-world domain | README and report: initial cybersecurity incident triage |
| Domain study and external sources | knowledge.json sources S1-S7; P1 explicitly denotes project policy |
| Knowledge engineering process | Report section 2 |
| At least 20 facts | 32 observation definitions; examples/ransomware-full.json contains 32 ground yes/no case facts |
| At least 20 rules with references | 42 rules R01-R42 in knowledge.json |
| Prolog encouraged | prolog/main.pl; selectable --engine prolog; execution not verified here |
| Forward chaining | forward in engine.py and forward/6 in Prolog |
| Backward chaining | backward in engine.py and prove/5 in Prolog |
| Interface | web/index.html, app.js and style.css |
| Explanations | Round traces, antecedents, source IDs, recursive proof trees |
| Executable and instructions | Python portable mode tested; README and launch scripts |
| Tests and actual results | tests/, docs/test-results.txt and scenario-results.json |
| One report, code separate | Separate DOCX report and source ZIP |

Remaining verification: run Prolog parity and manual browser acceptance on the submission computer. No expert interview or operational validation is claimed.
