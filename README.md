# can-mask-filter
A program that calculates the CAN mask and filter based on DBC, knowing the messages we want to receive.

## Requirements
- Python 3.x
- `cantools` library (`pip install cantools`)

## How to Run Locally
1. Install the required dependencies:
   ```bash
   pip install cantools
   ```
2. Run the application from the project root:
   ```bash
   python src/can_filter_app.py
   ```

## How to Build Executable (.exe)
To create a standalone `.exe` file for Windows:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Run the build command:
   ```bash
   pyinstaller --noconfirm --onefile --windowed --name "CanMaskFilter" "src/can_filter_app.py"
   ```
   
The resulting `CanMaskFilter.exe` will be generated in the `dist/` folder.
