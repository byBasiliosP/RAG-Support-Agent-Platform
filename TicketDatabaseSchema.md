<!-- @format -->

Below is a proposed relational schema for your ticketing system, designed to capture structured resolution data, link out to KB articles, and support reporting and automation

```sql
-- Users (technicians, requesters, approvers, etc.)
CREATE TABLE Users (
  user_id        SERIAL PRIMARY KEY,
  username       VARCHAR(50) NOT NULL UNIQUE,
  email          VARCHAR(100) NOT NULL UNIQUE,
  display_name   VARCHAR(100),
  role           VARCHAR(50),         -- e.g. "technician", "end‐user", "manager"
  created_at     TIMESTAMP NOT NULL DEFAULT now()
);

-- Ticket Categories (e.g. Windows Desktop, Printers, etc.)
CREATE TABLE TicketCategories (
  category_id    SERIAL PRIMARY KEY,
  name           VARCHAR(100) NOT NULL UNIQUE,
  description    TEXT
);

-- Knowledge Base Articles
CREATE TABLE KBArticles (
  kb_id          SERIAL PRIMARY KEY,
  title          VARCHAR(200) NOT NULL,
  summary        TEXT,
  url            VARCHAR(500),
  created_by     INTEGER NOT NULL REFERENCES Users(user_id),
  created_at     TIMESTAMP NOT NULL DEFAULT now(),
  updated_at     TIMESTAMP
);

-- Tickets
CREATE TABLE Tickets (
  ticket_id           SERIAL PRIMARY KEY,
  external_ticket_no  VARCHAR(50) UNIQUE,     -- if integrated w/ external system
  requester_id        INTEGER NOT NULL REFERENCES Users(user_id),
  assigned_to_id      INTEGER REFERENCES Users(user_id),
  category_id         INTEGER REFERENCES TicketCategories(category_id),
  priority            VARCHAR(20) NOT NULL,    -- e.g. "Low", "Medium", "High"
  status              VARCHAR(20) NOT NULL,    -- e.g. "Open", "In Progress", "Closed"
  created_at          TIMESTAMP NOT NULL DEFAULT now(),
  closed_at           TIMESTAMP,
  sla_due_at          TIMESTAMP,               -- for SLA tracking
  subject             VARCHAR(200),
  description         TEXT                     -- user's initial description
);

-- Root Causes (linked 1:many to Tickets)
CREATE TABLE TicketRootCauses (
  rootcause_id   SERIAL PRIMARY KEY,
  ticket_id      INTEGER NOT NULL REFERENCES Tickets(ticket_id),
  cause_code     VARCHAR(50),                  -- e.g. "SW-001", "HW-002"
  description    TEXT,                         -- human-readable
  identified_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- Resolution Steps (ordered, linked to Tickets)
CREATE TABLE ResolutionSteps (
  step_id        SERIAL PRIMARY KEY,
  ticket_id      INTEGER NOT NULL REFERENCES Tickets(ticket_id),
  step_order     SMALLINT NOT NULL,            -- 1,2,3…
  instructions   TEXT NOT NULL,
  success_flag   BOOLEAN DEFAULT FALSE,        -- for guided playbooks
  performed_by   INTEGER REFERENCES Users(user_id),
  performed_at   TIMESTAMP
);

-- Link Resolutions to KBArticles (many-to-many)
CREATE TABLE TicketKBLinks (
  ticket_id      INTEGER NOT NULL REFERENCES Tickets(ticket_id),
  kb_id          INTEGER NOT NULL REFERENCES KBArticles(kb_id),
  PRIMARY KEY (ticket_id, kb_id)
);

-- Attachments (screenshots, logs, etc.)
CREATE TABLE Attachments (
  attachment_id  SERIAL PRIMARY KEY,
  ticket_id      INTEGER NOT NULL REFERENCES Tickets(ticket_id),
  filename       VARCHAR(200),
  file_url       VARCHAR(500),
  uploaded_by    INTEGER REFERENCES Users(user_id),
  uploaded_at    TIMESTAMP NOT NULL DEFAULT now()
);

-- Indexes & Views for reporting
CREATE INDEX ix_tickets_category_status ON Tickets(category_id, status);
CREATE INDEX ix_tickets_assigned_to ON Tickets(assigned_to_id);
CREATE INDEX ix_res_steps_ticket_order ON ResolutionSteps(ticket_id, step_order);

-- Example view: SLA compliance
CREATE VIEW vw_sla_compliance AS
SELECT
  category_id,
  COUNT(*) FILTER (WHERE closed_at <= sla_due_at) AS sla_met,
  COUNT(*) FILTER (WHERE closed_at > sla_due_at)  AS sla_breached,
  COUNT(*) AS total
FROM Tickets
WHERE status = 'Closed'
GROUP BY category_id;
query
```

