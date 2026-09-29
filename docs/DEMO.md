# Five minute demonstration

1. Start the application and point to the engine indicator. If demonstrating Prolog, explicitly start with --engine prolog.
2. Open Knowledge base. Explain the 32 observations and inspect R07, R24 and R33. Source IDs distinguish reference concepts from project policy.
3. Load Ransomware on a critical server. Analyze. Show the suspected ransomware category and critical project priority.
4. Expand the forward trace: R07 recognizes the indicator combination, R24 sets critical priority and later rules recommend evidence preservation and escalation.
5. Select ransomware in Test a hypothesis. Explain the backward proof from goal to R07 conditions. Explain that other alternative paths can remain unknown even when one path is proven.
6. Change ransom note to No. The old assessment is invalidated. Analyze again. The ransomware goal is unknown because malware evidence could still support the alternative R08 path.
7. Reset. Analyze the empty case. Explain why unassessed does not mean safe.
8. Load Phishing with credential exposure. Show the multi-round chain: phishing -> credential exposure -> suspected account compromise -> high priority -> actions.
9. Export the case and show the JSON includes observations and the rule trace.
10. Run the tests and disclose any skipped tests.

## Manual browser acceptance checklist

Not executed in the build environment. Record your own results before submission.

- Desktop and phone-width layout has no clipping or horizontal overflow.
- All 32 selects accept Unknown, Yes and No.
- A sample selection sets its evidence and resets other fields.
- Analyze produces the documented category and priority.
- Forward trace displays conditions, round, rule and references.
- Backward proof expands and distinguishes unknown from negative evidence.
- Editing evidence clears stale results.
- Rule search finds R41 and the reference list opens source links.
- Reset clears observations; export downloads valid JSON.
- Refresh clears the in-memory case.

## Viva talking points

Why an expert system? Knowledge is explicit and inspectable as facts and IF-THEN rules.
Why not machine learning? No training data or learned classifier is used.
What is forward chaining? Start from facts and repeatedly fire applicable rules.
What is backward chaining? Start from a goal and recursively check rules that could establish it.
What is the conflict policy? Fire all applicable rules once; choose the highest derived priority for display.
What does proven mean? Supported by this knowledge base and input, not confirmed in the real world.
How is missing evidence handled? Unknown is kept separate from explicitly observed No.
Where did the knowledge come from? NIST, CISA and MITRE concepts, formalized into project rules with policy decisions explicitly labeled.
What are the limits? Manual inputs, qualitative heuristics, finite coverage, no expert validation and no measured operational accuracy.
