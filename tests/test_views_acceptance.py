import os
import sys
import unittest
import multiprocessing
import time
from urllib.parse import urlparse
from unittest import skip

from werkzeug.security import generate_password_hash
from splinter import Browser

# Configure your app to use the testing database
if os.environ.get("CONFIG_PATH") == None:
	os.environ["CONFIG_PATH"] = "blog.config.TestingConfig"

from blog import app
from blog.database import Base, engine, session, User

class TestViews(unittest.TestCase):
	def setUp(self):
		""" Test setup """
		self.browser = Browser("phantomjs")
		
		# Set up the tables in the database
		Base.metadata.create_all(engine)
		
		# Create example users
		self.user = User(name="Alice", email="alice@example.com",
				password=generate_password_hash("test"))
		session.add(self.user)
		self.user2 = User(name="Bob", email="bob@example.com",
				password=generate_password_hash("asdf"))
		session.add(self.user2)
		session.commit()
		
		self.process = multiprocessing.Process(target=app.run,
							kwargs={"port": 8081})
		self.process.start()
		time.sleep(1)
	
	def tearDown(self):
		""" Test teardown """
		# Remove the tables and their data from the database
		self.process.terminate()
		session.close()
		engine.dispose()
		Base.metadata.drop_all(engine)
		# Hack to handle exception caused by Selenium bug
		try:
			self.browser.quit()
		except OSError:
			pass
	
	def test_login_correct(self):
		self.browser.visit("http://127.0.0.1:8081/login")
		self.browser.fill("email", "alice@example.com")
		self.browser.fill("password", "test")
		button = self.browser.find_by_css("button[type=submit]")
		button.click()
		self.assertEqual(self.browser.url, "http://127.0.0.1:8081/")
		self.assertEqual(self.browser.find_by_css(".username").first.html, "Alice")
	
	def test_login_incorrect(self):
		self.browser.visit("http://127.0.0.1:8081/login")
		self.browser.fill("email", "bob@example.com")
		self.browser.fill("password", "test")
		button = self.browser.find_by_css("button[type=submit]")
		button.click()
		self.assertEqual(self.browser.url, "http://127.0.0.1:8081/login")
		self.assertEqual(self.browser.find_by_css(".alert-danger").first.text,
					"Incorrect username or password")
	
	def test_login_view(self):
		self.browser.visit("http://127.0.0.1:8081/")
		# Working around an apparent PhantomJS bug that "throws out the baby with the bathwater" -
		# The text seems to be stripped as well as the HTML
		self.assertEqual(self.browser.find_by_css(".login").first.html, "Login")
		self.browser.visit("http://127.0.0.1:8081/entry/add")
		self.assertEqual(self.browser.url, "http://127.0.0.1:8081/login?next=%2Fentry%2Fadd")
		self.assertEqual(self.browser.find_by_css(".alert-danger").first.text,
					"Please log in to access this page.")
		self.browser.fill("email", "alice@example.com")
		self.browser.fill("password", "test")
		button = self.browser.find_by_css("button[type=submit]")
		button.click()
		self.assertEqual(self.browser.url, "http://127.0.0.1:8081/entry/add")
		self.assertEqual(self.browser.find_by_css(".logout").first.html, "Logout")
	
	def test_add_entry(self):
		self.test_login_correct()
		self.browser.visit("http://127.0.0.1:8081/entry/add")
		self.browser.fill("title", "Test Entry")
		self.browser.fill("content", "Testibg new entry.")
		button = self.browser.find_by_css("button[type=submit]")
		button.click()
		self.assertEqual(self.browser.url, "http://127.0.0.1:8081/")
		self.assertEqual(self.browser.find_by_css("#title-1").first.text,
					"Test Entry")
	
	def test_edit_entry(self):
		self.test_add_entry()
		self.browser.visit("http://127.0.0.1:8081/entry/1/edit")
		self.assertEqual(self.browser.find_by_css("#title").first.value,
					"Test Entry")
		self.assertEqual(self.browser.find_by_css("#content").first.value,
					"Testibg new entry.")
		self.browser.fill("content", "Testing new entry.")
		button = self.browser.find_by_css("button[type=submit]")
		button.click()
		self.assertEqual(self.browser.url, "http://127.0.0.1:8081/")
		self.assertEqual(self.browser.find_by_css("#content-1").first.text,
					"Testing new entry.")
	
	def test_delete_entry(self):
		self.test_add_entry()
		self.browser.visit("http://127.0.0.1:8081/entry/1/delete")
		button = self.browser.find_by_css("button[type=submit]")
		button.click()
		self.assertEqual(len(self.browser.find_by_css("#title-1")), 0)
	
	def test_entries_count(self):
		# Content seed lifted from manage.py
		# Slow as sludge via HTTP but I really don't care
		seed_content = """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
		self.test_login_correct()
		for i in range(51):
			self.browser.visit("http://127.0.0.1:8081/entry/add")
			self.browser.fill("title", "Test Entry #{}".format(i))
			self.browser.fill("content", seed_content)
			button = self.browser.find_by_css("button[type=submit]")
			button.click()			
		self.browser.visit("http://127.0.0.1:8081/")
		self.assertTrue(len(self.browser.find_by_css(".row"))<=10)
		self.browser.visit("http://127.0.0.1:8081/?limit=20")
		self.assertTrue(len(self.browser.find_by_css(".row"))<=20)
		self.browser.visit("http://127.0.0.1:8081/?limit=50")
		self.assertTrue(len(self.browser.find_by_css(".row"))<=50)
		self.browser.visit("http://127.0.0.1:8081/?limit=3.14")
		self.assertTrue(len(self.browser.find_by_css(".row"))<=10)
	
	def test_author_links(self):
		self.test_add_entry()
		self.assertTrue(self.browser.is_element_present_by_text("Edit"))
		self.assertTrue(self.browser.is_element_present_by_text("Delete"))
		# check not logged in
		self.browser.visit("http://127.0.0.1:8081/logout")
		self.assertTrue(self.browser.is_element_not_present_by_text("Edit"))
		self.assertTrue(self.browser.is_element_not_present_by_text("Delete"))
		# check other user logged in
		self.browser.visit("http://127.0.0.1:8081/login")
		self.browser.fill("email", "bob@example.com")
		self.browser.fill("password", "asdf")
		button = self.browser.find_by_css("button[type=submit]")
		button.click()
		self.assertTrue(self.browser.is_element_not_present_by_text("Edit"))
		self.assertTrue(self.browser.is_element_not_present_by_text("Delete"))
		

if __name__ == "__main__":
	unittest.main()
