def _h(t):
    return {"Authorization": f"Bearer {t}"}


def test_seed_demo_present(client, officer_token):
    r = client.get("/api/v1/meta/demo")
    assert r.json()["has_demo"] is True
    bid = r.json()["beneficiary_id"]

    r = client.get(f"/api/v1/recommendations?beneficiary_id={bid}&sort=rank", headers=_h(officer_token))
    items = r.json()["items"]
    assert items
    top = items[0]
    assert "Solar PV Installer" in top["skill"]["name"]
    assert top["match_score"] == 94.0
    assert top["reasons"] and top["career_pathway"]


def test_full_beneficiary_journey(client, officer_token):
    h = _h(officer_token)

    # create
    r = client.post("/api/v1/beneficiaries", json={
        "full_name": "Journey Test", "age": 24, "education_level": "secondary",
        "preferred_language": "hi", "employment_preference": "wage_employment",
        "interests": ["solar", "electronics"],
    }, headers=h)
    assert r.status_code == 201, r.text
    bid = r.json()["id"]

    # interview
    r = client.post("/api/v1/interviews", json={"beneficiary_id": bid, "language": "hi"}, headers=h)
    assert r.status_code == 201
    iv = r.json()["id"]

    turns = [
        ("haan", "yes"), ("Journey Test", "My name is Journey Test"), ("chaubis saal", "I am 24 years old"),
        ("Ranchi", "village Nagri district Ranchi"), ("dasvi paas", "I passed class 10"),
        ("kheti", "I do farming"), ("kheti", "family does farming"),
        ("kheti aati hai", "I know farming"), ("solar sikhna hai", "I want to learn solar and electrical work"),
        ("nahi ja sakta", "no I cannot travel, only local"), ("naukri chahiye", "I want a wage job"),
        ("paisa nahi hai", "money problem, cannot pay fees"),
    ]
    complete = False
    for original, english in turns:
        r = client.post(f"/api/v1/interviews/{iv}/turn", json={
            "text": original, "text_english": english, "language": "hi",
        }, headers=h)
        assert r.status_code == 200, r.text
        complete = r.json()["is_complete"]
        if complete:
            break
    assert complete

    r = client.get(f"/api/v1/interviews/{iv}/transcript", headers=h)
    assert r.json()["structured_profile"] is not None

    # recommendations
    r = client.post("/api/v1/recommendations/generate", json={"beneficiary_id": bid, "top_n": 5}, headers=h)
    assert r.status_code == 200, r.text
    recs = r.json()["recommendations"]
    assert len(recs) == 5
    assert all(0 <= x["match_score"] <= 100 for x in recs)
    assert abs(sum(recs[0]["factor_scores"].values())) > 0

    # apply to the suggested program
    program_id = recs[0]["suggested_program"]["id"] if recs[0].get("suggested_program") else None
    if not program_id:
        progs = client.get(f"/api/v1/training-programs?skill_id={recs[0]['skill']['id']}", headers=h).json()["items"]
        program_id = progs[0]["id"] if progs else None
    assert program_id

    r = client.post("/api/v1/applications", json={"beneficiary_id": bid, "program_id": program_id}, headers=h)
    assert r.status_code == 201, r.text
    app_id = r.json()["id"]

    r = client.post(f"/api/v1/applications/{app_id}/enroll", headers=h)
    assert r.status_code in (200, 400, 409)  # 400/409 if eligibility/seat edge

    if r.status_code == 200:
        r = client.post(f"/api/v1/applications/{app_id}/certificate", json={"assessment_score": 78}, headers=h)
        assert r.status_code == 200
        assert r.json()["status"] == "certified"


def test_analytics_and_map(client, officer_token):
    h = _h(officer_token)
    r = client.get("/api/v1/analytics/overview", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert len(body["kpis"]) >= 6
    assert body["funnel"][0]["stage"] == "Registered"

    r = client.get("/api/v1/analytics/outcomes", headers=h)
    assert r.status_code == 200
    assert "placement_rate" in r.json()

    r = client.get("/api/v1/map/livelihood", headers=h)
    assert r.status_code == 200
    assert len(r.json()["points"]) > 0


def test_recommendation_weights_configurable(client, officer_token):
    h = _h(officer_token)
    bid = client.get("/api/v1/meta/demo").json()["beneficiary_id"]
    base = client.post("/api/v1/recommendations/generate", json={
        "beneficiary_id": bid, "top_n": 5, "persist": False,
    }, headers=h).json()
    skewed = client.post("/api/v1/recommendations/generate", json={
        "beneficiary_id": bid, "top_n": 5, "persist": False,
        "weights_override": {"interests": 0.9, "local_demand": 0.01},
    }, headers=h).json()
    assert base["weights"] != skewed["weights"]


def test_pagination_and_filters(client, officer_token):
    h = _h(officer_token)
    r = client.get("/api/v1/beneficiaries?page=1&page_size=5", headers=h)
    assert r.status_code == 200
    meta = r.json()["meta"]
    assert meta["page_size"] == 5 and meta["total"] >= 5

    r = client.get("/api/v1/skills?nsqf_level=4", headers=h)
    assert all(s["nsqf_level"] == 4 for s in r.json()["items"])
