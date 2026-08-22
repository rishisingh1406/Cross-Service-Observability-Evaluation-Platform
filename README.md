# Cross-Service Observability & Evaluation Platform

A production-style observability and evaluation platform for distributed AI systems.

This project demonstrates how to build, instrument, monitor, debug, and evaluate a multi-service AI application using **OpenTelemetry, Jaeger, Prometheus, Grafana, Docker Compose, FastAPI, and automated evaluation tests**.

The central goal is to solve a common problem in modern AI systems:

> When an AI request passes through multiple independent services, how do we understand what happened, identify where latency or failures occurred, and verify that the system is making the correct decisions?

Instead of treating an AI application as a single black box, this project turns it into an observable and testable distributed system.

---

## Table of Contents

- [Overview](#overview)
- [Why This Project Exists](#why-this-project-exists)
- [Key Goals](#key-goals)
- [Architecture](#architecture)
- [Services](#services)
- [Observability Stack](#observability-stack)
- [Distributed Tracing](#distributed-tracing)
- [Metrics](#metrics)
- [Grafana Dashboard](#grafana-dashboard)
- [Evaluation System](#evaluation-system)
- [Regression Testing](#regression-testing)
- [Request Flow](#request-flow)
- [API](#api)
- [Docker Compose](#docker-compose)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running the System](#running-the-system)
- [Testing](#testing)
- [Verifying the API](#verifying-the-api)
- [Observability Verification](#observability-verification)
- [Debugging Workflow](#debugging-workflow)
- [Latency Incident Simulation](#latency-incident-simulation)
- [Production Engineering Concepts Learned](#production-engineering-concepts-learned)
- [Technology Stack](#technology-stack)
- [Current Status](#current-status)
- [Release](#release)
- [Future Improvements](#future-improvements)
- [What I Learned](#what-i-learned)
- [Author](#author)
- [License](#license)

---

## Overview

The **Cross-Service Observability & Evaluation Platform** is a distributed AI engineering project designed to provide complete visibility into an AI application's behavior.

The platform contains multiple independent services responsible for different parts of the AI request lifecycle:

- Gateway
- Agent
- Retrieval
- Memory
- LLM

These services communicate with each other through HTTP APIs. Every important service is instrumented with **OpenTelemetry**, allowing requests to be traced across service boundaries. The collected telemetry is sent to an **OpenTelemetry Collector**, which acts as the telemetry pipeline.

From there:

- Traces are visualized in **Jaeger**
- Metrics are collected by **Prometheus**
- Metrics are visualized in **Grafana**

Alongside observability, the project contains an evaluation and regression testing system that verifies important agent behavior such as:

- Retrieval routing
- Memory routing
- Tool avoidance for simple conversations
- Prompt regression protection

The result is a small but production-oriented distributed AI system where behavior can be executed, observed, debugged, measured, evaluated, and regression-tested.

---

## Why This Project Exists

AI systems become difficult to debug once they are distributed across multiple services.

For example, a single user request may follow a path such as:

```text
User → Gateway → Agent → Retrieval / Memory → LLM
```

If the final response takes five seconds, simply looking at the gateway does not explain the problem. The actual delay could come from gateway processing, agent reasoning, retrieval, memory, LLM inference, network communication, or external dependencies.

Traditional application logs are often insufficient for understanding this type of behavior. Distributed tracing solves this by allowing the entire request lifecycle to be represented as a trace containing multiple spans.

This project focuses on a key production engineering principle:

> **AI systems should be observable and evaluatable, not treated as black boxes.**

---

## Key Goals

1. **Distributed Tracing** — Track a request across multiple services using OpenTelemetry.
2. **Centralized Telemetry** — Use an OpenTelemetry Collector as the telemetry pipeline.
3. **Trace Debugging** — Use Jaeger to identify slow services and problematic spans.
4. **Metrics Monitoring** — Expose Prometheus metrics from services and monitor them using Grafana.
5. **Unified Dashboard** — Create a Grafana dashboard for a centralized view of service health and performance.
6. **Agent Evaluation** — Evaluate whether the agent selected the correct execution path.
7. **Regression Protection** — Prevent accidental changes to important agent behavior and prompts.
8. **Reproducible Infrastructure** — Run the entire stack locally using Docker Compose.
9. **Production-Oriented Engineering** — Practice the same observability and evaluation concepts used in real distributed systems.

---

## Architecture

```text
                         +----------------+
                         |      User      |
                         +-------+--------+
                                 |
                                 v
                       +-------------------+
                       |      Gateway      |
                       |      :8000        |
                       +---------+---------+
                                 |
                                 v
                       +-------------------+
                       |       Agent       |
                       |      :8001        |
                       +----+---------+----+
                            |         |
                +-----------+         +-----------+
                |                                   |
                v                                   v
       +-------------------+                +-------------------+
       |     Retrieval     |                |      Memory       |
       |      :8002        |                |      :8003        |
       +---------+---------+                +---------+---------+
                 |                                    |
                 +----------------+-------------------+
                                  |
                                  v
                         +-------------------+
                         |       LLM         |
                         |      :8004        |
                         +-------------------+


                         OBSERVABILITY
                              |
                              v
                    +----------------------+
                    | OpenTelemetry        |
                    | SDK / Instrumentation|
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | OTel Collector       |
                    +----------+-----------+
                               |
                    +----------+----------+
                    |                     |
                    v                     v
             +-------------+       +-------------+
             |    Jaeger   |       | Prometheus  |
             |   Traces    |       |   Metrics   |
             +-------------+       +------+------+
                                           |
                                           v
                                     +-----------+
                                     |  Grafana  |
                                     | Dashboard |
                                     +-----------+
```

> **Note:** Ports `8000`–`8004` above are the container-internal ports. If your `docker-compose.yml` maps the Gateway to a different host port (for example `8010`), document that mapping explicitly, e.g.:
> ```text
> Container: Gateway → 8000
> Host:      Gateway → 8010
> ```

---

## Services

### Gateway (`:8000`)
The public entry point for the AI system. Exposes the main chat API and forwards requests into the distributed pipeline.

**Main endpoints:**
```text
GET  /health
POST /chat
GET  /metrics
```

### Agent (`:8001`)
Decides how a user request should be handled — whether it requires Retrieval, Memory, or a direct response. Routing behavior is explicitly covered by automated tests.

### Retrieval Service (`:8002`)
Handles retrieval-related operations, used when the agent determines external or indexed context is required. Instrumented so retrieval operations appear as spans inside distributed traces.

### Memory Service (`:8003`)
Handles persistent conversational context — previous conversations, stored user context, and explicit memory operations. Exposes Prometheus-compatible metrics.

### LLM Service (`:8004`)
Represents the model inference layer, isolating model interaction from the rest of the system since LLM inference is often the most expensive and latency-sensitive part of an AI system.

---

## Observability Stack

### OpenTelemetry
Provides the instrumentation layer — traces, spans, metrics, and trace context — using a common telemetry standard instead of a proprietary system per service.

### OpenTelemetry Collector
Acts as the central telemetry pipeline:

```text
Application Services → OpenTelemetry SDK → OTel Collector → Jaeger
                                                          → Metrics Pipeline
```

### Jaeger
Used for trace visualization and analysis, providing a waterfall-style view of distributed requests so latency relationships are immediately visible.

### Prometheus
Collects and stores time-series metrics from every major service:

```text
Gateway, Agent, Retrieval, Memory, LLM  →  Prometheus
```

Used to monitor request counts, latency, error rates, and general application performance.

### Grafana Dashboard
Grafana provides the visualization layer for metrics. The project includes a provisioned dashboard committed to the repo as code:

```text
observability/grafana/dashboards/cross-service-observability.json
```

Storing the dashboard as code (rather than configuring it manually in the UI) means it can be version controlled, reviewed, modified, recreated, and shared:

```text
dashboard JSON → Git → Grafana provisioning → Reproducible dashboard
```

---

## Distributed Tracing

A request can generate a trace such as:

```text
Trace
|
+-- gateway.chat
    |
    +-- agent.run
    +-- retrieval.search
    +-- memory.lookup
    +-- llm.generate
```

This allows questions like the following to be answered directly from a trace:

- Which service was slow?
- Which operation consumed the most time?
- Did retrieval run? Did memory run? Did the LLM request occur?
- Where did an error originate?
- What was the exact request path?

A simplified waterfall view looks conceptually like:

```text
gateway.chat       |----------------------------|
agent.run             |----------------------|
retrieval.search        |--------|
memory.lookup                   |-----|
llm.generate                       |------------|
```

---

## Metrics

Each major service exposes a Prometheus-compatible metrics endpoint:

```text
GET /metrics
GET /metrics/
```

`/metrics` redirects to `/metrics/`, which returns `200 OK` and is scraped continuously by Prometheus.

---

## Evaluation System

Observability answers **"what happened?"** Evaluation answers **"was the system correct?"** This project combines both.

```text
evals/
├── agent/
│   └── test_routing.py
│
└── regression/
    └── test_retrieval_prompt_regression.py
```

### Agent Routing Evaluation

The agent should not blindly use every available tool — it should choose the appropriate execution path:

```text
Policy question       → Retrieval
Returning user        → Memory
Simple greeting        → Direct response
```

**Current routing test cases:**

```text
policy_question_uses_retrieval
distributed_system_question_uses_retrieval
observability_question_uses_retrieval
agent_architecture_question_uses_retrieval

returning_user_uses_memory
remember_request_uses_memory
previous_context_uses_memory

greeting_skips_tools
casual_conversation_skips_tools
simple_thanks_skips_tools
```

### Regression Testing

```text
test_retrieval_instruction_is_present
```

Ensures an important retrieval-related instruction remains present in the agent prompt. This protects against a subtle class of bug: a developer edits a prompt, the app still starts and still returns responses, but the agent's behavior silently gets worse. Regression tests catch this.

### Test Results

```text
11 tests
11 passed
0 failed
```

```text
================================= 11 passed in 0.25s =================================
```

Covering retrieval routing, memory routing, tool avoidance, and prompt regression protection.

---

## Request Flow

```text
Client
  |
  | POST /chat
  v
Gateway
  |
  | user_id + message
  v
Agent
  |
  +----> Decide routing
  +----> Retrieval (if required)
  +----> Memory (if required)
  +----> LLM
  |
  v
Gateway
  |
  v
Client
```

At the same time, telemetry is generated:

```text
Service → OpenTelemetry → OTel Collector → Jaeger
                                         → Metrics pipeline → Prometheus → Grafana
```

The request is both **executed** and **observed**.

---

## API

### Health

```http
GET /health
```

Verifies that the Gateway is running.

### Chat

```http
POST /chat
```

Request:

```json
{
  "user_id": "day84-test-user",
  "message": "What is distributed tracing?"
}
```

Example response:

```json
{
  "answer": "Mock LLM response...",
  "request_id": "2ea26b47-78a9-41d4-ac7e-b0de71e40e0d",
  "prompt_version": "v1"
}
```

- **answer** — the generated answer
- **request_id** — a unique identifier for the request, useful for correlating application behavior with telemetry
- **prompt_version** — the version of the prompt used to process the request, useful for evaluation and regression analysis

### OpenAPI

```text
GET /openapi.json
```

Exposes `/health` and `/chat` along with FastAPI's documentation endpoints (`/docs`, `/redoc`).

---

## Docker Compose

Start the entire stack:

```bash
docker compose up --build
```

Services managed by Compose:

```text
observability-gateway
observability-agent
observability-retrieval
observability-memory
observability-llm

observability-otel-collector
observability-prometheus
observability-grafana
observability-jaeger
```

---

## Project Structure

```text
cross-service-ai-observability/
│
├── evals/
│   ├── agent/
│   │   └── test_routing.py
│   │
│   └── regression/
│       └── test_retrieval_prompt_regression.py
│
├── libs/
│   └── otel_common/
│       └── ...
│
├── observability/
│   ├── grafana/
│   │   └── dashboards/
│   │       └── cross-service-observability.json
│   │
│   ├── prometheus/
│   │   └── ...
│   │
│   ├── jaeger/
│   │   └── ...
│   │
│   └── otel-collector/
│       └── ...
│
├── prompts/
│   └── ...
│
├── services/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   ├── agent/
│   │   ├── Dockerfile
│   │   ├── ...
│   │   └── requirements.txt
│   │
│   ├── retrieval/
│   │   ├── Dockerfile
│   │   ├── ...
│   │   └── requirements.txt
│   │
│   ├── memory/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   └── llm/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
│
├── docker-compose.yml
├── pytest.ini
├── RUNBOOK.md
├── README.md
└── .env.example
```

---

## Getting Started

### Requirements

- Docker Desktop
- Docker Compose
- Python 3.12+
- Git

Optional: PowerShell, VS Code, Postman (or another API client).

### Clone the Repository

```bash
git clone https://github.com/rishisingh1406/Cross-Service-Observability-Evaluation-Platform.git
cd Cross-Service-Observability-Evaluation-Platform
```

If the repo contains a nested project directory:

```bash
cd cross-service-ai-observability
```

---

## Running the System

Build and start all services:

```bash
docker compose up --build
```

Run in detached (background) mode:

```bash
docker compose up --build -d
docker compose ps
```

Stop the stack:

```bash
docker compose down
```

---

## Testing

Run the evaluation suite:

```bash
pytest evals -v
```

Expected result:

```text
collected 11 items

evals/agent/test_routing.py::test_routing_case[policy_question_uses_retrieval] PASSED
evals/agent/test_routing.py::test_routing_case[distributed_system_question_uses_retrieval] PASSED
evals/agent/test_routing.py::test_routing_case[observability_question_uses_retrieval] PASSED
evals/agent/test_routing.py::test_routing_case[agent_architecture_question_uses_retrieval] PASSED

evals/agent/test_routing.py::test_routing_case[returning_user_uses_memory] PASSED
evals/agent/test_routing.py::test_routing_case[remember_request_uses_memory] PASSED
evals/agent/test_routing.py::test_routing_case[previous_context_uses_memory] PASSED

evals/agent/test_routing.py::test_routing_case[greeting_skips_tools] PASSED
evals/agent/test_routing.py::test_routing_case[casual_conversation_skips_tools] PASSED
evals/agent/test_routing.py::test_routing_case[simple_thanks_skips_tools] PASSED

evals/regression/test_retrieval_prompt_regression.py::test_retrieval_instruction_is_present PASSED

11 passed
```

---

## Verifying the API

### Gateway routes (from inside the container)

```bash
docker exec observability-gateway python -c "import main; print([r.path for r in main.app.routes])"
```

Expected output includes:

```text
/openapi.json
/docs
/docs/oauth2-redirect
/redoc
/metrics
/health
/chat
```

### Testing the Chat API (PowerShell)

> Adjust the host/port below to match your actual `docker-compose.yml` port mapping (e.g. host `8010` → container `8000`).

```powershell
$body = @{
    user_id = "day84-test-user"
    message = "What is distributed tracing?"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8010/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body |
ConvertTo-Json -Depth 10
```

Expected response structure:

```json
{
  "answer": "...",
  "request_id": "...",
  "prompt_version": "v1"
}
```

The `request_id` changes on every request.

### Verifying OpenAPI

```powershell
$openapi = Invoke-RestMethod "http://localhost:8010/openapi.json"
$openapi.paths
```

`/chat` should appear as a `POST` endpoint accepting:

```json
{ "user_id": "string", "message": "string" }
```

and returning:

```json
{ "answer": "string", "request_id": "string", "prompt_version": "string" }
```

---

## Observability Verification

**Level 1 — Application**
```text
Gateway is running
Agent is running
Retrieval is running
Memory is running
LLM is running
```

**Level 2 — Metrics**
```text
Prometheus
    +-- Gateway metrics
    +-- Agent metrics
    +-- Retrieval metrics
    +-- Memory metrics
    +-- LLM metrics
```

**Level 3 — Traces**
```text
Jaeger
   +-- Gateway spans
   +-- Agent spans
   +-- Retrieval spans
   +-- Memory spans
   +-- LLM spans
```

> Verify Level 3 directly in the Jaeger UI before claiming a fully populated cross-service trace — the current verified claims are: services running, `/metrics` scraping working, and the 11-test evaluation suite passing.

---

## Debugging Workflow

```text
Symptom
   ↓
Check Metrics
   ↓
Identify abnormal service
   ↓
Open distributed trace
   ↓
Inspect waterfall
   ↓
Identify slow span
   ↓
Locate service / operation
   ↓
Inspect application code
   ↓
Fix root cause
   ↓
Re-run request
   ↓
Verify improvement
```

This is documented in more detail in `RUNBOOK.md`.

---

## Latency Incident Simulation

An artificial delay (e.g. `time.sleep(0.5)`) was injected into a service operation to simulate a real production incident, then diagnosed using the debugging workflow above — finding the unusually long span in the trace, identifying the service, and locating the injected delay in code.

---

## Production Engineering Concepts Learned

- **Observability** — understanding what the system is doing internally
- **Distributed Tracing** — following a single request across multiple services
- **Metrics** — measuring application behavior over time
- **Trace Context Propagation** — maintaining request identity across service boundaries
- **Service-Level Monitoring** — each microservice has independent performance characteristics
- **Centralized Telemetry** — one OpenTelemetry Collector instead of isolated pipelines
- **Infrastructure as Code** — dashboards and infra config live in Git
- **Automated Evaluation** — testing AI behavior, not just whether code executes
- **Regression Testing** — protecting important behavior against accidental changes
- **AI System Debugging** — combining logs, metrics, traces, and evaluation results

A production AI system needs more than a model:

```text
Model + Prompt + Tools + Routing + Memory + Retrieval
      + Observability + Evaluation + Regression Testing
```

This project focuses particularly on the final three layers.

---

## Technology Stack

**Programming:** Python, FastAPI, Pytest

**AI / Agent:** LLM service, Agent routing, Retrieval, Memory, Prompt engineering, AI evaluation

**Observability:** OpenTelemetry, OpenTelemetry Collector, Jaeger, Prometheus, Grafana

**Infrastructure:** Docker, Docker Compose

**Testing:** Pytest, DeepEval

**Version Control:** Git, GitHub

---

## Current Status

```text
Gateway        :8000
Agent          :8001
Retrieval      :8002
Memory         :8003
LLM            :8004
```

Observability infrastructure running: OpenTelemetry Collector, Prometheus, Grafana, Jaeger.

- API verified
- Docker Compose environment builds successfully
- Prometheus successfully scrapes application metrics endpoints
- Evaluation suite: **11 passed, 0 failed**
- Grafana dashboard stored in repo at `observability/grafana/dashboards/cross-service-observability.json`
- Distributed debugging runbook included

---

## Release

```text
v1.0.0
```

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## Future Improvements

1. **Real LLM Provider** — replace the mock LLM response with a production model provider
2. **Advanced LLM Metrics** — input/output/total tokens, time to first token, generation latency, model errors, cost per request
3. **Advanced Evaluation** — faithfulness, answer relevancy, contextual relevancy, tool correctness, retrieval quality, groundedness, response quality
4. **Trace-Based Evaluation** — connect evaluation results directly to trace IDs so incorrect evaluations can be investigated through their corresponding trace
5. **CI/CD Integration** — run the evaluation suite automatically on every pull request (unit tests, agent evaluations, regression tests, Docker build)
6. **Alerting** — Prometheus alert rules for high latency, high error rate, service downtime, retrieval/LLM failures
7. **Production Deployment** — extend to Kubernetes, managed observability infrastructure, cloud-hosted services, distributed databases, production LLM providers

---

## What I Learned

This project taught me that building reliable AI systems requires much more than making an LLM generate a response.

I learned how to think about an AI application as a **distributed system** composed of independent services. The Gateway, Agent, Retrieval, Memory, and LLM services each have their own responsibilities, failure modes, and performance characteristics. Docker Compose let me reproduce this architecture locally and understand how multiple containers communicate as a single application.

I learned how **OpenTelemetry** can act as a common instrumentation layer across services, rather than bolting unrelated monitoring logic onto each one — especially important since a single user request can cross several service boundaries.

I learned how to use **distributed tracing to debug latency**: inspect the trace and waterfall, identify the slow span, locate the corresponding service and operation, then investigate the code. Deliberately injecting latency into a service helped me understand this from an incident-response perspective.

I also learned the difference between **observability and evaluation**. Observability tells me what happened inside the system; evaluation tells me whether the system behaved correctly. An agent can be fast and technically healthy while still making the wrong routing decision — so production AI systems need both telemetry and behavioral evaluation.

Another lesson: **prompts are part of the software system**. A prompt change can alter behavior just like a code change. The retrieval prompt regression test showed me how important instructions can be protected through automated testing, treating prompts as versioned, testable engineering artifacts.

I learned how to evaluate **agent routing decisions** rather than just the final generated answer — because in agentic systems, the internal decision path can matter as much as the response itself.

I learned the importance of **metrics and dashboards**, with Prometheus providing time-series data and Grafana the visualization layer, and storing the dashboard as JSON introduced me to dashboard-as-code and reproducible observability infrastructure.

I also learned that **request IDs and prompt versions are important metadata** — a request ID connects an API call to logs, traces, and debugging information, while a prompt version helps determine which instruction set produced a given behavior.

Most importantly, this project changed how I think about AI engineering. Building an AI application isn't simply `User → LLM → Answer`. A production-oriented system looks closer to:

```text
User → Gateway → Agent → Routing → Retrieval / Memory / Tools → LLM → Response
```

running alongside an observability layer (`OpenTelemetry → Collector → Jaeger/Prometheus/Grafana`) and an evaluation layer (`Evaluation → Regression Tests → Behavior Verification`).

> **A production AI engineer does not only build agents. They build systems that can be observed, evaluated, debugged, tested, and trusted.**

---

## Author

**Rishi Singh**
Computer Science / AI & ML Student

Focused on: Agentic AI, AI Engineering, Context Engineering, Evaluation Harnesses, Distributed Systems, Observability, LLM Systems, Production AI Infrastructure

- GitHub: [github.com/rishisingh1406](https://github.com/rishisingh1406)
- Project: [Cross-Service-Observability-Evaluation-Platform](https://github.com/rishisingh1406/Cross-Service-Observability-Evaluation-Platform)

---

## License

This project is intended primarily as an educational and engineering portfolio project demonstrating distributed AI systems, observability, evaluation, and production-oriented engineering practices.
