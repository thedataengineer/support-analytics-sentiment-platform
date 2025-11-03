# Outstanding Stories & Roadmap

## ✅ COMPLETED MVP Stories

| Story ID | Title | Status | Notes |
|----------|-------|--------|-------|
| ~~STORY-001~~ | ~~Persist ingestion jobs & status API~~ | ✅ COMPLETE | Redis-backed job tracking with /api/job/{id} and /api/jobs endpoints implemented |
| ~~STORY-004~~ | ~~Database-backed sentiment overview~~ | ✅ COMPLETE | Real PostgreSQL queries with caching in report_api.py |
| ~~STORY-006~~ | ~~Job status frontend experience~~ | ✅ COMPLETE | JobStatusPage and JobListPage components exist |
| ~~STORY-009~~ | ~~Parquet ingestion pipeline~~ | ✅ COMPLETE | Async Celery task with chunked processing |

---

## 🟡 PARTIALLY COMPLETE - Need Finishing Touches

### STORY-002: Make CSV Processing Fully Asynchronous
**Current State:** CSV processing runs synchronously on API thread (backend/api/ingest_csv.py:186)
**Remaining Work:**
- Replace `process_csv_upload(file_path, job_id)` with `celery_app.send_task("backend.jobs.ingest_job.process_csv_task", args=[file_path, job_id])`
- Create Celery task wrapper for process_csv_upload
- Return immediately with job_id instead of waiting for completion
- Update tests to use async patterns

**Acceptance Criteria:**
- `/api/upload` returns in < 500ms
- Large CSVs process in background
- Job status updates visible via polling

---

### STORY-003: Add Authentication to JSON Ingest API
**Current State:** Basic endpoint exists but no auth and Celery is commented out (backend/api/ingest_csv.py:214)
**Remaining Work:**
- Add `@router.post("/data-ingest", dependencies=[Depends(require_role("analyst", "admin"))])` decorator
- Uncomment Celery task dispatch
- Add request validation (max 1000 records, required fields)
- Write tests for auth rejection

**Acceptance Criteria:**
- Endpoint requires valid JWT token
- Only analyst/admin roles can submit
- Batch size limited to 1000 records
- Returns job_id and status_url

---

### STORY-005: Complete Database-Backed Authentication
**Current State:** JWT infrastructure exists but uses hardcoded credentials (backend/api/auth.py:81)
**Remaining Work:**
- Update `/login` to query users table with password verification
- Update `/register` to persist new users to database
- Create `require_role()` dependency for route protection
- Add password reset flow
- Write integration tests

**Acceptance Criteria:**
- Login validates against database
- Passwords hashed with bcrypt/argon2
- Role-based access control on all protected routes
- Admin can create/manage users

---

### STORY-007: Integrate Elasticsearch for Advanced Search
**Current State:** Search uses PostgreSQL ILIKE (backend/api/search_api.py:29)
**Remaining Work:**
- Create Elasticsearch index for tickets
- Index tickets during ingestion (backend/jobs/ingest_job.py)
- Update search_api.py to query Elasticsearch with fallback to PostgreSQL
- Add fuzzy matching and relevance scoring
- Implement entity aggregation endpoint

**Acceptance Criteria:**
- Full-text search across 100k+ tickets in < 500ms
- Fuzzy matching for typos
- Faceted search (by sentiment, entity, date)
- Entity aggregation API: `/api/entities/top`

---

### STORY-008: Scheduled Reporting with Email Delivery
**Current State:** PDF generation works from real data but no scheduling (backend/services/report_summarizer.py)
**Remaining Work:**
- Create Celery Beat schedule for daily/weekly reports
- Implement email service with SendGrid/SMTP
- Add user_preferences table for report schedules
- Create `/api/report/schedule` endpoint
- Generate reports from live data and attach to emails

**Acceptance Criteria:**
- Users can configure daily/weekly report schedules
- Reports emailed at configured times
- Reports contain real sentiment data and charts
- Unsubscribe link included

