Yes. Your existing `RUNBOOK.md` documents the **Retrieval latency exercise**, but Day 81 specifically requires the **Memory latency exercise** with the Prometheus `memory_latency_seconds` evidence.

I would update the file so it contains **both exercises**, while keeping your existing Retrieval documentation intact.

# Distributed Latency Debugging Runbook

## Purpose

This runbook defines the methodology for investigating latency problems in the distributed AI system using Prometheus, Jaeger, and OpenTelemetry.

The goal is to identify the service and span responsible for increased latency using observability evidence before inspecting application code.

The debugging workflow is:

```text
Symptom
   ↓
Metrics detect abnormal latency
   ↓
Find trace
   ↓
Check total duration
   ↓
Inspect waterfall
   ↓
Find abnormal span
   ↓
Identify responsible service
   ↓
Form root-cause hypothesis
   ↓
Apply fix
   ↓
Generate verification request
   ↓
Verify metrics recovery
   ↓
Verify trace recovery
```

---

# 1. Core Debugging Principle

When a distributed request is slow:

> **Do not guess which service is responsible. Follow the telemetry.**

Metrics answer:

> **"Is the system becoming slow?"**

Distributed traces answer:

> **"Where is the latency occurring?"**

Span inspection helps answer:

> **"Which operation is responsible?"**

Application code inspection can then establish:

> **"Why is that operation slow?"**

The objective is to move from:

```text
"I think Memory might be slow."
```

to:

```text
"Prometheus shows elevated write latency,
and Jaeger shows memory.store consuming the majority
of the request duration."
```

---

# 2. General Latency Debugging Workflow

## Step 1 — Detect the Symptom

A request is reported as slow or an observed latency metric increases significantly above the expected baseline.

Do not immediately inspect application code.

First establish whether the latency increase is visible through telemetry.

```text
Application request
      ↓
Prometheus latency metric
      ↓
Abnormal latency detected
```

---

## Step 2 — Locate the Trace

Open the Jaeger Search interface and search for traces associated with the affected service or operation.

Useful filters include:

* Service
* Operation
* Time range
* Duration
* Trace attributes

The important principle is:

> **Start with telemetry, not source code.**

---

## Step 3 — Inspect the Trace Waterfall

After opening a suspicious trace:

1. Check total trace duration.
2. Inspect the waterfall.
3. Identify unusually long spans.
4. Compare parent and child span durations.
5. Determine where the majority of the latency is concentrated.

The waterfall should narrow the investigation from:

```text
Entire distributed system
```

to:

```text
Specific service
    ↓
Specific operation
    ↓
Specific span
```

---

# 3. Latency Debugging Exercise — Retrieval Service

This was the earlier distributed latency debugging experiment.

## Symptom

The Retrieval operation became significantly slower than its normal baseline.

Approximate baseline:

```text
≈ 390 ms
```

During the latency-injection experiment:

```text
Total trace duration:
520.38 ms
```

This indicated that additional latency had been introduced somewhere in the distributed request path.

---

## Find the Relevant Trace

The affected service was:

```text
retrieval-service
```

The relevant operation was:

```text
retrieval.search
```

The objective was to locate the slow trace through Jaeger without initially inspecting the application source code.

---

## Trace Inspection

The Jaeger waterfall showed:

```text
retrieval.search
≈ 301.56 ms
```

This span consumed a substantial portion of the total:

```text
Total request:
520.38 ms

retrieval.search:
301.56 ms
```

This concentrated the investigation on the Retrieval service.

---

## Suspicious Span

The abnormal span was:

```text
retrieval.search
```

Duration:

```text
301.56 ms
```

Reasoning:

```text
520.38 ms total request
        ↓
301.56 ms in retrieval.search
        ↓
Large latency concentration
        ↓
Investigate retrieval-service
```

---

## Root-Cause Hypothesis

The trace established **where** the latency occurred.

The hypothesis was:

> The Retrieval service contains an operation introducing approximately 300 ms of additional latency inside `retrieval.search`.

The artificial delay was deliberately injected into the Retrieval service, allowing the hypothesis to be validated.

---

## Fix

The artificial latency was removed from the Retrieval service.

A new request was then generated to produce fresh observability evidence.

---

## Verification

The fixed trace showed:

```text
Total trace:
121.94 ms

retrieval.search:
415 µs
```

Comparison:

```text
                         Injected       Fixed

Total trace             520.38 ms      121.94 ms

retrieval.search        301.56 ms      415 µs
```

The important verification was not that the total request duration exactly matched the original baseline.

The important verification was:

```text
301.56 ms
    ↓
415 µs
```

The abnormal latency inside `retrieval.search` disappeared.