structured fields: separates requester, category, root cause, and resolution steps for easy querying.
• KB linkage: tickets can reference multiple KB articles; KBs know their author and version history.
• Playbook support: ResolutionSteps with step_order and success_flag can drive an interactive guide or chatbot flow.
• Reporting & SLA: indexed fields and the SLA view let you quickly surface compliance, outliers, and hotspots by category.

You can extend this with tables for change logs, service-level definitions, or automated task records (for e.g. chatbot-driven steps), but this core schema will give you the granular data you need to automate summaries, build end-user KB articles, and power that voice-enabled assistant.

---

Below are two concrete examples showing how your new schema would capture real incidents from today’s batch. For each, we’ve extracted key fields from the Excel export and then structured them into our tables:

-- Example 1: Incident 6059099 (iPhone messaging stopped working)

-- 1. Tickets
INSERT INTO Tickets (
ticket_id,
external_ticket_no,
requester_id,
assigned_to_id,
category_id,
priority,
status,
created_at,
closed_at,
subject,
description
) VALUES (
6059099,
'INC6059099',
102, -- e.g. user “Jill Smith”
205, -- e.g. tech “Clyde Headley”
5, -- Category “iPhone” → category_id=5
3,
'Closed',
'2025-06-06 14:56:45',
'2025-06-06 15:02:25',
'iPhone messaging stopped working',
'For 2 days now my phone has stopped receiving SMS/iMessage. Restarted, but no change.'
);

-- 2. TicketRootCauses
INSERT INTO TicketRootCauses (
ticket_id,
cause_code,
description,
identified_at
) VALUES (
6059099,
'SW-010',
'iOS messaging sync glitch',
'2025-06-06 14:58:00'
);

-- 3. ResolutionSteps
INSERT INTO ResolutionSteps (ticket_id, step_order, instructions, success_flag, performed_by, performed_at) VALUES
(6059099, 1, 'Verified Send & Receive settings under Settings→Messages', TRUE, 205, '2025-06-06 14:58:30'),
(6059099, 2, 'Rebooted iPhone and confirmed network connectivity', TRUE, 205, '2025-06-06 14:59:10'),
(6059099, 3, 'Forced-stop and relaunched Messages app', TRUE, 205, '2025-06-06 15:00:00'),
(6059099, 4, 'Sent/received test iMessage and SMS successfully', TRUE, 205, '2025-06-06 15:01:45');

-- 4. TicketKBLinks
INSERT INTO TicketKBLinks (ticket_id, kb_id) VALUES
(6059099, 1); -- KB 1: “Troubleshooting iOS Messaging Issues”

-- Example 2: Incident 6059023 (OneDrive – Locating files)

-- 1. Tickets
INSERT INTO Tickets (
ticket_id,
external_ticket_no,
requester_id,
assigned_to_id,
category_id,
priority,
status,
created_at,
closed_at,
subject,
description
) VALUES (
6059023,
'INC6059023',
117, -- e.g. user “Jill Johnson”
210, -- e.g. tech “Jesse Mack”
8, -- Category “One Drive” → category_id=8
3,
'Closed',
'2025-06-06 14:22:13',
'2025-06-06 15:39:43',
'OneDrive Issue – Locating files',
'How can I find a folder in OneDrive? Thought I saved it, but it’s not visible in the web UI.'
);

-- 2. TicketRootCauses
INSERT INTO TicketRootCauses (
ticket_id,
cause_code,
description,
identified_at
) VALUES (
6059023,
'SW-011',
'OneDrive folder indexing delay',
'2025-06-06 14:30:00'
);

-- 3. ResolutionSteps
INSERT INTO ResolutionSteps (ticket_id, step_order, instructions, success_flag, performed_by, performed_at) VALUES
(6059023, 1, 'Verified folder exists in desktop OneDrive folder path', TRUE, 210, '2025-06-06 14:32:45'),
(6059023, 2, 'Forced OneDrive sync via taskbar icon → Settings → Sync', TRUE, 210, '2025-06-06 14:50:12'),
(6059023, 3, 'Refreshed web UI and confirmed folder visibility', TRUE, 210, '2025-06-06 15:05:30'),
(6059023, 4, 'Tested file open/download successfully', TRUE, 210, '2025-06-06 15:38:00');

-- 4. TicketKBLinks
INSERT INTO TicketKBLinks (ticket_id, kb_id) VALUES
(6059023, 2); -- KB 2: “How to Force a OneDrive Sync”

