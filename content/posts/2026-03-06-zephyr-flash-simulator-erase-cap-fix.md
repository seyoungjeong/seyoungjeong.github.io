---
title: "Fixing the Zephyr Flash Simulator Erase Capability Bug"
date: 2026-03-06
draft: true
tags: ["zephyr", "flash", "bugfix"]
---

Today I fixed a bug in the Zephyr RTOS Flash Simulator ([#100352](https://github.com/zephyrproject-rtos/zephyr/issues/100352) and [#100400](https://github.com/zephyrproject-rtos/zephyr/issues/100400)).

### The Bug

The simulated flash driver incorrectly applied the `no_explicit_erase` capability. It was overriding the Kconfig settings with a missing Devicetree property since it used a global fallback but couldn't accommodate boolean properties naturally. This caused even RAM-like configurations (which do not require erasing before writing) to wrongly report needing explicit erases.

### The Fix

To resolve this issue, I submitted [PR #105035](https://github.com/zephyrproject-rtos/zephyr/pull/105035) with the following targeted fixes:

1. **Added `no-explicit-erase` to Devicetree Bindings**: I extended `zephyr,sim-flash.yaml` to accept a boolean `no-explicit-erase` property, allowing per-instance configuration without relying entirely on a global Kconfig. 
2. **Updated the Initialization Macro**: In `flash_simulator.c`, I added the `FLASH_SIMULATOR_NO_EXPLICIT_ERASE` macro. This performs a logical OR between the Devicetree property and the Kconfig fallback, ensuring that the runtime capability accurately reflects either option correctly.
3. **Added Unit Tests**: I wrote `test_erase_capability` as a new ztest suite scenario to fully verify `flash_params_get_erase_cap()`. Now I evaluate the runtime `caps.no_explicit_erase` value instead of relying purely on `#if` compile-time guards. 

### Planning & Root Cause Analysis

If you want to read deeper into my initial plan, the specific root cause analysis, and the different approaches I considered, check out the full fix plan document here: 

👉 [**Flash Simulator Erase Capability Fix Plan**]({{< ref "2026-03-06-zephyr-flash-simulator-erase-cap-fix-plan.md" >}})
