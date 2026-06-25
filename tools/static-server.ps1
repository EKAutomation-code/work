param(
    [string]$Root,
    [string]$Prefix = "http://localhost:5500/"
)

$resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add($Prefix)
$listener.Start()
Write-Host "Serving $resolvedRoot at $Prefix"

$mimeTypes = @{
    ".html" = "text/html; charset=utf-8"
    ".css" = "text/css; charset=utf-8"
    ".js" = "application/javascript; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".svg" = "image/svg+xml"
    ".png" = "image/png"
    ".jpg" = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".pdf" = "application/pdf"
}

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $requestPath = [Uri]::UnescapeDataString($context.Request.Url.AbsolutePath.TrimStart("/"))
    if ([string]::IsNullOrWhiteSpace($requestPath)) {
        $requestPath = "index.html"
    }

    $candidate = Join-Path $resolvedRoot $requestPath
    $resolvedCandidate = [System.IO.Path]::GetFullPath($candidate)

    if (-not $resolvedCandidate.StartsWith($resolvedRoot)) {
        $context.Response.StatusCode = 403
        $context.Response.Close()
        continue
    }

    if (-not [System.IO.File]::Exists($resolvedCandidate)) {
        $context.Response.StatusCode = 404
        $context.Response.Close()
        continue
    }

    $bytes = [System.IO.File]::ReadAllBytes($resolvedCandidate)
    $extension = [System.IO.Path]::GetExtension($resolvedCandidate).ToLowerInvariant()
    if ($mimeTypes.ContainsKey($extension)) {
        $context.Response.ContentType = $mimeTypes[$extension]
    } else {
        $context.Response.ContentType = "application/octet-stream"
    }
    $context.Response.ContentLength64 = $bytes.Length
    $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $context.Response.Close()
}
