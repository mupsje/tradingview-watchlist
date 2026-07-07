# Update all exchange data + forex + stocks
$exchanges = @("binance", "bitfinex", "bitget", "bitstamp", "bybit", "coinbase", "gateio", "huobi", "kraken", "kucoin", "mexc", "okx")
$futuresExchanges = @("binance", "bybit", "coinbase", "okx")
$quoteAssets = @("USDT", "EUR", "USD", "BTC", "ETH")
$futuresQuoteAssets = @("USDT", "USDC")
$volumes = @(500000, 1000000, 5000000)
$currentDate = Get-Date -Format "dd-MMM-yy"

Write-Host "Starting full update of all data..." -ForegroundColor Green
Write-Host "- Crypto Exchanges (spot): $($exchanges.Count)" -ForegroundColor Yellow
Write-Host "- Perpetual Futures (.P): $($futuresExchanges.Count)" -ForegroundColor Cyan
Write-Host "- Forex (OANDA): 3 types" -ForegroundColor Yellow  
Write-Host "- Stocks: NYSE, NASDAQ, ARCA" -ForegroundColor Yellow
Write-Host "Current date: $currentDate" -ForegroundColor Yellow

# Volume bucket lookup (mirrors config.py)
$volDirLookup = @{
    500000  = "output\vol_500K-1000K"
    1000000 = "output\vol_1M-5M"
    5000000 = "output\vol_5M+"
}

# Clean up old files first (spot + perpetual)
Write-Host "`nCleaning up old files..." -ForegroundColor Yellow
foreach ($volume in $volumes) {
    $volDir = $volDirLookup[$volume]
    if (Test-Path $volDir) {
        $oldFiles = Get-ChildItem "$volDir\*pairs*.txt" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "*$currentDate*" }
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
                    $pairMatch = $result | Select-String "Found (\d+)"
                    if ($pairMatch) {
                        $pairCount = $pairMatch.Matches[0].Groups[1].Value
                        if ([int]$pairCount -gt 0) {
                            Write-Host "✓ Success: $exchange $quote ($pairCount pairs)" -ForegroundColor Green
                        } else {
                            Write-Host "○ Success: $exchange $quote (0 pairs)" -ForegroundColor DarkGray
                        }
                    } else {
                        Write-Host "○ Success: $exchange $quote (unknown count)" -ForegroundColor DarkGray
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

# ========== Perpetual Futures (.P) ==========
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "🔮 UPDATING PERPETUAL FUTURES (.P) SYMBOLS" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

foreach ($volume in $volumes) {
    Write-Host "`nUpdating volume threshold: $volume" -ForegroundColor Yellow
    
    foreach ($exchange in $futuresExchanges) {
        foreach ($quote in $futuresQuoteAssets) {
            Write-Host "Processing: $exchange perpetual with $quote (vol: $volume)..." -ForegroundColor Cyan
            
            try {
                $result = python .\main.py --exchange $exchange --quote-asset $quote --min-volume $volume --futures 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $pairCountMatch = $result | Select-String "Found (\d+) pairs"
                    if ($pairCountMatch) {
                        $pairCount = $pairCountMatch.Matches[0].Groups[1].Value
                        if ([int]$pairCount -gt 0) {
                            Write-Host "✓ Success: $exchange $quote perpetual ($pairCount pairs)" -ForegroundColor Green
                        } else {
                            Write-Host "○ Success: $exchange $quote perpetual (0 pairs)" -ForegroundColor DarkGray
                        }
                    } else {
                        Write-Host "✓ Success: $exchange $quote perpetual (no count)" -ForegroundColor Green
                    }
                } else {
                    Write-Host "✗ Failed: $exchange $quote perpetual - $result" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "✗ Error: $exchange $quote perpetual - $($_.Exception.Message)" -ForegroundColor Red
            }
            
            Start-Sleep -Seconds 0.5
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
    $stockResult = python .\nasdaqtrader.py -nq -nyse -arca 2>&1
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

Write-Host "`n🧭 Building market-cap buckets..." -ForegroundColor Yellow
try {
    python .\marketcap_bucket.py
    Write-Host "✓ Market-cap buckets created" -ForegroundColor Green
} catch {
    Write-Host "✗ Market-cap bucketing failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "UPDATE COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green

# Show summary of new files
Write-Host "`nNew files created today ($currentDate):" -ForegroundColor Yellow

# Crypto files
foreach ($volume in $volumes) {
    $volDir = $volDirLookup[$volume]
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

# TradingView exports
$masterWatchlist = "output\tradingview_master_watchlist.txt"
$rankingsDir = "output\crypto_rankings"
if ((Test-Path $masterWatchlist) -or (Test-Path $rankingsDir)) {
    Write-Host "`n🎯 TradingView exports:" -ForegroundColor Cyan
    if (Test-Path $masterWatchlist) {
        $masterCount = (Get-Content $masterWatchlist | Where-Object { $_.Trim() }).Count
        Write-Host "  ✓ tradingview_master_watchlist.txt ($masterCount symbols)" -ForegroundColor White
    }
    if (Test-Path $rankingsDir) {
        $mdFiles = Get-ChildItem $rankingsDir -Recurse -Filter "*_top_20.md" -ErrorAction SilentlyContinue
        $txtFiles = Get-ChildItem $rankingsDir -Recurse -Filter "*_tradingview_import.txt" -ErrorAction SilentlyContinue
        if ($mdFiles) {
            Write-Host "  ✓ Per-exchange markdown files: $($mdFiles.Count)" -ForegroundColor White
        }
        if ($txtFiles) {
            Write-Host "  ✓ Per-exchange import files: $($txtFiles.Count)" -ForegroundColor White
        }
    }
}

Write-Host "`n📊 Charts available in: output\charts\" -ForegroundColor Cyan
Write-Host "📈 Reports available in: output\*.md" -ForegroundColor Cyan