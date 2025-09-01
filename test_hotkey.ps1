# Test hotkey by sending Shift+O
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class KeyboardSimulator {
        [DllImport("user32.dll")]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
        
        public const byte VK_SHIFT = 0x10;
        public const byte VK_O = 0x4F;
        public const uint KEYEVENTF_KEYUP = 0x0002;
        
        public static void SendShiftO() {
            // Press Shift
            keybd_event(VK_SHIFT, 0, 0, UIntPtr.Zero);
            System.Threading.Thread.Sleep(50);
            
            // Press O
            keybd_event(VK_O, 0, 0, UIntPtr.Zero);
            System.Threading.Thread.Sleep(50);
            
            // Release O
            keybd_event(VK_O, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
            System.Threading.Thread.Sleep(50);
            
            // Release Shift
            keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
        }
    }
"@

Write-Host "Waiting 3 seconds before sending Shift+O..."
Start-Sleep -Seconds 3
Write-Host "Sending Shift+O hotkey..."
[KeyboardSimulator]::SendShiftO()
Write-Host "Hotkey sent! Check Electron console for output."