def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_login_me(client):
    email = "new.user@example.com"
    r = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Str0ngPass!", "full_name": "New User", "role": "beneficiary",
    })
    assert r.status_code == 201, r.text
    tokens = r.json()
    assert tokens["user"]["email"] == email

    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Str0ngPass!"})
    assert r.status_code == 200
    access = r.json()["access_token"]

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert r.json()["role"] == "beneficiary"


def test_login_wrong_password(client):
    r = client.post("/api/v1/auth/login", json={"email": "admin@kaushai.gov.in", "password": "nope"})
    assert r.status_code == 401


def test_forgot_and_reset_password(client):
    r = client.post("/api/v1/auth/forgot-password", json={"email": "officer@kaushai.gov.in"})
    assert r.status_code == 200
    token = r.json()["token"]
    assert token
    r = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "Officer@2027"})
    assert r.status_code == 200
    r = client.post("/api/v1/auth/login", json={"email": "officer@kaushai.gov.in", "password": "Officer@2027"})
    assert r.status_code == 200
    # reset back
    client.post("/api/v1/auth/reset-password", json={
        "token": client.post("/api/v1/auth/forgot-password", json={"email": "officer@kaushai.gov.in"}).json()["token"],
        "new_password": "Officer@2026",
    })


def test_protected_route_requires_auth(client):
    assert client.get("/api/v1/beneficiaries").status_code == 401


def test_rbac_beneficiary_cannot_list_users(client):
    client.post("/api/v1/auth/register", json={
        "email": "b2@example.com", "password": "Str0ngPass!", "full_name": "B Two", "role": "beneficiary",
    })
    tok = client.post("/api/v1/auth/login", json={"email": "b2@example.com", "password": "Str0ngPass!"}).json()["access_token"]
    r = client.get("/api/v1/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403
