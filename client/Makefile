DL=`ldd /bin/ls | grep "libdl.so" | awk '{ print $$3 }'`
LIBC=`ldd /bin/ls | grep "libc.so" | awk '{ print $$3 }'`
DEBUG=1
HOSTNAME=`hostname`

all: database_server.c add_users_and_groups.c preload.c
	echo "#define LIBC \"${LIBC}\"" > preload.h
	echo "#define HOSTNAME \"${HOSTNAME}\"" >> preload.h
	gcc database_server.c -o database_server
	gcc add_users_and_groups.c -o add_users_and_groups
	gcc -rdynamic -shared -fPIC -o preload.so preload.c ${DL}

debug: database_server.c add_users_and_groups.c preload.c
	echo "#define LIBC \"${LIBC}\"" > preload.h
	echo "#define DEBUG" >> preload.h
	gcc database_server.c -o database_server
	gcc add_users_and_groups.c -o add_users_and_groups
	gcc -rdynamic -shared -fPIC -o preload.so preload.c ${DL}
