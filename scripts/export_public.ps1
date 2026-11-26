# Готовит публичную копию проекта без личных данных в C:\Users\<вы>\Documents\FalseDmitryMod_public
# Запуск: powershell -ExecutionPolicy Bypass -File scripts\export_public.ps1
# Копия не содержит истории git, .venv, скриншотов, дампов и справочника, снятого с данных игры.
$ErrorActionPreference = "Stop"
$src = Split-Path $PSScriptRoot -Parent
$dst = Join-Path (Split-Path $src -Parent) "FalseDmitryMod_public"

# Пути, которые нельзя публиковать
$exclDirs  = @(".git", ".venv", "__pycache__", "screens", "preview", "audio_test")
$exclFiles = @("error_file.txt", "game-catalog.md", "*.pyc", "*.wav", "*.zip")

if (Test-Path $dst) {
    # чистим всё, кроме .git, чтобы сохранить связь с удалённым репозиторием
    Get-ChildItem $dst -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force
} else {
    New-Item -ItemType Directory -Force $dst | Out-Null
}

$xd = @(); foreach ($d in $exclDirs) { $xd += @("/XD", $d) }
$xf = @(); foreach ($f in $exclFiles) { $xf += @("/XF", $f) }
robocopy $src $dst /E @xd @xf /NFL /NDL /NJH /NJS /NP | Out-Null

# build\ не публикуем целиком: только готовые сценарии в dist\
Remove-Item (Join-Path $dst "build") -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force (Join-Path $dst "dist") | Out-Null
Copy-Item (Join-Path $src "build\01_cherez_granitsu_v3.aoe2scenario") (Join-Path $dst "dist") -ErrorAction SilentlyContinue

# Замена личных данных на шаблоны
$userRoot = [regex]::Escape($env:USERPROFILE)
Get-ChildItem $dst -Recurse -File -Include *.md,*.py,*.json,*.ps1,*.txt | ForEach-Object {
    $t = [IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8)
    $n = $t
    $n = $n -replace "$userRoot\\Documents\\FalseDmitryMod", "<КОРЕНЬ_ПРОЕКТА>"
    $n = $n -replace "$userRoot\\Games\\Age of Empires 2 DE\\\d{17}", "%USERPROFILE%\Games\Age of Empires 2 DE\<STEAM_ID>"
    $n = $n -replace "\b7656119\d{10}\b", "<STEAM_ID>"
    $n = $n -replace $userRoot, "%USERPROFILE%"
    if ($n -ne $t) { [IO.File]::WriteAllText($_.FullName, $n, (New-Object Text.UTF8Encoding($false))) }
}

# Проверка: ничего личного не осталось
$me = [regex]::Escape($env:USERNAME)
$left = Get-ChildItem $dst -Recurse -File -Exclude *.aoe2scenario | Where-Object { $_.Name -ne "export_public.ps1" } | Select-String -Pattern "$me|7656119\d{10}" -ErrorAction SilentlyContinue
if ($left) { $left | Select-Object -First 20 | ForEach-Object { "LEFT: $($_.Path):$($_.LineNumber)" }; throw "Остались личные данные" }
"OK: $dst"
