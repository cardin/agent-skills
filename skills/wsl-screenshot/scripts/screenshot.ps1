<#
  screenshot.ps1 - capture the Windows desktop from WSL (or natively).

  Outputs machine-readable KEY=VALUE lines:
    PATH=C:\...\screen-....png
    SIZE=<width>x<height>
    MONITOR=<label>
    BYTES=<n>

  Options:
    -OutDir <dir>    Where to write the PNG. Default: %TEMP%\opencode-screenshots
    -Name  <file>    File name. Default: screen-<timestamp>.png
    -Monitor <n>     0 = all monitors (default), 1..N = a single monitor
    -MaxWidth <px>   Downscale so the image is at most this wide (0 = no scaling)
#>
param(
    [string]$OutDir = (Join-Path $env:TEMP 'opencode-screenshots'),
    [string]$Name = '',
    [int]$Monitor = 0,
    [int]$MaxWidth = 0
)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Opt into real pixels instead of DPI-virtualized coordinates, so the capture
# is sharp and correctly sized on scaled/high-DPI displays.
try {
    Add-Type -Namespace Win32 -Name Dpi -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
'@ -ErrorAction Stop
    [void][Win32.Dpi]::SetProcessDPIAware()
} catch { }

if (-not (Test-Path -LiteralPath $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

$screens = [System.Windows.Forms.Screen]::AllScreens

if ($Monitor -gt 0) {
    if ($Monitor -gt $screens.Count) {
        throw "Monitor $Monitor requested but only $($screens.Count) display(s) found."
    }
    $screen = $screens[$Monitor - 1]
    $bounds = $screen.Bounds
    $label  = "$($screen.DeviceName) (primary=$($screen.Primary))"
} else {
    $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $label  = "all ($($screens.Count) display(s))"
}

$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$gfx.Dispose()

if ($MaxWidth -gt 0 -and $bmp.Width -gt $MaxWidth) {
    $scale = $MaxWidth / $bmp.Width
    $newW  = [int][Math]::Round($bmp.Width * $scale)
    $newH  = [int][Math]::Round($bmp.Height * $scale)
    $resized = New-Object System.Drawing.Bitmap($newW, $newH)
    $rGfx = [System.Drawing.Graphics]::FromImage($resized)
    $rGfx.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $rGfx.DrawImage($bmp, 0, 0, $newW, $newH)
    $rGfx.Dispose()
    $bmp.Dispose()
    $bmp = $resized
}

if (-not $Name) {
    $Name = 'screen-{0:yyyyMMdd-HHmmss-fff}.png' -f (Get-Date)
}

$path = Join-Path $OutDir $Name
$finalW = $bmp.Width
$finalH = $bmp.Height
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

$info = Get-Item -LiteralPath $path
"PATH=$($info.FullName)"
"SIZE=${finalW}x${finalH}"
"MONITOR=$label"
"BYTES=$($info.Length)"