---

## 🚀 NEW WORLD-CLASS FEATURES

### STORY-010: Predictive Churn Risk Scoring
**Priority:** HIGH | **Effort:** Large | **Impact:** High

Build ML model to predict customer churn risk based on support patterns.

**Features:**
- **Churn Score Calculation**: Analyze sentiment trajectory, escalation count, response time, executive involvement
- **Risk Factors API**: `/api/analytics/churn-risk` returns risk score (0-100) with contributing factors
- **Alert Thresholds**: Configurable alerts when accounts exceed risk threshold
- **Historical Training**: Train model on tickets with known churn outcomes
- **Dashboard Widget**: Real-time churn risk leaderboard

**Data Science Mockup:**
```python
# backend/ml/churn_predictor.py
from sklearn.ensemble import GradientBoostingClassifier

class ChurnPredictor:
    def predict_risk(self, ticket_history: List[Ticket]) -> Dict:
        features = {
            'sentiment_decline': calculate_sentiment_slope(ticket_history),
            'escalation_count': count_escalations(ticket_history),
            'avg_response_time': calculate_avg_response_time(ticket_history),
            'executive_mentions': count_executive_mentions(ticket_history),
            'ticket_velocity': calculate_velocity(ticket_history),
        }

        risk_score = self.model.predict_proba([features])[0][1] * 100

        return {
            'risk_score': risk_score,
            'risk_level': 'high' if risk_score > 70 else 'medium' if risk_score > 40 else 'low',
            'contributing_factors': rank_features(features),
            'recommended_action': get_recommendation(risk_score)
        }
```

**API Endpoint:**
```python
@router.get("/analytics/churn-risk")
async def get_churn_risk(
    account_id: Optional[str] = None,
    threshold: int = Query(70, description="Risk threshold for alerts"),
    db: Session = Depends(get_db)
):
    if account_id:
        # Single account risk
        tickets = get_account_tickets(db, account_id)
        return churn_predictor.predict_risk(tickets)
    else:
        # All high-risk accounts
        high_risk_accounts = []
        for account in get_all_accounts(db):
            risk = churn_predictor.predict_risk(account.tickets)
            if risk['risk_score'] > threshold:
                high_risk_accounts.append({
                    'account_id': account.id,
                    'account_name': account.name,
                    **risk
                })
        return sorted(high_risk_accounts, key=lambda x: x['risk_score'], reverse=True)
```

**Acceptance Criteria:**
- Model trained on historical data with >75% accuracy
- API returns risk score in < 1 second
- Dashboard shows top 20 at-risk accounts
- Alert sent to Slack when account enters high-risk zone
- Explainable predictions (show contributing factors)

---

### STORY-011: Smart Ticket Routing & Assignment
**Priority:** HIGH | **Effort:** Medium | **Impact:** High

ML-based routing to assign tickets to best-fit agents.

**Features:**
- **Agent Specialization Detection**: Analyze historical resolution patterns by category/product
- **Skills Matrix**: Auto-build agent expertise profiles
- **Routing Model**: Train classifier on (ticket features) → (best agent)
- **Real-Time Assignment**: API to suggest agent for new ticket
- **Performance Tracking**: Resolution rate by agent-category combination

**Implementation:**
```python
# backend/services/ticket_router.py
class TicketRouter:
    def suggest_agent(self, ticket: Ticket) -> Dict:
        # Extract ticket features
        features = {
            'sentiment': ticket.ultimate_sentiment,
            'category': classify_category(ticket.summary),
            'urgency': calculate_urgency(ticket),
            'complexity': estimate_complexity(ticket),
            'entities': extract_product_mentions(ticket),
        }

        # Find best agent based on historical performance
        agent_scores = []
        for agent in self.agents:
            score = calculate_match_score(agent, features)
            agent_scores.append({
                'agent_id': agent.id,
                'agent_name': agent.name,
                'match_score': score,
                'avg_resolution_time': agent.get_avg_resolution_time(features['category']),
                'success_rate': agent.get_success_rate(features['category']),
            })

        return sorted(agent_scores, key=lambda x: x['match_score'], reverse=True)[:3]
```

