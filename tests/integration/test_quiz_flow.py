"""Pilno klausimyno srauto integracijos testai per HTTP klientą."""


class TestQuizFlow:
    def test_healthz(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json["status"] == "ok"

    def test_index_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Saugumo vedlys" in response.data or b"patikr" in response.data.lower()

    def test_quiz_start_get(self, client, platform_win):
        response = client.get("/quiz/start")
        assert response.status_code == 200
        assert b"Windows" in response.data

    def test_full_quiz_flow_via_api(self, client, platform_win):
        response = client.post(
            "/api/v1/sessions",
            json={"platform": "WIN"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "token" in data
        assert data["first_question"]["text"] == "Test klausimas 1"
        token = data["token"]

        q1 = data["first_question"]
        first_answer_id = q1["answers"][0]["id"]

        response = client.post(
            f"/api/v1/sessions/{token}/answer",
            json={
                "question_id": q1["id"],
                "answer_ids": [first_answer_id],
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "next_question" in data
        assert data["current_step"] == 2

        q2 = data["next_question"]
        nesaugus_answer = q2["answers"][-1]["id"]

        response = client.post(
            f"/api/v1/sessions/{token}/answer",
            json={
                "question_id": q2["id"],
                "answer_ids": [nesaugus_answer],
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["completed"] is True

        response = client.get(f"/api/v1/sessions/{token}/result")
        assert response.status_code == 200
        result = response.get_json()
        assert result["profile"]["total_score"] == 9
        assert "items" in result

    def test_invalid_platform_rejected(self, client, platform_win):
        response = client.post(
            "/api/v1/sessions",
            json={"platform": "LINUX"},
        )
        assert response.status_code == 422

    def test_session_not_found(self, client, platform_win):
        response = client.get("/api/v1/sessions/nonexistent-token")
        assert response.status_code == 404

    def test_invalid_answer_rejected(self, client, platform_win):
        response = client.post("/api/v1/sessions", json={"platform": "WIN"})
        token = response.get_json()["token"]

        response = client.post(
            f"/api/v1/sessions/{token}/answer",
            json={"question_id": 999, "answer_ids": [99999]},
        )
        assert response.status_code == 400

    def test_go_back_removes_latest_answer(self, client, platform_win):
        response = client.post("/api/v1/sessions", json={"platform": "WIN"})
        data = response.get_json()
        token = data["token"]
        first_question = data["first_question"]

        client.post(
            f"/api/v1/sessions/{token}/answer",
            json={
                "question_id": first_question["id"],
                "answer_ids": [first_question["answers"][0]["id"]],
            },
        )

        response = client.post(f"/quiz/{token}/back")
        assert response.status_code == 302

        response = client.get(f"/api/v1/sessions/{token}")
        state = response.get_json()
        assert state["current_step"] == 0
        assert state["current_question"]["id"] == first_question["id"]


class TestApiPlatforms:
    def test_list_platforms(self, client, platform_win):
        response = client.get("/api/v1/platforms")
        assert response.status_code == 200
        data = response.get_json()
        codes = [p["code"] for p in data["platforms"]]
        assert "WIN" in codes