---

# 4. Latency Debugging Exercise — Memory Service

This exercise is the primary Day 81 distributed debugging exercise.

## Objective

Demonstrate that a latency problem can be detected through Prometheus and then localized using Jaeger.

The experiment intentionally introduced artificial latency into the Memory Service.

The debugging process was performed using:

```text
Prometheus
+
Jaeger
+
OpenTelemetry
```

---

# 5. Memory Service — Symptom

The Memory Service exposes the Prometheus metric:

```text
memory_latency_seconds
```

with the operation label:

```text
operation="write"
```

The latency-injection experiment added:

```python
time.sleep(0.5)
```

inside the `memory.store` span.

This intentionally introduced approximately 500 ms of additional latency.

---

## Prometheus Detection

The p95 write latency during the injected-latency experiment was approximately:

```text
0.7375 seconds
```

Equivalent to:

```text
737.5 ms
```

Prometheus therefore established that the Memory Service write path had become significantly slower.

The important observation was:

```text
memory_latency_seconds
operation="write"

p95 ≈ 737.5 ms
```

At this point Prometheus established **that** the Memory Service was experiencing elevated write latency.

It did not establish exactly where inside the request the latency occurred.

That required Jaeger.

---

# 6. Memory Service — Trace Inspection

The next step was to open Jaeger:

```text
http://localhost:16686
```

The relevant service was:

```text
memory-service
```

The relevant operation was:

```text
POST /memory
```

The trace waterfall was then inspected.

The expected span hierarchy was:

```text
POST /memory
    ↓
memory.store
    ↓
memory.database.insert
```

---

# 7. Memory Service — Suspicious Span

The suspicious span was:

```text
memory.store
```

The database operation:

```text
memory.database.insert
```

was comparatively short.

The important observation was that the majority of the request duration was concentrated inside the parent `memory.store` span rather than the SQLite insert itself.

The trace therefore narrowed the investigation to:

```text
memory-service
      ↓
POST /memory
      ↓
memory.store
```

This was the key distributed-debugging signal.

---

# 8. Memory Service — Root Cause

The trace established **where** the latency was occurring.

The source code was then inspected to validate the root-cause hypothesis.

The intentional latency injection was:

```python
time.sleep(0.5)
```

inside:

```text
memory.store
```

The causal chain was:

```text
Prometheus
    ↓
write p95 ≈ 737.5 ms
    ↓
Jaeger
    ↓
POST /memory is slow
    ↓
memory.store is slow
    ↓
database.insert is comparatively fast
    ↓
time.sleep(0.5) identified
```

Therefore the artificial sleep was confirmed as the root cause of the injected latency.

---

# 9. Memory Service — Fix

The artificial delay was removed:

```python
# Removed
time.sleep(0.5)
```

No other intentional latency was added or modified for the write-path recovery test.

The Memory Service image was then rebuilt:

```text
docker compose build memory
```

and restarted:

```text
docker compose up -d memory
```

The service was confirmed running on:

```text
memory
host port: 8013
```

---

# 10. Memory Service — Verification Requests

Five new write requests were generated after the fix:

```text
jaeger latency recovery 1
jaeger latency recovery 2
jaeger latency recovery 3
jaeger latency recovery 4
jaeger latency recovery 5
```

All five requests completed successfully.

Returned memory IDs:

```text
26
27
28
29
30
```

This generated fresh Prometheus and Jaeger telemetry after the fix.

---

# 11. Memory Service — Prometheus Recovery

The same Prometheus p95 query was used after the fix:

```promql
histogram_quantile(
  0.95,
  sum by (le) (
    rate(memory_latency_seconds_bucket{operation="write"}[5m])
  )
)
```

Before the fix:

```text
p95 ≈ 0.7375 seconds
```

After the fix:

```text
p95 ≈ 0.0457837511 seconds
```

Equivalent to approximately:

```text
45.8 ms
```

Therefore:

```text
Before:
≈ 737.5 ms

After:
≈ 45.8 ms
```

The p95 latency dropped by approximately:

```text
94%
```

This provided quantitative evidence that the latency regression had been removed.

---

# 12. Memory Service — Jaeger Recovery

A new `POST /memory` trace was inspected in Jaeger after the fix.

The recovered trace showed:

```text
POST /memory
    ↓
memory.store
    ↓
memory.database.insert
```

The previously observed long `memory.store` duration was no longer present.

The `memory.store` span became substantially shorter after removing the artificial delay.

This independently confirmed the Prometheus recovery.

The two telemetry systems therefore agreed:

```text
Prometheus
737.5 ms
    ↓
45.8 ms

Jaeger
long memory.store
    ↓
short memory.store
```

