set builddir=C:\Temp\build_cts
set repo=%builddir%\repo
set distbase=%builddir%\dist
set distdir=cryptotaxsweden
set package=%distdir%.zip
echo %builddir%

rmdir /S /Q %builddir%
mkdir %builddir%
git clone . %repo%

cd %repo%
virtualenv venv
call venv\scripts\activate.bat
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile report.py
mkdir %distbase%\%distdir%
copy dist\report.exe %distbase%\%distdir%\
copy README.md %distbase%\%distdir%\
copy LICENSE %distbase%\%distdir%\
mkdir %distbase%\%distdir%\data
copy data\personal_details_template.json %distbase%\%distdir%\data\
copy data\stocks_template.json %distbase%\%distdir%\data\
mkdir %distbase%\%distdir%\data\rates
copy data\rates\usdsek.csv %distbase%\%distdir%\data\rates\
mkdir %distbase%\%distdir%\docs
copy docs\K4-template-*.pdf %distbase%\%distdir%\docs\
cd %distbase%
"c:\Program Files\7-Zip\7z.exe" a -r %package% %distdir%
