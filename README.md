# 🧩 Pattern Nesting Tool

<div align="center">
  
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)

**A tool for pattern layout optimization in the garment industry**

</div>

---

## 📋 Overview

The Pattern Nesting Tool is a specialized application designed for the garment and textile industry that helps maximize material usage by optimizing pattern layouts. By efficiently arranging pattern pieces on fabric markers, this tool reduces material waste, saves time, and improves production efficiency.

<div align="center">
  <img src="https://github.com/user-attachments/assets/4d1ffa62-116e-491a-af7d-55615c1d9810" width=600/>

  <p><em>Pattern nesting optimization example</em></p>
</div>

## ✨ Features

- **📂 DXF File Support** - Import pattern pieces from industry-standard DXF files
- **🔍 Pattern Visualization** - View and inspect pattern pieces with zoom/pan capabilities
- **📊 Pattern Analysis** - Calculate area, perimeter, and other metrics for each pattern piece
- **⚙️ Nesting Parameters** - Configure width, efficiency targets, and time limits
- **🚀 External Nesting Integration** - Seamless integration with industrial nesting programs
- **📊 Result Visualization** - Interactive display of optimized layout results
- **📈 Efficiency Analysis** - Calculate and display material utilization metrics
- **🔄 Batch Processing** - Queue and manage multiple nesting tasks via the Process Manager

## 🛠️ Installation

### Requirements

- Python 3.6 or higher
- PyQt5
- ezdxf

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/pattern-nesting.git
cd pattern-nesting

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```


## 🚀 Usage

### Basic Workflow

1. **Load Pattern File** - Import a DXF file containing pattern pieces
2. **Configure Parameters** - Set fabric width, efficiency targets, and time limits
3. **Generate WRK File** - Create a work file for the nesting program
4. **Run Nesting** - Execute the external nesting program
5. **Visualize Results** - View and analyze the optimized layout

### Advanced Features

- **Pattern Manager** - Manage multiple nesting tasks simultaneously
- **Result Comparison** - Compare efficiency between different nesting attempts
- **Settings Persistence** - Your preferences and program paths are automatically saved

## 📂 Project Structure

```
pattern_nesting/
│
├── core/                      # Core functionality
│   ├── parser.py              # SES file parser
│   └── settings.py            # Application settings manager
│
├── gui/                       # GUI components
│   ├── widgets/               # Custom widgets
│   │   ├── graphics_view.py   # Enhanced QGraphicsView
│   │   └── preview_widget.py  # Pattern preview widget
│   ├── dialogs/               # Dialog windows
│   │   └── add_task_dialog.py # Dialog for adding tasks
│   ├── main_window.py         # Main application window
│   └── process_manager.py     # Nesting process manager
│
├── models/                    # Data models
│   └── nesting_task.py        # Nesting task model
│
├── docs/                      # Documentation
│   ├── images/                # Documentation images
│   └── usage_guide.md         # Detailed usage guide
│
├── main.py                    # Application entry point
└── requirements.txt           # Dependencies
```

## 📘 Detailed Documentation

For more detailed instructions, see the [Usage Guide](docs/usage_guide.md).


## 🖼️ Screenshots

<div align="center">
  <img src="https://github.com/user-attachments/assets/f9d0ba7d-45d5-4695-bdfe-32a40851f0b1" width=600/>

  <p><em>Main application window</em></p>
</div>

<div align="center">
  <img src="https://github.com/user-attachments/assets/b1e06733-c25c-48fc-b06c-3b233d4aaf77" width=600/>

  <p><em>Nesting result visualization</em></p>
</div>


## 📞 Support

For support or questions, please contact [vladyslavmos@gmail.com](mailto:vladyslavmos@gmail.com).

---

<div align="center">
  
  **Created with ❤️ by VladMos**
  
</div>