---

# 13. Memory Service — Final Diagnosis

The complete investigation was:

```text
Elevated Memory write latency
        ↓
Prometheus
        ↓
memory_latency_seconds
operation="write"
        ↓
p95 ≈ 737.5 ms
        ↓
Jaeger Search
        ↓
POST /memory
        ↓
Waterfall inspection
        ↓
memory.store identified as suspicious
        ↓
memory.database.insert comparatively fast
        ↓
time.sleep(0.5) identified
        ↓
Artificial latency removed
        ↓
Docker image rebuilt
        ↓
5 verification requests
        ↓
Prometheus p95 ≈ 45.8 ms
        ↓
Jaeger memory.store became short
        ↓
Latency recovery confirmed
```

---

# 14. Before vs After

The Memory Service experiment produced the following evidence:

```text
                         Before Fix       After Fix

Write p95                ~737.5 ms        ~45.8 ms

Artificial delay         500 ms            Removed

memory.store             Long              Short

POST /memory              Slow              Recovered
```

The exact p95 value is expected to vary depending on the Prometheus observation window and request history.

The important evidence is the large reduction in write latency combined with the corresponding Jaeger trace recovery.

---

# 15. What Each Observability Tool Proved

## Prometheus

Prometheus answered:

> **Is the Memory Service experiencing elevated write latency?**

Evidence:

```text
p95 ≈ 737.5 ms
```

After the fix:

```text
p95 ≈ 45.8 ms
```

Therefore Prometheus provided quantitative evidence of the regression and recovery.

---

## Jaeger

Jaeger answered:

> **Where is the latency occurring?**

Evidence:

```text
POST /memory
    ↓
memory.store
```

The waterfall showed that the latency was concentrated around `memory.store`.

After the fix, the same span became substantially shorter.

---

## OpenTelemetry

OpenTelemetry connected the request to the individual operations through distributed spans:

```text
POST /memory
    ↓
memory.store
    ↓
memory.database.insert
```

This provided the trace-level context required to investigate the latency.

---

# 16. Cross-Exercise Debugging Pattern

Both latency experiments demonstrate the same general methodology.

### Retrieval

```text
Slow request
    ↓
Jaeger
    ↓
retrieval.search
    ↓
~301 ms abnormal latency
    ↓
Artificial delay
    ↓
Remove delay
    ↓
415 µs
```

### Memory

```text
High Prometheus p95
    ↓
Jaeger
    ↓
memory.store
    ↓
Artificial delay
    ↓
Remove delay
    ↓
Prometheus p95 recovery
    ↓
Jaeger trace recovery
```

The same methodology can be applied to future services.

---

# 17. Production Debugging Checklist

When investigating a latency problem:

* [ ] Confirm the latency symptom using metrics.
* [ ] Identify the affected service.
* [ ] Find a representative slow trace in Jaeger.
* [ ] Check total trace duration.
* [ ] Inspect the waterfall.
* [ ] Identify unusually long spans.
* [ ] Compare parent and child span durations.
* [ ] Narrow the investigation to the responsible service.
* [ ] Compare against a known-good baseline when available.
* [ ] Form a root-cause hypothesis.
* [ ] Inspect application code only after telemetry narrows the search.
* [ ] Apply the fix.
* [ ] Generate new verification requests.
* [ ] Verify metric recovery.
* [ ] Verify trace recovery.
* [ ] Record the incident and evidence in this runbook.

---

# 18. Final Debugging Principle

When a distributed request is slow:

> **Do not guess which service is responsible. Follow the trace.**

The complete observability workflow is:

```text
Metric
  ↓
Symptom
  ↓
Trace
  ↓
Waterfall
  ↓
Suspicious span
  ↓
Responsible service
  ↓
Root-cause hypothesis
  ↓
Fix
  ↓
Verification metric
  ↓
Verification trace
```

That is the difference between simply collecting telemetry and actually using observability for distributed-system debugging.

---

# Conclusion

The latency debugging exercises demonstrated that a distributed AI system can be investigated systematically using telemetry rather than guesswork.

The Retrieval exercise demonstrated span-level latency isolation:

```text
retrieval.search
301.56 ms
    ↓
415 µs after fix
```

The Memory exercise demonstrated metric-to-trace correlation:

```text
Prometheus:
737.5 ms
    ↓
Jaeger:
memory.store identified
    ↓
time.sleep(0.5)
    ↓
Fix
    ↓
Prometheus:
45.8 ms
    ↓
Jaeger:
short memory.store
```

The final methodology is:

> **Detect → Trace → Localize → Hypothesize → Fix → Measure → Verify**

This provides a repeatable method for debugging latency across the distributed AI system.
