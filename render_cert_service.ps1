Add-Type -AssemblyName System.Drawing

$fullName = $args[0]
if (-not $fullName) { $fullName = "Aswin Asok" }
$eventDate = $args[1]
if (-not $eventDate) { $eventDate = "08/10/2026" }
$speakerId = $args[2]
if (-not $speakerId) { $speakerId = "admin2" }
$outputFile = $args[3]
if (-not $outputFile) { $outputFile = "c:\Users\ASWIN\Downloads\certificate\rendered_cert_temp.png" }

$baseDir = "c:\Users\ASWIN\Downloads\certificate"
$templatePath = Join-Path $baseDir "template_clean_2x.png"

$tmpl = [System.Drawing.Image]::FromFile($templatePath)
$bmp = New-Object System.Drawing.Bitmap $tmpl
$tmpl.Dispose()

$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

# Speaker mapping
$speakers = @{
    "admin1" = @{ name = "ASWIN ASOK KV"; gid = "14248"; sig = "Aswin Signature.png" }
    "admin2" = @{ name = "Paulbin Chacko"; gid = "12348"; sig = "paul_signature_transparent.png" }
    "admin3" = @{ name = "THOMAS"; gid = "1443"; sig = "thomas_signature.png" }
}

$sp = $speakers[$speakerId]
if (-not $sp) { $sp = $speakers["admin1"] }

# 1. Draw Participant Name (Centered at X=1024, underline is at Y=784, baseline Y=768)
$fontSize = 48
if ($fullName.Length -gt 28) { $fontSize = 34 }
elseif ($fullName.Length -gt 20) { $fontSize = 40 }

$fontName = New-Object System.Drawing.Font("Georgia", $fontSize, [System.Drawing.FontStyle]::Italic)
$brushDark = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(17, 17, 17))
$formatCenter = New-Object System.Drawing.StringFormat
$formatCenter.Alignment = [System.Drawing.StringAlignment]::Center
$formatCenter.LineAlignment = [System.Drawing.StringAlignment]::Far

$rectName = New-Object System.Drawing.RectangleF(0, 0, 2048, 768)
$g.DrawString($fullName, $fontName, $brushDark, $rectName, $formatCenter)

# 2. Draw Date (Centered at X=376, underline is at Y=1258, baseline Y=1242)
$fontDate = New-Object System.Drawing.Font("Arial", 26, [System.Drawing.FontStyle]::Bold)
$rectDate = New-Object System.Drawing.RectangleF(200, 1190, 352, 52)
$g.DrawString($eventDate, $fontDate, $brushDark, $rectDate, $formatCenter)

# 3. Draw Speaker Signature
$sigPath = Join-Path $baseDir $sp.sig
if (Test-Path $sigPath) {
    try {
        $sig = [System.Drawing.Image]::FromFile($sigPath)
        $g.DrawImage($sig, 1550, 1090, 240, 84)
        $sig.Dispose()
    } catch {
        $fontSig = New-Object System.Drawing.Font("Georgia", 36, [System.Drawing.FontStyle]::Italic)
        $rectSig = New-Object System.Drawing.RectangleF(1490, 1100, 360, 50)
        $g.DrawString($sp.name, $fontSig, $brushDark, $rectSig, $formatCenter)
    }
} else {
    $fontSig = New-Object System.Drawing.Font("Georgia", 36, [System.Drawing.FontStyle]::Italic)
    $rectSig = New-Object System.Drawing.RectangleF(1490, 1100, 360, 50)
    $g.DrawString($sp.name, $fontSig, $brushDark, $rectSig, $formatCenter)
}

# 4. Draw Speaker Name & Role
$fontSpeaker = New-Object System.Drawing.Font("Arial", 22, [System.Drawing.FontStyle]::Regular)
$rectSpeaker = New-Object System.Drawing.RectangleF(1490, 1160, 360, 45)
$g.DrawString($sp.name, $fontSpeaker, $brushDark, $rectSpeaker, $formatCenter)

$fontRole = New-Object System.Drawing.Font("Arial", 18, [System.Drawing.FontStyle]::Regular)
$brushMuted = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(60, 64, 67))
$rectRole = New-Object System.Drawing.RectangleF(1490, 1205, 360, 35)
$g.DrawString("Google Student Ambassador", $fontRole, $brushMuted, $rectRole, $formatCenter)

# 5. Draw GID
$fontGID = New-Object System.Drawing.Font("Arial", 20, [System.Drawing.FontStyle]::Regular)
$brushGID = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(95, 99, 104))
$formatRight = New-Object System.Drawing.StringFormat
$formatRight.Alignment = [System.Drawing.StringAlignment]::Far
$rectGID = New-Object System.Drawing.RectangleF(0, 1400, 1960, 35)
$g.DrawString("GID:$($sp.gid)", $fontGID, $brushGID, $rectGID, $formatRight)

# NO QR CODE

$fontName.Dispose()
$fontDate.Dispose()
$fontSpeaker.Dispose()
$fontRole.Dispose()
$fontGID.Dispose()
$brushDark.Dispose()
$brushMuted.Dispose()
$brushGID.Dispose()
$g.Dispose()

$bmp.Save($outputFile, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

Write-Output "Certificate rendered: $outputFile"
