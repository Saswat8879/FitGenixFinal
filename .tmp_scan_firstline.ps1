$exts = @('.py','.ts','.tsx','.js','.jsx','.mjs','.cjs','.json','.md','.yml','.yaml','.toml','.ini','.cfg','.sh','.ps1','.txt')
$rows = New-Object System.Collections.Generic.List[object]
Get-ChildItem -Recurse -File | ForEach-Object {
  $p = $_.FullName
  if ($p.Contains('\.venv\') -or $p.Contains('\node_modules\') -or $p.Contains('\.next\') -or $p.Contains('\.git\') -or $p.Contains('\.pytest_cache\') -or $p.Contains('__pycache__')) { return }
  if (-not ($exts -contains $_.Extension.ToLower())) { return }
  $first = Get-Content -Path $p -TotalCount 1 -ErrorAction SilentlyContinue
  if ($null -eq $first) { return }
  $trim = $first.TrimStart()
  if ($trim.Length -eq 0) { return }
  if ($trim.StartsWith('#') -or $trim.StartsWith('//') -or $trim.StartsWith('/*') -or $trim.StartsWith('"') -or $trim.StartsWith("'") -or $trim.StartsWith('<!--')) {
    $rows.Add([PSCustomObject]@{ Path = $p; FirstLine = $first }) | Out-Null
  }
}
$rows | Sort-Object Path | ConvertTo-Json -Depth 2