**API:**
```python
@router.post("/tickets/route")
async def route_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    suggestions = ticket_router.suggest_agent(ticket)
    return {
        'ticket_id': ticket_id,
        'recommended_agents': suggestions,
        'routing_confidence': suggestions[0]['match_score']
    }
```

**Acceptance Criteria:**
- Agent suggestions returned in < 500ms
- Routing improves resolution time by 20%
- Agent specialization dashboard shows expertise areas
- Integration hook for auto-assignment in ticketing systems

---

### STORY-012: Intent Classification & Auto-Tagging
**Priority:** MEDIUM | **Effort:** Medium | **Impact:** High

Automatically classify ticket intent and apply tags.

**Features:**
- **Intent Taxonomy**: Bug report, feature request, how-to, billing issue, access problem, etc.
- **Multi-Label Classification**: Tickets can have multiple tags
- **Custom Entity Training**: Product names, feature areas, API endpoints
- **Auto-Triage**: Priority assignment based on intent + sentiment
- **Tag Analytics**: Most common intents by time period

**Model:**
```python
# ml/intent_classifier.py
from transformers import pipeline

class IntentClassifier:
    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

        self.intent_labels = [
            "bug_report", "feature_request", "how_to_question",
            "billing_issue", "access_problem", "performance_issue",
            "security_concern", "integration_help", "data_question"
        ]

    def classify(self, text: str) -> List[Dict]:
        result = self.classifier(text, self.intent_labels, multi_label=True)

        # Return all intents with confidence > 0.5
        intents = []
        for label, score in zip(result['labels'], result['scores']):
            if score > 0.5:
                intents.append({
                    'intent': label,
                    'confidence': score
                })

        return intents
```

**Integration:**
```python
# backend/jobs/ingest_job.py (add to process_chunk)
# After sentiment analysis:
intents = intent_classifier.classify(combined_text)
for intent_data in intents:
    tag = TicketTag(
        ticket_id=ticket_id,
        tag_type='intent',
        tag_value=intent_data['intent'],
        confidence=intent_data['confidence']
    )
    db.add(tag)
```

**Acceptance Criteria:**
- Auto-tag 90%+ of tickets with correct intent
- Multi-label support (e.g., bug + security)
- Custom labels trainable via UI
- Tag analytics dashboard
- Filter/search by intent tags

---

### STORY-013: Real-Time Operational Dashboard
**Priority:** HIGH | **Effort:** Medium | **Impact:** Medium

Live dashboard for support operations with alerting.

**Features:**
- **Live Metrics**: Current queue depth, tickets created last hour, SLA breach risk
- **Agent Status**: Online/offline, active tickets, avg handle time
- **Anomaly Detection**: Alert on unusual spikes (2σ above baseline)
- **WebSocket Updates**: Real-time metric updates without polling
- **Role-Based Views**: Different dashboards for support agents, managers, executives
- **Customizable Widgets**: Drag-and-drop dashboard builder

**Backend (WebSockets):**
```python
# backend/api/realtime.py
from fastapi import WebSocket
import asyncio

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            metrics = get_live_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        pass

def get_live_metrics():
    with get_db_context() as db:
        last_hour = datetime.now() - timedelta(hours=1)

        return {
            'queue_depth': count_open_tickets(db),
            'tickets_created_last_hour': count_tickets_since(db, last_hour),
            'avg_response_time_minutes': get_avg_response_time(db, last_hour),
            'sentiment_distribution': get_sentiment_counts(db, last_hour),
            'sla_breach_risk': calculate_sla_risk(db),
            'active_agents': count_active_agents(),
        }
```