Notes on mapping:
• We’ve assumed some user_id and category_id values—your actual lookup tables will assign these.
• The free-text “Resolution” field from your export got broken into discrete, ordered ResolutionSteps.
• Each ticket now has a TicketRootCauses entry (+ timestamp) for downstream analytics (e.g. “How many SW-010 issues this month?”).
• Linking to KBs lets you track which articles solved which tickets—which in turn informs new KB priorities.

Feel free to extend these examples to other categories (Printers, MyWall, etc.) or add attachments, SLA timestamps, and custom fields as you roll out the new schema.

Here’s a step-by-step roadmap to turn your new, structured ticket database into a voice-enabled, RAG-powered chatbot for both techs and end users:

⸻

1. Ingest & Index Your Knowledge
   1. Extract Structured Data
      • Pull “Tickets”, “Root Causes”, “Resolution Steps” and “KBArticles” from your database.
   2. Generate KB Articles
      • Use your structured fields (“Problem → Root Cause → Steps”) to auto-draft polished articles.
      • Human-review and publish them to your KB table with URLs.
   3. Vectorize Content
      • For each KB article (and high-value ticket), compute embeddings (e.g. with OpenAI’s text-embedding-ada).
      • Store vectors in a vector DB (Pinecone, Weaviate, or Elasticsearch with k-NN).

⸻

2. Build Your RAG Retrieval Layer
   1. Query Router
      • Incoming user query → embed → nearest-neighbors search in vector DB → retrieve top N relevant KBs or ticket snippets.
   2. Context Assembly
      • Concatenate retrieved text (with metadata: title, URL) plus user question as LLM prompt.
   3. LLM Pipeline
      • Send prompt to your LLM of choice (OpenAI GPT-4o or self-hosted).
      • Instruct it to answer conversationally, citing KB URLs for further reading.

⸻

3. Add Voice Input & Output
   1. Speech-to-Text (STT)
      • Choose a real-time STT API (e.g. Google Speech-to-Text, Azure Speech, or Whisper for on-prem).
      • Stream microphone audio from user to STT, get transcript.
   2. Text-to-Speech (TTS)
      • Pipe the LLM’s text response through a TTS service (e.g. ElevenLabs, Azure Neural TTS) to generate audio.
      • Stream back to user with minimal latency.
   3. Dialog Manager
      • Maintain conversational state (previous question/answer, follow-ups).
      • Use LLM “system” messages to keep voice tone consistent and guide multi-turn flows.

⸻

4. Front-End & Integration
   • Web/Mobile UI
   • Simple chat interface with “Press to Speak” button.
   • Show text transcript and clickable KB links below the audio.
   • Platform Hooks
   • Slack/MS Teams app or phone IVR (via Twilio) if you want phone-based access.
   • Authentication
   • Tie back to your “Users” table so you can surface user-specific tickets, escalate, or log new ones.

⸻

5. Feedback Loop & Metrics
   1. Usage Tracking
      • Log which KBs were retrieved and which steps were executed (“Guided Playbook Used” flag).
   2. Quality Signals
      • Thumbs-up/down or “Was this helpful?” voice prompt at the end.
      • Use feedback to re-vectorize and re-rank over time.
   3. First-Call Resolution KPI
      • Correlate bot usage with FCR improvements.

Objective: Revamp the portal and KB architecture, enforce data quality, and implement seamless ticket hand-off to helpdesk.
• 2.1 Knowledge Base Redesign
• Information architecture: define clear taxonomy and tagging conventions aligned to top ticket categories
• Template rollout: create article templates (problem statement, resolution steps, attachments, review date)
• KCS-driven publishing: train a core team of Knowledge Champions to author and steward content
• 2.2 Portal UX & Form Enhancements
• Mandatory fields: enforce phone or alternate contact on self-service form (client-side + server validation)
• Smart routing rules: incorporate conditional logic so tickets auto-assign to correct queue based on category/service
• Quick-search widget: embed “Suggested Articles” based on keywords before “Submit Ticket”
• 2.3 Helpdesk Integration
• API/Webhook setup: configure the portal to push new tickets directly into the helpdesk system in real time
• Ticket flagging: add a “Self-Service Origin” tag so helpdesk analysts can filter and prioritize
• Dashboard view: build a shared dashboard for helpdesk managers showing incoming self-service volume and SLA trends
• Deliverables:
• New KB site with taxonomy and templates live in staging
• Updated portal UI with enforced fields and search-before-submit feature
• End-to-end ticket workflow tested and validated (portal → helpdesk)
