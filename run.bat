@echo off

for /f "tokens=2 delims==" %%a in (config.json) do (
    set %%a
)

pip install -r requirements.txt

python -m main
start http://localhost:5000