**Frontend:**
```jsx
// client/src/components/LiveDashboard/LiveDashboard.js
function LiveDashboard() {
    const [metrics, setMetrics] = useState(null);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws/metrics');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setMetrics(data);

            // Alert on anomalies
            if (data.sla_breach_risk > 0.7) {
                showAlert('High SLA breach risk!', 'error');
            }
        };

        return () => ws.close();
    }, []);

    return (
        <Grid container spacing={3}>
            <MetricCard title="Queue Depth" value={metrics?.queue_depth} />
            <MetricCard title="Last Hour" value={metrics?.tickets_created_last_hour} />
            <SentimentChart data={metrics?.sentiment_distribution} />
            <SLAGauge risk={metrics?.sla_breach_risk} />
        </Grid>
    );
}
```

**Acceptance Criteria:**
- Metrics update in real-time (< 5 second latency)
- Anomaly alerts via Slack/email
- Custom dashboard builder with save/share
- Mobile-responsive
- Historical playback mode

---

### STORY-014: Proactive Automation Workflows
**Priority:** MEDIUM | **Effort:** Large | **Impact:** High

Visual workflow builder for automating support actions.

**Features:**
- **Trigger Conditions**: If sentiment=negative AND ticket_reopened > 2 THEN...
- **Actions**: Escalate, assign, tag, notify, send email, webhook
- **Visual Builder**: Drag-and-drop workflow designer (like Zapier)
- **Workflow Templates**: Pre-built for common scenarios
- **Audit Log**: Track all automated actions

**Workflow Engine:**
```python
# backend/services/workflow_engine.py
class WorkflowEngine:
    def evaluate_ticket(self, ticket: Ticket) -> List[Action]:
        actions = []

        for workflow in self.active_workflows:
            if self.evaluate_conditions(workflow.conditions, ticket):
                actions.extend(workflow.actions)

        return actions

    def evaluate_conditions(self, conditions: List[Condition], ticket: Ticket) -> bool:
        for condition in conditions:
            if condition.field == 'sentiment':
                if ticket.ultimate_sentiment != condition.value:
                    return False
            elif condition.field == 'escalation_count':
                if count_escalations(ticket) < condition.value:
                    return False
            # ... more conditions

        return True

    async def execute_actions(self, actions: List[Action], ticket: Ticket):
        for action in actions:
            if action.type == 'escalate':
                await escalate_ticket(ticket, action.params['tier'])
            elif action.type == 'notify':
                await send_notification(action.params['channel'], ticket)
            elif action.type == 'assign':
                await assign_ticket(ticket, action.params['agent_id'])
            # ... more actions
```

**API:**
```python
@router.post("/workflows")
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    # Save workflow definition
    db_workflow = Workflow(
        name=workflow.name,
        conditions=json.dumps(workflow.conditions),
        actions=json.dumps(workflow.actions),
        enabled=True
    )
    db.add(db_workflow)
    db.commit()
    return {"workflow_id": db_workflow.id}

@router.post("/workflows/{workflow_id}/test")
async def test_workflow(workflow_id: int, ticket_id: str, db: Session = Depends(get_db)):
    # Dry run to see what actions would trigger
    workflow = db.query(Workflow).get(workflow_id)
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

    actions = workflow_engine.evaluate_ticket(ticket)
    return {
        'would_trigger': len(actions) > 0,
        'actions': [{'type': a.type, 'params': a.params} for a in actions]
    }
```

**Acceptance Criteria:**
- Visual workflow builder in UI
- 10+ pre-built templates
- Test mode (dry run)
- Workflow execution within 1 second of trigger
- Audit trail for compliance

---

### STORY-015: Customer 360° Health Score
**Priority:** MEDIUM | **Effort:** Large | **Impact:** High

Comprehensive account health scoring combining support + product usage.

**Features:**
- **Multi-Signal Health Score**: Support sentiment + product usage + financial metrics
- **Trend Detection**: Improving, declining, stable
- **Account Timeline**: Visual journey showing key events
- **Integration Points**: Connect to CRM (Salesforce), product analytics (Amplitude)
- **Health Change Alerts**: Notify CSM when health drops

