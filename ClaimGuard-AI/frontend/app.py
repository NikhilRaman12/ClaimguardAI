from datetime import date
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

# Ensure frontend folder is always available for imports
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from components.api import API_URL, get, login, post
from components.ui import claims_table, metric_card, page_header, risk_tone


def load_css() -> None:
    css_path = CURRENT_DIR / "assets" / "styles.css"

    if css_path.exists():
        with open(css_path, encoding="utf-8") as file:
            st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found: {css_path}")


st.set_page_config(page_title="ClaimGuard AI", page_icon="CG", layout="wide")
load_css()


def login_screen() -> None:
    page_header("ClaimGuard AI", "Enterprise insurance claims orchestration")

    left, right = st.columns([1, 1])

    with left:
        st.markdown("### Secure Access")
        email = st.text_input("Email", value="admin@claimguard.ai")
        password = st.text_input("Password", value="ClaimGuard@2026", type="password")

        if st.button("Sign in", type="primary", use_container_width=True):
            payload = login(email, password)
            if payload:
                st.session_state.token = payload["access_token"]
                st.session_state.user = payload
                st.rerun()
            else:
                st.error("Login failed. Please check backend API and credentials.")

    with right:
        st.markdown(
            """
            <div class="section-panel">
              <h3>Operational Control Plane</h3>
              <p>Claims intake, fraud intelligence, policy validation, human approvals, audit trails, and executive analytics in one governed workflow.</p>
              <span class="badge badge-green">RBAC Enabled</span>
              <span class="badge badge-blue">AI Orchestrated</span>
              <span class="badge badge-amber">Audit Ready</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def sidebar() -> str:
    st.sidebar.markdown("## ClaimGuard AI")
    st.sidebar.caption(f"API: {API_URL}")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Executive Dashboard",
            "Claims",
            "Claim Details",
            "New Claim",
            "AI Agent Center",
            "Fraud Intelligence",
            "Human Review",
            "Analytics",
            "Audit Logs",
            "Admin",
            "Settings",
        ],
    )

    st.sidebar.divider()
    user = st.session_state.get("user", {})
    st.sidebar.write(user.get("name", "Authenticated User"))
    st.sidebar.caption(user.get("role", ""))

    if st.sidebar.button("Sign out"):
        st.session_state.clear()
        st.rerun()

    return page


def executive_dashboard() -> None:
    page_header(
        "Executive Dashboard",
        "Real-time claims operations, automation performance, and enterprise risk posture",
    )

    kpi = get("/dashboard/kpis") or {}

    cols = st.columns(4)
    values = [
        ("Claims Today", kpi.get("claims_today", 0), "blue"),
        ("Pending Approvals", kpi.get("pending_approvals", 0), "amber"),
        ("High Risk Claims", kpi.get("high_risk_claims", 0), "red"),
        ("Automation Rate", f'{kpi.get("automation_rate", 0)}%', "green"),
        ("Avg Processing", f'{kpi.get("average_processing_time_hours", 0)}h', "blue"),
        ("Cost Saved", f'${kpi.get("cost_saved", 0):,.0f}', "green"),
        ("Fraud Prevented", f'${kpi.get("fraud_prevented", 0):,.0f}', "red"),
        ("Human Review Queue", kpi.get("human_review_queue", 0), "amber"),
    ]

    for idx, item in enumerate(values):
        with cols[idx % 4]:
            metric_card(item[0], str(item[1]), item[2])

    claims = get("/claims") or []
    if not claims:
        st.info("No claims available.")
        return

    frame = pd.DataFrame(claims)
    left, right = st.columns([1.1, 0.9])

    with left:
        st.markdown("### Case Pipeline")
        required = ["case_id", "customer", "category", "status", "risk_score", "claim_amount"]
        st.dataframe(frame[required].head(12), use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Risk Distribution")
        fig = px.histogram(frame, x="risk_score", nbins=12)
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)


def claims_page() -> None:
    page_header("Claims", "Search, filter, and act on enterprise claim inventory")

    claims = get("/claims") or []
    if not claims:
        st.info("No claims available.")
        return

    search = st.text_input("Search claims, customers, policies, or adjusters")
    category = st.selectbox("Category", ["All"] + sorted({item.get("category", "") for item in claims}))

    filtered = [
        item
        for item in claims
        if (category == "All" or item.get("category") == category)
        and (not search or search.lower() in str(item).lower())
    ]

    claims_table(filtered)
    st.download_button(
        "Download visible claims as CSV",
        pd.DataFrame(filtered).to_csv(index=False),
        "claims.csv",
        "text/csv",
    )


def claim_details_page() -> None:
    page_header("Claim Details", "Timeline, explainability, decision evidence, and approval history")

    claims = get("/claims") or []
    if not claims:
        st.info("No claims available.")
        return

    selected = st.selectbox("Case ID", [item["case_id"] for item in claims])
    claim = get(f"/claims/{selected}") or {}
    decision = get(f"/claims/{selected}/decision") or {}

    left, right = st.columns([1, 1])

    with left:
        st.markdown("### Case Summary")
        keys = ["case_id", "customer", "policy", "category", "claim_amount", "coverage", "status", "risk_score"]
        st.json({key: claim.get(key) for key in keys})

    with right:
        st.markdown("### Decision Engine")
        st.info(f'{decision.get("decision", "Pending")}: {decision.get("reason", "Awaiting decision")}')
        risk_score = claim.get("risk_score", 0)
        st.markdown(
            f"<span class='badge badge-{risk_tone(risk_score)}'>Risk {risk_score}</span>",
            unsafe_allow_html=True,
        )

        if st.button("Run Agent Orchestration", type="primary"):
            post(f"/claims/{selected}/process")
            st.success("Claim orchestration completed.")
            st.rerun()

    st.markdown("### Agent Outputs")
    st.dataframe(pd.DataFrame(claim.get("agent_outputs", [])), use_container_width=True, hide_index=True)

    st.markdown("### Approval Timeline")
    st.dataframe(pd.DataFrame(claim.get("approval_history", [])), use_container_width=True, hide_index=True)


def new_claim_page() -> None:
    page_header("New Claim", "Guided enterprise claim intake with immediate AI orchestration")

    with st.form("new_claim"):
        cols = st.columns(2)

        customer = cols[0].text_input("Customer", "Nikhil Raman")
        policy = cols[1].text_input("Policy", "AUT-482916")
        category = cols[0].selectbox(
            "Category",
            [
                "Auto",
                "Medical",
                "Travel",
                "Home",
                "Property",
                "Flood",
                "Fire",
                "Theft",
                "Life",
                "Motor",
                "Business Insurance",
            ],
        )
        coverage = cols[1].number_input("Coverage", min_value=1000.0, value=125000.0)
        amount = cols[0].number_input("Claim Amount", min_value=100.0, value=28500.0)
        incident_date = cols[1].date_input("Incident Date", value=date.today())
        location = st.text_input("Location", "Hyderabad")
        description = st.text_area(
            "Incident Description",
            "Rear-end collision with repair estimate and verified service invoice attached.",
        )
        documents = st.multiselect(
            "Documents",
            ["Policy", "Invoice", "Police Report", "Medical Report", "Photos", "Repair Estimate"],
            default=["Policy", "Invoice"],
        )

        submitted = st.form_submit_button("Create and Orchestrate", type="primary")

    if submitted:
        payload = {
            "customer": customer,
            "policy": policy,
            "category": category,
            "coverage": coverage,
            "claim_amount": amount,
            "incident_date": str(incident_date),
            "location": location,
            "description": description,
            "documents": documents,
        }

        claim = post("/claims", payload)
        if claim:
            st.success(f'Claim {claim["case_id"]} created and routed to {claim["status"]}.')
        else:
            st.error("Claim creation failed. Please check backend API.")


def agents_page() -> None:
    page_header("AI Agent Center", "Command center for agent health, orchestration state, and service-level confidence")

    status = get("/agents/status") or []
    if not status:
        st.info("No agent status available.")
        return

    frame = pd.DataFrame(status)
    st.dataframe(frame, use_container_width=True, hide_index=True)

    fig = px.bar(frame, x="agent", y="sla", color="mode")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-35,
    )
    st.plotly_chart(fig, use_container_width=True)


def fraud_page() -> None:
    page_header("Fraud Intelligence", "Prioritized investigation queue with explainable risk signals")

    claims = get("/claims") or []
    if not claims:
        st.info("No claims available.")
        return

    frame = pd.DataFrame(claims)
    high = frame.sort_values("risk_score", ascending=False).head(20)
    columns = ["case_id", "customer", "category", "risk_score", "fraud_indicators", "claim_amount", "status"]
    st.dataframe(high[columns], use_container_width=True, hide_index=True)


def human_review_page() -> None:
    page_header("Human Review", "Approval workbench for cases requiring accountable human judgment")

    claims = [
        item
        for item in (get("/claims") or [])
        if item.get("status") in ["Human Review", "Investigation"]
    ]

    claims_table(claims)

    if claims:
        selected = st.selectbox("Select case for approval", [item["case_id"] for item in claims])
        note = st.text_area(
            "Approval Note",
            "Reviewed policy, documents, and AI explanation. Approved for settlement.",
        )

        if st.button("Approve Claim", type="primary"):
            post(f"/claims/{selected}/approve", {"note": note})
            st.success(f"{selected} approved.")
            st.rerun()


def analytics_page() -> None:
    page_header("Analytics", "Portfolio trends, settlement patterns, fraud distribution, and automation metrics")

    data = get("/analytics") or {}

    charts = [
        ("Claim Categories", data.get("claim_categories", {})),
        ("Fraud Distribution", data.get("fraud_distribution", {})),
        ("Approval Rate", data.get("approval_rate", {})),
        ("Agent Performance", data.get("agent_performance", {})),
    ]

    cols = st.columns(2)

    for index, (title, payload) in enumerate(charts):
        with cols[index % 2]:
            if not payload:
                st.info(f"No data available for {title}.")
                continue

            frame = pd.DataFrame({"name": list(payload.keys()), "value": list(payload.values())})
            fig = px.bar(frame, x="name", y="value", title=title)
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)


def audit_page() -> None:
    page_header("Audit Logs", "Immutable operational evidence for claims, approvals, and administrative actions")

    events = get("/audit") or []
    st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)


def admin_page() -> None:
    page_header("Admin", "Operational controls for access, workflow thresholds, and enterprise governance")

    st.markdown("### Role Matrix")
    st.dataframe(
        pd.DataFrame(
            [
                {"role": "admin", "claims": "read/write", "approval": "yes", "audit": "yes", "settings": "write"},
                {"role": "adjuster", "claims": "read/write", "approval": "no", "audit": "yes", "settings": "read"},
                {"role": "reviewer", "claims": "read", "approval": "yes", "audit": "yes", "settings": "read"},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def settings_page() -> None:
    page_header("Settings", "Runtime configuration, API health, and environment posture")

    st.markdown("### Runtime Settings")
    st.json(get("/settings") or {})

    st.markdown("### API Health")
    st.json(get("/health") or {})


def main() -> None:
    if "token" not in st.session_state:
        login_screen()
        return

    selected_page = sidebar()

    pages = {
        "Executive Dashboard": executive_dashboard,
        "Claims": claims_page,
        "Claim Details": claim_details_page,
        "New Claim": new_claim_page,
        "AI Agent Center": agents_page,
        "Fraud Intelligence": fraud_page,
        "Human Review": human_review_page,
        "Analytics": analytics_page,
        "Audit Logs": audit_page,
        "Admin": admin_page,
        "Settings": settings_page,
    }

    pages[selected_page]()


if __name__ == "__main__":
    main()