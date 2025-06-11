import tkinter as tk
from tkinter import messagebox
import mysql.connector
import pandas as pd
#pip install openpyxl
#pip install mysql-connector-python
#pip install pandas
#pip install tkinter

#Color assignments
BG_COLOR = "#2A2A57"  
FG_COLOR = "#abb2bf"
BUTTON_BG = "#A50000"      
BUTTON_FG = "#FFFFFF"   
FONT_NAME = "Helvetica"
FONT_SIZE = 14
BUTTON_WIDTH = 12
BUTTON_HEIGHT = 2
PAD_X = 10
PAD_Y = 10

#MYSQL AIVEN Server Connection
conn = mysql.connector.connect(
    host="mysql-27cf8055-otaviosdlopes-2a4d.i.aivencloud.com",
    port=20598,
    user="avnadmin",
    password="AVNS_NSxRHj-dNDoIaKEyhgE",
    database="jogo_milhao"
)
cursor = conn.cursor()


def load_questions(topic, difficulty):
    try:
        df = pd.read_excel("questions.xlsx")
    except FileNotFoundError:
        messagebox.showerror("Error", "Questions file not found.")
        return []

    df['Topic'] = df['Topic'].str.lower()
    df['Difficulty'] = df['Difficulty'].str.lower()

    filtered = df[(df['Topic'] == topic.lower()) & (df['Difficulty'] == difficulty.lower())]
    if filtered.empty:
        messagebox.showwarning("No Questions", "No questions found for this topic and difficulty.")
        return []

    return filtered.sample(min(12, len(filtered))).to_dict('records')


class User:
    def __init__(self, email, role):
        self.email = email
        self.role = role
        self.score = 0
        self.difficulty = ''
        self.topic = ''

    def update_score(self, score, difficulty, topic):
        self.score = score
        self.difficulty = difficulty
        self.topic = topic
        if self.role == "student":
            cursor.execute(
                "UPDATE students SET score = %s, difficulty = %s, topic = %s WHERE email = %s",
                (score, difficulty, topic, self.email)
            )
            conn.commit()


class LoginScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG_COLOR)
        self.app = app
        self.role_var = tk.StringVar(value="student")
        self.create_widgets()
        self.pack(expand=True, fill="both")

    def create_widgets(self):
        title = tk.Label(self, text="Login or Register", font=(FONT_NAME, 30, "bold"), fg=FG_COLOR, bg=BG_COLOR)
        title.pack(pady=40)

        role_frame = tk.Frame(self, bg=BG_COLOR)
        role_frame.pack(pady=20)
        tk.Label(role_frame, text="Select Role:", font=(FONT_NAME, 18), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)

        roles = [("Student", "student"), ("Teacher", "teacher")]
        for text, val in roles:
            rb = tk.Radiobutton(role_frame, text=text, variable=self.role_var, value=val,
                                font=(FONT_NAME, 16), fg=FG_COLOR, bg=BG_COLOR,
                                selectcolor=BUTTON_BG, indicatoron=0, width=10,
                                command=self.on_role_change)
            rb.pack(side=tk.LEFT, padx=10)

        self.email_label = tk.Label(self, text="Email:", fg=FG_COLOR, bg=BG_COLOR, font=(FONT_NAME, FONT_SIZE))
        self.email_label.pack(pady=(20, 5))
        self.email_entry = tk.Entry(self, width=40, font=(FONT_NAME, FONT_SIZE))
        self.email_entry.pack(pady=(0, PAD_Y))

        self.password_label = tk.Label(self, text="Password:", fg=FG_COLOR, bg=BG_COLOR, font=(FONT_NAME, FONT_SIZE))
        self.password_label.pack(pady=(10, 5))
        self.password_entry = tk.Entry(self, width=40, show="*", font=(FONT_NAME, FONT_SIZE))
        self.password_entry.pack(pady=(0, PAD_Y))

        self.login_btn = tk.Button(self, text="Login", bg=BUTTON_BG, fg=BUTTON_FG, width=BUTTON_WIDTH,
                                   height=BUTTON_HEIGHT, command=self.login_user)
        self.login_btn.pack(pady=15)

        self.register_btn = tk.Button(self, text="Register", bg=BUTTON_BG, fg=BUTTON_FG, width=BUTTON_WIDTH,
                                      height=BUTTON_HEIGHT, command=self.register_user)
        self.register_btn.pack()

        self.on_role_change()

    def on_role_change(self):
        role = self.role_var.get()
        if role == "teacher":
            self.email_label.pack_forget()
            self.email_entry.pack_forget()
            self.password_label.pack_forget()
            self.password_entry.pack_forget()
            self.login_btn.config(text="View Rankings", command=self.app.show_rankings_screen)
            self.register_btn.pack_forget()
        else:
            self.email_label.pack(pady=(20, 5))
            self.email_entry.pack(pady=(0, PAD_Y))
            self.password_label.pack(pady=(10, 5))
            self.password_entry.pack(pady=(0, PAD_Y))
            self.login_btn.config(text="Login", command=self.login_user)
            self.register_btn.pack()

    def login_user(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        if not email or not password:
            messagebox.showwarning("Input Error", "Please enter both email and password.")
            return

        table = "students" if role == "student" else "teachers"
        cursor.execute(f"SELECT * FROM {table} WHERE email=%s AND password=%s", (email, password))
        if cursor.fetchone():
            self.app.current_user = User(email, role)
            self.app.show_topic_difficulty_screen()
        else:
            messagebox.showerror("Authentication Failed", "Invalid email or password.")

    def register_user(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        if not email or not password:
            messagebox.showwarning("Input Error", "Please enter both email and password.")
            return

        table = "students" if role == "student" else "teachers"
        cursor.execute(f"SELECT email FROM {table} WHERE email = %s", (email,))
        if cursor.fetchone():
            messagebox.showerror("Registration Failed", f"Email already registered as {role}.")
            return

        if role == "student":
            cursor.execute(f"INSERT INTO {table} (email, password, score, difficulty, topic) VALUES (%s, %s, 0, '', '')",
                           (email, password))
        else:
            cursor.execute(f"INSERT INTO {table} (email, password) VALUES (%s, %s)", (email, password))

        conn.commit()
        messagebox.showinfo("Success", f"Registration successful as {role}! You can now log in.")


class TopicDifficultyScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG_COLOR)
        self.app = app
        self.topic_var = tk.StringVar(value="")
        self.difficulty_var = tk.StringVar(value="")
        self.create_widgets()
        self.pack(expand=True, fill="both")

    def create_widgets(self):
        self.clear_screen()

        self.add_return_button()

        tk.Label(self, text="Select Topic", font=(FONT_NAME, 28, "bold"), fg=FG_COLOR, bg=BG_COLOR).pack(pady=20)

        topics = self.get_unique_column_values('Topic')

        topics_frame = tk.Frame(self, bg=BG_COLOR)
        topics_frame.pack()

        for t in topics:
            btn = tk.Radiobutton(topics_frame, text=t.capitalize(), variable=self.topic_var, value=t,
                                 font=(FONT_NAME, FONT_SIZE), fg=FG_COLOR, bg=BG_COLOR,
                                 selectcolor=BUTTON_BG, indicatoron=0, width=BUTTON_WIDTH + 4)
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Label(self, text="Select Difficulty", font=(FONT_NAME, 28, "bold"), fg=FG_COLOR, bg=BG_COLOR).pack(pady=20)

        difficulties = ['easy', 'medium', 'hard']

        diff_frame = tk.Frame(self, bg=BG_COLOR)
        diff_frame.pack()

        for d in difficulties:
            btn = tk.Radiobutton(diff_frame, text=d.capitalize(), variable=self.difficulty_var, value=d,
                                 font=(FONT_NAME, FONT_SIZE), fg=FG_COLOR, bg=BG_COLOR,
                                 selectcolor=BUTTON_BG, indicatoron=0, width=BUTTON_WIDTH + 4)
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        start_btn = tk.Button(self, text="Start Quiz", bg=BUTTON_BG, fg=BUTTON_FG, width=BUTTON_WIDTH + 4,
                              height=BUTTON_HEIGHT + 1, command=self.start_quiz)
        start_btn.pack(pady=40)

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def add_return_button(self):
        btn = tk.Button(self, text="Return to Menu", bg=BUTTON_BG, fg=BUTTON_FG,
                        font=(FONT_NAME, FONT_SIZE), width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                        command=self.app.show_login_screen)
        btn.pack(side=tk.BOTTOM, pady=20)

    def get_unique_column_values(self, column_name):
        try:
            df = pd.read_excel("questions.xlsx")
            return sorted(df[column_name].dropna().str.lower().unique())
        except Exception:
            if column_name == 'Topic':
                return ['math', 'history', 'science']
            return []

    def start_quiz(self):
        topic = self.topic_var.get()
        difficulty = self.difficulty_var.get()

        if not topic or not difficulty:
            messagebox.showwarning("Selection Error", "Please select both topic and difficulty.")
            return

        self.app.current_user.topic = topic
        self.app.current_user.difficulty = difficulty

        questions = load_questions(topic, difficulty)

        if not questions:
            messagebox.showerror("No Questions", "No questions available for this selection.")
            return

        self.app.show_quiz_screen(questions)


class QuizScreen(tk.Frame):
    def __init__(self, master, app, questions):
        super().__init__(master, bg=BG_COLOR)
        self.app = app
        self.questions = questions
        self.current_q_index = 0
        self.score = 0
        self.money_tree = [100, 200, 300, 500, 1000, 2000, 4000,
                           8000, 16000, 32000, 64000, 125000]
        self.create_widgets()
        self.pack(expand=True, fill="both")

    def create_widgets(self):
        self.clear_screen()
        self.display_question()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def display_question(self):
        if self.current_q_index >= len(self.questions):
            messagebox.showinfo("Quiz Complete", f"Congrats! You completed the quiz with ${self.score}.")
            self.app.current_user.update_score(self.score, self.app.current_user.difficulty, self.app.current_user.topic)
            self.app.show_topic_difficulty_screen()
            return

        q = self.questions[self.current_q_index]

        question_label = tk.Label(self, text=f"Question {self.current_q_index + 1}: {q['Question']}",
                                  wraplength=1000, font=(FONT_NAME, 20), fg=FG_COLOR, bg=BG_COLOR)
        question_label.pack(pady=30)

        options_frame = tk.Frame(self, bg=BG_COLOR)
        options_frame.pack()

        def check_answer(selected):
            correct = q['CorrectAnswer'].upper()
            if selected == correct:
                self.score = self.money_tree[self.current_q_index]
                messagebox.showinfo("Correct!", f"Correct! You earned ${self.score}")
                self.current_q_index += 1
                self.clear_screen()
                self.display_question()
            else:
                messagebox.showerror("Wrong", "Wrong answer! Game over.")
                self.app.current_user.update_score(self.score, self.app.current_user.difficulty, self.app.current_user.topic)
                self.app.show_topic_difficulty_screen()

        for option_key in ['OptionA', 'OptionB', 'OptionC', 'OptionD']:
            btn = tk.Button(options_frame, text=f"{option_key[-1]}. {q[option_key]}", bg=BUTTON_BG, fg=BUTTON_FG,
                            font=(FONT_NAME, FONT_SIZE), width=50, height=2,
                            command=lambda c=option_key[-1]: check_answer(c))
            btn.pack(pady=5)

        quit_btn = tk.Button(self, text="Quit", bg=BUTTON_BG, fg=BUTTON_FG,
                             width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                             command=self.quit_quiz)
        quit_btn.pack(pady=20)

    def quit_quiz(self):
        if messagebox.askyesno("Quit", "Are you sure you want to quit? Your current score will be saved."):
            self.app.current_user.update_score(self.score, self.app.current_user.difficulty, self.app.current_user.topic)
            self.app.show_topic_difficulty_screen()


class RankingView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG_COLOR)
        self.app = app
        self.create_widgets()
        self.pack(expand=True, fill="both")

    def create_widgets(self):
        self.clear_screen()

        label = tk.Label(self, text="Student Rankings", font=(FONT_NAME, 30, "bold"), fg=FG_COLOR, bg=BG_COLOR)
        label.pack(pady=20)

        columns = ["Email", "Score", "Difficulty", "Topic"]

        # Treeview for rankings
        import tkinter.ttk as ttk
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor=tk.CENTER)
        self.tree.pack(pady=20)

        self.load_rankings()

        back_btn = tk.Button(self, text="Back to Menu", bg=BUTTON_BG, fg=BUTTON_FG,
                             width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                             command=self.app.show_login_screen)
        back_btn.pack(pady=20)

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def load_rankings(self):
        cursor.execute("SELECT email, score, difficulty, topic FROM students ORDER BY score DESC LIMIT 50")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Who Wants to Be a Millionaire? Quiz")
        self.geometry("1200x750")
        self.configure(bg=BG_COLOR)
        self.current_user = None
        self.fullscreen = True
        self.attributes("-fullscreen", self.fullscreen)
        self.bind("<Escape>", self.toggle_fullscreen)
        self.active_frame = None
        self.show_login_screen()

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)

    def switch_frame(self, new_frame_class, *args):
        if self.active_frame is not None:
            self.active_frame.destroy()
        self.active_frame = new_frame_class(self, self, *args)

    def show_login_screen(self):
        self.switch_frame(LoginScreen)

    def show_topic_difficulty_screen(self):
        self.switch_frame(TopicDifficultyScreen)

    def show_quiz_screen(self, questions):
        self.switch_frame(QuizScreen, questions)

    def show_rankings_screen(self):
        self.switch_frame(RankingView)


if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
    cursor.close()
    conn.close()
