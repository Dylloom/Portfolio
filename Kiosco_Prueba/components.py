import tkinter as tk

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=150, height=38, radius=14, color="#111827", text_color="#FFFFFF", bg_color="#FFFFFF"):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0, bd=0)
        self.command = command
        self.color = color
        self.text_color = text_color
        self.radius = radius
        self.width = width
        self.height = height
        self.text = text
        self.draw()
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        self.bind("<Leave>", lambda e: self.config(cursor=""))

    def draw(self):
        self.delete("all")
        r, w, h = self.radius, self.width, self.height
        self.create_oval(0, 0, r, r, fill=self.color, outline=self.color)
        self.create_oval(w-r, 0, w, r, fill=self.color, outline=self.color)
        self.create_oval(0, h-r, r, h, fill=self.color, outline=self.color)
        self.create_oval(w-r, h-r, w, h, fill=self.color, outline=self.color)
        self.create_rectangle(r/2, 0, w-r/2, h, fill=self.color, outline=self.color)
        self.create_rectangle(0, r/2, w, h-r/2, fill=self.color, outline=self.color)
        self.create_text(w//2, h//2, text=self.text, fill=self.text_color, font=("Arial", 10, "bold"))
