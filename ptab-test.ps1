$key = 'arpepdsheafyidxpnbdxielusaxuje'
$ua = 'reference-harvester/0.1'

foreach ($h in @('api_key', 'X-Api-Key')) {
    foreach ($hst in @('api.uspto.gov', 'api.data.uspto.gov')) {
        Write-Host "Testing $hst with header $h..."
        try {
            $r = Invoke-RestMethod -Method Get `
                -Uri "https://$hst/api/v1/patent/trials/proceedings/search?searchText=%2A:%2A&rows=2" `
                -Headers @{ $h = $key; 'User-Agent' = $ua } `
                -TimeoutSec 30
            $r | ConvertTo-Json -Depth 6 | Out-String | Write-Host
        }
        catch { Write-Host $_.Exception.Message }
    }
}