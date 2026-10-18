param([double]$Seconds=10,[string]$BuildDir='',[switch]$ContinuousCamera,[switch]$Hud,[switch]$Sky,[switch]$Steer,[string]$RuntimeDir='',[switch]$Profile,[switch]$ArmProfile,[switch]$BackgroundOnly,[switch]$ModelSubsets,[switch]$SkyBoundaries,[string]$AvailabilityTrace='',[switch]$ContinuousSky,[string]$SkyPhaseLog='',[switch]$SourcePoses)
if(!$BuildDir){$BuildDir=Join-Path $env:TEMP 'NFSUG-live-window-build'}
$ErrorActionPreference='Stop'
$env:PATH='C:\msys64\mingw64\bin;'+$env:PATH
$run=Join-Path $BuildDir ('bounded-'+[DateTime]::Now.ToString('yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$env:NF_LIVE_TEST_SECONDS=$Seconds.ToString([Globalization.CultureInfo]::InvariantCulture)
$env:NF_LIVE_TEST_INPUT='1'
if($SourcePoses){if(!$SkyBoundaries){throw '-SourcePoses requires -SkyBoundaries'};$env:NF_LIVE_SOURCE_POSES='1'}else{Remove-Item Env:NF_LIVE_SOURCE_POSES -ErrorAction SilentlyContinue}
if($ContinuousSky){if(!$Sky -or !$SkyBoundaries){throw '-ContinuousSky requires -Sky -SkyBoundaries'};$env:NF_LIVE_SKY_CONTINUOUS='1'}else{Remove-Item Env:NF_LIVE_SKY_CONTINUOUS -ErrorAction SilentlyContinue}
if($SkyPhaseLog){$env:NF_LIVE_SKY_PHASE_LOG=$SkyPhaseLog}else{Remove-Item Env:NF_LIVE_SKY_PHASE_LOG -ErrorAction SilentlyContinue}
if($AvailabilityTrace){$env:NF_LIVE_AVAILABILITY_TRACE=$AvailabilityTrace}else{Remove-Item Env:NF_LIVE_AVAILABILITY_TRACE -ErrorAction SilentlyContinue}
if($SkyBoundaries){if(!$Sky){throw '-SkyBoundaries requires -Sky'};$env:NF_LIVE_SKY_BOUNDARIES='1'}else{Remove-Item Env:NF_LIVE_SKY_BOUNDARIES -ErrorAction SilentlyContinue}
if($ModelSubsets){if(!$ContinuousCamera){throw '-ModelSubsets requires -ContinuousCamera'};$env:NF_CONTINUOUS_MODEL_SETS='1'}else{Remove-Item Env:NF_CONTINUOUS_MODEL_SETS -ErrorAction SilentlyContinue}
if($BackgroundOnly){if(!$Sky){throw '-BackgroundOnly requires -Sky'};$env:NF_LIVE_BACKGROUND_ONLY='1'}else{Remove-Item Env:NF_LIVE_BACKGROUND_ONLY -ErrorAction SilentlyContinue}
Remove-Item Env:NF_LIVE_PREPARE -ErrorAction SilentlyContinue
if($Profile -or $ArmProfile){$env:NF_CAPTURE_PROFILE='1'}else{Remove-Item Env:NF_CAPTURE_PROFILE -ErrorAction SilentlyContinue}
if($ArmProfile){$env:NF_ARM_STAGE_PROFILE='1'}else{Remove-Item Env:NF_ARM_STAGE_PROFILE -ErrorAction SilentlyContinue}
if($Hud -or $Sky){$env:NF_LIVE_HUD='1';$env:NF_LIVE_HUD_BASE_CAPTURE=Join-Path $run 'without-hud.ppm'}
else{Remove-Item Env:NF_LIVE_HUD,Env:NF_LIVE_HUD_BASE_CAPTURE -ErrorAction SilentlyContinue}
if($Sky){
 $env:NF_LIVE_SKY='1';$table=Join-Path $BuildDir 'source-table.bin'
 if(!(Test-Path -LiteralPath $table)){Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'road-correction-reciprocal.bin') -Destination $table}
 $env:NF_LIVE_SOURCE_TABLE=$table
}else{Remove-Item Env:NF_LIVE_SKY,Env:NF_LIVE_SOURCE_TABLE -ErrorAction SilentlyContinue}
if($Steer){$env:NF_LIVE_TEST_STEER='1'}else{Remove-Item Env:NF_LIVE_TEST_STEER -ErrorAction SilentlyContinue}

$env:NF_CONTINUOUS_CAMERA=if($ContinuousCamera){'1'}else{'0'}
$env:NF_LIVE_TEST_REPORT=Join-Path $run 'report.json'
$env:NF_LIVE_TEST_CAPTURE=Join-Path $run 'capture.ppm'
$exe=Join-Path $BuildDir 'NFSUG-Live-Window-Test.exe'
$project=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$bridge=Join-Path $project 'work\v2\package\NFSUG-Native-Renderer-source\build\nfsprobe.dll'
$rom=Join-Path (Split-Path $project -Parent) 'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
$state=Join-Path $project 'work\integration-0.state'
if($RuntimeDir){
 $bridge=Join-Path $RuntimeDir 'nfsprobe.dll';$rom=Join-Path $RuntimeDir 'game.gba';$state=Join-Path $RuntimeDir 'checkpoint.state'
}
@{source_poses=[bool]$SourcePoses;seconds=$Seconds;sky=[bool]$Sky;hud=[bool]($Hud -or $Sky);steering=[bool]$Steer;runtime=$RuntimeDir;profile=[bool]($Profile -or $ArmProfile);intrusive_arm_profile=[bool]$ArmProfile;background_only=[bool]$BackgroundOnly;model_subsets=[bool]$ModelSubsets;sky_boundaries=[bool]$SkyBoundaries;availability_trace=$AvailabilityTrace;continuous_sky=[bool]$ContinuousSky;sky_phase_log=$SkyPhaseLog}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $run 'configuration.json') -Encoding UTF8

