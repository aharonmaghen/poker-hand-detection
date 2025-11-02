# Windows Setup Guide

## Do I need a virtual environment?

**Yes, it's highly recommended!** Using a virtual environment:
- Keeps your system Python clean
- Avoids conflicts with other projects
- Makes dependency management easier
- Allows different Python projects to use different package versions

## Quick Setup (PowerShell or Command Prompt)

### Step 1: Navigate to your project directory
```powershell
cd C:\aharon-poker-pornhub\poker-hand-detection
```

### Step 2: Create a virtual environment
```powershell
python -m venv venv
```

### Step 3: Activate the virtual environment

**In PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**In Command Prompt (cmd.exe):**
```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` at the beginning of your prompt.

### Step 4: Install required packages

**Option A: Using the Windows-specific requirements file:**
```powershell
pip install -r requirements_windows.txt
```

**Option B: Install manually:**
```powershell
pip install ultralytics>=8.0.0 numpy>=1.21.0 Pillow>=9.0.0 pywin32>=300
```

### Step 5: Verify installation
```powershell
python -c "import ultralytics, numpy, PIL, win32gui; print('All packages installed successfully!')"
```

### Step 6: Run the test script
```powershell
python test.py
```

## Required Modules

The script needs these packages:

1. **ultralytics** (>=8.0.0) - For YOLO11 model (card detection)
2. **numpy** (>=1.21.0) - For array operations
3. **Pillow** (>=9.0.0) - For image processing
4. **pywin32** (>=300) - Windows-specific package for window capture (finding scrcpy windows)

## Deactivating the Virtual Environment

When you're done, deactivate the virtual environment:
```powershell
deactivate
```

## Troubleshooting

### Issue: "python is not recognized"
- Make sure Python is installed and added to PATH
- Try using `py` instead of `python`:
  ```powershell
  py -m venv venv
  py test.py
  ```

### Issue: Execution Policy Error (PowerShell)
Run this command once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: ModuleNotFoundError after installation
- Make sure the virtual environment is activated (you should see `(venv)` in your prompt)
- Reinstall packages:
  ```powershell
  pip install --upgrade -r requirements_windows.txt
  ```

### Issue: pywin32 installation fails
- Make sure you're using a recent version of pip:
  ```powershell
  python -m pip install --upgrade pip
  ```
- Try installing pywin32 separately:
  ```powershell
  pip install pywin32
  ```

## Running Without Virtual Environment (Not Recommended)

If you choose not to use a virtual environment, you can install packages globally:

```powershell
pip install ultralytics>=8.0.0 numpy>=1.21.0 Pillow>=9.0.0 pywin32>=300
```

However, this can cause conflicts with other Python projects on your system.

