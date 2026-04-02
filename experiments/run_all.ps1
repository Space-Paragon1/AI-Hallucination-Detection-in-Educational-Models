#!/usr/bin/env pwsh
# experiments/run_all.ps1
# -------------------------------------------------------
# Reproducible pipeline for AI Hallucination Guard.
# Runs: merge -> train -> eval -> ablation
#
# Usage:  powershell -ExecutionPolicy Bypass -File experiments/run_all.ps1
# -------------------------------------------------------

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host "=== AI Hallucination Guard: Experiment Pipeline ==="
Write-Host "    Repo: $repoRoot"
Write-Host ""

Set-Location $repoRoot

Write-Host "--- Step 1/4: Merging datasets ---"
python experiments/merge_datasets.py
Write-Host ""

Write-Host "--- Step 2/4: Training (5-fold CV, model comparison) ---"
python experiments/train.py
Write-Host ""

Write-Host "--- Step 3/4: Evaluating on dev set ---"
python experiments/eval.py
Write-Host ""

Write-Host "--- Step 4/4: Ablation study ---"
python experiments/ablation.py
Write-Host ""

Write-Host "=== Done. Results in experiments/results/ ==="
if (Test-Path "experiments/results") {
    Get-ChildItem "experiments/results"
}
