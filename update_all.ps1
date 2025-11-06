# Update all exchange data + forex + stocks
$exchanges = @("binance", "bitfinex", "bitget", "bitstamp", "bybit", "coinbase", "gateio", "huobi", "kraken", "kucoin", "mexc", "okx")
$quoteAssets = @("USDT", "EUR", "USD", "BTC", "ETH")
$volumes = @(500000, 1000000, 5000000)
$currentDate = Get-Date -Format "dd-MMM-yy"

Write-Host "Starting full update of all data..." -ForegroundColor Green
Write-Host "- Crypto Exchanges: $($exchanges.Count)" -ForegroundColor Yellow
Write-Host "- Forex (OANDA): 3 types" -ForegroundColor Yellow  
Write-Host "- Stocks: NYSE, NASDAQ, ARCA" -ForegroundColor Yellow
Write-Host "Current date: $currentDate" -ForegroundColor Yellow

# Clean up old files first
Write-Host "`nCleaning up old files..." -ForegroundColor Yellow
foreach ($volume in $volumes) {
    $volDir = "output\vol_$([int]($volume/1000))K"
    if (Test-Path $volDir) {
        $oldFiles = Get-ChildItem "$volDir\*pairs*.txt" | Where-Object { $_.Name -notlike "*$currentDate*" }
        if ($oldFiles) {
            Write-Host "Removing $($oldFiles.Count) old files from $volDir..." -ForegroundColor Gray
            $oldFiles | Remove-Item -Force
        }
    }
}

# Clean forex and stocks old files
@("forex", "stocks") | ForEach-Object {
    if (Test-Path $_) {
        $oldFiles = Get-ChildItem "$_\*" -Include "*.txt" | Where-Object { $_.Name -notlike "*$currentDate*" }
        if ($oldFiles) {
            Write-Host "Removing $($oldFiles.Count) old files from $_..." -ForegroundColor Gray
            $oldFiles | Remove-Item -Force
        }
    }
}

foreach ($volume in $volumes) {
    Write-Host "`nUpdating volume threshold: $volume" -ForegroundColor Yellow
    
    foreach ($exchange in $exchanges) {
        foreach ($quote in $quoteAssets) {
            Write-Host "Processing: $exchange with $quote (vol: $volume)..." -ForegroundColor Cyan
            
            try {
                $result = python .\main.py --exchange $exchange --quote-asset $quote --min-volume $volume 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $pairCount = ($result | Select-String "Found (\d+) pairs").Matches[0].Groups[1].Value
                    if ([int]$pairCount -gt 0) {
                        Write-Host "✓ Success: $exchange $quote ($pairCount pairs)" -ForegroundColor Green
                    } else {
                        Write-Host "○ Success: $exchange $quote (0 pairs)" -ForegroundColor DarkGray
                    }
                } else {
                    Write-Host "✗ Failed: $exchange $quote - $result" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "✗ Error: $exchange $quote - $($_.Exception.Message)" -ForegroundColor Red
            }
            
            Start-Sleep -Seconds 0.5  # Avoid hitting API limits
        }
    }
}

# Update Forex (OANDA)
Write-Host "`n💱 Updating Forex data..." -ForegroundColor Magenta
Set-Location forex
try {
    $forexResult = python .\oanda.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ OANDA forex data updated" -ForegroundColor Green
    } else {
        Write-Host "✗ OANDA forex failed - $forexResult" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ OANDA forex error - $($_.Exception.Message)" -ForegroundColor Red
}
Set-Location ..

# Update Stocks 
Write-Host "`n📈 Updating Stock data..." -ForegroundColor Magenta
Set-Location stocks  
try {
    $stockResult = python .\nasdaqtrader.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Stock data updated (NYSE, NASDAQ, ARCA)" -ForegroundColor Green
    } else {
        Write-Host "✗ Stock data failed - $stockResult" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Stock data error - $($_.Exception.Message)" -ForegroundColor Red
}
Set-Location ..

Write-Host "`nGenerating analysis..." -ForegroundColor Yellow
try {
    python .\analysis\visualize.py
    Write-Host "✓ Analysis complete!" -ForegroundColor Green
} catch {
    Write-Host "✗ Analysis failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "UPDATE COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green

# Show summary of new files
Write-Host "`nNew files created today ($currentDate):" -ForegroundColor Yellow

# Crypto files
foreach ($volume in $volumes) {
    $volDir = "output\vol_$([int]($volume/1000))K"
    if (Test-Path $volDir) {
        $newFiles = Get-ChildItem "$volDir\*$currentDate*.txt" -ErrorAction SilentlyContinue
        if ($newFiles) {
            Write-Host "`n📁 $volDir\:" -ForegroundColor Cyan
            foreach ($file in $newFiles) {
                $content = Get-Content $file.FullName
                $pairCount = ($content | Measure-Object).Count
                Write-Host "  📄 $($file.Name) ($pairCount pairs)" -ForegroundColor White
            }
        }
    }
}

# Forex files
$forexFiles = Get-ChildItem "forex\*$currentDate*.txt" -ErrorAction SilentlyContinue
if ($forexFiles) {
    Write-Host "`n📁 forex\:" -ForegroundColor Cyan
    foreach ($file in $forexFiles) {
        $content = Get-Content $file.FullName
        $pairCount = ($content | Measure-Object).Count
        Write-Host "  💱 $($file.Name) ($pairCount pairs)" -ForegroundColor White
    }
}

# Stock files  
$stockFiles = Get-ChildItem "stocks\*$currentDate*.txt" -ErrorAction SilentlyContinue
if ($stockFiles) {
    Write-Host "`n📁 stocks\:" -ForegroundColor Cyan
    foreach ($file in $stockFiles) {
        $content = Get-Content $file.FullName
        $pairCount = ($content | Measure-Object).Count
        Write-Host "  📈 $($file.Name) ($pairCount stocks)" -ForegroundColor White
    }
}

Write-Host "`n📊 Charts available in: output\charts\" -ForegroundColor Cyan
Write-Host "📈 Reports available in: output\*.md" -ForegroundColor Cyan