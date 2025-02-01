import tkinter as tk
from tkinter import ttk
import PIL.Image, PIL.ImageTk, PIL.ImageSequence # type: ignore
import ollama
import pygments
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from tkhtmlview import HTMLLabel

class AnimatedIcon:
    def __init__(self, path, size):
        self.frames = []
        self.size = size
        self.load_frames(path)

    def load_frames(self, path):
        image = PIL.Image.open(path)
        for frame in PIL.ImageSequence.Iterator(image):
            frame = frame.resize(self.size, PIL.Image.Resampling.LANCZOS)
            self.frames.append(PIL.ImageTk.PhotoImage(frame))

    def get_frames(self):
        return self.frames

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LogRig Chatbot")
        self.root.geometry("900x700")
        self.root.configure(bg="#000000")
        self.root.overrideredirect(True)
        
        # Initialize is_maximized as False
        self.is_maximized = False
        
        # Available models
        self.models = [
            "qwen2.5", "olmo2", "deepseek-r1", "llama3.2:latest", "llama3.2-vision", 
            "codellama", "mistral:latest", "phi4", "llama3.3", "nomic-embed-text"
        ]
        self.selected_model = tk.StringVar()
        self.selected_model.set(self.models[0])  # Default model

        # Title bar frame
        self.title_bar = tk.Frame(self.root, bg="#121212", relief='raised', bd=0, height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)

        # Window title
        title_label = tk.Label(self.title_bar, text="LogRig Chatbot", bg="#121212", fg="white")
        title_label.pack(side=tk.LEFT, padx=10)

        # Model Selection Dropdown
        model_label = tk.Label(self.title_bar, text="Model:", bg="#121212", fg="white")
        model_label.pack(side=tk.LEFT, padx=(20, 5))

        model_dropdown = ttk.Combobox(self.title_bar, textvariable=self.selected_model, values=self.models, state="readonly")
        model_dropdown.pack(side=tk.LEFT)
        
        # Window control buttons
        self.close_button = tk.Button(self.title_bar, text="✖", command=self.root.quit, 
                                      bg="#121212", fg="#ff5f5f", bd=0, padx=5, pady=2)
        self.close_button.pack(side=tk.RIGHT, padx=5)
        
        self.maximize_button = tk.Button(self.title_bar, text="⬜", command=self.toggle_maximize, 
                                         bg="#121212", fg="#5f87ff", bd=0, padx=5, pady=2)
        self.maximize_button.pack(side=tk.RIGHT)
        
        self.minimize_button = tk.Button(self.title_bar, text="➖", command=self.minimize_window, 
                                         bg="#121212", fg="#5fff5f", bd=0, padx=5, pady=2)
        self.minimize_button.pack(side=tk.RIGHT)

        # Bind window movement events
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        self.title_bar.bind("<Double-Button-1>", lambda e: self.toggle_maximize())
        
        # Add window border frame
        self.border_frame = tk.Frame(self.root, bg="#121212")
        self.border_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))

        # Chat display frame with background image
        self.chat_display_frame = tk.Frame(self.border_frame, bg="#121212")
        self.chat_display_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        self.bg_image = PIL.Image.open("images/bg.jpg")
        self.bg_photo = PIL.ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self.chat_display_frame, image=self.bg_photo, bg="#121212")
        self.bg_label.place(relwidth=1, relheight=1)
        
        # Create custom style for the Text widget
        self.chat_display = tk.Text(self.chat_display_frame, 
                                    bg="#121212", 
                                    fg="white",
                                    font=("Arial", 12), 
                                    state=tk.DISABLED, 
                                    wrap=tk.WORD,
                                    insertbackground="white")  # Make cursor white
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for consistent text colors
        self.chat_display.tag_configure("message_container", spacing1=5, spacing3=5)
        self.chat_display.tag_configure("default_text", foreground="white")
        self.chat_display.tag_configure("prompt_text", foreground="#5f87ff")  # Prompt text in blue

        # Input frame
        self.input_frame = ttk.Frame(self.border_frame)
        self.input_frame.pack(pady=10, fill=tk.X, padx=20)

        # Style the entry widget
        self.style = ttk.Style()
        self.style.configure("Custom.TEntry", foreground="black", fieldbackground="#121212")
        
        self.input_entry = ttk.Entry(self.input_frame, style="Custom.TEntry")
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Load icons
        self.bot_icon = AnimatedIcon("icons/png/bot.png", (40, 40))
        self.user_icon = AnimatedIcon("icons/png/human.png", (40, 40))
        self.animate_icons()

    def toggle_maximize(self):
        if not self.is_maximized:
            self.previous_state = {
                'geometry': self.root.geometry()
            }
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.maximize_button.configure(text="❐")
            self.is_maximized = True
        else:
            self.root.geometry(self.previous_state['geometry'])
            self.maximize_button.configure(text="⬜")
            self.is_maximized = False

    def minimize_window(self):
        if self.normal_geometry is None:
            self.normal_geometry = self.root.geometry()
        self.root.overrideredirect(False)  # Temporarily show window decorations
        self.root.iconify()

    def on_map(self, event):
        if self.normal_geometry:
            self.root.overrideredirect(True)  # Remove window decorations
            self.root.geometry(self.normal_geometry)

    def on_unmap(self, event):
        if not self.root.state() == 'iconic':  # If not minimized
            self.normal_geometry = self.root.geometry()

    def start_move(self, event):
        if not self.is_maximized:
            self.x = event.x
            self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        if not self.is_maximized:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

    def send_message(self):
        message = self.input_entry.get().strip()
        if message:
            self.display_message(message, is_user=True)
            self.input_entry.delete(0, tk.END)
            self.root.after(1000, self.bot_response, message)

    def bot_response(self, user_message):
        try:
            selected_model = self.selected_model.get()  # Get the selected model
            response = ollama.generate(model=selected_model, prompt=user_message)
            bot_message = response['response']
            if "def" in bot_message or "import" in bot_message:
                bot_message = self.format_code(bot_message)
        except Exception as e:
            bot_message = f"Error: {str(e)}"
        self.display_message(bot_message, is_user=False)

    def format_code(self, code):
        formatter = HtmlFormatter(style="monokai")
        formatted_code = pygments.highlight(code, PythonLexer(), formatter)
        return formatted_code

    def display_message(self, message, is_user=True):
        self.chat_display.config(state=tk.NORMAL)
        
        # Create message container frame
        message_frame = tk.Frame(self.chat_display, bg="#121212")
        
        # Add appropriate icon
        icon = self.user_icon if is_user else self.bot_icon
        icon_label = tk.Label(message_frame, image=icon.get_frames()[0], bg="#121212")
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create message content frame
        content_frame = tk.Frame(message_frame, bg="#121212")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add message content
        if message.startswith("<div"):
            html_label = HTMLLabel(content_frame, html=message, background="#121212", foreground="white")
            html_label.pack(fill=tk.BOTH, expand=True)
        else:
            if is_user:
                message_label = tk.Label(content_frame, text=message, fg="white", bg="#121212", 
                                         justify=tk.LEFT, wraplength=600, anchor="w")
            else:
                message_label = tk.Label(content_frame, text=message, fg="white", bg="#121212", 
                                         justify=tk.LEFT, wraplength=600, anchor="w")
            
            message_label.pack(fill=tk.BOTH, expand=True)
        
        # Insert the frame into chat display
        self.chat_display.window_create(tk.END, window=message_frame, padx=5, pady=5)
        self.chat_display.insert(tk.END, "\n", ("message_container", "default_text"))
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def animate_icons(self):
        self.root.after(100, self.animate_icons)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
