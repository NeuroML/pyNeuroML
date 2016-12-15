
if [ ! -d "jdk1.8.0_112" ] ; 

then 

    wget --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u112-b15/jdk-8u112-linux-x64.tar.gz
    tar xvzf jdk-8u112-linux-x64.tar.gz
    rm jdk-8u112-linux-x64.tar.gz

fi

export JAVA_HOME="`pwd`/jdk1.8.0_112"
echo "Set JAVA_HOME to $JAVA_HOME"
export PATH=$JAVA_HOME/bin:$PATH
echo "Set PATH to $PATH"

