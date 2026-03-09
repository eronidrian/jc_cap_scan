```
$ docker build --rm -t javacard .
$ docker run -it --rm -v $(pwd):/applet javacard
$ cd applet/SimpleApplet
$ ant -f jcbuild.xml build
```