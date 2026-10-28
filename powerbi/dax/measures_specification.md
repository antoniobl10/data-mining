# Current DAX specification

The authoritative [catalog](measures.md) documents all 61 authored measures with exact DAX, descriptions, folders, formats and primary pages. measures.dax and measures.json provide readable and machine-readable equivalents. All measures live in _Measures.

Calculations aggregate the customer-grain fact, distinguish observed averages from all-customer denominators, use safe division and explicit selected-country shares/ranks. No dates or CLV are invented. Independent references cover twelve filter scenarios but do not execute DAX. See [validation](../../docs/powerbi_validation.md).
