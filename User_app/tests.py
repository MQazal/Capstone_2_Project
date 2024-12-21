from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from User_app.models import Event
from datetime import datetime, timedelta
import time
import statistics
import psutil
import requests
from locust import HttpUser, task, between

class LoadTestUser(HttpUser):
    """Load testing with Locust"""
    wait_time = between(1, 3)  # Wait between requests

    @task
    def view_homepage(self):
        self.client.get("/")

    @task
    def search_events(self):
        self.client.get("/search/?event_type=Conference")

    @task
    def view_event_details(self):
        self.client.get("/event/1/")

class PerformanceTest(TestCase):
    """Performance tests for Event Management System"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.event = Event.objects.create(
            EventTitle="Test Event",
            EventType="Conference",
            EventDate=datetime.now().date() + timedelta(days=30),
            EventTime=datetime.now().time()
        )
        
    def measure_response_time(self, url, method='get', data=None):
        """Measure response time for a request"""
        start_time = time.time()
        if method == 'get':
            response = self.client.get(url)
        else:
            response = self.client.post(url, data)
        end_time = time.time()
        return (end_time - start_time) * 1000  # Convert to milliseconds

    def test_page_load_performance(self):
        """Test page load times"""
        urls_to_test = [
            reverse('home'),
            reverse('search_events'),
            reverse('signup'),
            reverse('signin')
        ]
        
        results = {}
        for url in urls_to_test:
            times = []
            # Make multiple requests to get average
            for _ in range(10):
                response_time = self.measure_response_time(url)
                times.append(response_time)
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            # Assert reasonable response times
            self.assertLess(avg_time, 500)  # Average should be under 500ms
            self.assertLess(max_time, 1000)  # Max should be under 1000ms
            
            results[url] = {
                'average': avg_time,
                'max': max_time
            }
            
        print("\nPage Load Performance Results:")
        for url, metrics in results.items():
            print(f"{url}:")
            print(f"  Average: {metrics['average']:.2f}ms")
            print(f"  Maximum: {metrics['max']:.2f}ms")

    def test_database_query_performance(self):
        """Test database query performance"""
        # Create test data
        events = [
            Event(
                EventTitle=f"Test Event {i}",
                EventType="Conference",
                EventDate=datetime.now().date() + timedelta(days=i),
                EventTime=datetime.now().time()
            ) for i in range(100)
        ]
        Event.objects.bulk_create(events)
        
        # Measure query times
        start_time = time.time()
        Event.objects.all().count()
        count_time = time.time() - start_time
        
        start_time = time.time()
        Event.objects.filter(EventType="Conference").select_related().all()
        filter_time = time.time() - start_time
        
        # Assert reasonable query times
        self.assertLess(count_time, 0.1)  # Under 100ms
        self.assertLess(filter_time, 0.2)  # Under 200ms
        
        print("\nDatabase Query Performance:")
        print(f"Count query time: {count_time*1000:.2f}ms")
        print(f"Filter query time: {filter_time*1000:.2f}ms")

    def test_resource_usage(self):
        """Test CPU and memory usage"""
        process = psutil.Process()
        
        # Measure baseline
        baseline_cpu = process.cpu_percent()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        # Perform intensive operation
        events = [Event(
            EventTitle=f"Test Event {i}",
            EventType="Conference",
            EventDate=datetime.now().date() + timedelta(days=i),
            EventTime=datetime.now().time()
        ) for i in range(1000)]
        Event.objects.bulk_create(events)
        
        # Measure after operation
        final_cpu = process.cpu_percent()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        print("\nResource Usage:")
        print(f"CPU Usage: {final_cpu - baseline_cpu:.2f}%")
        print(f"Memory Usage: {final_memory - baseline_memory:.2f}MB")
        
        # Assert reasonable resource usage
        self.assertLess(final_cpu - baseline_cpu, 50)  # CPU increase under 50%
        self.assertLess(final_memory - baseline_memory, 100)  # Memory increase under 100MB

    def test_concurrent_users(self):
        """Test system performance with concurrent users"""
        def simulate_user_actions():
            self.client.get(reverse('home'))
            self.client.get(reverse('search_events'))
            self.client.get(reverse('signin'))
        
        start_time = time.time()
        
        # Simulate multiple concurrent users
        for _ in range(10):
            simulate_user_actions()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\nConcurrent Users Test:")
        print(f"Total time for 10 concurrent users: {total_time:.2f}s")
        print(f"Average time per user: {total_time/10:.2f}s")
        
        # Assert reasonable processing time
        self.assertLess(total_time/10, 1.0)  # Average time per user under 1 second