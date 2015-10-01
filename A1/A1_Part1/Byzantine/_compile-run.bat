rem set path=C:\Windows\Microsoft.NET\Framework64\v4.0.30319;%path%

csc /out:Byzantine.exe /r:System.Threading.Tasks.Dataflow.dll,System.Runtime.dll,System.Threading.Tasks.dll Byzantine.cs
pause

Byzantine.exe Generals4-No1.txt
pause

Byzantine.exe Generals4-No2.txt
pause

Byzantine.exe Generals4-Yes1.txt
pause

Byzantine.exe Generals4-Yes2.txt
pause

Byzantine.exe Generals4-Mix1.txt
pause

Byzantine.exe Generals4-Mix2.txt
pause

Byzantine.exe Generals7-No1.txt
pause

Byzantine.exe Generals7-Yes1.txt
pause