foreach($path in @($exe,$bridge,$rom,$state)){if(!(Test-Path -LiteralPath $path)){throw "Missing input: $path"}}
$argsQuoted='"'+$bridge+'" "'+$rom+'" "'+$state+'"'
$proc=Start-Process -FilePath $exe -ArgumentList $argsQuoted -WorkingDirectory $run -PassThru -RedirectStandardOutput (Join-Path $run 'stdout.txt') -RedirectStandardError (Join-Path $run 'stderr.txt')
if(!$proc.WaitForExit([int](($Seconds+20)*1000))){throw "Test process $($proc.Id) still live; inspect it before retrying."}
$proc.Refresh()
"runtime_exit=$($proc.ExitCode) run=$run"
Get-Content (Join-Path $run 'stderr.txt')
if(!(Test-Path -LiteralPath $env:NF_LIVE_TEST_REPORT)){throw 'Runtime did not produce a timing report.'}
$r=Get-Content $env:NF_LIVE_TEST_REPORT -Raw | ConvertFrom-Json
$r | Format-List
if($r.failures -or !$r.capture_ok -or !$r.presented -or $r.frames -ne $r.core_frames){throw 'Bounded renderer/capture check failed.'}
if([Math]::Abs($r.wall_seconds-$r.simulation_seconds)-gt .1){throw 'Simulation fell more than 100 ms behind the wall clock.'}

if(($Hud -or $Sky) -and (!$r.hud_enabled -or $r.hud_select_misses -or $r.hud_text_missing -or !$r.hud_base_capture_ok)){throw 'Owned HUD/text integration check failed.'}
if($Sky -and (!$r.sky_enabled -or !$r.sky_draw_calls)){throw 'Owned sky integration check failed.'}

$stages=@($r.stage_profile)
$coreStage=@($stages|Where-Object name -eq 'core_capture')
if($stages.Count -ne 6 -or $coreStage.Count -ne 1 -or $coreStage[0].calls -ne $r.frames){throw 'Missing or incomplete per-stage measurements.'}
if(($Profile -or $ArmProfile) -and !$r.bridge_profile_enabled){throw 'This bridge lacks capture profiling exports.'}
if($ArmProfile -and !$r.arm_profile_available){throw 'This bridge lacks ARM-stage profiling exports.'}

if($BackgroundOnly -and !$r.background_capture_only){throw 'Background-only capture did not activate.'}

if($ModelSubsets -and (!$r.model_subset_frames -or $r.model_endpoint_fallbacks)){throw 'Model subset path did not cover transitions without whole-scene holds.'}

if(!$ModelSubsets -and $r.model_subset_frames){throw 'Opt-in model subset mode activated unexpectedly.'}

if($SkyBoundaries -and (!$r.sky_boundary_enabled -or $r.sky_boundary_failures -or $r.sky_boundaries_retained -ne $r.source_packets)){throw 'Incomplete sky boundary ownership in live renderer.'}

if(!$SkyBoundaries -and $r.sky_boundary_enabled){throw 'Opt-in sky boundary capture activated unexpectedly.'}

if($ContinuousSky -and (!$r.sky_continuous -or $r.sky_continuous_frames -lt $r.rendered -or $r.sky_continuous_fallbacks -or !$r.sky_subpixel_frames)){throw 'Continuous GPU sky path incomplete or fell back.'}
if(!$ContinuousSky -and $r.sky_continuous){throw 'Continuous sky activated unexpectedly.'}

if($SourcePoses -and (!$r.source_pose_enabled -or $r.source_pose_failures -or $r.source_pose_scenes -ne $r.source_packets -or $r.source_pose_sky_matches -ne $r.source_packets -or !$r.source_pose_models -or $r.source_pose_min_lead_frames -lt 1 -or $r.source_clock_checks -ne $r.source_packets -or !$r.source_clock_pairs)){throw 'Early source pose ownership/coherence/availability check failed.'}
if(!$SourcePoses -and $r.source_pose_enabled){throw 'Early source pose adapter activated unexpectedly.'}
