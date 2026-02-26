#!/usr/bin/env pwsh
<#
  Auto-generated quarantine move script
  Branch: chore/repo-hygiene-20260226
  Date: 2026-02-26
#>

$ROOT = "D:\varnit\demo\2101_f\2101_UI_Chang\dummy\AA_Flight_booking_2402\AA_Flight_booking_2302"
$Q = ".quarantine\unused_20260226"
Set-Location $ROOT

$moves = @(
    # ── Category A: Stale / orphan Python files ─────────────────────────────
    # views_fixed.py: 93-line partial stub, never imported by any urls.py
    @(".quarantine\unused_20260226\views_fixed.py",
      ".quarantine\unused_20260226\microservices\ui-service\ui\views_fixed.py"),

    # backend-service flight/views.py: DRF views never wired into flight/urls.py
    @("microservices\backend-service\flight\views.py",
      ".quarantine\unused_20260226\microservices\backend-service\flight\views.py"),

    # backend-service serializers.py: only imported by the orphaned views.py
    @("microservices\backend-service\flight\serializers.py",
      ".quarantine\unused_20260226\microservices\backend-service\flight\serializers.py"),

    # ── Category B: Stale / backup templates ────────────────────────────────
    # .bak template in _temp – literally a backup, never rendered
    @("microservices\ui-service\templates\_temp\flight\index.bak.html",
      ".quarantine\unused_20260226\microservices\ui-service\templates\_temp\flight\index.bak.html"),

    # index_new.html: 55-line partial, never referenced in views.py
    @("flight\templates\flight\index_new.html",
      ".quarantine\unused_20260226\flight\templates\flight\index_new.html"),

    # ── Category C: Root-level one-off debug/check scripts ───────────────────
    @("BEFORE_AFTER_DEMONSTRATION.py",
      ".quarantine\unused_20260226\BEFORE_AFTER_DEMONSTRATION.py"),
    @("check_aa_routes.py",
      ".quarantine\unused_20260226\check_aa_routes.py"),
    @("check_airlines.py",
      ".quarantine\unused_20260226\check_airlines.py"),
    @("check_db_direct.py",
      ".quarantine\unused_20260226\check_db_direct.py"),
    @("check_dfw_ord.py",
      ".quarantine\unused_20260226\check_dfw_ord.py"),
    @("check_flights.py",
      ".quarantine\unused_20260226\check_flights.py"),
    @("check_jfk_lax.py",
      ".quarantine\unused_20260226\check_jfk_lax.py"),
    @("check_ny.py",
      ".quarantine\unused_20260226\check_ny.py"),
    @("debug_trip_type.py",
      ".quarantine\unused_20260226\debug_trip_type.py"),
    @("final_verification.py",
      ".quarantine\unused_20260226\final_verification.py"),
    @("inspect_template.py",
      ".quarantine\unused_20260226\inspect_template.py"),
    @("validate_flight_search_fix.py",
      ".quarantine\unused_20260226\validate_flight_search_fix.py"),
    @("VISUAL_GUIDE.py",
      ".quarantine\unused_20260226\VISUAL_GUIDE.py"),
    @("start_backend.py",
      ".quarantine\unused_20260226\start_backend.py"),
    @("verify_all_fixes.py",
      ".quarantine\unused_20260226\verify_all_fixes.py"),
    @("verify_roundtrip_fixes.py",
      ".quarantine\unused_20260226\verify_roundtrip_fixes.py"),
    @("response.html",
      ".quarantine\unused_20260226\response.html"),
    @("test_flight2_html.html",
      ".quarantine\unused_20260226\test_flight2_html.html"),

    # ── Category D: Root-level loose test scripts (outside pytest testpaths) ─
    @("test_actual_html.py",
      ".quarantine\unused_20260226\test_actual_html.py"),
    @("test_api.py",
      ".quarantine\unused_20260226\test_api.py"),
    @("test_backend_api.py",
      ".quarantine\unused_20260226\test_backend_api.py"),
    @("test_complete_flow.py",
      ".quarantine\unused_20260226\test_complete_flow.py"),
    @("test_export.py",
      ".quarantine\unused_20260226\test_export.py"),
    @("test_final_fix.py",
      ".quarantine\unused_20260226\test_final_fix.py"),
    @("test_flight_search.py",
      ".quarantine\unused_20260226\test_flight_search.py"),
    @("test_flights.py",
      ".quarantine\unused_20260226\test_flights.py"),
    @("test_flights2_debug.py",
      ".quarantine\unused_20260226\test_flights2_debug.py"),
    @("test_one_way_fix.py",
      ".quarantine\unused_20260226\test_one_way_fix.py"),
    @("test_roundtrip_complete.py",
      ".quarantine\unused_20260226\test_roundtrip_complete.py"),
    @("test_slice_fix.py",
      ".quarantine\unused_20260226\test_slice_fix.py"),
    @("test_template_render.py",
      ".quarantine\unused_20260226\test_template_render.py"),
    @("test_ui_flight_direct.py",
      ".quarantine\unused_20260226\test_ui_flight_direct.py"),
    @("test_ui_flight_search.py",
      ".quarantine\unused_20260226\test_ui_flight_search.py"),

    # ── Category E: Non-README Markdown files (no CI reference) ─────────────
    @("COMPLETE_FIX_SUMMARY.md",
      ".quarantine\unused_20260226\COMPLETE_FIX_SUMMARY.md"),
    @("DEPLOYMENT_CHECKLIST.md",
      ".quarantine\unused_20260226\DEPLOYMENT_CHECKLIST.md"),
    @("EXECUTIVE_SUMMARY.md",
      ".quarantine\unused_20260226\EXECUTIVE_SUMMARY.md"),
    @("FINAL_FIX_SUMMARY.md",
      ".quarantine\unused_20260226\FINAL_FIX_SUMMARY.md"),
    @("FINAL_STATUS_REPORT.md",
      ".quarantine\unused_20260226\FINAL_STATUS_REPORT.md"),
    @("FLIGHT_TIMING_SAGA_IMPROVEMENTS.md",
      ".quarantine\unused_20260226\FLIGHT_TIMING_SAGA_IMPROVEMENTS.md"),
    @("IMPLEMENTATION_DETAILS.md",
      ".quarantine\unused_20260226\IMPLEMENTATION_DETAILS.md"),
    @("QUICK_START_TESTING.md",
      ".quarantine\unused_20260226\QUICK_START_TESTING.md"),
    @("ROOT_CAUSE_AND_FIX.md",
      ".quarantine\unused_20260226\ROOT_CAUSE_AND_FIX.md"),
    @("ROUND_TRIP_FIX_SUMMARY.md",
      ".quarantine\unused_20260226\ROUND_TRIP_FIX_SUMMARY.md"),
    @("ROUND_TRIP_FIXES_SUMMARY.md",
      ".quarantine\unused_20260226\ROUND_TRIP_FIXES_SUMMARY.md"),
    @("round_trip_implementation_plan.md",
      ".quarantine\unused_20260226\round_trip_implementation_plan.md"),
    @("ROUND_TRIP_IMPLEMENTATION_SUMMARY.md",
      ".quarantine\unused_20260226\ROUND_TRIP_IMPLEMENTATION_SUMMARY.md"),
    @("ROUND_TRIP_VERIFICATION.md",
      ".quarantine\unused_20260226\ROUND_TRIP_VERIFICATION.md"),
    @("ROUNDTRIP_FIX_SUMMARY.md",
      ".quarantine\unused_20260226\ROUNDTRIP_FIX_SUMMARY.md"),
    @("ROUNDTRIP_PAYMENT_FIXES.md",
      ".quarantine\unused_20260226\ROUNDTRIP_PAYMENT_FIXES.md"),
    @("TESTING_GUIDE.md",
      ".quarantine\unused_20260226\TESTING_GUIDE.md"),
    @("VERIFICATION_CHECKLIST.md",
      ".quarantine\unused_20260226\VERIFICATION_CHECKLIST.md"),

    # ── Category F: Unreferenced static assets ───────────────────────────────
    # service_status.js: never loaded by any template (git grep confirms empty)
    @("flight\static\js\service_status.js",
      ".quarantine\unused_20260226\flight\static\js\service_status.js"),

    # ── Category G: Microservices debug / diagnostic scripts ─────────────────
    @("microservices\backend-service\check_imports.py",
      ".quarantine\unused_20260226\microservices\backend-service\check_imports.py"),
    @("microservices\backend-service\debug_trip_type.py",
      ".quarantine\unused_20260226\microservices\backend-service\debug_trip_type.py"),
    @("microservices\backend-service\run_backend.py",
      ".quarantine\unused_20260226\microservices\backend-service\run_backend.py"),
    @("microservices\backend-service\test_api.py",
      ".quarantine\unused_20260226\microservices\backend-service\test_api.py"),
    @("microservices\backend-service\test_trip_type.py",
      ".quarantine\unused_20260226\microservices\backend-service\test_trip_type.py"),
    @("microservices\diagnose_services.py",
      ".quarantine\unused_20260226\microservices\diagnose_services.py"),
    @("microservices\simple_diagnosis.py",
      ".quarantine\unused_20260226\microservices\simple_diagnosis.py"),
    @("microservices\start_all_services.py",
      ".quarantine\unused_20260226\microservices\start_all_services.py"),
    @("microservices\start_services.py",
      ".quarantine\unused_20260226\microservices\start_services.py")
)

$ok = 0
$fail = 0

foreach ($pair in $moves) {
    $src = $pair[0]
    $dst = $pair[1]

    # Skip first entry – it was already moved manually (views_fixed.py)
    if ($src -eq ".quarantine\unused_20260226\views_fixed.py") {
        # Rename to correct structure path
        $correctDst = ".quarantine\unused_20260226\microservices\ui-service\ui\views_fixed.py"
        New-Item -ItemType Directory -Force (Split-Path $correctDst) | Out-Null
        git mv $src $correctDst 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { $ok++; Write-Host "[OK] $src -> $correctDst" }
        else { $fail++; Write-Host "[FAIL] $src" }
        continue
    }

    if (-not (Test-Path $src)) {
        Write-Host "[SKIP] Not found: $src"
        continue
    }

    # Ensure destination directory exists
    $dstDir = Split-Path $dst
    if ($dstDir) { New-Item -ItemType Directory -Force $dstDir | Out-Null }

    git mv $src $dst 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ok++
        Write-Host "[OK]   $src"
    } else {
        $fail++
        Write-Host "[FAIL] $src"
    }
}

Write-Host ""
Write-Host "======================================="
Write-Host "Moves OK: $ok   Failures: $fail"
Write-Host "======================================="
