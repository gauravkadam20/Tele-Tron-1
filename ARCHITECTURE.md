# 🤖 Tele-Tron-1: Architecture in Hand-Drawn Illustrations

A complete 4-part visual architectural walkthrough of the **Tele-Tron-1** autonomous logistics intelligence engine, rendered in minimalist hand-drawn English illustrations.

---

## 1. Data Ingestion: Sensor Chaos to Read-Only Vault

![Part 1: Raw Telematics to Read-Only Vault](docs/assets/01-data-ingestion.jpg)

### What Happens Here:
* **The Raw Input:** Unruly IoT sensor streams—including GPS coordinates, cold-chain temperature readings, fuel consumption gauges, and traffic severity scores—pour into an eccentric intake hopper.
* **Xiaohei's Action:** Xiaohei manually cranks a mechanical sorting machine that stamps and formats raw sensor events into structured database index cards.
* **The Destination:** The clean cards slide along an orange conveyor belt into a reinforced steel safe labeled `SQLite Vault: logistics_data`, sealed with a prominent brass padlock enforcing **`Read-Only Lock (mode=ro)`**.
* **Why It Matters:** Destructive database operations (`DROP`, `DELETE`, `UPDATE`) are physically impossible at the SQLite engine level.

---

## 2. Security Gatekeeper: Dual-Tier Query Protection

![Part 2: Dual-Tier Security Gatekeeper](docs/assets/02-security-gatekeeper.jpg)

### What Happens Here:
* **The Two Arriving Queries:** User questions arrive along the intake track. A malicious or hazardous prompt turns into a spiky black block tagged `"DROP / DELETE"`, while a legitimate analytical request becomes a clean white envelope tagged `"Safe SELECT"`.
* **Xiaohei's Action:** Xiaohei stands as a switch-track operator with a wooden lever. Upon detecting dangerous tokens or stacked statements, Xiaohei flips the switch, opening a trapdoor that drops the spiky block into the `"AST Filter: Blocked"` scrap bin.
* **The Destination:** Clean, non-destructive queries roll straight along the orange rails through the `"Read-Only Gateway"` into execution.
* **Why It Matters:** Multi-statement injections and destructive actions are intercepted before reaching the database connection.

---

## 3. Query Generation: Semantic Catalog & Self-Correction

![Part 3: Semantic Catalog & Self-Correction Engine](docs/assets/03-self-healing-engine.jpg)

### What Happens Here:
* **The Reference Book:** On the left, an oversized blueprint manual on an easel serves as the **`Semantic Catalog`**, detailing business definitions, measurement units (`USD`, `Days`, `Hours`), and executive risk tiers (`'Low Risk'`, `'High Risk'`).
* **The Machinery:** Gemini translates the human question into SQLite inside an eccentric glass beaker containing interlocking mechanical gears.
* **Xiaohei's Action:** When an unexpected syntax error or schema mismatch pops out a spring tagged `"SQLite Error"`, Xiaohei climbs a stepstool with a small mechanic's wrench. Guided by an orange **`Self-Correction Loop`**, Xiaohei quickly retightens the gear, correcting the query on the fly.
* **The Output:** A perfectly formatted, verified scroll tagged `"Validated SQL"` rolls out the output chute.
* **Why It Matters:** Tele-Tron-1 automatically recovers from syntax errors without crashing or burdening the user.

---

## 4. Synthesis: Safety Limiter & Executive Summary

![Part 4: Memory Safety Cap & Executive Synthesizer](docs/assets/04-insight-synthesizer.jpg)

### What Happens Here:
* **The Problem:** The database returns an enormous, unwieldy roll of paper containing `"50,000 Raw Rows"`, which would freeze browser interfaces and overwhelm human reviewers.
* **Xiaohei's Action:**
  1. A mechanical paper cutter with a ruler cleanly slices the data with a **`Safety Cap (100 Rows)`**, protecting memory and rendering latency.
  2. Xiaohei forcefully pushes down on a large rubber stamp press labeled **`Insight Synthesizer`**.
* **The Final Output:** Beneath the stamp emerges a crisp, concise executive insight ticket displaying high-level bullet points, transparent business assumptions, and a mini visual bar chart.
* **Why It Matters:** Business stakeholders get direct, actionable answers and KPIs in seconds instead of drowning in spreadsheet rows.
