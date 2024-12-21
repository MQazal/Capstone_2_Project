from locust import HttpUser, task, between

class EventUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup user before tests"""
        pass

    @task(2)
    def view_homepage(self):
        """Test homepage access"""
        self.client.get("/")

    @task(1)
    def view_signup(self):
        """Test signup page access"""
        self.client.get("/signup/")

    @task(1)
    def view_signin(self):
        """Test signin page access"""
        self.client.get("/signin/")

    @task(3)
    def search_events(self):
        """Test event search"""
        self.client.get("/search/?event_type=Conference")

    @task(1)
    def view_event_details(self):
        """Test event detail view"""
        self.client.get("/event/1/")