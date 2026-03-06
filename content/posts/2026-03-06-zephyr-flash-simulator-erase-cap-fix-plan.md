---
title: "Zephyr Flash Simulator Erase Capability Fix Plan"
date: 2026-03-06
draft: false
tags: ["zephyr", "flash", "simulator"]
---

# Flash Simulator Erase Capability Fix Plan
## Issues: [#100352](https://github.com/zephyrproject-rtos/zephyr/issues/100352) · [#100400](https://github.com/zephyrproject-rtos/zephyr/issues/100400)

---

## 1. Root Cause

### Background
The Flash Simulator driver supports two operating modes:
- **Erase-before-write (classic Flash)**: set by `CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=y` (default)
- **RAM-like (no explicit erase required)**: set by `CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=n`

The Flash API uses `flash_get_parameters()→caps.no_explicit_erase` (a runtime boolean field) to allow code to query at runtime whether a device requires erase prior to write.

### The Bug

**File**: `drivers/flash/flash_simulator.c`, line 556 (inside the `FLASH_SIMULATOR_INIT(n)` macro):

```c
// BUGGY – uses global Kconfig constant for ALL instances
static const struct flash_parameters flash_parameters_##n = {
    .write_block_size = FLASH_SIMULATOR_PROG_UNIT(n),
    .erase_value = FLASH_SIMULATOR_ERASE_VALUE(n),
    .caps = {
        .no_explicit_erase = !IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE),  // ← BUG
    },
};
```

`IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE)` is a **compile-time global Kconfig option** that applies uniformly to **all instances**. It does **not** look at per-device Devicetree properties.

