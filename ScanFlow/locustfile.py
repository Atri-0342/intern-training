from locust import HttpUser, task, constant


class ScanFlowUser(HttpUser):
    wait_time = constant(0)

    def on_start(self):
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzYzc5Y2MzOS03MGEzLTQwNTYtODgzOS0zYmY3YzJlZTY3NTkiLCJyb2xlIjoiY2xpbmljaWFuIiwiZXhwIjoxNzkxNzUzODc5fQ.VxOqElS3umU-sUFf7arYNBYZUYQuQuGtgCqk3VAP_28"

    @task
    def read_patients(self):
        with self.client.get(
            "/v1/patients?limit=10",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/v1/patients",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Unexpected HTTP status: {response.status_code}"
                )