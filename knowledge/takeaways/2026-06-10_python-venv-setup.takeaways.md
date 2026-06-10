# Takeaways — Python venv setup for MotionBlocks

## Goal

Create and use a local Python virtual environment for MotionBlocks tools, for example `tools/serial_logger.py`.

---

## Project folder

Always run Python tool commands from the **root of the repository**:

```powershell
cd C:\Users\XPS\Documents\proj\motionblocks
```

This is the folder that contains:

```text
firmware/
tools/
data/
docs/
llm/
README.md
```

Do **not** run the logger from:

```text
firmware/m5stickc-plus2
```

Otherwise files may be created in the wrong place.

---

## Create virtual environment

From the repository root:

```powershell
python -m venv .venv
```

Wait until the command finishes and PowerShell prompt appears again.

---

## Activate virtual environment

In PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the prompt should start with:

```text
(.venv)
```

Example:

```text
(.venv) PS C:\Users\XPS\Documents\proj\motionblocks>
```

---

## If activation is blocked

If PowerShell blocks `Activate.ps1`, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Install dependencies

For the serial logger:

```powershell
pip install pyserial
```

Check installation:

```powershell
python -c "import serial; print(serial.__version__)"
```

---

## Run serial logger

Make sure PlatformIO Serial Monitor is closed.

Then run:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001
```

---

## Usual daily startup

Each new terminal session:

```powershell
cd C:\Users\XPS\Documents\proj\motionblocks
.\.venv\Scripts\Activate.ps1
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001
```

---

## Git rule

The virtual environment must not be committed to Git.

`.gitignore` should contain:

```gitignore
.venv/
venv/
```