**Health Calculator:**
```python
# backend/services/health_scorer.py
class HealthScorer:
    def calculate_health(self, account: Account) -> Dict:
        # Support signals (40% weight)
        support_score = self._calculate_support_health(account)

        # Product usage signals (40% weight)
        usage_score = self._calculate_usage_health(account)

        # Financial signals (20% weight)
        financial_score = self._calculate_financial_health(account)

        overall_health = (
            support_score * 0.4 +
            usage_score * 0.4 +
            financial_score * 0.2
        )

        return {
            'account_id': account.id,
            'account_name': account.name,
            'overall_health': overall_health,
            'health_grade': self._get_grade(overall_health),
            'trend': self._calculate_trend(account),
            'breakdown': {
                'support': support_score,
                'usage': usage_score,
                'financial': financial_score
            },
            'risk_factors': self._identify_risks(account),
            'opportunities': self._identify_opportunities(account)
        }

    def _calculate_support_health(self, account: Account) -> float:
        tickets = get_account_tickets(account.id)

        # Positive factors
        resolution_rate = calculate_resolution_rate(tickets)
        avg_sentiment = calculate_avg_sentiment(tickets)

        # Negative factors
        escalation_rate = calculate_escalation_rate(tickets)
        open_critical = count_open_critical_tickets(tickets)

        score = (
            resolution_rate * 0.3 +
            (avg_sentiment + 1) / 2 * 0.4 +  # Convert -1,1 to 0,1
            (1 - escalation_rate) * 0.2 +
            max(0, 1 - open_critical * 0.1) * 0.1
        )

        return score * 100
```

**Dashboard:**
```jsx
// client/src/pages/AccountHealth/AccountHealthDashboard.js
function AccountHealthDashboard() {
    const [accounts, setAccounts] = useState([]);

    useEffect(() => {
        fetch('/api/analytics/health-scores')
            .then(res => res.json())
            .then(data => setAccounts(data.accounts));
    }, []);

    return (
        <>
            <HealthDistributionChart accounts={accounts} />
            <AtRiskAccountsList
                accounts={accounts.filter(a => a.health_grade === 'at_risk')}
            />
            <AccountTimeline />
        </>
    );
}
```

**Acceptance Criteria:**
- Health score calculated for all accounts
- Trend detection (7/30/90 day windows)
- Dashboard shows distribution and at-risk list
- Alerts when account drops grade
- Integration with Salesforce (sync health score to custom field)

---

### STORY-016: Advanced NLP - Topic Modeling
**Priority:** LOW | **Effort:** Medium | **Impact:** Medium

Unsupervised discovery of emerging support topics.

**Features:**
- **Topic Extraction**: Use LDA or BERTopic to find hidden themes
- **Topic Trends**: Track topic volume over time
- **Anomaly Detection**: Alert when new topic emerges rapidly
- **Topic-Sentiment Correlation**: Which topics have worst sentiment?
- **Visualizations**: Topic clouds, trend lines, correlation heatmaps

**Implementation:**
```python
# ml/topic_modeler.py
from bertopic import BERTopic

class TopicModeler:
    def __init__(self):
        self.model = BERTopic(
            embedding_model="all-MiniLM-L6-v2",
            min_topic_size=10
        )

    def discover_topics(self, texts: List[str], timestamps: List[datetime]) -> Dict:
        topics, probs = self.model.fit_transform(texts)

        topic_info = self.model.get_topic_info()

        # Calculate topic trends
        topic_trends = {}
        for topic_id in set(topics):
            topic_docs = [t for i, t in enumerate(timestamps) if topics[i] == topic_id]
            topic_trends[topic_id] = calculate_trend(topic_docs)

        return {
            'topics': [
                {
                    'id': row.Topic,
                    'size': row.Count,
                    'representative_words': self.model.get_topic(row.Topic),
                    'trend': topic_trends.get(row.Topic, 'stable')
                }
                for _, row in topic_info.iterrows()
            ],
            'topic_assignments': topics,
            'visualizations': {
                'topic_hierarchy': self.model.visualize_hierarchy(),
                'topic_similarity': self.model.visualize_heatmap()
            }
        }
```

