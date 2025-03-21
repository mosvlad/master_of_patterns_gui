# Pattern Nesting Tool - Usage Guide

This guide provides instructions for using the Pattern Nesting Tool application to optimize pattern layouts.

## Table of Contents

1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Loading DXF Files](#loading-dxf-files)
4. [Working with Patterns](#working-with-patterns)
5. [Generating WRK Files](#generating-wrk-files)
6. [Running the Nesting Program](#running-the-nesting-program)
7. [Viewing Nesting Results](#viewing-nesting-results)
8. [Using the Process Manager](#using-the-process-manager)
9. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.6 or higher
- PyQt5
- ezdxf

### Install from Source

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pattern-nesting.git
   cd pattern-nesting
   ```

2. Install requirements:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

### Install as Package

```
pip install .
pattern-nesting
```

## Getting Started

When you first open the application, you'll see the main window divided into two panels:

- **Left Panel**: Contains file path inputs, nesting parameters, and action buttons
- **Right Panel**: Contains the pattern visualization and data tabs

## Loading DXF Files

1. Click the "Browse..." button next to "DXF File" or use the "Load DXF" toolbar button
2. Select a DXF file containing pattern pieces
3. Click the "Load DXF" button to parse and display the pattern pieces

The DXF file should contain blocks (preferably with names starting with 'B') that represent individual pattern pieces. If no blocks are found, the application will try to use entities directly from the modelspace.

## Working with Patterns

Once a DXF file is loaded, the pattern pieces will be displayed in the "Pattern Pieces" tab. You can:

- **Zoom In/Out**: Use the mouse wheel or the toolbar buttons
- **Pan**: Click and drag with the middle mouse button or left mouse button
- **Fit View**: Click the "Fit View" toolbar button to show all patterns
- **View Pattern Data**: Switch to the "Pattern Data" tab to see information about each pattern piece, including area and perimeter calculations

## Generating WRK Files

The WRK file contains instructions for the nesting program. To generate it:

1. Set nesting parameters in the left panel:
   - **Width**: The width of the material
   - **Min Efficiency**: Target efficiency for the nesting algorithm
   - **Time Limit**: Maximum time for the nesting algorithm to run
   - **Flip Options**: Allow horizontal or vertical flipping of patterns

2. Click the "Generate WRK File" button
3. If prompted, select a location to save the WRK file

## Running the Nesting Program

Before running the nesting program, you need to:

1. Select the nesting program executable by clicking "Browse..." next to "Nesting Program"
2. Generate a WRK file (see previous section)

Then click the "Run Nesting Program" button or use the toolbar button. A progress dialog will appear showing:

- The status of the nesting process
- A progress bar based on elapsed time vs. time limit
- Time elapsed
- Information about the nesting parameters

The nesting program will be executed with the WRK file as an argument. When it completes, you'll be asked if you want to view the results.

## Viewing Nesting Results

Nesting results are stored in SES files (usually with the same base name as your DXF file). You can view them by:

1. Clicking "Yes" when prompted after a successful nesting operation
2. Using the "Load Nesting Result" toolbar button
3. Using the "View Result" feature in the Process Manager

The nesting result will be displayed in the "Nesting Result" tab, showing:

- The positioned pattern pieces
- Piece IDs
- Marker dimensions and efficiency information

## Using the Process Manager

The Process Manager allows you to:

1. **Queue Multiple Tasks**: Add multiple nesting tasks and run them sequentially or in parallel
2. **Monitor Progress**: See the status and progress of each task
3. **View Results**: View the results of completed tasks
4. **Manage Tasks**: Start, stop, and remove tasks

To open the Process Manager, click the "Process Manager" toolbar button.

### Adding a Task

1. Click "Add Task" in the Process Manager
2. Select a DXF file
3. Set the width and time limit
4. Optionally check "Start immediately" to run the task right away

### Managing Tasks

- **Start**: Select a task and click "Start"
- **Stop**: Select a running task and click "Stop"
- **View Result**: Select a completed task and click "View Result"
- **Remove**: Select a task and click "Remove"

## Troubleshooting

### DXF File Issues

- Ensure the DXF file contains blocks (preferably with names starting with 'B')
- Check that the file is not corrupted or in an unsupported format
- Try simplifying complex patterns

### Nesting Program Issues

- Make sure the nesting program executable is correctly selected
- Check that the WRK file is correctly formatted
- Look for error messages in the process output

### Other Issues

- If the application crashes, check the console output for error messages
- Ensure you have sufficient disk space and memory
- Try restarting the application