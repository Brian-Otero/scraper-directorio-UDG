from locust import HttpUser, task, between

class FastAPITestUser(HttpUser):
    
    host = "http://148.202.152.59:8001"
    
    
    wait_time = between(1, 3)

    
    @task(1)
    def test_contact_info(self):
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code {response.status_code}")

    
    @task(2)
    def test_becas_info(self):
        with self.client.get("/becas", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code {response.status_code}")

    
    @task(1)
    def test_get_image(self):
        filename = "erasmo.jpg"  # Cambiar por un nombre de imagen válido
        with self.client.get(f"/get-image/{filename}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get image {filename} with status code {response.status_code}")