**Acceptance Criteria:**
- Discover topics from 10k+ tickets
- Topic discovery runs daily via Celery Beat
- Dashboard shows top topics with trends
- Alert on rapidly growing topics
- Export topic assignments to CSV

---

### STORY-017: Multi-Channel Ingestion Pipeline
**Priority:** HIGH | **Effort:** Large | **Impact:** High

Expand beyond CSV to ingest from email, chat, phone, social media.

**Channels to Support:**
- **Email**: IMAP/POP3 connector, parse threads
- **Chat**: Slack, Intercom, Zendesk Chat webhooks
- **Phone**: Transcribe with Whisper API, analyze transcripts
- **Social**: Twitter, LinkedIn mentions via APIs
- **Community**: Discourse, Stack Overflow scraping

**Architecture:**
```python
# backend/connectors/base.py
class BaseConnector:
    def fetch_new_messages(self) -> List[Message]:
        raise NotImplementedError

    def transform_to_ticket(self, message: Message) -> Ticket:
        raise NotImplementedError

# backend/connectors/email_connector.py
import imaplib

class EmailConnector(BaseConnector):
    def __init__(self, host, username, password):
        self.client = imaplib.IMAP4_SSL(host)
        self.client.login(username, password)

    def fetch_new_messages(self) -> List[Message]:
        self.client.select('INBOX')
        status, messages = self.client.search(None, 'UNSEEN')

        emails = []
        for msg_id in messages[0].split():
            status, data = self.client.fetch(msg_id, '(RFC822)')
            raw_email = data[0][1]
            email_msg = parse_email(raw_email)
            emails.append(email_msg)

        return emails

    def transform_to_ticket(self, message: Message) -> Ticket:
        return Ticket(
            ticket_id=f"EMAIL-{message.message_id}",
            summary=message.subject,
            description=message.body,
            source='email',
            customer_email=message.from_address
        )

# Celery task to poll connectors
@celery_app.task
def poll_connectors():
    for connector in get_active_connectors():
        messages = connector.fetch_new_messages()
        for message in messages:
            ticket = connector.transform_to_ticket(message)
            ingest_ticket(ticket)
```

**Acceptance Criteria:**
- Email connector fetches every 5 minutes
- Chat webhook handlers for Slack/Intercom
- Phone transcription via OpenAI Whisper
- Unified ticket format across channels
- Channel-specific metadata preserved

---

### STORY-018: Integration Marketplace
**Priority:** MEDIUM | **Effort:** Large | **Impact:** High

Pre-built connectors for popular tools.

**Integrations:**
1. **Zendesk**: Bidirectional sync (pull tickets, push sentiment scores)
2. **Jira Service Desk**: Auto-create tickets from analysis results
3. **Salesforce**: Sync account health to custom fields
4. **Slack**: Alerts, slash commands for querying
5. **Datadog**: Push metrics for monitoring
6. **Amplitude**: Correlate product events with support issues
7. **Snowflake**: Replicate analytics data to warehouse

**Architecture:**
```python
# backend/integrations/registry.py
class IntegrationRegistry:
    integrations = {}

    @classmethod
    def register(cls, name: str, integration_class):
        cls.integrations[name] = integration_class

    @classmethod
    def get(cls, name: str):
        return cls.integrations.get(name)

# backend/integrations/zendesk.py
@IntegrationRegistry.register('zendesk')
class ZendeskIntegration:
    def __init__(self, subdomain, email, api_token):
        self.client = Zenpy(subdomain=subdomain, email=email, token=api_token)

    def sync_sentiment_to_ticket(self, ticket_id: str, sentiment: str, confidence: float):
        # Update Zendesk ticket custom field
        ticket = self.client.tickets(id=ticket_id)
        ticket.custom_fields.append({
            'id': 360000123456,  # Custom field ID
            'value': f"{sentiment} ({confidence:.2f})"
        })
        self.client.tickets.update(ticket)

    def pull_recent_tickets(self, since: datetime) -> List[Ticket]:
        # Fetch tickets created since timestamp
        zd_tickets = self.client.search(type='ticket', created_after=since)

        return [self.transform_ticket(t) for t in zd_tickets]
```

