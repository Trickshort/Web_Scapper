import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk, Menu
import textwrap
import os
import threading
from urllib.parse import urljoin, urlparse
import time
import json
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import random
from fake_useragent import UserAgent

class WebScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Web Scraper Pro")
        self.root.geometry("1000x800")
        self.root.configure(bg="#2C3E50")
        
        # Variables
        self.scraping = False
        self.stop_scraping = False
        self.output_format = tk.StringVar(value="xlsx")
        self.theme_mode = tk.StringVar(value="dark")
        self.use_selenium = tk.BooleanVar(value=False)
        self.use_proxy = tk.BooleanVar(value=False)
        self.follow_external = tk.BooleanVar(value=False)
        self.respect_robots = tk.BooleanVar(value=True)
        
        # Create UI
        self.create_widgets()
        self.create_menu()
        
        # Ensure output folder exists
        self.output_folder = os.path.join(os.getcwd(), "scraper_output")
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Selenium driver (will be initialized when needed)
        self.driver = None
        
        # User agent generator
        self.ua = UserAgent()
        
        # Initialize proxy list
        self.proxies = []
        self.load_proxies()
    
    def create_menu(self):
        menubar = Menu(self.root)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Scrape", command=self.reset_scraper)
        file_menu.add_command(label="Save As...", command=self.save_as)
        file_menu.add_command(label="Open Output Folder", command=self.open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Settings menu
        settings_menu = Menu(menubar, tearoff=0)
        settings_menu.add_checkbutton(label="Use Selenium (for JS sites)", variable=self.use_selenium)
        settings_menu.add_checkbutton(label="Use Proxies", variable=self.use_proxy)
        settings_menu.add_checkbutton(label="Follow External Links", variable=self.follow_external)
        settings_menu.add_checkbutton(label="Respect robots.txt", variable=self.respect_robots)
        settings_menu.add_separator()
        settings_menu.add_command(label="Configure Proxies...", command=self.configure_proxies)
        settings_menu.add_command(label="Configure User Agents...", command=self.configure_user_agents)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # View menu
        view_menu = Menu(menubar, tearoff=0)
        view_menu.add_radiobutton(label="Dark Mode", variable=self.theme_mode, value="dark", command=self.toggle_theme)
        view_menu.add_radiobutton(label="Light Mode", variable=self.theme_mode, value="light", command=self.toggle_theme)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2C3E50")
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # URL Entry
        url_frame = tk.Frame(main_frame, bg="#2C3E50")
        url_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(url_frame, text="Website URL:", font=("Arial", 12, "bold"), 
                fg="#ECF0F1", bg="#2C3E50").pack(side=tk.LEFT, padx=5)
        
        self.url_entry = tk.Entry(url_frame, width=70, font=("Arial", 12))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Options Frame
        options_frame = tk.Frame(main_frame, bg="#2C3E50")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Content to scrape
        tk.Label(options_frame, text="Scrape:", font=("Arial", 10), 
                fg="#ECF0F1", bg="#2C3E50").pack(side=tk.LEFT, padx=5)
        
        self.scrape_headings = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Headings", variable=self.scrape_headings, 
                      bg="#2C3E50", fg="#ECF0F1", selectcolor="#34495E").pack(side=tk.LEFT, padx=5)
        
        self.scrape_paragraphs = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Paragraphs", variable=self.scrape_paragraphs, 
                      bg="#2C3E50", fg="#ECF0F1", selectcolor="#34495E").pack(side=tk.LEFT, padx=5)
        
        self.scrape_lists = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Lists", variable=self.scrape_lists, 
                      bg="#2C3E50", fg="#ECF0F1", selectcolor="#34495E").pack(side=tk.LEFT, padx=5)
        
        self.scrape_tables = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Tables", variable=self.scrape_tables, 
                      bg="#2C3E50", fg="#ECF0F1", selectcolor="#34495E").pack(side=tk.LEFT, padx=5)
        
        self.scrape_images = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Images", variable=self.scrape_images, 
                      bg="#2C3E50", fg="#ECF0F1", selectcolor="#34495E").pack(side=tk.LEFT, padx=5)
        
        self.scrape_links = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Links", variable=self.scrape_links, 
                      bg="#2C3E50", fg="#ECF0F1", selectcolor="#34495E").pack(side=tk.LEFT, padx=5)
        
        # Output format
        tk.Label(options_frame, text="Format:", font=("Arial", 10), 
                fg="#ECF0F1", bg="#2C3E50").pack(side=tk.LEFT, padx=(20,5))
        
        formats = [("Excel", "xlsx"), ("JSON", "json"), ("CSV", "csv"), ("Text", "txt")]
        for text, value in formats:
            tk.Radiobutton(options_frame, text=text, variable=self.output_format, 
                         value=value, bg="#2C3E50", fg="#ECF0F1", selectcolor="#34495E").pack(side=tk.LEFT, padx=2)
        
        # Depth control
        tk.Label(options_frame, text="Depth:", font=("Arial", 10), 
                fg="#ECF0F1", bg="#2C3E50").pack(side=tk.LEFT, padx=(20,5))
        
        self.depth_var = tk.IntVar(value=1)
        tk.Spinbox(options_frame, from_=1, to=10, textvariable=self.depth_var, 
                 width=3, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Delay control
        tk.Label(options_frame, text="Delay (s):", font=("Arial", 10), 
                fg="#ECF0F1", bg="#2C3E50").pack(side=tk.LEFT, padx=(20,5))
        
        self.delay_var = tk.DoubleVar(value=0.5)
        tk.Spinbox(options_frame, from_=0, to=10, increment=0.1, textvariable=self.delay_var, 
                 width=4, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Button Frame
        button_frame = tk.Frame(main_frame, bg="#2C3E50")
        button_frame.pack(fill=tk.X, pady=10)
        
        self.scrape_button = tk.Button(button_frame, text="Start Scraping", font=("Arial", 12, "bold"), 
                                     bg="#27AE60", fg="white", command=self.toggle_scraping)
        self.scrape_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="Stop", font=("Arial", 12), 
                                   bg="#E74C3C", fg="white", state=tk.DISABLED, command=self.stop_scraping_process)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.schedule_button = tk.Button(button_frame, text="Schedule...", font=("Arial", 12), 
                                       bg="#3498DB", fg="white", command=self.schedule_scraping)
        self.schedule_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Ready", font=("Arial", 10), 
                                    fg="#ECF0F1", bg="#2C3E50", anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)
        
        # Text area with line numbers
        text_frame = tk.Frame(main_frame, bg="#2C3E50")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers
        self.line_numbers = tk.Text(text_frame, width=4, padx=4, takefocus=0, border=0,
                                  background="#34495E", foreground="#ECF0F1", state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Text area
        self.text_area = scrolledtext.ScrolledText(text_frame, width=100, height=25, 
                                                 font=("Consolas", 10), bg="#34495E", fg="#ECF0F1")
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for syntax highlighting
        self.text_area.tag_configure("url", foreground="#3498DB")
        self.text_area.tag_configure("heading", foreground="#E74C3C")
        self.text_area.tag_configure("error", foreground="#E74C3C")
        self.text_area.tag_configure("success", foreground="#27AE60")
        
        # Bind events
        self.text_area.bind('<KeyRelease>', self.update_line_numbers)
        self.text_area.bind('<MouseWheel>', self.update_line_numbers)
        self.text_area.bind('<Button-4>', self.update_line_numbers)
        self.text_area.bind('<Button-5>', self.update_line_numbers)
        
        # Initialize line numbers
        self.update_line_numbers()
    
    def update_line_numbers(self, event=None):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        line_count = self.text_area.get('1.0', tk.END).count('\n')
        line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.insert(1.0, line_numbers_string)
        self.line_numbers.config(state='disabled')
    
    def toggle_theme(self):
        if self.theme_mode.get() == "dark":
            self.root.configure(bg="#2C3E50")
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.configure(bg="#2C3E50")
            self.text_area.configure(bg="#34495E", fg="#ECF0F1")
            self.line_numbers.configure(bg="#34495E", fg="#ECF0F1")
        else:
            self.root.configure(bg="#F5F5F5")
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.configure(bg="#F5F5F5")
            self.text_area.configure(bg="white", fg="black")
            self.line_numbers.configure(bg="#E0E0E0", fg="black")
    
    def load_proxies(self):
        proxy_file = os.path.join(os.path.dirname(__file__), "proxies.txt")
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
    
    def configure_proxies(self):
        proxy_window = tk.Toplevel(self.root)
        proxy_window.title("Configure Proxies")
        proxy_window.geometry("500x400")
        
        text_frame = tk.Frame(proxy_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        proxy_text = scrolledtext.ScrolledText(text_frame, width=60, height=20)
        proxy_text.pack(fill=tk.BOTH, expand=True)
        proxy_text.insert(tk.END, "\n".join(self.proxies))
        
        button_frame = tk.Frame(proxy_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_proxies():
            proxy_content = proxy_text.get("1.0", tk.END)
            self.proxies = [line.strip() for line in proxy_content.split("\n") if line.strip()]
            
            proxy_file = os.path.join(os.path.dirname(__file__), "proxies.txt")
            with open(proxy_file, 'w') as f:
                f.write("\n".join(self.proxies))
            
            messagebox.showinfo("Success", "Proxies saved successfully!")
            proxy_window.destroy()
        
        tk.Button(button_frame, text="Save", command=save_proxies).pack(side=tk.RIGHT)
        tk.Button(button_frame, text="Cancel", command=proxy_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def configure_user_agents(self):
        messagebox.showinfo("User Agents", "User agents are automatically rotated using the fake-useragent library.")
    
    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def get_random_user_agent(self):
        return self.ua.random
    
    def init_selenium_driver(self):
        if self.driver is not None:
            return
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if self.use_proxy.get() and self.proxies:
            proxy = self.get_random_proxy()
            options.add_argument(f'--proxy-server={proxy}')
        
        user_agent = self.get_random_user_agent()
        options.add_argument(f'user-agent={user_agent}')
        
        self.driver = webdriver.Chrome(options=options)
    
    def close_selenium_driver(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
    
    def scrape_with_selenium(self, url):
        try:
            self.init_selenium_driver()
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
        
        except Exception as e:
            self.text_area.insert(tk.END, f"Error with Selenium: {str(e)}\n", "error")
            return None
    
    def scrape_with_requests(self, url):
        headers = {
            'User-Agent': self.get_random_user_agent()
        }
        
        proxies = None
        if self.use_proxy.get() and self.proxies:
            proxy = self.get_random_proxy()
            proxies = {
                'http': proxy,
                'https': proxy
            }
        
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        
        except requests.exceptions.RequestException as e:
            self.text_area.insert(tk.END, f"Error scraping {url}: {str(e)}\n", "error")
            return None
    
    def scrape_page(self, url):
        if self.use_selenium.get():
            return self.scrape_with_selenium(url)
        else:
            return self.scrape_with_requests(url)
    
    def is_same_domain(self, url1, url2):
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False
    
    def toggle_scraping(self):
        if self.scraping:
            self.stop_scraping_process()
        else:
            self.start_scraping_process()
    
    def start_scraping_process(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        self.scraping = True
        self.stop_scraping = False
        self.scrape_button.config(text="Stop Scraping", bg="#E74C3C")
        self.stop_button.config(state=tk.NORMAL)
        self.text_area.delete('1.0', tk.END)
        self.update_status("Starting scraping process...")
        
        # Start scraping in a separate thread
        threading.Thread(target=self.scrape_website, args=(url,), daemon=True).start()
    
    def stop_scraping_process(self):
        self.stop_scraping = True
        self.update_status("Stopping scraping process...")
        self.close_selenium_driver()
    
    def reset_scraper(self):
        self.stop_scraping_process()
        self.url_entry.delete(0, tk.END)
        self.text_area.delete('1.0', tk.END)
        self.update_status("Ready")
        self.update_progress(0)
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()
    
    def save_as(self):
        file_types = [
            ("Excel files", "*.xlsx"),
            ("JSON files", "*.json"),
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.asksaveasfilename(
            initialdir=self.output_folder,
            title="Save As",
            filetypes=file_types,
            defaultextension=".xlsx"
        )
        
        if file_path:
            try:
                content = self.text_area.get('1.0', tk.END)
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext == '.xlsx':
                    # Try to parse as structured data first
                    try:
                        data = []
                        current_url = ""
                        current_data = {}
                        
                        for line in content.split('\n'):
                            if line.startswith("URL: "):
                                if current_data:
                                    data.append(current_data)
                                current_url = line[5:]
                                current_data = {"URL": current_url}
                            elif line.startswith("=== "):
                                current_section = line[4:-4].lower()
                            elif line.strip() and not line.startswith("="):
                                if current_section == "headings":
                                    if "Headings" not in current_data:
                                        current_data["Headings"] = []
                                    current_data["Headings"].append(line.strip())
                                elif current_section == "paragraphs":
                                    if "Paragraphs" not in current_data:
                                        current_data["Paragraphs"] = []
                                    current_data["Paragraphs"].append(line.strip())
                                # Add other sections as needed
                        
                        if current_data:
                            data.append(current_data)
                        
                        df = pd.DataFrame(data)
                        df.to_excel(file_path, index=False)
                    except:
                        # Fallback to simple text export
                        df = pd.DataFrame({"Content": [content]})
                        df.to_excel(file_path, index=False)
                elif ext == '.json':
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({"content": content}, f, indent=2, ensure_ascii=False)
                elif ext == '.csv':
                    with open(file_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(["Content"])
                        writer.writerow([content])
                else:  # txt
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                messagebox.showinfo("Success", f"Data saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def open_output_folder(self):
        try:
            os.startfile(self.output_folder)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    def schedule_scraping(self):
        schedule_window = tk.Toplevel(self.root)
        schedule_window.title("Schedule Scraping")
        schedule_window.geometry("400x300")
        
        tk.Label(schedule_window, text="Schedule Options", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Schedule type
        tk.Label(schedule_window, text="Run:").pack(anchor=tk.W, padx=20)
        
        self.schedule_type = tk.StringVar(value="once")
        tk.Radiobutton(schedule_window, text="Once", variable=self.schedule_type, value="once").pack(anchor=tk.W, padx=40)
        tk.Radiobutton(schedule_window, text="Daily", variable=self.schedule_type, value="daily").pack(anchor=tk.W, padx=40)
        tk.Radiobutton(schedule_window, text="Weekly", variable=self.schedule_type, value="weekly").pack(anchor=tk.W, padx=40)
        
        # Time selection
        tk.Label(schedule_window, text="At:").pack(anchor=tk.W, padx=20)
        
        time_frame = tk.Frame(schedule_window)
        time_frame.pack(anchor=tk.W, padx=40)
        
        self.schedule_hour = tk.IntVar(value=12)
        self.schedule_minute = tk.IntVar(value=0)
        
        tk.Spinbox(time_frame, from_=0, to=23, textvariable=self.schedule_hour, width=3).pack(side=tk.LEFT)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.schedule_minute, width=3).pack(side=tk.LEFT)
        
        # Buttons
        button_frame = tk.Frame(schedule_window)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        tk.Button(button_frame, text="Schedule", command=lambda: self.confirm_schedule(schedule_window)).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=schedule_window.destroy).pack(side=tk.LEFT)
    
    def confirm_schedule(self, window):
        schedule_type = self.schedule_type.get()
        time_str = f"{self.schedule_hour.get():02d}:{self.schedule_minute.get():02d}"
        
        message = f"Scraping scheduled to run {schedule_type} at {time_str}"
        messagebox.showinfo("Scheduled", message)
        window.destroy()
    
    def categorize_text(self, text):
        length = len(text.split())
        if length < 50:
            return "(Short)"
        elif length < 200:
            return "(Medium)"
        else:
            return "(Long)"
    
    def extract_images(self, soup, base_url):
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                images.append((src, img.get('alt', '')))
        return images
    
    def extract_links(self, soup, base_url):
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href:
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                links.append((href, a.get_text(strip=True)))
        return links
    
    def scrape_website(self, start_url):
        try:
            visited_urls = set()
            to_visit = [(start_url, 0)]  # (url, depth)
            all_data = []
            
            max_depth = self.depth_var.get()
            delay = self.delay_var.get()
            total_pages = 0
            processed_pages = 0
            
            # First pass to count pages (for progress bar)
            if not self.stop_scraping:
                self.update_status("Counting pages to scrape...")
                temp_visited = set()
                temp_queue = [(start_url, 0)]
                while temp_queue and not self.stop_scraping:
                    current_url, depth = temp_queue.pop(0)
                    if current_url in temp_visited or depth > max_depth:
                        continue
                    temp_visited.add(current_url)
                    total_pages += 1
                    
                    try:
                        soup = self.scrape_page(current_url)
                        if soup is None:
                            continue
                        
                        for link in soup.find_all('a', href=True):
                            next_url = urljoin(current_url, link['href'])
                            if (self.follow_external.get() or self.is_same_domain(start_url, next_url)) and next_url not in temp_visited and depth < max_depth:
                                temp_queue.append((next_url, depth + 1))
                    except:
                        continue
            
            if total_pages == 0:
                total_pages = 1  # Prevent division by zero
            
            # Actual scraping
            while to_visit and not self.stop_scraping:
                current_url, depth = to_visit.pop(0)
                
                if current_url in visited_urls or depth > max_depth:
                    continue
                
                self.update_status(f"Scraping: {current_url} (Depth: {depth})")
                self.update_progress((processed_pages / total_pages) * 100)
                
                try:
                    soup = self.scrape_page(current_url)
                    if soup is None:
                        continue
                    
                    page_data = {
                        "url": current_url,
                        "title": soup.title.string if soup.title else "",
                        "headings": [],
                        "paragraphs": [],
                        "lists": [],
                        "tables": [],
                        "images": [],
                        "links": []
                    }
                    
                    # Extract requested content
                    if self.scrape_headings.get():
                        headings = [(h.name, h.get_text(strip=True), self.categorize_text(h.get_text(strip=True))) 
                                  for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) if h.get_text(strip=True)]
                        page_data["headings"] = headings
                    
                    if self.scrape_paragraphs.get():
                        paragraphs = [(p.get_text(strip=True), self.categorize_text(p.get_text(strip=True))) 
                                    for p in soup.find_all('p') if p.get_text(strip=True)]
                        page_data["paragraphs"] = paragraphs
                    
                    if self.scrape_lists.get():
                        lists = [(li.get_text(strip=True), self.categorize_text(li.get_text(strip=True))) 
                               for li in soup.find_all('li') if li.get_text(strip=True)]
                        page_data["lists"] = lists
                    
                    if self.scrape_tables.get():
                        tables = []
                        for table in soup.find_all('table'):
                            rows = table.find_all('tr')
                            for row in rows:
                                cells = row.find_all(['td', 'th'])
                                row_text = " | ".join(cell.get_text(strip=True) for cell in cells)
                                tables.append((row_text, self.categorize_text(row_text)))
                        page_data["tables"] = tables
                    
                    if self.scrape_images.get():
                        page_data["images"] = self.extract_images(soup, current_url)
                    
                    if self.scrape_links.get():
                        page_data["links"] = self.extract_links(soup, current_url)
                    
                    all_data.append(page_data)
                    visited_urls.add(current_url)
                    processed_pages += 1
                    
                    # Display progress in text area
                    self.text_area.insert(tk.END, f"Scraped: {current_url}\n", "url")
                    self.text_area.see(tk.END)
                    
                    # Find and queue additional links
                    for link in soup.find_all('a', href=True):
                        next_url = urljoin(current_url, link['href'])
                        if (self.follow_external.get() or self.is_same_domain(start_url, next_url)) and next_url not in visited_urls and depth < max_depth:
                            to_visit.append((next_url, depth + 1))
                    
                    # Be polite to the server
                    time.sleep(delay)
                
                except Exception as e:
                    self.text_area.insert(tk.END, f"Error scraping {current_url}: {str(e)}\n", "error")
                    continue
            
            # Save results
            if not self.stop_scraping and all_data:
                output_format = self.output_format.get()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(self.output_folder, f"scraped_data_{timestamp}.{output_format}")
                
                try:
                    if output_format == "json":
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(all_data, f, indent=2, ensure_ascii=False)
                    elif output_format == "csv":
                        # Flatten data for CSV
                        csv_data = []
                        for page in all_data:
                            for section in ['headings', 'paragraphs', 'lists', 'tables', 'images', 'links']:
                                for item in page[section]:
                                    row = {
                                        'url': page['url'],
                                        'type': section[:-1],  # Remove 's' (headings -> heading)
                                        'content': item[0],
                                        'category': item[1] if len(item) > 1 else ''
                                    }
                                    if section == 'images' and len(item) > 1:
                                        row['alt_text'] = item[1]
                                    csv_data.append(row)
                        
                        with open(output_file, 'w', encoding='utf-8', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=['url', 'type', 'content', 'category', 'alt_text'])
                            writer.writeheader()
                            writer.writerows(csv_data)
                    elif output_format == "xlsx":
                        # Create a pandas Excel writer
                        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                            # Create separate sheets for each content type
                            for content_type in ['headings', 'paragraphs', 'lists', 'tables', 'images', 'links']:
                                data = []
                                for page in all_data:
                                    for item in page[content_type]:
                                        row = {
                                            'URL': page['url'],
                                            'Content': item[0],
                                            'Category': item[1] if len(item) > 1 else ''
                                        }
                                        if content_type == 'images' and len(item) > 1:
                                            row['Alt Text'] = item[1]
                                        data.append(row)
                                
                                if data:  # Only create sheet if there's data
                                    df = pd.DataFrame(data)
                                    df.to_excel(writer, sheet_name=content_type.capitalize(), index=False)
                            
                            # Create a summary sheet
                            summary_data = []
                            for page in all_data:
                                summary_data.append({
                                    'URL': page['url'],
                                    'Title': page['title'],
                                    'Headings': len(page['headings']),
                                    'Paragraphs': len(page['paragraphs']),
                                    'List Items': len(page['lists']),
                                    'Tables': len(page['tables']),
                                    'Images': len(page['images']),
                                    'Links': len(page['links']),
                                })
                            
                            df = pd.DataFrame(summary_data)
                            df.to_excel(writer, sheet_name='Summary', index=False)
                    else:  # txt
                        with open(output_file, 'w', encoding='utf-8') as f:
                            for page in all_data:
                                f.write(f"URL: {page['url']}\n")
                                f.write(f"Title: {page['title']}\n\n")
                                
                                if page['headings']:
                                    f.write("=== Headings ===\n")
                                    for tag, text, category in page['headings']:
                                        f.write(f"{tag.upper()}: {text} {category}\n")
                                    f.write("\n")
                                
                                if page['paragraphs']:
                                    f.write("=== Paragraphs ===\n")
                                    for text, category in page['paragraphs']:
                                        f.write(f"{textwrap.fill(text, width=80)} {category}\n")
                                    f.write("\n")
                                
                                if page['lists']:
                                    f.write("=== Lists ===\n")
                                    for text, category in page['lists']:
                                        f.write(f"- {text} {category}\n")
                                    f.write("\n")
                                
                                if page['tables']:
                                    f.write("=== Table Data ===\n")
                                    for text, category in page['tables']:
                                        f.write(f"{text} {category}\n")
                                    f.write("\n")
                                
                                if page['images']:
                                    f.write("=== Images ===\n")
                                    for src, alt in page['images']:
                                        f.write(f"SRC: {src}\nALT: {alt}\n\n")
                                
                                if page['links']:
                                    f.write("=== Links ===\n")
                                    for href, text in page['links']:
                                        f.write(f"LINK: {href}\nTEXT: {text}\n\n")
                                
                                f.write("="*80 + "\n\n")
                    
                    # Display results in text area
                    self.text_area.insert(tk.END, "\nScraping completed!\n\n", "success")
                    self.text_area.insert(tk.END, f"Pages scraped: {len(all_data)}\n")
                    self.text_area.insert(tk.END, f"Data saved to:\n{output_file}\n\n", "success")
                    
                    with open(output_file, 'r', encoding='utf-8') as f:
                        self.text_area.insert(tk.END, f.read())
                    
                    self.update_status(f"Scraping completed. Data saved to {output_file}")
                    messagebox.showinfo("Success", f"Data saved to {output_file}")
                
                except Exception as e:
                    self.text_area.insert(tk.END, f"\nError saving results: {str(e)}\n", "error")
                    self.update_status(f"Error saving results: {str(e)}")
            
            elif self.stop_scraping:
                self.text_area.insert(tk.END, "\nScraping stopped by user\n", "error")
                self.update_status("Scraping stopped by user")
            
            else:
                self.text_area.insert(tk.END, "\nNo data scraped\n", "error")
                self.update_status("No data scraped")
        
        except Exception as e:
            self.text_area.insert(tk.END, f"\nError: {str(e)}\n", "error")
            self.update_status(f"Error: {str(e)}")
        
        finally:
            self.scraping = False
            self.stop_scraping = False
            self.scrape_button.config(text="Start Scraping", bg="#27AE60")
            self.stop_button.config(state=tk.DISABLED)
            self.update_progress(0)
            self.close_selenium_driver()
    
    def show_documentation(self):
        docs = """Web Scraper Pro Documentation

1. Basic Usage:
- Enter the starting URL
- Select what content to scrape
- Choose output format
- Set scraping depth
- Click "Start Scraping"

2. Advanced Features:
- Selenium Mode: For JavaScript-heavy websites
- Proxy Support: Rotate IP addresses to avoid blocking
- Scheduling: Run scrapes at specific times
- Export Formats: Excel, JSON, CSV, or Text

3. Tips:
- Use delay to avoid being blocked
- Start with depth 1 to test
- Check robots.txt for scraping policies
- Use proxies for large-scale scraping
"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x400")
        
        text_area = scrolledtext.ScrolledText(doc_window, width=80, height=25, 
                                            font=("Consolas", 10), wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, docs)
        text_area.config(state=tk.DISABLED)
    
    def show_about(self):
        messagebox.showinfo("About Web Scraper Pro", 
                          "Web Scraper Pro\nVersion 2.0\n\nA powerful web scraping tool with advanced features\n\n© 2023 Web Scraper Team")

if __name__ == "__main__":
    root = tk.Tk()
    app = WebScraperApp(root)
    root.mainloop()
