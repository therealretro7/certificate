Add-Type -AssemblyName System.Drawing

$fullName = $args[0]
if (-not $fullName) { $fullName = "Participant Name" }
$eventDate = $args[1]
if (-not $eventDate) { $eventDate = "08/10/2026" }
$speakerId = $args[2]
if (-not $speakerId) { $speakerId = "admin1" }
$outputFile = $args[3]
if (-not $outputFile) { $outputFile = "c:\Users\ASWIN\Downloads\certificate\rendered_cert_temp.png" }

$initiativeName = if ($args[4]) { $args[4] } else { "Product understanding" }
$sessionLocation = if ($args[5]) { $args[5] } else { "Virtual(Google meet)" }

$baseDir = "c:\Users\ASWIN\Downloads\certificate"
$templatePath = Join-Path $baseDir "template_clean_2x.png"

$tmpl = [System.Drawing.Image]::FromFile($templatePath)
$bmp = New-Object System.Drawing.Bitmap $tmpl
$tmpl.Dispose()

$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic

# Speaker mapping
$speakers = @{
    "admin1" = @{ name = "ASWIN ASOK KV"; gid = "14248"; sig = "Aswin Signature.png" }
    "admin2" = @{ name = "Paulbin Chacko"; gid = "12348"; sig = "paul_signature_transparent.png" }
    "admin3" = @{ name = "THOMAS P D"; gid = "14434"; sig = "th.jpeg" }
}

$sp = $speakers[$speakerId]
if (-not $sp) { $sp = $speakers["admin1"] }

$brushDark = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(17, 17, 17))
$formatCenter = New-Object System.Drawing.StringFormat
$formatCenter.Alignment = [System.Drawing.StringAlignment]::Center
$formatCenter.LineAlignment = [System.Drawing.StringAlignment]::Far

# Load GoogleSans-Bold font
$fontFilePath = Join-Path $baseDir "GoogleSans-Bold.ttf"
$pfc = New-Object System.Drawing.Text.PrivateFontCollection
if (Test-Path $fontFilePath) {
    $pfc.AddFontFile($fontFilePath)
    $ff = $pfc.Families[0]
} else {
    $ff = [System.Drawing.FontFamily]::GenericSansSerif
}

# 1. Recipient Name (Centered at X=1024, underline is at Y=660)
$nameFontSize = 64
if ($fullName.Length -gt 28) { $nameFontSize = 46 }
elseif ($fullName.Length -gt 20) { $nameFontSize = 54 }

$fontName = New-Object System.Drawing.Font($ff, $nameFontSize, [System.Drawing.FontStyle]::Bold)
$rectName = New-Object System.Drawing.RectangleF(0, 0, 2048, 646)
$g.DrawString($fullName, $fontName, $brushDark, $rectName, $formatCenter)

# 2. "participated in [Product understanding]" (Centered at X=959, underline is at Y=820)
$fontPart = New-Object System.Drawing.Font($ff, 44, [System.Drawing.FontStyle]::Bold)
$rectPart = New-Object System.Drawing.RectangleF(566, 730, 786, 85)
$g.DrawString($initiativeName, $fontPart, $brushDark, $rectPart, $formatCenter)

# 3. "Semester 2 at [Virtual(Google meet)]" (Centered at X=1576, underline is at Y=910)
$fontSem = New-Object System.Drawing.Font($ff, 36, [System.Drawing.FontStyle]::Bold)
$rectSem = New-Object System.Drawing.RectangleF(1296, 825, 560, 80)
$g.DrawString($sessionLocation, $fontSem, $brushDark, $rectSem, $formatCenter)

# 4. Draw Date (Centered at X=468, underline is at Y=1280)
$fontDate = New-Object System.Drawing.Font($ff, 30, [System.Drawing.FontStyle]::Bold)
$rectDate = New-Object System.Drawing.RectangleF(268, 1205, 400, 70)
$g.DrawString($eventDate, $fontDate, $brushDark, $rectDate, $formatCenter)

# 5. Draw Initiative Name (Centered at X=1024, underline is at Y=1280)
$fontInit = New-Object System.Drawing.Font($ff, 26, [System.Drawing.FontStyle]::Bold)
$rectInit = New-Object System.Drawing.RectangleF(824, 1208, 398, 68)
$g.DrawString($initiativeName, $fontInit, $brushDark, $rectInit, $formatCenter)

# 6. Draw Authorized Signature (Centered at X=1578, underline is at Y=1280)
$sigPath = Join-Path $baseDir $sp.sig
if (Test-Path $sigPath) {
    try {
        $sig = [System.Drawing.Image]::FromFile($sigPath)
        $sigW = 220
        $sigH = 75
        $sigX = 1578 - ($sigW / 2)
        $sigY = 1272 - $sigH
        $g.DrawImage($sig, $sigX, $sigY, $sigW, $sigH)
        $sig.Dispose()
    } catch {
        $fontSig = New-Object System.Drawing.Font("Georgia", 36, [System.Drawing.FontStyle]::Italic)
        $rectSig = New-Object System.Drawing.RectangleF(1378, 1215, 400, 60)
        $g.DrawString($sp.name, $fontSig, $brushDark, $rectSig, $formatCenter)
    }
} else {
    $fontSig = New-Object System.Drawing.Font("Georgia", 36, [System.Drawing.FontStyle]::Italic)
    $rectSig = New-Object System.Drawing.RectangleF(1378, 1215, 400, 60)
    $g.DrawString($sp.name, $fontSig, $brushDark, $rectSig, $formatCenter)
}

# 7. Draw GID at Bottom-Right Corner
$fontGID = New-Object System.Drawing.Font("Arial", 20, [System.Drawing.FontStyle]::Regular)
$brushGID = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(95, 99, 104))
$formatRight = New-Object System.Drawing.StringFormat
$formatRight.Alignment = [System.Drawing.StringAlignment]::Far
$rectGID = New-Object System.Drawing.RectangleF(0, 1400, 1960, 35)
$g.DrawString("GID:$($sp.gid)", $fontGID, $brushGID, $rectGID, $formatRight)

$fontName.Dispose()
$fontPart.Dispose()
$fontSem.Dispose()
$fontDate.Dispose()
$fontInit.Dispose()
$fontGID.Dispose()
$pfc.Dispose()
$brushDark.Dispose()
$brushGID.Dispose()
$g.Dispose()

$bmp.Save($outputFile, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

Write-Output "Certificate rendered: $outputFile"