**Configuration UI:**
```jsx
// client/src/pages/Integrations/IntegrationConfig.js
function IntegrationConfig() {
    const [integrations, setIntegrations] = useState([]);

    const connectZendesk = async (subdomain, email, apiToken) => {
        await fetch('/api/integrations/zendesk', {
            method: 'POST',
            body: JSON.stringify({ subdomain, email, api_token: apiToken })
        });
    };

    return (
        <Grid>
            <IntegrationCard
                name="Zendesk"
                icon={<ZendeskIcon />}
                connected={hasIntegration('zendesk')}
                onConnect={connectZendesk}
            />
            {/* More integrations */}
        </Grid>
    );
}
```

**Acceptance Criteria:**
- 5+ integrations live
- OAuth flows for supported platforms
- Configuration UI for credentials
- Health checks for integration status
- Rate limiting and retry logic

---

### STORY-019: Custom Report Builder
**Priority:** LOW | **Effort:** Medium | **Impact:** Medium

Drag-and-drop report builder like Looker.

**Features:**
- **Visual Query Builder**: Select dimensions (date, sentiment, agent) and metrics (count, avg confidence)
- **Filters**: Date range, sentiment type, ticket status
- **Visualizations**: Bar, line, pie, table, heatmap
- **Scheduled Reports**: Email weekly/monthly
- **Share Links**: Public URLs for dashboards
- **Export**: CSV, PDF, PNG

**Implementation uses existing dashboard components but adds:**
- Saved report definitions in database
- Query builder component
- Chart type selector
- Schedule configuration

**Acceptance Criteria:**
- Create report without coding
- Save and share report definitions
- Export in multiple formats
- Email scheduled reports

---

### STORY-020: Quality Assurance & Agent Coaching
**Priority:** LOW | **Effort:** Medium | **Impact:** Medium

Auto-score agent responses for quality.

**Features:**
- **Response Quality Scoring**: Grammar, tone, completeness, empathy
- **Compliance Checking**: Did agent follow required scripts?
- **Coaching Recommendations**: Identify skill gaps per agent
- **Best Practice Library**: Extract exemplary responses
- **Performance Trends**: Track improvement over time

**Scoring Model:**
```python
# backend/services/qa_scorer.py
class QAScorer:
    def score_response(self, response: str, ticket: Ticket) -> Dict:
        scores = {
            'grammar': self._score_grammar(response),
            'tone': self._score_tone(response),
            'completeness': self._score_completeness(response, ticket),
            'empathy': self._score_empathy(response),
            'policy_compliance': self._check_compliance(response)
        }

        overall = sum(scores.values()) / len(scores)

        feedback = self._generate_feedback(scores)

        return {
            'overall_score': overall,
            'breakdown': scores,
            'feedback': feedback,
            'exemplary': overall > 0.9
        }
```

**Acceptance Criteria:**
- Score 95%+ of agent responses
- Generate actionable coaching tips
- Manager dashboard showing agent scores
- Best practice library with search

---

## Summary

**Completed:** 4/9 MVP stories (44%)
**In Progress:** 5/9 MVP stories (56%)
**New World-Class Features:** 11 stories

**Recommended Priority:**
1. **Complete MVP First** (STORY-002, 003, 005, 007, 008) - 2-3 weeks
2. **High-Impact Intelligence** (STORY-010, 011, 013, 017) - 2-3 months
3. **Ecosystem Integration** (STORY-018) - 1-2 months
4. **Advanced Features** (STORY-012, 014, 015, 016, 019, 020) - Ongoing

**Total Roadmap:** 6-9 months to world-class
