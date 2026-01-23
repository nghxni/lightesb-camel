@echo off
chcp 65001 >nul
set JAVA_OPTS=-Dfile.encoding=UTF-8 -Dconsole.encoding=UTF-8 -Duser.language=zh -Duser.country=CN
java %JAVA_OPTS% -jar lightesb-camel-1.0.0-SNAPSHOT.jar
pause
