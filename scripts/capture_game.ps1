# Снимок окна AoE2 DE в build\screens\. Запуск по команде пользователя.
# Использование: powershell -ExecutionPolicy Bypass -File scripts\capture_game.ps1 [-Name метка]
param([string]$Name = "shot")

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
}
"@
[Win]::SetProcessDPIAware() | Out-Null

$p = Get-Process AoE2DE_s -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output "NO_WINDOW: AoE2DE_s не запущена или без окна"; exit 1 }
if ([Win]::IsIconic($p.MainWindowHandle)) { Write-Output "MINIMIZED: окно игры свёрнуто"; exit 1 }

$r = New-Object Win+RECT
[Win]::GetWindowRect($p.MainWindowHandle, [ref]$r) | Out-Null
$w = $r.Right - $r.Left; $h = $r.Bottom - $r.Top
if ($w -le 0 -or $h -le 0) { Write-Output "BAD_RECT: $w x $h"; exit 1 }

$dir = Join-Path (Split-Path $PSScriptRoot -Parent) "build\screens"
New-Item -ItemType Directory -Force $dir | Out-Null
$file = Join-Path $dir ("{0}_{1}.png" -f $Name, (Get-Date -Format "yyyyMMdd_HHmmss"))

$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.Left, $r.Top, 0, 0, $bmp.Size)
$g.Dispose()
$bmp.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output $file
