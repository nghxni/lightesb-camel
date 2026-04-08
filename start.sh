#!/usr/bin/env bash

export JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8"

java -noverify -javaagent:./lightesb-camel-1.0.0.jar="-pwd test" -jar ./lightesb-camel-1.0.0.jar
