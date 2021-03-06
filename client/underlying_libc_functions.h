#ifndef _UND_LIBC_FUN_H_
#define _UND_LIBC_FUN_H_

#include <dlfcn.h>
#include "preload.h"

void *get_libc() {
    static void *libc_handle = 0;
    if (!libc_handle) {
        libc_handle = dlopen(LIBC, RTLD_LAZY);
    }
    return libc_handle;
}

pid_t underlying_fork(void) {
    static pid_t (*underlying)(void) = 0;
    if (!underlying) {
        underlying = dlsym(get_libc(), "fork");
    }
    return (*underlying)();
}

int underlying_open(const char *pathname, int flags) {
    static int (*underlying)(const char *pathname, int flags) = 0;
    if (!underlying) {
        underlying = dlsym(get_libc(), "open");
    }
    return (*underlying)(pathname, flags);
}

int underlying_read(int fd, void *buf, size_t count) {
    static int (*underlying)(int fd, void *buf, size_t count) = 0;
    if (!underlying) {
        underlying = dlsym(get_libc(), "read");
    }
    return (*underlying)(fd, buf, count);
}

int underlying_write(int fd, const void *buf, size_t count) {
    static int (*underlying)(int fd, const void *buf, size_t count) = 0;
    if (!underlying) {
        underlying = dlsym(get_libc(), "write");
    }
    return (*underlying)(fd, buf, count);
}

int underlying_close(int fd) {
    static int (*underlying)(int fd) = 0;
    if (!underlying) {
        underlying = dlsym(get_libc(), "close");
    }
    return (*underlying)(fd);
}

#endif