This means:
1. If you have two Flash Simulator instances where one is erase-type and one is RAM-like, both will get the same `no_explicit_erase` value — whichever the global Kconfig says.
2. The reported bug (issue #100352) is: even a single RAM-like device (configured with `CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=n`) would incorrectly report itself as requiring erase if the Kconfig was somehow inconsistent, or if the intent was to configure per-instance.

### Why It Was Not Caught

Issue #100400 explains the gap: the existing test in `tests/drivers/flash_simulator/flash_sim_impl/src/main.c`:
- Was written for **a single instance only**.
- Uses the same **Kconfig `#if` guards** as the driver to branch test logic — it **never calls `flash_get_parameters()` and checks `caps.no_explicit_erase` at runtime**.
- This means the test never verifies that the runtime device capability matches what the Kconfig/DT configuration says it should be.

### Concrete Impact
Any code that calls `flash_params_get_erase_cap()` (or reads `caps.no_explicit_erase`) to decide whether it must erase before writing will get incorrect behavior when using a RAM-like Flash Simulator device, potentially triggering unnecessary erase cycles.

---

## 2. Options to Fix/Implement

### Option A — Driver Fix: Use Per-Instance DT Property for `no_explicit_erase` (Preferred)

Instead of using the global `!IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE)`, derive the `no_explicit_erase` capability from a **per-instance Devicetree property** (e.g., a new `no-explicit-erase` boolean property on the `zephyr,sim-flash` DT binding), or by checking instance-level DT property.

**Proposed change in `drivers/flash/flash_simulator.c`** (inside `FLASH_SIMULATOR_INIT(n)` macro):

```diff
-   .no_explicit_erase = !IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE),
+   .no_explicit_erase = DT_INST_PROP(n, no_explicit_erase),
```

And add `no-explicit-erase` boolean property to the DT binding YAML for `zephyr,sim-flash`.

> [!NOTE]
> This approach allows different DT instances to have different erase capabilities (one erase-type, one RAM-like), which is architecturally correct and future-proof.

**Variant A2 (simpler, backward compatible)**: Keep the Kconfig but also honor the DT prop when present:

```c
.no_explicit_erase = DT_INST_NODE_HAS_PROP(n, no_explicit_erase)
    ? DT_INST_PROP(n, no_explicit_erase)
    : !IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE),
```

---

### Option B — Kconfig-Only Clarification (Minimal Patch to Fix Single-Instance Bug)

If multi-instance support is out of scope, the minimal fix is the same macro line but with a clearer comment and an assertion that only one Kconfig can be active at a time. Since the code already sets `no_explicit_erase = !IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE)`, the current code is actually **correct for a single instance** when the user sets the Kconfig correctly.

> [!IMPORTANT]
> If the bug is only about the Kconfig value flowing correctly (i.e., one instance where `EXPLICIT_ERASE=n` leads to `no_explicit_erase=true`), then the driver is already correct. The actual symptom (#100352) might have been fixed already in the codebase. Verify this by building with `CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=n` and checking the runtime value.

---

### Option C — Add the Per-Instance Runtime Capability Check to the Test Suite Only

If the driver fix is out of scope (e.g., already addressed in a pending PR), address **only** issue #100400 by adding a new `ZTEST` that:
1. Calls `flash_get_parameters(flash_dev)` to get runtime `flash_parameters`.
2. Verifies `caps.no_explicit_erase` matches the expected value based on Kconfig.
3. Verifies `flash_params_get_erase_cap()` returns the correct value.

This is complementary with Option A and should be done regardless.

---

## 3. Step-by-Step Implementation

### Step 1 — Verify the current state of the bug in the local repo

```bash
cd /Users/seokyoungjeong/ws/zephyr
grep -n "no_explicit_erase" drivers/flash/flash_simulator.c
```

Expected buggy line (line 556):
```
.no_explicit_erase = !IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE),
```

---

### Step 2 — Check DT binding for `zephyr,sim-flash`

```bash
find . -name "*.yaml" | xargs grep -l "zephyr,sim-flash" 2>/dev/null
# Or:
find dts/bindings -name "*sim-flash*" -o -name "*simulator*"
```

Read the binding YAML to see existing properties. We'll need to add `no-explicit-erase` if it doesn't already exist.

---

### Step 3 — Add `no-explicit-erase` property to the DT Binding YAML

**File**: `dts/bindings/flash_controller/zephyr,sim-flash.yaml` (find exact path in Step 2).

Add a new optional boolean property:
```yaml
properties:
  no-explicit-erase:
    type: boolean
    description: |
      When set, the device is RAM-like and does not require explicit erase
      before writing. Overrides CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE for
      this instance.
```

---

### Step 4 — Fix the driver to use per-instance DT property

**File**: `drivers/flash/flash_simulator.c`, inside the `FLASH_SIMULATOR_INIT(n)` macro (around line 552–558):

```diff
 static const struct flash_parameters flash_parameters_##n = {         \
     .write_block_size = FLASH_SIMULATOR_PROG_UNIT(n),                  \
     .erase_value = FLASH_SIMULATOR_ERASE_VALUE(n),                     \
     .caps = {                                                           \
-        .no_explicit_erase = !IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE), \
+        .no_explicit_erase = DT_INST_NODE_HAS_PROP(n, no_explicit_erase) \
+            ? DT_INST_PROP(n, no_explicit_erase)                         \
+            : !IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE),         \
     },                                                                   \
 };
```

Also add a helper macro near the top of the INIT section for clarity:
```c
#define FLASH_SIMULATOR_NO_EXPLICIT_ERASE(n)                              \
    COND_CODE_1(DT_INST_NODE_HAS_PROP(n, no_explicit_erase),              \
        (DT_INST_PROP(n, no_explicit_erase)),                             \
        (!IS_ENABLED(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE)))
```

Then use: `.no_explicit_erase = FLASH_SIMULATOR_NO_EXPLICIT_ERASE(n),`

---

### Step 5 — Add a New Test Case in `tests/drivers/flash_simulator/flash_sim_impl`

**File**: `tests/drivers/flash_simulator/flash_sim_impl/src/main.c`

Add a new `ZTEST` to verify the runtime capability matches what the configuration says:

```c
ZTEST(flash_sim_api, test_erase_capability)
{
    const struct flash_parameters *fp = flash_get_parameters(flash_dev);

    zassert_not_null(fp, "flash_get_parameters returned NULL");

#if defined(CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE)
    /* Device should report as requiring explicit erase */
    zassert_false(fp->caps.no_explicit_erase,
                  "Device configured as explicit-erase but reports no_explicit_erase=true");
    zassert_equal(FLASH_ERASE_C_EXPLICIT,
                  flash_params_get_erase_cap(fp),
                  "Expected FLASH_ERASE_C_EXPLICIT erase capability");
#else
    /* Device should report as NOT requiring explicit erase (RAM-like) */
    zassert_true(fp->caps.no_explicit_erase,
                 "Device configured as RAM-like but reports no_explicit_erase=false");
    zassert_equal(0, flash_params_get_erase_cap(fp),
                  "Expected no erase capability (0) for RAM-like device");
#endif
}
```

> [!NOTE]
> This test directly addresses the gap described in issue #100400: it checks at runtime that the device capability matches the configuration, rather than using `#if` to skip paths.

---

### Step 6 — (Optional) Add a Multi-Instance Test Scenario

If the DT binding approach from Step 3/4 is implemented, add an overlay that creates two simulator instances with different erase modes, and a test that verifies each has the correct `no_explicit_erase` value.

**New overlay file**: `tests/drivers/flash_simulator/flash_sim_impl/boards/qemu_x86_dual_instance.overlay`

```dts
/ {
    soc {
        sim_flash_controller0: sim-flash-controller@0 {
            compatible = "zephyr,sim-flash";
            /* ... standard erase-type instance ... */
            erase-value = <0xff>;
            /* no-explicit-erase = <0>; // not set = uses Kconfig */
        };
        sim_flash_controller1: sim-flash-controller@1 {
            compatible = "zephyr,sim-flash";
            /* ... RAM-like instance ... */
            erase-value = <0xff>;
            no-explicit-erase;  /* This instance is RAM-like */
        };
    };
};
```

Add a new test scenario in `testcase.yaml`:
```yaml
  drivers.flash.flash_simulator.dual_instance:
    extra_args: DTC_OVERLAY_FILE=boards/qemu_x86_dual_instance.overlay
    platform_allow: qemu_x86
    integration_platforms:
      - qemu_x86
```

---

### Step 7 — Update `testcase.yaml` to Include the New Capability Test

The new test `test_erase_capability` added in Step 5 will be picked up automatically by the existing test suite on all platforms. No change to `testcase.yaml` is needed for this test.

However, verify the test is running by checking that `drivers.flash.flash_simulator` and `drivers.flash.flash_simulator.ramlike` both run on `qemu_x86`.

---

## 4. Test Plan

### 4.1 Existing Tests to Run

Run all existing flash simulator tests to verify no regression:

```bash
cd /Users/seokyoungjeong/ws/zephyr

# Erase-type (default) test on QEMU x86
west build -p always -b qemu_x86 tests/drivers/flash_simulator/flash_sim_impl \
  && west build -t run

# RAM-like test (no explicit erase) on QEMU x86
west build -p always -b qemu_x86 tests/drivers/flash_simulator/flash_sim_impl \
  -- -DCONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=n \
  && west build -t run

# Erase value 0x00 variant
west build -p always -b qemu_x86 tests/drivers/flash_simulator/flash_sim_impl \
  -- -DDTC_OVERLAY_FILE=boards/qemu_x86_ev_0x00.overlay \
  && west build -t run

# native_sim erase-type
west build -p always -b native_sim tests/drivers/flash_simulator/flash_sim_impl \
  && west build -t run

# native_sim RAM-like
west build -p always -b native_sim tests/drivers/flash_simulator/flash_sim_impl \
  -- -DCONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=n \
  && west build -t run
```

Or equivalently use twister to run all test scenarios at once:

```bash
./scripts/twister -T tests/drivers/flash_simulator/flash_sim_impl \
  -p qemu_x86 -p native_sim -p native_sim/native/64 \
  --inline-logs -v
```

---

### 4.2 New Test Verification

The new `test_erase_capability` ztest (Step 5) will be compiled and run as part of the existing test suite. To specifically verify it:

```bash
# For explicit erase (Kconfig default):
west build -p always -b qemu_x86 tests/drivers/flash_simulator/flash_sim_impl \
  && west build -t run
# Expected: test_erase_capability PASS — no_explicit_erase=false, erase_cap=FLASH_ERASE_C_EXPLICIT

# For RAM-like device:
west build -p always -b qemu_x86 tests/drivers/flash_simulator/flash_sim_impl \
  -- -DCONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=n \
  && west build -t run
# Expected: test_erase_capability PASS — no_explicit_erase=true, erase_cap=0
```

---

### 4.3 Driver Fix Verification

After applying the driver fix (Step 4), the existing `test_get_erase_value` test plus the new `test_erase_capability` test together confirm correct behavior. Also verify `flash_params_get_erase_cap()` returns the right value:

- With `CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=y`: `flash_params_get_erase_cap(fp)` must return `FLASH_ERASE_C_EXPLICIT` (0x01)
- With `CONFIG_FLASH_SIMULATOR_EXPLICIT_ERASE=n`: `flash_params_get_erase_cap(fp)` must return `0`

---

### 4.4 Regression Check via Twister (Full CI-Like Run)

```bash
./scripts/twister -T tests/drivers/flash_simulator \
  -p qemu_x86 -p native_sim --inline-logs -v
```

All test scenarios listed in `testcase.yaml` must pass.

---

## 5. Files to Modify

| File | Change |
|------|--------|
| `drivers/flash/flash_simulator.c` | Fix `no_explicit_erase` initialization in `FLASH_SIMULATOR_INIT(n)` macro |
| `dts/bindings/flash_controller/zephyr,sim-flash.yaml` | Add `no-explicit-erase` boolean property |
| `tests/drivers/flash_simulator/flash_sim_impl/src/main.c` | Add `test_erase_capability` ztest function |
| `tests/drivers/flash_simulator/flash_sim_impl/testcase.yaml` | (Optional) Add dual-instance test scenario |
| `tests/drivers/flash_simulator/flash_sim_impl/boards/` | (Optional) Add dual-instance DTS overlay |

---

## 6. References

- **Bug**: [#100352](https://github.com/zephyrproject-rtos/zephyr/issues/100352) — Flash Simulator always reports requiring erase
- **Feature**: [#100400](https://github.com/zephyrproject-rtos/zephyr/issues/100400) — Missing erase capability check in tests
- **Regression commit**: [`ff81b52`](https://github.com/zephyrproject-rtos/zephyr/commit/ff81b5244833fc7d163f0d26ed35538c9bb577f7) — where `no_explicit_erase` was introduced with global Kconfig
- **Driver**: [`drivers/flash/flash_simulator.c`](file:///Users/seokyoungjeong/ws/zephyr/drivers/flash/flash_simulator.c) — line 556
- **Kconfig**: [`drivers/flash/Kconfig.simulator`](file:///Users/seokyoungjeong/ws/zephyr/drivers/flash/Kconfig.simulator)
- **Test main**: [`tests/drivers/flash_simulator/flash_sim_impl/src/main.c`](file:///Users/seokyoungjeong/ws/zephyr/tests/drivers/flash_simulator/flash_sim_impl/src/main.c)
- **Flash API Header**: [`include/zephyr/drivers/flash.h`](file:///Users/seokyoungjeong/ws/zephyr/include/zephyr/drivers/flash.h) — `flash_parameters` struct & `flash_params_get_erase_cap()`
