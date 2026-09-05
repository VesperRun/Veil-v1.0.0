# Copyright (C) 2026 Veil contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import ctypes
import os
from ctypes import c_void_p, sizeof


def _virtual_lock(address: int, size: int) -> bool:
    if os.name != "nt":
        return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.VirtualLock.argtypes = [c_void_p, ctypes.c_size_t]
    kernel32.VirtualLock.restype = ctypes.c_bool
    return bool(kernel32.VirtualLock(c_void_p(address), size))


def _virtual_unlock(address: int, size: int) -> None:
    if os.name != "nt":
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.VirtualUnlock.argtypes = [c_void_p, ctypes.c_size_t]
    kernel32.VirtualUnlock.restype = ctypes.c_bool
    kernel32.VirtualUnlock(c_void_p(address), size)


def _mlock(address: int, size: int) -> bool:
    if os.name == "nt":
        return False
    libc = ctypes.CDLL(None, use_errno=True)
    libc.mlock.argtypes = [c_void_p, ctypes.c_size_t]
    libc.mlock.restype = ctypes.c_int
    return libc.mlock(c_void_p(address), size) == 0


def _munlock(address: int, size: int) -> None:
    if os.name == "nt":
        return
    libc = ctypes.CDLL(None, use_errno=True)
    libc.munlock.argtypes = [c_void_p, ctypes.c_size_t]
    libc.munlock.restype = ctypes.c_int
    libc.munlock(c_void_p(address), size)


def wipe_bytearray(buf: bytearray) -> None:
    for i in range(len(buf)):
        buf[i] = 0


class LockedBuffer:
    """Best-effort locked RAM for a secret blob. Not a security boundary."""

    def __init__(self, data: bytes):
        if not data:
            data = b"\x00"
        self._n = len(data)
        self._buf = ctypes.create_string_buffer(data, self._n)
        self._addr = ctypes.addressof(self._buf)
        self._locked = False
        if os.name == "nt":
            self._locked = _virtual_lock(self._addr, max(self._n, sizeof(c_void_p)))
        else:
            self._locked = _mlock(self._addr, self._n)

    def snapshot(self) -> bytes:
        return bytes(self._buf.raw[: self._n])

    def replace(self, data: bytes) -> None:
        self.wipe()
        self.__init__(data)

    def wipe(self) -> None:
        ctypes.memset(self._buf, 0, self._n)
        if self._locked:
            if os.name == "nt":
                _virtual_unlock(self._addr, max(self._n, sizeof(c_void_p)))
            else:
                _munlock(self._addr, self._n)
            self._locked = False
