# 💰 Expense Tracker

A personal expense tracking project built in Python, offered in two flavors — a lightweight **CLI version** for quick terminal-based tracking, and an **advanced GUI version** for a more visual, user-friendly experience. Both versions persist data locally using JSON, so your expense history is saved between sessions.

---

## ✨ Features

### 🖥️ Basic Version — `expense_tracker/`
- Simple, distraction-free command-line interface
- Add, view, and manage expenses directly from the terminal
- Lightweight — no external dependencies beyond the Python standard library
- Data persisted to a local JSON file

### 🎨 Advanced Version — `advance_expense_tracker/`
- Graphical desktop interface for a more intuitive experience
- Point-and-click expense entry and management
- Visual, form-based workflow instead of typed commands
- Same underlying JSON-based data persistence

---

## 🧱 Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3 |
| Interface (Basic) | Command-Line Interface (CLI) |
| Interface (Advanced) | GUI (Tkinter) |
| Data Storage | JSON |

---

## 📂 Project Structure

```
Expense-tracker/
├── expense_tracker/           # Basic CLI version
│   └── ...
├── advance_expense_tracker/   # Advanced GUI version
│   └── ...
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- No external packages required for the CLI version
- Tkinter (usually bundled with Python; on Linux you may need `sudo apt install python3-tk`) for the GUI version

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/naman827/Expense-tracker.git
   cd Expense-tracker
   ```

2. **Run the version you want**

   **Basic (CLI):**
   ```bash
   cd expense_tracker
   python main.py
   ```

   **Advanced (GUI):**
   ```bash
   cd advance_expense_tracker
   python main.py
   ```

   > 💡 If your entry-point file has a different name, adjust the command accordingly.

---

## 🕹️ Usage

**CLI version** — follow the on-screen prompts in your terminal to add new expenses, view your expense history, and manage entries. All data is written to and read from a local JSON file automatically, so nothing is lost between runs.

**GUI version** — launch the app to open a desktop window where you can add expenses through input fields and buttons instead of typing commands. Like the CLI version, all entries are saved to a local JSON file behind the scenes.

---

## 🗺️ Roadmap

- [ ] Add expense categories and filtering
- [ ] Add monthly/weekly spending summaries and charts
- [ ] Migrate storage from JSON to SQLite for larger datasets
- [ ] Export expense history to CSV/PDF
- [ ] Merge CLI and GUI versions behind a shared core module

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the terms specified in the [LICENSE](./LICENSE) file.

---

## 👤 Author

**Naman**
GitHub: [@naman827](https://github.com/naman827)
