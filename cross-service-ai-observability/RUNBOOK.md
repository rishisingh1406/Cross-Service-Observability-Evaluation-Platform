# Distributed Latency Debugging Runbook

## Purpose

This runbook defines the methodology for investigating latency problems in the distributed AI system using Jaeger and OpenTelemetry.

The goal is to identify the service and span responsible for increased latency using distributed traces before inspecting application code.

The debugging workflow is:

```text
Symptom
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
Compare against baseline
   ↓
Form root-cause hypothesis
   ↓
Apply fix
   ↓
Generate verification trace
```

---

# 1. Symptom

A request is reported as slow or the observed latency is significantly higher than the expected baseline.

The first step is not to immediately inspect application code.

Instead, locate the distributed trace associated with the slow request.

Example baseline latency:

```text
≈ 390 ms
```

During the latency-injection experiment, the observed trace duration increased to:

```text
520.38 ms
```

This indicated that additional latency had been introduced somewhere in the distributed request path.

---

# 2. Find the Relevant Trace

Open the Jaeger Search interface and search for traces associated with the suspected service or operation.

For the latency-debugging experiment, the relevant service was:

```text
retrieval-service
```

The relevant operation was:

```text
retrieval.search
```

The objective is to locate the slow trace without reading the application code.

Jaeger Search can be used to narrow the investigation by:

* Service
* Operation
* Time range
* Duration
* Other available trace filters

The important principle is:

> Start with the trace, not the source code.

---

# 3. Check Total Trace Duration

After opening the trace, first inspect the total duration.

The injected-delay trace had:

```text
Total trace duration:
520.38 ms
```

This establishes that the request was significantly slower than the approximate baseline of:

```text
≈ 390 ms
```

However, the total duration alone does not identify the cause.

The next step is to inspect the waterfall.

---

# 4. Inspect the Trace Waterfall

The Jaeger waterfall shows how the request propagated across services and how much time individual spans consumed.

The investigation should focus on spans whose duration is unusually large compared with surrounding spans.

In the injected trace, the important observation was:

```text
retrieval.search
≈ 301.56 ms
```

This span was substantially longer than the other Retrieval operations.

The waterfall therefore provided evidence that the latency increase was concentrated in the Retrieval operation.

---

# 5. Identify the Abnormal Span

The abnormal span was:

```text
retrieval.search
```

with a duration of:

```text
301.56 ms
```

This was the key signal in the trace.

The reasoning was:

```text
520.38 ms total request
        ↓
301.56 ms spent in retrieval.search
        ↓
Large portion of request time concentrated in one span
        ↓
Investigate Retrieval
```

The important lesson is that the trace identifies the **location of the latency**, even before the underlying code is inspected.

---

# 6. Identify the Responsible Service

The abnormal span belonged to:

```text
retrieval-service
```

Therefore, the latency investigation was narrowed from the entire distributed system to the Retrieval service.

Instead of investigating every component:

```text
Gateway
Agent
Retrieval
Memory
LLM
```

the trace allowed the investigation to focus on:

```text
retrieval-service
        ↓
retrieval.search
```

This is the primary value of distributed tracing during latency debugging.

---

# 7. Compare Against Baseline

The injected trace was compared against a fixed trace.

### Injected trace

```text
Total:
520.38 ms

retrieval.search:
301.56 ms
```

### Fixed trace

```text
Total:
121.94 ms

retrieval.search:
415 µs
```

The important comparison is not simply the total trace duration because distributed systems naturally experience latency variation between requests.

The important observation is the dramatic change in the problematic span:

```text
301.56 ms
      ↓
415 µs
```

This showed that the abnormal latency inside `retrieval.search` disappeared after the artificial delay was removed.

---

# 8. Form Root-Cause Hypothesis

Based on the trace evidence, the hypothesis was:

> The Retrieval service contains an operation causing approximately 300 ms of additional latency inside `retrieval.search`.

The trace alone establishes **where** the latency occurs.

The source code or additional application-level investigation can then be used to determine **why** it occurs.

In this experiment, the approximately 300 ms delay was deliberately injected into the Retrieval service, allowing the hypothesis to be validated.

---

# 9. Apply the Fix

The artificial latency was removed from the Retrieval service.

A new request was generated after the change.

The purpose of the new request was not simply to confirm that the code changed.

The purpose was to generate new observability evidence.

---

# 10. Generate a Verification Trace

After the fix, a new trace was inspected in Jaeger.

The resulting trace showed:

```text
Total trace:
121.94 ms

retrieval.search:
415 µs
```

The previously observed approximately 300 ms latency spike was no longer present.

Comparison:

```text
                    Injected       Fixed

Total trace         520.38 ms      121.94 ms

retrieval.search    301.56 ms      415 µs
```

The exact total request duration does not need to match the original baseline because distributed-service latency naturally varies.

The critical verification is that the abnormal `retrieval.search` latency disappeared.

---

# 11. Final Diagnosis

The latency investigation can therefore be summarized as:

```text
Slow request
    ↓
Jaeger Search
    ↓
520.38 ms trace identified
    ↓
Waterfall inspected
    ↓
retrieval.search = 301.56 ms
    ↓
retrieval-service identified
    ↓
Latency hypothesis formed
    ↓
Artificial delay removed
    ↓
Verification trace generated
    ↓
retrieval.search = 415 µs
```

## Conclusion

An approximately 300 ms artificial latency spike was isolated to `retrieval.search` using the Jaeger waterfall and disappeared after the delay was removed.

The investigation demonstrated that distributed tracing can be used to identify the location of a latency problem across multiple services without initially reading the application code.

---

# Core Debugging Principle

When a distributed request is slow:

> **Do not guess which service is responsible. Follow the trace.**

The objective is to move from:

```text
"I think Retrieval might be slow."
```

to:

```text
"Jaeger shows retrieval.search consumed
301.56 ms of the 520.38 ms request."
```

That is the difference between having telemetry and actually using observability for production debugging.
