import tkinter as tk
from tkinter import scrolledtext, font
import threading
import uuid
import history_manager
import shopify_api
import llm_router

class AgentChatWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Shopify Agentic Assistant")
        self.root.geometry("800x600")
        
        # This makes the window "floating" (always on top of other windows)
        self.root.attributes("-topmost", True)  
        self.root.configure(bg="#f4f6f9")
        
        self.current_session_id = str(uuid.uuid4())
        self.message_history = []
        
        # Main layout: PanedWindow for resizable sidebar
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=5, bg="#d1d5db")
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left Sidebar (History)
        self.sidebar = tk.Frame(self.paned_window, bg="#2c3e50", width=200)
        self.paned_window.add(self.sidebar, minsize=150)
        
        self.new_chat_btn = tk.Button(self.sidebar, text="+ New Chat", bg="#1abc9c", fg="white", 
                                      font=("Segoe UI", 11, "bold"), relief="flat", command=self.start_new_chat)
        self.new_chat_btn.pack(fill=tk.X, padx=10, pady=15)
        
        self.history_listbox = tk.Listbox(self.sidebar, bg="#34495e", fg="white", font=("Segoe UI", 10), 
                                          relief="flat", selectbackground="#1abc9c", highlightthickness=0)
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.history_listbox.bind('<<ListboxSelect>>', self.load_selected_chat)
        
        # Database Status Label
        db_status_color = "#2ecc71" if history_manager.is_db_connected() else "#e74c3c"
        db_status_text = "● MongoDB Connected" if history_manager.is_db_connected() else "● Local Storage"
        self.db_status_label = tk.Label(self.sidebar, text=db_status_text, bg="#2c3e50", fg=db_status_color, font=("Segoe UI", 9, "bold"))
        self.db_status_label.pack(side=tk.BOTTOM, pady=10)
        
        self.session_map = [] # Maps listbox index to session_id
        
        # Right Chat Area
        self.chat_frame = tk.Frame(self.paned_window, bg="#f4f6f9")
        self.paned_window.add(self.chat_frame, minsize=400)
        
        # Custom Fonts
        self.header_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.text_font = font.Font(family="Segoe UI", size=10)
        
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state='disabled', 
                                                      bg="#ffffff", font=self.text_font, relief="flat", padx=15, pady=15)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Tags for colored headers and alignment
        self.chat_display.tag_config("user_header", foreground="#007bff", font=self.header_font)
        self.chat_display.tag_config("agent_header", foreground="#2c3e50", font=self.header_font)
        self.chat_display.tag_config("system_header", foreground="#e67e22", font=self.header_font)
        self.chat_display.tag_config("text", foreground="#333333")
        self.chat_display.tag_config("spacing", font=("Segoe UI", 4))
        
        # Input Frame
        input_frame = tk.Frame(self.chat_frame, bg="#f4f6f9")
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        self.entry_field = tk.Entry(input_frame, font=("Segoe UI", 11), relief="flat", highlightthickness=1, highlightbackground="#cccccc")
        self.entry_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=5)
        self.entry_field.bind("<Return>", self.send_message)
        
        self.send_button = tk.Button(input_frame, text="Send", command=self.send_message, bg="#007bff", fg="white", 
                                     font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2")
        self.send_button.pack(side=tk.RIGHT, ipadx=10, ipady=3)
        
        self.refresh_history_sidebar()
        self.start_new_chat()

    def start_new_chat(self):
        self.current_session_id = str(uuid.uuid4())
        self.message_history = []
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')
        self.append_message("System", "Agent UI started. Ready to help with your Shopify store!")
        self.history_listbox.selection_clear(0, tk.END)

    def refresh_history_sidebar(self):
        self.history_listbox.delete(0, tk.END)
        sessions = history_manager.get_all_sessions()
        self.session_map = []
        for s in sessions:
            self.history_listbox.insert(tk.END, s['title'])
            self.session_map.append(s['session_id'])

    def load_selected_chat(self, event):
        selection = self.history_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        session_id = self.session_map[index]
        
        self.current_session_id = session_id
        messages = history_manager.get_session_messages(session_id)
        
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')
        
        display_messages = [m for m in messages if m.get("role") in ["user", "assistant"] and m.get("content")]
        
        if not display_messages:
            self.append_message("System", "Empty chat loaded.")
        
        for msg in display_messages:
            sender = "You" if msg["role"] == "user" else "Agent"
            self.append_message(sender, msg["content"])
            
        self.message_history = messages

    def append_message(self, sender, message):
        self.chat_display.config(state='normal')
        
        if sender == "You":
            header_tag = "user_header"
        elif sender == "System":
            header_tag = "system_header"
        else:
            header_tag = "agent_header"
            
        self.chat_display.insert(tk.END, f"{sender}:\n", header_tag)
        self.chat_display.insert(tk.END, f"{message}\n", "text")
        self.chat_display.insert(tk.END, "\n", "spacing")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def send_message(self, event=None):
        user_text = self.entry_field.get().strip()
        if not user_text:
            return
            
        self.append_message("You", user_text)
        self.entry_field.delete(0, tk.END)
        
        # Disable input while processing
        self.entry_field.config(state='disabled')
        self.send_button.config(state='disabled')
        
        # Run agent logic
        threading.Thread(target=self.process_agent_response, args=(user_text,), daemon=True).start()

    def process_agent_response(self, text):
        # Save initial user message
        history_manager.save_message(self.current_session_id, "user", text)
        self.message_history.append({"role": "user", "content": text})
        
        try:
            response, self.message_history = llm_router.process_agent_message(self.message_history)
            
            # Save the entire updated history (including tool calls and assistant response)
            history_manager.save_full_session(self.current_session_id, self.message_history)
            
        except Exception as e:
            response = f"Error processing with LLM: {str(e)}"
            history_manager.save_message(self.current_session_id, "assistant", response)
            
        self.root.after(0, self.enable_input, response)
        
    def enable_input(self, response):
        self.append_message("Agent", response)
        self.refresh_history_sidebar()
        self.entry_field.config(state='normal')
        self.send_button.config(state='normal')
        self.entry_field.focus()

if __name__ == "__main__":
    root = tk.Tk()
    app = AgentChatWindow(root)
    root.mainloop()
